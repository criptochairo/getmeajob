# Aprobación antes de enviar

`uv run gmaj check <carpeta>` verifica el paquete y guarda las huellas de sus
documentos y PDF. `uv run gmaj review <carpeta...>` inicia una revisión con
contexto limpio y sella su resultado en `.review-binding.json`. En modo
supervisado, tras la aprobación real del usuario se registra
`uv run gmaj set-status <id> approved --agent human`.

Justo antes de pulsar el botón de envío, ejecuta
`uv run gmaj before-send <carpeta>`. Un cambio posterior a la revisión invalida
la aprobación. Las postulaciones aprobadas antes de esta versión vuelven a pasar por check y revisión automáticamente y luego a tu lista por aprobar.

Una pausa en `needs_user` conserva la huella: resolver un CAPTCHA o iniciar
sesión permite continuar con `before-send` sin repetir todo si el paquete no
cambió. Esto no significa que la postulación se haya enviado.

Cuando el portal confirma el envío, se registra siempre como un hecho con
`uv run gmaj log-applied <carpeta> applied <canal>`; no se vuelve a verificar la
huella después del envío, para evitar perder el registro y postular dos veces.
Si el usuario confirma que envió a mano, se usa
`uv run gmaj log-applied <carpeta> applied <canal> --agent human` o
`uv run gmaj set-status <id> applied --agent human`. Ninguna de estas dos vías
exige huella vigente ni aprobación previa para registrar el hecho.

## Límite de la protección

La huella protege contra cambios accidentales o posteriores a la revisión.
No protege contra un agente que falsifique `.review-binding.json`, modifique
los archivos de control o añada `--agent human` por su cuenta. Ese argumento
registra quién aprobó o envió; no autentica a una persona. La separación de
revisión y las instrucciones al agente siguen siendo necesarias. No es una
firma digital ni una barrera contra un agente malicioso con acceso de escritura.
