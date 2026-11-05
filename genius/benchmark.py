"""Exact finite-dimensional Hodge benchmark, with a deliberately false claim.

This backend executes deterministic Python code, never a simulated language model.
The producer and audit implementations use different constructions of the matrix.
They still share a codebase and are not an external scientific review.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import json
import uuid

BASIS = list(combinations(range(1, 5), 2))
CONVENTIONS = {
    "space": "Lambda^2((R^4)^*)", "metric": "diag(+1,+1,+1,+1)",
    "signature": "Euclidean", "orientation": "e1 wedge e2 wedge e3 wedge e4 positive",
    "basis": [list(pair) for pair in BASIS], "field": "real; exact rational matrix entries",
    "definition": "alpha wedge *beta = <alpha,beta> vol",
    "regime": "single oriented inner-product vector space; no field equations",
    "units": "dimensionless linear algebra in an orthonormal coframe",
}
FALSE_STATEMENT = "*^2 = -I on real Euclidean two-forms in dimension four"
IDENTITY_STATEMENT = "*^2 = I on Lambda^2((R^4)^*) for the declared Euclidean metric"
DIMENSION_STATEMENT = "The real +1 and -1 eigenspaces each have dimension three"


def _parity(sequence):
    return (-1) ** sum(sequence[i] > sequence[j]
                       for i in range(len(sequence)) for j in range(i + 1, len(sequence)))


def hodge_matrix():
    """Columns are the stars of the six ordered basis elements."""
    matrix = [[0] * 6 for _ in range(6)]
    for column, pair in enumerate(BASIS):
        complement = tuple(index for index in range(1, 5) if index not in pair)
        matrix[BASIS.index(complement)][column] = _parity(pair + complement)
    return matrix


def _audit_matrix():
    # Independent construction: solve alpha wedge *beta = delta(alpha,beta) vol
    # using the wedge-pairing matrix and exact Gaussian elimination.
    wedge = [[0] * 6 for _ in range(6)]
    for row, alpha in enumerate(BASIS):
        for column, beta in enumerate(BASIS):
            sequence = alpha + beta
            if len(set(sequence)) == 4:
                # Compute permutation sign by determinant of its permutation matrix.
                permutation = [[int(sequence[j] == i + 1) for j in range(4)]
                               for i in range(4)]
                determinant = Fraction(1)
                for pivot in range(4):
                    found = next((r for r in range(pivot, 4) if permutation[r][pivot]), None)
                    if found is None:
                        determinant = Fraction(0)
                        break
                    if found != pivot:
                        permutation[pivot], permutation[found] = permutation[found], permutation[pivot]
                        determinant *= -1
                    value = permutation[pivot][pivot]
                    determinant *= value
                    permutation[pivot] = [Fraction(x, value) for x in permutation[pivot]]
                    for r in range(pivot + 1, 4):
                        multiplier = permutation[r][pivot]
                        permutation[r] = [x - multiplier * y for x, y in zip(permutation[r], permutation[pivot])]
                wedge[row][column] = determinant
    augmented = [[Fraction(x) for x in row] + [Fraction(i == j) for j in range(6)]
                 for i, row in enumerate(wedge)]
    for pivot in range(6):
        found = next(r for r in range(pivot, 6) if augmented[r][pivot])
        augmented[pivot], augmented[found] = augmented[found], augmented[pivot]
        value = augmented[pivot][pivot]
        augmented[pivot] = [x / value for x in augmented[pivot]]
        for row in range(6):
            if row != pivot:
                multiplier = augmented[row][pivot]
                augmented[row] = [x - multiplier * y for x, y in zip(augmented[row], augmented[pivot])]
    return [[int(x) for x in row[6:]] for row in augmented]


def _multiply(left, right):
    return [[sum(Fraction(left[i][k]) * Fraction(right[k][j]) for k in range(len(right)))
             for j in range(len(right[0]))] for i in range(len(left))]


def _rank(matrix):
    rows = [[Fraction(x) for x in row] for row in matrix]
    rank = 0
    for column in range(len(rows[0])):
        found = next((r for r in range(rank, len(rows)) if rows[r][column]), None)
        if found is None:
            continue
        rows[rank], rows[found] = rows[found], rows[rank]
        value = rows[rank][column]
        rows[rank] = [x / value for x in rows[rank]]
        for row in range(len(rows)):
            if row != rank:
                multiplier = rows[row][column]
                rows[row] = [x - multiplier * y for x, y in zip(rows[row], rows[rank])]
        rank += 1
    return rank


def compute():
    matrix = hodge_matrix()
    square = _multiply(matrix, matrix)
    identity = [[int(i == j) for j in range(6)] for i in range(6)]
    plus_projector = [[(Fraction(matrix[i][j]) + identity[i][j]) / 2 for j in range(6)] for i in range(6)]
    minus_projector = [[(identity[i][j] - Fraction(matrix[i][j])) / 2 for j in range(6)] for i in range(6)]
    return {"matrix": matrix, "basis": deepcopy(CONVENTIONS["basis"]),
            "square": [[int(x) for x in row] for row in square],
            "square_is_identity": square == identity,
            "self_dual_dimension": _rank(plus_projector),
            "anti_self_dual_dimension": _rank(minus_projector),
            "counterexample": {"input": "e1 wedge e2", "star": "e3 wedge e4",
                               "star_twice": "e1 wedge e2", "false_prediction": "-e1 wedge e2",
                               "difference_coefficient": 2},
            "arithmetic": "fractions.Fraction; no floating-point tolerance"}


def _read_inputs(value, _seen_paths=None):
    """Traverse structured inputs; read only explicit JSON paths."""
    if _seen_paths is None:
        _seen_paths = set()
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _read_inputs(child, _seen_paths)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _read_inputs(child, _seen_paths)
    elif isinstance(value, (str, Path)):
        path = Path(value)
        try:
            if path.suffix == ".json" and path.is_file() and path.resolve() not in _seen_paths:
                _seen_paths.add(path.resolve())
                yield from _read_inputs(json.loads(path.read_text(encoding="utf-8")), _seen_paths)
        except (OSError, ValueError):
            return


def _claim(identifier, statement, status, evidence):
    return {"id": identifier, "statement": statement, "status": status,
            "hypotheses": deepcopy(CONVENTIONS), "evidence": evidence,
            "review_kind": "internal; separate execution required for promotion"}


def _producer_verdict(producer, independent, square):
    """Check one complete execution, including its claims' attached evidence."""
    evidence = producer.get("evidence")
    checks = {
        "execution_identity": isinstance(producer.get("execution_id"), str) and bool(producer["execution_id"]),
        "conventions": producer.get("conventions") == CONVENTIONS,
        "evidence_present": isinstance(evidence, dict),
    }
    evidence = evidence if isinstance(evidence, dict) else {}
    checks.update({"matrix": evidence.get("matrix") == independent,
                   "basis": evidence.get("basis") == CONVENTIONS["basis"],
                   "square": evidence.get("square") == square,
                   "square_is_identity": evidence.get("square_is_identity") is True,
                   "self_dual_dimension": evidence.get("self_dual_dimension") == 3,
                   "anti_self_dual_dimension": evidence.get("anti_self_dual_dimension") == 3})
    claims = producer.get("claims")
    checks["claims_present"] = isinstance(claims, list) and bool(claims)
    expected = {"HODGE-E4-001": (IDENTITY_STATEMENT, evidence),
                "HODGE-E4-002": (DIMENSION_STATEMENT, {"plus": 3, "minus": 3})}
    if isinstance(claims, list):
        for identifier, (statement, expected_evidence) in expected.items():
            matches = [claim for claim in claims if isinstance(claim, dict) and claim.get("id") == identifier]
            checks[f"claim_{identifier}"] = bool(matches) and all(
                claim.get("statement") == statement and claim.get("hypotheses") == CONVENTIONS
                and claim.get("evidence") == expected_evidence for claim in matches)
        checks["no_unknown_claims"] = all(isinstance(claim, dict) and claim.get("id") in expected for claim in claims)
    passed = all(checks.values())
    return {"execution_id": producer.get("execution_id"), "role": producer.get("role"),
            "checks": checks, "failed_checks": [name for name, passed in checks.items() if not passed],
            "verdict": "CONFIRMED_FINITE_FIXTURE" if passed else "REJECTED"}


