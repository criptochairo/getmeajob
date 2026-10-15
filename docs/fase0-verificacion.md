# Fase 0 — verificaciones manuales antes de publicar

Lo que no se puede probar con tests automáticos. Marca cada punto en una cuenta de Windows **limpia** (usuario nuevo o VM) y en una **Mac**, y actualiza `catalogs/channels.yaml` con los resultados.

## Instalación (por motor)
- [ ] Claude Desktop (Code): pegar el bloque del README → lista única de dependencias con una sola autorización → clona → `uv sync` → `gmaj doctor` sin ERR.
- [ ] App de Codex: lo mismo; anotar si `git clone` pidió aprobación de red.
- [ ] Sin git preinstalado (Windows): el agente ofrece `winget install Git.Git` y continúa.
- [ ] Claude lee `.claude/skills/` y Codex lee `.agents/skills/` (las skills aparecen / se activan por descripción).

## Tareas programadas
- [ ] Claude Desktop → Routines → Local: "Run now" + "always allow"; al día siguiente corrió sola y **pudo usar Claude in Chrome**.
- [ ] App de Codex → tarea programada: corrió sola y pudo usar la extensión de Chrome / el navegador.
- [ ] `gmaj schedule install` (Windows y macOS) corre `gmaj discover` y deja `user/data/discover_done.json`.
- [ ] Recuperación: con la PC dormida a la hora programada, corre al despertar.
- Si alguna tarea de app NO puede usar el navegador → documentar el modo CLI (`gmaj schedule install --kind daily`) como camino recomendado para ese motor.

## Matriz canal × motor (hasta antes de enviar, con cuenta de prueba)
| Canal | Claude in Chrome | Codex |
|---|---|---|
| LinkedIn Easy Apply (subida de PDF) | [ ] | [ ] |
| Indeed (colector + postulación) | [ ] | [ ] |
| OCC (colector + Postularme) | [ ] | [ ] |
| Computrabajo | [ ] | [ ] |
| Greenhouse / Lever / Ashby | [ ] | [ ] |
| Workday | [ ] | [ ] |
| Paradox / Olivia | [ ] | [ ] |

## E2E
- [ ] Solo Claude (sin Codex instalado): instalación → entrevista con "Ana Ejemplo" (CV PDF ficticio) → roles con conteos → PDFs ES/EN → `gmaj validate` OK → corrida diaria supervisada deja `por_aprobar.md`.
- [ ] Solo Codex (sin Claude instalado): lo mismo.
- [ ] Dual: lock de navegador, reparto de turnos, failover cuando un motor se queda sin cuota.
- [ ] Piloto real: un amigo hace 1 postulación supervisada de punta a punta.
- [ ] `uv run gmaj scrub` sin hallazgos (con tu denylist privada en `~/.gmaj-scrub-denylist.txt`) y revisión manual del diff antes del primer push.
