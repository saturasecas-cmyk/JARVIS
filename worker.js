import { DurableObject } from "cloudflare:workers";

// Modelo gratuito de Workers AI. Puedes cambiarlo por otro con "function calling".
const MODEL = "@cf/meta/llama-3.1-8b-instruct";
const MAX_STEPS = 5;

const SYSTEM =
  "Eres Jarvis, el asistente personal del usuario, al estilo de Iron Man. " +
  "Respondes siempre en español, de forma breve y directa (máximo 2 o 3 frases), " +
  "porque tus respuestas se leerán o dirán en voz alta. " +
  "Usa las herramientas cuando el usuario pida algo sobre su ordenador. " +
  "Si una herramienta devuelve un error, dilo con claridad. " +
  "Nunca inventes archivos ni resultados.";

const TOOLS = [
  {
    name: "search_files",
    description: "Busca archivos por nombre en Escritorio, Documentos y Descargas del PC.",
    parameters: {
      type: "object",
      properties: { query: { type: "string", description: "Parte del nombre del archivo" } },
      required: ["query"],
    },
  },
  {
    name: "list_folder",
    description: "Lista el contenido de una carpeta del PC.",
    parameters: {
      type: "object",
      properties: { folder: { type: "string", enum: ["desktop", "documents", "downloads"] } },
      required: ["folder"],
    },
  },
  {
    name: "open_app",
    description: "Abre una aplicación del PC (bloc de notas, calculadora, chrome, explorador...).",
    parameters: {
      type: "object",
      properties: { name: { type: "string", description: "Nombre de la aplicación" } },
      required: ["name"],
    },
  },
  {
    name: "organize_desktop",
    description:
      "Ordena los archivos del escritorio en carpetas por tipo. Con dry_run=true solo enseña el plan. " +
      "Con dry_run=false el usuario debe confirmar en el PC antes de mover nada.",
    parameters: {
      type: "object",
      properties: { dry_run: { type: "boolean" } },
      required: ["dry_run"],
    },
  },
  {
    name: "system_info",
    description: "Devuelve información del PC: sistema, RAM libre y espacio en disco.",
    parameters: { type: "object", properties: {} },
  },
];

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname !== "/ws") return new Response("Jarvis online");
    if (req.headers.get("Upgrade") !== "websocket") return new Response("Se espera WebSocket", { status: 426 });
    if (req.headers.get("Authorization") !== `Bearer ${env.JARVIS_TOKEN}`) {
      return new Response("No autorizado", { status: 401 });
    }
    const stub = env.HUB.get(env.HUB.idFromName("main"));
    return stub.fetch(req);
  },
};

export class JarvisHub extends DurableObject {
  pending = new Map();

  async fetch(req) {
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    // API con hibernación: el objeto no consume cuota mientras no hay mensajes.
    this.ctx.acceptWebSocket(server);
    return new Response(null, { status: 101, webSocket: client });
  }

  async webSocketMessage(ws, raw) {
    let msg;
    try {
      msg = JSON.parse(raw);
    } catch {
      return;
    }
    if (msg.type === "tool_result") {
      const resolve = this.pending.get(msg.id);
      if (resolve) {
        this.pending.delete(msg.id);
        resolve(msg.result);
      }
    } else if (msg.type === "user") {
      await this.think(ws, String(msg.text ?? ""));
    }
  }

  callTool(ws, name, args) {
    const id = crypto.randomUUID();
    return new Promise((resolve) => {
      this.pending.set(id, resolve);
      ws.send(JSON.stringify({ type: "tool_call", id, name, args }));
      setTimeout(() => {
        if (this.pending.delete(id)) resolve("Error: el PC no respondió a tiempo.");
      }, 90000);
    });
  }

  async think(ws, text) {
    const history = (await this.ctx.storage.get("history")) ?? [];
    history.push({ role: "user", content: text });
    let answer = "No he podido completar la petición.";

    try {
      for (let step = 0; step < MAX_STEPS; step++) {
        const res = await this.env.AI.run(MODEL, {
          messages: [{ role: "system", content: SYSTEM }, ...history],
          tools: TOOLS,
          max_tokens: 400,
        });
        const calls = res.tool_calls ?? [];
        if (!calls.length) {
          const t = (res.response ?? "").trim();
          if (t) answer = t;
          history.push({ role: "assistant", content: answer });
          break;
        }
        for (const c of calls) {
          let args = c.arguments ?? {};
          if (typeof args === "string") {
            try {
              args = JSON.parse(args);
            } catch {
              args = {};
            }
          }
          const result = await this.callTool(ws, c.name, args);
          history.push({ role: "tool", name: c.name, content: String(result).slice(0, 3000) });
        }
      }
    } catch (e) {
      answer = "Error del cerebro: " + e.message;
    }

    await this.ctx.storage.put("history", history.slice(-20));
    ws.send(JSON.stringify({ type: "say", text: answer }));
  }
}
