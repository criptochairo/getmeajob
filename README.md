# GetMeAJob 1.0 by Criptochairo

Tu asistente de búsqueda de empleo. Encuentra vacantes cada mañana, adapta tu CV a cada una **sin inventar nada**, y postula por ti en LinkedIn, Indeed, OCC, Computrabajo y portales de empresas — con tu permiso. Funciona con **Claude Desktop** o con la **app de Codex** (no necesitas los dos).

## Instalar (5 minutos de tu parte)

1. Ten instalado **Claude Desktop** (con un plan que incluya Claude Code) **o** la **app de Codex** (ChatGPT), y **Google Chrome**.
2. Abre Claude Desktop (pestaña **Code**, elige tu carpeta Documentos) o la app de Codex, y pega esto:

```
Instala GetMeAJob desde https://github.com/criptochairo/getmeajob :
clónalo en mi carpeta Documentos/GetMeAJob, lee su INSTALL.md y síguelo
(muéstrame primero la lista de lo que hay que instalar y pídeme una sola autorización).
```

3. El agente te guiará: instalar lo necesario, la extensión de Chrome, iniciar sesión en tus portales (tú tecleas tus contraseñas) y una **entrevista** de ~30–45 min para armar tu perfil (puedes subir tu CV o tu PDF de LinkedIn para ir más rápido). Al final te sugiere qué roles buscar, con datos reales de vacantes, y genera tus CVs.

¿Recién egresado o buscas tu primer empleo? También funciona: la entrevista rescata tus prácticas, servicio social, proyectos escolares y voluntariado (sin hacerlos pasar por empleos), busca vacantes de nivel de entrada y prácticas, y descarta las que piden más años de los que tienes. Es para mayores de 18 años.

## Cómo funciona

| Cuándo | Qué pasa |
|---|---|
| Cada mañana (sin IA) | Busca vacantes nuevas en tu mercado y descarta las que no cumplen tus filtros (modalidad, ubicación, salario, idioma). |
| Una hora después | El agente califica las vacantes, verifica la modalidad real, adapta tu CV y carta al idioma de cada anuncio, y otra instancia revisa que no haya nada exagerado. |
| Primeras ~10 | **Modo supervisado:** nada se envía sin tu visto bueno. Abre el proyecto y di "pendientes". |
| Después | Si quieres, **piloto automático**: envía lo aprobado por la revisión y te deja solo lo que necesita a una persona (CAPTCHA, video, cuentas nuevas, preguntas abiertas). |

## Principios

- **Cero datos inventados.** Cada línea de tu CV sale de lo que confirmaste en la entrevista.
- **Tus datos se quedan en tu computadora**, en la carpeta `user/` (no se sube a GitHub). Ver [docs/privacidad.md](docs/privacidad.md).
- **Tú decides**: el agente te muestra la lista de lo que hay que instalar y te pide una sola autorización; también pide permiso para programar tareas y enviar.

## Riesgos que debes conocer

- Postular de forma automatizada puede ir contra los términos de algunos portales y, en casos extremos, provocar restricciones de cuenta. GetMeAJob usa ritmos humanos y topes diarios bajos, pero el riesgo no es cero.
- La IA puede equivocarse: revisa tus CVs al inicio y lo que se envía en modo supervisado.
- Tú eres responsable de lo que se envía en tu nombre.

## Para quien mantiene el proyecto

- `uv sync && uv run pytest` — tests con una persona ficticia.
- `uv run gmaj --help` — CLI. Reglas para agentes: [AGENTS.md](AGENTS.md). Skills: `.agents/skills/` (espejo en `.claude/skills/` con `uv run gmaj sync-skills`).
- Antes de publicar: `uv run gmaj scrub` (datos personales) — también corre en CI.
- Verificaciones manuales pendientes por plataforma y motor: [docs/fase0-verificacion.md](docs/fase0-verificacion.md).

Licencia MIT.
