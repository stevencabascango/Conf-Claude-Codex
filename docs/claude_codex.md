# Desarrollo separado y revisión cruzada

`prepare-pair` crea briefs idénticos con problema, convenciones, criterios,
documentación y presupuestos, en carpetas distintas. No permite sobrescribir una
comparación existente. Las ejecuciones de desarrollo usan contextos nuevos y no
leen el trabajo contrario. Esta restricción es una regla de investigación, no
una garantía criptográfica de aislamiento del filesystem del usuario.

Un informe cerrable es JSON con `status: completed`, `execution_id`, `model`
(null si no fue informado), `tools` y `claims` (ID, enunciado, estado, evidencia).
Los informes fallidos no satisfacen la comparación. `seal-report` guarda copia,
hash y fecha; el sellado no garantiza verdad ni atribución externa.

Sólo con ambos informes sellados `prepare-cross-review` entrega a cada entorno
el informe contrario y la tarea de reconstrucción. Ejecuta cada revisión en un
contexto nuevo y con presupuesto registrado. Un informe de revisión contiene:

```json
{
  "status": "completed",
  "execution_id": "identificador-de-la-nueva-ejecucion",
  "model": null,
  "tools": [],
  "reviewed_claims": [{
    "id": "CLAIM-001",
    "verdict": "incomplete",
    "reconstruction": "Paso reconstruido y laguna exacta",
    "evidence": ["ruta/al/artefacto"]
  }],
  "disagreements": ["Hipótesis global no justificada"],
  "next_checks": ["Construir un contraejemplo compacto"]
}
```

`seal-review` exige un ID distinto de ambas ejecuciones de desarrollo.
`synthesize` comprueba los hashes y conserva desacuerdos de informes y revisiones.
Sin ambas revisiones devuelve pendiente. La síntesis nunca convierte acuerdo en
demostración: la promoción pertenece a la memoria y su auditoría específica.

La ejecución de modelos requiere las CLIs y autenticación. El protocolo no
simula informes cuando un proveedor está ausente. Los fixtures de software que
validan este flujo se identifican como fixtures, no investigación real.
