---
name: gmaj-onboarding
description: Entrevista de GetMeAJob para armar el perfil del candidato (datos básicos, experiencia, educación, certificaciones, habilidades, preferencias y respuestas típicas de formularios). Úsala al instalar GetMeAJob, cuando user/profile.yaml esté vacío o incompleto, o cuando el usuario diga "armemos mi perfil" / "sigamos con la entrevista". No la uses para cambios puntuales (eso es gmaj-update-profile).
---

# Entrevista de perfil

Objetivo: llenar `user/profile.yaml` y `user/answers.yaml` con hechos **confirmados por el usuario**, para que nunca haya que inventar nada en un CV o formulario.

## Reglas de conversación
- Habla en el idioma del usuario. Tono cálido y concreto. **Una pregunta a la vez** (o un grupo corto de datos simples: "nombre, correo y teléfono").
- Al empezar, pregunta en qué idioma quiere la entrevista.
- Nunca supongas: si algo no está claro, pregunta. Si el usuario no sabe o no quiere responder, guarda `TODO` (o `prefer_not_to_say` en lo demográfico) y sigue.
- **Guarda cada respuesta en el YAML en cuanto la recibas** (edita el archivo, no acumules en memoria) y añade `confirmed: <fecha de hoy>` a los hechos. Actualiza `user/onboarding/state.json` con `{"block": N, "updated": "..."}` para poder retomar.
- Si `state.json` existe, saluda, resume en 2 líneas lo que ya hay y continúa desde el bloque pendiente.
- Cifras y logros: pregunta siempre "¿Podrías respaldar esa cifra si te preguntan en una entrevista?". Solo se guarda lo que diga que sí, con su `evidence`.
- No pidas números de CURP/RFC/NSS/pasaporte: solo si los tiene (sí/no). Esos números jamás se guardan ni se escriben.
- Cada 3–4 bloques, muestra un resumen corto de lo guardado y pregunta si algo está mal.

## 0. Aviso de privacidad (antes de la primera pregunta)
Explica en 4 líneas: todo se guarda solo en su computadora (`user/`), nada se sube a GitHub; los datos sensibles (edad, género, pronombres, etnia, discapacidad) son opcionales y "prefiero no decir" siempre es válido; la herramienta solo usará lo que confirme; puede pedir ver o borrar cualquier dato. Pide su OK para empezar.

## 1. Atajo: importar lo que ya tiene
Pregunta si tiene un CV (PDF o Word) o puede exportar su perfil de LinkedIn ("Más → Guardar en PDF"). Si sí: pídele la ruta o que lo deje en `user/documents/`, léelo y prellena un **borrador** de los bloques 1–8. Desde ahí, la entrevista **confirma y corrige** en vez de preguntar desde cero ("Veo que trabajaste en X de 2020 a 2023 como Y, ¿correcto?"). Lo importado no cuenta como confirmado hasta que el usuario lo valide.

## 2. Bloques (en este orden)
1. **Identidad y contacto** → `profile.personal`, `answers.identity`
   - Nombre legal completo y cómo prefiere que le llamen; edad o fecha de nacimiento (opcional); género y pronombres (opcional); nacionalidad(es).
   - Ciudad, zona/colonia, estado, país; dirección completa para formularios (calle, colonia, CP) → `answers.address_for_forms`.
   - Correo y teléfono para reclutadores; ¿hay correos o teléfonos viejos que NO deban usarse? → `cv_policy.forbidden_strings`.
   - LinkedIn, portafolio, GitHub u otros enlaces.
2. **Autorización de trabajo y documentos** → `answers.work_authorization`, `engagement`, `country_specific`
   - Países donde puede trabajar sin patrocinio; ¿necesitaría visa/sponsorship para EE.UU. u otros?
   - ¿Acepta nómina, honorarios, contratista internacional, pago por hora?
   - (MX) ¿RFC activo? ¿e.firma vigente? (solo sí/no).
   - Documentos que tiene a la mano (título, cédula, constancias, kárdex, cartas de recomendación) → que los copie a `user/documents/`.
3. **Experiencia laboral, empleo por empleo** (del más reciente al más antiguo) → `profile.experience`
   - Puesto, empresa, fechas (mes/año), ciudad, modalidad, tipo de contrato, ¿vía agencia u outsourcing?
   - Qué hacía (3–6 responsabilidades) y logros con cifras respaldables.
   - Herramientas/tecnologías; motivo de salida (cómo quiere expresarlo en formularios).
   - Último sueldo bruto mensual (opcional; algunos formularios lo exigen) y si está dispuesto a revelarlo → `answers.salary_expectation.disclose_last_salary`.
   - ¿Hay algún empleo que **no** quiera mencionar nunca? → `cv_policy.omit_employers`; y si un formulario exige "todos los empleos", ¿escalar, incluirlo u omitirlo? → `cv_policy.if_form_requires_all_employers`.
