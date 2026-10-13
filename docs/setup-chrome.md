# Preparar Chrome

El agente te guía; esto es la referencia.

## 1. Google Chrome
- Windows: `winget install --id Google.Chrome -e` o https://www.google.com/chrome/
- macOS: `brew install --cask google-chrome` o https://www.google.com/chrome/
Usa tu perfil de Chrome de siempre (ahí están tus sesiones).

## 2a. Si usas Claude
1. Instala **Claude in Chrome** desde la Chrome Web Store (busca "Claude" publicado por Anthropic) y fíjala en la barra.
2. Inicia sesión con la misma cuenta de Claude Desktop.
3. En Claude Desktop, en una sesión de Code del proyecto, conecta Chrome cuando lo pida (o escribe `/chrome`).
4. Permisos por sitio: cuando la extensión pregunte, permite LinkedIn, Indeed, OCC, Computrabajo y los portales de empleo que vayan apareciendo.

## 2b. Si usas Codex
1. Instala la extensión de Chrome de Codex/ChatGPT desde la Chrome Web Store e inicia sesión con tu cuenta de ChatGPT.
2. chrome://extensions → la extensión → **Detalles** → activa **Permitir acceso a URLs de archivo** (sin esto no puede adjuntar tu CV).
3. Aprueba los sitios de `catalogs/channels.yaml` cuando la app los pida. Si una vacante usa un dominio nuevo, Codex lo marcará como bloqueado: apruébalo solo si es el portal de empleo de la empresa.
4. En Windows, el uso del escritorio/navegador por Codex toma el primer plano: no uses la computadora durante la corrida.

## 3. Inicia sesión tú
LinkedIn, Indeed, OCC, Computrabajo (los que uses) y Gmail. El agente nunca teclea contraseñas ni códigos.

## 4. Durante las corridas
- Deja Chrome abierto. El agente abre pestañas nuevas y las cierra al terminar cada vacante.
- Modo dual: Claude y Codex nunca usan el navegador al mismo tiempo.
