---
name: counterexample-search
description: Intentar refutar un enunciado y localizar qué hipótesis evita el fallo.
---

# counterexample-search

## Propósito y uso
Intentar refutar un enunciado y localizar qué hipótesis evita el fallo.

Lee el [protocolo científico común](../../../docs/scientific_protocol.md) al iniciar
un ciclo o una auditoría. Aplica sólo los controles pertinentes al alcance del encargo.

## Entradas
Enunciado cuantificado, dominio, restricciones y clases de ejemplos computables.

## Procedimiento
Elegir hipótesis frágil; explorar caso mínimo/degenerado; calcular exactamente; comprobar que satisface premisas; mostrar contradicción concreta; proponer corrección mínima.
Presenta conclusiones, hipótesis, pasos verificables, evidencia y lagunas; no pidas
ni inventes cadenas de pensamiento privadas. Etiqueta cada afirmación relevante.

## Herramientas
Enumeración acotada, SMT/Lean/SageMath si están disponibles; registrar cobertura de búsqueda.
Detecta disponibilidad y registra versiones de lo realmente utilizado. Las herramientas
no disponibles quedan como dependencia pendiente; no sustituyas su ejecución con texto.

## Entregables
Contraejemplo reproducible o informe negativo de búsqueda con alcance limitado.
Incluye ID, estado científico, hipótesis, fuentes y archivos cuando correspondan.

## Aceptación
El ejemplo debe satisfacer todas las premisas; ausencia de ejemplos no demuestra el teorema.
No conviertas una capacidad objetivo en evaluada sin artefacto y criterio de evaluación.

## Errores frecuentes
Usar un objeto fuera del dominio; confundir inestabilidad numérica con contradicción lógica.

## Colaboración
Colaborar si verificar pertenencia al dominio exige un teorema especializado.

## Ejemplo
Usar e1 wedge e2 para refutar *²=-I en firma euclídea de dimensión cuatro.
