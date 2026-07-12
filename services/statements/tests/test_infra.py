"""Infra control tests (AC2): the statements bucket must use CMEK and least privilege.

These read the Terraform source directly so the AC2 controls are executable in pytest
too, not only in tfsec. RED on demo-start; GREEN after the infra fix.
"""
import pathlib

import pytest

TF = pathlib.Path("infra/terraform/main.tf").read_text()


@pytest.mark.control
def test_statements_bucket_uses_cmek():
    assert "default_kms_key_name" in TF, "statements bucket has no CMEK (AC2)"


@pytest.mark.control
def test_statements_bucket_is_not_public():
    assert "allUsers" not in TF, "statements bucket has a public/over-broad IAM binding (AC2)"
    assert "allAuthenticatedUsers" not in TF
