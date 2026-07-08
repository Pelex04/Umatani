"""
Upload validation.

Per the spec's security requirements (MIME validation, file size limits,
secure upload validation), we never trust a client-supplied Content-Type
header — a malicious upload can claim to be "image/png" while containing
an HTML file with a <script> tag (a classic stored-XSS-via-upload vector)
or an executable. Instead we sniff the actual file signature (magic
bytes) and only accept files whose real content matches an allow-listed
type.

No external dependency (e.g. python-magic/libmagic) is used, since the
small, fixed set of types this platform needs to accept (JPEG, PNG,
WEBP, PDF) have simple, well-known magic-byte signatures — this keeps
the deployment footprint smaller and avoids a libmagic system dependency
that may not be present on the host.
"""
from dataclasses import dataclass
from enum import StrEnum


class UploadPurpose(StrEnum):
    STUDENT_ID = "student_id"
    BUSINESS_LOGO = "business_logo"
    BUSINESS_COVER = "business_cover"
    PORTFOLIO_IMAGE = "portfolio_image"
    PORTFOLIO_DOCUMENT = "portfolio_document"
    REVIEW_PHOTO = "review_photo"


class UploadValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class DetectedFileType:
    mime_type: str
    extension: str


# (magic bytes, offset, mime_type, extension)
_SIGNATURES: list[tuple[bytes, int, str, str]] = [
    (b"\xff\xd8\xff", 0, "image/jpeg", "jpg"),
    (b"\x89PNG\r\n\x1a\n", 0, "image/png", "png"),
    (b"RIFF", 0, "image/webp", "webp"),  # also requires b"WEBP" at offset 8, checked below
    (b"%PDF-", 0, "application/pdf", "pdf"),
]

_IMAGE_PURPOSES = {
    UploadPurpose.STUDENT_ID,
    UploadPurpose.BUSINESS_LOGO,
    UploadPurpose.BUSINESS_COVER,
    UploadPurpose.PORTFOLIO_IMAGE,
    UploadPurpose.REVIEW_PHOTO,
}

_ALLOWED_MIME_BY_PURPOSE: dict[UploadPurpose, set[str]] = {
    purpose: {"image/jpeg", "image/png", "image/webp"} for purpose in _IMAGE_PURPOSES
} | {
    UploadPurpose.PORTFOLIO_DOCUMENT: {"image/jpeg", "image/png", "image/webp", "application/pdf"},
}


def detect_file_type(content: bytes) -> DetectedFileType | None:
    """Sniff the real file type from its magic bytes. Returns None if unrecognized."""
    for signature, offset, mime_type, extension in _SIGNATURES:
        end = offset + len(signature)
        if len(content) >= end and content[offset:end] == signature:
            if mime_type == "image/webp":
                if len(content) < 12 or content[8:12] != b"WEBP":
                    continue
            return DetectedFileType(mime_type=mime_type, extension=extension)
    return None


def validate_upload(
    content: bytes,
    *,
    purpose: UploadPurpose,
    max_size_mb: int,
) -> DetectedFileType:
    """
    Validates an uploaded file's size and actual content type against
    what's allowed for the given purpose. Raises UploadValidationError
    with a safe, user-facing message on any failure.
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(content) == 0:
        raise UploadValidationError("Uploaded file is empty")
    if len(content) > max_size_bytes:
        raise UploadValidationError(f"File exceeds the {max_size_mb}MB size limit")

    detected = detect_file_type(content)
    if detected is None:
        raise UploadValidationError(
            "Unrecognized or unsupported file type. Allowed types: JPEG, PNG, WEBP"
            + (", PDF" if purpose == UploadPurpose.PORTFOLIO_DOCUMENT else "")
        )

    allowed = _ALLOWED_MIME_BY_PURPOSE.get(purpose, set())
    if detected.mime_type not in allowed:
        raise UploadValidationError(
            f"File type '{detected.mime_type}' is not allowed for this upload purpose"
        )

    return detected
