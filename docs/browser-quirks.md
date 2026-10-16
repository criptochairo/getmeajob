# Mañas de los sitios bajo automatización del navegador

Aprendidas operando el sistema a diario. Aplican a Claude in Chrome y a la extensión de Codex (las herramientas cambian de nombre, la técnica es la misma).

## General
- La herramienta de JavaScript trunca la salida en ~800 caracteres: devuelve resultados por páginas (`window.__x_page(n)`) o escríbelos en el body y lee el texto de la página.
- Un POST desde la página a un servidor local (127.0.0.1) congela la pestaña con el permiso de "red local" de Chrome: nunca lo hagas.
- Las capturas de pantalla fallan a veces (sobre todo en LinkedIn); leer el texto de la página, buscar elementos y medir coordenadas con JS sigue funcionando.
- Una pestaña que roba el foco (p. ej. una entrevista de voz) hace fallar capturas en otras; un scroll en la pestaña objetivo la reactiva.
- Clics por referencia a veces no enfocan el campo: usa coordenadas. Textos largos pueden perder caracteres: verifica con JS y, en textareas, asigna con el setter nativo + evento `input`.

## Subir el CV (LinkedIn Easy Apply, Indeed, Paradox, ATS)
- El `input[type=file]` se crea al hacer clic y abre un selector nativo que congela el navegador. Antes de hacer clic, parchea en la página `HTMLInputElement.prototype.click` / `showPicker` / `dispatchEvent` para capturar el input en vez de abrir el selector; luego localiza el input y usa la herramienta de subir archivo. Navegar borra el parche.
- LinkedIn Easy Apply preselecciona un CV viejo: sube siempre el de la carpeta y verifica que quedó seleccionado. Desmarca "Seguir a la empresa".
- Indeed vuelve a leer nombre y teléfono del PDF después de subirlo: verifica el encabezado.
- **Codex:** las subidas solo funcionan con "Permitir acceso a URLs de archivo" activado en la extensión (chrome://extensions → Detalles) y el sitio aprobado.

## LinkedIn
- La etiqueta pública "remoto" no es confiable (6 de 7 "remotas" eran presenciales en una prueba): verifica la modalidad con sesión iniciada **antes** de adaptar.
- Al editar el perfil, el formulario de "agregar puesto" cambia el titular por defecto: deja el titular actual.

## Indeed
- Descubrimiento: `gmaj collector indeed` (lee el JSON `mosaic-provider-jobcards` de `/jobs` con `fetch` dentro de la pestaña). Con pausas fijas cortas responde 429 tras pocas búsquedas: el colector va a ritmo humano (orden aleatorio, 8–18 s entre búsquedas, descanso de 45–90 s cada 6–9, backoff con jitter) y corta tras 2 bloqueos seguidos (`blocked: true`). Tarda ~15–20 min con 25 búsquedas: la pestaña debe quedar en primer plano (en segundo plano Chrome la congela). Avance en `window.__indeed_progress`.
- `/viewjob` por `fetch` da 403: lee la oferta navegando la pestaña.
- En smartapply, "Postularse ahora" abre fuera del grupo de pestañas: quita `target` y haz clic por JS. Hay copias ocultas de "Continuar": usa la de ancho > 0. Un reCAPTCHA visible al final → escalar y dejar la pestaña abierta para el usuario.

## OCC (México)
- Búsquedas (`/empleos/de-<q>/tipo-home-office-remoto/`) y ofertas (`/empleo/oferta/<id>/`) funcionan con `fetch` dentro de la pestaña con sesión; fuera del navegador responden 403: no lo evadas. Colector: `gmaj collector occ`.
- "Postularme" no hace nada mientras el CV del perfil de OCC esté incompleto: complétalo (el lector de CV de OCC duplica experiencias; revisa antes de "Terminar CV").

## Paradox / Olivia (chats de reclutamiento)
- Los botones de respuesta rápida (`.el-checkbox-button`) reciben mal los clics: búscalos por texto exacto con JS, haz clic en su input y verifica que solo ese tenga `.is-checked`. Listas: `.el-select-dropdown__item` y verifica el valor.

## SAP SuccessFactors / iCIMS / Workday
- Formularios dentro de shadow DOM o iframes del mismo origen; navegar al `src` del iframe reinicia la sesión de iCIMS.
- Sesiones que caducan o piden crear cuenta → escalar.

## Entrevistas con IA (video/voz)
- Algunas plataformas (p. ej. Alignerr "Zara", entrevistas de voz) piden encender cámara/micrófono: **nunca** iniciarlas; cerrar la pestaña y escalar.