def execute(task: dict) -> dict:
    """Execute one known reference role; this is not general research intelligence."""
    role = task.get("role")
    roles = {"conceptual", "mathematics", "physics", "computation", "counterexample", "audit", "integration"}
    if role not in roles:
        raise ValueError(f"Unsupported benchmark role: {role}")
    result = {"backend": "deterministic-reference", "role": role,
              "execution_id": str(uuid.uuid4()), "conventions": deepcopy(CONVENTIONS),
              "model": None, "tools": ["Python standard library", "fractions.Fraction"],
              "claims": [], "artifacts": [],
              "limitations": ["Known finite-dimensional fixture; not an LLM research run.",
                              "Shared source code limits independence of internal checking.",
                              "No Einstein equations or Googly solution follows from this calculation."]}
    if role in {"mathematics", "computation"}:
        evidence = compute()
        result.update(summary="Exact six-dimensional Hodge-star calculation completed.", evidence=evidence)
        result["claims"] = [_claim("HODGE-E4-001", IDENTITY_STATEMENT,
                                   "EVIDENCIA SIMBÓLICA O NUMÉRICA", evidence),
                            _claim("HODGE-E4-002", DIMENSION_STATEMENT,
                                   "EVIDENCIA SIMBÓLICA O NUMÉRICA",
                                   {"plus": evidence["self_dual_dimension"], "minus": evidence["anti_self_dual_dimension"]})]
    elif role == "counterexample":
        evidence = compute()["counterexample"]
        result.update(summary="The deliberately false Euclidean claim *^2=-I is refuted by e1 wedge e2.", evidence=evidence)
        result["claims"] = [_claim("HODGE-E4-FALSE", FALSE_STATEMENT,
                                   "REFUTADO", evidence)]
    elif role == "audit":
        candidates = list(_read_inputs(task.get("inputs", {})))
        producers = [item for item in candidates if item.get("role") in {"mathematics", "computation"}]
        if not producers:
            raise ValueError("A separate audit requires an explicit producer artifact in task.inputs")
        independent = _audit_matrix()
        independent_square = _multiply(independent, independent)
        square = [[int(x) for x in row] for row in independent_square]
        # Deduplicate identical snapshots only. A second artifact with the same ID
        # and different evidence must still be reviewed and rejected if corrupt.
        snapshots = {}
        for producer in producers:
            fingerprint = json.dumps({key: producer.get(key) for key in
                                      ("execution_id", "role", "conventions", "evidence", "claims")},
                                     sort_keys=True, ensure_ascii=False)
            snapshots.setdefault(fingerprint, producer)
        producer_verdicts = [_producer_verdict(producer, independent, square) for producer in snapshots.values()]
        snapshot_counts = {}
        for verdict in producer_verdicts:
            identifier = str(verdict["execution_id"])
            snapshot_counts[identifier] = snapshot_counts.get(identifier, 0) + 1
        for verdict in producer_verdicts:
            unique = snapshot_counts[str(verdict["execution_id"])] == 1
            verdict["checks"]["unique_execution_snapshot"] = unique
            if not unique:
                verdict["failed_checks"].append("unique_execution_snapshot")
                verdict["verdict"] = "REJECTED"
        producer_executions = sorted({item["execution_id"] for item in producer_verdicts
                                      if isinstance(item["execution_id"], str)})
        producers_correct = all(item["verdict"] == "CONFIRMED_FINITE_FIXTURE" for item in producer_verdicts)
        correct = producers_correct
        false_proposals = [item for item in candidates if item.get("id") == "HODGE-E4-FALSE"]
        false_check = None
        if false_proposals:
            recognized = all(item.get("statement") == FALSE_STATEMENT
                             and item.get("hypotheses") == CONVENTIONS for item in false_proposals)
            actual_twice = [row[0] for row in square]
            false_prediction = [-1, 0, 0, 0, 0, 0]
            false_check = {"claim_id": "HODGE-E4-FALSE", "input": "e1 wedge e2",
                           "actual_star_twice_coefficients": actual_twice,
                           "false_prediction_coefficients": false_prediction,
                           "difference": [x - y for x, y in zip(actual_twice, false_prediction)],
                           "statement_and_hypotheses_match": recognized,
                           "submitted_statements": sorted({str(item.get("statement")) for item in false_proposals}),
                           "rejected": recognized and actual_twice != false_prediction,
                           "method": "apply independently reconstructed star twice to first basis vector"}
            correct = correct and recognized
        result.update(summary="Internal reconstruction completed.",
                      evidence={"producer_matches": producers_correct, "independent_matrix": independent,
                                "method": "invert wedge pairing by exact elimination; permutation determinants",
                                "checks": ["execution provenance", "conventions", "basis", "matrix", "square", "projector dimensions", "attached claims"],
                                "verdict": "CONFIRMED_FINITE_FIXTURE" if correct else "REJECTED",
                                "producer_execution_ids": producer_executions,
                                "producer_verdicts": producer_verdicts,
                                "reviewed_execution_ids": sorted({item["execution_id"] for item in producer_verdicts
                                                                  if item["verdict"] == "CONFIRMED_FINITE_FIXTURE"}),
                                "separate_task_call": True,
                                "process_isolation": "not established by benchmark backend alone",
                                "false_proposal_present": bool(false_proposals),
                                "false_proposal_audit": false_check},
                      reviewed=correct)
        result["claims"] = [_claim("HODGE-E4-AUDIT", "Every supplied producer matches the independent exact reconstruction and conventions",
                                   "EVIDENCIA SIMBÓLICA O NUMÉRICA" if correct else "REFUTADO", result["evidence"])]
        if false_check:
            false_result = deepcopy(false_proposals[0])
            false_result.update(status="REFUTADO" if false_check["rejected"] else "EN REVISIÓN",
                                evidence=false_check,
                                review_kind="internal; exact submitted statement and hypotheses checked")
            result["claims"].append(false_result)
    elif role == "conceptual":
        result.update(summary="Question and success criterion fixed before calculation.",
                      evidence={"question": "Determine the sign of *^2 and eigenspace dimensions on Euclidean 4D two-forms.",
                                "success": "Exact matrix square is I; projector ranks are 3; false-sign claim rejected.",
                                "known_result": "Riemannian *^2=(-1)^(k(n-k)); specialize n=4,k=2."})
    elif role == "physics":
        result.update(summary="Signature and scope checked.",
                      evidence={"units": "dimensionless", "signature_change": "With one negative metric direction, *^2=-I on 4D two-forms.",
                                "physical_scope": "Algebraic self-duality; no gravitational helicity count or dynamics established.",
                                "gauge": "none in this finite vector-space fixture"})
    else:
        candidates = list(_read_inputs(task.get("inputs", {})))
        audits = [item for item in candidates if item.get("role") == "audit"]
        passed = bool(audits) and all(item.get("reviewed") is True for item in audits)
        result.update(summary="Finite fixture integrated; external comparison remains pending.",
                      evidence={"internal_audit_present": bool(audits), "internal_audit_passed": passed,
                                "scientific_scope": "finite exact linear algebra",
                                "cross_model_comparison": "PENDING: no independent Claude and Codex reports supplied"},
                      reviewed=passed)
    workspace = task.get("workspace")
    if workspace:
        destination = Path(workspace)
        destination.mkdir(parents=True, exist_ok=True)
        artifact = destination / f"{role}.json"
        result["artifacts"] = [str(artifact)]
        artifact.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def run_reference(output: str | Path) -> dict:
    """Run deterministic producer, auditor and counterexample as distinct calls."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    producer = execute({"role": "mathematics", "workspace": output / "producer"})
    false = execute({"role": "counterexample", "workspace": output / "counterexample"})
    audit = execute({"role": "audit", "inputs": [producer, false], "workspace": output / "auditor"})
    report = {"benchmark": "hodge-euclidean-4d", "conventions": CONVENTIONS,
              "producer": producer, "audit": audit, "deliberately_incorrect_proposal": false,
              "passed": bool(audit["reviewed"] and audit["evidence"]["false_proposal_audit"]["rejected"]
                             and false["claims"][0]["status"] == "REFUTADO"),
              "execution_kind": "deterministic code; not Claude or Codex model execution",
              "separation": "distinct task calls in one process; orchestrator provides process separation",
              "general_claim_status": "No general theorem promoted by this fixture",
              "cross_model_comparison": "pending"}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
