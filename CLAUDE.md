# GENIUS-5000 para Claude Code

Aplica `AGENTS.md` y `docs/scientific_protocol.md`. Las habilidades de
`.claude/skills/` enlazan el núcleo común `.agents/skills/`; evita duplicar reglas.
Los siete agentes `.claude/agents/genius-*.md` reciben fichas seleccionadas del
catálogo; no cargues las 5.000 fichas en un contexto ni actives todas a la vez.
Usa contextos nuevos en las fases separadas Claude–Codex y sella los informes.
Registra herramientas/modelos reales y límites de independencia. No cambies
configuraciones globales, permisos ni credenciales. Pruebas y ejecución en `README.md`.
