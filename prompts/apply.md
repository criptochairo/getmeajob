# Envío de aplicaciones en el navegador

Lee `AGENTS.md` (secciones "Envío" y "Navegador"), `docs/browser-quirks.md`, `user/answers.yaml` y, en cada carpeta, `job.md`, `answers.json`, `review.json` y `cover.md`. Estas carpetas ya están aprobadas (por el usuario en modo supervisado, o por la revisión cruzada en piloto automático).

Carpetas (dentro de `user/`):
{{FOLDERS}}

Para cada carpeta, con las sesiones de Chrome del usuario:
0. Ejecuta `uv run gmaj before-send <carpeta>`; solo continua si termina bien. Si falla, repite check + review + aprobacion (supervisado: aprobacion del usuario con `--agent human`). No envies por aparecer solamente en la lista approved.
1. Antes de empezar: `uv run gmaj cap <canal>`; si `remaining` es 0, deja la vacante para mañana.
2. Abre la URL de `job.md` en una pestaña nueva y sigue el botón de aplicar.
3. Llena solo con `answers.json`, `answers.yaml` y `profile.yaml` (contacto: `personal.email`, `personal.phone`). Adjunta el PDF de la carpeta (idioma `cv_language`); verifica que quedó seleccionado ese archivo y no uno viejo. Carta: `cover.md`. Demográficas: `eeo_voluntary`. Desmarca "seguir a la empresa".
4. **No envíes y escala** si: hay que crear cuenta/contraseña o verificar un código; piden video, audio, entrevista con IA o assessment; hay una pregunta sin respuesta en los archivos; aparece una verificación anti-bot o CAPTCHA (Cloudflare "verifica que eres humano", reCAPTCHA, hCaptcha, Indeed...) (nunca la saltes ni intentes resolverla); los términos van más allá de un aviso de privacidad; piden números de identificación oficial. Escalar = entrada en `user/inbox/tareas_humanas.md` (fecha, empresa, rol, URL, qué se necesita, fecha límite) + `uv run gmaj log-applied <carpeta> needs_user <canal> "<motivo>" --agent <tu motor>`.
5. Inmediatamente antes de pulsar enviar, vuelve a ejecutar `uv run gmaj before-send <carpeta>` y exige exito; verifica campo por campo (idioma del CV, teléfono, correo, salario). Salario: la expectativa de `answers.json`; si `job.md` trae `salary_family`, la meta de esa familia; si el anuncio publica un rango cuyo tope la supera, el punto medio del rango (misma moneda y periodo); nunca por debajo del piso.
6. Solo con confirmación del portal de que la postulación fue enviada (resolver una tarea humana no basta): `uv run gmaj log-applied <carpeta> applied <canal> "<nota>" --agent <tu motor>` y `uv run gmaj pace` antes de la siguiente.
7. Cierra las pestañas de esa vacante solo si quedó enviada o descartada (o si el usuario lo pide), antes de pasar a la siguiente. Si quedó esperando una acción del usuario (iniciar sesión, crear cuenta, grabar video/audio, assessment, verificación anti-bot/CAPTCHA), deja esa pestaña abierta donde te quedaste y registra su URL en `user/inbox/tareas_humanas.md`. Al final cierra todas tus otras pestañas, exceptuando las que esperan tareas pendientes del usuario.

Al final imprime una tabla: carpeta | status | motivo si no se envió.
