# Límites y tareas pendientes

- Los 5.000 perfiles están registrados y estructuralmente comprobados. Su
  excelencia y utilidad científica individual son objetivos pendientes de
  evaluación; la diversidad combinatoria no acredita originalidad científica.
- La referencia exacta comprueba infraestructura y un resultado conocido de
  álgebra lineal. No demuestra novedad, capacidad para resolver Googly ni
  equivalencia física o recuperación de Einstein.
- Las revisiones son internas. Procesos distintos pueden compartir código,
  entrenamiento y errores. Las revisiones externas se registran por separado.
- Los adaptadores Claude/Codex ejecutan las CLIs si existe acceso. La disponibilidad
  local del binario no acredita autenticación o un informe terminado. Los resultados
  de texto libre requieren ingesta crítica antes de crear afirmaciones en memoria.
- Presupuestos estrictos de llamadas/tiempo/bytes tienen alcance del coordinador.
  No hay un límite duro de tokens/coste Codex verificado; no se promete.
- No se ejecutaron Lean/Sage/otros verificadores para el benchmark: usa Fraction
  exacta. Esas herramientas se detectan o quedan como dependencia explícita.
- La memoria comprueba registros y hashes, no la verdad de pruebas. La verificación
  formal requiere archivos, versión, comando y log reales además de revisión.
- La lectura remota GitHub está comprobada, pero la integración de ChatGPT rechazó
  escritura con403. La terminal del agente sigue sin DNS/gh; publicación pendiente.
  `scripts/connect_and_publish.py` debe ejecutarse interactivamente desde WSL con
  Internet para autorizar GitHub CLI y publicar con el historial preservado.
- El validador auxiliar de skill-creator necesita PyYAML, ausente en este entorno.
  La validación autónoma de las 22 habilidades y TOML nativos sí está implementada.

Próximos pasos verificables: conectar CLIs con límites apropiados, evaluar perfiles
con problemas ciegos y rúbricas específicas, realizar una comparación real sellada
Claude–Codex y aportar pruebas formales para afirmaciones que se quieran formalizar.
