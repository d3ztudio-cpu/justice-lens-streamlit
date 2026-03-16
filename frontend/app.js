const DEFAULT_API_BASE = "http://localhost:8000";

function el(id) {
  return document.getElementById(id);
}

function loadApiBase() {
  return localStorage.getItem("jl_api_base") || DEFAULT_API_BASE;
}

function setApiBase(value) {
  localStorage.setItem("jl_api_base", value);
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
  el("apiBaseLabel").textContent = apiBase;
  const resp = await fetch(`${apiBase}/api/chat`, {
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

function init() {
  initTheme();
  el("apiBaseLabel").textContent = loadApiBase();

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
      appendMessage({ role: "assistant", content: `Error: ${err.message}`, category: "ERROR" });
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

  const params = new URLSearchParams(window.location.search);
  const apiBase = params.get("apiBase");
  if (apiBase) {
    setApiBase(apiBase);
    el("apiBaseLabel").textContent = apiBase;
  }
}

init();
