# Entrega GENIUS-5000 · 2026-11-05

## Implementado

Registro reproducible de exactamente5.000 perfiles y distribución solicitada,
12 referentes metodológicos, 100 líneas científicas, controles de duplicación y
cobertura, 22 habilidades compartidas y siete adaptadores nativos para cada entorno.
Las fichas contienen los campos obligatorios, límites y criterios de colaboración.

Orquestador con selección de equipos3–50, siete funciones, DAG de tareas,
concurrencia, tiempo, llamadas, bytes, reintentos, checkpoints y recuperación.
Adaptadores reales de CLI, memoria transaccional/versionada, estados científicos,
auditorías con archivos/hash, bloqueo de objeciones e invalidación transitiva.
Protocolo Claude–Codex con briefs idénticos, sellado, revisión cruzada y desacuerdos.
Instalador local conservador, documentación, CI y script de publicación sin force push.

## Ejecutado y comprobado

- `scipython scripts/check.py --output institute/evaluations/software_checks.json`:
  **64 pruebas**, cero fallos/errores/omisiones; validación del catálogo y habilidades aprobada.
- Selección inicial de30 perfiles; equipos pequeños y amplios cubren las siete funciones.
- Caso Hodge: **7 procesos deterministas**, concurrencia máxima2, siete terminados,
  una reconstrucción auditora separada y refutación explícita de la propuesta falsa.
  Memoria antes/después del cambio de dependencia y evidencia en
  `institute/evaluations/reference_example/`.
- 26 pruebas adversariales y revisión interna por un agente distinto; informe en
  `docs/internal_review.md`. Las correcciones incluyeron preservación de contextos,
  objeciones, convenciones, múltiples productores y recuperación tras fallos.
- Intento acotado de cada CLI: Claude agotó ocho segundos sin informe; Codex falló
  al iniciar su app-server por filesystem de solo lectura. **Cero ejecuciones LLM
  científicas terminadas**; comparación real pendiente. Artefactos en
  `institute/evaluations/native_access/`.

La comprobación estructural y el caso conocido no evalúan científicamente las
5.000 capacidades objetivo. Esas evaluaciones permanecen pendientes en las fichas.
No se creó ni se afirmó una teoría física nueva, una solución Googly o una
demostración general formalizada.

## Acceso y publicación

Se inicializó el repositorio local con el remoto solicitado. No fue posible
inspeccionar el remoto: DNS de GitHub falló y la consulta web no devolvió contenido.
El script de publicación se intentó y falló porque no hay `gh`. No hubo push ni
creación confirmada en GitHub; véase `institute/evaluations/publication.json`.
Con acceso restaurado, inspeccionar/integrar contenido remoto antes de publicar.

## Skills y división de trabajo

El coordinador aplicó `metacognicion-operativa`, `graphify` (detección y política;
sin construir grafo), `skill-creator`, `openai-docs`, `prompt-master`,
`colaborador-matematica-pura`, `investigador-elite` y `colaborador-cientifico`.
El trabajador del catálogo aplicó metacognición y los roles científicos; el de
habilidades/benchmark añadió skill-creator y prompt-master. El revisor aplicó
metacognición y los tres roles científicos. El trabajador de OneDrive aplicó
metacognición; no escribió en este repositorio. No se aplicó `teoria-original`
porque el encargo implementa infraestructura y un caso conocido.

En paralelo se resumieron114 salidas OneDrive y se actualizó su manifiesto.
La regeneración automática posterior de sus webs falló por `/mnt/c` de solo
lectura. Se diagnosticó el `AttributeError` previo por `revision` textual en
`cerebro2.py:100`; no se modificó el BRAIN UFT en esta implementación.
