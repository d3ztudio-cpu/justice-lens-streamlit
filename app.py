"""Justice Lens Streamlit entrypoint.

Streamlit Community Cloud uses `app.py` by default.

This file injects a small, high-priority CSS shim (fonts + UI bugfixes)
before importing the main app in `justicelens.py`.
"""

import os
import streamlit as st

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

# Font pre-inject (browser will load it early).
st.markdown(
    f"<link rel='stylesheet' href='{_MATERIAL_SYMBOLS_ROUNDED}'>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* --- High-priority bugfix CSS (loaded before justicelens.py) --- */

    /* Force sidebar toggle icons to render as Material Symbols (prevents text like double_arrow_right). */
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
        background: rgba(226, 232, 240, 0.75);
        border: 1px solid rgba(226, 232, 240, 1);
        border-radius: 999px;
        padding: 4px;
        gap: 4px;
    }
    section[data-testid="stSidebar"] [data-baseweb="tab"]{
        border-radius: 999px !important;
        background: transparent !important;
        background-image: none !important;
        background-clip: padding-box !important;
        -webkit-background-clip: padding-box !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] [aria-selected="true"][data-baseweb="tab"]{
        background: #06B6D4 !important;
        color: #FFFFFF !important;
    }

    /* Center logo in sidebar. */
    section[data-testid="stSidebar"] img{
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

import justicelens  # noqa: F401,E402
