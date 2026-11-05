# GENIUS-5000 · Conf-Claude-Codex

Instituto virtual para investigar gravedad cuántica, unificación y el problema de Googly con Claude Code y OpenAI Codex. Incluye **5.000 perfiles de diseño**, un selector de equipos, 22 habilidades compartidas, agentes nativos, ejecuciones acotadas y memoria científica con auditorías trazables.

«Genio» es una aspiración metodológica: **no acredita capacidades, títulos ni equivalencia con científicos históricos**. Las capacidades científicas individuales del catálogo están pendientes de evaluación. Registrar 5.000 perfiles no ejecuta 5.000 agentes.

## Empezar localmente

Requiere Python 3.11 o superior; el núcleo usa únicamente la biblioteca estándar. No necesita instalación global, claves API, `sudo` ni paquetes científicos para su demostración exacta.

```bash
cd Conf-Claude-Codex
python3 -m genius doctor
python3 scripts/check.py --output institute/evaluations/software_checks.json
python3 -m genius demo --output runs/hodge-example
```

La demostración selecciona siete perfiles y ejecuta siete procesos deterministas: formulación, matemáticas, física, cálculo, contraejemplo, auditoría e integración. Reconstruye el operador de Hodge en dos-formas de R⁴ euclídeo, comprueba sus subespacios de dimensión 3+3 y rechaza la afirmación deliberadamente incorrecta `*²=-I`. Registra el resultado, su revisión y la propagación de un cambio de dependencia. **Esta demostración no llama a un LLM ni resuelve el problema de Googly.**

Para un equipo pequeño y una selección inicial amplia:

```bash
python3 -m genius demo --team-size 3 --output runs/hodge-small
python3 -m genius plan 'Googly: precisar obstrucciones y régimen local' --team-size 30 --backend codex --output runs/googly-plan.json
python3 -m genius profile G5K-TWISTORS-0001
```

Los identificadores válidos están en [el registro](institute/registry/profiles.jsonl); consúltalos si cambia la convención de generación. Crear un plan no lo ejecuta.

## Distribución del catálogo

| División | Perfiles |
|---|---:|
| Relatividad general y geometría gravitatoria | 500 |
| LQG y espumas de espín | 500 |
| Cuerdas, supergravedad y teoría M | 450 |
| Twistores y Googly | 650 |
| Topología algebraica y homotopía | 550 |
| Geometría algebraica y derivada | 550 |
| QFT y teorías gauge | 500 |
| Categorías superiores y geometría no conmutativa | 350 |
| Verificación formal y computación científica | 500 |
| Integración, arbitraje y revisión | 450 |
| **Total** | **5.000** |

La diversidad se construye a partir de 100 líneas científicas específicas, cinco modalidades de investigación y diez tareas de comprobación. Se auditan campos, distribución, huellas semánticas, cobertura y contextos compartidos. La generación combinatoria aporta especializaciones de trabajo; su eficacia científica requiere evaluaciones individuales. Detalles y límites en [el registro](institute/registry/README.md).

## Ejecutar con Claude o Codex

Instala y autentica la CLI elegida mediante su procedimiento oficial. `doctor` distingue presencia del ejecutable de autenticación y ejecución efectivas. Se heredan modelo y permisos del usuario salvo un `--model` explícito. No se habilitan permisos de omisión del sandbox.

```bash
python3 -m genius plan 'Precisar una pregunta local sobre twistores y sus hipótesis' --backend codex --team-size 3 --output runs/codex-plan.json
python3 -m genius run runs/codex-plan.json --output runs/codex-cycle --concurrency 2 --max-calls 10 --max-seconds 300 --task-seconds 60 --retries 1
```

`--backend claude` usa Claude Code. Las llamadas, el tiempo y los bytes de entrada/salida tienen límites explícitos; Claude admite además `--max-usd`. Un presupuesto monetario estricto para Codex se rechaza porque no se ha verificado un control equivalente en su CLI. El uso de tokens se conserva cuando el proveedor lo informa. [Instalación y límites operativos](docs/installation.md).

Un fallo deja `checkpoint.json`, intentos y logs. Para recuperar, repite el mismo comando con `--resume`, el mismo plan y presupuesto. Nunca sobrescribe resultados terminados. Si un proceso previo sigue activo o su inicio es indeterminado, bloquea el reintento automático para evitar duplicar consumo.

## Investigación separada y revisión cruzada

```bash
python3 -m genius prepare-pair institute/configurations/common_brief.json --output runs/comparison-01
# Ejecutar fase 1 en los espacios claude/ y codex/ separados.
python3 -m genius seal-report runs/comparison-01 claude /ruta/informe-claude.json
python3 -m genius seal-report runs/comparison-01 codex /ruta/informe-codex.json
python3 -m genius prepare-cross-review runs/comparison-01
# Ejecutar las dos revisiones en NUEVOS contextos y cerrar sus informes.
python3 -m genius seal-review runs/comparison-01 claude /ruta/revision-claude.json
python3 -m genius seal-review runs/comparison-01 codex /ruta/revision-codex.json
python3 -m genius synthesize runs/comparison-01
```

Los informes se sellan con SHA-256. Sin ambos informes la comparación queda pendiente. Los desacuerdos se conservan. Esta separación de carpetas/contextos es administrativa: no garantiza independencia de errores ni constituye aislamiento de seguridad. [Protocolo y formatos](docs/claude_codex.md).

## Componentes y evidencia

- [Arquitectura](docs/architecture.md), [protocolo científico](docs/scientific_protocol.md) y [habilidades](docs/skills.md).
- [Matriz de los 14 requisitos de prueba](docs/acceptance_matrix.md) y [evaluaciones ejecutadas](institute/evaluations/).
- [Memoria versionada](memory/README.md): afirmaciones, revisiones, fuentes, obstrucciones y dependencias.
- [Limitaciones y trabajo pendiente](docs/limitations.md), [contribuciones](CONTRIBUTING.md).

El repositorio distribuye habilidades en `.agents/skills` y adaptadores TOML en `.codex/agents` conforme a la [documentación oficial de habilidades](https://learn.chatgpt.com/docs/build-skills) y [subagentes de Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents). Claude usa enlaces al mismo núcleo y [agentes Markdown](https://code.claude.com/docs/en/sub-agents).

## GitHub

Destino solicitado: [stevencabascango/Conf-Claude-Codex](https://github.com/stevencabascango/Conf-Claude-Codex). El repositorio remoto tiene un README inicial. La integración de ChatGPT permite leerlo, pero rechazó la escritura con `403 Resource not accessible by integration`; [OpenAI documenta esa restricción de lectura](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt).

Desde la raíz del repositorio, en tu **terminal de Ubuntu/WSL con Internet**, ejecuta:

```bash
python3 scripts/connect_and_publish.py
```

El comando instala GitHub CLI localmente si falta, comprueba el SHA-256 del paquete oficial, solicita la autorización en el navegador y ejecuta la publicación. Conserva ambos historiales y archiva el README remoto original. No usa `sudo` ni fuerza un push. [Detalles de instalación y publicación](docs/installation.md#publicación-en-github).
