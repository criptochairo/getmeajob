---
name: gmaj-onboarding
description: Entrevista de GetMeAJob para armar el perfil del candidato (datos básicos, experiencia o primer empleo, educación, certificaciones, habilidades, preferencias y respuestas típicas de formularios). Úsala al instalar GetMeAJob, cuando user/profile.yaml esté vacío o incompleto, o cuando el usuario diga "armemos mi perfil" / "sigamos con la entrevista". No la uses para cambios puntuales (eso es gmaj-update-profile).
---

# Entrevista de perfil

Objetivo: llenar `user/profile.yaml` y `user/answers.yaml` con hechos **confirmados por el usuario**, para que nunca haya que inventar nada en un CV o formulario.

## Reglas de conversación
- Habla en el idioma del usuario. Tono cálido y concreto. **Una pregunta a la vez** (o un grupo corto de datos simples: "nombre, correo y teléfono"). Excepción: en el **modo rápido** (sección 1) se confirma un resumen completo de un solo jalón.
- Al empezar, pregunta en qué idioma quiere la entrevista.
- Nunca supongas: si algo no está claro, pregunta. Si el usuario no sabe o no quiere responder, guarda `TODO` (o `prefer_not_to_say` en lo demográfico) y sigue.
- **Guarda cada respuesta en el YAML en cuanto la recibas** (edita el archivo, no acumules en memoria) y añade `confirmed: <fecha de hoy>` a los hechos. Actualiza `user/onboarding/state.json` con `{"block": N, "updated": "..."}` para poder retomar.
- Si `state.json` existe, saluda, resume en 2 líneas lo que ya hay y continúa desde el bloque pendiente.
- Cifras y logros: pregunta siempre "¿Podrías respaldar esa cifra si te preguntan en una entrevista?" (en modo rápido, una sola pregunta con la lista de cifras). Solo se guarda lo que diga que sí, con su `evidence`.
- No pidas números de CURP/RFC/NSS/pasaporte: solo si los tiene (sí/no). Esos números jamás se guardan ni se escriben.
- Cada 3–4 bloques, muestra un resumen corto de lo guardado y pregunta si algo está mal.

## 0. Aviso de privacidad (antes de la primera pregunta)
Explica en 4 líneas: todo se guarda solo en su computadora (`user/`), nada se sube a GitHub; los datos sensibles (edad, género, pronombres, etnia, discapacidad) son opcionales y "prefiero no decir" siempre es válido; la herramienta solo usará lo que confirme; puede pedir ver o borrar cualquier dato. Pide su OK para empezar.

## 0.5 Edad y etapa (antes del bloque 1)
- Pregunta si tiene 18 años o más. **GetMeAJob es solo para mayores de 18.** Si no, explícalo con amabilidad (los menores necesitan permisos y condiciones especiales que la herramienta no puede verificar), sugiere la bolsa de trabajo de su escuela o el servicio de empleo de su país, y **detén la entrevista** sin guardar más datos.
- Pregunta su etapa → `profile.career_stage`: estudiante (`student`), recién egresado (`new_grad`), busca su primer empleo (`first_job`), cambio de carrera (`career_change`) o ya tiene experiencia (`experienced`). Con `student`, `new_grad` o `first_job`, el bloque 3 se reemplaza por el **3E** y el bloque 4 va antes que el 3E.

## 1. Atajo: importar lo que ya tiene y elegir el modo
Pregunta si tiene un CV (PDF o Word) o puede exportar su perfil de LinkedIn ("Más → Guardar en PDF"). Si sí: pídele la ruta o que lo deje en `user/documents/`, léelo y prellena un **borrador** de los bloques 3–8 (experiencia o primer empleo, educación, certificaciones, idiomas, habilidades, proyectos). Lo importado no cuenta como confirmado hasta que el usuario lo valide.

Luego pregúntale cómo quiere revisarlo (con CV o sin él):
- **Rápido (recomendado):** le muestras un resumen y lo confirma de un solo jalón.
- **Detallado:** revisan juntos cada empleo, con fechas y detalles (bloques 3–8 como están abajo).

### Modo rápido
1. **Sin CV:** pídele en un solo mensaje sus empleos (puesto, empresa, mes/año de inicio y fin, una línea de qué hacía), su educación y sus certificaciones, como le salga; tú lo ordenas. En perfiles de entrada, pide lo mismo para prácticas, servicio social, trabajos de medio tiempo, proyectos y voluntariado (ver 3E).
2. **Muestra un resumen compacto** de todo junto, sin YAML:
   - Experiencia: una línea por empleo, `Puesto · Empresa · ene 2020 – mar 2023 · qué hacía en ≤ 12 palabras`.
   - Educación, certificaciones e idiomas: una línea cada uno.
   - Habilidades y herramientas: una sola línea.
   - Cifras y logros detectados: lista corta, cada uno con "¿lo puedes respaldar?".
   - Lo que no se pudo leer o falta (p. ej. un mes de inicio) va **marcado con ❓**, nunca supuesto.
