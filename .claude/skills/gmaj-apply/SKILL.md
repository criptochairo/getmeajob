---
name: gmaj-apply
description: Envía postulaciones ya aprobadas en el navegador del usuario (LinkedIn Easy Apply, Indeed, OCC, Computrabajo, ATS como Workday/Greenhouse/Lever/Ashby y chats de reclutamiento), con pausas humanas, topes por canal y escalamiento. Úsala en la corrida diaria en piloto automático o cuando el usuario apruebe vacantes en gmaj-inbox.
---

# Enviar postulaciones aprobadas

Sigue `prompts/apply.md` al pie de la letra, en orden de score, con:
- **Desde gmaj-inbox:** exactamente las carpetas que el usuario acaba de aprobar, nada más.
- **Desde la corrida diaria en piloto automático:** las `approved` (`uv run gmaj list --status approved --json`).
- En modo supervisado nunca envíes una vacante que siga en `reviewed`: esa todavía no la aprobó el usuario.

- **Antes de empezar:** en modo dual crea `user/state/browser.lock` (`{"engine": "<tú>", "since": "<hora>"}`); si ya existe y tiene < 3 h, espera o termina. Bórralo al acabar.
- **Canales no soportados** por tu motor (`catalogs/channels.yaml`): no lo intentes; escala a `tareas_humanas.md`.
- **Mañas por sitio:** `docs/browser-quirks.md` (subida de archivos, texto que se pierde, chips de Paradox, Easy Apply con CV viejo preseleccionado, reCAPTCHA).
- **Si eres Claude:** usa Claude in Chrome. **Si eres Codex:** usa tu extensión de Chrome o el navegador; si una subida de archivo es rechazada por permisos, escala y anota en el reporte "activar 'Permitir acceso a URLs de archivo' en la extensión".
- Tras cada envío: `uv run gmaj log-applied ...`. (El conteo de aprobaciones del modo supervisado lo registra solo **gmaj-inbox**.)
- Si te quedas sin cuota a la mitad: registra lo enviado, deja el resto `approved` para mañana y anótalo en el reporte.
