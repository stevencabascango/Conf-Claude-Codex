"""Sealed two-provider development and cross-review, with retained disagreements."""
from __future__ import annotations

from pathlib import Path
import shutil
import hashlib
import json

from .io import digest, now, read_json, write_json
from .planning import compare_reports


def _provider(provider: str):
    if provider not in {"claude", "codex"}:
        raise ValueError("Provider must be claude/codex")


def _load(root: Path) -> dict:
    manifest = read_json(root / "comparison.json")
    for provider in ("claude", "codex"):
        brief = read_json(root / provider / "brief.json")
        actual = hashlib.sha256(json.dumps(brief, sort_keys=True).encode()).hexdigest()
        if actual != manifest["brief_sha256"]:
            raise ValueError("A common brief changed after preparation; create a new comparison")
    for provider, record in manifest.get("reports", {}).items():
        if digest(root / record["path"]) != record["sha256"]:
            raise ValueError(f"Sealed {provider} report changed; create a new comparison")
    for provider, record in manifest.get("cross_reviews", {}).items():
        if isinstance(record, dict) and digest(root / record["path"]) != record["sha256"]:
            raise ValueError(f"Sealed {provider} review changed")
    return manifest


def seal_report(root: str | Path, provider: str, source: str | Path) -> dict:
    _provider(provider)
    root = Path(root).resolve()
    manifest = _load(root)
    if manifest["phase"] != "independent-development" or provider in manifest["reports"]:
        raise ValueError("This phase/report is already sealed")
    report = read_json(source)
    if report.get("status") != "completed" or not all(key in report for key in ("claims", "execution_id", "tools", "model")):
        raise ValueError("Completed report must record claims, execution ID, actual tools and model (null if unreported)")
    if not report["execution_id"] or not isinstance(report["claims"], list):
        raise ValueError("Invalid completed report")
    target = root / provider / "report.json"
    if target.exists():
        raise ValueError("Report artifact exists; will not overwrite it")
    write_json(target, report)
    manifest["reports"][provider] = {"path": str(target.relative_to(root)), "sha256": digest(target),
                                      "execution_id": report["execution_id"], "sealed": now()}
    manifest["status"] = "both_reports_sealed" if len(manifest["reports"]) == 2 else "pending"
    write_json(root / "comparison.json", manifest)
    return manifest


def prepare_cross_review(root: str | Path) -> dict:
    root = Path(root).resolve()
    manifest = _load(root)
    if set(manifest["reports"]) != {"claude", "codex"}:
        return {"status": "pending", "missing_reports": sorted({"claude", "codex"} - set(manifest["reports"]))}
    if manifest["phase"] != "independent-development":
        raise ValueError("Cross-review already prepared")
    reports = {name: read_json(root / entry["path"]) for name, entry in manifest["reports"].items()}
    if reports["claude"]["execution_id"] == reports["codex"]["execution_id"]:
        raise ValueError("Separate development requires distinct execution identifiers")
    for provider, peer in (("claude", "codex"), ("codex", "claude")):
        review_dir = root / "peer_review" / provider
        if review_dir.exists():
            raise ValueError("Cross-review workspace already exists; preserve its evidence")
        write_json(review_dir / "peer_report.json", reports[peer])
        shutil.copy2(root / provider / "brief.json", review_dir / "brief.json")
        (review_dir / "TASK.md").write_text(
            f"Review the sealed {peer} report in a NEW {provider} execution.\n"
            "Reconstruct central arguments, test hypotheses/dependencies and limits, search for counterexamples, "
            "and record each claim's verdict, evidence and remaining disagreement. "
            "Apply Protocols A/B when relevant. Do not treat agreement as proof. "
            "Record execution_id, actual model (null if unreported), tools and budget. "
            "Return status=completed, reviewed_claims (id/verdict/reconstruction/evidence), disagreements and next_checks.\n")
    manifest.update(phase="cross-review", status="pending_cross_reviews", cross_reviews={})
    write_json(root / "comparison.json", manifest)
    return manifest


def seal_review(root: str | Path, provider: str, source: str | Path) -> dict:
    _provider(provider)
    root = Path(root).resolve()
    manifest = _load(root)
    if manifest["phase"] != "cross-review" or provider in manifest["cross_reviews"]:
        raise ValueError("Review must be a new artifact in the cross-review phase")
    review = read_json(source)
    required = {"execution_id", "model", "tools", "reviewed_claims", "disagreements", "next_checks"}
    if review.get("status") != "completed" or not required.issubset(review):
        raise ValueError("Cross-review report is incomplete")
    if not review["execution_id"] or review["execution_id"] in {r["execution_id"] for r in manifest["reports"].values()}:
        raise ValueError("Cross-review needs a distinct execution")
    if review["execution_id"] in {r["execution_id"] for r in manifest["cross_reviews"].values()}:
        raise ValueError("The two cross-reviews require distinct executions")
    if not isinstance(review["reviewed_claims"], list) or not review["reviewed_claims"]:
        raise ValueError("Cross-review must reconstruct at least one identified claim")
    for claim in review["reviewed_claims"]:
        if not all(claim.get(k) for k in ("id", "verdict", "reconstruction", "evidence")):
            raise ValueError("Every reviewed claim needs ID, verdict, reconstruction and evidence")
    target = root / "peer_review" / provider / "review.json"
    if target.exists():
        raise ValueError("Will not overwrite a review artifact")
    write_json(target, review)
    manifest["cross_reviews"][provider] = {"path": str(target.relative_to(root)), "sha256": digest(target),
                                          "execution_id": review["execution_id"], "sealed": now()}
    write_json(root / "comparison.json", manifest)
    return manifest


def synthesize(root: str | Path) -> dict:
    root = Path(root).resolve()
    manifest = _load(root)
    reports = {provider: read_json(root / record["path"]) for provider, record in manifest.get("reports", {}).items()}
    base = compare_reports(reports.get("claude"), reports.get("codex"))
    reviews = manifest.get("cross_reviews", {})
    if len(reviews) < 2:
        return {**base, "status": "pending", "missing_cross_reviews": sorted({"claude", "codex"} - set(reviews)),
                "scientific_promotion": "none"}
    review_reports = {p: read_json(root / r["path"]) for p, r in reviews.items()}
    disagreements = list(base["disagreements"])
    for provider, report in review_reports.items():
        disagreements.extend({"reviewer": provider, "disagreement": item} for item in report["disagreements"])
    result = {**base, "status": "cross_reviewed_with_open_disagreements" if disagreements else "internally_cross_reviewed",
              "disagreements": disagreements, "review_reports": review_reports,
              "cross_reviews": {p: "completed" for p in reviews}, "scientific_promotion": "none",
              "limits": "Internal review with shared-model risks; promotion still needs claim-specific recorded audit."}
    write_json(root / "synthesis.json", result)
    return result
