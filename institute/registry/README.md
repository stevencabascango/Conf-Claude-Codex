# Catálogo GENIUS-5000

`profiles.jsonl` contiene exactamente 5.000 fichas completas, una por línea.
`schema.json` describe su estructura y `manifest.json` fija la distribución y
la huella SHA-256 del archivo. El código de generación y validación está en
`genius/catalogue.py`; la taxonomía legible está en
`institute/divisions/taxonomy.json` y los referentes metodológicos en
`institute/archetypes/library.json`.

El diseño comprende 100 líneas científicas delimitadas. Cada línea contiene
cinco modos de trabajo y diez tareas con preguntas, métodos, entregables y
perspectivas de revisión diferentes. Los modos modifican el alcance: local,
formal, global, ejemplo finito o comparación, con adaptaciones específicas para
computación e integración. La compatibilidad de un modo con un objeto se debe
justificar durante la ejecución; un informe de incompatibilidad u obstrucción
es un resultado válido. No se presupone que toda técnica se aplique a todo
objeto.

La validación comprueba identificadores, distribución, campos, núcleo formativo,
duplicados semánticos evidentes y cobertura de ejes. Ignora identificadores y
versiones al buscar copias del mismo trabajo. Informa también de los 500 grupos
que comparten contexto de línea y modo: no oculta esa proximidad.

Estas verificaciones demuestran integridad y diversidad estructural del diseño.
No demuestran capacidad científica de cada perfil ni independencia de los
errores de los modelos. Todos los perfiles comparten un estándar exigente de
conducta observable, pero sus campos `evaluated_capabilities` y
`evaluation_results` están vacíos hasta que exista evidencia de ejecución
identificada. El catálogo no atribuye títulos, IQ ni equivalencia con los
referentes históricos. La disponibilidad de herramientas se comprueba en el
entorno de ejecución; una herramienta indicada no cuenta como ejecutada.

Para regenerar y comprobar el catálogo sin dependencias externas:

```bash
python3 -m genius.catalogue --root .
python3 -m unittest discover -s tests -p test_catalogue.py -v
```

No añadas evaluaciones individuales directamente al archivo generado: se
perderían al regenerarlo. Conserva su evidencia y los resultados de ejecución
en la memoria y registros de evaluaciones del proyecto, vinculados por ID y
versión del perfil. Una futura promoción de capacidades necesita una política
de evaluación explícita y resultados observados.
