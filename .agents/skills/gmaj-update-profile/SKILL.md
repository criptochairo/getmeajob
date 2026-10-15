---
name: gmaj-update-profile
description: Cambios puntuales al perfil de GetMeAJob - nuevo empleo, certificación, cambio de salario, de modalidad, de zona, de familias de rol o de canales - y regeneración de lo que dependa de ellos. Úsala cuando el usuario diga "agrega...", "ya no quiero...", "cambié de trabajo", "sube mi piso", etc.
---

# Actualizar el perfil

1. Aclara el cambio con preguntas cortas y, antes de tocar nada, anuncia en una frase lo que vas a cambiar y qué se actualiza con eso ("Voy a agregar tu certificación de Scrum y actualizar tus 4 CVs con ella; luego te los muestro. ¿Va?"). Con ese sí no vuelvas a preguntar hasta mostrar el resultado. Aplica las mismas reglas de la entrevista (`gmaj-onboarding`): hechos confirmados, cifras respaldables, `confirmed: <hoy>`.
2. Edita `user/profile.yaml` / `user/answers.yaml` / `user/search.yaml` según corresponda. Si `user/` es un repo git local, haz commit con un mensaje claro (permite deshacer).
3. Regenera lo que dependa:
   - Hechos de experiencia, educación, certificaciones o habilidades → actualiza las variantes afectadas y `generated/candidate_brief.md`, vuelve a renderizar los PDFs, pide la revisión cruzada (como en `gmaj-build-profile` paso 4) y muestra los CVs para su visto bueno (como en `gmaj-build-profile` paso 5).
   - Familias de rol → corre **gmaj-suggest-roles** / **gmaj-build-profile**.
   - Cambio de etapa (`career_stage`: se tituló, consiguió su primer empleo, terminó las prácticas) → actualiza `education.status` o `experience` y corre **gmaj-build-profile** completo: cambian `entry_level`, filtros, consultas, CV y brief. Al dejar de ser perfil de entrada, `entry_level.enabled: false` y vuelven las exclusiones de prácticas.
   - Salario, modalidad, zonas, exclusiones, canales → solo `search.yaml` (y `answers.yaml`); `uv run gmaj prefilter` aplica a lo nuevo.
4. `uv run gmaj validate` y resume qué cambió.
