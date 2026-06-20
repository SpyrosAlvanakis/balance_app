from unittest.mock import MagicMock, patch

import pytest

from utils.authentication import authenticate


def _mock_secrets(passwords, roles):
    secrets = MagicMock()
    secrets.__getitem__.side_effect = lambda key: {"passwords": passwords}[key] if key == "passwords" else None
    secrets.roles = roles
    return secrets


@patch("utils.authentication.st")
def test_authenticate_returns_roles_for_valid_credentials(mock_st):
    mock_st.secrets = _mock_secrets(
        passwords={"alice": "correct-password"},
        roles={"admin": ["alice"]},
    )

    result = authenticate("alice", "correct-password")

    assert result == ["admin"]


@patch("utils.authentication.st")
def test_authenticate_returns_none_for_wrong_password(mock_st):
    mock_st.secrets = _mock_secrets(
        passwords={"alice": "correct-password"},
        roles={"admin": ["alice"]},
    )

    result = authenticate("alice", "wrong-password")

    assert result is None


@patch("utils.authentication.st")
def test_authenticate_returns_none_for_unknown_username(mock_st):
    mock_st.secrets = _mock_secrets(
        passwords={"alice": "correct-password"},
        roles={"admin": ["alice"]},
    )

    result = authenticate("bob", "anything")

    assert result is None


@patch("utils.authentication.st")
def test_authenticate_returns_none_when_user_has_no_role(mock_st):
    mock_st.secrets = _mock_secrets(
        passwords={"alice": "correct-password"},
        roles={"admin": []},
    )

    result = authenticate("alice", "correct-password")

    assert result is None
