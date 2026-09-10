"""
Document processing exception hierarchy.
"""


class DocumentError(Exception):
    """Base exception for all document processing errors."""
    pass


class UnsupportedDocumentFormatError(DocumentError):
    """Raised when a document format has no registered parser/handler."""
    def __init__(self, message: str = "UNSUPPORTED_DOCUMENT_FORMAT"):
        super().__init__(message)


class OCRRequiredError(DocumentError):
    """Raised when a PDF is image-only or requires OCR which is unavailable."""
    def __init__(self, message: str = "OCR_REQUIRED"):
        super().__init__(message)


class DocumentSecurityError(DocumentError):
    """Raised when document content violates security policies."""
    pass


class DocumentLimitExceededError(DocumentError):
    """Raised when a document exceeds file size, page count, or character limits."""
    pass


class DocumentCreationError(DocumentError):
    """Raised when document creation fails validation or verification."""
    pass


class DocumentConversionError(DocumentError):
    """Raised when document format conversion fails."""
    pass
