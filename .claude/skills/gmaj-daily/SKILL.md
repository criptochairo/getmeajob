---
name: gmaj-daily
description: Corrida diaria de GetMeAJob - lee lo descubierto, califica, verifica modalidad en el navegador, adapta, revisa, envía (o deja para aprobación en modo supervisado) y reporta. Úsala desde la tarea programada diaria o cuando el usuario diga "corre la búsqueda de hoy".
---

# Corrida diaria

Reglas: `AGENTS.md`. Si la corrida es desatendida, **no hagas preguntas**: todo lo que requiera al usuario va a `user/inbox/`. Ahorra tokens: lee solo lo necesario, usa `uv run gmaj` para lo mecánico.

## 0. Guardas
- `uv run gmaj validate`: si falla, escribe el motivo en `user/reports/<fecha>.md` y termina.
- Si ya existe `user/reports/<fecha>.md` con "Corrida completa", termina (evita doble corrida). Si son más de las 20:00, haz solo descubrimiento y reporte.
- Lee `user/data/discover_done.json`. Si no es de hoy, corre `uv run gmaj discover` en segundo plano (puede tardar 30+ min por las esperas de LinkedIn); **nunca lances dos a la vez**. Mientras, avanza con el paso 1b.
- Modo y canales: `uv run gmaj engines` y `uv run gmaj autonomy`. Revisa `catalogs/channels.yaml` para tu motor.

## 1. Descubrimiento extra
a. **Correo** (si hay conector/plugin de Gmail): `uv run gmaj mail` (o sigue `prompts/mail_triage.md` en la sesión). Si existe `user/data/mail_leads.json`: `uv run gmaj add-jobs user/data/mail_leads.json`.
b. **OCC / Indeed** (solo si están en `search.yaml sources` con `browser: true`): en una pestaña nueva del sitio con sesión iniciada, pega el resultado de `uv run gmaj collector occ` (o `indeed`) en la herramienta de JavaScript; espera consultando `window.__occ_done` / `window.__indeed_done` (≤ 10 s por consulta); lee las páginas; arma el JSON para `uv run gmaj add-jobs <archivo>`. Indeed tarda ~15–20 min por su ritmo humano: deja esa pestaña en primer plano (en segundo plano Chrome la congela), sigue el avance en `window.__indeed_progress` y mientras haz trabajo sin navegador (scoring). Si termina con `blocked: true`, inserta lo parcial, anótalo en el reporte y no lo relances ese día. Ver `docs/browser-quirks.md`. Cierra la pestaña. **Verificaciones** (Cloudflare "verifica que eres humano", CAPTCHA): nunca las saltes ni intentes resolverlas; deja esa pestaña abierta para el usuario, anota la URL en el reporte y en `user/inbox/tareas_humanas.md`, y sigue.
c. `uv run gmaj prefilter`.

## 2. Scoring
`uv run gmaj score run` (lotes con el modelo barato del rol `score`). Si sale con código 75 (límite), sigue con lo ya calificado.

## 3. Selección y verificación de modalidad
- `uv run gmaj top --limit <limits.tailor_per_day>` (idempotente).
- Para cada carpeta de LinkedIn/Indeed/OCC: abre la vacante con sesión iniciada y lee la modalidad real (Remoto/Híbrido/Presencial), ubicación y si es Easy Apply o externa. Las búsquedas públicas marcan como remoto lo que no lo es. No cumple reglas de `work_mode` → `uv run gmaj set-status <id> discarded --note "<motivo>"`; zona "ask" → `needs_user` + entrada en `tareas_humanas.md`.

## 4. Adaptación y revisión cruzada
- Score ≥ 75: `uv run gmaj tailor <carpetas> --high`; el resto: `uv run gmaj tailor <carpetas>` (lotes de ~8).
- `uv run gmaj check <carpetas>`; corrige los FAIL solo con datos del perfil o marca `needs_user`.
- `uv run gmaj review <carpetas>` (otra llamada, contexto limpio; en modo dual la hace el otro motor). `reject` → `set-status rejected` y mueve la carpeta a `user/applications/_rejected/`. `changes` → aplica solo correcciones respaldadas, vuelve a renderizar el PDF y repite `check` + `review` **una vez**; si aún no sale `approve`, `needs_user` con el motivo.
- Solo las que tienen `review.json` con `approve` y `check` OK pasan al paso 5:
  - **Supervisado:** `set-status <id> reviewed` (lista para que el usuario la vea). **Nunca** `approved`: ese estado lo pone solo la aprobación del usuario en gmaj-inbox, y gmaj-apply envía lo que esté `approved`.
  - **Piloto automático:** `set-status <id> approved`.

## 5. Envío o aprobación
- **Supervisado** (`autonomy: supervised`): NO envíes. Agrega cada una (estado `reviewed`) a `user/inbox/por_aprobar.md` (número, empresa, rol, URL, score, canal, ruta del PDF, 3 respuestas clave, salario que se pondrá). Opcional: llena el formulario hasta antes de enviar solo si el sitio guarda borradores.
- **Piloto automático**: sigue la skill **gmaj-apply** con las aprobadas, respetando `uv run gmaj cap <canal>` y `uv run gmaj pace`.
- Modo dual, **solo en piloto automático** (en supervisado no se envía nada en esta corrida): el turno de navegador lo toma un motor a la vez (`user/state/browser.lock`); los ATS largos (`assign.apply`) los envía ese motor con `uv run gmaj run-role apply --chrome --prompt-file <prompt con prompts/apply.md + carpetas>`; espera a que termine antes de tocar el navegador.

## 6. Reporte
Escribe `user/reports/<fecha>.md`: fuentes con errores o 0 resultados (`user/data/fetch_report.json`; si LinkedIn está en pausa por bloqueo — `user/data/linkedin_guest_cooldown.json` — dilo y que las alertas por correo cubren el hueco), nuevas / filtradas / calificadas, carpetas creadas, enviadas, por aprobar, escaladas (con motivo), correos importantes, consumo (`user/logs/usage.jsonl` de hoy). Última línea: "Corrida completa". Cierra todas tus pestañas.
