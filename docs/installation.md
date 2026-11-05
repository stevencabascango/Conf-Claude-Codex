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

El contenido remoto no pudo inspeccionarse: Git falló con `Could not resolve host:
github.com` y la consulta web no devolvió el repositorio. La implementación local
no reemplaza contenido remoto desconocido.

Con red y GitHub CLI autenticado, revisa primero los archivos y ejecuta:

```bash
python3 scripts/publish.py
```

El script comprueba repositorio/usuario, crea el repositorio **privado** si confirma
que falta, exige un árbol limpio y un commit local, e inspecciona referencias. Si
hay historia remota desconocida se detiene para su integración, preservando ambos
contenidos. Nunca usa `--force`, elimina ramas o publica credenciales. La orden
de creación/publicación está autorizada por el encargo, pero su éxito depende del
acceso real; sólo una comprobación posterior del SHA remoto permite confirmarlo.
