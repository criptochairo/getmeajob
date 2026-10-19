# Envío de aplicaciones en el navegador

Lee `AGENTS.md` (secciones "Envío" y "Navegador"), `docs/browser-quirks.md`, `user/answers.yaml` y, en cada carpeta, `job.md`, `answers.json`, `review.json` y `cover.md`. Estas carpetas ya están aprobadas (por el usuario en modo supervisado, o por la revisión cruzada en piloto automático).

Carpetas (dentro de `user/`):
{{FOLDERS}}

Para cada carpeta, con las sesiones de Chrome del usuario:
0. **Verifica que esté aprobada:** su vacante debe aparecer en `uv run gmaj list --status approved --json` (campo `app_dir`). Si no aparece (p. ej. sigue `reviewed`, que en modo supervisado significa que el usuario todavía no la aprueba), **no la envíes** y anótalo en la tabla final.
1. Antes de empezar: `uv run gmaj cap <canal>`; si `remaining` es 0, deja la vacante para mañana.
2. Abre la URL de `job.md` en una pestaña nueva y sigue el botón de aplicar.
3. Llena solo con `answers.json`, `answers.yaml` y `profile.yaml` (contacto: `personal.email`, `personal.phone`). Adjunta el PDF de la carpeta (idioma `cv_language`); verifica que quedó seleccionado ese archivo y no uno viejo. Carta: `cover.md`. Demográficas: `eeo_voluntary`. Desmarca "seguir a la empresa".
4. **No envíes y escala** si: hay que crear cuenta/contraseña o verificar un código; piden video, audio, entrevista con IA o assessment; hay una pregunta sin respuesta en los archivos; aparece una verificación anti-bot o CAPTCHA (Cloudflare "verifica que eres humano", reCAPTCHA, hCaptcha, Indeed...) (nunca la saltes ni intentes resolverla); los términos van más allá de un aviso de privacidad; piden números de identificación oficial. Escalar = entrada en `user/inbox/tareas_humanas.md` (fecha, empresa, rol, URL, qué se necesita, fecha límite) + `uv run gmaj log-applied <carpeta> needs_user <canal> "<motivo>" --agent <tu motor>`.
5. Antes de pulsar enviar, verifica campo por campo (idioma del CV, teléfono, correo, salario).
6. Al enviar: `uv run gmaj log-applied <carpeta> applied <canal> "<nota>" --agent <tu motor>` y `uv run gmaj pace` antes de la siguiente.
7. Cierra las pestañas de esa vacante solo si quedó enviada o descartada (o si el usuario lo pide), antes de pasar a la siguiente. Si quedó esperando una acción del usuario (iniciar sesión, crear cuenta, grabar video/audio, assessment, verificación anti-bot/CAPTCHA), deja esa pestaña abierta donde te quedaste. Al final no queda abierta ninguna otra pestaña tuya.

Al final imprime una tabla: carpeta | status | motivo si no se envió.
