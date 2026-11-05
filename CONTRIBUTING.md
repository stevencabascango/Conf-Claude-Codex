# Contribuir

Describe un problema delimitado, sus hipótesis y una comprobación reproducible.
Separa cambios de infraestructura de afirmaciones científicas. Ejecuta
`python3 scripts/check.py` antes de proponer cambios.

Modifica el catálogo en `genius/catalogue.py` y regenera con `python3 -m genius generate`.
Conserva la distribución exacta y documenta cambios de versiones/IDs. Cambia las
habilidades canónicas en `.agents/skills/` y conserva los enlaces Claude.

Cada afirmación científica lleva ID, estado, hipótesis, fuentes verificadas,
archivos, dependencias y revisión. Una refutación es un resultado válido. Una
objeción no resuelta impide promoción. Documenta el alcance de búsquedas antes
de afirmar novedad. Nunca incluyas secretos, datos privados ni afiliaciones falsas.

Las auditorías del instituto son internas. Registra revisiones externas por
separado. Las pruebas de software no acreditan excelencia científica individual.
