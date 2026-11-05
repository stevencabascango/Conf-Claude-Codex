---
name: research-memory
description: Conservar afirmaciones, evidencias y dependencias científicas en memoria versionada.
---

# research-memory

## Propósito y uso
Conservar afirmaciones, evidencias y dependencias científicas en memoria versionada.

Lee el [protocolo científico común](../../../docs/scientific_protocol.md) al iniciar
un ciclo o una auditoría. Aplica sólo los controles pertinentes al alcance del encargo.

## Entradas
Resultado con ID, estado, hipótesis, fuentes, archivos, revisiones y dependencias.

## Procedimiento
Validar enlaces e IDs; registrar evento inmutable; conservar estatus y versiones; actualizar dependencias; propagar revisión cuando cambian; registrar siguiente paso.
Presenta conclusiones, hipótesis, pasos verificables, evidencia y lagunas; no pidas
ni inventes cadenas de pensamiento privadas. Etiqueta cada afirmación relevante.

## Herramientas
JSON/JSONL y git; hashes de archivos; base de datos opcional no requerida.
Detecta disponibilidad y registra versiones de lo realmente utilizado. Las herramientas
no disponibles quedan como dependencia pendiente; no sustituyas su ejecución con texto.

## Entregables
Registro enlazado de definiciones, problemas, pruebas, contraejemplos, auditorías y preguntas abiertas.
Incluye ID, estado científico, hipótesis, fuentes y archivos cuando correspondan.

## Aceptación
No guardar un resultado como demostrado sin auditoría requerida; preservar historia de refutaciones.
No conviertas una capacidad objetivo en evaluada sin artefacto y criterio de evaluación.

## Errores frecuentes
Sobrescribir desacuerdos; referencias rotas; cambiar dependencia sin invalidar descendientes.

## Colaboración
Consultar auditor y mantenedor si hay conflicto de estados o ciclos de dependencias.

## Ejemplo
Marcar EN REVISIÓN un corolario cuando cambia la hipótesis del lema del que depende.
