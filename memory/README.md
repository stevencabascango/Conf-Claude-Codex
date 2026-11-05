# Memoria científica versionada

Conserva definiciones, problemas, conjeturas, derivaciones, contraejemplos,
obstrucciones, bibliografía, auditorías, desacuerdos y preguntas abiertas en JSON
revisable por Git. SQLite es sólo el índice de trabajo; exporta con
`ScientificMemory.export(path)` antes de proponer un cambio científico.

Cada afirmación contiene ID, enunciado, estado, hipótesis, fuentes, archivos y
dependencias. `revision` y `history` conservan cambios. Las fuentes se identifican
como consultadas/verificadas o pendientes, con el resultado concreto utilizado.

El ejemplo exporta memoria antes y después de invalidación de dependencias. Una
refutación conserva su estado. Una corrección requiere `revise`, `resubmit` y una
auditoría nueva; los certificados de revisiones antiguas no valen para la nueva.

```python
from genius.memory import ScientificMemory

with ScientificMemory("runs/memory.sqlite") as memory:
    memory.add({"id": "Q-001", "statement": "Pregunta precisa y delimitada",
                "status": "proposal", "hypotheses": [], "sources": [],
                "artifacts": [], "dependencies": []})
    memory.export("memory/claims.json")
```
