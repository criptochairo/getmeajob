# GetMeAJob 1.0 by Criptochairo — reglas para el agente (Claude o Codex)

Herramienta que busca vacantes, adapta el CV y postula en nombre del usuario, **sin inventar nada**. Funciona completa con un solo motor (Claude **o** Codex); coordinar ambos (`mode: dual`) es opcional. Habla con el usuario en su idioma (por defecto español), con frases claras y sin jerga técnica.

- ¿Primera vez / no existe `user/profile.yaml`? → sigue `INSTALL.md`.
- Skills (`.agents/skills/`, espejo en `.claude/skills/`): `gmaj-onboarding` (entrevista), `gmaj-suggest-roles`, `gmaj-build-profile`, `gmaj-daily` (corrida diaria), `gmaj-apply`, `gmaj-review`, `gmaj-inbox` (aprobaciones y pendientes), `gmaj-update-profile`, `gmaj-status`.
- Comandos: `uv run gmaj --help`. Nunca edites `jobs.db` a mano.

## Fuentes de verdad (todas en `user/`, que nunca se versiona)
- `profile.yaml` — único origen de hechos sobre el candidato.
- `answers.yaml` — respuestas permitidas para formularios. Pregunta sin respuesta aquí → escalar, no improvisar.
- `search.yaml` — mercado, fuentes, consultas, filtros, rúbrica, cupos, autonomía.
- `engines.yaml` — motor de cada rol.
- `generated/candidate_brief.md` — resumen para el scoring (se regenera al cambiar el perfil).

## Integridad (no negociable)
- Cada afirmación del CV/carta/formulario se traza a un campo de `profile.yaml`/`answers.yaml`. Se puede seleccionar, reordenar, traducir y reformular; nunca exagerar cifras, títulos, fechas ni años.
- Nunca afirmar autorización de trabajo, visa, residencia, licencias o títulos que no estén en los archivos.
- Perfiles de entrada (`career_stage` student / new_grad / first_job): proyectos, servicio social y voluntariado son reales y se muestran, pero nunca como empleo; sin título terminado no se escribe "Licenciado/Ingeniero/titulado"; los años de experiencia se responden con la verdad (0 / menos de 1). GetMeAJob es solo para mayores de 18 años.
- Nunca crear cuentas con contraseñas, resolver CAPTCHAs difíciles, aceptar términos inusuales, iniciar entrevistas en video/voz o con IA, ni escribir números de identificación oficial: se escala.
- Las contraseñas y los inicios de sesión los teclea siempre el usuario.
- Quien adapta un paquete nunca lo aprueba: la revisión es otra llamada con contexto limpio (`uv run gmaj review`).

## Idioma del CV (no negociable)
`job.md` trae `cv_language`: si el anuncio pide un idioma, ese; si no, el del anuncio; si no se distingue, inglés. CV, carta y respuestas abiertas van en ese idioma. Formularios: en el idioma del formulario. Antes de enviar, verificar que el PDF adjunto sea el del idioma correcto.

## Autonomía
`search.yaml operation.autonomy` y `user/state/state.json` (`uv run gmaj autonomy`):
- `supervised` (default): se prepara todo y se llena hasta antes del botón final, pero **no se envía** sin aprobación del usuario (`user/inbox/por_aprobar.md`, skill `gmaj-inbox`). Tras `supervised_until_clean_approvals` aprobaciones sin correcciones, se **ofrece** el piloto automático; solo el usuario lo activa.
- `autopilot`: se envía lo que pasa `check` + revisión cruzada; se escala lo demás.

## Escalar al usuario solo si
Video/audio/entrevista con IA, assessment, CAPTCHA no resoluble, pregunta sin respuesta, salario bajo el piso, híbrido/presencial en zona "ask", crear cuenta, términos inusuales, documentos no disponibles, IDs oficiales. Formato en `user/inbox/tareas_humanas.md`: fecha, empresa, rol, URL, qué se necesita, fecha límite. La vacante pasa a `needs_user` y el resto continúa.

## Revisión de un paquete (`user/applications/<carpeta>/`)
Compara `job.md`, `cv.md`, `cover.md`, `answers.json` con `profile.yaml`/`answers.yaml` y escribe **solo** `review.json`:
```json
{"verdict": "approve | changes | reject", "fit_score": 0,
 "unsupported_claims": [{"text": "...", "file": "cv.md", "why": "no aparece en profile.yaml"}],
 "missing_keywords": [], "language_issues": [], "comments": ["cambio concreto"], "reject_reason": null}
```
Cualquier afirmación no respaldada obliga a `changes` o `reject`. Idioma distinto de `cv_language` → `changes` con "IDIOMA INCORRECTO". No reescribas los documentos.

## Envío y navegador
- Un canal a la vez, con pausas humanas (`uv run gmaj pace`) y el tope diario (`uv run gmaj cap <canal>`).
- En modo `dual`, Claude y Codex comparten el mismo Chrome: **nunca a la vez**. Se turnan con `user/state/browser.lock` (crear al empezar con motor y hora; borrar al terminar; si tiene más de 3 h, se considera abandonado).
- Cada agente abre pestañas nuevas, cierra las de cada vacante al terminarla y no deja ninguna suya abierta. Mañas por sitio: `docs/browser-quirks.md`.
- Si `catalogs/channels.yaml` marca un canal como `unsupported` para tu motor, esa vacante va a `tareas_humanas.md`.

## Ahorro de tokens
Lee solo los fragmentos que necesitas; usa `uv run gmaj` para todo lo mecánico; delega lotes (scoring, adaptación, revisión) a `uv run gmaj score run | tailor | review`, que usan el modelo barato configurado para cada rol.

## Cuando implementas código
Python ≥ 3.11 con uv (`uv sync`, `uv run pytest`). Código en `gmaj/`, configuración leída de `user/`. Tests con la persona ficticia de `tests/fixtures/user/`; ningún dato real en el repo (`uv run gmaj scrub`). Las skills se editan en `.agents/skills/` y se espejan con `uv run gmaj sync-skills`.
