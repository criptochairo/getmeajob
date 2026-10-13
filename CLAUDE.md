@AGENTS.md

## Solo para Claude
- Navegador: extensión Claude in Chrome (herramientas `mcp__claude-in-chrome__*`). Antes de usarla, carga todas las que vas a necesitar en una sola búsqueda de herramientas y revisa las pestañas abiertas; trabaja en pestañas nuevas.
- Dentro de una sesión interactiva puedes usar subagentes en vez de `uv run gmaj score run | tailor | review`, con los modelos de `user/engines.yaml` (`score` → haiku, `tailor` → sonnet, `tailor_high` y `review` → opus). El subagente que revisa nunca es el que adaptó.
- En corridas desatendidas no hagas preguntas: escribe en `user/inbox/`.
