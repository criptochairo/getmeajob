# INSTALL — guion para el agente (Claude Desktop o app de Codex)

Lo sigue el agente cuando el usuario pega el bloque de instalación del README. Habla con el usuario en su idioma y explica cada paso en una frase. No pidas permisos sueltos: al empezar cada etapa explica en palabras sencillas qué vas a hacer y pide **una sola confirmación** ("Voy a…, ¿está bien?"): instalación (paso 1), Chrome (paso 3), grupos de búsqueda y CVs (paso 4) y horario de la corrida diaria (paso 5); enviar postulaciones se confirma aparte. Nunca por cada programa, comando, extensión o sitio. Ver `AGENTS.md` → "Cómo avanzar con el usuario". Nunca pidas ni teclees contraseñas: los inicios de sesión los hace el usuario.

## Paso 0 — Bienvenida (antes de revisar o instalar nada)
Muestra la pantalla de bienvenida **tal cual**, dentro de un bloque de código para que el arte se vea alineado: el contenido de `docs/welcome.txt` (si todavía no está clonado, léelo de `https://raw.githubusercontent.com/criptochairo/getmeajob/main/docs/welcome.txt`). No la resumas ni la traduzcas, salvo que el usuario hable otro idioma. Después pregunta: "¿Empezamos con el paso 1?". Si el usuario tiene dudas, respóndelas antes de seguir. Más adelante puede volver a verla con `uv run gmaj welcome`.

## Paso 1 — Revisar qué falta y confirmar todo de una vez
1. Revisa en silencio, sin pedir permiso (solo lectura): sistema (Windows o macOS), `git --version`, `uv --version` (también `~/.local/bin/uv`), si hay Google Chrome, `claude --version` y `codex --version`, y si la carpeta destino ya tiene un clon.
2. Muestra **una sola lista breve** con lo que hace falta, marcando lo que ya está, y pide **una sola confirmación para todo**. Ejemplo:

   > Para funcionar, GetMeAJob necesita lo siguiente en tu computadora:
   > - ✅ Git (ya instalado)
   > - ⬇️ uv — instala Python y las librerías del proyecto por su cuenta
   > - ✅ Google Chrome (ya instalado)
   > - ⬇️ Claude Code en terminal (`claude`) — el mismo Claude que ya usas, con tu misma cuenta
   > - ⬇️ Descargar GetMeAJob en `Documentos/GetMeAJob` y sus librerías de Python
   >
   > Voy a instalar lo que falta y descargar GetMeAJob en `Documentos/GetMeAJob`. Tarda unos 5 minutos y te voy avisando. ¿Está bien, o quieres cambiar algo (p. ej. la carpeta)?

   - Carpeta propuesta: `%USERPROFILE%\Documents\GetMeAJob` o `~/Documents/GetMeAJob`; el usuario puede elegir otra.
   - CLI del motor: incluye el del producto en el que estás (Claude → `claude`; Codex → `codex`). Si el usuario tiene ambos y quiere `dual`, se agrega después en el paso 2.
3. Con ese **sí**, ejecuta todo seguido, sin volver a preguntar, avisando en una línea qué va instalándose. Comandos (los mismos de `gmaj doctor`):
   - git: Windows `winget install --id Git.Git -e`; macOS `xcode-select --install`.
   - uv: Windows `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`; macOS `curl -LsSf https://astral.sh/uv/install.sh | sh`. No hace falta instalar Python a mano. Tras instalarlo usa la ruta completa (`~/.local/bin/uv`) si la terminal aún no lo ve.
   - Chrome: Windows `winget install --id Google.Chrome -e`; macOS `brew install --cask google-chrome` o https://www.google.com/chrome/.
   - CLI: Claude → Windows `powershell -c "irm https://claude.ai/install.ps1 | iex"`, macOS `curl -fsSL https://claude.ai/install.sh | bash`; Codex → `npm install -g @openai/codex` (en Windows requiere Node: `winget install --id OpenJS.NodeJS.LTS -e`) o `brew install codex`.
   - `git clone https://github.com/criptochairo/getmeajob.git "<carpeta>"` (si ya existe el clon: `git pull`), luego dentro de la carpeta `uv sync` y `uv run gmaj init` (crea `user/`, privado y fuera de git).
   - Si algo falla, explica el error en una frase y sigue con lo demás; al final reporta qué quedó pendiente.
4. Aviso de la app: Claude Desktop o Codex pueden mostrar su propio cuadro de aprobación por cada comando (eso no lo controla este guion). Antes de empezar, dile al usuario que puede elegir "permitir siempre" / aprobar la sesión para que no se le pregunte uno por uno. Si el sandbox bloquea la red (Codex), pide esa aprobación una vez.
5. A partir de aquí trabaja dentro de la carpeta; lee `AGENTS.md`.

## Paso 2 — Motor y verificación (`gmaj doctor`)
1. **Motor:** confirma con el usuario:
   - Solo Claude → `uv run gmaj engines set claude`. Solo Codex → `codex`. Ambos → explica que lo normal es usar uno; `dual` significa dos suscripciones, turnos de navegador y revisión cruzada entre ambos. Solo si lo pide: `dual` (y, si falta el segundo CLI, instálalo: ya va dentro de lo que confirmó).
