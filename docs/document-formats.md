# Supported Document Formats

| Extension | MIME Type | Classification | Parser Handler |
|---|---|---|---|
| `.txt` | `text/plain` | Text | `PlainTextExtractor` |
| `.md` | `text/markdown` | Text | `MarkdownExtractor` |
| `.json` | `application/json` | Text | `JSONYAMLExtractor` |
| `.yaml`, `.yml` | `application/x-yaml` | Text | `JSONYAMLExtractor` |
| `.csv` | `text/csv` | Text | `CSVExtractor` |
| `.html`, `.xml` | `text/html` | Text | `HTMLExtractor` |
| `.pdf` | `application/pdf` | Binary | `PDFExtractor` |
| `.docx` | `application/vnd.openxmlformats...` | Binary | `DOCXExtractor` |
