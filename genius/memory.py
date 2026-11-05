"""Versioned scientific claims with conservative promotion and invalidation.

SQLite is the working index. Exported JSON is the portable, Git-reviewable record.
An internal audit is never described as external peer review.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .io import now, write_json, read_json, digest

STATES = {
    "established": "RESULTADO ESTABLECIDO",
    "proposal": "PROPUESTA",
    "conjecture": "CONJETURA",
    "evidence": "EVIDENCIA SIMBÓLICA O NUMÉRICA",
    "pending_audit": "DERIVACIÓN PENDIENTE DE AUDITORÍA",
    "proven": "DEMOSTRADO BAJO HIPÓTESIS EXPLÍCITAS",
    "formal": "VERIFICADO FORMALMENTE",
    "refuted": "REFUTADO",
    "review": "EN REVISIÓN",
}


class ScientificMemory:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY, revision INTEGER NOT NULL, status TEXT NOT NULL,
                data TEXT NOT NULL, updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS dependencies (
                claim_id TEXT NOT NULL REFERENCES claims(id),
                dependency_id TEXT NOT NULL REFERENCES claims(id),
                dependency_revision INTEGER NOT NULL,
                PRIMARY KEY(claim_id, dependency_id));
            CREATE TABLE IF NOT EXISTS history (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, claim_id TEXT NOT NULL,
                revision INTEGER NOT NULL, event TEXT NOT NULL, data TEXT NOT NULL,
                recorded TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audits (
                id TEXT PRIMARY KEY, claim_id TEXT NOT NULL REFERENCES claims(id),
                revision INTEGER NOT NULL, verdict TEXT NOT NULL,
                producer_execution TEXT NOT NULL, reviewer_execution TEXT NOT NULL,
                scope TEXT NOT NULL, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY, record_path TEXT NOT NULL, sha256 TEXT NOT NULL,
                role TEXT NOT NULL, backend TEXT NOT NULL);
        """)

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def get(self, claim_id: str) -> dict:
        row = self.db.execute("SELECT * FROM claims WHERE id=?", (claim_id,)).fetchone()
        if row is None:
            raise KeyError(claim_id)
        return {**json.loads(row["data"]), "id": row["id"], "revision": row["revision"],
                "status": row["status"], "status_label": STATES[row["status"]]}

    def _history(self, claim: dict, event: str) -> None:
        self.db.execute("INSERT INTO history(claim_id,revision,event,data,recorded) VALUES(?,?,?,?,?)",
                        (claim["id"], claim["revision"], event, json.dumps(claim), now()))

    def register_execution(self, path: str | Path) -> str:
        """Link an actual completion artifact; this is provenance, not a proof oracle."""
        path = Path(path).resolve()
        record = read_json(path)
        required = ("execution_id", "role", "backend")
        if not all(record.get(k) for k in required) or record.get("execution_status") != "completed":
            raise ValueError("Execution record must identify a completed execution, role and backend")
        with self.db:
            self.db.execute("INSERT INTO executions VALUES(?,?,?,?,?)",
                            (record["execution_id"], str(path), digest(path), record["role"], record["backend"]))
        return record["execution_id"]

    def _execution(self, execution_id: str) -> dict:
        row = self.db.execute("SELECT * FROM executions WHERE id=?", (execution_id,)).fetchone()
        if not row or not Path(row["record_path"]).is_file() or digest(row["record_path"]) != row["sha256"]:
            raise ValueError("Missing or changed completion record for execution")
        return dict(row)

    def add(self, claim: dict) -> dict:
        data = dict(claim)
        for key in ("id", "statement", "hypotheses", "sources", "artifacts", "dependencies"):
            if key not in data:
                raise ValueError(f"Missing claim field: {key}")
        if not isinstance(data["id"], str) or not data["id"].strip():
            raise ValueError("Claim ID must be a nonempty string")
        status = data.setdefault("status", "proposal")
        if status not in STATES or status in {"proven", "formal"}:
            raise ValueError("New claims cannot start as proven/formal; a recorded audit is required")
        if status == "established" and not data["sources"]:
            raise ValueError("Established claims need identified sources")
        if status in {"evidence", "refuted"} and not data["artifacts"]:
            raise ValueError("Evidence/refutation requires an artifact")
        if not all(isinstance(data[k], list) for k in ("hypotheses", "sources", "artifacts", "dependencies")):
            raise ValueError("Claim collections must be lists")
        if data["id"] in data["dependencies"]:
            raise ValueError("Circular dependency")
        deps = [self.get(key) for key in data["dependencies"]]
        if status in {"established", "evidence"} and any(d["status"] in {"review", "refuted"} for d in deps):
            raise ValueError("Unreliable dependency; record a proposal instead")
        data["revision"] = 1
        with self.db:
            self.db.execute("INSERT INTO claims VALUES(?,?,?,?,?)",
                            (data["id"], 1, status, json.dumps(data), now()))
            self.db.executemany("INSERT INTO dependencies VALUES(?,?,?)",
                                [(data["id"], d["id"], d["revision"]) for d in deps])
            self._history(data, "created")
        return self.get(data["id"])

    def audit(self, claim_id: str, *, audit_id: str, verdict: str,
              producer_execution: str, reviewer_execution: str, checks: dict,
              artifacts: list, scope: str = "internal", limitations: str = "") -> None:
        claim = self.get(claim_id)
        if not producer_execution or not reviewer_execution or producer_execution == reviewer_execution:
            raise ValueError("Audit requires distinct, identified executions")
        producer_record = self._execution(producer_execution)
        reviewer_record = self._execution(reviewer_execution)
        if producer_record["record_path"] == reviewer_record["record_path"] or reviewer_record["role"] != "audit":
            raise ValueError("Review must link a separate audit completion artifact")
        if verdict not in {"confirmed", "rejected", "incomplete"}:
            raise ValueError("Unknown audit verdict")
        if scope not in {"internal", "external"}:
            raise ValueError("Audit scope must be internal/external")
        required = {"statement", "hypotheses", "logic", "dependencies", "conventions", "limits", "physical_scope", "tool_scope"}
        if not required.issubset(checks) or not artifacts:
            raise ValueError("Audit must document every required check and its artifacts")
        if verdict == "confirmed" and not all(checks[k] is True for k in required):
            raise ValueError("Confirmation requires successful documented checks")
        if not all(Path(path).is_file() for path in artifacts):
            raise ValueError("Audit artifacts must exist")
        record = {"checks": checks, "artifacts": artifacts, "limitations": limitations,
                  "artifact_hashes": {str(p): digest(p) for p in artifacts},
                  "recorded": now(), "separation": "Distinct execution IDs; independence of model errors is not guaranteed"}
        with self.db:
            self.db.execute("INSERT INTO audits VALUES(?,?,?,?,?,?,?,?)",
                            (audit_id, claim_id, claim["revision"], verdict, producer_execution,
                             reviewer_execution, scope, json.dumps(record)))

    def promote(self, claim_id: str, status: str, *, audit_id: str,
                formal_verification: dict | None = None) -> dict:
        claim = self.get(claim_id)
        if status not in {"proven", "formal"} or claim["status"] != "pending_audit":
            raise ValueError("Only an audited pending derivation can become proven/formal")
        audit = self.db.execute("SELECT * FROM audits WHERE id=?", (audit_id,)).fetchone()
        if not audit or audit["claim_id"] != claim_id or audit["revision"] != claim["revision"] or audit["verdict"] != "confirmed":
            raise ValueError("No confirming audit for this exact claim revision")
        objections = self.db.execute("SELECT id FROM audits WHERE claim_id=? AND revision=? AND verdict!='confirmed'",
                                    (claim_id, claim["revision"])).fetchall()
        if objections:
            raise ValueError("Unresolved audit objection; revise and resubmit before promotion")
        self._execution(audit["producer_execution"])
        self._execution(audit["reviewer_execution"])
        for path, checksum in json.loads(audit["data"])["artifact_hashes"].items():
            if not Path(path).is_file() or digest(path) != checksum:
                raise ValueError("Audit evidence changed after review")
        for dep in claim["dependencies"]:
            if self.get(dep)["status"] in {"review", "refuted", "proposal", "conjecture", "pending_audit"}:
                raise ValueError("Unresolved dependency prevents promotion")
        if status == "formal":
            if not formal_verification or not all(formal_verification.get(k) for k in ("tool", "version", "files", "command", "log")):
                raise ValueError("Formal verification needs tool, version, files, command and log")
            if not all(Path(p).is_file() for p in [*formal_verification["files"], formal_verification["log"]]):
                raise ValueError("Formal verification files and log must exist")
            claim["formal_verification"] = formal_verification
        claim.update(status=status, audit_id=audit_id)
        with self.db:
            self.db.execute("UPDATE claims SET status=?,data=?,updated=? WHERE id=?",
                            (status, json.dumps(claim), now(), claim_id))
            self._history(claim, "promoted")
        return self.get(claim_id)

    def revise(self, claim_id: str, *, statement: str | None = None,
               hypotheses: list | None = None, sources: list | None = None,
               artifacts: list | None = None, reason: str) -> list[str]:
        """Invalidate the changed claim and its transitive dependents atomically.

        Dependencies are immutable for a claim ID. A different graph needs a new
        claim ID; this prevents cycles and preserves the original proof lineage.
        Refuted claims retain their negative status when an input changes.
        """
        if not reason.strip():
            raise ValueError("A revision needs a reason")
        root = self.get(claim_id)
        updates = {"statement": statement, "hypotheses": hypotheses, "sources": sources, "artifacts": artifacts}
        root.update({k: v for k, v in updates.items() if v is not None})
        affected = [row[0] for row in self.db.execute("""
            WITH RECURSIVE affected(id) AS (
                SELECT ? UNION SELECT d.claim_id FROM dependencies d JOIN affected a ON d.dependency_id=a.id)
            SELECT id FROM affected
        """, (claim_id,))]
        with self.db:
            for key in affected:
                claim = root if key == claim_id else self.get(key)
                claim["revision"] += 1
                if claim["status"] != "refuted":
                    claim["status"] = "review"
                claim["review_reason"] = reason
                self.db.execute("UPDATE claims SET revision=?,status=?,data=?,updated=? WHERE id=?",
                                (claim["revision"], claim["status"], json.dumps(claim), now(), key))
                self._history(claim, "dependency_changed" if key != claim_id else "revised")
        return affected

    def resubmit(self, claim_id: str, *, reason: str) -> dict:
        """Return a corrected, reviewed claim to the audit queue; never unrefute."""
        claim = self.get(claim_id)
        if claim["status"] != "review" or not reason.strip() or not claim["artifacts"]:
            raise ValueError("Resubmission needs a reviewed claim, reason and new evidence")
        if not all(Path(p).is_file() for p in claim["artifacts"]):
            raise ValueError("Resubmission artifacts must exist")
        claim.update(status="pending_audit", resubmission_reason=reason)
        with self.db:
            self.db.execute("UPDATE claims SET status=?,data=?,updated=? WHERE id=?",
                            (claim["status"], json.dumps(claim), now(), claim_id))
            self._history(claim, "resubmitted")
        return self.get(claim_id)

    def export(self, path: str | Path) -> dict[str, Any]:
        claims = [self.get(row[0]) for row in self.db.execute("SELECT id FROM claims ORDER BY id")]
        audits = [dict(row) for row in self.db.execute("SELECT * FROM audits ORDER BY id")]
        history = [dict(row) for row in self.db.execute("SELECT * FROM history ORDER BY sequence")]
        for item in audits + history:
            item["data"] = json.loads(item["data"])
        record = {"schema_version": "1.0", "states": STATES, "claims": claims,
                  "audits": audits, "history": history,
                  "executions": [dict(r) for r in self.db.execute("SELECT * FROM executions ORDER BY id")],
                  "limits": "Audit records are attestations with linked evidence, not automatic proof checking."}
        write_json(path, record)
        return record
