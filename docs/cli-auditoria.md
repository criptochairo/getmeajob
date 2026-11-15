# Comandos para retomar postulaciones

Todos los comandos se ejecutan desde el motor con el prefijo `uv run gmaj`.
Los ejemplos son ficticios. Las rutas de `paths` son absolutas; `resume.dir`
es relativo al directorio del usuario activo.

| Comando y argumentos | Uso y salida |
| --- | --- |
| `before-send <carpeta>` | Verifica el paquete justo antes de pulsar enviar. JSON: `{"ok":true,"id":"job-1"}`. Acepta `approved` o `needs_user` con huella vigente. Error: código 2 y explicación en stderr. |
| `resume` | JSON: `[{"id":"job-1","dir":"applications/paquete","status":"approved","next":"send"}]`. `next` admite `send`, `approval`, `check_review`, `tailor`. No incluye `applied` ni `needs_user`. Las vacantes en `needs_user` se omiten intencionalmente porque esperan una acción del usuario; se consultan en `user/inbox/tareas_humanas.md`. |
| `paths` | Devuelve el objeto JSON completo de rutas del usuario activo (ejemplo debajo). |
| `sources` | Fuentes activas normalizadas como objetos. JSON: `{"remotive":{"enabled":true},"occ":{"browser":true}}`. Acepta la configuración escalar antigua `fuente: true`. |
| `sources --browser` | JSON: `{"active":{"occ":{"enabled":false,"browser":true}},"disabled_browser":{"indeed":{"browser":false}},"warnings":[]}`. `active`: portales con `browser: true` (el agente los recolecta; `enabled` no cuenta aquí). `disabled_browser`: los apagados por el usuario con `browser: false`. `warnings` se conserva vacío por compatibilidad. |
| `update --sync-complete` | Confirma que `uv sync` manual terminó bien, sincroniza las skills y limpia el contador. Salida de texto: `Sincronizacion manual confirmada.`; no devuelve JSON. |
| `set-status <id> approved --agent human` | Registra una aprobación real del usuario en modo supervisado, con check y revisión sellada vigentes. No devuelve stdout ni JSON. |
| `set-status <id> applied --agent human` | Registra que el usuario ya envió a mano, sin comprobar la huella. No devuelve stdout ni JSON. |
| `log-applied <carpeta> applied <canal> [nota] --agent human` | Alternativa para un envío manual confirmado; también escribe `submission.log`. Salida de texto, por ejemplo: `logged user/applications/paquete applied`; no devuelve JSON. |

Los tres últimos registros usan argumentos ya existentes con el comportamiento
corregido. `set-status` sigue aceptando `--note`, `--app-dir` y los agentes
`claude`, `codex`, `human`; `log-applied` sigue aceptando esos tres agentes
(por defecto `claude`). En modo supervisado aprobar exige `--agent human`.
La comprobación previa solo ocurre en `before-send`: registrar `applied`
representa un envío confirmado y no vuelve a comprobar la huella, con cualquier
agente. Véase [el alcance de la protección](approval.md).

Ejemplo completo de `paths` con `GMAJ_USER_DIR=C:/GMAJ/user`:

```json
{
  "profile.yaml": "C:/GMAJ/user/profile.yaml",
  "answers.yaml": "C:/GMAJ/user/answers.yaml",
  "search.yaml": "C:/GMAJ/user/search.yaml",
  "engines.yaml": "C:/GMAJ/user/engines.yaml",
  "generated/candidate_brief.md": "C:/GMAJ/user/generated/candidate_brief.md",
  "variants": "C:/GMAJ/user/variants",
  "applications": "C:/GMAJ/user/applications",
  "data": "C:/GMAJ/user/data",
  "inbox": "C:/GMAJ/user/inbox",
  "reports": "C:/GMAJ/user/reports",
  "state": "C:/GMAJ/user/state",
  "logs": "C:/GMAJ/user/logs",
  "user_dir": "C:/GMAJ/user"
}
```

En Windows el comando usa el separador nativo `\`, escapado como `\\` en JSON;
las barras `/` del ejemplo son equivalentes para ubicar archivos. Los prompts
usan `/` y comillas invertidas para conservar rutas con espacios. Las tareas
programadas capturan `GMAJ_USER_DIR`: reinstala las anteriores con
`uv run gmaj schedule install --kind discover --time 08:30`, o con el tipo y
horario que ya usabas. No se instala ninguna tarea como parte de la auditoría.
