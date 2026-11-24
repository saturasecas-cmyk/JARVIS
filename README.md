# Jarvis (gratis, todo en GitHub)

Cerebro y reconocimiento de voz en Cloudflare (gratis) + agente ligero en tu PC con Windows.

**Flujo:** programas en GitHub → GitHub Actions compila el `.exe` → tú lo descargas y lo ejecutas. No necesitas instalar Python ni Node.

## Qué sabe hacer
- **Escucha** "hey Jarvis" (detector local, casi no gasta CPU). Tras el pitido, di tu orden y calla un segundo.
- **Lee** archivos de texto, código y Word (`.docx`) de tu carpeta de usuario.
- **Escribe en el documento que tengas abierto** (Bloc de notas, Word, WordPad, VS Code...) donde esté el cursor.
- **Crea o amplía** archivos de texto en Escritorio, Documentos y Descargas (te pide permiso con una ventana).
- Busca archivos, lista carpetas, abre apps, ordena el escritorio (con permiso) y da info del PC.
- **Habla** con la voz de Windows.

## Instalación
1. En el repo: pestaña **Actions** → "Compilar agente de Jarvis (.exe)" → última ejecución verde → **Artifacts** → descarga `jarvis_agent-windows` y descomprímelo en una carpeta fija (por ejemplo `C:\Jarvis`).
2. Abre PowerShell en esa carpeta (escribe `powershell` en la barra de direcciones del Explorador) y ejecuta:
   ```
   .\jarvis_agent.exe --setup
   ```
   Pide la dirección (`jarvis.saturasecas.workers.dev`) y la contraseña. Se guardan en tu PC, no hay que repetirlo.
3. Pruébalo con ventana: `.\jarvis_agent.exe`. Di "hey Jarvis", espera el pitido y habla. También puedes escribir.
4. Cuando te guste, que arranque solo con Windows y sin ventana:
   ```
   .\jarvis_agent.exe --autostart on
   ```
   (`--autostart off` lo quita.) No muevas la carpeta después de activarlo.

Windows pedirá permiso para el micrófono la primera vez: *Configuración → Privacidad → Micrófono → permitir apps de escritorio*. SmartScreen puede avisar de que el `.exe` no está firmado: es normal.

## Ejemplos
- "Hey Jarvis… ¿qué hay en mi escritorio?"
- "Lee el archivo apuntes y resúmelo."
- "Escribe en mi documento: reunión mañana a las diez." (haz clic en el documento antes)
- "Crea un archivo lista.txt con tres ideas para el servidor."

## Seguridad
- Solo lee dentro de tu carpeta de usuario y nunca `.ssh`, `AppData`, ni archivos con nombres como *password*, *token* o *secret*.
- Solo escribe en Escritorio, Documentos y Descargas, nunca sobrescribe, y siempre pide confirmación.
- Solo teclea en apps de la lista `TYPE_ALLOWED` (nunca en terminales ni navegadores) y se detiene si cambias de ventana.
- Solo abre las apps de la lista `APPS`.
- El texto de los archivos que lee se trata como datos, pero un modelo pequeño puede equivocarse: no le pidas que lea archivos de origen dudoso.
- El audio se envía a tu Worker de Cloudflare solo después de oír "hey Jarvis".
- Nunca subas la contraseña al código.

## Cerebro: Gemini (opcional, gratis)
Por defecto Jarvis usa Workers AI. Con una clave de Gemini es bastante más listo eligiendo herramientas:
1. Crea la clave gratis en https://aistudio.google.com/apikey
2. Cloudflare → *Workers & Pages* → `jarvis` → *Settings* → *Variables and Secrets* → *Add* → tipo **Secret**, nombre `GEMINI_API_KEY`, pega la clave.
3. Opcional: variable `GEMINI_MODEL` para cambiar de modelo (por defecto `gemini-2.5-flash`).

Si Gemini falla (clave mala, cupo agotado), Jarvis avisa y sigue con Workers AI. La clave nunca debe ir en el código ni en GitHub.

## Límites
- Con el PC apagado no puede tocar el PC. Para encenderlo hace falta algo siempre encendido en tu red (Wake-on-LAN).
- Workers AI tiene un cupo gratuito diario; si se agota, Jarvis para hasta el día siguiente.
- El modelo (`MODEL` en `worker.js`) es pequeño: a veces se equivoca eligiendo herramientas.

## Desarrollo
- Servidor: `worker.js` + `wrangler.toml`. La acción "Desplegar Worker" es opcional y solo actúa si creas los secretos `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` y `JARVIS_TOKEN`.
- Agente: `jarvis_agent.py`. Cada herramienta nueva es una función más en `TOOLS` y su descripción en `worker.js`.
