# Habilidades y adaptadores

El núcleo canónico reside en `.agents/skills/`: 22 carpetas con `SKILL.md`.
`.claude/skills/` contiene enlaces relativos a esas mismas carpetas. Así, ambas
superficies leen el mismo procedimiento. Las habilidades son instrucciones
reutilizables; su presencia no acredita que un modelo las haya seguido con éxito.

`genius.skills.load_skill(root, name)` carga sólo nombres registrados y
`validate_skills(root)` comprueba descubrimiento, secciones y paridad. La evaluación
científica se realiza por tarea y se conserva separada de esta validación estructural.

Codex descubre habilidades del repositorio en `.agents/skills`. Sus agentes propios
se definen en `.codex/agents/*.toml` con nombre, descripción e instrucciones. Los
adaptadores conservan el modelo y los permisos heredados. Véanse la documentación
oficial de [habilidades](https://learn.chatgpt.com/docs/build-skills) y
[subagentes](https://learn.chatgpt.com/docs/agent-configuration/subagents), consultadas
el 5 de noviembre de 2026. Son siete roles operativos, que reciben una ficha
seleccionada del catálogo; no se instalan 5.000 agentes nativos.

Claude Code carga agentes del proyecto desde `.claude/agents/*.md` y habilidades
desde `.claude/skills`. Sus adaptadores usan frontmatter con nombre, descripción y
modelo heredado; véanse [agentes](https://code.claude.com/docs/en/sub-agents) y
[habilidades](https://code.claude.com/docs/en/skills). No se modifican los permisos
globales ni se atribuye a los adaptadores un aislamiento mayor al ofrecido por el
entorno real.

Cada ficha seleccionada aporta especialidad, límites, método, herramientas
requeridas y responsabilidades. Cada ejecución devuelve afirmaciones con estado,
evidencia, alcance y colaboración pendiente. El rol `audit` revisa un artefacto de
una ejecución diferente. Los roles son conceptual, mathematics, physics,
computation, counterexample, audit e integration.

Las skills de rol locales del usuario (`metacognicion-operativa`,
`colaborador-matematica-pura`, `investigador-elite`, `colaborador-cientifico`) se
aplicaron durante la implementación. No se copian sus archivos personales al
repositorio; el protocolo científico común contiene las reglas operativas que
necesitan los adaptadores para funcionar de forma portable.
