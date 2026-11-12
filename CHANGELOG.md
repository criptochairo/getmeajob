# Changelog

## Sin publicar
- **Auditoría 2026-11-11, rondas 1, 2 y 3:** saneador del HTML del CV y CSP que impide cargar recursos externos; dependencia `certifi` actualizada. Las instrucciones de GMAJ-08/09/10 ya exigen confirmar el envío en el portal y conservar las pestañas con tareas pendientes del usuario.
- **Actualización con reintentos:** si falla la sincronización, se reintenta en la siguiente ejecución. Tras tres fallos se frena solo el `uv sync` automático y se siguen buscando actualizaciones del motor. Después de completar `uv sync` a mano, usa `uv run gmaj update --sync-complete` para confirmar y limpiar los reintentos.
- **Aprobación ligada al paquete:** check y revisión independiente guardan una huella de documentos y PDF. `gmaj before-send <carpeta>` la verifica justo antes de enviar. Las postulaciones aprobadas antes de esta versión vuelven a pasar por check y revisión automáticamente y luego a tu lista por aprobar. Una pausa para el usuario conserva la huella. Registrar un envío ya confirmado siempre se acepta, para evitar postulaciones duplicadas.
- **Retomar y localizar archivos:** `gmaj resume` muestra qué falta (`send`, `approval`, `check_review` o `tailor`); `gmaj paths` muestra las rutas del usuario activo. Los prompts y las tareas programadas respetan `GMAJ_USER_DIR`, incluso con espacios. Las tareas ya instaladas deben reinstalarse con `gmaj schedule install` (conserva su horario y tipo).
- **Fuentes de navegador:** `gmaj sources --browser` muestra fuentes activas y desactivadas con avisos. Se acepta el formato antiguo `fuente: true`. Para OCC/Indeed, `browser: true` sin `enabled` activa la fuente; un `enabled: false` explícito la desactiva. Plantilla y catálogo nuevos traen `enabled: true`. Si ya usabas OCC/Indeed por navegador, revisa `search.yaml`: cambia a `enabled: true` si heredaste el `false` de la plantilla anterior. `validate` y `doctor` avisan; no se cambia tu configuración automáticamente.
- **Salarios en colectores:** OCC/Indeed ya no descartan por un piso general; el prefiltro aplica después el piso correcto de cada familia de rol.
- **Actualización automática:** cada sesión de Claude Code empieza con `gmaj update --auto` (hook de inicio); Codex lo corre como primera instrucción de `AGENTS.md`, y `discover`/`run-daily` se actualizan antes de empezar. Solo `--ff-only`; sin red o con cambios locales en el motor, sigue sin romper nada. Corre `uv sync` si cambian las dependencias.
- **Prefiltro por requisitos duros** sin gastar IA (`exclusions.hard_requirements`): software que el anuncio exige y no manejas, licencias o títulos que no tienes, puestos muy por debajo de tu nivel. Los años de experiencia **no** descartan: los pondera el scoring.
- **Scoring:** campo `hard_req_mismatch`; el motor topa esas vacantes en 40.
- **Bolsas ATS con 404** (`invalid_boards.txt`) se saltan en las siguientes corridas.
- **Freno adaptativo ante 429** (`adaptive_step_seconds`, activo en LinkedIn): cada bloqueo duplica la espera extra y cada éxito la reduce.
- **No reaplicar** a una empresa con postulación ya enviada, aunque la vacante reaparezca en otra fuente o con otro título.
- **La corrida diaria abre Chrome** si está cerrado (`chrome_profile` en `engines.yaml`), para que la extensión conecte.
- **Indeed a ritmo humano:** orden aleatorio, pausas con jitter, descansos, backoff con `Retry-After`, corte tras 2 bloqueos (`blocked: true`) y avance en `window.__indeed_progress`. Los enlaces usan el dominio de Indeed del usuario (antes siempre `mx.`).
- **Verificaciones anti-bot/CAPTCHA:** nunca se saltan ni se intentan resolver; la pestaña se queda abierta para el usuario.
- **Pestañas que esperan al usuario se quedan abiertas:** iniciar sesión, crear cuenta, grabar video/audio, assessment o verificación. Solo se cierran las de postulaciones enviadas o descartadas, o cuando el usuario lo pide.
- **Triage de correo:** no escala recordatorios de vacantes ya descartadas ni duplica pendientes.
- **Remotos listados en otro país** ("Remote (US)", LinkedIn "Remote" en Bogotá) ya no se descartan por ubicación ni se penalizan en el scoring: suelen aceptar contratistas internacionales. Solo cae la vacante si exige explícitamente residencia o autorización allá. Se desactiva con `eligibility.remote_abroad_ok: false`.
- **Familias de rol con piso y meta propios** (`salary.role_families`, opcional): los títulos que coinciden con una familia usan su piso en lugar de `floor_month` (el descarte nombra la familia; las prácticas conservan su piso). `job.md` trae `salary_family` y los prompts de adaptación/envío responden la meta de la familia. Regla genérica nueva: si el anuncio publica un rango cuyo tope supera la expectativa, se responde el punto medio del rango, nunca por debajo del piso.

## 1.0.0 — 2026-10
- Primera versión pública, extraída de una instancia personal en uso diario.
- Motor `gmaj` (Python + uv): descubrimiento sin IA (LinkedIn, Computrabajo, Himalayas, Remotive, RemoteOK, WWR, Working Nomads, Greenhouse, Lever, Ashby, Alignerr) y colectores en navegador (OCC, Indeed).
- Funciona con un solo motor (Claude o Codex) o en modo dual con failover.
- Entrevista de perfil, sugerencia de roles con conteos reales, CVs por familia e idioma, revisión cruzada.
- Modo supervisado → piloto automático.
- Windows y macOS (Programador de tareas / LaunchAgent).
