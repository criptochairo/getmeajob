# Privacidad

- **Dónde viven tus datos:** solo en tu computadora, en `GetMeAJob/user/`. Esa carpeta está en `.gitignore`: nunca se sube al repositorio público. Si `git` está instalado, `user/` tiene su propio historial local (para deshacer cambios), sin ningún remoto.
- **Qué se guarda:** lo que confirmas en la entrevista (perfil, respuestas para formularios), tus CVs y cartas, las vacantes encontradas y el registro de postulaciones.
- **Datos sensibles:** edad, género, pronombres, etnia, discapacidad y similares se te piden porque muchos formularios los preguntan (encuestas de diversidad); en cada uno puedes elegir "prefiero no decir", y eso es lo que se responde en lo que no quieras dar.
- **Identificaciones oficiales** (CURP, RFC, NSS, pasaporte): solo se guarda si las tienes (sí/no); los números nunca se guardan ni se escriben en formularios sin preguntarte.
- **Contraseñas y códigos:** nunca. Tú inicias sesión en cada portal.
- **Qué ve la IA:** el agente (Claude o Codex) lee tus archivos para adaptar CVs y llenar formularios, bajo las políticas de privacidad de tu cuenta de Anthropic u OpenAI.
- **Correo:** si conectas Gmail, se usa en modo lectura para detectar entrevistas, rechazos y alertas de vacantes; no se responde, borra ni abre enlaces.
- **Borrar todo:** elimina la carpeta `user/` (y, si quieres, la carpeta GetMeAJob completa y las tareas programadas: `uv run gmaj schedule remove` y la rutina de la app).
- **Respaldo:** si quieres respaldar `user/`, usa un repo **privado** o una carpeta en la nube personal; nunca un repo público.
