"""Output-boundary data redaction for examination document results."""

from .service import REDACTION_VERSION, redact_and_record, redact_result

__all__ = ["REDACTION_VERSION", "redact_and_record", "redact_result"]
