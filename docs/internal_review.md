# Revisión interna independiente de GENIUS-5000

Revisión del 5 de noviembre de 2026, realizada por el agente `review_runtime`
en una ejecución distinta de las que implementaron el núcleo y el ejemplo
científico. Es una revisión interna de software y del caso matemático declarado.
Los agentes comparten proveedor, contexto inicial y código; no constituye revisión
externa ni acredita independencia de todos los errores sistemáticos.

## Alcance comprobado

Se inspeccionaron memoria, planificación, orquestación, adaptadores, comparación
Claude–Codex, catálogo, habilidades y caso de Hodge. Las pruebas independientes
están en `tests/test_adversarial.py`; utilizan archivos temporales, SQLite y
procesos locales pequeños. Los datos con backend `unit-test-fixture` son fixtures
de software, no ejecuciones científicas ni llamadas a modelos.

La orden reproducible es:

```bash
python3 -m unittest discover -s tests -p test_adversarial.py -v
```

El coordinador conserva el resultado final de toda la suite mediante
`scripts/check.py`. Una ejecución del caso de referencia no certifica las
capacidades científicas objetivo de los perfiles.

Resultado final de esta revisión: se ejecutó
`scipython -m unittest discover -s tests -p test_adversarial.py -v`; las 26 pruebas
terminaron correctamente, código de salida 0. La salida fue:

```text
Ran 26 tests in 0.354s

OK
```

## Hallazgos y correcciones

| Clasificación | Hallazgo reproducido o comprobado | Corrección revisada |
|---|---|---|
| ERROR | Preparar una comparación por segunda vez sobrescribía el contexto y el manifiesto. | Se rechaza la sobrescritura y se conserva el estado anterior. |
| ERROR | Una lista de perfiles seleccionados duplicada inflaba su contador. | El plan exige identificadores seleccionados únicos. |
| ERROR | Un JSON vacío de Claude se aceptaba como un informe terminado. | Se exige un resultado estructurado y un informe no vacío. |
| ERROR | El inicio real del proceso no quedaba confirmado hasta que terminaba. | PID e identidad de inicio se registran mediante callback inmediatamente tras crearlo. |
| ERROR | Un directorio de intento huérfano podía impedir la recuperación. | Se preserva el directorio y el nuevo intento usa otro número. |
| ERROR | Un proceso superviviente al cierre abrupto del coordinador podía duplicarse al reanudar. | Se comprueba PID/identidad; un trabajador previo vivo impide reanudar y lanzar otro. |
| HUECO | Bastaban nombres de ejecución y rutas inexistentes para registrar una auditoría confirmada. | Se requieren registros completados enlazados, archivos existentes y hashes que se revalidan al promover. |
| HUECO | Una afirmación invalidada no tenía vía de regreso a la cola de auditoría. | `resubmit` permite una nueva revisión con evidencia; no revierte refutaciones. |
| ERROR | Una auditoría favorable podía usarse pese a una objeción vigente de otra auditoría. | Las objeciones de la misma versión impiden promover hasta revisar y reenviar el resultado. |
| ERROR | El auditor de Hodge ignoraba productores posteriores al primero. | Se revisan las evidencias, afirmaciones y convenciones de cada ejecución productora. |
| ERROR | El auditor aceptaba una matriz euclídea con firma productora incompatible. | Las convenciones e hipótesis deben coincidir con el caso declarado. |
| ERROR | Alterar las convenciones devueltas por una ejecución podía modificar el objeto compartido de referencia. | Cada resultado recibe copias de sus convenciones. |
| ERROR | El ID de la propuesta falsa bastaba para atribuirle una refutación aunque se hubiera corregido su texto. | Se comprueban enunciado e hipótesis; una versión distinta queda en revisión. |
| ERROR | Las convenciones de un contexto inicial podían cambiar después de preparar la comparación sin invalidar el sellado. | Se verifica el hash de ambos contextos comunes antes de sellar o comparar. |
| ERROR | Las dos revisiones cruzadas podían reutilizar un identificador de ejecución. | Cada revisión exige un ID distinto de las ejecuciones productoras y de la otra revisión. |

Las pruebas adversariales finales confirmaron las correcciones de integridad del
contexto sellado y exclusividad de los identificadores de revisión. No quedaron
fallos abiertos en las pruebas de esta revisión. Su alcance sigue limitado a los
contratos y casos enumerados; no constituye una prueba de ausencia de todo error.

## Comprobación matemática y física

El caso usa exclusivamente $\Lambda^2((\mathbb R^4)^*)$, métrica positiva y
orientación declarada. La revisión fijó de forma independiente las seis imágenes
de la base exterior a partir del emparejamiento con el volumen. Con esas
convenciones, $*^2=I$ y los autoespacios reales tienen dimensiones $3+3$. La
propuesta $*^2=-I$ queda refutada por $e^{12}$. Estos signos no se extrapolan a
firma lorentziana.

El argumento escrito en `research/quantum_gravity/REFERENCE_HODGE.md` satisface
el alcance pertinente del Protocolo B: premisas, resultado conocido, pasos
explícitos, hipótesis y límites. Los controles físicos del Protocolo A son
dimensiones y firma; aquí no hay ecuaciones de movimiento ni predicción
gravitatoria nueva. No se fuerza la aparición de un resultado original.
La regla de dualidad usada se contrastó con la
[documentación primaria de SageMath](https://doc.sagemath.org/html/en/reference/algebras/sage/algebras/clifford_algebra_element.html#sage.algebras.clifford_algebra_element.ExteriorAlgebraElement.hodge_dual).

## Límites conservados

- El catálogo describe 5.000 objetivos de diseño, con 100 líneas científicas y
  tareas/metodologías explícitas. Su validación estructural y su diversidad
  combinatoria no prueban capacidad científica de 5.000 agentes.
- La presencia, descubrimiento y coherencia de las 22 habilidades se verifican
  estructuralmente. Su eficacia para investigación abierta requiere evaluaciones
  por tarea, con resultados positivos y negativos independientes.
- El ejemplo usa procesos deterministas y aritmética exacta; no ejecuta un
  investigador LLM ni verifica una teoría general con Lean o Coq.
- Los límites de tiempo requieren un coordinador vivo. Tras una caída abrupta
  puede sobrevivir un proceso hijo; la recuperación evita duplicarlo y exige
  reconciliarlo. Un supervisor externo sería necesario para una garantía de
  terminación que sobreviva a `SIGKILL` del coordinador.
- Los archivos y hashes acreditan procedencia; no son un verificador lógico ni
  autentican una afirmación falsa introducida deliberadamente por un operador.
- Los límites de tokens y gasto no se inventan cuando el proveedor no expone
  un control verificable. Se distinguen presupuesto de llamadas/tiempo/bytes y
  consumo comunicado por el proveedor.
- Un informe ausente deja pendiente la comparación. El acuerdo entre informes
  no constituye demostración ni revisión externa.

## Skills aplicadas en esta revisión

`metacognicion-operativa`: registro de evidencia, pruebas negativas y corrección.
`colaborador-matematica-pura`: hipótesis, signos y alcance del argumento de Hodge.
`investigador-elite` y `colaborador-cientifico`: interpretación física limitada,
separación de evidencia, revisión interna y resultados abiertos. Se leyó el
arranque obligatorio y los Protocolos A/B. No se construyó una teoría nueva ni
se solicitó cadena de pensamiento privada.
