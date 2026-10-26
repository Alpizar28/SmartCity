"""Validate Phase 6 documentation without network, services or historical writes.

Python standard library only. Full private-evidence verification is optional;
a clean clone can validate its public documents without claiming data replay.
Secret scanning is pattern-based and never prints a matched secret value.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[3]
DATASETS = ROOT / "research/datasets"
OUT = DATASETS / "results/phase6"
REPORTS = {OUT / n for n in ("validation.json", "candidate_inventory.csv", "outputs_manifest.csv")}
EXPECTED_DOCS = [
    "docs/README.md", "docs/academico/texto_para_informe.md", "docs/academico/uso_ia.md",
    "docs/datasets/seleccion_dataset.md", "docs/datasets/fuentes_y_procedencia.md",
    "docs/datasets/calidad_y_limitaciones.md", "docs/datasets/indice_evidencias.md",
    "docs/arquitectura/modelos.md", "docs/arquitectura/pipeline.md",
    "docs/arquitectura/diagramas.md", "docs/equipo/preguntas_profesor.md",
    "docs/equipo/ESTADO_SPRINT1.md", "CONTRATO_PROVISIONAL_DATASET.md",
    "PREGUNTAS_PROFESOR.md",
    "docs/equipo/guia_integrantes.md", "docs/equipo/revision_repositorio.md",
    "docs/decisiones/ADR-001-madrid.md",
]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main_revision():
    # A clone checking out the docs branch usually has origin/main, not local main.
    for reference in ("refs/heads/main", "refs/remotes/origin/main"):
        result = subprocess.run(["git", "rev-parse", "--verify", reference], cwd=ROOT,
                                capture_output=True, text=True)
        if result.returncode == 0:
            return reference, result.stdout.strip()
    raise RuntimeError("Cannot verify main: neither local main nor origin/main exists")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def unfenced(text):
    return re.sub(r"^```[^\n]*\n.*?^```\s*$", "", text, flags=re.M | re.S)


def anchors(text):
    found, seen = set(), {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", unfenced(text), re.M):
        heading = heading.replace("`", "").lower()
        slug = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        found.add(slug if not count else f"{slug}-{count}")
    found.update(re.findall(r'(?:id|name)=["\']([^"\']+)["\']', text))
    return found


def validate_links(files, failures):
    checked, external, local_only = 0, set(), []
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        text = unfenced(path.read_text())
        targets = re.findall(r"!?\[[^\]\n]*\]\(([^\s]+?)(?:\s+[\"\'][^\n]*?[\"\'])?\)", text)
        targets += re.findall(r"^\[[^\]]+\]:\s*(\S+)", text, re.M)
        definitions = {x.lower() for x in re.findall(r"^\[([^\]]+)\]:", text, re.M)}
        for _, key in re.findall(r"\[([^\]\n]+)\]\[([^\]\n]+)\]", text):
            if key.lower() not in definitions:
                failures.append(f"Undefined reference {path.relative_to(ROOT)}: {key}")
        for raw in targets:
            target = unquote(raw.strip("<>"))
            parts = urlsplit(target)
            if parts.scheme or target.startswith("//"):
                external.add(target)
                continue
            checked += 1
            dest = (ROOT / parts.path.lstrip("/")) if parts.path.startswith("/") else path.parent / parts.path
            if not parts.path:
                dest = path
            dest = dest.resolve()
            try:
                dest.relative_to(ROOT)
            except ValueError:
                failures.append(f"Link outside repository: {path.relative_to(ROOT)} -> {raw}")
                continue
            if not dest.exists():
                failures.append(f"Missing link: {path.relative_to(ROOT)} -> {raw}")
            elif parts.fragment and dest.suffix.lower() == ".md" and parts.fragment not in anchors(dest.read_text()):
                failures.append(f"Missing anchor: {path.relative_to(ROOT)} -> {raw}")
            if dest.is_file():
                ignored = subprocess.run(["git", "check-ignore", "--no-index", "-q", str(dest.relative_to(ROOT))], cwd=ROOT)
                if ignored.returncode == 0:
                    local_only.append({"from": str(path.relative_to(ROOT)), "to": str(dest.relative_to(ROOT))})
    return {"internal_checked": checked, "external_references": len(external),
            "external_live_requests": 0, "scope": "Markdown inline and reference links in candidate files",
            "local_only_links": local_only}


def secret_findings(files):
    patterns = {
        "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
        "aws_access_key": r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
        "github_token": r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b",
        "slack_token": r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b",
        "api_secret": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b",
        "credential_uri": r"\b(?:postgres(?:ql)?|mongodb(?:\+srv)?|https?)://[^\s/@:]+:[^\s/@]+@",
        "jwt": r"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\b",
    }
    findings, placeholders = [], []
    assignment = re.compile(r"(?i)\b(?:password|passwd|secret|api_key|access_token|private_key|\w+_password)\s*[=:]\s*[\"\']?([^\s\"\',;]+)")
    for path in files:
        try:
            text = path.read_text()
        except UnicodeError:
            continue
        for label, pattern in patterns.items():
            for match in re.finditer(pattern, text):
                findings.append({"path": str(path.relative_to(ROOT)), "line": text[:match.start()].count("\n") + 1,
                                 "pattern": label})
        for line_no, line in enumerate(text.splitlines(), 1):
            for match in assignment.finditer(line):
                value = match.group(1)
                if any(s in value.lower() for s in ("change", "replace", "example", "placeholder")) or value.startswith(("$", "{", "<")):
                    placeholders.append({"path": str(path.relative_to(ROOT)), "line": line_no})
                else:
                    findings.append({"path": str(path.relative_to(ROOT)), "line": line_no, "pattern": "credential_assignment"})
    return {"method": "bounded static regex scan; not proof of absence or history audit",
            "candidate_files_scanned": len(files), "findings": findings,
            "placeholders_or_variables": placeholders}


def validate_model(failures):
    sql = (DATASETS / "scripts/phase5_postgresql.sql").read_text()
    tables = re.findall(r"CREATE TABLE (\w+)\(", sql)
    fks = set()
    for table, body in re.findall(r"CREATE TABLE (\w+)\((.*?)\);", sql, re.S):
        for column, rest, parent in re.findall(r"(?:^|,)\s*(\w+)\s+\w+([^,]*?)\bREFERENCES\s+(\w+)", body):
            fks.add((parent, table, "||" if "NOT NULL" in rest else "o|"))
    diagram = (ROOT / "docs/arquitectura/diagramas.md").read_text()
    er = re.search(r"```mermaid\nerDiagram\n(.*?)\n```", diagram, re.S).group(1)
    entities = set(re.findall(r"^\s+(\w+)\s+\{", er, re.M))
    edges = set(re.findall(r"^\s+(\w+)\s+(\|\||o\|)\.\.o\{\s+(\w+)\s*:", er, re.M))
    represented = {(parent, child, nullable) for parent, nullable, child in edges}
    if entities != set(tables):
        failures.append("ER entities differ from CREATE TABLE names")
    if represented != fks:
        failures.append(f"ER FK/cardinality mismatch: {sorted(represented ^ fks)}")
    count = diagram.count("```mermaid")
    if count != 5 or len(tables) != 12:
        failures.append("Expected five diagrams and twelve SQL tables")
    return {"sql_tables": len(tables), "ddl_foreign_keys": len(fks), "er_relationships": len(represented),
            "mermaid_blocks": count, "fk_and_nullability_match": represented == fks,
            "validation": "text structure and exact DDL topology; no Mermaid parser/render or visual test"}


def check_ignores(failures):
    ignored = [".env", ".env.production", "data/probe.csv", "raw/probe.csv",
               "research/datasets/raw/probe.bin", "research/datasets/private_results/probe.csv",
               "research/datasets/.venv/probe", "volumes/probe", "tmp/probe", "probe.dump",
               "probe.sqlite", "probe.parquet", "probe.key", "probe.log",
               "research/datasets/results/phase4/E_original.txt"]
    kept = [".env.example", "data/.gitkeep", "research/datasets/.gitignore",
            "research/datasets/05_data_dictionary.csv", "research/datasets/04_scores.csv",
            "research/datasets/00_query_matrix.csv", "research/datasets/scripts/phase5_postgresql.sql",
            "research/datasets/scripts/phase5_prepare.py", "research/datasets/results/phase5/mongodb_server.log"]
    for expected, paths in ((True, ignored), (False, kept)):
        for name in paths:
            result = subprocess.run(["git", "check-ignore", "--no-index", "-q", name], cwd=ROOT)
            if (result.returncode == 0) != expected:
                failures.append(f"Ignore expectation failed: {name}")
    return {"ignored_probes": len(ignored), "versionable_probes": len(kept)}


def verify_metrics(failures):
    prep = json.loads((DATASETS / "results/phase5/preparation.json").read_text())
    counts = {k: v["effective_documents"] for k, v in prep["counts"].items()}
    if counts != {"MAD-AIR": 91959, "MAD-METEO": 66005, "MAD-TRAFFIC": 674704} or sum(counts.values()) != 832668:
        failures.append("Core counts do not match documented values")
    rows = list(csv.DictReader((DATASETS / "04_scores.csv").open()))
    totals = {r["alternative"]: Decimal(r["score_points"]) for r in rows if r["criterion_id"] == "TOTAL"}
    expected = {"Madrid": Decimal("63.665"), "London": Decimal("49.345"), "NYC": Decimal("46.345")}
    if totals != expected:
        failures.append("Scores differ from historical Phase 4 values")
    for city, total in totals.items():
        if sum(Decimal(r["score_points"]) for r in rows if r["alternative"] == city and r["criterion_id"] != "TOTAL") != total:
            failures.append(f"Score subcriteria sum mismatch: {city}")
    sources = list(csv.DictReader((DATASETS / "01_sources_catalog.csv").open()))
    dictionary = list(csv.DictReader((DATASETS / "05_data_dictionary.csv").open()))
    if len(sources) != 30 or len(dictionary) != 75:
        failures.append("Catalog or dictionary count mismatch")
    for name in ("postgresql_sample.json", "mongodb_execution.json"):
        native = json.loads((DATASETS / "results/phase5" / name).read_text())
        if not all(native[k] for k in ("native_executed", "container_removed", "anonymous_volumes_removed")):
            failures.append(f"Native evidence/cleanup missing: {name}")
        size = native.get("sample_size", native.get("counts", {}).get("observations"))
        if size != 5000:
            failures.append(f"Native sample count mismatch: {name}")
    return {"eligible_by_source": counts, "eligible_total": sum(counts.values()),
            "planning_scores": {k: str(v) for k, v in totals.items()},
            "catalog_sources": len(sources), "dictionary_entries": len(dictionary),
            "native_samples": 5000, "native_evidence_mode": "historical results verified, engines not rerun"}


def verify_baseline(path, failures):
    before = json.loads(path.read_text())
    permitted = {"README.md", ".gitignore", "docs/README.md"}
    checked, changed = 0, []
    for name, sha in before["files"].items():
        p = ROOT / name
        checked += 1
        if not p.is_file() or digest(p) != sha:
            changed.append(name)
            if name not in permitted:
                failures.append(f"Unexpected prior-file change: {name}")
    _, current_main = main_revision()
    if current_main != before["main"] or git("rev-parse", "HEAD") != before["head"]:
        failures.append("main or HEAD moved since baseline")
    return {"prior_files_checked": checked, "changed_prior_files": changed,
            "main_unchanged": current_main == before["main"],
            "head_unchanged": git("rev-parse", "HEAD") == before["head"],
            "compose_unchanged": "compose.yaml" not in changed}


def verify_private_evidence(required, failures):
    checked, missing = 0, []
    migration = json.loads((ROOT/'docs/decisiones/unified-v1.json').read_text())
    migrated = set(migration['historical_source_paths'])
    archived_sources = []
    for phase in (3, 4, 5):
        names = ["outputs_manifest.csv"] + (["inputs_manifest.csv"] if phase == 3 else [])
        for name in names:
            for row in csv.DictReader((DATASETS / f"results/phase{phase}" / name).open()):
                path = DATASETS / row["path"]
                relative = str(path.relative_to(ROOT))
                if relative in migrated:
                    original = subprocess.run(['git','show',migration['historical_revision']+':'+relative],
                                              cwd=ROOT, capture_output=True)
                    if original.returncode or hashlib.sha256(original.stdout).hexdigest() != row['sha256']:
                        failures.append(f'Historical Git source mismatch or unavailable: {relative}')
                    else:
                        checked += 1
                        archived_sources.append(relative)
                    continue
                if not path.exists():
                    missing.append(str(path.relative_to(ROOT)))
                else:
                    checked += 1
                    if digest(path) != row["sha256"]:
                        failures.append(f"Historical hash mismatch: {path.relative_to(ROOT)}")
    if required and missing:
        failures.append(f"Missing {len(missing)} historical/private manifest paths")
    return {"manifest_entries_verified": checked, "missing_local_inputs": sorted(set(missing)),
            "migrated_source_verification": "original Git bytes at recorded pre-migration revision; not current source",
            "migrated_sources_verified": archived_sources,
            "require_local_evidence": required, "missing_inputs_are_not_data_replay_success": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, help="Optional pre-edit local snapshot")
    parser.add_argument("--require-local-evidence", action="store_true")
    args = parser.parse_args()
    failures = []
    OUT.mkdir(parents=True, exist_ok=True)
    names = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).decode().split("\0")
    files = sorted({ROOT / n for n in names if n and (ROOT / n).is_file()} - REPORTS)
    for name in EXPECTED_DOCS:
        if not (ROOT / name).is_file():
            failures.append(f"Required documentation missing: {name}")
    # Documentation integrity is branch-independent. This permits maintenance branches
    # to validate a proposed consolidation before it is merged into main.
    if git("diff", "--", "compose.yaml", ".env.example", "postgres", "mongodb"):
        failures.append("Protected infrastructure diff detected")
    if git("diff", "--cached", "--name-only"):
        failures.append("Staged changes detected; Phase 6 prepares no staging")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    for path in files:
        if path.suffix in (".md", ".py", ".js", ".sql") and (path.is_relative_to(ROOT / "docs") or path.name == "phase6_validate_docs.py" or path == ROOT / "README.md"):
            for n, line in enumerate(path.read_text().splitlines(), 1):
                if line != line.rstrip() or re.match(r"^(<<<<<<< |=======|>>>>>>> )", line):
                    failures.append(f"Whitespace/conflict: {path.relative_to(ROOT)}:{n}")
    main_reference, main_commit = main_revision()
    report = {"phase": 6, "branch": git("branch", "--show-current"), "main_commit": main_commit,
              "main_reference": main_reference,
              "remote_configured": git("remote", "get-url", "origin"), "network_requests": 0,
              "services_started": 0, "historical_outputs_regenerated": False,
              "required_documents": len(EXPECTED_DOCS), "candidate_inputs": len(files),
              "inventory_scope": "tracked and nonignored untracked files, excluding this validator's three generated reports"}
    report["links"] = validate_links(files, failures)
    report["metrics"] = verify_metrics(failures)
    report["diagrams"] = validate_model(failures)
    report["ignore_rules"] = check_ignores(failures)
    report["secrets"] = secret_findings(files)
    if report["secrets"]["findings"]:
        failures.append("Potential secrets need manual review (values redacted)")
    large = [str(p.relative_to(ROOT)) for p in files if p.stat().st_size > 1024 * 1024]
    report["candidate_files_over_1_MiB"] = large
    if large:
        failures.append("Large candidate files require review")
    # Script references in the new runnable docs; no shell execution of examples.
    refs = set()
    for name in ["README.md", *EXPECTED_DOCS]:
        text = (ROOT / name).read_text()
        refs.update(re.findall(r"(?:\b|/)scripts/([\w.-]+\.(?:py|sql|js|lock))", text))
    for name in refs:
        if not (DATASETS / "scripts" / name).is_file():
            failures.append(f"Documented script missing: {name}")
    report["documented_script_paths_checked"] = sorted(refs)
    suites = list(ET.parse(OUT / "tests.xml").getroot().iter("testsuite")) if (OUT / "tests.xml").exists() else []
    report["phase6_tests"] = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    if suites and any(report["phase6_tests"][k] for k in ("failures", "errors", "skipped")):
        failures.append("Phase 6 test JUnit contains failures/errors/skips")
    report["historical_manifests"] = verify_private_evidence(args.require_local_evidence, failures)
    if args.baseline:
        report["baseline"] = verify_baseline(args.baseline, failures)
    report["failures"] = failures
    report["all_checks_passed"] = not failures
    with (OUT / "candidate_inventory.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        for p in files:
            writer.writerow({"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": digest(p)})
    (OUT / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    produced = [ROOT / "README.md", ROOT / ".gitignore", *[ROOT / p for p in EXPECTED_DOCS],
                Path(__file__).resolve(), OUT / "tests.xml", OUT / "validation.json", OUT / "candidate_inventory.csv"]
    with (OUT / "outputs_manifest.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        for p in sorted(set(produced)):
            if p.exists():
                writer.writerow({"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": digest(p)})
    print(json.dumps({k: report[k] for k in ("branch", "all_checks_passed", "links", "diagrams", "phase6_tests", "failures")}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
