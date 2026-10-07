import re

from utils.errors import ValidationError


def validate_pdf(filename: str, data: bytes, max_mb: int) -> str:
    """Reject paths and special Windows filenames before allocating an upload file."""
    if (not filename or len(filename) > 180 or filename != filename.strip()
            or re.search(r'[\x00-\x1f<>:"/\\|?*]', filename)):
        raise ValidationError("Use a plain PDF filename, without paths or special characters.")
    stem = filename.split(".", 1)[0].rstrip(" .").upper()
    reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    reserved.update(f"{prefix}{suffix}" for prefix in ("COM", "LPT") for suffix in "123456789¹²³")
    if stem in reserved or not filename.lower().endswith(".pdf"):
        raise ValidationError("Only files with a valid .pdf filename are supported.")
    if not data:
        raise ValidationError("The uploaded file is empty.")
    if len(data) > max_mb * 1024 * 1024:
        raise ValidationError(f"The PDF exceeds the {max_mb} MB upload limit.")
    if not data.startswith(b"%PDF-"):
        raise ValidationError("The file does not have a valid PDF header.")
    return filename


INJECTION = re.compile(
    r"ignore\s+(all\s+)?(previous|prior|system)\s+instructions|"
    r"(reveal|print|show)\s+(the\s+)?(system prompt|api key|password|secrets)|"
    r"you are now|<\s*/?\s*(system|assistant)\s*>|override\s+(the\s+)?(rules|instructions)",
    re.IGNORECASE,
)


def suspicious(text: str) -> bool:
    """Conservative heuristic only; it cannot detect all prompt injections."""
    return bool(INJECTION.search(text))


def validate_question(question: str, max_chars: int) -> str:
    question = question.strip()
    if len(question) < 3 or len(question) > max_chars:
        raise ValidationError(f"Enter a question between 3 and {max_chars} characters.")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", question):
        raise ValidationError("The question contains unsupported control characters.")
    if suspicious(question):
        raise ValidationError("Ask about document facts without instructions to override security rules.")
    return question