4. **Educación** → `profile.education`: grado, carrera, institución, años, estado (titulado/trunco/en curso), cédula o licencia (sí/no), promedio, honores.
5. **Certificaciones, cursos y licencias** → `profile.certifications`: nombre, emisor, fecha, vencimiento, ID de credencial.
6. **Idiomas** → `profile.languages`: nivel (y CEFR si lo sabe), certificados (TOEFL, etc.).
7. **Habilidades y años por área** → `profile.skills`, `profile.years_by_domain`
   - Técnicas, herramientas, blandas, de dominio.
   - Matriz de años: para cada área relevante, ¿cuántos años y dónde? Explica que los formularios preguntan "¿cuántos años de experiencia en X?" y que se responderá exactamente esto (o "no / menos de N").
8. **Proyectos, voluntariado, publicaciones, premios** (opcional, rápido).
9. **Qué busca** → `profile.preferences`, `answers.salary_expectation`, `answers.availability`
   - Roles e industrias que le gustarían (en sus palabras) y cuáles evitar; nivel (junior/mid/senior/lead).
   - Modalidad: remoto / híbrido / presencial. Si acepta híbrido o presencial: zonas a las que sí iría, zonas a preguntar, zonas que nunca.
   - Salario → `answers.salary_expectation`: piso (`floor_month`), meta (`target_month`), qué responder (`monthly`, `yearly`, `hourly_usd`, `monthly_usd`, `range_rule`) y mínimo para trabajos con oficina (`office_min_month`).
   - Preaviso, fecha de inicio, horario y zona horaria, ¿puede cubrir horario de EE.UU.?, reubicación, viajes.
   - **Deal-breakers** (lo que nunca aceptaría) y empresas a excluir. ¿La búsqueda es confidencial? (si sí, excluir a su empleador actual).
10. **Preguntas típicas de formularios** → `answers.conflicts`, `consents`, `references`, `how_did_you_hear`
    - ¿Conoce gente en empresas a las que aplicaría? ¿Familiares en gobierno o es persona políticamente expuesta?
    - ¿Acepta mensajes SMS de reclutadores? ¿Que guarden su solicitud para otras vacantes? ¿Verificación de antecedentes?
    - Referencias (solo con permiso de cada una) o "disponibles a solicitud".
11. **Datos demográficos voluntarios** (EEO) → `answers.eeo_voluntary`: explica que son opcionales y que por defecto se responde "prefiero no decir".
12. **Cómo va a operar** → `search.yaml` (lo termina `gmaj-build-profile`) y `engines.yaml`
    - Si existe `user/onboarding/setup.json` (lo deja el paso 3 de `INSTALL.md`), **no vuelvas a preguntar** canales ni Gmail: muéstralos en una línea para confirmar ("Tienes sesión en LinkedIn y OCC, y Gmail conectado en lectura, ¿correcto?") y pregunta solo lo que falte. Si no existe, pregunta:
      - Canales donde **ya tiene cuenta** (LinkedIn, Indeed, OCC, Computrabajo...).
      - ¿Podemos leer su Gmail (solo lectura)? Sirve para detectar entrevistas y rechazos, y para recibir **alertas de LinkedIn por correo** (se crean en gmaj-build-profile), la fuente más estable de vacantes de LinkedIn.
    - En ambos casos, pregunta en cuáles canales sin cuenta estaría dispuesto a crearla por su cuenta.
    - Explica el **modo supervisado**: las primeras 10 postulaciones esperan su visto bueno; después se le ofrecerá el piloto automático.
    - Hora de la corrida diaria y si la computadora suele estar encendida a esa hora.
    - Plan de suscripción (Claude Pro/Max, ChatGPT Plus/Pro): con planes chicos se reducen `limits.tailor_per_day` (p. ej. 10) para no agotar la cuota.

## 3. Cierre
1. `uv run gmaj validate --only profile,answers` y resuelve lo que falte (search/variants se generan después).
2. Muestra un resumen final (5–10 líneas) y pide confirmación expresa: "¿Todo correcto?".
3. Sigue con **gmaj-suggest-roles** y luego **gmaj-build-profile**.
