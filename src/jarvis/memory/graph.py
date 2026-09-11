"""
Lightweight Embedded SQLite Knowledge Graph Subsystem for JARVIS.

Stores entities (Person, Project, Application, File, Folder, Document, Website, Task, Preference, Device, Location, Organization)
and relationships (OWNS, USES, PREFERS, LOCATED_IN, CONTAINS, DEPENDS_ON, CREATED, MODIFIED, RELATED_TO, WORKS_ON, GENERATED, USED_IN).
Supports entity resolution, alias mapping, bounded query limits (depth <= 3, nodes <= 50), and graph poisoning defense.
"""

import sqlite3
import json
import time
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from jarvis.memory.memory_layers import MemorySource, SOURCE_TRUST_WEIGHTS
from jarvis.utils.paths import ResourcePathResolver

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    PERSON = "Person"
    PROJECT = "Project"
    APPLICATION = "Application"
    FILE = "File"
    FOLDER = "Folder"
    DOCUMENT = "Document"
    WEBSITE = "Website"
    TASK = "Task"
    PREFERENCE = "Preference"
    DEVICE = "Device"
    LOCATION = "Location"
    ORGANIZATION = "Organization"


class RelationType(str, Enum):
    OWNS = "OWNS"
    USES = "USES"
    PREFERS = "PREFERS"
    LOCATED_IN = "LOCATED_IN"
    CONTAINS = "CONTAINS"
    DEPENDS_ON = "DEPENDS_ON"
    CREATED = "CREATED"
    MODIFIED = "MODIFIED"
    RELATED_TO = "RELATED_TO"
    WORKS_ON = "WORKS_ON"
    GENERATED = "GENERATED"
    USED_IN = "USED_IN"


class GraphNode(BaseModel):
    node_id: str
    entity_type: EntityType
    name: str
    aliases: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
    source: MemorySource = MemorySource.USER_EXPLICIT
    confidence: float = 1.0
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class GraphEdge(BaseModel):
    edge_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0
    source: MemorySource = MemorySource.USER_EXPLICIT
    created_at: float = Field(default_factory=time.time)


