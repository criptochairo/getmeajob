---
name: gmaj-update-profile
description: Cambios puntuales al perfil de GetMeAJob - nuevo empleo, certificación, cambio de salario, de modalidad, de zona, de familias de rol o de canales - y regeneración de lo que dependa de ellos. Úsala cuando el usuario diga "agrega...", "ya no quiero...", "cambié de trabajo", "sube mi piso", etc.
---

# Actualizar el perfil

1. Aclara el cambio con preguntas cortas; aplica las mismas reglas de la entrevista (`gmaj-onboarding`): hechos confirmados, cifras respaldables, `confirmed: <hoy>`.
2. Edita `user/profile.yaml` / `user/answers.yaml` / `user/search.yaml` según corresponda. Si `user/` es un repo git local, haz commit con un mensaje claro (permite deshacer).
3. Regenera lo que dependa:
   - Hechos de experiencia, educación, certificaciones o habilidades → actualiza las variantes afectadas y `generated/candidate_brief.md`, vuelve a renderizar los PDFs y pide la revisión cruzada (como en `gmaj-build-profile` paso 4) y la aprobación del usuario.
   - Familias de rol → corre **gmaj-suggest-roles** / **gmaj-build-profile**.
   - Salario, modalidad, zonas, exclusiones, canales → solo `search.yaml` (y `answers.yaml`); `uv run gmaj prefilter` aplica a lo nuevo.
4. `uv run gmaj validate` y resume qué cambió.
