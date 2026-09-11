"""
Semantic Table Representation and Manipulation for JARVIS.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from jarvis.computer.vision.ui_element import UIElement


class TableCell(BaseModel):
    row_index: int
    col_index: int
    column_name: str
    value: str
    element: Optional[UIElement] = None


class TableRow(BaseModel):
    row_index: int
    cells: Dict[str, TableCell] = Field(default_factory=dict)  # col_name -> cell
    row_element: Optional[UIElement] = None

    def get_cell_value(self, column_name: str) -> Optional[str]:
        cell = self.cells.get(column_name.lower())
        return cell.value if cell else None


class Table(BaseModel):
    """
    Semantic Table Model enabling row selection, cell extraction,
    and column-based querying across Accessibility, DOM, and OCR.
    """
    table_id: str
    title: str = ""
    columns: List[str] = Field(default_factory=list)
    rows: List[TableRow] = Field(default_factory=list)
    table_element: Optional[UIElement] = None

    def find_row_by_text(self, text: str) -> Optional[TableRow]:
        """Finds first row containing matching text in any cell."""
        text_lower = text.lower()
        for row in self.rows:
            for cell in row.cells.values():
                if text_lower in cell.value.lower():
                    return row
        return None

    def find_row_by_column_value(self, column_name: str, expected_value: str) -> Optional[TableRow]:
        """Finds row where specified column equals or contains expected_value."""
        col_lower = column_name.lower()
        val_lower = expected_value.lower()
        for row in self.rows:
            cell = row.cells.get(col_lower)
            if cell and val_lower in cell.value.lower():
                return row
        return None

    def get_cell_value(self, row_index: int, column_name: str) -> Optional[str]:
        """Reads cell value for given row_index and column_name."""
        if 0 <= row_index < len(self.rows):
            return self.rows[row_index].get_cell_value(column_name)
        return None
