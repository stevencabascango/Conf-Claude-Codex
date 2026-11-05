"""Discovery of the shared, repository-local research skills."""
from pathlib import Path
import re


SKILL_NAMES = (
    "first-principles-reasoning", "thought-experiment-design",
    "quantum-gravity-research", "mathematical-relativity", "twistor-theory",
    "googly-problem", "algebraic-topology", "algebraic-geometry",
    "derived-algebraic-geometry", "quantum-field-theory", "string-theory",
    "loop-quantum-gravity", "unified-field-theory", "theorem-discovery",
    "rigorous-proof", "independent-proof-audit", "counterexample-search",
    "scientific-literature-review", "physical-consistency-audit",
    "cross-model-comparison", "research-memory", "scientific-paper-writing",
)

REQUIRED_SECTIONS = (
    "Propósito y uso", "Entradas", "Procedimiento", "Herramientas",
    "Entregables", "Aceptación", "Errores frecuentes", "Colaboración", "Ejemplo",
)


def load_skill(root: str | Path, name: str) -> str:
    """Read a registered skill; arbitrary paths are not accepted."""
    if name not in SKILL_NAMES:
        raise ValueError(f"Unknown institute skill: {name}")
    return (Path(root) / ".agents" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def validate_skills(root: str | Path) -> dict:
    root = Path(root)
    errors = []
    for name in SKILL_NAMES:
        try:
            content = load_skill(root, name)
        except (OSError, ValueError) as error:
            errors.append(f"{name}: {error}")
            continue
        if not content.startswith("---\n") or "\n---\n" not in content[4:]:
            errors.append(f"{name}: invalid frontmatter")
            continue
        frontmatter = content.split("---", 2)[1]
        if not re.search(rf"^name: {re.escape(name)}$", frontmatter, re.M):
            errors.append(f"{name}: frontmatter name mismatch")
        if not re.search(r"^description: .+", frontmatter, re.M):
            errors.append(f"{name}: missing description")
        for section in REQUIRED_SECTIONS:
            if f"## {section}\n" not in content:
                errors.append(f"{name}: missing section {section}")
        mirror = root / ".claude" / "skills" / name / "SKILL.md"
        if not mirror.exists() or mirror.read_text(encoding="utf-8") != content:
            errors.append(f"{name}: Claude adapter does not resolve to canonical content")
        protocol = root / "docs" / "scientific_protocol.md"
        if not protocol.exists():
            errors.append(f"{name}: missing shared scientific protocol")
    return {"valid": not errors, "count": len(SKILL_NAMES), "errors": errors,
            "scope": "structural discovery; scientific effectiveness remains task-specific"}
