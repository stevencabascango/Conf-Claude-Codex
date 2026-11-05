# Instalación y operación

Trabaja desde la raíz del repositorio con Python3.11+. Todos los comandos funcionan
sin instalación ni bibliotecas externas. El ejecutable opcional se puede instalar
en un venv con `python -m pip install -e .`; eso requiere setuptools y no es
necesario para las pruebas o la demostración. El paquete de código requiere los
datos del checkout: conserva el repositorio y usa `--root /ruta/Conf-Claude-Codex`
si invocas `genius5000` desde otro lugar.

Para colocar una copia local en otro proyecto, conservando archivos existentes:

```bash
python3 -m genius install --target /ruta/proyecto --dry-run
python3 -m genius install --target /ruta/proyecto
```

El instalador nunca reemplaza un archivo existente, ni siquiera una configuración.
Informa conflictos y devuelve estado incompleto; resuélvelos mediante revisión.
Una segunda ejecución conserva lo idéntico. No escribe en `~/.codex/config.toml`
ni en configuraciones globales de Claude. Las habilidades se descubren desde la
raíz del proyecto; los enlaces relativos mantienen un único núcleo.

## CLIs

La inspección local encontró `codex-cli 0.166.0` y `Claude Code 2.1.318`. Esto no
garantiza disponibilidad de cuenta, modelo ni red en otras instalaciones. Consulta
las [habilidades oficiales](https://learn.chatgpt.com/docs/build-skills),
[subagentes Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[subagentes Claude](https://code.claude.com/docs/en/sub-agents) y
[habilidades Claude](https://code.claude.com/docs/en/skills). Ejecuta `doctor` y
comprueba `--help` después de actualizar las CLIs.

El adaptador Codex usa `codex exec --json --ephemeral`; Claude usa `--print
--output-format json --no-session-persistence`. Ambos conservan autenticación,
modelo y políticas del entorno. No se copian secretos al repositorio. Se conservan
uso/modelos que la CLI reporte, sin deducirlos del nombre del perfil.

Límites de concurrencia, llamadas, reintentos, tiempo y bytes son explícitos.
`--max-usd` se distribuye conservadoramente entre el máximo de intentos Claude
mediante su flag documentado. Para Codex el comando lo rechaza; un límite de
tokens/dólares estricto requiere un adaptador/proveedor con ese control verificado.
El máximo de bytes limita la captura del coordinador, no todos los archivos que
un agente pueda crear dentro de su espacio autorizado.

## Publicación en GitHub

Durante la primera implementación no pudo inspeccionarse el remoto: Git falló con `Could not resolve host:
github.com` y la consulta web no devolvió el repositorio. La implementación local
no reemplazó contenido remoto desconocido.

Actualización: el conector permitió identificar la cuenta y leer el repositorio,
pero `create_blob` devolvió `403 Resource not accessible by integration`. No se
publicó nada. La [documentación oficial de OpenAI](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt)
indica que la app de GitHub en ChatGPT es de lectura. Conectar esa app no basta
para autorizar un push. El remoto inspeccionado sólo contiene el README inicial,
con commit `ea230a00ed58ee4225e255c52ffe48c0143aba83`.

Desde una terminal propia de Ubuntu/WSL con Internet:

```bash
python3 /home/asus/Conf-Claude-Codex/scripts/connect_and_publish.py
```

El asistente local conserva un `gh` existente. Si falta, descarga la versión
portable de la publicación oficial `cli/cli`, verifica su checksum publicado y
coloca sólo el ejecutable en `~/.local/bin/gh`, sin reemplazar archivos existentes.
La autorización se completa directamente en el navegador mediante el flujo
oficial `gh auth login --web`. Las credenciales quedan bajo la gestión de GitHub
CLI y no se solicitan ni copian al chat o al repositorio. No necesita sudo.
Se solicita el alcance `workflow` porque el proyecto contiene su archivo de CI
en `.github/workflows/`. Una sesión GitHub CLI preexistente necesita permisos
suficientes para publicar ese archivo, además del contenido del repositorio.

Con red y GitHub CLI autenticado, revisa primero los archivos y ejecuta:

```bash
python3 scripts/publish.py
```

El script comprueba repositorio/usuario, crea el repositorio **privado** si confirma
que falta, exige un árbol limpio y un commit local, e inspecciona referencias. Si
encuentra exclusivamente el README inicial ya inspeccionado, integra ambas
historias en un worktree temporal y conserva ese README en
`docs/README.remote-original.md`. Otros contenidos/conflictos se detienen para
revisión. El push es normal, sin forzar, y su SHA se verifica después. No elimina
ramas ni publica credenciales. El helper de credenciales se aplica sólo a la
invocación Git, sin cambiar la configuración global. La orden
de creación/publicación está autorizada por el encargo, pero su éxito depende del
acceso real; sólo una comprobación posterior del SHA remoto permite confirmarlo.
