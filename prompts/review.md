# Revisión cruzada de paquetes (contexto limpio: tú NO adaptaste estos paquetes)

Lee UNA vez `AGENTS.md` (sección "Revisión de un paquete"), `user/profile.yaml` y `user/answers.yaml`.
Revisa cada carpeta (job.md, cv.md, cover.md, answers.json, check.json) y escribe **solo** `<carpeta>/review.json` con el esquema de AGENTS.md más `"recommendation": "apply" | "needs_user" | "skip"` y `"recommendation_reason"`. Máximo 6 comentarios por carpeta.

Si `profile.career_stage` es student, new_grad o first_job, revisa además: proyectos escolares, servicio social o voluntariado presentados como empleo o "experiencia laboral"; años de experiencia que no salen de `years_by_domain`/`experience`; títulos ("Licenciado", "Ingeniero", "titulado", "graduated") con educación en curso o sin titular; prácticas que exigen estar inscrito cuando ya egresó. Cualquiera obliga a `changes`.

Carpetas (dentro de `user/`):
{{FOLDERS}}

Al final imprime una línea por carpeta: carpeta | verdict | recommendation | motivo (≤ 12 palabras).
