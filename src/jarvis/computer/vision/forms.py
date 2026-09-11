"""
Semantic Form Modeling, Validation, and Safe Data Binding for JARVIS.
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from jarvis.computer.vision.ui_element import UIElement

logger = logging.getLogger(__name__)


class FormField(BaseModel):
    """
    Represents an input field within a UI form.
    """
    field_id: str
    label: str
    name: str = ""
    control_type: str = "text"  # "text", "password", "checkbox", "radio", "select", "textarea", "file"
    current_value: str = ""
    placeholder: str = ""
    required: bool = False
    validation_state: str = "valid"  # "valid", "invalid", "unknown"
    is_sensitive: bool = False
    element: Optional[UIElement] = None


class FormPreview(BaseModel):
    """
    Pre-submission preview structure presented before executing form submissions.
    """
    form_id: str
    target_action: str
    fields_to_populate: Dict[str, Any]
    sensitive_fields_detected: List[str]
    requires_authorization: bool = True


class Form(BaseModel):
    """
    Semantic Form representation supporting field mapping, validation,
    data binding from structured documents, and safe submission preview.
    """
    form_id: str
    title: str = "Form"
    fields: List[FormField] = Field(default_factory=list)
    submit_button: Optional[UIElement] = None
    form_element: Optional[UIElement] = None

    def find_field_by_label(self, label_text: str) -> Optional[FormField]:
        """Matches form field by label, name, or placeholder."""
        target = label_text.lower().strip()
        for f in self.fields:
            if target in f.label.lower() or target in f.name.lower() or target in f.placeholder.lower():
                return f
        return None

    def map_document_data(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps key-value pairs from structured document data to matching form fields.
        """
        if not self.fields:
            return dict(doc_data)

        mapped: Dict[str, Any] = {}
        for key, val in doc_data.items():
            field = self.find_field_by_label(key)
            if field:
                mapped[field.label or field.name or key] = str(val)
            else:
                mapped[key] = str(val)
        return mapped

    def generate_preview(self, data_to_populate: Dict[str, Any]) -> FormPreview:
        """
        Generates pre-submission safety preview highlighting sensitive fields.
        """
        sensitive: List[str] = []
        for key in data_to_populate.keys():
            field = self.find_field_by_label(key)
            if field and (field.control_type == "password" or field.is_sensitive):
                sensitive.append(key)
            elif any(s in key.lower() for s in ("password", "secret", "cvv", "token", "ssn", "credit")):
                sensitive.append(key)

        return FormPreview(
            form_id=self.form_id,
            target_action="submit",
            fields_to_populate={
                k: ("********" if k in sensitive else v) for k, v in data_to_populate.items()
            },
            sensitive_fields_detected=sensitive,
            requires_authorization=len(sensitive) > 0 or True,
        )
