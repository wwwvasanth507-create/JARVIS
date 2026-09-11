"""
Unit tests for embedded SQLite Knowledge Graph Subsystem.
"""

import pytest
from jarvis.memory.graph import KnowledgeGraphManager, EntityType, RelationType, MemorySource


def test_knowledge_graph_node_and_edge_creation(tmp_path):
    db_file = tmp_path / "test_graph.db"
    kg = KnowledgeGraphManager(db_path=db_file)

    p_node = kg.add_node(EntityType.PROJECT, "JARVIS", aliases=["jarvis-repo"])
    a_node = kg.add_node(EntityType.APPLICATION, "Chrome", aliases=["Google Chrome", "chrome.exe"])

    edge = kg.add_edge(p_node.node_id, a_node.node_id, RelationType.USES)
    assert edge.relation_type == RelationType.USES

    resolved = kg.resolve_entity("chrome.exe")
    assert resolved is not None
    assert resolved.node_id == a_node.node_id

    neighborhood = kg.query_neighborhood(p_node.node_id, max_depth=2, max_nodes=50)
    assert neighborhood["node_count"] == 2
    assert neighborhood["edge_count"] == 1


def test_graph_poisoning_defense(tmp_path):
    db_file = tmp_path / "test_graph_poison.db"
    kg = KnowledgeGraphManager(db_path=db_file)

    ext_node = kg.add_node(
        EntityType.WEBSITE,
        "MaliciousSite",
        source=MemorySource.EXTERNAL_CONTENT,
        confidence=0.95
    )
    assert ext_node.confidence <= 0.3  # External graph nodes are capped at low confidence
