"""Short-code generation using a Base62 alphabet."""
import secrets
import string

ALPHABET = string.ascii_letters + string.digits  # base62


def generate_short_code(length: int = 7) -> str:
    """Cryptographically-random base62 code.

    With 62^7 (~3.5e12) combinations, random generation with a uniqueness
    check on insert is collision-safe for a very long time and avoids the
    hotspotting of sequential/auto-increment encoding.
    """
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
