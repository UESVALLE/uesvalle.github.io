(() => {
  "use strict";

  const PROD_API = "https://uesvalle-ai-api.vercel.app";
  const ON_VERCEL = /\.vercel\.app$/i.test(window.location.hostname);
  const API_BASE = ON_VERCEL ? window.location.origin : PROD_API;
  const API_CREDENTIALS = ON_VERCEL ? "same-origin" : "omit";
  const CAT_SRC = "assets/ai/asistente-gatita.webp";

  const qs = (s, root = document) => root.querySelector(s);
  let previousFocus = null;
  let healthChecked = false;

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[c]);
  }

  function formatText(value) {
    let safe = escapeHtml(value);
    safe = safe.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    safe = safe.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    return safe.replace(/\n/g, "<br>");
  }

  function extractError(payload, fallback = "No fue posible completar la consulta.") {
    if (!payload) return fallback;
    if (typeof payload === "string") return payload.trim() || fallback;
    if (payload instanceof Error) return extractError(payload.message, fallback);
    if (typeof payload === "object") {
      for (const key of ["message", "error", "detail"]) {
        if (payload[key] != null) {
          const text = extractError(payload[key], "");
          if (text) return text;
        }
      }
    }
    return fallback;
  }

  async function readPayload(response) {
    const type = response.headers.get("content-type") || "";
    if (type.includes("application/json")) {
      try { return await response.json(); } catch { return null; }
    }
    try { return await response.text(); } catch { return null; }
  }

  function buildUi() {
    const launcher = document.createElement("button");
    launcher.type = "button";
    launcher.className = "pai-launcher";
    launcher.setAttribute("aria-label", "Abrir Asistente UESVALLE");
    launcher.setAttribute("aria-haspopup", "dialog");
    launcher.innerHTML = `
      <img class="pai-launcher-cat" src="${CAT_SRC}" alt="" aria-hidden="true">
      <span class="pai-launcher-pill">
        <span class="pai-launcher-chat" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M5 5h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-7l-4.5 3V17H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="8" cy="11" r="1" fill="currentColor"/><circle cx="12" cy="11" r="1" fill="currentColor"/><circle cx="16" cy="11" r="1" fill="currentColor"/></svg>
        </span>
        <span class="pai-launcher-text">Pregúntame aquí</span>
        <span class="pai-launcher-arrow" aria-hidden="true">›</span>
      </span>`;

    const chat = document.createElement("aside");
    chat.className = "pai-chat";
    chat.id = "paiChat";
    chat.hidden = true;
    chat.setAttribute("role", "dialog");
    chat.setAttribute("aria-labelledby", "paiTitle");
    chat.innerHTML = `
      <div class="pai-head">
        <div class="pai-avatar"><img src="${CAT_SRC}" alt=""></div>
        <div class="pai-brand">
          <h2 id="paiTitle">Asistente UESVALLE</h2>
          <div class="pai-presence"><span class="pai-dot" id="paiDot"></span><span id="paiStatus">Disponible</span></div>
        </div>
        <button class="pai-close" id="paiClose" type="button" aria-label="Cerrar asistente">
          <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
      </div>
      <div class="pai-messages" id="paiMessages" aria-live="polite"></div>
      <div class="pai-bottom">
        <form class="pai-form" id="paiForm">
          <textarea id="paiInput" maxlength="2500" rows="1" placeholder="Escribe tu pregunta…" aria-label="Pregunta para el Asistente UESVALLE" required></textarea>
          <button class="pai-send" id="paiSend" type="submit" aria-label="Enviar pregunta">
            <svg viewBox="0 0 24 24"><path d="m4 4 16 8-16 8 3-8-3-8Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M7 12h13" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>
          </button>
        </form>
        <p class="pai-foot">Consulta asistida por IA. Verifique la información crítica en la fuente citada.</p>
      </div>`;

    document.body.append(launcher, chat);
    return {
      launcher,
      chat,
      close: qs("#paiClose", chat),
      messages: qs("#paiMessages", chat),
      form: qs("#paiForm", chat),
      input: qs("#paiInput", chat),
      send: qs("#paiSend", chat),
      status: qs("#paiStatus", chat),
      dot: qs("#paiDot", chat)
    };
  }

  const ui = buildUi();

  function addMessage(text, type = "bot", sources = []) {
    const box = document.createElement("div");
    box.className = `pai-msg ${type}`;

    const body = document.createElement("div");
    body.innerHTML = formatText(text);
    box.appendChild(body);

    if (sources.length) {
      const refs = document.createElement("div");
      refs.className = "pai-sources";
      const title = document.createElement("b");
      title.textContent = sources.length === 1 ? "Fuente" : "Fuentes";
      refs.appendChild(title);
      sources.forEach((source) => {
        const link = document.createElement("a");
        link.textContent = source.path || source.title || "Fuente consultada";
        link.href = source.url || "#";
        link.target = "_blank";
        link.rel = "noopener";
        refs.appendChild(link);
      });
      box.appendChild(refs);
    }

    ui.messages.appendChild(box);
    ui.messages.scrollTop = ui.messages.scrollHeight;
    return box;
  }

  function addThinking() {
    const box = document.createElement("div");
    box.className = "pai-msg bot";
    box.dataset.thinking = "1";
    box.innerHTML = '<span class="pai-thinking" aria-label="Consultando"><i></i><i></i><i></i></span>';
    ui.messages.appendChild(box);
    ui.messages.scrollTop = ui.messages.scrollHeight;
    return box;
  }

  function setStatus(text, bad = false) {
    ui.status.textContent = text;
    ui.dot.classList.toggle("bad", bad);
  }

  async function checkHealth() {
    if (healthChecked) return;
    healthChecked = true;
    try {
      const response = await fetch(`${API_BASE}/api/health`, {
        cache: "no-store",
        credentials: API_CREDENTIALS
      });
      if (response.ok) setStatus("Disponible");
      else setStatus("Servicio temporalmente no disponible", true);
    } catch {
      setStatus("Servicio temporalmente no disponible", true);
    }
  }

  function openChat() {
    previousFocus = document.activeElement;
    ui.launcher.hidden = true;
    ui.chat.hidden = false;
    checkHealth();
    window.setTimeout(() => ui.input.focus(), 0);
  }

  function closeChat() {
    ui.chat.hidden = true;
    ui.launcher.hidden = false;
    if (previousFocus && typeof previousFocus.focus === "function") previousFocus.focus();
  }

  async function ask(message) {
    const question = String(message || "").trim();
    if (!question || ui.send.disabled) return;

    addMessage(question, "user");
    ui.input.value = "";
    ui.send.disabled = true;
    const thinking = addThinking();

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: API_CREDENTIALS,
        body: JSON.stringify({ message: question })
      });

      const payload = await readPayload(response);
      if (!response.ok) throw new Error(extractError(payload));

      thinking.remove();
      addMessage(payload?.answer || "No se recibió una respuesta.", "bot", payload?.sources || []);
      setStatus("Disponible");
    } catch (error) {
      thinking.remove();
      const detail = extractError(error);
      const friendly = /protected deployment/i.test(detail)
        ? "El entorno de prueba requiere autenticación de Vercel. Recargue la página después de iniciar sesión."
        : detail;
      addMessage(friendly, "error");
      setStatus("No fue posible completar la consulta", true);
    } finally {
      ui.send.disabled = false;
      ui.input.focus();
    }
  }

  ui.launcher.addEventListener("click", openChat);
  ui.close.addEventListener("click", closeChat);
  ui.form.addEventListener("submit", (event) => {
    event.preventDefault();
    ask(ui.input.value);
  });
  ui.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      ui.form.requestSubmit();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !ui.chat.hidden) closeChat();
  });

  addMessage("Hola 👋 ¿En qué te puedo ayudar?");
})();
