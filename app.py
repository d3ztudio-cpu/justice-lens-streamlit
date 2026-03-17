"""Justice Lens Streamlit entrypoint.

Streamlit Community Cloud uses `app.py` by default.

This file injects a small, high-priority CSS shim (fonts + UI bugfixes)
before importing the main app in `justicelens.py`.
"""

import os

import streamlit as st
import streamlit.components.v1 as components

_MATERIAL_SYMBOLS_ROUNDED = (
    "https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:"
    "opsz,wght,FILL,GRAD@20..48,400,0,0"
)

# IMPORTANT: Streamlit requires `set_page_config` to be the first Streamlit call.
st.set_page_config(
    page_title="Justice Lens | Expert Cyber Legal AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Prevent `justicelens.py` from calling `set_page_config` again after we already did.
os.environ["JUSTICE_LENS_SKIP_PAGE_CONFIG"] = "1"

# Best-effort: inject the font link into the actual document <head>.
components.html(
    f"""
    <script>
      (function() {{
        const href = "{_MATERIAL_SYMBOLS_ROUNDED}";
        const id = "jl-material-symbols-rounded";
        const doc = (window.parent && window.parent.document) ? window.parent.document : document;
        if (!doc.getElementById(id)) {{
          const link = doc.createElement("link");
          link.id = id;
          link.rel = "stylesheet";
          link.href = href;
          (doc.head || doc.documentElement).appendChild(link);
        }}
      }})();
    </script>
    """,
    height=0,
)

# Fallback: also inject a link tag (often ends up in body, but still loads the font).
st.markdown(f"<link rel='stylesheet' href='{_MATERIAL_SYMBOLS_ROUNDED}'>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    /* --- High-priority bugfix CSS (loaded before justicelens.py) --- */
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="collapsedControl"] span,
    [data-testid="stSidebarCollapsedControl"] span,
    [data-testid="stSidebarCollapseButton"] i,
    [data-testid="collapsedControl"] i,
    [data-testid="stSidebarCollapsedControl"] i{
        font-family: "Material Symbols Rounded" !important;
        font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        line-height: 1;
    }

    /* Remove unwanted gradient leaks on auth buttons; keep solid / outline looks. */
    section[data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] .stFormSubmitButton > button{
        background: #06B6D4 !important;
        background-image: none !important;
        background-clip: padding-box !important;
        -webkit-background-clip: padding-box !important;
        width: 100% !important;
    }

    /* Segmented control styling for sidebar auth tabs (Login / Create Account). */
    section[data-testid="stSidebar"] [data-baseweb="tab-list"]{
        background: rgba(248, 250, 252, 1);
        border: 1px solid rgba(226, 232, 240, 1);
        border-radius: 999px;
        padding: 3px;
        gap: 0px;
    }
    section[data-testid="stSidebar"] [data-baseweb="tab"]{
        width: 100%;
        border-radius: 999px !important;
        background: transparent !important;
        background-image: none !important;
        background-clip: padding-box !important;
        -webkit-background-clip: padding-box !important;
        font-weight: 800 !important;
        color: #0F172A !important; /* Slate-900 */
        border: 1px solid rgba(226, 232, 240, 0) !important;
    }
    section[data-testid="stSidebar"] [aria-selected="true"][data-baseweb="tab"]{
        background: #06B6D4 !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(6, 182, 212, 0.35) !important;
    }
    section[data-testid="stSidebar"] [aria-selected="false"][data-baseweb="tab"]{
        background: transparent !important;
        color: #0F172A !important; /* Slate-900 */
        border: 1px solid rgba(226, 232, 240, 1) !important;
    }

    /* Center logo in sidebar. */
    section[data-testid="stSidebar"] [data-testid="stImage"]{
        display: flex !important;
        justify-content: center !important;
    }
    section[data-testid="stSidebar"] [data-testid="stImage"] img{
        max-width: min(240px, 100%) !important;
    }

    /* Responsive: prevent sidebar auth inputs from overflowing on small screens. */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] [data-baseweb="input"]{
        max-width: 100% !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# DOM hardening: target any element whose textContent is the ligature text and force the font.
# This survives Streamlit internal class name changes.
components.html(
    """
    <script>
      (function () {
        const TARGETS = new Set(["double_arrow_right", "double_arrow_left"]);
        const FONT = '"Material Symbols Rounded", sans-serif';
        const doc = (window.parent && window.parent.document) ? window.parent.document : document;

        function fixEl(el) {
          if (!el || el.nodeType !== Node.ELEMENT_NODE) return;
          const t = (el.textContent || "").trim();
          if (!TARGETS.has(t)) return;
          el.style.fontFamily = FONT;
          el.style.fontVariationSettings = '"FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24';
          el.style.lineHeight = "1";
        }

        function scan(root) {
          const base = root && root.querySelectorAll ? root : doc;
          base.querySelectorAll("*").forEach(fixEl);
        }

        const obs = new MutationObserver((mutations) => {
          for (const m of mutations) {
            if (m.type === "characterData" && m.target && m.target.parentElement) {
              fixEl(m.target.parentElement);
            }
            for (const n of m.addedNodes || []) {
              if (n && n.querySelectorAll) scan(n);
              fixEl(n);
            }
          }
        });

        scan(doc);
        if (doc.body) obs.observe(doc.body, { subtree: true, childList: true, characterData: true });
      })();
    </script>
    """,
    height=0,
)

import justicelens  # noqa: F401,E402
