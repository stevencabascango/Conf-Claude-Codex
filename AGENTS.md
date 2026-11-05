# GENIUS-5000: instrucciones del proyecto

Consulta `docs/scientific_protocol.md` y las habilidades pertinentes de `.agents/skills/`.
El registro tiene 5.000 perfiles de diseño; activa sólo el equipo necesario. Usa
`python3 -m genius plan` para seleccionar perfiles y documenta cada ejecución real.
Declara capacidades objetivo, evaluadas y pendientes por separado. No inventes
credenciales, modelos, herramientas, referencias ni resultados.

Para investigación, aplica el ciclo de diez pasos y los Protocolos A/B del núcleo.
La revisión requiere una ejecución distinta de la productora y evidencia conservada.
No promociones estados por consenso. Conserva refutaciones y desacuerdos; cambia
dependencias mediante la memoria para activar revisión transitiva.

Usa `.codex/agents/genius-*.toml` para roles nativos cuando corresponda. Un perfil
del catálogo no es un subagente activo. Mantén presupuestos explícitos; no cambies
permisos ni configuración global para hacer funcionar una ejecución.

Si existe `~/.claude/arranque-subagentes.md`, aplícalo al delegar. En una instalación
sin ese archivo, usa el núcleo autónomo del repositorio. Si hay
`graphify-out/graph.json`, consulta su grafo antes de explorar archivos sueltos.
La construcción de un grafo nuevo con LLM requiere autorización específica.

Pruebas: `python3 scripts/check.py`. Demostración: `python3 -m genius demo --output runs/example`.
Preserva configuraciones ajenas. No publiques afirmaciones científicas sin revisión.
