# Matriz de aceptación y alcance de la evidencia

La evidencia ejecutada se registra con `python3 scripts/check.py --output
institute/evaluations/software_checks.json`. La tabla vincula los catorce
requisitos de pruebas del encargo con pruebas que pueden fallar por un error
real. Su existencia no equivale a haberlas ejecutado: el JSON de la ejecución
indica resultados, errores, versiones y fecha.

| # | Requisito | Prueba o artefacto | Alcance y limitación |
|---|---|---|---|
| 1 | Exactamente 5.000 perfiles | `test_catalogue.CatalogueTests.test_exact_count_and_distribution`; `institute/registry/profiles.jsonl` | Cuenta fichas registradas; no agentes ejecutados. |
| 2 | Identificadores únicos | `test_exact_count_and_distribution`; `catalogue_validation.json` → `uniqueness` | Compara todos los IDs y las huellas semánticas. |
| 3 | Distribución por división | `test_exact_count_and_distribution`; `institute/divisions/taxonomy.json` | Verifica la distribución solicitada, incluida la división twistoriana de 650. |
| 4 | Campos obligatorios | `test_missing_field_and_fake_evaluation_are_rejected`; `test_nested_malformed_values_fail_without_certifying`; `schema.json` | Validación estructural; corrección científica requiere tareas individuales. |
| 5 | Duplicación evidente | `test_obvious_semantic_clone_ignores_new_name`; `test_diversity_is_explicit_and_shared_context_reported` | Cambiar nombre/ID/versión no oculta una copia; proximidad estructural compartida se informa. No prueba originalidad científica. |
| 6 | Habilidades localizables y utilizables | `test_benchmark.SharedSkillTests.test_all_skills_discoverable_in_both_environments`; `genius.skills.load_skill` | Las 22 habilidades resuelven al núcleo común. No equivale a evaluar eficacia en un modelo. |
| 7 | Concurrencia y presupuesto | `test_adversarial.SubprocessAdversarialTests.test_call_budget_blocks_downstream_work`; `test_captured_output_never_exceeds_byte_budget`; `test_timeout_kills_a_real_local_process`; `test_workflow.SelectionAndWorkflowTests.test_real_failure_is_logged_and_bounded_retry_recovers` | Comprueba límites en procesos reales locales. Los límites de bytes/llamadas/tiempo no son un presupuesto universal de tokens o dólares. |
| 8 | Registro y recuperación de fallos | `test_real_failure_is_logged_and_bounded_retry_recovers`; `test_interrupted_run_resumes_without_repeating_completed_work`; `test_resume_rejects_changed_completed_artifacts`; checkpoint y logs | Fallo real de proceso con reintento acotado; interrupción simulada del coordinador con reanudación sin repetir trabajo terminado; rechazo de evidencia alterada. Los servicios externos quedan por evaluar. |
| 9 | Refutado no pasa a demostrado | `test_adversarial.ScientificMemoryAdversarialTests.test_refutation_cannot_be_promoted_even_with_audit_id`; `test_benchmark.HodgeBenchmarkTests.test_false_claim_refuted_and_never_demonstrated` | Protege transición de estado y conserva contraejemplo. La calidad general de futuras auditorías no queda certificada. |
| 10 | Dependencias modificadas activan revisión | `test_revision_invalidates_all_descendants_and_retains_refutation`; `test_known_problem_runs_separate_audit_classification_and_memory` | Propaga revisión transitiva y conserva refutaciones. Las dependencias omitidas por el autor no pueden detectarse solo por el grafo. |
| 11 | Comparación pendiente si falta informe | `test_workflow.InstallationAndComparisonTests.test_missing_comparison_and_disagreements_remain_visible`; `test_missing_or_failed_report_never_completes_comparison` | Un informe fallido o ausente no es revisión cruzada. Dos informes concordantes todavía requieren revisión. |
| 12 | Instalación conserva configuración | `test_installation_preserves_existing_configuration_and_is_idempotent`; `test_fresh_install_and_dry_run_do_not_touch_global_settings` | Comprueba hashes de instrucciones, configuración Codex y configuración Claude existentes; los conflictos se preservan y se notifican. |
| 13 | Problema de referencia completa el flujo | `test_known_problem_runs_separate_audit_classification_and_memory`; `test_stage_a_selects_thirty_from_full_registry_without_execution`; `test_small_and_transversal_teams_cover_all_roles` | Selección de 30 y equipos de 3/21; siete procesos del benchmark con auditoría separada, clasificación y memoria. Es un caso conocido de álgebra lineal, sin ejecución LLM. |
| 14 | Diferenciar propuestas/evaluaciones/ejecuciones | `test_validate_cli_distinguishes_targets_from_execution_evidence`; `test_design_status_and_common_training_are_honest`; `demo.json` → `execution`/`capabilities` | 5.000 perfiles de diseño, selección, procesos realmente ejecutados y resultados revisados tienen contadores distintos; competencias científicas individuales pendientes. |

La CI usa Python 3.11–3.13 sobre Linux, sin paquetes adicionales ni secretos.
Las comprobaciones locales usan la versión de Python indicada en el informe.
La CI queda por ejecutar en GitHub hasta que el repositorio esté publicado y
sus Actions puedan iniciarse. No se presenta una revisión interna como revisión
externa ni como demostración general del problema de Googly.