3. Pregunta **una vez**: "¿Está bien así? Dime solo lo que haya que corregir, qué cifras no puedes respaldar y si algún empleo no quieres que aparezca nunca." Con su respuesta, guarda todo con `confirmed: <hoy>`; las cifras que no respalde no se guardan, los ❓ sin respuesta quedan `TODO`, y los empleos que no quiera mencionar van a `cv_policy.omit_employers` (si hay alguno, pregunta también `if_form_requires_all_employers`).
4. Pregunta **una vez** si quiere añadir algo, con opciones para que solo elija: herramientas o programas, logros con cifras, habilidades, certificaciones o cursos, idiomas, proyectos, un empleo que falte. Si dice "no", sigue.
5. **Años por área:** propón tú la matriz calculada con las fechas confirmadas ("análisis de datos: 4 años, en X y Y") y que la confirme o corrija en una sola respuesta.
6. Lo que el resumen no cubre se pregunta agrupado y es opcional: motivo de salida (una frase general para todos sirve) y último sueldo bruto (y si lo revelaría). Si no quiere responder, `TODO`: los formularios que lo pidan se escalan.
7. Si en cualquier momento prefiere ir empleo por empleo, cambia al modo detallado desde donde van.
8. Sigue con los bloques 1–2 si faltan y luego con el 9 en adelante. Guarda `{"mode": "quick"}` en `user/onboarding/state.json`.

### Modo detallado
La entrevista **confirma y corrige** el borrador bloque por bloque en vez de preguntar desde cero ("Veo que trabajaste en X de 2020 a 2023 como Y, ¿correcto?"). Guarda `{"mode": "detailed"}` en `state.json`.

## 2. Bloques (en este orden; en modo rápido, los bloques 3–8 ya quedaron cubiertos por el resumen)
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
   **3E. Primer empleo (solo perfiles de entrada).** Explica que casi todo el mundo tiene experiencia aunque no sea un empleo formal, y que solo se usa lo que confirme. Recorre, una a una:
   - Prácticas profesionales (`engagement: practicum`) y servicio social (`social_service`) → `experience`, con lo que hizo y herramientas.
   - Trabajos de medio tiempo, de verano, en el negocio familiar o por su cuenta (`part_time`, `family_business`, `informal`) → `experience`. Cuentan aunque no sean del área: muestran responsabilidad y trato con clientes.
   - Proyectos escolares, personales, tesis aplicada, hackathons, concursos → `projects` (qué hizo **la persona**, no el equipo; resultados solo si los puede respaldar).
   - Voluntariado, sociedad de alumnos, equipos deportivos, clubes → `volunteering` o `education.activities`.
   - Si de verdad no hay nada de esto, no pasa nada: el CV se arma con educación y habilidades, y se lo dices sin juzgar.
4. **Educación** → `profile.education`: grado, carrera, institución, años, estado (titulado `completed` / egresado o pasante sin titular `coursework_completed` / en curso `in_progress` / trunco `incomplete`), cédula o licencia (sí/no), promedio, honores. Perfiles de entrada, además: fecha esperada de egreso, horario de clases si sigue estudiando, materias relacionadas con lo que busca, tesis, becas y actividades.
5. **Certificaciones, cursos y licencias** → `profile.certifications`: nombre, emisor, fecha, vencimiento, ID de credencial.
6. **Idiomas** → `profile.languages`: nivel (y CEFR si lo sabe), certificados (TOEFL, etc.).
7. **Habilidades y años por área** → `profile.skills`, `profile.years_by_domain`
   - Técnicas, herramientas, blandas, de dominio.
   - Matriz de años: para cada área relevante, ¿cuántos años y dónde? Explica que los formularios preguntan "¿cuántos años de experiencia en X?" y que se responderá exactamente esto (o "no / menos de N"). Perfiles de entrada: cuenta solo prácticas y empleos (no proyectos escolares); lo normal es 0 o "menos de 1 año", y está bien.
8. **Proyectos, voluntariado, publicaciones, premios** (opcional, rápido).
9. **Qué busca** → `profile.preferences`, `answers.salary_expectation`, `answers.availability`
   - Roles e industrias que le gustarían (en sus palabras) y cuáles evitar; nivel (entry/junior/mid/senior/lead).
   - Perfiles de entrada: ¿acepta prácticas, becas o programas de trainee? → `preferences.accepts_internships`. Si sí, ¿cuál es el apoyo económico mínimo que aceptaría? → `answers.salary_expectation.internship_floor_month` (puede ser null). Explica que en un primer empleo abrir híbrido o presencial en zonas cercanas multiplica las opciones: casi todo lo remoto pide experiencia.
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
