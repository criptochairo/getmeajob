# Changelog

## Sin publicar
- **Actualización automática:** cada sesión de Claude Code empieza con `gmaj update --auto` (hook de inicio); Codex lo corre como primera instrucción de `AGENTS.md`, y `discover`/`run-daily` se actualizan antes de empezar. Solo `--ff-only`; sin red o con cambios locales en el motor, sigue sin romper nada. Corre `uv sync` si cambian las dependencias.
- **Prefiltro por requisitos duros** sin gastar IA (`exclusions.hard_requirements`): software que el anuncio exige y no manejas, licencias o títulos que no tienes, puestos muy por debajo de tu nivel. Los años de experiencia **no** descartan: los pondera el scoring.
- **Scoring:** campo `hard_req_mismatch`; el motor topa esas vacantes en 40.
- **Bolsas ATS con 404** (`invalid_boards.txt`) se saltan en las siguientes corridas.
- **Freno adaptativo ante 429** (`adaptive_step_seconds`, activo en LinkedIn): cada bloqueo duplica la espera extra y cada éxito la reduce.
- **No reaplicar** a una empresa con postulación ya enviada, aunque la vacante reaparezca en otra fuente o con otro título.
- **La corrida diaria abre Chrome** si está cerrado (`chrome_profile` en `engines.yaml`), para que la extensión conecte.
- **Indeed a ritmo humano:** orden aleatorio, pausas con jitter, descansos, backoff con `Retry-After`, corte tras 2 bloqueos (`blocked: true`) y avance en `window.__indeed_progress`. Los enlaces usan el dominio de Indeed del usuario (antes siempre `mx.`).
- **Verificaciones anti-bot/CAPTCHA:** nunca se saltan ni se intentan resolver; la pestaña se queda abierta para el usuario.
- **Triage de correo:** no escala recordatorios de vacantes ya descartadas ni duplica pendientes.

## 1.0.0 — 2026-10
- Primera versión pública, extraída de una instancia personal en uso diario.
- Motor `gmaj` (Python + uv): descubrimiento sin IA (LinkedIn, Computrabajo, Himalayas, Remotive, RemoteOK, WWR, Working Nomads, Greenhouse, Lever, Ashby, Alignerr) y colectores en navegador (OCC, Indeed).
- Funciona con un solo motor (Claude o Codex) o en modo dual con failover.
- Entrevista de perfil, sugerencia de roles con conteos reales, CVs por familia e idioma, revisión cruzada.
- Modo supervisado → piloto automático.
- Windows y macOS (Programador de tareas / LaunchAgent).
