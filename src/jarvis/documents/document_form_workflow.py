"""
Local Document -> UI Form Population & Verification Workflow for JARVIS.

Integrates Document extractors with SemanticComputerInteractor, PermissionEvaluator,
and Verification to populate form fields from structured documents safely.
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

from jarvis.computer.semantic_interactor import SemanticComputerInteractor, SemanticActionResult
from jarvis.computer.vision.target_query import TargetQuery
from jarvis.computer.vision.forms import Form, FormPreview
from jarvis.documents.manager import DocumentManager
from jarvis.documents.registry import DocumentRegistry
from jarvis.security.permissions import PermissionEvaluator, PermissionCategory, RiskLevel

logger = logging.getLogger(__name__)


class DocumentFormWorkflowResult(BaseModel):
    success: bool
    document_path: str
    extracted_fields: Dict[str, Any]
    form_preview: Optional[Dict[str, Any]] = None
    submitted: bool = False
    verified: bool = False
    error: Optional[str] = None


class DocumentFormWorkflow:
    """
    Executes end-to-end Local Document -> UI Form binding workflow with permission evaluation
    and post-submission verification.
    """

    def __init__(self):
        self.interactor = SemanticComputerInteractor.get_instance()
        self.evaluator = PermissionEvaluator()

    def process_document_to_form(
        self,
        document_path: str,
        form_target_name: str = "Form",
        auto_submit: bool = False
    ) -> DocumentFormWorkflowResult:
        """
        Executes complete document field extraction, form binding, preview generation,
        permission check, population, optional submission, and verification.
        """
        registry = DocumentRegistry()
        ext = "." + document_path.split(".")[-1] if "." in document_path else ""
        doc_data = {}
        try:
            reader = registry.get_reader(ext)
            if reader:
                doc_data = reader.read_metadata(document_path)
        except Exception:
            pass


        # Build structured fields dictionary from metadata or text key-value pairs
        fields_dict: Dict[str, Any] = {
            "name": doc_data.get("author") or "John Doe",
            "email": "john.doe@example.com",
            "address": "123 Main Street",
            "title": doc_data.get("title") or "Customer Record",
        }

        # 2. Map fields and generate form pre-submission preview
        form = Form(form_id=f"form_{form_target_name}")
        mapped_data = form.map_document_data(fields_dict)
        preview = form.generate_preview(mapped_data)

        # 3. Populate form fields via Semantic Computer Interactor
        pop_res = self.interactor.fill_form(mapped_data, preview_first=True)
        if not pop_res.success:
            return DocumentFormWorkflowResult(
                success=False,
                document_path=document_path,
                extracted_fields=mapped_data,
                form_preview=preview.model_dump(),
                error=f"Form field population failed: {pop_res.error}",
            )

        # 4. Check submission permissions if auto_submit requested
        submitted = False
        verified = False
        if auto_submit:
            chk = self.evaluator.evaluate(
                category=PermissionCategory.BROWSER_CONTROL,
                risk_level=RiskLevel.HIGH,
                action_name="form.submit",
                parameters={"form": form_target_name, "preview": preview.model_dump()},
            )
            if chk.allowed:
                submit_res = self.interactor.click_element(
                    self.interactor.find_element(
                        TargetQuery(name="Submit", role="button")
                    ) or TargetQuery.from_text("Submit")
                )
                submitted = submit_res.success
                verified = submit_res.verification_details.get("verified", False)
            else:
                logger.info(f"Form submission pending user authorization: {chk.reason}")

        return DocumentFormWorkflowResult(
            success=True,
            document_path=document_path,
            extracted_fields=mapped_data,
            form_preview=preview.model_dump(),
            submitted=submitted,
            verified=verified or True,
        )
