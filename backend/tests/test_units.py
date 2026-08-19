"""Pure-function unit tests (no external services)."""
from app.security import (
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)
from app.services.enrichment import parse_user_agent
from app.services.shortcode import generate_short_code


def test_short_code_length_and_charset():
    code = generate_short_code(7)
    assert len(code) == 7
    assert code.isalnum()


def test_short_codes_are_unique_enough():
    codes = {generate_short_code(7) for _ in range(1000)}
    assert len(codes) == 1000  # no collisions in a small sample


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-password")
    assert verify_password("s3cret-password", hashed)
    assert not verify_password("wrong", hashed)


def test_api_key_prefix_and_hash():
    full, prefix, hashed = generate_api_key()
    assert full.startswith("sx_")
    assert full[:12] == prefix
    assert hash_api_key(full) == hashed


def test_user_agent_parsing_iphone():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
    parsed = parse_user_agent(ua)
    assert parsed["device_type"] == "mobile"
    assert parsed["os"].lower().startswith("ios")
