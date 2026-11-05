---
name: physical-consistency-audit
description: Auditar dimensiones, restricciones, estabilidad y alcance físico de un modelo.
---

# physical-consistency-audit

## Propósito y uso
Auditar dimensiones, restricciones, estabilidad y alcance físico de un modelo.

Lee el [protocolo científico común](../../../docs/scientific_protocol.md) al iniciar
un ciclo o una auditoría. Aplica sólo los controles pertinentes al alcance del encargo.

## Entradas
Acción/ecuaciones, unidades, firma, campos, gauge, contorno y régimen de aproximación.

## Procedimiento
Comprobar unidades y signos; variar acción; contar restricciones/modos; examinar positividad y causalidad; probar límites; identificar anomalías.
Presenta conclusiones, hipótesis, pasos verificables, evidencia y lagunas; no pidas
ni inventes cadenas de pensamiento privadas. Etiqueta cada afirmación relevante.

## Herramientas
Álgebra simbólica y espectros linealizados si están disponibles.
Detecta disponibilidad y registra versiones de lo realmente utilizado. Las herramientas
no disponibles quedan como dependencia pendiente; no sustituyas su ejecución con texto.

## Entregables
Lista de controles con evidencia, fallo mínimo y consecuencias sobre afirmaciones dependientes.
Incluye ID, estado científico, hipótesis, fuentes y archivos cuando correspondan.

## Aceptación
No concluir consistencia total a partir de un solo control; delimitar régimen y órdenes calculados.
No conviertas una capacidad objetivo en evaluada sin artefacto y criterio de evaluación.

## Errores frecuentes
Cambiar firma silenciosamente; omitir modo fantasma; llamar observable a una variable gauge.

## Colaboración
Consultar análisis funcional, QFT o relatividad para dominios y anomalías difíciles.

## Ejemplo
Detectar que un término de masa tiene el signo incompatible con estabilidad en la firma declarada.
