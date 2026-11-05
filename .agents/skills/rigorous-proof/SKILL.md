---
name: rigorous-proof
description: Producir demostraciones auditables de enunciados matemáticos definidos.
---

# rigorous-proof

## Propósito y uso
Producir demostraciones auditables de enunciados matemáticos definidos.

Lee el [protocolo científico común](../../../docs/scientific_protocol.md) al iniciar
un ciclo o una auditoría. Aplica sólo los controles pertinentes al alcance del encargo.

## Entradas
Enunciado, dominios, hipótesis, resultados previos identificados y criterio de conclusión.

## Procedimiento
Aplicar Protocolo B; ordenar dependencias; justificar paso decisivo; controlar límites y extensiones; revisar hipótesis; presentar argumento completo o laguna exacta.
Presenta conclusiones, hipótesis, pasos verificables, evidencia y lagunas; no pidas
ni inventes cadenas de pensamiento privadas. Etiqueta cada afirmación relevante.

## Herramientas
Lean/SageMath/SymPy si aportan comprobación pertinente y están disponibles.
Detecta disponibilidad y registra versiones de lo realmente utilizado. Las herramientas
no disponibles quedan como dependencia pendiente; no sustituyas su ejecución con texto.

## Entregables
Enunciado y prueba con dependencias y estatus de cada parte.
Incluye ID, estado científico, hipótesis, fuentes y archivos cuando correspondan.

## Aceptación
Ningún paso decisivo puede ocultarse en «evidente»; marcar auditoría pendiente hasta revisión separada.
No conviertas una capacidad objetivo en evaluada sin artefacto y criterio de evaluación.

## Errores frecuentes
Razonamiento circular; cambiar cuantificadores; probar sólo un caso o un enunciado formal distinto.

## Colaboración
Pedir especialista para dominios analíticos, convergencia o resultados no verificados.

## Ejemplo
Demostrar un lema de álgebra lineal desde rango y núcleo, mostrando cada inclusión.
