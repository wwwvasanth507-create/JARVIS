"""
Table extraction and structured data representation.
"""

import json
import csv
import io
from typing import List, Dict, Any, Optional
from jarvis.documents.models import ExtractedTable, DocumentStructure
from jarvis.documents.registry import DocumentRegistry


class TableExtractor:
    """
    Extracts tabular data from documents into ExtractedTable models.
    """

    def __init__(self, registry: Optional[DocumentRegistry] = None):
        self.registry = registry or DocumentRegistry()

    def extract_tables(self, path: str, extension: str) -> List[ExtractedTable]:
        """
        Extracts all tables from a document file.
        """
        reader = self.registry.get_reader(extension)
        structure = reader.extract_structure(path)
        tables: List[ExtractedTable] = []

        if extension.lower() in [".csv"]:
            meta = reader.read_metadata(path)
            raw_text = reader.extract_text(path)
            f = io.StringIO(raw_text)
            csv_reader = csv.reader(f)
            headers = next(csv_reader, [])
            rows = [r for r in csv_reader]
            tables.append(ExtractedTable(
                table_id="tbl_csv_1",
                headers=headers,
                rows=rows,
                source_location="entire_file"
            ))

        elif extension.lower() in [".md"]:
            # Parse Markdown tables
            raw_text = reader.extract_text(path)
            lines = raw_text.split("\n")
            in_table = False
            table_lines = []
            table_idx = 1

            for line in lines:
                stripped = line.strip()
                if "|" in stripped:
                    in_table = True
                    table_lines.append(stripped)
                else:
                    if in_table and len(table_lines) >= 2:
                        parsed_tbl = self._parse_markdown_table(table_lines, f"tbl_md_{table_idx}")
                        if parsed_tbl:
                            tables.append(parsed_tbl)
                            table_idx += 1
                    in_table = False
                    table_lines = []

            if in_table and len(table_lines) >= 2:
                parsed_tbl = self._parse_markdown_table(table_lines, f"tbl_md_{table_idx}")
                if parsed_tbl:
                    tables.append(parsed_tbl)

        elif extension.lower() in [".docx"]:
            for idx, tbl_data in enumerate(structure.tables):
                tables.append(ExtractedTable(
                    table_id=f"tbl_docx_{idx+1}",
                    headers=tbl_data.get("headers", []),
                    rows=tbl_data.get("rows", []),
                    source_location=f"table_{idx+1}"
                ))

        return tables

    def _parse_markdown_table(self, lines: List[str], table_id: str) -> Optional[ExtractedTable]:
        # Filter out delimiter line (e.g., |---|---|)
        clean_lines = [l for l in lines if not re.match(r"^\|?[\s:-|]+\|?$", l)]
        if not clean_lines:
            return None

        headers = [c.strip() for c in clean_lines[0].strip("|").split("|")]
        rows = []
        for line in clean_lines[1:]:
            row_cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(row_cells)

        return ExtractedTable(
            table_id=table_id,
            headers=headers,
            rows=rows,
            source_location=f"line_range"
        )

    def convert_table(self, table: ExtractedTable, target_format: str) -> str:
        """Converts ExtractedTable to csv, json, or markdown format string."""
        target_fmt = target_format.lower().lstrip(".")

        if target_fmt == "json":
            result = []
            for r in table.rows:
                row_dict = {}
                for i, h in enumerate(table.headers):
                    row_dict[h] = r[i] if i < len(r) else None
                result.append(row_dict)
            return json.dumps(result, indent=2)

        elif target_fmt == "csv":
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(table.headers)
            writer.writerows(table.rows)
            return out.getvalue()

        elif target_fmt in ["md", "markdown"]:
            header_str = "| " + " | ".join(table.headers) + " |"
            sep_str = "| " + " | ".join(["---"] * len(table.headers)) + " |"
            row_strs = ["| " + " | ".join([str(c) for c in r]) + " |" for r in table.rows]
            return "\n".join([header_str, sep_str] + row_strs)

        return ""
