"""
Structured Document Intelligence Tools for JARVIS.
"""

from typing import Any, Dict, Optional
from jarvis.documents.manager import DocumentManager
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult

_doc_manager = DocumentManager()


class DocumentInspectTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.inspect",
                description="Inspect document metadata, format, page count, and hash.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target document path"}
                    },
                    "required": ["path"]
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="document_inspected"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            info = self.mgr.inspect_document(kwargs["path"])
            return ToolResult(success=True, data={
                "document_id": info.document_id,
                "filename": info.filename,
                "extension": info.extension,
                "mime_type": info.mime_type,
                "size": info.size,
                "page_count": info.page_count,
                "content_hash": info.content_hash,
                "is_binary": info.is_binary
            })
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DocumentReadTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.read",
                description="Read document with structural headings, paragraphs, and sections.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target document path"},
                        "start_page": {"type": "integer", "description": "Optional start page"},
                        "end_page": {"type": "integer", "description": "Optional end page"}
                    },
                    "required": ["path"]
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="document_read"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            p_range = None
            if "start_page" in kwargs and "end_page" in kwargs:
                p_range = (kwargs["start_page"], kwargs["end_page"])

            res = self.mgr.read_document(kwargs["path"], page_range=p_range)
            return ToolResult(success=True, data={
                "document_id": res["info"].document_id,
                "text": res["text"],
                "wrapped_text": res["wrapped_text"],
                "page_count": res["info"].page_count
            })
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DocumentExtractTextTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.extract_text",
                description="Extract raw normalized text content from a document.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target document path"}
                    },
                    "required": ["path"]
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="text_extracted"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.read_document(kwargs["path"])
            return ToolResult(success=True, data={"text": res["text"]})
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DocumentSearchTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.search",
                description="Perform deterministic string search inside document.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target document path"},
                        "query": {"type": "string", "description": "Search query string"}
                    },
                    "required": ["path", "query"]
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="document_searched"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            matches = self.mgr.search_document(kwargs["query"], kwargs["path"])
            return ToolResult(success=True, data={"matches": matches, "count": len(matches)})
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DocumentSummarizeTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.summarize",
                description="Summarize a document or specific section locally.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target document path"},
                        "section_title": {"type": "string", "description": "Optional section title"}
                    },
                    "required": ["path"]
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="document_summarized"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            summary = self.mgr.summarize_document(
                kwargs["path"],
                section_title=kwargs.get("section_title")
            )
            return ToolResult(success=True, data={
                "summary": summary.summary_text,
                "key_points": summary.key_points,
                "section_summaries": summary.section_summaries
            })
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DocumentAskTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.ask",
                description="Answer a question against a document with grounded citations.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target document path"},
                        "question": {"type": "string", "description": "Question text"}
                    },
                    "required": ["path", "question"]
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="document_asked"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            ans = self.mgr.ask_document(kwargs["question"], kwargs["path"])
            return ToolResult(success=True, data={
                "question": ans.question,
                "answer": ans.answer,
                "sources": ans.sources,
                "confidence": ans.confidence
            })
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DocumentCompareTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.compare",
                description="Compare two documents deterministically and structurally.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path_a": {"type": "string", "description": "First document path"},
                        "path_b": {"type": "string", "description": "Second document path"}
                    },
                    "required": ["path_a", "path_b"]
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="documents_compared"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            comp = self.mgr.compare_documents(kwargs["path_a"], kwargs["path_b"])
            return ToolResult(success=True, data={
                "added_sections": comp.added_sections,
                "removed_sections": comp.removed_sections,
                "changed_sections": comp.changed_sections,
                "structural_differences": comp.structural_differences,
                "summary": comp.semantic_summary
            })
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DocumentExtractTableTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.extract_table",
                description="Extract tables from document into structured data.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target document path"}
                    },
                    "required": ["path"]
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="table_extracted"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            tbls = self.mgr.extract_tables(kwargs["path"])
            tables_data = []
            for t in tbls:
                tables_data.append({
                    "table_id": t.table_id,
                    "headers": t.headers,
                    "rows": t.rows,
                    "source_location": t.source_location
                })
            return ToolResult(success=True, data={"tables": tables_data, "count": len(tables_data)})
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DocumentCreateTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.create",
                description="Create a document using atomic write and verification.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target file path"},
                        "content": {"type": "string", "description": "Document text content"},
                        "format": {"type": "string", "default": "md"},
                        "overwrite": {"type": "boolean", "default": False}
                    },
                    "required": ["path", "content"]
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="document_created"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.create_document(
                path=kwargs["path"],
                content=kwargs["content"],
                format_type=kwargs.get("format", "md"),
                overwrite=kwargs.get("overwrite", False)
            )
            return ToolResult(success=True, data=res)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DocumentConvertTool(BaseTool):
    def __init__(self, manager: Optional[DocumentManager] = None):
        self.mgr = manager or _doc_manager
        super().__init__(
            ToolMetadata(
                name="document.convert",
                description="Convert document between supported formats safely.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "source_path": {"type": "string", "description": "Source file path"},
                        "target_path": {"type": "string", "description": "Target file path"},
                        "overwrite": {"type": "boolean", "default": False}
                    },
                    "required": ["source_path", "target_path"]
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="document_converted"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.convert_document(
                source_path=kwargs["source_path"],
                target_path=kwargs["target_path"],
                overwrite=kwargs.get("overwrite", False)
            )
            return ToolResult(success=True, data=res)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


DOCUMENT_TOOLS = [
    DocumentInspectTool(),
    DocumentReadTool(),
    DocumentExtractTextTool(),
    DocumentSearchTool(),
    DocumentSummarizeTool(),
    DocumentAskTool(),
    DocumentCompareTool(),
    DocumentExtractTableTool(),
    DocumentCreateTool(),
    DocumentConvertTool(),
]

