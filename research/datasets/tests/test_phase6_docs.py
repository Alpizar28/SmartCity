"""Regression tests for the documented validator in a docs-branch clone."""
import subprocess
from unittest.mock import patch

import pytest

import phase6_validate_docs as validator


def result(code, output=""):
    return subprocess.CompletedProcess([], code, stdout=output, stderr="")


def test_main_revision_prefers_local_main():
    with patch.object(validator.subprocess, "run", return_value=result(0, "local-sha\n")) as run:
        assert validator.main_revision() == ("refs/heads/main", "local-sha")
    assert run.call_count == 1


def test_main_revision_falls_back_to_origin_main():
    with patch.object(validator.subprocess, "run", side_effect=[result(128), result(0, "remote-sha\n")]) as run:
        assert validator.main_revision() == ("refs/remotes/origin/main", "remote-sha")
    assert run.call_args_list[1].args[0][-1] == "refs/remotes/origin/main"


def test_main_revision_does_not_claim_success_without_reference():
    with patch.object(validator.subprocess, "run", return_value=result(128)):
        with pytest.raises(RuntimeError, match="neither local main nor origin/main"):
            validator.main_revision()
