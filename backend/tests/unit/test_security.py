import time
from datetime import timedelta

import pytest

from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self) -> None:
        hashed = hash_password("CorrectHorseBattery9")
        assert hashed != "CorrectHorseBattery9"
        assert hashed.startswith("$argon2id$")

    def test_verify_correct_password(self) -> None:
        hashed = hash_password("CorrectHorseBattery9")
        assert verify_password("CorrectHorseBattery9", hashed) is True

    def test_verify_incorrect_password(self) -> None:
        hashed = hash_password("CorrectHorseBattery9")
        assert verify_password("WrongPassword1", hashed) is False

    def test_verify_handles_malformed_hash_without_raising(self) -> None:
        assert verify_password("anything", "not-a-real-hash") is False

    def test_same_password_produces_different_hashes(self) -> None:
        # Argon2 salts automatically — two hashes of the same password
        # must never be identical.
        h1 = hash_password("CorrectHorseBattery9")
        h2 = hash_password("CorrectHorseBattery9")
        assert h1 != h2


class TestJWTTokens:
    def test_access_token_round_trip(self) -> None:
        token = create_access_token(subject="user-123", role="business_owner")
        payload = decode_token(token, expected_type=TokenType.ACCESS)
        assert payload.sub == "user-123"
        assert payload.role == "business_owner"
        assert payload.type == TokenType.ACCESS

    def test_refresh_token_round_trip(self) -> None:
        token, jti = create_refresh_token(subject="user-123", role="business_owner")
        payload = decode_token(token, expected_type=TokenType.REFRESH)
        assert payload.sub == "user-123"
        assert payload.jti == jti
        assert payload.type == TokenType.REFRESH

    def test_access_token_rejected_as_refresh_token(self) -> None:
        token = create_access_token(subject="user-123", role="business_owner")
        with pytest.raises(InvalidTokenError):
            decode_token(token, expected_type=TokenType.REFRESH)

    def test_tampered_token_is_rejected(self) -> None:
        token = create_access_token(subject="user-123", role="business_owner")
        tampered = token[:-4] + "abcd"
        with pytest.raises(InvalidTokenError):
            decode_token(tampered, expected_type=TokenType.ACCESS)

    def test_malformed_token_is_rejected(self) -> None:
        with pytest.raises(InvalidTokenError):
            decode_token("not.a.jwt", expected_type=TokenType.ACCESS)

    def test_each_refresh_token_has_unique_jti(self) -> None:
        _, jti1 = create_refresh_token(subject="user-123", role="business_owner")
        _, jti2 = create_refresh_token(subject="user-123", role="business_owner")
        assert jti1 != jti2
