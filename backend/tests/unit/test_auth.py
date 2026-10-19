from app.auth import csrf_token, digest_token, hash_password, verify_password


def test_password_hash_is_salted_and_verifies_only_matching_password():
    password = "synthetic-unit-test-only"
    encoded = hash_password(password)
    assert password not in encoded
    assert encoded != hash_password(password)
    assert verify_password(password, encoded)
    assert not verify_password("wrong", encoded)
    assert not verify_password(password, "malformed")


def test_session_and_csrf_derivations_are_distinct():
    assert digest_token("one") != digest_token("two")
    assert csrf_token("one") != digest_token("one")
    assert csrf_token("one") != csrf_token("two")
