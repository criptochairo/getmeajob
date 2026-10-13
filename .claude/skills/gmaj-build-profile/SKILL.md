---
name: gmaj-build-profile
description: Genera la configuración de búsqueda (user/search.yaml), los CV maestros y variantes por familia de rol e idioma, las cartas plantilla y el resumen para scoring, a partir del perfil confirmado y las familias elegidas; luego los revisa contra sobreafirmaciones y pide aprobación. Úsala al terminar gmaj-suggest-roles o cuando cambien las familias de rol o el perfil.
---

# Construir el perfil operativo

Entrada: `user/profile.yaml`, `user/answers.yaml` (confirmados) y `preferences.chosen_role_families`. **No inventes nada**: solo seleccionar, reordenar, traducir y reformular.

## 1. `user/search.yaml`
Parte de `templates/user/search.yaml` (ya copiado por `gmaj init`) y de `catalogs/countries/<país>.yaml`:
- `market`, `currency` (base + tipos de cambio aproximados), fuentes del país (`sources`) y `apply_sources` según los canales donde el usuario tiene cuenta.
- `salary.floor_month` / `target_month` / `office_min_month` desde `answers.salary_expectation.floor_month` / `target_month` / `office_min_month`.
- `work_mode`: `remote: accept`; `hybrid`/`onsite`: `reject`, `accept` o `zones` con las zonas que dio el usuario.
- `eligibility`: frases de rechazo según su autorización de trabajo (p. ej. si puede trabajar en EE.UU., quita las de EE.UU.); `location_ok` con su país/región.
- `queries.es` / `queries.en`: los títulos de las familias elegidas (máx. ~25 en total).
- `relevance_keywords`: palabras **completas** de esos títulos y del área (10–30; el plural se reconoce solo: "analista" cubre "analistas"), sin palabras genéricas como "manager" sueltas.
- `exclusions`: empresas excluidas (`preferences.excluded_companies`) y `off_target_title_keywords` (áreas que nunca quiere).
- `scoring.role_fit.tiers`: 40 para las familias `seguro`, 30 `adyacente`, 20 `stretch`, con descripciones concretas; `skills_match.note` con sus habilidades clave; `seniority.note` con su nivel.
- `sources.greenhouse/lever/ashby`: slugs de `catalogs/ats_boards.yaml` de sus industrias (opcional).
- `limits.start_date` = hoy; `operation.autonomy: supervised`.

## 2. CV maestros y variantes (`user/variants/`)
- Un CV por **familia × idioma** que use (español del mercado y, si su inglés es B2+, inglés): `cv_<familia>_<idioma>.md`, y su carta `cover_<familia>_<idioma>.md`. Regístralos en `search.yaml variants`.
- Formato (compatible con `gmaj render`): `# Nombre`, línea en negritas con el titular, línea de contacto (`ciudad · correo · teléfono · LinkedIn`), `## Perfil`/`## Summary`, `## Experiencia`/`## Experience` con `**Puesto** - Empresa · Modalidad · fechas` y viñetas `- `, luego Educación, Certificaciones, Idiomas, Habilidades. Una columna, ≤ 2 páginas.
- Omite `cv_policy.omit_employers`. Cifras solo las de `achievements` confirmados.
- Cartas: ≤ 250 palabras, con marcadores `{{company}}`, `{{role}}`, `{{why_company}}`, `{{job_keywords}}`; sin datos personales sensibles.
- Renderiza cada CV: `uv run gmaj render user/variants/<archivo>.md`.

## 3. `user/generated/candidate_brief.md`
≤ 250 palabras para el scoring: quién es (años, áreas, nivel), familias objetivo con etiqueta, dónde puede trabajar (y dónde no), idiomas con nivel, licencias/títulos que tiene y que NO tiene, piso y meta (en moneda base y USD/mes y USD/h), modalidad aceptada, y la matriz de años por área.

## 4. Revisión cruzada (contexto limpio)
Pide la revisión a otra instancia: escribe la lista de archivos en un prompt y córrelo con `uv run gmaj run-role review --prompt-file <archivo>` (o un subagente distinto si eres Claude): "Compara cada variante y carta con user/profile.yaml; lista afirmaciones no respaldadas (cifras, años, 'diario', 'experto', resultados de equipo atribuidos a la persona) en user/generated/variants_review.json". Corrige lo que señale.

## 5. Aprobación del usuario
Muestra la lista de PDFs (rutas) y pídele que los abra y revise. Aplica sus correcciones (actualizando primero `profile.yaml` si es un hecho). Pide confirmación expresa: "¿Apruebas estos CVs para usarlos en tus postulaciones?". Registra `profile.cv_policy.approved: <fecha>`.

## 6. Alertas de LinkedIn por correo (segunda fuente, sin peticiones)
Explica: LinkedIn limita cuántas búsquedas automáticas acepta; si un día bloquea, las alertas por correo siguen trayendo sus vacantes sin hacerle ninguna petición. Requiere que el agente pueda leer su Gmail (conector de Claude o plugin de Codex); si no lo tiene, ofrece conectarlo o sáltate este paso.
1. Pide permiso para crear las alertas en su cuenta (o que él haga clic, si lo prefiere).
2. Por cada familia elegida, en una pestaña nueva con su sesión: `https://www.linkedin.com/jobs/search/?keywords=<2-3 títulos de la familia unidos con OR>&location=<market.linkedin_location>&f_TPR=r86400` (+ `&f_WT=2` si solo quiere remoto). Activa **"Crear alerta" / "Set alert"** con frecuencia **diaria** y aviso **por correo**. Máximo ~5 alertas en total.
3. Verifica en "Preferencias de alertas de empleo" que quedaron, cierra las pestañas y anota en `search.yaml operation.linkedin_alerts` la lista `[{family, keywords, created}]`.
4. Las alertas entran solas: `gmaj mail` las extrae a `user/data/mail_leads.json` y la corrida diaria las inserta con `gmaj add-jobs`.

## 7. Cierre
`uv run gmaj validate` debe pasar. Opcional: ofrece sugerencias para alinear su perfil de LinkedIn/Indeed/OCC con el CV (titular, extracto, experiencia) — OCC no deja postular con el perfil incompleto. Luego vuelve a `INSTALL.md` paso 5 (programar la corrida diaria).
