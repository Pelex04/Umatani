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


# Longest-side cap per purpose. Phone cameras commonly produce 3000-6000px,
# multi-megabyte photos — served raw, a single business card grid with a
# dozen logos/covers meant downloading tens of megabytes per page load,
# which is the dominant cause of "everything feels slow" on the mobile
# networks this platform's users are actually on. These caps are chosen
# by how large the image is ever actually displayed at, not by an
# arbitrary global limit — a logo shown at ~50px on a card never needs
# more than a few hundred pixels of real resolution.
_MAX_DIMENSION_BY_PURPOSE: dict[UploadPurpose, int] = {
    UploadPurpose.BUSINESS_LOGO: 800,
    UploadPurpose.BUSINESS_COVER: 1600,
    UploadPurpose.PORTFOLIO_IMAGE: 1600,
    UploadPurpose.REVIEW_PHOTO: 1600,
    # Student IDs are reviewed by an admin who needs to actually read the
    # card, not just glance at it — kept larger and at higher quality than
    # display-only images so text on the ID stays legible.
    UploadPurpose.STUDENT_ID: 2000,
}
_JPEG_QUALITY_BY_PURPOSE: dict[UploadPurpose, int] = {
    UploadPurpose.STUDENT_ID: 90,
}
_DEFAULT_JPEG_QUALITY = 82


def _trim_logo_padding(img: "Image.Image") -> "Image.Image":
    """
    Business logos exported from most icon/design tools carry a chunk
    of transparent or solid-color padding baked around the actual mark
    — invisible in a big preview, but very visible once shown in this
    app's small square logo badge. objectFit:cover can't crop that
    padding away on its own: the badge and the source image are both
    square, so there's nothing for "cover" to crop — the padding is
    baked into the image's own pixels, not something CSS sizing can
    see past. Detect it here and trim it, then pad the trimmed mark
    back out to a square canvas so it still displays correctly in a
    1:1 container without stretching or losing part of the mark.
    """
    from PIL import Image, ImageChops

    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    is_transparent = alpha.getextrema()[0] < 250

    if is_transparent:
        bbox = alpha.point(lambda a: 255 if a > 8 else 0).getbbox()
    else:
        # Fully opaque — assume a solid-color background matching
        # whichever color sits in the corner, and trim to whatever
        # differs from it (small tolerance for compression noise /
        # anti-aliasing at the mark's edge).
        corner = rgba.getpixel((0, 0))
        bg = Image.new("RGB", rgba.size, corner[:3])
        diff = ImageChops.difference(rgba.convert("RGB"), bg)
        bbox = diff.point(lambda p: 255 if p > 18 else 0).getbbox()

    if not bbox:
        return img

    left, top, right, bottom = bbox
    trimmed_w, trimmed_h = right - left, bottom - top

    # Bail out rather than trim if there's basically no padding to
    # remove, or if what's "detected" is implausibly tiny (a near-
    # solid-color image would otherwise get trimmed to a sliver).
    if trimmed_w > img.width * 0.96 and trimmed_h > img.height * 0.96:
        return img
    if trimmed_w < img.width * 0.05 or trimmed_h < img.height * 0.05:
        return img

    # Add a little breathing room back so the mark isn't flush
    # against the badge's edges.
    pad = int(max(trimmed_w, trimmed_h) * 0.08)
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(img.width, right + pad)
    bottom = min(img.height, bottom + pad)
    cropped = rgba.crop((left, top, right, bottom))

    # Pad back out to a square canvas (centered) — cropping straight
    # to a square here instead would cut off part of a non-square mark.
    side = max(cropped.width, cropped.height)
    fill = (0, 0, 0, 0) if is_transparent else (*corner[:3], 255)
    canvas = Image.new("RGBA", (side, side), fill)
    canvas.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2), cropped)
    return canvas


def optimize_image(content: bytes, *, purpose: UploadPurpose) -> tuple[bytes, DetectedFileType]:
    """
    Downscales to the purpose's max dimension and re-encodes, dropping
    EXIF metadata along the way — which, for phone photos, often includes
    GPS coordinates of where the picture was taken (a real privacy leak
    for a student uploading their own ID or business photos, not just a
    file-size concern). Images with real transparency are kept as PNG;
    everything else becomes JPEG, since photographic content compresses
    far better as JPEG than PNG and none of these purposes need lossless
    output. Falls back to returning the original bytes untouched if
    Pillow can't decode the content for any reason — optimization is a
    quality-of-life improvement, not something an upload should ever hard
    -fail on.

    BUSINESS_LOGO additionally gets its padding auto-trimmed first (see
    _trim_logo_padding) — covers and portfolio photos are left alone,
    since those are real photographs where content legitimately runs to
    the edges and shouldn't be auto-cropped.
    """
    from io import BytesIO

    from PIL import Image

    try:
        img = Image.open(BytesIO(content))
        img.load()
    except Exception:
        return content, detect_file_type(content) or DetectedFileType(
            mime_type="image/jpeg", extension="jpg"
        )

    if purpose == UploadPurpose.BUSINESS_LOGO:
        try:
            img = _trim_logo_padding(img)
        except Exception:
            pass  # trimming is a nice-to-have; never let it break an upload

    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)

    max_dim = _MAX_DIMENSION_BY_PURPOSE.get(purpose, 1600)
    if max(img.size) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)

    buffer = BytesIO()
    if has_alpha:
        img.convert("RGBA").save(buffer, format="PNG", optimize=True)
        result_type = DetectedFileType(mime_type="image/png", extension="png")
    else:
        quality = _JPEG_QUALITY_BY_PURPOSE.get(purpose, _DEFAULT_JPEG_QUALITY)
        img.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
        result_type = DetectedFileType(mime_type="image/jpeg", extension="jpg")

    optimized = buffer.getvalue()
    # Rare edge case (already-tiny/already-optimal source): don't let
    # re-encoding overhead make a small file bigger.
    if len(optimized) >= len(content):
        return content, detect_file_type(content) or result_type
    return optimized, result_type
