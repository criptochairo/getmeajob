---
name: gmaj-review
description: Revisión cruzada de paquetes de aplicación (CV, carta, respuestas) contra el perfil, con contexto limpio, escribiendo review.json. Úsala cuando haya carpetas adaptadas sin review.json o el usuario pida "revisa estos paquetes". Quien adaptó un paquete no debe revisarlo.
---

# Revisión cruzada

- Forma preferida: `uv run gmaj review <carpetas>` — lanza una llamada nueva del rol `review` (otro modelo/motor según `user/engines.yaml`), así nunca revisa quien adaptó.
- Si estás dentro de esa llamada (o eres un subagente revisor): sigue `prompts/review.md` y el esquema de `AGENTS.md` → "Revisión de un paquete". Busca especialmente: cifras o años que no estén en `profile.yaml`, palabras que exageran ("experto", "diario", "lideré" cuando fue colaboración), empleadores omitidos, idioma distinto de `cv_language`, salario o autorización de trabajo que no coinciden con `answers.yaml`, placeholders sin llenar.
- No reescribas documentos: solo `review.json`.
