---
name: gmaj-status
description: Resumen del estado de la búsqueda de empleo en GetMeAJob - cuántas vacantes se encontraron, calificaron, enviaron, escalaron; últimas corridas, errores y consumo. Úsala cuando el usuario pregunte "¿cómo va?", "estado", "qué se hizo hoy/esta semana".
---

# Estado

1. `uv run gmaj stats`, último `user/reports/*.md`, `user/data/discover_done.json`, `uv run gmaj autonomy`, y `uv run gmaj doctor` solo si algo parece roto.
2. Responde en ≤ 10 líneas: enviadas (hoy / semana / total), por aprobar, tareas pendientes, respuestas de empresas (entrevistas, rechazos), fuentes con errores, si la tarea diaria corrió hoy, y el siguiente paso recomendado (p. ej. "tienes 4 por aprobar: ¿las vemos?").
3. Si el rendimiento es bajo (muchas descartadas o 0 envíos varios días), explica la causa principal (filtros de modalidad/ubicación, pocas consultas, piso alto) y sugiere un ajuste con **gmaj-update-profile**.
