const DEFAULT_API_BASE = "";

function el(id) {
  return document.getElementById(id);
}

function isLocalhost() {
  return (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "::1"
  );
}

function normalizeApiBase(value) {
  const v = String(value || "").trim();
  if (!v) return "";
  return v.replace(/\/+$/, "");
}

function loadApiBase() {
  const saved = normalizeApiBase(localStorage.getItem("jl_api_base"));
  if (saved) return saved;
  if (DEFAULT_API_BASE) return normalizeApiBase(DEFAULT_API_BASE);
  return isLocalhost() ? "http://localhost:8000" : "";
}

function setApiBase(value) {
  const v = normalizeApiBase(value);
  if (!v) localStorage.removeItem("jl_api_base");
  else localStorage.setItem("jl_api_base", v);
}

function apiLabel(value) {
  return value ? value : "(same origin)";
}

function showBanner(message) {
  const b = el("banner");
  b.textContent = message;
  b.style.display = "block";
}

function hideBanner() {
  const b = el("banner");
  b.textContent = "";
  b.style.display = "none";
}

function appendMessage({ role, content, category }) {
  const chat = el("chat");
  const node = document.createElement("div");
  node.className = `msg ${role}`;

  const meta = document.createElement("div");
  meta.className = "meta";
  const badge = document.createElement("span");
  badge.className = `badge ${category === "PHYSICAL" ? "warn" : "good"}`;
  badge.textContent = category ? category : role.toUpperCase();
  meta.appendChild(badge);
  node.appendChild(meta);

  const body = document.createElement("div");
  body.textContent = content;
  node.appendChild(body);

  chat.appendChild(node);
  chat.scrollTop = chat.scrollHeight;
}

function setWelcomeVisible(visible) {
  el("welcome").style.display = visible ? "block" : "none";
}

async function sendMessage(message) {
  const apiBase = loadApiBase();
  el("apiBaseLabel").textContent = apiLabel(apiBase);

  const url = apiBase ? `${apiBase}/api/chat` : "/api/chat";
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
  return await resp.json();
}

function autoGrow(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 160) + "px";
}

function setTheme(theme) {
  document.body.dataset.theme = theme;
  localStorage.setItem("jl_theme", theme);
  el("lightBtn").classList.toggle("active", theme !== "dark");
  el("darkBtn").classList.toggle("active", theme === "dark");
}

function initTheme() {
  const theme = localStorage.getItem("jl_theme") || "light";
  setTheme(theme);
}

function openModal() {
  el("apiModal").classList.add("open");
  el("apiModal").setAttribute("aria-hidden", "false");
}

function closeModal() {
  el("apiModal").classList.remove("open");
  el("apiModal").setAttribute("aria-hidden", "true");
}

function initApiModal() {
  const input = el("apiInput");
  input.value = loadApiBase();

  el("apiBtn").addEventListener("click", () => {
    input.value = loadApiBase();
    openModal();
    input.focus();
  });
  el("apiClose").addEventListener("click", closeModal);
  el("apiOverlay").addEventListener("click", closeModal);

  el("apiReset").addEventListener("click", () => {
    setApiBase("");
    input.value = loadApiBase();
    el("apiBaseLabel").textContent = apiLabel(loadApiBase());
    if (!isLocalhost()) showBanner("Backend not configured. Click API and set your backend URL.");
  });

  el("apiSave").addEventListener("click", () => {
    setApiBase(input.value);
    el("apiBaseLabel").textContent = apiLabel(loadApiBase());
    hideBanner();
    closeModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
}

function init() {
  initTheme();
  initApiModal();

  const params = new URLSearchParams(window.location.search);
  const apiBase = params.get("apiBase");
  if (apiBase) {
    setApiBase(apiBase);
  }

  const base = loadApiBase();
  el("apiBaseLabel").textContent = apiLabel(base);

  if (!isLocalhost() && !base) {
    showBanner("Backend not configured. Click API and set your backend URL (e.g. https://your-api.onrender.com). ");
  }

  const textarea = el("message");
  textarea.addEventListener("input", () => autoGrow(textarea));

  el("chatForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = textarea.value.trim();
    if (!message) return;

    setWelcomeVisible(false);
    appendMessage({ role: "user", content: message, category: "USER" });
    textarea.value = "";
    autoGrow(textarea);

    try {
      el("sendBtn").disabled = true;
      const out = await sendMessage(message);
      appendMessage({ role: "assistant", content: out.answer, category: out.category });
    } catch (err) {
      const msg = String(err && err.message ? err.message : err);
      const help =
        !isLocalhost() && !loadApiBase()
          ? "\n\nFix: Click API and set your backend URL."
          : "";
      appendMessage({ role: "assistant", content: `Error: ${msg}${help}`, category: "ERROR" });
    } finally {
      el("sendBtn").disabled = false;
    }
  });

  el("clearBtn").addEventListener("click", () => {
    el("chat").innerHTML = "";
    setWelcomeVisible(true);
  });

  document.querySelectorAll(".tile").forEach((btn) => {
    btn.addEventListener("click", () => {
      textarea.value = btn.getAttribute("data-seed") || "";
      autoGrow(textarea);
      textarea.focus();
    });
  });

  el("lightBtn").addEventListener("click", () => setTheme("light"));
  el("darkBtn").addEventListener("click", () => setTheme("dark"));
}

init();
