"""Broken documentation remains diagnosable even when repaired during a gate."""
import json
import os
from pathlib import Path

import pytest

import check_all
import family


def test_fresh_isolation_resolves_core_sibling_links(monkeypatch, tmp_path):
    root = tmp_path / "scenarios"
    root.mkdir()
    (root / "README.md").write_text("Scenario fixture\n")
    (root / "docs").mkdir()
    (root / "docs/acceptance.md").write_text("# Acceptance\n\n## Release checks\n")
    monkeypatch.setattr(family, "ROOT", root)
    monkeypatch.setattr(check_all, "ROOT", root)
    source = tmp_path / "releases/usdaeco-core"
    source.mkdir(parents=True)
    (source / "README.md").write_text("[acceptance](../usdaeco-scenarios/docs/acceptance.md)\n")
    (source / "docs").mkdir()
    (source / "docs/coverage.md").write_text(
        "[release checks](../../usdaeco-scenarios/docs/acceptance.md#release-checks)\n")
    family.run(["git", "init", "--quiet", source])
    family.run(["git", "add", "."], cwd=source)
    family.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Seed documentation"], cwd=source)
    family.run(["git", "tag", "v0.1.0"], cwd=source)
    report = {"core": {"revision": family.run(["git", "rev-parse", "HEAD"], cwd=source).strip()}}
    (root / "dependencies.json").write_text(json.dumps({"repos":{"core":{"ref":"v0.1.0","revision":report["core"]["revision"]}}}))
    monkeypatch.setenv("AECO_GIT_BASE", "https://example.invalid")
    monkeypatch.setenv("AECO_CORE_SOURCE", str(source))
    monkeypatch.setattr(family, "repos", lambda **kwargs: {"core": Path(os.environ["AECO_CORE_SOURCE"])})
    output = root / ".work"
    link = output / "sources/usdaeco-scenarios"

    def audit():
        assert link.is_symlink() and link.resolve() == root
        return report

    monkeypatch.setattr(family, "audit_sources", audit)
    assert not output.exists()
    assert family.isolate_sources(output) == report
    assert family.repos()["core"] == output / "sources/usdaeco-core"
    assert check_all.documentation_links(family.repos())[:2] == (True, "4/4 roots")
    target = link.readlink()
    assert family.isolate_sources(output) == report
    assert link.readlink() == target
    assert (source / "README.md").read_text().startswith("[acceptance]")


@pytest.mark.parametrize("entry", ["directory", "file", "wrong-link", "dangling-link", "loop"])
def test_isolation_refuses_conflicting_scenarios_entry(monkeypatch, tmp_path, entry):
    monkeypatch.setattr(family, "ROOT", tmp_path)
    output = tmp_path / ".work"
    link = output / "sources/usdaeco-scenarios"
    link.parent.mkdir(parents=True)
    if entry == "directory":
        link.mkdir()
    elif entry == "file":
        link.write_text("caller-owned\n")
    else:
        target = tmp_path / "other"
        if entry == "wrong-link":
            target.mkdir()
        elif entry == "loop":
            target = link
        link.symlink_to(target, target_is_directory=True)
    before = link.lstat()

    def unexpected_audit():
        pytest.fail("Conflicting layouts must be refused before source auditing")

    monkeypatch.setattr(family, "audit_sources", unexpected_audit)
    with pytest.raises(RuntimeError, match="Family layout conflict: sources/usdaeco-scenarios"):
        family.isolate_sources(output)
    assert link.lstat() == before


def test_link_failure_details_survive_later_repair(monkeypatch, tmp_path):
    monkeypatch.setattr(check_all, "ROOT", tmp_path)
    source = tmp_path / ".work/sources/usdaeco-core"
    source.mkdir(parents=True)
    (tmp_path / "README.md").write_text("[missing](missing.md)\n")
    (source / "README.md").write_text("[sibling](../usdaeco-scenarios/README.md)\n")
    paths = {"core": source}
    before, before_detail, before_checks = check_all.documentation_links(paths)
    assert not before and before_detail.startswith("0/2 roots; ")
    assert "usdaeco-scenarios/README.md: missing.md" in before_detail
    assert "usdaeco-core/README.md: ../usdaeco-scenarios/README.md" in before_detail
    assert str(tmp_path) not in before_detail

    (tmp_path / "missing.md").touch()
    (source.parent / "usdaeco-scenarios").symlink_to(tmp_path, target_is_directory=True)
    after, after_detail, after_checks = check_all.documentation_links(paths)
    assert after and after_detail == "2/2 roots"
    rows = [dict(gate="links before builds", passed=before, status="FAIL",
                 result=before_detail, evidence=before_checks),
            dict(gate="links at end", passed=after, status="PASS",
                 result=after_detail, evidence=after_checks)]
    saved = json.loads(json.dumps(rows))
    assert all(not root["passed"] for root in saved[0]["evidence"])
    assert all(root["passed"] for root in saved[1]["evidence"])
    assert any(row["status"] == "FAIL" for row in saved)
    table = check_all.acceptance_table(saved)
    assert "usdaeco-scenarios/README.md: missing.md" in table
    assert "usdaeco-core/README.md: ../usdaeco-scenarios/README.md" in table
    assert "| links at end | 2/2 roots | PASS |" in table


def test_link_with_table_delimiter_keeps_its_diagnostic(monkeypatch, tmp_path):
    monkeypatch.setattr(check_all, "ROOT", tmp_path)
    (tmp_path / "README.md").write_text("[missing](missing|file.md)\n")
    passed, detail, _ = check_all.documentation_links({})
    assert not passed and "README.md: missing|file.md" in detail
    table = check_all.acceptance_table([
        dict(gate="links before builds", result=detail, status="FAIL")])
    assert "README.md: missing\\|file.md" in table
