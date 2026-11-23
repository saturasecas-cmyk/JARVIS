# Jarvis, fase 1 (gratis, todo en GitHub)

Cerebro en Cloudflare (Workers AI) + agente ligero en tu PC con Windows. Por ahora se usa escribiendo; la voz es la fase 2.

**Flujo:** programas en GitHub → GitHub Actions despliega el servidor y compila el `.exe` → tú solo descargas y ejecutas. No necesitas instalar Node ni Python en tu PC.

## 1. Crear el repositorio
1. En github.com crea un repositorio nuevo (privado, para proteger tu configuración).
2. Sube todos los archivos de esta carpeta, incluida `.github/` (en la web: *Add file → Upload files*).
3. Para editar código sin instalar nada, pulsa la tecla `.` dentro del repositorio: se abre VS Code en el navegador.

## 2. Guardar los secretos
En el repositorio: *Settings → Secrets and variables → Actions → New repository secret*. Crea tres:

| Nombre | Valor |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare → *My Profile → API Tokens → Create Token → plantilla "Edit Cloudflare Workers"*. |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare → *Workers & Pages*, aparece a la derecha. |
| `JARVIS_TOKEN` | Una contraseña larga inventada por ti (30+ caracteres aleatorios). |

## 3. Desplegar y compilar
Al subir los archivos a `main`, GitHub ejecuta solo dos acciones (pestaña *Actions*):
- **Desplegar Worker de Jarvis**: publica el servidor en Cloudflare. En el registro verás la dirección `https://jarvis.TU-SUBDOMINIO.workers.dev`.
- **Compilar agente de Jarvis (.exe)**: genera `jarvis_agent.exe`. Descárgalo desde el resumen de la ejecución, en *Artifacts*.

Si no se lanzan solas, entra en *Actions*, elige la acción y pulsa *Run workflow*.

## 4. Arrancar el agente en tu PC
En PowerShell, en la carpeta donde descargaste el `.exe`:

```
$env:JARVIS_URL = "wss://jarvis.TU-SUBDOMINIO.workers.dev/ws"
$env:JARVIS_TOKEN = "LA-MISMA-CONTRASEÑA-DE-JARVIS_TOKEN"
.\jarvis_agent.exe
```

Windows SmartScreen puede avisar porque el `.exe` no está firmado: es normal, lo compilas tú.

## 5. Pruébalo
- "¿Qué hay en mi escritorio?"
- "Busca el archivo informe"
- "Abre la calculadora"
- "Ordena mi escritorio" (te pedirá confirmar en la terminal antes de mover nada)

## Seguridad
- El agente solo toca Escritorio, Documentos y Descargas.
- Solo abre las apps de la lista `APPS` en `jarvis_agent.py`.
- Nunca mueve archivos sin que escribas `s` en el PC.
- Nunca subas el token al código: va solo en los secretos de GitHub.

## Notas
- El cupo gratuito de Workers AI es diario. Si se agota, Jarvis dejará de responder hasta el día siguiente.
- El modelo se cambia en la constante `MODEL` de `worker.js`.
- Las acciones de GitHub son gratis en repositorios públicos y tienen minutos mensuales gratis en los privados.
