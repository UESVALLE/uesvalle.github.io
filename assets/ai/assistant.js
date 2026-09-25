(() => {
  "use strict";

  const messages = document.querySelector("#messages");
  const form = document.querySelector("#chatForm");
  const input = document.querySelector("#messageInput");
  const send = document.querySelector("#sendButton");
  const health = document.querySelector("#apiStatus");
  const model = document.querySelector("#modelStatus");

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
    })[c]);
  }

  function addMessage(text, type = "bot", sources = []) {
    const box = document.createElement("div");
    box.className = `msg ${type}`;
    box.innerHTML = `<div>${escapeHtml(text)}</div>`;

    if (sources.length) {
      const refs = document.createElement("div");
      refs.className = "sources";
      refs.innerHTML =
        "<b>Fuentes consultadas</b>" +
        sources.map((s) =>
          `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.path)}</a>`
        ).join("");
      box.appendChild(refs);
    }

    messages.appendChild(box);
    messages.scrollTop = messages.scrollHeight;
  }

  async function checkHealth() {
    try {
      const r = await fetch("/api/health", { cache: "no-store" });
      const d = await r.json();
      health.textContent =
        d.ok && d.hasApiKey ? "Conectada" : "Revisar configuración";
      model.textContent = d.model || "—";
    } catch {
      health.textContent = "No disponible";
    }
  }

  async function ask(message) {
    addMessage(message, "user");
    send.disabled = true;
    send.textContent = "Consultando…";

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "No fue posible obtener respuesta.");
      }

      addMessage(data.answer, "bot", data.sources || []);

      if (data.model) model.textContent = data.model;
    } catch (error) {
      addMessage(
        error.message || "Ocurrió un error inesperado.",
        "error"
      );
    } finally {
      send.disabled = false;
      send.textContent = "Enviar";
      input.focus();
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    ask(message);
  });

  document.querySelectorAll("[data-question]").forEach((button) => {
    button.addEventListener("click", () => ask(button.dataset.question));
  });

  addMessage(
    "Hola. Soy el piloto del Asistente UESVALLE con NVIDIA Nemotron. En esta primera fase puedo responder utilizando únicamente fuentes autorizadas del repositorio institucional."
  );

  checkHealth();
})();
