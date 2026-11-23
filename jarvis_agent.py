"""Agente de Jarvis para Windows (fase 1: por texto).

Se conecta al Worker de Cloudflare y ejecuta las herramientas que pida el cerebro.
Consume muy pocos recursos: solo una conexión WebSocket y funciones sencillas.
"""
import asyncio
import json
import os
import platform
import shutil
from pathlib import Path

import websockets

URL = os.environ.get("JARVIS_URL", "")
TOKEN = os.environ.get("JARVIS_TOKEN", "")
HOME = Path.home()


def _find(*names):
    for base in (HOME, HOME / "OneDrive"):
        for n in names:
            p = base / n
            if p.is_dir():
                return p
    return HOME / names[0]


FOLDERS = {
    "desktop": _find("Desktop", "Escritorio"),
    "documents": _find("Documents", "Documentos"),
    "downloads": _find("Downloads", "Descargas"),
}

# Solo se pueden abrir estas apps. Añade las tuyas aquí.
APPS = {
    "bloc de notas": "notepad.exe",
    "notepad": "notepad.exe",
    "calculadora": "calc.exe",
    "explorador": "explorer.exe",
    "paint": "mspaint.exe",
    "administrador de tareas": "taskmgr.exe",
    "chrome": "chrome",
    "edge": "msedge",
}

CATEGORIES = {
    "Imágenes": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"},
    "Documentos": {".pdf", ".doc", ".docx", ".txt", ".xlsx", ".pptx", ".csv"},
    "Instaladores": {".exe", ".msi"},
    "Comprimidos": {".zip", ".rar", ".7z"},
    "Vídeo y audio": {".mp4", ".mkv", ".mp3", ".wav"},
}


def search_files(query="", **_):
    q = query.lower().strip()
    if not q:
        return "Error: falta el texto a buscar."
    found = []
    for root in FOLDERS.values():
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d.lower() not in ("node_modules", "__pycache__")]
            for f in filenames:
                if q in f.lower():
                    found.append(os.path.join(dirpath, f))
                    if len(found) >= 15:
                        return "\n".join(found)
    return "\n".join(found) or "No encontré ningún archivo."


def list_folder(folder="desktop", **_):
    path = FOLDERS.get(folder)
    if not path or not path.is_dir():
        return "Error: carpeta no permitida o inexistente."
    items = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
    return "\n".join(items[:80]) or "La carpeta está vacía."


def open_app(name="", **_):
    exe = APPS.get(name.lower().strip())
    if not exe:
        return f"Error: '{name}' no está en la lista de apps permitidas."
    try:
        os.startfile(exe)
        return f"Abierto: {name}"
    except OSError as e:
        return f"Error al abrir {name}: {e}"


def _plan_desktop():
    plan = []
    desktop = FOLDERS["desktop"]
    for item in desktop.iterdir():
        if item.is_dir() or item.suffix.lower() in (".lnk", ".url", ".ini"):
            continue
        for cat, exts in CATEGORIES.items():
            if item.suffix.lower() in exts:
                plan.append((item, cat))
                break
    return plan


def organize_desktop(dry_run=True, **_):
    plan = _plan_desktop()
    if not plan:
        return "El escritorio ya está ordenado, no hay nada que mover."
    resumen = "\n".join(f"{i.name} -> {c}/" for i, c in plan[:40])
    if dry_run:
        return f"Plan ({len(plan)} archivos):\n{resumen}"
    print(f"\n[Jarvis quiere mover {len(plan)} archivos del escritorio]\n{resumen}")
    if input("¿Confirmas? (s/n): ").strip().lower() != "s":
        return "El usuario canceló la operación. No se movió nada."
    moved = 0
    for item, cat in plan:
        dest_dir = FOLDERS["desktop"] / cat
        dest_dir.mkdir(exist_ok=True)
        dest = dest_dir / item.name
        if dest.exists():
            continue
        shutil.move(str(item), str(dest))
        moved += 1
    return f"Listo: moví {moved} archivos."


def system_info(**_):
    total, used, free = shutil.disk_usage(HOME.anchor or "C:\\")
    return f"{platform.system()} {platform.release()}, disco libre: {free // 2**30} GB de {total // 2**30} GB."


TOOLS = {
    "search_files": search_files,
    "list_folder": list_folder,
    "open_app": open_app,
    "organize_desktop": organize_desktop,
    "system_info": system_info,
}


def run_tool(name, args):
    fn = TOOLS.get(name)
    if not fn:
        return f"Error: herramienta desconocida '{name}'."
    try:
        return str(fn(**(args or {})))
    except Exception as e:  # nunca dejar caer el agente por una herramienta
        return f"Error ejecutando {name}: {e}"


async def session():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with websockets.connect(URL, additional_headers=headers, ping_interval=30) as ws:
        print("Conectado a Jarvis. Escribe 'salir' para cerrar.")
        loop = asyncio.get_running_loop()
        while True:
            text = (await loop.run_in_executor(None, input, "Tú: ")).strip()
            if text.lower() in ("salir", "exit"):
                return True
            if not text:
                continue
            await ws.send(json.dumps({"type": "user", "text": text}))
            while True:
                msg = json.loads(await ws.recv())
                if msg["type"] == "tool_call":
                    result = await loop.run_in_executor(None, run_tool, msg["name"], msg.get("args", {}))
                    await ws.send(json.dumps({"type": "tool_result", "id": msg["id"], "result": result}))
                elif msg["type"] == "say":
                    print("Jarvis:", msg["text"])
                    break


async def main():
    if not URL or not TOKEN:
        print("Faltan las variables JARVIS_URL y JARVIS_TOKEN. Mira el README.")
        return
    while True:
        try:
            if await session():
                return
        except (OSError, websockets.ConnectionClosed) as e:
            print(f"Conexión perdida ({e}). Reintentando en 5 s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
