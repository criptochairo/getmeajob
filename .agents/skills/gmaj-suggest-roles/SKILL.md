---
name: gmaj-suggest-roles
description: Sugiere familias de rol e industrias a buscar a partir del perfil del candidato, respaldadas con conteos reales de vacantes recientes, y registra las que el usuario elija. Úsala después de la entrevista (gmaj-onboarding) o cuando el usuario quiera replantear qué buscar.
---

# Sugerir roles

1. Lee `user/profile.yaml` (experiencia, educación, certificaciones, habilidades, años por área, `preferences`) y `catalogs/role_families.yaml` como inspiración (no es una lista cerrada).
2. Propón **4–8 familias de rol**. Para cada una:
   - nombre corto e `id` (minúsculas, sin espacios: `analista-datos`);
   - 3–6 títulos de búsqueda en español y en inglés;
   - nivel sugerido e industrias donde encaja;
   - **por qué** (qué hechos del perfil lo respaldan, en 1–2 frases);
   - etiqueta: `seguro` (lo ha hecho), `adyacente` (habilidades transferibles), `stretch` (aspiracional, pide algo que aún no tiene — dilo).
   Incluye siempre las que el usuario pidió en `preferences.roles_wanted`, aunque no sean las mejores; si alguna no tiene respaldo en el perfil, dilo con tacto.
3. **Respaldo con datos:** corre `uv run gmaj sample "<título 1>" "<título 2>" ...` con 1–2 títulos por familia (en el idioma del mercado y en inglés). Muestra los conteos de los últimos 7 días (LinkedIn de su país, Computrabajo, remotos de Himalayas). Aclara que son mínimos aproximados para comparar, no totales.
4. Presenta una tabla: familia | etiqueta | por qué | vacantes 7 días. Recomienda 2–4.
5. El usuario elige **2–5 familias** (puede editar títulos). Guarda en `profile.preferences.chosen_role_families`: `[{id, name, label, titles: {es: [], en: []}, industries: []}]` con `confirmed`.
6. Continúa con **gmaj-build-profile**.
