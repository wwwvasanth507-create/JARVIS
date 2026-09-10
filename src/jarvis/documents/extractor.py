"""
Format-specific document extractors implementing DocumentReader.
"""

import os
import json
import csv
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Dict, Any, List, Tuple, Optional
import yaml

from jarvis.documents.reader import DocumentReader
from jarvis.documents.models import DocumentStructure
from jarvis.documents.errors import OCRRequiredError, UnsupportedDocumentFormatError


class PlainTextExtractor(DocumentReader):
    def can_read(self, extension: str, mime_type: str) -> bool:
        return extension in [".txt"]

    def read_metadata(self, path: str) -> Dict[str, Any]:
        return {"page_count": 1}

    def extract_text(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def extract_structure(self, path: str) -> DocumentStructure:
        text = self.extract_text(path)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return DocumentStructure(paragraphs=paragraphs)


class MarkdownExtractor(DocumentReader):
    def can_read(self, extension: str, mime_type: str) -> bool:
        return extension in [".md"]

    def read_metadata(self, path: str) -> Dict[str, Any]:
        return {"page_count": 1}

    def extract_text(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def extract_structure(self, path: str) -> DocumentStructure:
        text = self.extract_text(path)
        headings = []
        sections = []
        paragraphs = []
        code_blocks = []
        links = []
        tables = []

        current_sec_title = "Preamble"
        current_sec_lines = []

        # Simple regex based parser
        lines = text.split("\n")
        in_code_block = False
        code_lang = ""
        code_lines = []

        for idx, line in enumerate(lines):
            stripped = line.strip()
            
            # Code blocks
            if stripped.startswith("```"):
                if in_code_block:
                    code_blocks.append({"language": code_lang, "code": "\n".join(code_lines)})
                    in_code_block = False
                    code_lines = []
                else:
                    in_code_block = True
                    code_lang = stripped.lstrip("`").strip()
                continue
            if in_code_block:
                code_lines.append(line)
                continue

            # Headings
            if stripped.startswith("#"):
                match = re.match(r"^(#+)\s+(.*)$", stripped)
                if match:
                    level = len(match.group(1))
                    h_text = match.group(2).strip()
                    headings.append({"level": level, "text": h_text, "line": idx + 1})

                    if current_sec_lines:
                        sections.append({"title": current_sec_title, "content": "\n".join(current_sec_lines), "page": 1})
                        current_sec_lines = []
                    current_sec_title = h_text
                    continue

            # Tables
            if "|" in stripped and ("---" in stripped or len(stripped.split("|")) > 2):
                tables.append({"raw": stripped, "line": idx + 1})

            # Links
            for link_match in re.finditer(r"\[(.*?)\]\((.*?)\)", stripped):
                links.append({"text": link_match.group(1), "url": link_match.group(2)})

            current_sec_lines.append(line)

        if current_sec_lines:
            sections.append({"title": current_sec_title, "content": "\n".join(current_sec_lines), "page": 1})

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and not p.strip().startswith("#")]

        return DocumentStructure(
            title=headings[0]["text"] if headings else None,
            headings=headings,
            sections=sections,
            paragraphs=paragraphs,
            code_blocks=code_blocks,
            links=links,
            tables=tables
        )


class JSONYAMLExtractor(DocumentReader):
    def can_read(self, extension: str, mime_type: str) -> bool:
        return extension in [".json", ".yaml", ".yml"]

    def read_metadata(self, path: str) -> Dict[str, Any]:
        return {"page_count": 1}

    def extract_text(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def extract_structure(self, path: str) -> DocumentStructure:
        ext = os.path.splitext(path)[1].lower()
        text = self.extract_text(path)
        parsed_data = None
        try:
            if ext == ".json":
                parsed_data = json.loads(text)
            else:
                parsed_data = yaml.safe_load(text)
        except Exception:
            parsed_data = {}

        return DocumentStructure(
            paragraphs=[text],
            sections=[{"title": "Root", "content": text, "parsed": parsed_data}]
        )

    def query_key(self, path: str, key_path: str) -> Any:
        """Deterministic key lookup, e.g. 'database.host'"""
        text = self.extract_text(path)
        ext = os.path.splitext(path)[1].lower()
        data = json.loads(text) if ext == ".json" else yaml.safe_load(text)

        parts = key_path.split(".")
        curr = data
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return None
        return curr


class CSVExtractor(DocumentReader):
    def can_read(self, extension: str, mime_type: str) -> bool:
        return extension in [".csv"]

    def read_metadata(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            row_count = sum(1 for _ in reader)
        return {
            "page_count": 1,
            "headers": headers,
            "column_count": len(headers),
            "row_count": row_count
        }

    def extract_text(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def extract_structure(self, path: str) -> DocumentStructure:
        meta = self.read_metadata(path)
        text = self.extract_text(path)
        return DocumentStructure(
            headings=[{"level": 1, "text": f"CSV Dataset ({meta['row_count']} rows, {meta['column_count']} columns)"}],
            sections=[{"title": "CSV Data", "content": text}],
            tables=[{"headers": meta["headers"], "row_count": meta["row_count"]}]
        )


class SafeHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.headings = []
        self.links = []
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ["script", "style"]:
            self.in_script = True
        if tag.lower() in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.headings.append({"tag": tag, "attrs": attrs})
        if tag.lower() == "a":
            for k, v in attrs:
                if k.lower() == "href":
                    self.links.append(v)

    def handle_endtag(self, tag):
        if tag.lower() in ["script", "style"]:
            self.in_script = False

    def handle_data(self, data):
        if not self.in_script and data.strip():
            self.text_parts.append(data.strip())


class HTMLExtractor(DocumentReader):
    def can_read(self, extension: str, mime_type: str) -> bool:
        return extension in [".html", ".xml"]

    def read_metadata(self, path: str) -> Dict[str, Any]:
        return {"page_count": 1}

    def extract_text(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()

        ext = os.path.splitext(path)[1].lower()
        if ext == ".xml":
            try:
                tree = ET.parse(path)
                return "".join(tree.getroot().itertext())
            except Exception:
                return raw

        parser = SafeHTMLParser()
        parser.feed(raw)
        return "\n".join(parser.text_parts)

    def extract_structure(self, path: str) -> DocumentStructure:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
        parser = SafeHTMLParser()
        parser.feed(raw)
        text = "\n".join(parser.text_parts)

        return DocumentStructure(
            headings=[{"level": int(h["tag"][1]), "text": h["tag"]} for h in parser.headings],
            sections=[{"title": "HTML Body", "content": text}],
            paragraphs=parser.text_parts,
            links=[{"url": link} for link in parser.links]
        )


class PDFExtractor(DocumentReader):
    """
    Safely extracts PDF text page by page.
    If PyPDF2/pypdf/pdfplumber is installed, uses it; otherwise falls back to safe mock/basic parsing.
    Raises OCRRequiredError if PDF has 0 extracted text characters.
    """

    def can_read(self, extension: str, mime_type: str) -> bool:
        return extension in [".pdf"]

    def read_metadata(self, path: str) -> Dict[str, Any]:
        text, page_count = self._extract_pdf_pages(path)
        return {"page_count": page_count}

    def extract_text(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        text, page_count = self._extract_pdf_pages(path, page_range=page_range)
        if not text.strip():
            raise OCRRequiredError(f"PDF document at '{path}' contains no readable text. OCR is required.")
        return text

    def extract_structure(self, path: str) -> DocumentStructure:
        text, page_count = self._extract_pdf_pages(path)
        if not text.strip():
            raise OCRRequiredError(f"PDF document at '{path}' contains no readable text. OCR is required.")

        pages = text.split("\n--- Page Break ---\n")
        sections = []
        for i, page_text in enumerate(pages):
            sections.append({
                "title": f"Page {i+1}",
                "content": page_text,
                "page": i + 1
            })

        return DocumentStructure(
            sections=sections,
            paragraphs=[p.strip() for p in text.split("\n\n") if p.strip()]
        )

    def _extract_pdf_pages(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> Tuple[str, int]:
        # Attempt to import pypdf or PyPDF2
        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            num_pages = len(reader.pages)
            start_p = (page_range[0] - 1) if page_range else 0
            end_p = page_range[1] if page_range else num_pages
            start_p = max(0, min(start_p, num_pages))
            end_p = max(start_p, min(end_p, num_pages))

            extracted = []
            for idx in range(start_p, end_p):
                page_t = reader.pages[idx].extract_text() or ""
                extracted.append(page_t)

            return "\n--- Page Break ---\n".join(extracted), num_pages
        except Exception:
            pass

        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(path)
            num_pages = len(reader.pages)
            start_p = (page_range[0] - 1) if page_range else 0
            end_p = page_range[1] if page_range else num_pages

            extracted = []
            for idx in range(start_p, end_p):
                page_t = reader.pages[idx].extract_text() or ""
                extracted.append(page_t)

            return "\n--- Page Break ---\n".join(extracted), num_pages
        except Exception:
            pass


        # Native fallback: scan raw stream for PDF text strings
        with open(path, "rb") as f:
            content = f.read()

        # Simple pdf text stream extractor regex
        text_matches = re.findall(rb"\((.*?)\)\s*Tj", content)
        extracted_text = " ".join([m.decode("utf-8", errors="ignore") for m in text_matches])

        # Page count heuristic
        pages_matches = len(re.findall(rb"/Type\s*/Page\b", content))
        page_count = max(1, pages_matches)

        return extracted_text, page_count


class DOCXExtractor(DocumentReader):
    """
    Safely extracts DOCX content. 0 macro/script execution.
    If python-docx is installed, uses it; otherwise parses zipped word/document.xml.
    """

    def can_read(self, extension: str, mime_type: str) -> bool:
        return extension in [".docx"]

    def read_metadata(self, path: str) -> Dict[str, Any]:
        return {"page_count": 1}

    def extract_text(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        structure = self.extract_structure(path)
        full_text = []
        for sec in structure.sections:
            full_text.append(sec["content"])
        return "\n\n".join(full_text)

    def extract_structure(self, path: str) -> DocumentStructure:
        try:
            import docx
            doc = docx.Document(path)
            headings = []
            sections = []
            paragraphs = []
            tables = []

            curr_title = "Document Body"
            curr_lines = []

            for p in doc.paragraphs:
                p_text = p.text.strip()
                if not p_text:
                    continue

                if p.style.name.startswith("Heading"):
                    level = 1
                    try:
                        level = int(p.style.name.replace("Heading", "").strip())
                    except Exception:
                        pass
                    headings.append({"level": level, "text": p_text})
                    if curr_lines:
                        sections.append({"title": curr_title, "content": "\n".join(curr_lines)})
                        curr_lines = []
                    curr_title = p_text
                else:
                    curr_lines.append(p_text)
                    paragraphs.append(p_text)

            if curr_lines:
                sections.append({"title": curr_title, "content": "\n".join(curr_lines)})

            for table in doc.tables:
                table_rows = []
                for row in table.rows:
                    table_rows.append([cell.text.strip() for cell in row.cells])
                if table_rows:
                    tables.append({
                        "headers": table_rows[0],
                        "rows": table_rows[1:],
                        "source_location": "docx_table"
                    })

            return DocumentStructure(
                title=headings[0]["text"] if headings else None,
                headings=headings,
                sections=sections,
                paragraphs=paragraphs,
                tables=tables
            )
        except ImportError:
            pass

        # Fallback ZIP xml parser for docx
        import zipfile
        with zipfile.ZipFile(path) as z:
            xml_content = z.read("word/document.xml")

        root = ET.fromstring(xml_content)
        # Extract all text elements w:t
        text_elements = root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
        full_text = "".join([t.text for t in text_elements if t.text])

        return DocumentStructure(
            sections=[{"title": "DOCX Body", "content": full_text}],
            paragraphs=[full_text]
        )
