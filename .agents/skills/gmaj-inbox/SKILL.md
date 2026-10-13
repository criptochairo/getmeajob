---
name: gmaj-inbox
description: Recorre con el usuario sus pendientes de GetMeAJob - postulaciones por aprobar (modo supervisado), tareas que solo él puede hacer (cuentas, CAPTCHA, video, assessments, preguntas abiertas) y correos de entrevistas. Úsala cuando el usuario diga "pendientes", "qué tengo que aprobar", "revisemos el inbox" o abra una sesión después de una corrida.
---

# Pendientes del usuario

1. Lee `user/inbox/por_aprobar.md`, `user/inbox/tareas_humanas.md` y `user/data/mail_triage.json` (entrevistas/solicitudes). Resume en 3–5 líneas: cuántas por aprobar, cuántas tareas, fechas límite próximas primero.
2. **Por aprobar** (de una en una o en lista numerada): empresa, rol, por qué encaja (score/razón), modalidad y salario, canal, y las respuestas clave que se darán; ofrece abrir el PDF (ruta). El usuario puede: aprobar ("apruebo 1, 3, 5"), pedir cambios, o descartar.
   - Aprobada sin cambios → envíala con **gmaj-apply** (con su permiso de enviar ahora) y `uv run gmaj autonomy record`.
   - Con cambios → corrige (si es un hecho nuevo, primero actualiza `profile.yaml`/`answers.yaml` con `confirmed`), re-renderiza, envía y `uv run gmaj autonomy record --corrected`.
   - Descartada → `uv run gmaj set-status <id> rejected --note "descartada por el usuario: <motivo>"`.
   - Quita de `por_aprobar.md` lo resuelto.
3. Si `uv run gmaj autonomy` muestra `offer_autopilot: true`: explica qué cambia (se enviará sin pedirle aprobación lo que pase la revisión; seguirá escalando lo dudoso) y pregunta si lo quiere activar. Solo con un "sí" expreso: `uv run gmaj autonomy set autopilot`.
4. **Tareas humanas**: para cada una, explica qué hay que hacer y abre la URL si lo pide (crear cuenta, resolver CAPTCHA, grabar video, presentar assessment). Si la respuesta a una pregunta nueva debe reutilizarse, guárdala en `answers.yaml` con `confirmed`. Marca la tarea como hecha (`- [x]`) y actualiza el estado de la vacante (`applied` / `rejected`).
5. **Correos**: entrevistas e información solicitada con su fecha límite; ofrece preparar notas de entrevista desde `job.md` y el CV enviado.
