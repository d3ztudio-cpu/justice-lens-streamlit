import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import sys
import json
import uuid
import requests
import time
import re
import html
import urllib.parse
import base64
import io
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
import streamlit.components.v1 as components

# ==========================================
# CONFIGURATION
# ==========================================
PINECONE_KEY = st.secrets.get("PINECONE_KEY", "")
INDEX_NAME = "justice-lens"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
FIREBASE_WEB_API_KEY = st.secrets.get("FIREBASE_WEB_API_KEY", "AIzaSyAklh23Fu6-P5vNsGDh2-U9titgRvqzJaU")
LOGO_FALLBACK_URL = "https://i.ibb.co/mCP4BQC5/width-1200.jpg"
LOCAL_LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")
LOGO_SOURCE = LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else LOGO_FALLBACK_URL
APP_TZ = ZoneInfo("Asia/Kolkata")


def utc_now():
    return datetime.now(timezone.utc)

def format_app_time(dt_obj, fmt='%d %b, %H:%M'):
    if not dt_obj:
        return "N/A"
    try:
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        return dt_obj.astimezone(APP_TZ).strftime(fmt)
    except Exception:
        return "N/A"

# --- PAGE CONFIG ---
# Streamlit requires `set_page_config` to be the first Streamlit call.
# When running via `app.py`, that file sets the config first and sets an env var to skip this.
if not os.environ.get("JUSTICE_LENS_SKIP_PAGE_CONFIG"):
    st.set_page_config(
        page_title="Justice Lens | Expert Cyber Legal AI",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

# --- Justice Lens: Deep Dive Theme ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Public+Sans:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0,0');

    :root{
        --jl-bg: #0D1117;
        --jl-card: #161B22;
        --jl-text: #C9D1D9;
        --jl-muted: #8B949E;
        --jl-border: #30363D;
        --jl-primary: #58A6FF;
        --jl-primary-2: #388BFD;
        --jl-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        --jl-shadow-sm: 0 6px 18px rgba(0, 0, 0, 0.15);
        --jl-radius: 14px;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"]{
        background: var(--jl-bg) !important;
        overflow-x: hidden !important;
    }

    html, body, [data-testid="stMarkdownContainer"] p,
    .stMarkdown, label, li, h1, h2, h3, h4, h5, h6, div, span{
        font-family: "Public Sans", Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif !important;
        color: var(--jl-text) !important;
    }

    .main .block-container{
        padding-top: 1.25rem !important;
        padding-bottom: 5.5rem !important;
        max-width: 1120px !important;
    }
    [data-testid="stAppViewContainer"] > .main{
        margin-left: 0 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"]{
        background: var(--jl-card) !important;
        border-right: 1px solid var(--jl-border) !important;
    }
    [data-testid="stSidebarContent"]{
        padding-top: 0.5rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    section[data-testid="stSidebar"] label{
        color: var(--jl-text) !important;
    }
    .jl-sidebar-connected{
        color: var(--jl-text) !important;
        background: rgba(88, 166, 255, 0.1) !important;
        border: 1px solid var(--jl-border) !important;
        border-radius: 10px !important;
        font-weight: 700;
        padding: 0.35rem 0.55rem;
        display: inline-block;
    }
    .jl-sidebar-connected::selection,
    .jl-sidebar-connected *::selection{
        background: rgba(88, 166, 255, 0.22);
        color: var(--jl-text) !important;
    }

    /* Remove fullscreen/view controls */
    button[title="View fullscreen"],
    button[aria-label="View fullscreen"],
    button[title*="fullscreen" i],
    button[aria-label*="fullscreen" i],
    [data-testid="stFullScreenButton"]{
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* Remove Streamlit toolbar/decorations but keep header so sidebar toggle can appear */
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }
    header[data-testid="stHeader"]{
        background: transparent !important;
        border-bottom: none !important;
        pointer-events: none !important;
    }

    /* Hide Streamlit's sidebar toggle controls; use custom hamburger on mobile only */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    button[aria-label="Open sidebar"],
    button[aria-label="Close sidebar"],
    button[title="Open sidebar"],
    button[title="Close sidebar"],
    button[title="Show sidebar"],
    button[title="Hide sidebar"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* Buttons */
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button{
        background: var(--jl-primary) !important;
        border: 1px solid rgba(88, 166, 255, 0.35) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        padding: 0.58rem 0.9rem !important;
        font-weight: 700 !important;
        box-shadow: var(--jl-shadow-sm) !important;
        transition: transform 0.12s ease, background 0.12s ease, box-shadow 0.12s ease;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover{
        background: var(--jl-primary-2) !important;
        transform: translateY(-1px);
        box-shadow: 0 12px 26px rgba(0, 0, 0, 0.2) !important;
    }

    /* Inputs */
    input, textarea, [data-baseweb="select"] > div{
        background: #0D1117 !important;
        border: 1px solid var(--jl-border) !important;
        border-radius: 12px !important;
        color: var(--jl-text) !important;
        box-shadow: none !important;
    }
    input:focus, textarea:focus{
        border-color: var(--jl-primary) !important;
        box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.2) !important;
        outline: none !important;
    }

    /* Hero + cards */
    .jl-hero{
        background: var(--jl-card);
        border: 1px solid var(--jl-border);
        border-radius: var(--jl-radius);
        padding: 1.35rem 1.3rem;
        box-shadow: var(--jl-shadow);
        text-align: center;
    }
    .jl-hero .title{
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .jl-hero .subtitle{
        margin-top: 0.35rem;
        font-size: 1rem;
        font-weight: 600;
        color: var(--jl-muted) !important;
    }
    .jl-card{
        background: var(--jl-card);
        border: 1px solid var(--jl-border);
        border-radius: var(--jl-radius);
        padding: 1rem 1rem;
        box-shadow: var(--jl-shadow-sm);
    }
    .jl-feature{
        background: var(--jl-card);
        border: 1px solid var(--jl-border);
        border-radius: var(--jl-radius);
        padding: 1rem 1rem;
        box-shadow: var(--jl-shadow-sm);
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .jl-feature .kicker{
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--jl-muted) !important;
        margin-bottom: 0.25rem;
        font-weight: 700;
    }
    .jl-feature .headline{
        font-size: 1.05rem;
        font-weight: 800;
        margin: 0.1rem 0 0.35rem 0;
    }
    .jl-feature .desc{
        margin: 0;
        color: var(--jl-muted) !important;
        line-height: 1.55;
        font-size: 0.95rem;
        flex: 1;
    }

    /* Chat */
    [data-testid="stChatMessage"]{
        border: 1px solid var(--jl-border) !important;
        border-radius: 16px !important;
        padding: 1.5rem 1.75rem !important;
        box-shadow: var(--jl-shadow-sm) !important;
        background: var(--jl-card) !important;
        margin-bottom: 1.2rem !important;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {
        font-size: 1.15rem !important;
        line-height: 1.7 !important;
    }
    [data-testid="stChatMessage"] a{
        color: #8B949E !important;
        text-decoration: none !important;
        font-size: 0.9em !important;
    }
    [data-testid="stChatInput"]{ 
        max-width: 920px;
        margin-left: auto;
        margin-right: auto;
    }
    [data-testid="stChatInput"] textarea{
        border-radius: 14px !important;
        border: 1px solid var(--jl-border) !important;
        box-shadow: var(--jl-shadow-sm) !important;
        font-size: 1.1rem !important;
        padding: 0.85rem 1rem !important;
        background-color: var(--jl-card) !important;
    }

    /* Border containers as white cards (Admin) */
    div[data-testid="stVerticalBlockBorderWrapper"]{
        background: var(--jl-card) !important;
        border: 1px solid var(--jl-border) !important;
        border-radius: var(--jl-radius) !important;
        box-shadow: var(--jl-shadow-sm) !important;
    }

    .jl-badge{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid var(--jl-border);
        background: #30363D;
    }
    .jl-badge-active{
        border-color: rgba(34, 197, 94, 0.35);
        background: rgba(34, 197, 94, 0.10);
        color: #3FB950 !important;
    }
    .jl-badge-banned{
        border-color: rgba(239, 68, 68, 0.35);
        background: rgba(239, 68, 68, 0.10);
        color: #F85149 !important;
    }

    .jl-mobile-only{ display: none; }
    @media (max-width: 700px){
        .jl-mobile-only{ display: block; }
    }

    @media (max-width: 700px){
        .jl-hero .title{ font-size: 1.65rem; }
        .main .block-container{ padding-left: 0.9rem !important; padding-right: 0.9rem !important; }
        [data-testid="stChatMessage"]{
            padding: 1rem 1.1rem !important;
            border-radius: 14px !important;
        }
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] span,
        [data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {
            font-size: 0.98rem !important;
            line-height: 1.55 !important;
        }
        [data-testid="stChatMessage"] a{
            font-size: 0.85em !important;
        }
        [data-testid="stChatInput"] textarea{
            font-size: 0.98rem !important;
            padding: 0.7rem 0.85rem !important;
        }
        .jl-report-header{
            flex-direction: column;
            align-items: flex-start;
        }
    }

    .jl-chat-actions{
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        margin-top: 0.35rem;
    }
    .jl-report{
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
        padding: 1.1rem 1.1rem 1.2rem;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.96), rgba(13, 17, 23, 0.92));
        border: 1px solid rgba(88, 166, 255, 0.2);
        box-shadow: var(--jl-shadow);
        overflow: hidden;
    }
    .jl-report::before{
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 6px;
        background: linear-gradient(180deg, #58A6FF, #34D399);
        opacity: 0.95;
    }
    .jl-report-header{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.8rem;
    }
    .jl-report-title{
        font-size: 1.05rem;
        font-weight: 800;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin: 0;
    }
    .jl-report-chips{
        display: flex;
        gap: 0.4rem;
        flex-wrap: wrap;
    }
    .jl-chip{
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
        color: var(--jl-text) !important;
        background: rgba(88, 166, 255, 0.16);
        border: 1px solid rgba(88, 166, 255, 0.35);
    }
    .jl-report-block{
        display: grid;
        gap: 0.4rem;
        padding: 0.7rem 0.85rem;
        border-radius: 12px;
        background: rgba(13, 17, 23, 0.6);
        border: 1px solid var(--jl-border);
    }
    .jl-report-badge{
        font-weight: 800;
        font-size: 0.7rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: var(--jl-muted) !important;
    }
    .jl-report-body{
        font-size: 1.02rem;
        line-height: 1.6;
    }
    .jl-report-section{
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: #7DD3FC !important;
        margin: 0.4rem 0 0.1rem;
    }
    .jl-report-list{
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 0.6rem;
    }
    .jl-report-step{
        display: grid;
        grid-template-columns: 32px 1fr;
        gap: 0.7rem;
        padding: 0.6rem 0.75rem;
        border-radius: 12px;
        background: rgba(88, 166, 255, 0.08);
        border: 1px dashed rgba(88, 166, 255, 0.45);
    }
    .jl-report-step-num{
        width: 26px;
        height: 26px;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.8rem;
        color: #0D1117 !important;
        background: #34D399;
    }
    .jl-copy-btn{
        background: transparent;
        border: 1px solid var(--jl-border);
        color: var(--jl-muted);
        border-radius: 8px;
        padding: 0.15rem 0.45rem;
        font-size: 0.9rem;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    .jl-copy-btn:active{
        transform: translateY(1px);
    }
    .jl-translate-link{
        color: var(--jl-muted) !important;
        text-decoration: none !important;
        font-size: 0.9em;
    }

    .jl-mobile-toggle{
        display: none;
        position: fixed;
        top: 0.9rem;
        left: 0.9rem;
        z-index: 10005;
        width: 42px;
        height: 42px;
        border-radius: 10px;
        border: 1px solid var(--jl-border);
        background: var(--jl-card);
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: var(--jl-shadow-sm);
        pointer-events: auto;
        touch-action: manipulation;
    }
    .jl-mobile-toggle span{
        display: block;
        width: 18px;
        height: 2px;
        background: var(--jl-text);
        margin: 3px 0;
        border-radius: 2px;
    }
    .jl-drawer-backdrop{
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 10000;
    }
    @media (max-width: 700px){
        :root{
            --jl-drawer-width: min(320px, 88vw);
        }
        .jl-mobile-toggle{ display: inline-flex; }
        .jl-drawer-backdrop{
            display: block;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
        }
        body.jl-drawer-open .jl-drawer-backdrop,
        html.jl-drawer-open .jl-drawer-backdrop{ opacity: 1; pointer-events: auto; }
        body.jl-drawer-open,
        html.jl-drawer-open{
            --sidebar-width: var(--jl-drawer-width);
        }
        section[data-testid="stSidebar"]{
            display: block !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            width: var(--jl-drawer-width) !important;
            max-width: 88vw !important;
            background: var(--jl-card) !important;
            box-shadow: var(--jl-shadow) !important;
            transform: translateX(-110%);
            transition: transform 0.22s ease;
            z-index: 10002;
            overflow-y: auto;
            border-right: none !important;
        }
        body.jl-drawer-open section[data-testid="stSidebar"],
        html.jl-drawer-open section[data-testid="stSidebar"]{ transform: translateX(0); }
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{
            width: 100% !important;
            min-width: 100% !important;
        }
    }
    @media (min-width: 701px){
        body{
            --jl-desktop-sidebar: 20rem;
            --sidebar-width: var(--jl-desktop-sidebar);
        }
        section[data-testid="stSidebar"]{
            display: block !important;
            position: sticky !important;
            top: 0 !important;
            height: 100vh !important;
            width: var(--jl-desktop-sidebar) !important;
            min-width: var(--jl-desktop-sidebar) !important;
            max-width: var(--jl-desktop-sidebar) !important;
            transform: none !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"]{
            width: var(--jl-desktop-sidebar) !important;
            min-width: var(--jl-desktop-sidebar) !important;
            max-width: var(--jl-desktop-sidebar) !important;
            transform: none !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <script>
    (function() {
      if (window.__jlCopyInit) return;
      window.__jlCopyInit = true;
      const copyText = (text) => {
        if (!text) return;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).catch(() => {});
        }
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); } catch (e) {}
        document.body.removeChild(ta);
      };
      document.addEventListener("click", function(e){
        const btn = e.target.closest(".jl-copy-btn");
        if (!btn) return;
        const b64 = btn.getAttribute("data-copy-b64");
        if (!b64) return;
        try{
          const text = decodeURIComponent(escape(atob(b64)));
          copyText(text);
          const old = btn.textContent;
          btn.textContent = "Copied";
          setTimeout(() => { btn.textContent = old; }, 1200);
        }catch(err){}
      });
      document.addEventListener("touchstart", function(e){
        const btn = e.target.closest(".jl-copy-btn");
        if (!btn) return;
        const b64 = btn.getAttribute("data-copy-b64");
        if (!b64) return;
        try{
          const text = decodeURIComponent(escape(atob(b64)));
          copyText(text);
          const old = btn.textContent;
          btn.textContent = "Copied";
          setTimeout(() => { btn.textContent = old; }, 1200);
        }catch(err){}
      }, {passive: true});
    })();
    </script>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="jl-mobile-toggle" data-jl-drawer-toggle aria-label="Open menu">
      <div>
        <span></span><span></span><span></span>
      </div>
    </div>
    <div class="jl-drawer-backdrop" data-jl-drawer-backdrop></div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#0D1117">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    """,
    unsafe_allow_html=True,
)
components.html(
    """
    <script>
    (function(){
      if (window.__jlDrawerInit) return;
      window.__jlDrawerInit = true;
      const doc = window.parent && window.parent.document ? window.parent.document : document;
      const body = doc.body;
      const root = doc.documentElement || doc;
      const OPEN_CLASS = "jl-drawer-open";
      const openDrawer = () => {
        body && body.classList.add(OPEN_CLASS);
        root && root.classList.add(OPEN_CLASS);
      };
      const closeDrawer = () => {
        body && body.classList.remove(OPEN_CLASS);
        root && root.classList.remove(OPEN_CLASS);
      };
      const isMobile = () => doc.defaultView && doc.defaultView.matchMedia("(max-width: 700px)").matches;
      const ensureDesktopSidebar = () => {
        if (isMobile()) return;
        const openBtn = doc.querySelector(
          'button[aria-label="Open sidebar"], button[title="Open sidebar"], button[title="Show sidebar"]'
        );
        if (openBtn) openBtn.click();
      };
      ensureDesktopSidebar();
      const bindToggleHandlers = () => {
        const toggle = doc.querySelector("[data-jl-drawer-toggle]");
        const backdrop = doc.querySelector("[data-jl-drawer-backdrop]");
        if (toggle && !toggle.__jlBound){
          const open = (e) => { e.preventDefault(); openDrawer(); };
          toggle.addEventListener("click", open, true);
          toggle.addEventListener("touchstart", open, {passive: false, capture: true});
          toggle.__jlBound = true;
        }
        if (backdrop && !backdrop.__jlBound){
          const close = (e) => { e.preventDefault(); closeDrawer(); };
          backdrop.addEventListener("click", close, true);
          backdrop.addEventListener("touchstart", close, {passive: false, capture: true});
          backdrop.__jlBound = true;
        }
      };
      bindToggleHandlers();
      const bindTimer = setInterval(() => {
        bindToggleHandlers();
        if (doc.querySelector("[data-jl-drawer-toggle]")) clearInterval(bindTimer);
      }, 600);
      doc.defaultView && doc.defaultView.addEventListener("resize", () => {
        if (!isMobile()) {
          closeDrawer();
          ensureDesktopSidebar();
        }
      });
      const handler = function(e){
        const toggle = e.target.closest("[data-jl-drawer-toggle]");
        const backdrop = e.target.closest("[data-jl-drawer-backdrop]");
        const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
        const insideSidebar = sidebar && sidebar.contains(e.target);
        const clickedButton = e.target.closest("button");
        const clickedOption = e.target.closest("input, select, textarea, label, [role='option'], [role='radio'], [role='checkbox']");
        if (toggle){
          e.preventDefault();
          openDrawer();
          return;
        }
        if (backdrop){
          e.preventDefault();
          closeDrawer();
          return;
        }
        if (body.classList.contains(OPEN_CLASS) && insideSidebar && isMobile() && (clickedButton || clickedOption)){
          setTimeout(() => closeDrawer(), 60);
          return;
        }
        if (body.classList.contains(OPEN_CLASS) && !insideSidebar){
          closeDrawer();
        }
      };
      doc.addEventListener("click", handler, true);
      doc.addEventListener("touchstart", handler, {passive: true, capture: true});
    })();
    </script>
    """,
    height=0,
    width=0,
)
components.html(
    """
    <script>
    (function(){
      if (window.__jlPwaInit) return;
      window.__jlPwaInit = true;
      const win = window.parent || window;
      if ("serviceWorker" in win.navigator){
        win.navigator.serviceWorker.register("/static/service-worker.js").catch(() => {});
      }
      win.addEventListener("beforeinstallprompt", (e) => {
        e.preventDefault();
        win.__jlInstallPrompt = e;
      });
    })();
    </script>
    """,
    height=0,
    width=0,
)

if "view" not in st.session_state:
    st.session_state.view = "AI Assistant"
if "cooldown_until" not in st.session_state:
    st.session_state.cooldown_until = 0.0

 

# --- BOOTSTRAP / INITIALIZATION ---
@st.cache_resource(show_spinner=False)
def init_backend():
    try:
        splash = st.empty()
        with splash.container():
            st.markdown(f"""
                <div style="text-align:center; padding:80px 20px; background:var(--jl-card); border-radius:1rem; border:1px solid var(--jl-border); margin: 50px auto; max-width: 600px; box-shadow: var(--jl-shadow);">
                    <h2 style="color:var(--jl-text); margin-bottom:10px; font-weight:900;">JUSTICE LENS</h2>
                    <p style="color:var(--jl-muted); font-weight: 700; margin-bottom: 25px; font-size: 0.95rem; letter-spacing: 0.5px;">Establishing secure connection…</p>
                </div>
            """, unsafe_allow_html=True)
            
            bar = st.progress(0, text="Verifying Database...")
            pc = Pinecone(api_key=PINECONE_KEY)
            idx = pc.Index(INDEX_NAME)
            
            bar.progress(50, text="Synchronizing AI Engine...")
            embed_model = HuggingFaceEmbeddings(model_name="nlpaueb/legal-bert-base-uncased")
            
            bar.progress(100, text="AI Online.")
            
        splash.empty()
        return idx, embed_model
    except Exception as e:
        st.error(f"Critical Offline: {e}")
        return None, None

def init_firebase():
    if not firebase_admin._apps:
        try:
            fb_data = dict(st.secrets["firebase"])
            cred = credentials.Certificate(fb_data)
            bucket = (
                fb_data.get("storage_bucket")
                or st.secrets.get("FIREBASE_STORAGE_BUCKET", "")
                or os.environ.get("FIREBASE_STORAGE_BUCKET", "")
            )
            init_args = {'projectId': fb_data.get('project_id')}
            if bucket:
                init_args["storageBucket"] = bucket
            firebase_admin.initialize_app(cred, init_args)
        except Exception as e:
            st.sidebar.error(f"Database Error: {e}")
    return firestore.client() if firebase_admin._apps else None

db = init_firebase()
pinecone_index, legal_embeddings = None, None

def get_backend():
    global pinecone_index, legal_embeddings
    if pinecone_index is None or legal_embeddings is None:
        pinecone_index, legal_embeddings = init_backend()
    return pinecone_index, legal_embeddings

# --- SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "admin_mode" not in st.session_state: st.session_state.admin_mode = False
if "view" not in st.session_state: st.session_state.view = "AI Assistant"
if "projects" not in st.session_state or not isinstance(st.session_state.get("projects"), dict):
    st.session_state.projects = {"Default": list(st.session_state.chat_history)}
if "active_project" not in st.session_state:
    st.session_state.active_project = "Default"
if "mobile_login_open" not in st.session_state:
    st.session_state.mobile_login_open = False

def _session_store_ref():
    if not db:
        return None
    return (
        db.collection("artifacts")
        .document("justicelens-law")
        .collection("public")
        .document("data")
        .collection("sessions")
    )

def _chat_store_ref():
    if not db:
        return None
    return (
        db.collection("artifacts")
        .document("justicelens-law")
        .collection("public")
        .document("data")
        .collection("chats")
    )

def _get_sid():
    try:
        return st.query_params.get("sid")
    except Exception:
        return None

def _set_sid(sid: str):
    try:
        st.query_params["sid"] = sid
    except Exception:
        pass

def _clear_sid():
    try:
        st.query_params.clear()
    except Exception:
        pass

def _restore_session_from_sid():
    if st.session_state.user or not db:
        return
    sid = _get_sid()
    if not sid:
        return
    try:
        ref = _session_store_ref()
        doc = ref.document(sid).get() if ref else None
        if doc and doc.exists:
            data = doc.to_dict() or {}
            if data.get("uid") and data.get("email"):
                st.session_state.user = {
                    "uid": data.get("uid"),
                    "email": data.get("email"),
                    "name": data.get("name") or data.get("email", "").split("@")[0],
                }
                st.session_state.view = st.session_state.view or "AI Assistant"
    except Exception:
        pass

if "projects" not in st.session_state:
    st.session_state.projects = {"Default": st.session_state.get("chat_history", [])}
if "active_project" not in st.session_state:
    st.session_state.active_project = "Default"
if "jl_chats_loaded" not in st.session_state:
    st.session_state.jl_chats_loaded = False

def _load_chats_for_user(uid: str):
    if not db or not uid:
        return
    ref = _chat_store_ref()
    if not ref:
        return
    try:
        docs = ref.document(uid).collection("projects").stream()
        loaded = {}
        for doc in docs:
            data = doc.to_dict() or {}
            msgs = data.get("messages") or []
            if isinstance(msgs, list):
                loaded[doc.id] = msgs
        if loaded:
            st.session_state.projects = loaded
            if st.session_state.active_project not in st.session_state.projects:
                st.session_state.active_project = next(iter(loaded.keys()))
    except Exception:
        pass

def _persist_chat_for_user(uid: str, project: str, history: list):
    if not db or not uid or not project:
        return
    ref = _chat_store_ref()
    if not ref:
        return
    try:
        # Keep a reasonable cap to avoid oversized documents.
        trimmed = list(history)[-50:]
        ref.document(uid).collection("projects").document(project).set({
            "messages": trimmed,
            "updated_at": utc_now(),
        }, merge=True)
    except Exception:
        pass

def _delete_chat_for_user(uid: str, project: str):
    if not db or not uid or not project:
        return
    ref = _chat_store_ref()
    if not ref:
        return
    try:
        ref.document(uid).collection("projects").document(project).delete()
    except Exception:
        pass

def _ensure_chats_loaded():
    if st.session_state.jl_chats_loaded:
        return
    user = st.session_state.get("user") or {}
    uid = user.get("uid")
    if uid:
        _load_chats_for_user(uid)
        st.session_state.jl_chats_loaded = True

_restore_session_from_sid()
_ensure_chats_loaded()

# --- AUTH SYSTEM ---
def authenticate(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.ok:
            data = r.json()
            user_obj = auth.get_user(data['localId'])
            return True, user_obj
        return False, None
    except: return False, None

def sync_user(user_data):
    if db:
        try:
            user_ref = db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("users").document(user_data['uid'])
            user_ref.set({
                **user_data,
                "last_active": utc_now(),
                "is_banned": user_data.get('is_banned', False)
            }, merge=True)
        except: pass

def check_ban(uid):
    if not db: return False
    doc = db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("users").document(uid).get()
    return doc.to_dict().get("is_banned", False) if doc.exists else False

# --- AI LOGIC ---
def _justice_lens_legal_anchor() -> str:
    return """
    STATUTORY REFERENCE:
    - Section 65: Tampering with Computer Source Documents
    - Section 66: Computer Related Offences
    - Section 66B: Receiving Stolen Computer Resource/Device
    - Section 66C: Identity Theft
    - Section 66D: Cheating by Personation (Online Fraud)
    - Section 66E: Violation of Privacy (Private Images)
    - Section 66F: Cyber Terrorism (Critical/National Infrastructure only)
    - Section 67/67A/67B: Obscenity, Sexually Explicit, Child Sexual Material
    - Section 72/72A: Breach of Confidentiality/Unlawful Disclosure
    - Section 43/43A: Civil Compensation for Damage/Data Negligence
    """

def _justice_lens_case_history() -> str:
    return """
    LANDMARK PRECEDENTS:
    - State of Tamil Nadu vs. Suhas Katti (2004)
    - Shreya Singhal vs. Union of India (2015)
    - Anvar P.V. vs. P.K. Basheer (2014)
    - Justice K.S. Puttaswamy vs. Union of India (2017)
    """


def _contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    h = str(haystack or "").lower()
    return any(n.lower() in h for n in needles)

## Section 66 enforcement removed to keep responses aligned with backend prompt logic.

def _is_cyber_relevant(user_input: str) -> bool:
    if not user_input:
        return False
    text = str(user_input).lower()
    if re.search(r"\b(section|sec|s\.)\s*\d+\b", text):
        return True
    if _contains_any(text, ("it act", "information technology act", "cyber", "cybercrime", "cyber crime")):
        return True
    return _contains_any(text, (
        "hacking", "hack", "unauthorized access", "unauthorised access",
        "phishing", "otp", "upi", "bank fraud", "digital fraud",
        "identity theft", "impersonation", "deepfake", "morphed",
        "data breach", "privacy violation", "doxing",
        "malware", "ransomware", "spyware",
        "account hacked", "login hacked", "credential", "credential theft",
        "social media", "whatsapp scam", "sms scam", "email scam",
        "cyber stalking", "obscenity", "revenge porn",
    ))

def _is_phishing_portal_or_deepfake(user_input: str) -> bool:
    return _contains_any(user_input, (
        "phishing", "phish", "fake login", "spoof", "credential harvest", "otp page", "login page", "portal", "malicious link",
        "deepfake", "synthetic", "ai-generated", "ai generated", "morphed", "voice clone", "face swap", "impersonation video",
        "sgi", "synthetically generated",
    ))

def _is_ncii_or_intimate_imagery(user_input: str) -> bool:
    return _contains_any(user_input, (
        "revenge porn", "intimate images", "private photos", "private videos", "leaked nudes",
        "non-consensual", "without consent", "morphed", "deepfake nude", "deepfake porn",
        "obscene video", "sexual video", "sexually explicit",
    ))

def _is_data_breach(user_input: str) -> bool:
    return _contains_any(user_input, (
        "data breach", "breach", "leak", "leaked database", "exposed data",
        "ransomware", "stolen data", "database dump", "credential dump",
    ))

def _is_national_or_govt_infra(user_input: str) -> bool:
    return _contains_any(user_input, (
        "critical infrastructure", "protected system", "national security", "defence", "defense",
        "government", "govt", "ministry", "army", "air force", "navy", "intelligence",
        "power grid", "nuclear", "railway", "telecom backbone", "space", "satellite", "isro",
    ))

def _is_loan_identity_theft(user_input: str) -> bool:
    return _contains_any(user_input, (
        "loan", "emi", "nbfc", "lender", "personal loan", "credit card", "cibil", "experian", "credit score",
        "account opened", "opened a loan", "taken in my name", "taken on my name", "identity theft loan",
    ))

def _justice_lens_dynamic_scenario_rules(user_input: str) -> str:
    rules = []

    if _is_phishing_portal_or_deepfake(user_input):
        rules.append("""
        - Intermediary compliance (IT Rules 2021 as amended in 2026): If the user mentions an active phishing portal or deepfake/synthetic content, state that "synthetically generated information" (SGI) is covered under the 2026 amendment.
          Advise issuing a takedown/abuse report to the platform and, where required, seeking a court/government order; intermediaries must act on lawful orders within 3 hours to retain Section 79 safe-harbor.
          Include a concrete takedown step in ACTION PLAN.
        """)

    if _is_ncii_or_intimate_imagery(user_input):
        rules.append("""
        - Intimate imagery takedown (IT Rules 2021 as amended 2026): For non-consensual intimate content, the platform must remove/disable access within 2 hours of a valid complaint under Rule 3(2)(b). Do NOT use 36 hours for NCII. Include an immediate takedown step.
        """)

    if _is_data_breach(user_input):
        rules.append("""
        - DPDP breach notification (DPDP Rules 2025): On becoming aware of a personal data breach, notify affected Data Principals without delay and report to the Data Protection Board. A detailed follow-up report is due within 72 hours (Rule 7).
        """)

    if _is_loan_identity_theft(user_input):
        rules.append("""
        - Loan identity-theft recovery (CIBIL/RBI): If a loan/credit product is taken in the victim's name, ACTION PLAN MUST include:
          (a) Raise a dispute on the CIBIL/Experian portal (resolution required within 30 days).
          (b) If the lender does not resolve the identity theft claim within 30 days, escalate to the RBI Ombudsman via the CMS Portal (cms.rbi.org.in).
          WIN PROBABILITY MUST be calibrated to 40–60% and must acknowledge that reversing a financial loan has a heavy burden of proof (Police FIR + forensic audit/lender investigation) to establish non-authorization.
        """)

    return "\n".join(rules).strip()

def _justice_lens_2026_scenario_logic() -> str:
    return """
    JUSTICE LENS — CYBER LAW UPDATES (APPLY TO ALL SCENARIO RESPONSES):
    - Jurisdiction: Focus strictly on Indian cyber law (IT Act 2000 + IT Rules). If clearly outside scope, respond with OUT OF SCOPE.
    - Phishing/identity theft/personation: Lead with IT Act Sections 66C (Identity Theft) and 66D (Cheating by Personation). Treat Section 43/43A as secondary civil-compensation remedies.
    - CERT-In Directions (28 Apr 2022): If the victim is an organisation/service provider or the incident affects enterprise systems, include reporting to CERT-In within 6 hours of noticing/being notified (for reportable incidents).
    - Golden Hour: In ACTION PLAN, emphasize immediate reporting via 1930/cybercrime.gov.in to maximize lien/freeze chances (avoid promising refunds).
    - Liability nuance: Do NOT claim “0% liability” as a blanket rule. Clarify victim must report promptly and secure the breach (passwords/2FA/session revokes).
    - Evidence strategy (primary): Preserve Email Headers, UPI Transaction IDs, URL Metadata, and device logs; reference Section 65B (Indian Evidence Act) for admissibility of electronic records.
    """

def _ensure_intermediary_takedown_mention(answer: str) -> str:
    if not answer:
        return answer

    already_mentions = (
        _contains_any(answer, ("it rules 2021", "intermediary", "intermediaries", "it amendment rules 2026")) and
        _contains_any(answer, ("section 79", "safe harbor", "safe harbour"))
    )
    if already_mentions:
        return answer

    insertion = (
        '4. (Intermediary takedown) For an active phishing portal/deepfake: cite the IT Rules 2021 as amended in 2026—'
        'synthetically generated information is covered; file a takedown/abuse report with the host/platform and, where required, seek a court/government order. '
        'Intermediaries must act within the amended timelines (3 hours for lawful takedown orders; 2 hours for NCII complaints) to retain Section 79 safe-harbor.'
    )

    if "ACTION PLAN:" in answer:
        # Append as an extra step to preserve the required format.
        return answer.rstrip() + "\n" + insertion

    return answer.rstrip() + "\n\n" + insertion

def _enforce_loan_dispute_requirements(answer: str) -> str:
    if not answer:
        return answer

    updated = answer

    updated = re.sub(
        r"(?im)^WIN PROBABILITY:\s*.*$",
        "WIN PROBABILITY: 40–60% - Criminal sections (66C/66D) are usually clear on paper, but reversing/cancelling a loan requires strong proof of non-authorization (Police FIR + lender investigation/forensic audit) to satisfy the lender and credit bureaus.",
        updated,
        count=1,
    )

    loan_steps = []
    if not (_contains_any(updated, ("cibil", "experian")) and _contains_any(updated, ("30 day", "30-day", "30 days"))):
        loan_steps.append("Raise a dispute on the CIBIL/Experian portal (resolution required within 30 days).")
    if not (_contains_any(updated, ("cms.rbi.org.in", "rbi ombudsman", "cms portal")) and _contains_any(updated, ("30 day", "30-day", "30 days"))):
        loan_steps.append("If the lender does not resolve the identity theft claim within 30 days, escalate to the RBI Ombudsman via the CMS Portal (cms.rbi.org.in).")

    if not loan_steps:
        return updated

    if "ACTION PLAN:" in updated:
        # Add as additional numbered steps without renumbering existing items.
        suffix_lines = []
        start_n = 4
        for i, s in enumerate(loan_steps):
            suffix_lines.append(f"{start_n + i}. (Loan dispute) {s}")
        return updated.rstrip() + "\n" + "\n".join(suffix_lines)

    return updated.rstrip() + "\n\n" + "\n".join(f"- {s}" for s in loan_steps)

def _apply_high_priority_refinements(user_input: str, category: str, answer: str) -> str:
    if not answer or "EXPLAIN" in str(category).upper():
        return answer

    updated = answer

    # Guardrail: Shreya Singhal (2015) is not a negligence/hacking precedent.
    updated = re.sub(
        r"(?im)^(.*\bDATA\s+NEGLIGENCE\s*:\s*)Shreya\s+Singhal\s+vs\.\s+Union\s+of\s+India\s*\(2015\)\.?\s*$",
        r"\1Justice K.S. Puttaswamy (Retd.) vs. Union of India (2017).",
        updated,
    )

    if _is_loan_identity_theft(user_input):
        updated = _enforce_loan_dispute_requirements(updated)

    if _is_phishing_portal_or_deepfake(user_input):
        updated = _ensure_intermediary_takedown_mention(updated)

    # Guardrail: Section 66F only for national/govt infrastructure.
    if not _is_national_or_govt_infra(user_input):
        updated = re.sub(r"(?i)\bsection\s*66f\b", "", updated)
        updated = re.sub(r"(?i)\b66f\b", "", updated)
        updated = re.sub(r"[;,]\s*[;,]", "; ", updated)
        updated = re.sub(r"\s{2,}", " ", updated)
        updated = re.sub(r"(?im)^\s*LEGAL PROVISIONS:\s*;?\s*", "LEGAL PROVISIONS: ", updated)

    return updated

def get_intent_category(user_input):
    """
    STRICT GATEKEEPER:
    Prevents physical crimes (murder, theft) from being processed.
    """
    # Deterministic local gate: block obvious physical/off-topic crimes before LLM call.
    if not _is_cyber_relevant(user_input):
        return "INVALID"
    if _contains_any(user_input, (
        "murder", "killed", "kill", "homicide", "manslaughter",
        "assault", "battery", "stabbing", "shooting",
        "rape", "sexual assault",
        "robbery", "burglary", "theft", "physical theft",
        "acid attack", "sulphuric", "sulfuric",
    )):
        return "INVALID"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    classifier_prompt = f"""
    Analyze user input: "{user_input}"
    CRITICAL RULE:
    If the query is about PHYSICAL CRIMES (Murder, Physical Theft, Assault, Physical Robbery)
    or non-legal topics (Math, Greetings), you MUST return 'INVALID'.
    Categories:
    1. CYBER_SCENARIO: Digital crimes only (Hacking, Phishing, Identity Theft).
    2. CYBER_EXPLAIN: IT Act 2000 section requests.
    3. INVALID: All other topics.
    Respond with ONLY the category name.
    """
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": classifier_prompt}],
        "temperature": 0.0,
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content'].strip().upper()
    except Exception:
        return "INVALID"

def ask_groq_lawyer(user_input, law_evidence, category):
    """Generates professional, non-repetitive legal reports."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    # SYSTEM PROMPT WITH 8 DYNAMIC PATHS
    system_prompt = """
Role: Professional Legal Validator (Indian IT Act 2000).

CASE SELECTION RULES (Choose ONLY ONE per report):
1. Financial/UPI/Bank Fraud -> Dhule Vikas Bank vs. Axis Bank (2025)
2. Identity Theft/Impersonation -> CBI vs. Arif Azim (Sony Sambandh Case)
3. Deepfakes/AI Harassment -> Delhi HC Deepfake Injunction (2025)
4. Hacking/Login Theft -> State vs. N.G. Arun Kumar (2011)
5. Privacy/Fundamental Rights -> Justice K.S. Puttaswamy vs. Union of India
6. Social Media/Intermediary -> Shreya Singhal vs. Union of India
7. Electronic Evidence/Logs -> Anvar P.V. vs. P.K. Basheer (2014)
8. Cyber Stalking/Obscenity -> State of Tamil Nadu vs. Suhas Katti

CRITICAL CONSTRAINTS:
- NEVER cite Section 66F (Terrorism) or Section 70 (Critical Systems) unless it involves National/Govt infrastructure.
- Provide ONLY the single most relevant case. Do NOT list others or explain why they were not chosen.
- Style: Professional technical plain text. No stars (*) or emojis.

REPORT FORMAT:
1. LEGAL PROVISIONS: [List specific IT Act sections]
2. STATUTORY PENALTIES: [List Jail/Fines]
3. JUDICIAL PRECEDENT: [The single matching case name and one sentence on its significance]
4. WIN PROBABILITY: [95% if logs exist, 40% if anonymous]
5. MANDATORY ACTION: [Must include 6-hour CERT-In rule]
"""

    full_prompt = f"{system_prompt}\nUser Input: {user_input}\nContext: {law_evidence}"
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.0,
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception:
        return "Error processing legal advisory."

def _format_report_body(body: str) -> str:
    cleaned = (body or "").strip()
    if not cleaned:
        return "JUSTICE LENS ADVISORY REPORT"
    cleaned = _normalize_report_spacing(cleaned)
    return "JUSTICE LENS ADVISORY REPORT\n" + cleaned

def _looks_like_report(text: str) -> bool:
    if not text:
        return False
    upper = text.upper()
    return (
        "JUSTICE LENS ADVISORY REPORT" in upper
        or "SECTION TITLE" in upper
        or "LEGAL DEFINITION" in upper
        or "STATUTORY PUNISHMENT" in upper
        or "RELEVANT SECTIONS" in upper
        or "LEGAL PROVISIONS" in upper
        or "STATUTORY PENALTIES" in upper
        or "JUDICIAL PRECEDENT" in upper
        or "MANDATORY ACTION" in upper
        or "ACTION PLAN" in upper
    )

def _render_report_html(text: str) -> str:
    cleaned = _normalize_report_spacing(text or "")
    lines = [ln for ln in cleaned.splitlines() if ln.strip()]
    title = ""
    rows = []
    action_steps = []
    in_action = False

    for line in lines:
        raw = line.strip()
        if raw.upper().startswith("JUSTICE LENS ADVISORY REPORT"):
            title = raw
            continue

        if raw.upper().startswith("ACTION PLAN"):
            in_action = True
            rows.append(("section", "ACTION PLAN", ""))
            continue

        if in_action:
            step_match = re.match(r"^(\d+)\.\s*(.+)$", raw)
            if step_match:
                action_steps.append(step_match.group(2).strip())
                continue
            in_action = False

        kv_numbered = re.match(r"^\d+\.\s*([A-Z][A-Z\s/&-]+)(?:\s*[:\-])?\s+(.*)$", raw)
        if kv_numbered:
            label = kv_numbered.group(1).strip()
            body = kv_numbered.group(2).strip()
            if body and body.isupper() and len(body.split()) <= 3 and not re.search(r"\d", body):
                rows.append(("section", f"{label} {body}".strip(), ""))
            else:
                rows.append(("kv", label, body))
            continue

        kv_plain = re.match(r"^([A-Z][A-Z\s/&-]+):\s*(.*)$", raw)
        if kv_plain:
            label = kv_plain.group(1).strip()
            body = kv_plain.group(2).strip()
            if body and body.isupper() and len(body.split()) <= 3 and not re.search(r"\d", body):
                rows.append(("section", f"{label} {body}".strip(), ""))
            else:
                rows.append(("kv", label, body))
            continue

        rows.append(("p", "", raw))

    html_parts = ["<div class='jl-report'>"]
    if title:
        html_parts.append("<div class='jl-report-header'>")
        html_parts.append(f"<div class='jl-report-title'>{html.escape(title)}</div>")
        html_parts.append("<div class='jl-report-chips'></div>")
        html_parts.append("</div>")
    for kind, label, body in rows:
        if kind == "section":
            html_parts.append(f"<div class='jl-report-section'>{html.escape(label)}</div>")
            continue
        if kind == "kv":
            html_parts.append(
                "<div class='jl-report-block'>"
                f"<div class='jl-report-badge'>{html.escape(label)}</div>"
                f"<div class='jl-report-body'>{html.escape(body)}</div>"
                "</div>"
            )
            continue
        html_parts.append(f"<div class='jl-report-body'>{html.escape(body)}</div>")

    if action_steps:
        html_parts.append("<ol class='jl-report-list'>")
        for idx, step in enumerate(action_steps, start=1):
            html_parts.append(
                "<li class='jl-report-step'>"
                f"<span class='jl-report-step-num'>{idx}</span>"
                f"<span class='jl-report-body'>{html.escape(step)}</span>"
                "</li>"
            )
        html_parts.append("</ol>")

    html_parts.append("</div>")
    return "".join(html_parts)

def _normalize_report_spacing(text: str) -> str:
    if not text:
        return text
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        line = re.sub(r"^\s*[-*•]\s+", "", line)
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(LEGAL ANALYSIS|STATUTORY PENALTIES|JUDICIAL PRECEDENT|PROBABILITY OF SUCCESS|REMEDIAL ACTION PLAN)\n+", r"\1\n", text)
    text = re.sub(r"\n+(\d+\.\s)", r"\n\1", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()

def _strip_unwanted_headings(text: str) -> str:
    if not text:
        return text
    remove_set = {
        "REPORT FORMAT",
        "CASE DETAILS",
        "REPORT",
        "IT ACT 2000",
        "EVIDENCE-ONLY",
        "EVIDENCE ONLY",
        "IT ACT 2000 EVIDENCE-ONLY",
        "IT ACT 2000 EVIDENCE ONLY",
    }
    cleaned = []
    for raw in text.splitlines():
        stripped = raw.strip()
        upper = stripped.upper()
        if upper in remove_set:
            continue
        if cleaned and cleaned[-1].strip() == stripped:
            continue
        cleaned.append(raw)
    return "\n".join(cleaned).strip()

def _collapse_act_headings(text: str) -> str:
    if not text:
        return text
    headings = {
        "LEGAL PROVISIONS:",
        "STATUTORY PENALTIES:",
        "JUDICIAL PRECEDENT:",
        "WIN PROBABILITY:",
        "MANDATORY ACTION:",
    }
    act_line = re.compile(
        r"^(IT\s+ACT|DPDP\s+ACT|IT\s+RULES|BNS|BNSS|CRPC|IPC|EVIDENCE\s+ACT|ACT\s*\d{4}|RULES\s*\d{4}).*$",
        re.IGNORECASE,
    )
    tag_line = re.compile(r"^[A-Z]{2,}$")
    label_act_line = re.compile(r"^(IT|DPDP|IT\s+RULES)\s*:\s*.*$", re.IGNORECASE)
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        upper = stripped.upper()
        if upper in headings:
            out.append(line)
            i += 1
            block = []
            while i < len(lines) and lines[i].strip().upper() not in headings:
                block.append(lines[i])
                i += 1
            has_act = any(act_line.match(b.strip()) for b in block)
            if has_act:
                out.append("ACTS:")
            for b in block:
                if act_line.match(b.strip()) or tag_line.match(b.strip()) or label_act_line.match(b.strip()):
                    continue
                out.append(b)
            continue
        out.append(line)
        i += 1
    return "\n".join(out).strip()

def _out_of_scope_report() -> str:
    return "\n".join([
        "JUSTICE LENS ADVISORY REPORT",
        "-" * 30,
        "OUT OF SCOPE NOTICE",
        "This query pertains to a topic outside the scope of Indian Cyber Law.",
        "Justice Lens provides advisory services exclusively for the IT Act, 2000.",
        "Please provide a digital or cyber-related scenario.",
        "-" * 30,
    ])

def show_sidebar():
    with st.sidebar:
        st.image(LOGO_SOURCE, use_container_width=True)

        if "show_login" not in st.session_state:
            st.session_state.show_login = True
        if "projects" not in st.session_state or not isinstance(st.session_state.get("projects"), dict):
            existing = list(st.session_state.get("chat_history") or [])
            st.session_state.projects = {"Default": existing}
        if "active_project" not in st.session_state:
            st.session_state.active_project = "Default"
        if st.session_state.active_project not in st.session_state.projects:
            st.session_state.projects[st.session_state.active_project] = []
        
        if not st.session_state.user:
            if st.session_state.show_login:
                auth_tab = st.tabs(["Login", "Create Account"])
                with auth_tab[0]:
                    e_val = st.text_input("Email", key="login_email")
                    p_val = st.text_input("Password", type="password", key="login_pass")
                    if st.button(" Authenticate"):
                        valid, u_obj = authenticate(e_val, p_val)
                        if valid:
                            if check_ban(u_obj.uid):
                                st.error("Access Forbidden.")
                            else:
                                st.session_state.user = {
                                    "name": u_obj.display_name or e_val.split('@')[0],
                                    "email": e_val,
                                    "uid": u_obj.uid
                                }
                                st.session_state.jl_chats_loaded = False
                                st.session_state.view = "AI Assistant"
                                if db:
                                    sid = str(uuid.uuid4())
                                    try:
                                        _session_store_ref().document(sid).set({
                                            "uid": u_obj.uid,
                                            "email": e_val,
                                            "name": u_obj.display_name or e_val.split('@')[0],
                                            "created_at": utc_now(),
                                        })
                                        _set_sid(sid)
                                    except Exception:
                                        pass
                                st.session_state.show_login = False  # Hide login form
                                sync_user(st.session_state.user)
                                _ensure_chats_loaded()
                                st.rerun()
                        else:
                            st.error("Invalid Credentials.")

                with auth_tab[1]:
                    nu = st.text_input("Full Name")
                    eu = st.text_input("Email", key="s_email")
                    pu = st.text_input("Create Password", type="password", key="s_pass")
                    if st.button("REGISTER"):
                        try:
                            auth.create_user(email=eu, password=pu, display_name=nu)
                            st.success("Account Ready! Use Login.")
                        except Exception as ex:
                            st.error(str(ex))

            if st.button("Guest User"):
                gid = str(uuid.uuid4())[:8]
                st.session_state.user = {"name": f"Guest_{gid}", "email": "guest@justicelens.io",
                                         "uid": f"guest_{gid}"}
                st.session_state.show_login = False  # Hide login form
                st.session_state.jl_chats_loaded = False
                _ensure_chats_loaded()
                if db:
                    sid = str(uuid.uuid4())
                    try:
                        _session_store_ref().document(sid).set({
                            "uid": st.session_state.user["uid"],
                            "email": st.session_state.user["email"],
                            "name": st.session_state.user["name"],
                            "created_at": utc_now(),
                        })
                        _set_sid(sid)
                    except Exception:
                        pass
                st.rerun()

            st.markdown("---")
            st.caption("Resources")
            public_pages = ["AI Assistant", "About", "Terms"]
            try:
                default_index = public_pages.index(st.session_state.view)
            except ValueError:
                default_index = 0
            public_choice = st.radio(
                "Resources",
                public_pages,
                index=default_index,
                key="jl_public_nav",
                label_visibility="collapsed",
            )
            if public_choice != st.session_state.view:
                st.session_state.view = public_choice
                st.rerun()
        else:
            st.markdown(
                f"<div class='jl-sidebar-connected'>Connected to: <b>{st.session_state.user['name']}</b></div>",
                unsafe_allow_html=True,
            )

            opts = ["AI Assistant", "Vision & Mission", "About", "Terms"]
            if st.session_state.user['email'] == "d3ztudio@gmail.com":
                st.markdown(
                    '<span style="color:var(--jl-primary); font-weight:800; font-size:0.7rem; letter-spacing:0.12em;">SYSTEM COMMANDER</span>',
                    unsafe_allow_html=True)
                if not st.session_state.admin_mode:
                    pin = st.text_input("PIN", type="password", placeholder="Enter PIN")
                    if pin == "1923":
                        st.session_state.admin_mode = True
                        st.rerun()
            if st.session_state.admin_mode:
                opts.append("Admin Dashboard")

            st.session_state.view = st.radio("NAVIGATION", [x.strip() for x in opts])

            if st.session_state.view == "AI Assistant":
                if st.button("Clear chat", use_container_width=True):
                    active = st.session_state.active_project
                    st.session_state.projects[active] = []
                    st.session_state.chat_history = []
                    _delete_chat_for_user(st.session_state.user.get("uid"), active)
                    st.rerun()

                st.markdown("### Chats")
                new_name = st.text_input("New Chats", placeholder="e.g. Incident Notes", key="jl_new_project_sb")
                if st.button("Create", use_container_width=True, key="jl_create_project_sb"):
                    name = (new_name or "").strip()
                    if name and name not in st.session_state.projects:
                        st.session_state.projects[name] = []
                        st.session_state.active_project = name
                        _persist_chat_for_user(st.session_state.user.get("uid"), name, [])
                        st.rerun()

                project_names = list((st.session_state.get("projects") or {}).keys())
                if project_names:
                    try:
                        current_index = project_names.index(st.session_state.active_project)
                    except ValueError:
                        current_index = 0
                    chosen = st.radio(
                        "Select",
                        project_names,
                        index=current_index,
                        label_visibility="collapsed",
                        key="jl_project_radio_sb",
                    )
                    if chosen != st.session_state.active_project:
                        st.session_state.active_project = chosen
                        st.rerun()

                st.caption("Tip: Use Chats to separate different incident chats.")

            st.markdown("---")
            if st.button("TERMINATE SESSION"):
                sid = _get_sid()
                if sid and db:
                    try:
                        _session_store_ref().document(sid).delete()
                    except Exception:
                        pass
                _clear_sid()
                st.session_state.user = None
                st.session_state.admin_mode = False
                st.session_state.chat_history = []
                st.session_state.jl_chats_loaded = False
                st.session_state.show_login = True  # Show login form
                st.rerun()

# --- SIDEBAR UI ---
show_sidebar()

# --- MAIN CONTENT ---
if not st.session_state.user:
    if st.session_state.view in ("Vision & Mission", "About", "Terms"):
        l_pad, main, r_pad = st.columns([1, 8, 1])
        with main:
            with st.container():
                st.markdown(
                    f"""
                    <div class="jl-hero">
                        <div class="title">{st.session_state.view}</div>
                        <div class="subtitle">Justice Lens resources</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.write("")

            if st.session_state.view == "About":
                st.markdown(
                    """
                    <div class="jl-card">
                        <h3 style="margin-top:0;">What is Justice Lens?</h3>
                        <p style="color: var(--jl-muted) !important;">
                            Justice Lens is an advanced cyber-law assistant engineered to provide immediate, structured, and actionable insights into common cyber incidents within the Indian legal framework.
                        </p>
                        <h3 style="margin-top:1.5rem;">How it Works</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                            Our system leverages a powerful AI engine coupled with a curated database of Indian cyber law, including the IT Act of 2000 and subsequent amendments. When you describe a scenario, the AI performs a multi-step analysis:
                        </p>
                        <ol style="color: var(--jl-muted) !important;">
                            <li><strong>Intent Classification:</strong> It first determines the nature of your query to understand if it's a real-world scenario, a request for a legal explanation, or a general question.</li>
                            <li><strong>Database Retrieval:</strong> It then queries its legal knowledge base, which includes statutory provisions, landmark case law, and dynamic rule updates, to find the most relevant legal precedents and sections.</li>
                            <li><strong>Structured Response Generation:</strong> Finally, it synthesizes this information into a clear, structured report, including an action plan and evidence preservation steps.</li>
                        </ol>
                        <p style="color: var(--jl-muted) !important; margin-top:1rem; margin-bottom:0;">
                           This process ensures that the guidance is not only rapid but also grounded in verified legal logic, empowering users to make informed decisions during the critical hours following a cyber incident.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif st.session_state.view == "Terms":
                st.markdown(
                    """
                    <div class="jl-card">
                        <h3 style="margin-top:0;">1. Scope of Guidance</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                            The information provided by Justice Lens is for informational and educational purposes only. The analysis is generated by an AI system based on a database of Indian cyber laws and is intended to serve as a preliminary guide for understanding potential legal avenues and immediate response actions.
                        </p>
                        <h3 style="margin-top:1.5rem;">2. Not a Substitute for Legal Counsel</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                            Justice Lens is not a law firm and does not provide legal advice. The information generated by the AI does not constitute a lawyer-client relationship. For any serious legal issue, you must consult with a qualified, licensed legal professional.
                        </p>
                        <h3 style="margin-top:1.5rem;">3. Data Privacy and Security</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                            Do not share any sensitive personal information in the chat, including but not limited to passwords, OTPs, financial account numbers, or government-issued identification numbers. The system is designed for scenario analysis, not for the transmission of confidential data.
                        </p>
                         <h3 style="margin-top:1.5rem;">4. Limitation of Liability</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                            While we strive for accuracy, the legal landscape is constantly evolving. We do not warrant the completeness or accuracy of the information provided. The developers of Justice Lens shall not be liable for any damages arising out of the use of the information provided.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        l_pad, main, r_pad = st.columns([1, 8, 1])
        with main:
            logo_l, logo_m, logo_r = st.columns([3, 2, 3])
            with logo_m:
                st.image(LOGO_SOURCE, use_container_width=True)

            with st.container():
                st.markdown(
                    """
                    <div class="jl-hero">
                        <div class="title">Justice Lens</div>
                        <div class="subtitle">Minimalist cyber-law AI for incident response and verified legal logic.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="jl-mobile-only">', unsafe_allow_html=True)
            btn_l, btn_m, btn_r = st.columns([3, 2, 3])
            with btn_m:
                if st.button("LOGIN", key="jl_login_btn_mobile", use_container_width=True):
                    st.session_state.mobile_login_open = True
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.mobile_login_open:
                st.markdown('<div class="jl-mobile-only">', unsafe_allow_html=True)
                m_tab = st.tabs(["Login", "Create Account"])
                with m_tab[0]:
                    m_email = st.text_input("Email", key="m_login_email")
                    m_pass = st.text_input("Password", type="password", key="m_login_pass")
                    if st.button(" Authenticate", key="m_login_btn"):
                        valid, u_obj = authenticate(m_email, m_pass)
                        if valid:
                            if check_ban(u_obj.uid):
                                st.error("Access Forbidden.")
                            else:
                                st.session_state.user = {"name": u_obj.display_name or m_email.split('@')[0], "email": m_email, "uid": u_obj.uid}
                                st.session_state.jl_chats_loaded = False
                                st.session_state.view = "AI Assistant"
                                st.session_state.mobile_login_open = False
                                _ensure_chats_loaded()
                                if db:
                                    sid = str(uuid.uuid4())
                                    try:
                                        _session_store_ref().document(sid).set({
                                            "uid": u_obj.uid,
                                            "email": m_email,
                                            "name": u_obj.display_name or m_email.split('@')[0],
                                            "created_at": utc_now(),
                                        })
                                        _set_sid(sid)
                                    except Exception:
                                        pass
                                sync_user(st.session_state.user)
                                st.rerun()
                        else:
                            st.error("Invalid Credentials.")

                with m_tab[1]:
                    m_name = st.text_input("Full Name", key="m_full_name")
                    m_email_new = st.text_input("Email", key="m_s_email")
                    m_pass_new = st.text_input("Create Password", type="password", key="m_s_pass")
                    if st.button("REGISTER", key="m_register_btn"):
                        try:
                            auth.create_user(email=m_email_new, password=m_pass_new, display_name=m_name)
                            st.success("Account Ready! Use Login.")
                        except Exception as ex:
                            st.error(str(ex))
                if st.button("Guest User", key="m_guest_btn"):
                    gid = str(uuid.uuid4())[:8]
                    st.session_state.user = {"name": f"Guest_{gid}", "email": "guest@justicelens.io", "uid": f"guest_{gid}"}
                    st.session_state.mobile_login_open = False
                    st.session_state.jl_chats_loaded = False
                    _ensure_chats_loaded()
                    if db:
                        sid = str(uuid.uuid4())
                        try:
                            _session_store_ref().document(sid).set({
                                "uid": st.session_state.user["uid"],
                                "email": st.session_state.user["email"],
                                "name": st.session_state.user["name"],
                                "created_at": utc_now(),
                            })
                            _set_sid(sid)
                        except Exception:
                            pass
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            st.write("")
            f1, f2, f3 = st.columns(3)
            with f1:
                st.markdown(
                    """
                    <div class="jl-feature">
                        <div class="kicker">Always On</div>
                        <div class="headline">24/7 Incident Support</div>
                        <p class="desc">Get immediate, automated guidance for reporting cybercrimes, preserving critical digital evidence, and containing the incident to prevent further harm.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with f2:
                st.markdown(
                    """
                    <div class="jl-feature">
                        <div class="kicker">Grounded</div>
                        <div class="headline">Verified Legal Framework</div>
                        <p class="desc">Our AI provides responses structured around specific IT Act sections, official punishments, and relevant case law, ensuring the guidance is grounded and reliable.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with f3:
                st.markdown(
                    """
                    <div class="jl-feature">
                        <div class="kicker">Tactical</div>
                        <div class="headline">Actionable Response Plans</div>
                        <p class="desc">Receive clear, step-by-step action plans, including golden-hour reporting, evidence collection, and strategic escalation paths for banks and authorities.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
else:
    page = st.session_state.view
    if page == "AI Assistant":
        active = st.session_state.active_project
        history = st.session_state.projects[active]
        # Keep backward compatibility for other parts of the app
        st.session_state.chat_history = history

        def _handle_user_message(user_msg: str):
            if not user_msg:
                return
            history.append({"role": "user", "content": user_msg})

            with st.spinner("Analyzing scope..."): 
                category = get_intent_category(user_msg)

            if category == "INVALID":
                ans = _out_of_scope_report()
            else:
                with st.spinner("Querying legal database..."):
                    dataset_evidence = ""
                    try:
                        idx, emb = get_backend()
                        if idx and emb:
                            v = emb.embed_query(user_msg)
                            m = idx.query(vector=v, top_k=3, include_metadata=True)
                            dataset_evidence = " ".join(
                                [x.get("metadata", {}).get("text", "") for x in m.get("matches", [])]
                            ) or ""
                    except Exception:
                        pass

                with st.spinner("Generating legal report..."):
                    try:
                        report = ask_groq_lawyer(user_msg, dataset_evidence, category)
                        ans = "\n".join([
                            "JUSTICE LENS ADVISORY REPORT",
                            "-" * 30,
                            report,
                            "-" * 30,
                        ])
                    except Exception:
                        ans = (
                            "I ran into an issue generating the report just now. "
                            "Please try again in a moment. If it persists, rephrase the query."
                        )

            history.append({"role": "assistant", "content": ans})
            _persist_chat_for_user(st.session_state.user.get("uid"), active, history)

            if db:
                try:
                    db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("logs").add({
                        "uid": st.session_state.user["uid"],
                        "user": st.session_state.user["name"],
                        "query": user_msg,
                        "report": ans,
                        "timestamp": utc_now(),
                        "project": active,
                    })
                except Exception:
                    pass

        # Header (minimal hero + utility actions)
        # _, clear_col = st.columns([5, 1])
        # with clear_col:
        #     if st.button("Clear chat", use_container_width=True):
        #         history.clear()
        #         st.rerun()

        # with st.container():
        #     st.markdown(
        #         """
        #         <div class="jl-hero">
        #             <div class="title">Justice Lens</div>
        #             <div class="subtitle">Professional cyber-law assistant for scenarios and IT Act references.</div>
        #         </div>
        #         """,
        #         unsafe_allow_html=True,
        #     )

        # st.write("")
        # g1, g2, g3 = st.columns(3)
        # with g1:
        #     st.markdown(
        #         """
        #         <div class="jl-feature">
        #             <div class="kicker">Always On</div>
        #             <div class="headline">24/7 Incident Support</div>
        #             <p class="desc">Get immediate, automated guidance for reporting cybercrimes, preserving critical digital evidence, and containing the incident to prevent further harm.</p>
        #         </div>
        #         """,
        #         unsafe_allow_html=True,
        #     )
        # with g2:
        #     st.markdown(
        #         """
        #         <div class="jl-feature">
        #             <div class="kicker">Grounded</div>
        #             <div class="headline">Verified Legal Framework</div>
        #             <p class="desc">Our AI provides responses structured around specific IT Act sections, official punishments, and relevant case law, ensuring the guidance is grounded and reliable.</p>
        #         </div>
        #         """,
        #         unsafe_allow_html=True,
        #     )
        # with g3:
        #     st.markdown(
        #         """
        #         <div class="jl-feature">
        #             <div class="kicker">Tactical</div>
        #             <div class="headline">Actionable Response Plans</div>
        #             <p class="desc">Receive clear, step-by-step action plans, including golden-hour reporting, evidence collection, and strategic escalation paths for banks and authorities.</p>
        #         </div>
        #         """,
        #         unsafe_allow_html=True,
        #     )

        # st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # Main chat area
        with st.container():
            # Welcome tiles when empty
            st.markdown("""
                <div class="jl-card" style="text-align:center; margin-bottom: 2rem;">
                    <h2 style="margin:0;">Welcome</h2>
                    <p style="margin:0.35rem 0 0; color: var(--jl-muted) !important; font-weight:600;">Start with a scenario or ask for an IT Act section explanation.</p>
                </div>
            """, unsafe_allow_html=True)

            t1, t2 = st.columns(2, gap="large")
            with t1:
                if st.button("Report UPI scam", use_container_width=True):
                    st.session_state.jl_pending_msg = "I was scammed via UPI. What sections apply?"
                    st.rerun()
                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
                if st.button("Account hacked", use_container_width=True):
                    st.session_state.jl_pending_msg = "My account was hacked and my data leaked. What should I do?"
                    st.rerun()
            with t2:
                if st.button("Explain Section 66F", use_container_width=True):
                    st.session_state.jl_pending_msg = "Explain Section 66F"
                    st.rerun()
                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
                if st.button("Privacy violation", use_container_width=True):
                    st.session_state.jl_pending_msg = "Someone posted my private photos without consent. What are the punishments?"
                    st.rerun()
        
        # Process any pending message (from tiles)
        pending = st.session_state.pop("jl_pending_msg", None)
        if pending:
            _handle_user_message(pending)
            st.rerun()

        for i, chat in enumerate(history):
            role = "user" if chat.get("role") == "user" else "assistant"
            avatar = "🧑‍💼" if role == "user" else "⚖️"
            with st.chat_message(role, avatar=avatar):
                content = chat.get("content", "")
                if role == "assistant" and content:
                    if _looks_like_report(content):
                        st.markdown(_render_report_html(content), unsafe_allow_html=True)
                    else:
                        safe = html.escape(content)
                        st.markdown(
                            f"<div style='white-space: pre-wrap;'>{safe}</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(content)
                if role == "assistant" and content:
                    encoded_content = urllib.parse.quote_plus(content)
                    translate_url = f"https://translate.google.com/m?sl=auto&tl=en&q={encoded_content}"
                    try:
                        b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
                    except Exception:
                        b64 = ""
                    st.markdown(
                        f'<div class="jl-chat-actions">'
                        f'<a class="jl-translate-link" href="{translate_url}" target="_blank" rel="noopener">Translate</a>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        cooldown_remaining = max(0, int(st.session_state.cooldown_until - time.time()))

        if cooldown_remaining > 0:
            st.info(f"Please wait {cooldown_remaining}s before sending another request.")
            _ = st.chat_input(
                "Describe a cyber incident, or ask e.g. “Explain Section 66F”",
                disabled=True,
                key="jl_chat_input",
            )
            time.sleep(1)
            st.rerun()
        else:
            user_msg = st.chat_input(
                "Describe a cyber incident, or ask e.g. “Explain Section 66F”",
                key="jl_chat_input",
            )
            if user_msg:
                st.session_state.cooldown_until = time.time() + 5
                _handle_user_message(user_msg)
                st.rerun()

    elif page == "Vision & Mission":
        st.title("Our Core Principles")
        st.markdown(
            """
            <div class="jl-card" style="margin-bottom: 1.5rem;">
                <h3 style="margin-top:0;">Our Vision</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    To create a future where every citizen and organization can navigate the complexities of Indian cyber law with clarity and confidence. We envision a digitally secure India where access to preliminary legal guidance for cyber incidents is immediate, accessible, and universally available, empowering individuals to protect their rights and digital identity.
                </p>
            </div>
            <div class="jl-card">
                <h3 style="margin-top:0;">Our Mission</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    Our mission is to democratize cyber law knowledge. We leverage state-of-the-art AI, grounded in a meticulously curated database of the Indian IT Act and case law, to provide structured, actionable, and context-aware guidance. We are committed to delivering a reliable first-response tool that helps users understand their situation, preserve critical evidence, and take the right initial steps during the golden hour of a cyber incident.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif page == "About":
        st.title("About")
        st.markdown(
            """
            <div class="jl-card">
                <h3 style="margin-top:0;">What is Justice Lens?</h3>
                <p style="color: var(--jl-muted) !important;">
                    Justice Lens is an advanced cyber-law assistant engineered to provide immediate, structured, and actionable insights into common cyber incidents within the Indian legal framework.
                </p>
                <h3 style="margin-top:1.5rem;">How it Works</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    Our system leverages a powerful AI engine coupled with a curated database of Indian cyber law, including the IT Act of 2000 and subsequent amendments. When you describe a scenario, the AI performs a multi-step analysis:
                </p>
                <ol style="color: var(--jl-muted) !important;">
                    <li><strong>Intent Classification:</strong> It first determines the nature of your query to understand if it's a real-world scenario, a request for a legal explanation, or a general question.</li>
                    <li><strong>Database Retrieval:</strong> It then queries its legal knowledge base, which includes statutory provisions, landmark case law, and dynamic rule updates, to find the most relevant legal precedents and sections.</li>
                    <li><strong>Structured Response Generation:</strong> Finally, it synthesizes this information into a clear, structured report, including an action plan and evidence preservation steps.</li>
                </ol>
                <p style="color: var(--jl-muted) !important; margin-top:1rem; margin-bottom:0;">
                   This process ensures that the guidance is not only rapid but also grounded in verified legal logic, empowering users to make informed decisions during the critical hours following a cyber incident.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif page == "Terms":
        st.title("Terms")
        st.markdown(
            """
            <div class="jl-card">
                <h3 style="margin-top:0;">1. Scope of Guidance</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    The information provided by Justice Lens is for informational and educational purposes only. The analysis is generated by an AI system based on a database of Indian cyber laws and is intended to serve as a preliminary guide for understanding potential legal avenues and immediate response actions.
                </p>
                <h3 style="margin-top:1.5rem;">2. Not a Substitute for Legal Counsel</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    Justice Lens is not a law firm and does not provide legal advice. The information generated by the AI does not constitute a lawyer-client relationship. For any serious legal issue, you must consult with a qualified, licensed legal professional.
                </p>
                <h3 style="margin-top:1.5rem;">3. Data Privacy and Security</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    Do not share any sensitive personal information in the chat, including but not limited to passwords, OTPs, financial account numbers, or government-issued identification numbers. The system is designed for scenario analysis, not for the transmission of confidential data.
                </p>
                 <h3 style="margin-top:1.5rem;">4. Limitation of Liability</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    While we strive for accuracy, the legal landscape is constantly evolving. We do not warrant the completeness or accuracy of the information provided. The developers of Justice Lens shall not be liable for any damages arising out of the use of the information provided.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


    elif page == "Admin Dashboard" and st.session_state.admin_mode:
        st.title("Admin Dashboard")
        if db:
            u_ref = db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("users")
            user_docs = list(u_ref.stream())
            users = []
            for u in user_docs:
                ud = u.to_dict() or {}
                users.append({
                    "doc_id": u.id,
                    "name": ud.get("name", "Unknown"),
                    "email": ud.get("email", ""),
                    "uid": ud.get("uid", u.id),
                    "is_banned": bool(ud.get("is_banned", False)),
                    "last_active": ud.get("last_active")
                })

            total_users = len(users)
            banned_users = sum(1 for x in users if x["is_banned"])
            active_users = total_users - banned_users
            guest_users = sum(1 for x in users if str(x["email"]).lower() == "guest@justicelens.io")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(label="Total Users", value=str(total_users), delta="—")
            m2.metric(label="Active Users", value=str(active_users), delta="—")
            m3.metric(label="Banned Users", value=str(banned_users), delta="—")
            m4.metric(label="Guest Users", value=str(guest_users), delta="—")

            st.divider()

            # --- Admin chat retention + cleanup tools ---
            def _to_dt(value):
                if isinstance(value, datetime):
                    return value
                if hasattr(value, "to_datetime"):
                    try:
                        return value.to_datetime()
                    except Exception:
                        return None
                return None

            def _iter_chat_project_docs():
                docs = []
                for ud in users:
                    try:
                        proj_ref = (
                            db.collection("artifacts")
                            .document("justicelens-law")
                            .collection("public")
                            .document("data")
                            .collection("chats")
                            .document(ud["uid"])
                            .collection("projects")
                        )
                        docs.extend(list(proj_ref.stream()))
                    except Exception:
                        continue
                return docs

            def _cleanup_chats_older_than(days: int):
                cutoff = utc_now() - timedelta(days=days)
                deleted = 0
                scanned = 0
                for doc in _iter_chat_project_docs():
                    scanned += 1
                    data = doc.to_dict() or {}
                    updated_at = _to_dt(data.get("updated_at"))
                    if updated_at and updated_at < cutoff:
                        doc.reference.delete()
                        deleted += 1
                return deleted, scanned

            def _delete_all_chats():
                deleted = 0
                for doc in _iter_chat_project_docs():
                    doc.reference.delete()
                    deleted += 1
                return deleted

            st.markdown("### Chat Retention & Cleanup")
            settings_ref = (
                db.collection("artifacts")
                .document("justicelens-law")
                .collection("public")
                .document("data")
                .collection("settings")
                .document("chat_retention")
            )
            settings = {}
            try:
                settings_doc = settings_ref.get()
                if settings_doc and settings_doc.exists:
                    settings = settings_doc.to_dict() or {}
            except Exception:
                settings = {}

            retention_options = {
                "Off": 0,
                "15 days": 15,
                "30 days": 30,
                "60 days": 60,
            }
            saved_days = int(settings.get("days") or 0)
            if saved_days not in retention_options.values():
                saved_days = 30
            saved_label = next((k for k, v in retention_options.items() if v == saved_days), "30 days")
            saved_enabled = bool(settings.get("enabled", False))

            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                retention_label = st.selectbox(
                    "Auto-delete chats after",
                    list(retention_options.keys()),
                    index=list(retention_options.keys()).index(saved_label),
                    key="admin_chat_retention_days",
                )
            with c2:
                retention_enabled = st.checkbox(
                    "Enable auto-delete",
                    value=saved_enabled,
                    key="admin_chat_retention_enabled",
                )
            with c3:
                st.caption("Admins only")

            save_col, run_col = st.columns([1, 1])
            with save_col:
                if st.button("Save retention settings", use_container_width=True):
                    days_val = retention_options.get(retention_label, 0)
                    settings_ref.set(
                        {
                            "enabled": bool(retention_enabled) and days_val > 0,
                            "days": int(days_val),
                            "updated_at": utc_now(),
                        },
                        merge=True,
                    )
                    st.success("Retention settings saved.")
            with run_col:
                if st.button("Run cleanup now", use_container_width=True, type="secondary"):
                    days_val = retention_options.get(retention_label, 0)
                    if days_val <= 0:
                        st.info("Select a retention period above to run cleanup.")
                    else:
                        with st.spinner("Deleting old chats..."):
                            deleted, scanned = _cleanup_chats_older_than(days_val)
                        settings_ref.set({"last_cleanup": utc_now()}, merge=True)
                        st.success(f"Cleanup complete: {deleted} chat documents removed (scanned {scanned}).")

            # Auto-cleanup runs only for admins and no more than twice per day (uses saved settings).
            auto_days = int(settings.get("days") or 0)
            auto_enabled = bool(settings.get("enabled", False))
            if auto_enabled and auto_days > 0:
                last_cleanup = _to_dt(settings.get("last_cleanup"))
                if (not last_cleanup) or (utc_now() - last_cleanup).total_seconds() > 12 * 3600:
                    with st.spinner("Auto-cleanup running..."):
                        deleted, scanned = _cleanup_chats_older_than(auto_days)
                    settings_ref.set({"last_cleanup": utc_now()}, merge=True)
                    if deleted:
                        st.info(f"Auto-cleanup removed {deleted} old chat documents.")

            st.caption("Use manual cleanup for immediate removal or set auto-delete to remove old chats automatically.")
            st.divider()

            f1, f2 = st.columns([3, 1])
            with f1:
                search_q = st.text_input("Search user (name/email)", key="admin_user_search")
            with f2:
                status_filter = st.selectbox("Status", ["All", "Active", "Banned"], key="admin_status_filter")

            filtered_users = users
            if search_q:
                q = search_q.strip().lower()
                filtered_users = [x for x in filtered_users if q in str(x["name"]).lower() or q in str(x["email"]).lower()]
            if status_filter == "Active":
                filtered_users = [x for x in filtered_users if not x["is_banned"]]
            elif status_filter == "Banned":
                filtered_users = [x for x in filtered_users if x["is_banned"]]

            if users:
                export_df = pd.DataFrame([
                    {
                        "name": x["name"],
                        "email": x["email"],
                        "uid": x["uid"],
                        "status": "BANNED" if x["is_banned"] else "ACTIVE",
                        "last_active_ist": format_app_time(x["last_active"], '%Y-%m-%d %H:%M:%S')
                    } for x in users
                ])
                st.download_button(
                    "Download user list (CSV)",
                    data=export_df.to_csv(index=False),
                    file_name="justice_lens_users.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            st.divider()
            st.markdown("### User Directory")
            if not filtered_users:
                st.info("No users match the current filter.")
            for ud in filtered_users:
                last_active = format_app_time(ud["last_active"], '%d %b, %H:%M IST')
                status_text = "BANNED" if ud["is_banned"] else "ACTIVE"
                badge_class = "jl-badge-banned" if ud["is_banned"] else "jl-badge-active"

                with st.container(border=True):
                    info_col, ban_col, del_col, chat_del_col = st.columns([4, 1, 1, 1])
                    with info_col:
                        st.markdown(
                            f"**{ud['name']}** <span class='jl-badge {badge_class}'>{status_text}</span>",
                            unsafe_allow_html=True,
                        )
                        st.caption(ud["email"] or "—")
                        st.caption(f"Last active: {last_active}")

                    with ban_col:
                        b_label = "Unban" if ud["is_banned"] else "Ban"
                        if st.button(b_label, key=f"ban_{ud['doc_id']}", use_container_width=True):
                            u_ref.document(ud["doc_id"]).update({"is_banned": not ud["is_banned"]})
                            st.rerun()

                    with del_col:
                        if st.button("Delete", key=f"del_{ud['doc_id']}", use_container_width=True, type="secondary"):
                            try:
                                auth.delete_user(ud["doc_id"])
                            except Exception:
                                pass
                            try:
                                u_ref.document(ud["doc_id"]).delete()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    with chat_del_col:
                        if st.button("Delete Chats", key=f"delchats_{ud['doc_id']}", use_container_width=True):
                            try:
                                deleted = 0
                                for doc in db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("chats").document(ud["uid"]).collection("projects").stream():
                                    doc.reference.delete()
                                    deleted += 1
                                st.success(f"Deleted {deleted} chat documents.")
                            except Exception as e:
                                st.error(f"Error deleting chats: {e}")

            st.divider()
            st.markdown("### Global Chat Delete")
            confirm_delete_all = st.checkbox(
                "I understand this will permanently delete all chats for all users.",
                key="admin_delete_all_chats_confirm",
            )
            if st.button("Delete ALL Chats", use_container_width=True, type="secondary", disabled=not confirm_delete_all):
                with st.spinner("Deleting all chats..."):
                    deleted = _delete_all_chats()
                settings_ref.set({"last_cleanup": utc_now()}, merge=True)
                st.success(f"Deleted {deleted} chat documents in total.")
        else:
            st.error("Database not available.")
                    
