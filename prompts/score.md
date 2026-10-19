# Scoring de un lote de vacantes

Califica de 0 a 100 cada vacante de `{{BATCH}}` para el candidato descrito en `user/generated/candidate_brief.md`, con la rúbrica `scoring` de `user/search.yaml`. Escribe **solo** `{{OUT}}`: un arreglo JSON `[{"id": "...", "score": 0, "reason": "≤ 20 palabras", "hard_req_mismatch": false}]` con **todas** las vacantes del lote, en el mismo orden. No escribas ningún otro archivo ni leas nada más.

## Rúbrica (suma, máximo 100)
- **Rol (0–40):** según `scoring.role_fit.tiers`. Un título que no corresponde a ninguna familia de rol del candidato vale 0–5.
- **Modalidad (0–20):** según `scoring.work_mode` (remoto, híbrido, presencial, desconocido).
- **Salario (0–20):** ≥ meta 20 · entre piso y meta 10 · no publicado 8 · bajo el piso 0. Convierte con `currency.rates`. Prácticas/becas (perfil de entrada): compara con `salary.internship_floor_month` en lugar del piso normal; si es null, 10.
- **Skills (0–15):** coincidencia con las habilidades del brief.
- **Seniority (0–5):** 5 si encaja con el nivel del candidato; 0 si exige ser director/VP o muchos más años.

## Penalizaciones (restar y decirlo en `reason`)
- −40 si el puesto está atado a un país o ciudad donde el candidato no puede trabajar (salvo worldwide/anywhere/su región). Un puesto **remoto** listado en otro país ("Remote (US)", "Remote – Canada") no se penaliza por ubicación si el brief dice que acepta trabajar como contratista internacional: solo cuenta si el texto exige explícitamente residencia o autorización allá.
- −40 si exige una licencia, colegiatura o título que el brief dice que no tiene.
- −30 si exige residencia o autorización de trabajo que el candidato no tiene (ver brief).
- −20 si exige un idioma que el candidato no habla al nivel pedido.
- −15 por cada requisito explícito de años que no cumple (compara con la matriz de años del brief).
- −20 si es híbrido/presencial fuera de las zonas aceptadas.
- Resultado mínimo 0.

## Tope por requisito duro
Si el anuncio **exige** algo que el brief dice que el candidato no tiene (licencia, colegiatura o título; software o certificación indispensable; nivel director/VP/head/socio), pon `"hard_req_mismatch": true`, empieza `reason` con `hard_req: <qué>` y el score no pasa de 40 (el motor lo topa de todos modos). Pedir más años de experiencia **no** activa el tope: eso ya lo pondera la penalización por años.

## Perfil de entrada (el brief dice etapa `student`, `new_grad` o `first_job`)
- **Rol:** juzga el encaje por carrera, materias, proyectos, prácticas y habilidades del brief, no por empleos previos.
- **Seniority:** 5 si el anuncio dice "sin experiencia", "recién egresado", "0–1 años", trainee, becario, practicante o junior; 2 si no menciona nivel; 0 si es senior/lead/gerente.
- **Años:** −5 si pide 1–2 años; −15 por cada requisito de 3 años o más (en vez del −15 general).
- Si pide un título terminado y el brief dice que está en curso o sin titular: −20 (no −40), salvo que acepte estudiantes o pasantes.
- Prácticas o trainee que exigen estar inscrito: solo puntúan si el brief dice que sigue estudiando.

Sé consistente y estricto: de cada lote normalmente menos del 15% queda por encima de 50. `reason` incluye el desglose, p. ej. `rol 40, remoto 20, sal 8, skills 12, sen 5, −40 ubicación Corea → 45`. Antes de escribir, cuenta cuántas quedaron ≥ 60; si son más del 35%, revisa de nuevo las penalizaciones.
