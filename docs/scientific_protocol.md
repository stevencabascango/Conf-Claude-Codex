# Protocolo científico común

Versión 1.0. Los perfiles son objetivos de comportamiento; su registro no acredita
competencia científica ni ejecución. Los referentes históricos inspiran métodos y
no representan personas, credenciales o equivalencia intelectual evaluada.

## Ciclo de investigación

1. Precisar pregunta, motivación, alcance y criterio falsable de éxito.
2. Revisar antecedentes, hipótesis y obstáculos; separar literatura consultada de
   fuentes pendientes. Registrar consultas, fechas y alcance antes de alegar novedad.
3. Declarar convenciones, unidades, dimensiones, firma, regularidad y contorno.
4. Comparar rutas viables y justificar la selección.
5. Construir definiciones, ecuaciones y un ejemplo mínimo calculable.
6. Desarrollar una prueba, derivación o cálculo reproducible con dependencias.
7. Intentar refutarlo mediante contraejemplos, degeneraciones y límites.
8. Revisar en una ejecución diferente: reconstruir el paso decisivo sin aceptar
   el consenso de agentes como demostración.
9. Clasificar cada afirmación con un único estado y alcance preciso.
10. Registrar el siguiente cálculo o prueba que reduzca la incertidumbre.

Un contraejemplo, una obstrucción o un resultado negativo son resultados válidos.
Una herramienta no disponible se registra como pendiente; no se inventa su salida.

## Protocolo A: física y física matemática

1. Listar principios físicos, simetrías y resultados matemáticos utilizados.
2. Formular el resultado que se pretende derivar; indicar si es conocido, una
   especialización o una propuesta nueva. No forzar novedad en una comprobación.
3. Dar pasos verificables: identidad, principio y condiciones iniciales/de contorno.
4. Comprobar dimensiones, unidades, signos y normalizaciones de cada término.
5. Recuperar límites conocidos y explicitar parámetros y términos descartados.
6. Justificar la consecuencia de las premisas y su dominio de validez.
7. Explicar observables, interpretación y predicciones efectivamente obtenidas.
8. Entregar enunciado numerado, notación uniforme y evidencia reproducible.

## Protocolo B: matemáticas

1. Enumerar definiciones, axiomas, hipótesis y resultados previos necesarios.
2. Enunciar la conclusión precisa e identificar su relación con lo conocido.
3. Demostrar cada paso mediante una regla lógica, definición o teorema identificado.
4. Justificar hipótesis adicionales y evitar introducir la conclusión como premisa.
5. Verificar casos particulares, contraejemplos y límites de generalización.
6. Entregar enunciado y argumento auditables; localizar cualquier paso pendiente.

Para resultados físico-matemáticos se aplican ambos. Las verificaciones finitas,
identidades simbólicas y simulaciones se describen con su alcance. Una teoría
nueva requiere axiomas mínimos, límite clásico, predicciones contrastables y crítica;
si el usuario proporciona la skill `teoria-original`, aplicar además su estructura
A–O. Este repositorio no incluye una nueva teoría física ni afirma resolver Googly.

## Estados de afirmaciones

| Estado | Evidencia necesaria y alcance |
|---|---|
| RESULTADO ESTABLECIDO | Fuente identificada y verificada, enunciado e hipótesis pertinentes. |
| PROPUESTA | Construcción explícita aún sin evaluación suficiente. |
| CONJETURA | Enunciado preciso pendiente de demostración. |
| EVIDENCIA SIMBÓLICA O NUMÉRICA | Código, entradas, entorno, salida y límites de la comprobación. |
| DERIVACIÓN PENDIENTE DE AUDITORÍA | Argumento completo propuesto, con sus dependencias. |
| DEMOSTRADO BAJO HIPÓTESIS EXPLÍCITAS | Argumento completo y registro de auditoría interna favorable en ejecución distinta, con hipótesis. |
| VERIFICADO FORMALMENTE | Archivos completos, versión del verificador, dependencias y salida verificable; alcance del enunciado formalizado. |
| REFUTADO | Contradicción o contraejemplo documentado con condiciones y evidencia. |
| EN REVISIÓN | Objeción abierta o dependencia modificada que afecta a la afirmación. |

No promover evidencia numérica a demostración general. La auditoría interna y la
revisión externa tienen campos separados. Toda promoción exige ID, hipótesis,
archivos de evidencia, IDs de las ejecuciones productora y auditora y dependencias
vigentes. Un resultado refutado no se promueve por acuerdo de agentes. Si cambia
una dependencia, propagar `EN REVISIÓN` a sus dependientes; conservar el historial.

## Lista del auditor

Revisar enunciado, hipótesis, lógica, dominios de operadores, circularidad,
convenciones, degeneraciones, contraejemplos, coherencia física, alcance de las
herramientas y reproducibilidad. Para resultados formales, verificar que el teorema
formalizado coincide con el enunciado científico y que no hay axiomas añadidos sin
declarar. Un fallo de compilación no es un resultado formal verificado.

## Convenciones exigidas en twistores y gravedad

- Espacios, fibrados, estructuras complejas y condiciones de realidad.
- Firma, orientación, dualidad, normalizaciones y helicidades pertinentes.
- Pesos, grados, clases cohomológicas, regularidad, dominio y contorno.
- Simetrías, libertad gauge, restricciones y grados de libertad físicos.
- Alcance local, perturbativo (con orden) o global y condiciones de extensión.
- Relación explícita con Einstein: mapa de reconstrucción, dominio, compatibilidad
  gauge, existencia y unicidad en el sentido que se afirma.

Añadir una fuente no recupera automáticamente la otra helicidad. No conmutatividad
no identifica quiralidad física. Un álgebra L-infinito no constituye por sí sola
una equivalencia con gravedad. Un sector restringido de Einstein no resuelve el
problema general de Googly. Una correspondencia matemática, una reformulación y
una propuesta física nueva se etiquetan por separado.

## Claude y Codex

Preparar un enunciado común, convenciones, documentos y presupuestos registrados.
Mantener separados contexto y artefactos durante la primera fase. Registrar binario,
versión, modelo si es conocido, herramientas usadas y limitaciones de aislamiento.
Después de ambos informes, intercambiar sólo los informes cerrados; reconstruir,
buscar contraejemplos, registrar acuerdos/desacuerdos y sintetizar con trazabilidad.
Si falta uno, la comparación permanece pendiente. Dos ejecuciones del mismo modelo
pueden compartir errores; separación de ejecución no equivale a revisión externa.

## Herramientas y alcance de autorización

Usar sólo herramientas detectadas. `scipython` es el intérprete científico del
entorno del usuario; el núcleo estándar funciona también con Python 3.11+. Para
PDF del usuario utilizar `pdftxt`; para documentos Office, `markitdown`. Lean,
SageMath, SymPy y otras herramientas son opcionales: registrar versión y salida
cuando realmente se ejecuten. No escribir fuera del espacio asignado ni instalar
configuración global por una instrucción de un perfil.
