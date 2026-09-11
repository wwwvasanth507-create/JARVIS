# Table Understanding & Column-Based Querying

JARVIS models tabular structures across Accessibility, DOM, and OCR sources.

## Table Structure (`Table`, `TableRow`, `TableCell`)

- `columns`: List of column headers
- `rows`: List of table rows
- `cells`: Cell values mapped by column name

## Operations

- `find_row_by_text(text: str)`: Searches for text in any table cell
- `find_row_by_column_value(column_name: str, expected_value: str)`: Matches value in specific column
- `select_table_row(table_query, row_query)`: Locates and clicks row element
- `get_cell_value(row_index, column_name)`: Reads cell value in row by column header name
