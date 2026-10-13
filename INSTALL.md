# INSTALL — guion para el agente (Claude Desktop o app de Codex)

Lo sigue el agente cuando el usuario pega el bloque de instalación del README. Habla con el usuario en su idioma, explica cada paso en una frase, y **pide permiso explícito antes de**: clonar, instalar software, cambiar configuración de extensiones, registrar tareas programadas y enviar postulaciones. Nunca pidas ni teclees contraseñas: los inicios de sesión los hace el usuario.

Al empezar, di: "Voy a instalar **GetMeAJob 1.0 by Criptochairo**. Son 6 pasos (~10 min de setup + ~30–45 min de entrevista). Puedes pausar cuando quieras y retomamos donde quedamos."

## Paso 1 — Clonar
1. Detecta el sistema (Windows o macOS) y si hay `git` (`git --version`).
   - Falta git → ofrece instalarlo: Windows `winget install --id Git.Git -e`; macOS `xcode-select --install`. Pide permiso; espera a que termine.
2. Propón la carpeta `Documentos/GetMeAJob` (`%USERPROFILE%\Documents\GetMeAJob` o `~/Documents/GetMeAJob`); el usuario puede elegir otra. Si ya existe con un clon, sáltate al paso 2 (`git pull`).
3. Con su OK: `git clone https://github.com/criptochairo/getmeajob.git "<carpeta>"`.
   - Si el sandbox bloquea la red (Codex), pide la aprobación para ese comando.
4. A partir de aquí trabaja dentro de esa carpeta; lee `AGENTS.md`.

## Paso 2 — Entorno (`gmaj doctor`)
1. Si no hay `uv`: ofrece instalarlo (Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`; macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`). uv instala Python solo; no hace falta instalar Python a mano. Tras instalarlo puede que haya que abrir una terminal nueva o usar la ruta completa (`~/.local/bin/uv`).
2. `uv sync` y luego `uv run gmaj init` (crea `user/`, privado y fuera de git).
3. **Motor:** detecta qué tiene el usuario y pregúntale para confirmar:
   - Solo Claude → `uv run gmaj engines set claude`. Solo Codex → `codex`. Ambos → explica que lo normal es usar uno; `dual` significa dos suscripciones, turnos de navegador y revisión cruzada entre ambos. Solo si lo pide: `dual`.
4. `uv run gmaj doctor --json` y, para cada `ERR`, explica el arreglo (`fix`) y pide permiso antes de correrlo. Puntos típicos:
   - **Google Chrome** (lo usa la extensión y genera los PDF).
   - **CLI del motor** (`claude` o `codex`) — **obligatorio**: con él corren el scoring, la adaptación y la revisión con contexto limpio (quien adapta nunca revisa). Explica que es el mismo producto que ya usa, en versión de terminal, con su misma cuenta; tras instalarlo, el usuario inicia sesión una vez (`claude` o `codex login`).

## Paso 3 — Chrome y extensión del navegador
Sigue `docs/setup-chrome.md` con el usuario, paso a paso:
- **Claude:** instalar **Claude in Chrome** desde la Chrome Web Store, iniciar sesión con su cuenta de Claude, y en Claude Desktop conectar Chrome. Verifica leyendo las pestañas abiertas.
- **Codex:** instalar la extensión de Chrome de Codex/ChatGPT, activar **"Permitir acceso a URLs de archivo"** (chrome://extensions → Detalles; necesario para adjuntar el CV), y aprobar los sitios de `catalogs/channels.yaml` (LinkedIn, Indeed, OCC, Computrabajo, ATS).
- El usuario inicia sesión **él mismo** en: LinkedIn, Indeed, OCC y Computrabajo (los que use) y Gmail. Tú solo verificas abriendo cada sitio en una pestaña nueva y confirmando que la sesión está activa; luego cierras esas pestañas.
- Correo (opcional): conector de Gmail en Claude, o plugin de Gmail en Codex, en modo lectura.

## Paso 4 — Entrevista, roles y CVs
1. Skill **gmaj-onboarding** (entrevista).
2. Skill **gmaj-suggest-roles** (familias de rol con conteos reales).
3. Skill **gmaj-build-profile** (search.yaml, CVs y cartas; revisión cruzada; aprobación expresa del usuario).
4. `uv run gmaj validate` debe salir OK.

## Paso 5 — Corrida diaria (con permiso)
Explica: cada mañana se descubren vacantes sin IA (~30 min, gratis), y una hora después el agente califica, adapta y prepara o envía. La computadora debe estar encendida y la app abierta a esa hora.
1. Hora: `search.yaml operation.discover_time` (p. ej. 08:30) y `run_time` (09:30). Pregunta si le acomodan.
2. Descubrimiento en el sistema operativo: `uv run gmaj schedule install --time <discover_time>` (Windows: Programador de tareas, solo con sesión iniciada; macOS: LaunchAgent; si la PC estaba dormida, corre al despertar).
3. Tarea de la app, en la carpeta del proyecto, con la instrucción **"Ejecuta la skill gmaj-daily (corrida desatendida)."**, diaria a `run_time`:
   - **Claude Desktop:** pestaña Code → Routines → New routine → Local (o pídelo en una sesión: "programa una tarea local diaria a las 9:30 en esta carpeta que ejecute la skill gmaj-daily"). Activa "Keep computer awake" en Settings → This computer. Haz **Run now** con el usuario y elige "always allow" en cada permiso, para que las siguientes corridas no se detengan.
   - **App de Codex:** crea una tarea programada (Scheduled) en este proyecto con esa instrucción; modo de permisos `workspace-write` con acceso a la red para el navegador si la app lo pide. Haz una corrida manual para aprobar permisos.
   - **Modo avanzado (sin app abierta):** `uv run gmaj schedule install --kind daily --time <run_time>` corre `gmaj run-daily` con el CLI del motor.
4. Explica el **modo supervisado**: las primeras ~10 postulaciones esperan su visto bueno en `user/inbox/por_aprobar.md`; basta con abrir el proyecto y decir "pendientes".

## Paso 6 — Cierre
Resume en 5 líneas qué quedó listo y cómo seguir:
- Abrir la carpeta GetMeAJob como proyecto en Claude Desktop/Codex.
- Frases útiles: "pendientes", "¿cómo va?", "corre la búsqueda de hoy", "agrega a mi perfil...", "ya no quiero...".
- Actualizar la herramienta: `uv run gmaj update`.
- Sus datos están solo en `user/` (respáldalo si quiere; no lo subas a un repo público).
