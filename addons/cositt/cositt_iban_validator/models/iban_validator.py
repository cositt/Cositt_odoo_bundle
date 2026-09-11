import re

IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]+$", re.ASCII)

# Longitud total esperada por país (ISO 13616). Si el país no está en esta
# tabla, se omite la comprobación de longitud exacta (solo se valida el
# rango genérico 15-34 y el dígito de control).
IBAN_LENGTHS = {
    "AD": 24, "AT": 20, "BE": 16, "BG": 22, "CH": 21, "CY": 28, "CZ": 24,
    "DE": 22, "DK": 18, "EE": 20, "ES": 24, "FI": 18, "FR": 27, "GB": 22,
    "GR": 27, "HR": 21, "HU": 28, "IE": 22, "IS": 26, "IT": 27, "LI": 21,
    "LT": 20, "LU": 20, "LV": 21, "MC": 27, "MT": 31, "NL": 18, "NO": 15,
    "PL": 28, "PT": 25, "RO": 24, "SE": 24, "SI": 19, "SK": 24, "SM": 27,
}


def normalize_iban(value):
    return re.sub(r"\s+", "", (value or "").strip().upper())


def looks_like_iban(value):
    """True si el valor tiene la forma general de un IBAN (2 letras de país
    + 2 dígitos + alfanumérico). Se usa para decidir si vale la pena
    validar del todo, sin forzar el formato IBAN a cuentas que no lo son
    (no todos los países usan IBAN)."""
    normalized = normalize_iban(value)
    return bool(IBAN_RE.match(normalized)) and 15 <= len(normalized) <= 34


def _mod97(normalized):
    rearranged = normalized[4:] + normalized[:4]
    digits = "".join(str(int(ch, 36)) for ch in rearranged)
    return int(digits) % 97


def check_iban(value):
    """Valida formato, longitud (según país, si se conoce) y dígito de
    control de un IBAN. Devuelve None si es válido, o un mensaje de error
    en caso contrario."""
    normalized = normalize_iban(value)

    if not IBAN_RE.match(normalized):
        return (
            "El formato no es válido (debe empezar con 2 letras de país "
            "y 2 dígitos de control, seguidos del código de cuenta)."
        )
    if not (15 <= len(normalized) <= 34):
        return "La longitud (%d caracteres) no es válida para un IBAN." % len(
            normalized
        )

    country = normalized[:2]
    expected_length = IBAN_LENGTHS.get(country)
    if expected_length and len(normalized) != expected_length:
        return (
            "La longitud (%d caracteres) no coincide con la esperada para "
            "%s (%d caracteres)." % (len(normalized), country, expected_length)
        )

    if _mod97(normalized) != 1:
        return (
            "El dígito de control no es válido (revisa que no haya un "
            "error al transcribirlo)."
        )

    return None