2. `uv run gmaj doctor --json`. Debe salir sin `ERR`; si queda alguno, corre su `fix` sin volver a preguntar (ya está confirmado), salvo que sea algo que el usuario no aprobó en la lista.
3. El usuario inicia sesión una vez en el CLI del motor (`claude` o `codex login`); él teclea sus datos. Explica que con ese CLI corren el scoring, la adaptación y la revisión con contexto limpio (quien adapta nunca revisa).

## Paso 3 — Chrome y extensión del navegador (una sola confirmación)
Referencia completa: `docs/setup-chrome.md`. Se usa siempre Google Chrome con la extensión del motor; no ofrezcas el navegador integrado de la app.

1. Pregunta qué portales usa (LinkedIn, Indeed, OCC, Computrabajo) y si quiere conectar su correo (opcional). Con eso, muestra **una sola lista** dividida en dos partes y pide **una sola confirmación** para todo:

   > **Lo que haré yo:**
   > - Abrir en Chrome la página de la extensión (Claude in Chrome / extensión de Codex) para que la instales.
   > - Abrir pestañas nuevas con LinkedIn, Indeed, OCC, Computrabajo y Gmail para que inicies sesión, revisar que la sesión quedó activa y cerrar esas pestañas.
   > - (Codex) Abrir `chrome://extensions` en la extensión correcta para el ajuste de archivos.
   > - (Opcional) Conectar Gmail en modo solo lectura.
   >
   > **Lo que te toca a ti (te guío en cada uno):**
   > - Clic en "Agregar a Chrome" e iniciar sesión en la extensión.
   > - (Claude) Conectar Chrome en Claude Desktop. (Codex) Activar "Permitir acceso a URLs de archivo".
   > - Iniciar sesión tú en cada portal y en Gmail (yo nunca tecleo contraseñas ni códigos).
   > - Cuando la extensión pregunte por cada sitio, elegir **"Permitir siempre"**.
   >
   > Empiezo con lo mío y te voy guiando en lo tuyo, un paso a la vez. ¿Está bien, o quieres cambiar algo?

2. Con ese **sí**, no vuelvas a preguntar en este paso. Avanza por la parte del usuario **de a un punto**: di exactamente qué hacer y dónde dar clic, espera a que diga "listo" (o compruébalo tú) y pasa al siguiente. Si se atora, explícale con más detalle; no te saltes ningún punto suyo.
   - **Claude:** Claude in Chrome desde la Chrome Web Store (publicada por Anthropic), fijarla en la barra, iniciar sesión con la misma cuenta de Claude Desktop, y en Claude Desktop conectar Chrome (o `/chrome`). Verifica leyendo las pestañas abiertas.
   - **Codex:** extensión de Codex/ChatGPT, iniciar sesión, activar **"Permitir acceso a URLs de archivo"** (chrome://extensions → Detalles; necesario para adjuntar el CV), y aprobar los sitios de `catalogs/channels.yaml` cuando la app los pida.
3. Sesiones: abre **todos** los portales elegidos y Gmail a la vez, en pestañas nuevas, para que el usuario inicie sesión y apruebe los permisos de sitio de una tanda. Luego verifica cada sesión y cierra esas pestañas. Reporta en una lista qué quedó listo y qué falta.
4. Correo (opcional, si lo incluyó): conector de Gmail en Claude, o plugin de Gmail en Codex, en modo lectura.
5. Guarda el resultado en `user/onboarding/setup.json` para que la entrevista no lo vuelva a preguntar: `{"channels_with_account": [...], "channels_missing_session": [...], "gmail_read": true|false, "updated": "<fecha>"}`.

## Paso 4 — Entrevista, roles y CVs
La elección de grupos (familias de rol), los CVs y las alertas de LinkedIn son **una sola etapa con una sola confirmación** (la pide gmaj-suggest-roles en su paso 5); gmaj-build-profile ya no vuelve a preguntar hasta mostrar los CVs terminados.
1. Skill **gmaj-onboarding** (entrevista).
2. Skill **gmaj-suggest-roles** (familias de rol con conteos reales).
3. Skill **gmaj-build-profile** (search.yaml, CVs y cartas; revisión cruzada; aprobación expresa del usuario).
4. `uv run gmaj validate` debe salir OK.

## Paso 5 — Corrida diaria (una sola confirmación)
Explica: cada mañana se descubren vacantes sin IA (~30 min, gratis), y una hora después el agente califica, adapta y prepara o envía. La computadora debe estar encendida y la app abierta a esa hora.
1. Hora: `search.yaml operation.discover_time` (p. ej. 08:30) y `run_time` (09:30). Anúncialo todo de una vez: "Voy a programar que cada mañana a las 8:30 se busquen vacantes nuevas y a las 9:30 se preparen tus postulaciones; tu compu tiene que estar encendida a esa hora. ¿Te acomoda ese horario?". Con ese sí, haz los puntos 2 y 3 sin volver a preguntar (salvo los cuadros de permiso propios de la app).
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
