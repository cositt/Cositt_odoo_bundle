import re
from typing import Dict, List, Union

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d \-./()]{6,}\d)")
WEBSITE_RE = re.compile(
    r"((?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|es|net|org|io|eu|co|info|biz)\b\S*)"
)
MOBILE_KEYWORDS = ("mobile", "móvil", "movil", "cell", "cel.")
PHONE_KEYWORDS = ("tel", "phone", "landline", "fijo")
FAX_KEYWORDS = ("fax",)
COMPANY_SUFFIXES = (
    "s.l.", "sl", "s.a.", "sa", "s.l.u.", "s.a.u.", "s.coop",
    "inc", "inc.", "llc", "ltd", "ltd.", "corp", "corp.", "gmbh", "group",
)
TITLE_KEYWORDS = (
    "director", "manager", "gerente", "ceo", "cto", "cfo", "coo",
    "responsable", "jefe", "head of", "sales", "ventas", "marketing",
    "consultant", "consultor", "founder", "fundador", "presidente",
    "president", "coordinador", "coordinator", "engineer", "ingeniero",
)


def normalize_phone_digits(value: Union[str, bool]) -> str:
    """Últimos 9 dígitos de un teléfono, para comparar sin importar el
    formato (espacios, guiones, prefijo de país) con el que llegó del OCR."""
    digits = re.sub(r"\D", "", value or "")
    return digits[-9:] if len(digits) >= 9 else digits


def _clean_lines(raw_text: str) -> List[str]:
    lines = []
    for line in raw_text.splitlines():
        line = line.strip(" \t|_-")
        if len(line) >= 2:
            lines.append(line)
    return lines


def parse_card_text(raw_text: str) -> Dict[str, Union[str, bool]]:
    """Best-effort extraction of contact fields from raw OCR text.

    Business cards have no fixed layout, so this is heuristic: the caller is
    always expected to let the user review/correct the result before saving.
    """
    result = {
        "partner_name": False,
        "function": False,
        "company_name": False,
        "phone": False,
        "mobile": False,
        "email": False,
        "website": False,
        "street": False,
    }

    if not raw_text:
        return result

    lines = _clean_lines(raw_text)

    email_match = EMAIL_RE.search(raw_text)
    if email_match:
        result["email"] = email_match.group(0)

    phone_candidates = []
    for line in lines:
        low = line.lower()
        if any(k in low for k in FAX_KEYWORDS):
            continue
        for match in PHONE_RE.finditer(line):
            digits = re.sub(r"\D", "", match.group(0))
            if 7 <= len(digits) <= 15:
                is_mobile = any(k in low for k in MOBILE_KEYWORDS)
                is_phone = any(k in low for k in PHONE_KEYWORDS)
                phone_candidates.append((match.group(0).strip(), is_mobile, is_phone))

    for value, is_mobile, _is_phone in phone_candidates:
        if is_mobile and not result["mobile"]:
            result["mobile"] = value
    for value, is_mobile, _is_phone in phone_candidates:
        if not is_mobile and not result["phone"]:
            result["phone"] = value
    remaining = [v for v, _m, _p in phone_candidates if v not in (result["phone"], result["mobile"])]
    if not result["mobile"] and remaining:
        result["mobile"] = remaining[0]

    for line in lines:
        if EMAIL_RE.search(line):
            # Es la línea del email, no una web (aunque comparta dominio).
            continue
        website_match = WEBSITE_RE.search(line)
        if website_match:
            result["website"] = website_match.group(0)
            break

    used_lines = set()
    for line in lines:
        if EMAIL_RE.search(line) or PHONE_RE.search(line) or (
            result["website"] and result["website"] in line
        ):
            used_lines.add(line)

    free_lines = [line for line in lines if line not in used_lines]

    for line in list(free_lines):
        if any(k in line.lower() for k in COMPANY_SUFFIXES):
            result["company_name"] = line
            free_lines.remove(line)
            break

    for line in list(free_lines):
        if any(k in line.lower() for k in TITLE_KEYWORDS):
            result["function"] = line
            free_lines.remove(line)
            break

    if free_lines:
        result["partner_name"] = free_lines.pop(0)

    if not result["company_name"] and free_lines:
        result["company_name"] = free_lines.pop(0)

    if free_lines:
        result["street"] = ", ".join(free_lines)

    return result
