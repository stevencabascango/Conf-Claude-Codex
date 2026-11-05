---
name: algebraic-geometry
description: Estudiar esquemas, haces y módulos con hipótesis geométricas declaradas.
---

# algebraic-geometry

## Propósito y uso
Estudiar esquemas, haces y módulos con hipótesis geométricas declaradas.

Lee el [protocolo científico común](../../../docs/scientific_protocol.md) al iniciar
un ciclo o una auditoría. Aplica sólo los controles pertinentes al alcance del encargo.

## Entradas
Cuerpo y característica, esquema/espacio, haz, finitud, suavidad y problema de módulos.

## Procedimiento
Fijar categoría; comprobar planitud o suavidad necesarias; calcular cohomología/Ext; construir morfismos; probar descenso y propiedades locales/globales.
Presenta conclusiones, hipótesis, pasos verificables, evidencia y lagunas; no pidas
ni inventes cadenas de pensamiento privadas. Etiqueta cada afirmación relevante.

## Herramientas
Macaulay2/Singular/SageMath opcionales con anillo y algoritmo registrados.
Detecta disponibilidad y registra versiones de lo realmente utilizado. Las herramientas
no disponibles quedan como dependencia pendiente; no sustituyas su ejecución con texto.

## Entregables
Construcción, lemas de base y cálculo reproducible de un ejemplo.
Incluye ID, estado científico, hipótesis, fuentes y archivos cuando correspondan.

## Aceptación
Cada cambio de base y uso de GAGA debe citar hipótesis; distinguir puntos de familias.
No conviertas una capacidad objetivo en evaluada sin artefacto y criterio de evaluación.

## Errores frecuentes
Confundir espacio de módulos grueso con stack; aplicar teoremas propios a abiertos no propios.

## Colaboración
Colaborar con análisis para espacios complejos no algebraizables y con deformaciones para obstrucciones.

## Ejemplo
Calcular Ext1 y Ext2 de un haz en una superficie algebraica especificada.