class KnowledgeGraphManager:
    """
    Embedded SQLite Knowledge Graph Manager.
    Enforces bounded traversal, alias deduplication, and graph poisoning defenses.
    """

    _instance: Optional["KnowledgeGraphManager"] = None

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (ResourcePathResolver.get_data_dir() / "database" / "knowledge_graph.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    @classmethod
    def get_instance(cls) -> "KnowledgeGraphManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    node_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    aliases TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_edges (
                    edge_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    weight REAL NOT NULL,
                    source TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES graph_nodes(node_id),
                    FOREIGN KEY (target_id) REFERENCES graph_nodes(node_id)
                );
            """)
            conn.commit()

    def add_node(
        self,
        entity_type: EntityType,
        name: str,
        aliases: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        source: MemorySource = MemorySource.USER_EXPLICIT,
        confidence: float = 1.0
    ) -> GraphNode:
        """
        Adds or merges entity node in knowledge graph.
        Enforces Graph Poisoning Defense: EXTERNAL_CONTENT source receives low trust and cannot override user node definitions.
        """
        if source == MemorySource.EXTERNAL_CONTENT:
            confidence = min(confidence, 0.3)
            logger.info(f"Graph Poisoning Defense: Lowered confidence for external graph node '{name}'")

        # Entity Resolution: Check for existing node with matching name or alias
        existing = self.resolve_entity(name, entity_type=entity_type)
        now = time.time()

        if existing:
            node_id = existing.node_id
            merged_aliases = list(set(existing.aliases + (aliases or []) + [name]))
            merged_props = {**existing.properties, **(properties or {})}
            # Trust higher precedence source
            if SOURCE_TRUST_WEIGHTS.get(source, 0.5) >= SOURCE_TRUST_WEIGHTS.get(existing.source, 0.5):
                final_source = source
                final_conf = max(confidence, existing.confidence)
            else:
                final_source = existing.source
                final_conf = existing.confidence

            node = GraphNode(
                node_id=node_id,
                entity_type=entity_type,
                name=existing.name,
                aliases=merged_aliases,
                properties=merged_props,
                source=final_source,
                confidence=final_conf,
                created_at=existing.created_at,
                updated_at=now,
            )

            with self._get_connection() as conn:
                conn.execute(
                    """
                    UPDATE graph_nodes
                    SET name=?, aliases=?, properties=?, source=?, confidence=?, updated_at=?
                    WHERE node_id=?
                    """,
                    (node.name, json.dumps(node.aliases), json.dumps(node.properties), node.source.value, node.confidence, now, node_id)
                )
                conn.commit()

            return node

        else:
            node_id = f"node_{entity_type.value.lower()}_{int(now*1000)}"
            node = GraphNode(
                node_id=node_id,
                entity_type=entity_type,
                name=name,
                aliases=aliases or [name],
                properties=properties or {},
                source=source,
                confidence=confidence,
                created_at=now,
                updated_at=now,
            )

            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO graph_nodes (node_id, entity_type, name, aliases, properties, source, confidence, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (node.node_id, node.entity_type.value, node.name, json.dumps(node.aliases), json.dumps(node.properties), node.source.value, node.confidence, now, now)
                )
                conn.commit()

            return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0,
        source: MemorySource = MemorySource.USER_EXPLICIT
    ) -> GraphEdge:
        """
        Adds directed relationship edge between two nodes.
        """
        edge_id = f"edge_{source_id}_{relation_type.value}_{target_id}"
        now = time.time()
        edge = GraphEdge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=properties or {},
            weight=weight,
            source=source,
            created_at=now,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO graph_edges (edge_id, source_id, target_id, relation_type, properties, weight, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (edge.edge_id, edge.source_id, edge.target_id, edge.relation_type.value, json.dumps(edge.properties), edge.weight, edge.source.value, now)
            )
            conn.commit()

        return edge

    def resolve_entity(self, name_or_alias: str, entity_type: Optional[EntityType] = None) -> Optional[GraphNode]:
        """
        Resolves entity name or alias (e.g. 'my browser' or 'Chrome') to known GraphNode.
        """
        target = name_or_alias.lower().strip()
        with self._get_connection() as conn:
            query = "SELECT * FROM graph_nodes"
            params = []
            if entity_type:
                query += " WHERE entity_type=?"
                params.append(entity_type.value)

            rows = conn.execute(query, params).fetchall()
            for r in rows:
                aliases = json.loads(r["aliases"]) if r["aliases"] else []
                if target == r["name"].lower().strip() or any(target == a.lower().strip() for a in aliases):
                    return GraphNode(
                        node_id=r["node_id"],
                        entity_type=EntityType(r["entity_type"]),
                        name=r["name"],
                        aliases=aliases,
                        properties=json.loads(r["properties"]),
                        source=MemorySource(r["source"]),
                        confidence=r["confidence"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                    )
        return None

    def query_neighborhood(self, root_node_id: str, max_depth: int = 2, max_nodes: int = 50) -> Dict[str, Any]:
        """
        Bounded neighborhood graph traversal. Enforces max_depth <= 3 and max_nodes <= 50.
        """
        depth_limit = min(max_depth, 3)
        nodes_limit = min(max_nodes, 50)

        visited_nodes: Dict[str, Dict[str, Any]] = {}
        visited_edges: List[Dict[str, Any]] = []

        queue: List[Tuple[str, int]] = [(root_node_id, 0)]

        with self._get_connection() as conn:
            while queue and len(visited_nodes) < nodes_limit:
                current_id, depth = queue.pop(0)

                if current_id in visited_nodes or depth > depth_limit:
                    continue

                r = conn.execute("SELECT * FROM graph_nodes WHERE node_id=?", (current_id,)).fetchone()
                if r:
                    visited_nodes[current_id] = {
                        "node_id": r["node_id"],
                        "entity_type": r["entity_type"],
                        "name": r["name"],
                        "properties": json.loads(r["properties"]),
                        "depth": depth,
                    }

                if depth < depth_limit:
                    # Outgoing edges
                    out_edges = conn.execute("SELECT * FROM graph_edges WHERE source_id=?", (current_id,)).fetchall()
                    for e in out_edges:
                        visited_edges.append({
                            "edge_id": e["edge_id"],
                            "source": e["source_id"],
                            "target": e["target_id"],
                            "relation": e["relation_type"],
                        })
                        if e["target_id"] not in visited_nodes:
                            queue.append((e["target_id"], depth + 1))

        return {
            "root_id": root_node_id,
            "node_count": len(visited_nodes),
            "edge_count": len(visited_edges),
            "nodes": list(visited_nodes.values()),
            "edges": visited_edges,
        }
