(() => {
  "use strict";

  const PROD_API = "https://uesvalle-ai-api.vercel.app";
  const API_BASE = /\.vercel\.app$/i.test(window.location.hostname)
    ? window.location.origin
    : PROD_API;

  const qs = (s, root = document) => root.querySelector(s);
  let healthChecked = false;
  let previousFocus = null;

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    })[c]);
  }

  function formatText(value) {
    let safe = escapeHtml(value);
    safe = safe.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    safe = safe.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    return safe.replace(/\n/g, "<br>");
  }

  function errorText(input) {
    if (!input) return "No fue posible completar la consulta.";
    if (typeof input === "string") return input;
    if (input instanceof Error) {
      return typeof input.message === "string" && input.message
        ? input.message
        : "No fue posible completar la consulta.";
    }
    if (typeof input === "object") {
      const candidates = [input.error, input.message, input.detail];
      for (const c of candidates) {
        if (typeof c === "string" && c.trim()) return c;
        if (c && typeof c === "object") {
          const nested = errorText(c);
          if (nested && nested !== "[object Object]") return nested;
        }
      }
      try {
        return JSON.stringify(input);
      } catch {
        return "No fue posible completar la consulta.";
      }
    }
    return String(input);
  }

  function buildUi() {
    const launcher = document.createElement("button");
    launcher.type = "button";
    launcher.className = "pai-launcher";
    launcher.id = "paiLauncher";
    launcher.setAttribute("aria-haspopup", "dialog");
    launcher.setAttribute("aria-controls", "paiChat");
    launcher.setAttribute("aria-label", "Abrir Asistente UESVALLE");
    launcher.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3v3M6 7l2 2M18 7l-2 2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        <rect x="4" y="9" width="16" height="10.5" rx="4" fill="none" stroke="currentColor" stroke-width="1.8"/>
        <circle cx="9" cy="14" r="1" fill="currentColor"/>
        <circle cx="15" cy="14" r="1" fill="currentColor"/>
        <path d="M9 17h6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <span class="pai-launcher-text">Asistente UESVALLE</span>`;

    const backdrop = document.createElement("div");
    backdrop.className = "pai-backdrop";
    backdrop.id = "paiBackdrop";
    backdrop.hidden = true;

    const drawer = document.createElement("aside");
    drawer.className = "pai-chat";
    drawer.id = "paiChat";
    drawer.setAttribute("role", "dialog");
    drawer.setAttribute("aria-modal", "true");
    drawer.setAttribute("aria-labelledby", "paiTitle");
    drawer.hidden = true;
    drawer.innerHTML = `
      <div class="pai-head">
        <div class="pai-brand">
          <span class="pai-kicker">Consulta institucional asistida por IA</span>
          <div class="pai-title-row">
            <h2 id="paiTitle">Asistente UESVALLE</h2>
          </div>
          <div class="pai-sub">Pregunte sobre información autorizada del repositorio institucional.</div>
          <div class="pai-status"><span class="pai-dot" id="paiDot" aria-hidden="true"></span><span id="paiStatus">Conexión pendiente</span></div>
        </div>
        <button class="pai-close" id="paiClose" type="button" aria-label="Cerrar asistente">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
      </div>
      <div class="pai-messages" id="paiMessages" aria-live="polite"></div>
      <div class="pai-quick" aria-label="Preguntas rápidas">
        <button type="button" data-pai-question="¿Qué tableros existen?">¿Qué tableros existen?</button>
        <button type="button" data-pai-question="¿Cómo se actualiza el tablero MPR?">¿Cómo se actualiza MPR?</button>
        <button type="button" data-pai-question="¿Cómo funciona IRCAS?">¿Cómo funciona IRCAS?</button>
      </div>
      <div class="pai-bottom">
        <form class="pai-form" id="paiForm">
          <textarea id="paiInput" maxlength="2500" placeholder="Pregunte sobre información autorizada de UESVALLE…" aria-label="Pregunta para el Asistente UESVALLE" required></textarea>
          <button class="pai-send" id="paiSend" type="submit">Enviar</button>
        </form>
        <p class="pai-note">Piloto de solo consulta. Las respuestas se generan a partir de fuentes autorizadas del repositorio UESVALLE.</p>
      </div>`;

    document.body.append(launcher, backdrop, drawer);

    return {
      launcher,
      backdrop,
      drawer,
      closeButton: qs("#paiClose", drawer),
      messages: qs("#paiMessages", drawer),
      form: qs("#paiForm", drawer),
      input: qs("#paiInput", drawer),
      send: qs("#paiSend", drawer),
      status: qs("#paiStatus", drawer),
      dot: qs("#paiDot", drawer)
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
      refs.innerHTML = "<b>Fuentes consultadas</b>";

      sources.forEach((source) => {
        const a = document.createElement("a");
        a.textContent = source.path || source.title || "Fuente";
        a.href = source.url || "#";
        a.target = "_blank";
        a.rel = "noopener";
        refs.appendChild(a);
      });
      box.appendChild(refs);
    }

    ui.messages.appendChild(box);
    ui.messages.scrollTop = ui.messages.scrollHeight;
  }

  function setStatus(text, state = "") {
    ui.status.textContent = text;
    ui.dot.classList.remove("ok", "bad");
    if (state) ui.dot.classList.add(state);
  }

  async function checkHealth() {
    if (healthChecked) return;
    healthChecked = true;
    setStatus("Conectando…");

    try {
      const response = await fetch(`${API_BASE}/api/health`, {
        cache: "no-store",
        credentials: "omit"
      });
      const data = await response.json();

      if (response.ok && data.ok && data.hasApiKey) {
        setStatus("NVIDIA Nemotron · RAG institucional", "ok");
      } else {
        setStatus("Revisar configuración del servicio", "bad");
      }
    } catch {
      setStatus("Servicio no disponible", "bad");
    }
  }

  function openChat() {
    previousFocus = document.activeElement;
    ui.backdrop.hidden = false;
    ui.drawer.hidden = false;
    document.body.classList.add("pai-opened");
    ui.launcher.setAttribute("aria-expanded", "true");
    checkHealth();
    window.setTimeout(() => ui.input.focus(), 0);
  }

  function closeChat() {
    ui.backdrop.hidden = true;
    ui.drawer.hidden = true;
    document.body.classList.remove("pai-opened");
    ui.launcher.setAttribute("aria-expanded", "false");
    if (previousFocus && typeof previousFocus.focus === "function") previousFocus.focus();
  }

  async function ask(message) {
    const question = String(message || "").trim();
    if (!question || ui.send.disabled) return;

    addMessage(question, "user");
    ui.input.value = "";
    ui.send.disabled = true;
    ui.send.textContent = "Consultando…";
    setStatus("Consultando fuentes autorizadas…");

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "omit",
        body: JSON.stringify({ message: question })
      });

      let data;
      try {
        data = await response.json();
      } catch {
        throw new Error("El servicio devolvió una respuesta no válida.");
      }

      if (!response.ok) {
        throw new Error(errorText(data));
      }

      addMessage(data.answer, "bot", data.sources || []);
      setStatus("NVIDIA Nemotron · RAG institucional", "ok");
    } catch (error) {
      addMessage(errorText(error), "error");
      setStatus("No fue posible completar la consulta", "bad");
    } finally {
      ui.send.disabled = false;
      ui.send.textContent = "Enviar";
      ui.input.focus();
    }
  }

  ui.launcher.addEventListener("click", openChat);
  ui.closeButton.addEventListener("click", closeChat);
  ui.backdrop.addEventListener("click", closeChat);
  ui.form.addEventListener("submit", (event) => {
    event.preventDefault();
    ask(ui.input.value);
  });

  ui.drawer.querySelectorAll("[data-pai-question]").forEach((button) => {
    button.addEventListener("click", () => ask(button.dataset.paiQuestion));
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !ui.drawer.hidden) closeChat();
  });

  addMessage("Hola. Soy el Asistente UESVALLE. Puedo consultar fuentes autorizadas del repositorio institucional y mostrarle las referencias utilizadas.");
})();
