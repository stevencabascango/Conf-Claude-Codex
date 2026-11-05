# Orquestación

El código ejecutable está en `genius/planning.py`, `genius/orchestration.py` y
`genius/adapters.py`. Este directorio documenta su configuración sin duplicarlo.

Valores por defecto: concurrencia2, máximo14 llamadas/intentos, 120 segundos
globales, 25 por tarea, un reintento, 120000 bytes por petición y 200000 bytes de
captura por proceso. Cada ejecución recibe una ficha y las habilidades pertinentes.
Las condiciones de parada son presupuesto agotado, tareas completas, dependencias
fallidas o intentos consumidos. Un resultado negativo científico puede completar
una tarea; un error de software queda fallido con sus logs.

Los checkpoints de cada ciclo quedan en su salida; no se ejecutan automáticamente
los 5.000 perfiles. Los campos registrados, seleccionados, procesos ejecutados,
agentes LLM confirmados, ejecuciones terminadas y resultados revisados son distintos.
