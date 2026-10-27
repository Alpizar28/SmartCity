"""Regression tests for the documented validator in a docs-branch clone."""
import subprocess
import csv
import hashlib
import json
from pathlib import Path
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


def test_synthetic_administration_authorization_is_documented_with_limits():
    evidence = validator.ROOT / "docs/equipo/EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md"
    assert evidence.exists()
    text = evidence.read_text(encoding="utf-8")
    assert "Pueden poner datos aleatorios a la hora de la carga" in text
    assert "No permitido inferir" in text
    assert "mediciones" in text

    contract = (validator.ROOT / "docs/equipo/CONTRATO_UNIFICADO.md").read_text(encoding="utf-8")
    assert "EVIDENCIA_AUTORIZACION_DATOS_SINTETICOS.md" in contract
    assert "data_origin=synthetic" in contract


def test_sprint_status_reports_populated_synthetic_administration_without_calling_it_observed():
    status = (validator.ROOT / "docs/equipo/ESTADO_SPRINT1.md").read_text(encoding="utf-8")
    assert "5.133 usuarios" in status
    assert "5.133 sensores" in status
    assert "sintétic" in status.lower()
    assert "inventario físico" in status.lower()


def test_summarized_research_index_preserves_exact_historical_git_bytes():
    migration = json.loads((validator.ROOT / 'docs/decisiones/unified-v1.json').read_text())
    path = 'research/datasets/README.md'
    assert path in migration['historical_source_paths']
    original = subprocess.check_output(
        ['git', 'show', migration['historical_revision'] + ':' + path], cwd=validator.ROOT)
    manifest = validator.DATASETS / 'results/phase3/inputs_manifest.csv'
    with manifest.open(newline='') as stream:
        expected = next(row for row in csv.DictReader(stream) if row['path'] == 'README.md')
    assert hashlib.sha256(original).hexdigest() == expected['sha256']
    assert len(original) == int(expected['bytes'])
