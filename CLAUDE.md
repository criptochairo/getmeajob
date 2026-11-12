@AGENTS.md

## Solo para Claude
- Navegador: extensión Claude in Chrome (herramientas `mcp__claude-in-chrome__*`). Antes de usarla, carga todas las que vas a necesitar en una sola búsqueda de herramientas y revisa las pestañas abiertas; trabaja en pestañas nuevas.
- Dentro de una sesión interactiva puedes usar subagentes para scoring y adaptación en vez de `uv run gmaj score run | tailor`, con los modelos de `user/engines.yaml` (`score` → haiku, `tailor` → sonnet, `tailor_high` → opus).
- En corridas desatendidas no hagas preguntas: escribe en `user/inbox/`.

- Para revisar paquetes usa siempre `uv run gmaj review <carpeta...>`: crea la huella de revisión independiente necesaria para aprobar. No lo sustituyas por subagentes.
