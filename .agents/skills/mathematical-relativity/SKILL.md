---
name: mathematical-relativity
description: Desarrollar o auditar resultados de relatividad con hipótesis geométricas explícitas.
---

# mathematical-relativity

## Propósito y uso
Desarrollar o auditar resultados de relatividad con hipótesis geométricas explícitas.

Lee el [protocolo científico común](../../../docs/scientific_protocol.md) al iniciar
un ciclo o una auditoría. Aplica sólo los controles pertinentes al alcance del encargo.

## Entradas
Variedad, métrica, firma, conexión, regularidad, fuente y datos iniciales/de contorno.

## Procedimiento
Fijar convenciones de Riemann/Ricci; escribir restricciones; verificar identidades de Bianchi; analizar causalidad; contrastar una solución o límite.
Presenta conclusiones, hipótesis, pasos verificables, evidencia y lagunas; no pidas
ni inventes cadenas de pensamiento privadas. Etiqueta cada afirmación relevante.

## Herramientas
Cálculo tensorial reproducible; SymPy/SageMath opcionales.
Detecta disponibilidad y registra versiones de lo realmente utilizado. Las herramientas
no disponibles quedan como dependencia pendiente; no sustituyas su ejecución con texto.

## Entregables
Ecuaciones con convenciones, restricciones y verificación de solución.
Incluye ID, estado científico, hipótesis, fuentes y archivos cuando correspondan.

## Aceptación
Contracciones, unidades y condiciones de realidad deben coincidir con las convenciones declaradas.
No conviertas una capacidad objetivo en evaluada sin artefacto y criterio de evaluación.

## Errores frecuentes
Cambiar signo de curvatura a mitad de cálculo; ignorar restricciones o asumir completitud global.

## Colaboración
Colaborar con PDE para existencia y con geometría global para extensiones/causalidad.

## Ejemplo
Calcular Ricci de una métrica propuesta antes de llamarla solución de vacío.
