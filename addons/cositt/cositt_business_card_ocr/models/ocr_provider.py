import io
import logging

_logger = logging.getLogger(__name__)

DEFAULT_LANG = "eng+spa"


def extract_text(image_bytes: bytes, lang: str = DEFAULT_LANG) -> str:
    """Run local OCR (Tesseract) on raw image bytes and return the text found.

    Kept as a single entry point so a future provider (cloud OCR / LLM vision,
    opt-in only) can be plugged in later without touching the calling model.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Tesseract OCR no está disponible en este servidor "
            "(faltan pytesseract/Pillow/tesseract-ocr)."
        ) from exc

    image = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(image, lang=lang)
    _logger.debug("OCR extracted %d characters", len(text))
    return text
