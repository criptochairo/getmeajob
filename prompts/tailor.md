# Adaptación de paquetes de aplicación

{{EXTRA}}

Lee UNA vez: `AGENTS.md` (Integridad, Idioma del CV), `user/profile.yaml`, `user/answers.yaml` y la lista `variants` de `user/search.yaml`.

Para cada carpeta (dentro de `user/`):
{{FOLDERS}}

1. Lee `job.md`: rol, empresa, descripción, `score` y **`cv_language`** (obligatorio).
2. Elige la variante de `user/variants/` de la familia más cercana **en ese idioma**. Si no existe en ese idioma, traduce la más cercana sin agregar hechos.
3. Escribe `cv.md`:
   - score ≥ 75 (o si arriba dice adaptación COMPLETA): ajusta titular y resumen al rol, reordena viñetas por relevancia, incorpora palabras clave del anuncio **solo si profile.yaml las respalda**.
   - si no: adaptación ligera: copia la variante y cambia solo titular y 2–3 frases del resumen.
   - Contacto, fechas, empresas y cifras exactamente como en profile.yaml. Nada de `cv_policy.omit_employers` ni `forbidden_strings`. Ningún dato nuevo.
4. Escribe `cover.md` desde el `cover` de la misma familia e idioma: llena `{{company}}`, `{{role}}`, `{{job_keywords}}` y escribe `{{why_company}}` (1–2 frases concretas tomadas del anuncio, sin inventar datos de la empresa). ≤ 250 palabras.
5. Escribe `answers.json`: `{"variant": "...", "cv_language": "..", "screening": [{"question": "...", "answer": "...", "source": "answers.yaml:<campo> | profile.yaml:<campo>"}], "escalate": []}` con las respuestas que el anuncio anticipa (autorización, salario, preaviso, idiomas, años, modalidad). Para híbrido/presencial usa `salary_expectation.office_min_month`. Lo que requiera escalar (video, assessment, licencia, pregunta sin respuesta) va en `escalate`.
6. Genera el PDF: `uv run gmaj render <carpeta>/cv.md "<carpeta>/<cv_policy.pdf_name con {full_name}>"`.

No toques nada fuera de esas carpetas. Al final imprime una línea por carpeta: carpeta | variante | idioma | completo/ligero | escalamientos.
