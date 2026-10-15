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
   **Perfil de entrada** (`career_stage` student / new_grad / first_job): parte de su carrera, materias, proyectos, prácticas y habilidades; prioriza las familias `entry_level: true` del catálogo (programas de trainee si `accepts_internships`) y las versiones "junior" de su área. `seguro` = encaja con su formación y lo que ya practicó; un rol que pide experiencia que no tiene es `stretch` aunque sea de su carrera.
   Incluye siempre las que el usuario pidió en `preferences.roles_wanted`, aunque no sean las mejores; si alguna no tiene respaldo en el perfil, dilo con tacto.
3. **Respaldo con datos:** en perfiles de entrada usa títulos con "junior", "trainee", "becario" o "sin experiencia" en el conteo. Corre `uv run gmaj sample "<título 1>" "<título 2>" ...` con 1–2 títulos por familia (en el idioma del mercado y en inglés). Muestra los conteos (LinkedIn de su país: últimos 7 días; Computrabajo y remotos de Himalayas: sin filtro de fecha — ver `notes`). Aclara que son mínimos aproximados para comparar, no totales. LinkedIn solo acepta 8 consultas por corrida; no repitas el conteo varias veces seguidas. Si LinkedIn aparece "en pausa" (bloqueó hace poco), compara con Computrabajo y Himalayas y no insistas.
4. Presenta una tabla: familia | etiqueta | por qué | vacantes (LinkedIn 7 días / Computrabajo / Himalayas). Recomienda 2–4.
5. **Una sola confirmación para grupos, CVs y alertas.** No preguntes por separado qué familias elige y si puedes armar los CVs: propón de una vez los grupos recomendados con letra y nombre, y lo que vas a preparar, en palabras sencillas y con números concretos. Ejemplo:
   > "Ahora voy a agrupar tu búsqueda de empleo en 4 grupos: **A** Análisis de datos, **B** Inteligencia de negocios, **C** Operaciones y **D** Soporte técnico. Para cada grupo voy a preparar un borrador de CV en español y otro en inglés (8 en total), que iremos adaptando a cada vacante que salga en ese grupo. También voy a crear 4 alertas de LinkedIn que te llegarán por correo. ¿Está bien, o quieres cambiar algún grupo?"
   - CVs = grupos × idiomas que va a usar (inglés solo si su nivel es B2+). Menciona las alertas solo si puede leerse su Gmail.
   - Si quiere cambiar algo (2–5 grupos; puede editar títulos), ajusta y vuelve a mostrar el mismo mensaje corto. Con el sí, guarda en `profile.preferences.chosen_role_families`: `[{id, name, label, titles: {es: [], en: []}, industries: []}]` con `confirmed`.
6. Continúa con **gmaj-build-profile** sin volver a preguntar: ese sí cubre la configuración, los CVs, las cartas y las alertas.
