import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json
import uuid
import requests
import time
import re
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings

# ==========================================
# âš™ï¸ CONFIGURATION & API KEYS
# ==========================================
PINECONE_KEY = st.secrets.get("PINECONE_KEY", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
FIREBASE_WEB_API_KEY = st.secrets.get("FIREBASE_WEB_API_KEY", "AIzaSyAklh23Fu6-P5vNsGDh2-U9titgRvqzJaU")
INDEX_NAME = "justice-lens"
LOGO_FALLBACK_URL = "https://i.ibb.co/B57FLnW4/image.png"
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
st.set_page_config(
    page_title="Justice Lens | Expert Cyber Legal AI",
    page_icon="âš–ï¸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Minimalist Professional UI Theme (Slate + Cyber Cyan) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
    
    :root {
        --bg: #0412B2;
        --bg-soft: #0D96CE;
        --panel: #0412B2;
        --panel-2: #0E6DB5;
        --text: #000000;
        --muted: #9FB2D9;
        --line: #223B6B;
        --accent: #43A2FF;
        --accent-2: #7FC4FF;
        --gold: #E0B45B;
        --good-shadow: 0 16px 38px rgba(3, 9, 22, 0.45);
    }

    html, body, [data-testid="stMarkdownContainer"] p,
    .stMarkdown, label, li, h1, h2, h3 {
        font-family: 'Manrope', sans-serif !important;
        color: var(--text) !important;
        font-size: 0.95rem !important;
    }
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em;
    }

    .stApp {
        background:
            radial-gradient(1200px 600px at 12% 0%, rgba(67,162,255,0.15), transparent 50%),
            radial-gradient(900px 500px at 100% 12%, rgba(224,180,91,0.10), transparent 48%),
            linear-gradient(180deg, #0D96CE 0%, #0E6DB5 45%, #0412B2 100%) !important;
        min-height: 100vh;
    }
    .main .block-container {
        padding-top: 1.05rem !important;
        max-width: 1120px !important;
        animation: fadeUp 0.45s ease-out;
    }
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="collapsedControl"] button,
    [data-testid="stSidebarCollapsedControl"] button {
        background: #0412B2 !important;
        border: 1px solid #2C5A98 !important;
        border-radius: 999px !important;
        width: 36px !important;
        height: 36px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 10px rgba(2, 9, 22, 0.24) !important;
        padding: 0 !important;
    }
    [data-testid="stSidebarCollapseButton"] button svg,
    [data-testid="collapsedControl"] button svg,
    [data-testid="stSidebarCollapsedControl"] button svg {
        color: #DCEAFF !important;
        width: 0.92rem !important;
        height: 0.92rem !important;
    }
    [data-testid="stSidebarCollapseButton"] button svg path,
    [data-testid="collapsedControl"] button svg path,
    [data-testid="stSidebarCollapsedControl"] button svg path {
        stroke: #DCEAFF !important;
        fill: #DCEAFF !important;
    }
    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="collapsedControl"] button:hover,
    [data-testid="stSidebarCollapsedControl"] button:hover {
        transform: translateY(-1px);
        filter: brightness(1.02);
    }
    [data-testid="collapsedControl"] button p,
    [data-testid="stSidebarCollapsedControl"] button p {
        color: #DCEAFF !important;
        font-weight: 900 !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stDecoration"], [data-testid="stStatusWidget"],
    [data-testid="stMainMenu"], .st-emotion-cache-zt53z0,
    button[title="Main menu"], button[aria-label="Main menu"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* Hide Streamlit creator/hosting badges shown in app footer */
    [data-testid="stAppCreatorBadge"],
    [data-testid="stAppHostingBadge"],
    [data-testid="stBadge"],
    [data-testid="stCaptionContainer"] a[href*="streamlit.io"],
    a[href*="streamlit.io/cloud"],
    a[href*="share.streamlit.io"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    [data-testid="stToolbarActions"] {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        border: none !important;
    }

    section[data-testid="stSidebar"] {
        background:
            radial-gradient(120% 80% at 0% 0%, rgba(67,162,255,0.20), transparent 50%),
            linear-gradient(180deg, #08162F 0%, #0B1C3A 100%) !important;
        border-right: 1px solid #1E386A;
        box-shadow: inset -1px 0 0 rgba(127,196,255,0.10);
    }
    section[data-testid="stSidebar"] * {
        color: #F2F7FF !important;
        font-size: 0.9rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding: 0.65rem 0.8rem 1rem 0.8rem !important;
    }
    section[data-testid="stSidebar"] .stTextInput > label {
        font-weight: 700 !important;
        margin-bottom: 0.24rem !important;
    }
    section[data-testid="stSidebar"] .stTextInput > div > div > input {
        min-height: 44px !important;
        background: rgba(255,255,255,0.97) !important;
        color: #0A1A37 !important;
        border: 1px solid #A7C2E7 !important;
        border-radius: 25px !important;
        padding: 0.58rem 0.76rem !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="input"] {
        align-items: center !important;
        border-radius: 25px !important;
        overflow: hidden !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="input"] > div {
        display: flex !important;
        align-items: center !important;
    }
    section[data-testid="stSidebar"] input[type="password"] {
        padding-right: 2.7rem !important;
        line-height: 1.2 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="input"] button {
        margin-right: 0.25rem !important;
        min-width: 1.9rem !important;
        height: 1.9rem !important;
        border-radius: 0.5rem !important;
    }
    section[data-testid="stSidebar"] .stTabs [data-baseweb="tab-list"] {
        margin-bottom: 0.6rem !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="tab-list"] {
        gap: 8px;
        padding: 6px;
        border-radius: 10px;
        background: rgba(127,196,255,0.10);
        display: grid !important;
        grid-template-columns: 1fr 1fr;
    }
    section[data-testid="stSidebar"] [data-baseweb="tab"] {
        border-radius: 8px !important;
        transition: all 0.18s ease !important;
    }
    section[data-testid="stSidebar"] [aria-selected="true"] {
        background: linear-gradient(135deg, #3F9EFF, #67B3FF) !important;
        color: #061022 !important;
        font-weight: 800 !important;
    }

    .glass-card, .team-card, .admin-data-card, .chat-container {
        background: linear-gradient(160deg, rgba(19,39,75,0.92), rgba(15,31,61,0.92)) !important;
        border: 1px solid #22437A !important;
        box-shadow: var(--good-shadow);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    .glass-card {
        padding: 1.2rem;
        border-radius: 18px;
        margin-bottom: 1rem;
        transition: transform 0.22s ease, box-shadow 0.22s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(2, 9, 22, 0.50);
    }
    .hero-panel { position: relative; overflow: hidden; }
    .hero-panel::before {
        content: "";
        position: absolute;
        inset: -45% auto auto -16%;
        width: 380px;
        height: 380px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(67,162,255,0.20), transparent 70%);
        pointer-events: none;
    }
    h1 { font-size: 1.95rem !important; font-weight: 800 !important; }
    h2 { font-size: 1.2rem !important; font-weight: 700 !important; margin-bottom: 0.7rem !important; }
    h3 { font-size: 0.92rem !important; font-weight: 700 !important; color: var(--gold) !important; margin-top: 0 !important; }

    .stTextInput > div > div > input,
    textarea, .stTextArea textarea, [data-baseweb="input"] input {
        border-radius: 10px !important;
        border: 1px solid #375C97 !important;
        background: #F7FAFF !important;
        color: #0412B2 !important;
        caret-color: #0A1A37 !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #6B7FA7 !important;
        opacity: 1 !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #5E739A !important;
        box-shadow: none !important;
    }

    .stButton > button, .stFormSubmitButton > button {
        width: 100%;
        border-radius: 10px;
        border: 1px solid rgba(127,196,255,0.32);
        padding: 0.58rem 1rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1A58A5 0%, #43A2FF 100%);
        color: #FFFFFF !important;
        text-transform: uppercase;
        letter-spacing: 0.9px;
        font-size: 0.74rem !important;
        box-shadow: 0 8px 20px rgba(67,162,255,0.22);
        transition: transform 0.2s ease, filter 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-2px);
        filter: brightness(1.05);
        box-shadow: 0 12px 24px rgba(67,162,255,0.26);
    }

    .chat-container {
        max-width: 980px;
        margin: 0 auto;
        padding: 1.4rem;
        border-radius: 18px;
    }
    .bubble-container { display: flex; flex-direction: column; gap: 1.2rem; }
    .chat-bubble {
        padding: 1rem 1.35rem;
        border-radius: 1.25rem;
        font-size: 0.95rem;
        line-height: 1.52;
        max-width: 88%;
        animation: bubbleIn 0.2s ease both;
    }
    @keyframes bubbleIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .user-bubble {
        background: linear-gradient(135deg, #1A58A5, #43A2FF);
        color: #FFFFFF !important;
        border-bottom-right-radius: 5px;
    }
    .ai-bubble {
        background: rgba(255,255,255,0.93);
        color: #0B1B39 !important;
        border: 1px solid #BED4F2;
        border-bottom-left-radius: 5px;
    }
    .ai-bubble, .ai-bubble * {
        color: #0B1B39 !important;
        opacity: 1 !important;
    }
    .ai-bubble p, .ai-bubble li, .ai-bubble span, .ai-bubble strong {
        color: #0B1B39 !important;
    }
    .ai-bubble a {
        color: #1A58A5 !important;
        text-decoration: underline !important;
        font-weight: 700 !important;
    }
    .role-label {
        font-size: 0.64rem;
        font-weight: 900;
        color: #8FCBFF !important;
        margin-bottom: 3px;
        text-transform: uppercase;
        letter-spacing: 1.8px;
    }

    .admin-data-card {
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 0.8rem;
    }
    .admin-data-card b, .admin-data-card p { color: #E9F1FF !important; }
    .admin-data-card p { margin: 0; font-size: 0.82rem !important; opacity: 0.84; }
    .status-badge {
        font-weight: 800;
        font-size: 0.66rem;
        padding: 2px 8px;
        border-radius: 4px;
        color: white !important;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #43A2FF, #7FC4FF) !important;
    }
    [data-testid="stRadio"] label {
        padding: 0.45rem 0.6rem;
        border-radius: 8px;
        transition: background 0.15s ease;
    }
    [data-testid="stRadio"] label:hover {
        background: rgba(67,162,255,0.16);
    }
    .team-card {
        padding: 1.5rem;
        border-radius: 14px;
        text-align: center;
        transition: transform 0.22s ease, box-shadow 0.22s ease;
    }
    .team-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 18px 35px rgba(2, 9, 22, 0.44);
    }
    .team-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1rem;
        margin-top: 0.8rem;
    }
    .team-card .avatar {
        font-size: 2.4rem;
        margin-bottom: 0.75rem;
        line-height: 1;
    }
    .team-card .team-name {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.45rem;
        font-weight: 700;
        color: #EAF2FF !important;
        margin-bottom: 0.35rem;
        word-break: break-word;
    }
    .team-card .team-role {
        font-size: 0.95rem;
        line-height: 1.45;
        color: #E0B45B !important;
        font-weight: 700;
        letter-spacing: 0.2px;
    }
    .hero-logo {
        width: min(170px, 34vw);
        display: block;
        margin: 0 auto 1rem auto;
        border-radius: 14px;
        border: 1px solid #27508C;
        box-shadow: 0 10px 24px rgba(2, 9, 22, 0.42);
    }
    .start-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-top: 0.7rem;
        padding: 0.75rem 1.24rem;
        border-radius: 999px;
        background: linear-gradient(135deg, #1A58A5, #43A2FF);
        border: 2px solid rgba(127,196,255,0.42);
        color: #FFFFFF !important;
        font-weight: 800;
        letter-spacing: 0.8px;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        box-shadow: 0 8px 20px rgba(67,162,255,0.26);
    }
    .light-panel, .light-panel p, .light-panel b {
        color: #0B1B39 !important;
    }
    .light-panel h3 {
        color: #A57316 !important;
    }

    [data-testid="stExpander"] summary p {
        font-weight: 700 !important;
        color: #E8F1FF !important;
        font-size: 1rem !important;
    }

    @media (max-width: 1100px) {
        section[data-testid="stSidebar"] {
            min-width: 300px !important;
            max-width: 86vw !important;
        }
    }
    @media (max-width: 960px) {
        .main .block-container {
            padding-top: 1rem !important;
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
        }
        .chat-container { padding: 1rem; }
        .chat-bubble { max-width: 96%; font-size: 0.92rem; }
        .team-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 700px) {
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.1rem !important; }
        .glass-card, .team-card, .admin-data-card { padding: 1rem !important; }
        .hero-logo { width: min(180px, 62vw); }
        .team-grid { grid-template-columns: 1fr; }
        .team-card .team-name { font-size: 1.3rem; }
    }
    @media (max-width: 640px) {
        section[data-testid="stSidebar"] { min-width: 84vw !important; }
        section[data-testid="stSidebar"] [data-baseweb="tab"] {
            font-size: 0.8rem !important;
            padding: 0.35rem 0.3rem !important;
        }
        .stButton > button, .stFormSubmitButton > button {
            font-size: 0.9rem !important;
            padding: 0.5rem 0.9rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- Minimalist overrides (applied after legacy CSS) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root{
        --jl-bg: #F8FAFC;
        --jl-card: #FFFFFF;
        --jl-text: #0F172A;
        --jl-muted: #475569;
        --jl-border: #E2E8F0;
        --jl-primary: #06B6D4;
        --jl-primary-2: #0891B2;
        --jl-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        --jl-shadow-sm: 0 6px 18px rgba(15, 23, 42, 0.05);
        --jl-radius: 14px;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"]{
        background: var(--jl-bg) !important;
    }

    html, body, [data-testid="stMarkdownContainer"] p,
    .stMarkdown, label, li, h1, h2, h3, h4, h5, h6, div, span{
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif !important;
        color: var(--jl-text) !important;
    }

    .main .block-container{
        padding-top: 1.25rem !important;
        padding-bottom: 3rem !important;
        max-width: 1120px !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"]{
        background: #FFFFFF !important;
        border-right: 1px solid var(--jl-border) !important;
    }

    /* Buttons */
    .stButton > button, .stFormSubmitButton > button{
        background: var(--jl-primary) !important;
        border: 1px solid rgba(6, 182, 212, 0.35) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        padding: 0.58rem 0.9rem !important;
        font-weight: 700 !important;
        box-shadow: var(--jl-shadow-sm) !important;
        transition: transform 0.12s ease, background 0.12s ease, box-shadow 0.12s ease;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover{
        background: var(--jl-primary-2) !important;
        transform: translateY(-1px);
        box-shadow: var(--jl-shadow) !important;
    }

    /* Inputs */
    input, textarea, [data-baseweb="select"] > div{
        background: #FFFFFF !important;
        border: 1px solid var(--jl-border) !important;
        border-radius: 12px !important;
        color: var(--jl-text) !important;
        box-shadow: none !important;
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
    }

    /* Chat */
    [data-testid="stChatMessage"]{
        border: 1px solid var(--jl-border) !important;
        border-radius: 16px !important;
        padding: 0.35rem 0.6rem !important;
        box-shadow: var(--jl-shadow-sm) !important;
        background: #FFFFFF !important;
        margin-bottom: 0.55rem !important;
    }
    [data-testid="stChatInput"] textarea{
        border-radius: 14px !important;
        border: 1px solid var(--jl-border) !important;
        box-shadow: var(--jl-shadow-sm) !important;
    }

    @media (max-width: 700px){
        .jl-hero .title{ font-size: 1.65rem; }
        .main .block-container{ padding-left: 0.9rem !important; padding-right: 0.9rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
            time.sleep(0.2)
            
            bar.progress(50, text="Synchronizing AI Engine...")
            embed_model = HuggingFaceEmbeddings(model_name="nlpaueb/legal-bert-base-uncased")
            time.sleep(0.2)
            
            bar.progress(100, text="AI Online.")
            time.sleep(0.4)
            
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
            firebase_admin.initialize_app(cred, {'projectId': fb_data.get('project_id')})
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
if "start_researching_flow" not in st.session_state: st.session_state.start_researching_flow = False

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
    INTERNAL REFERENCE (ABSOLUTE TRUTH):
    - Section 70 (IT Act): Protected Systems. Definition: Unauthorized access to systems declared as critical infrastructure by the Government. Punishment = Up to 10 years.
    - Section 67A (IT Act): Sexually Explicit Content. Definition: Publishing or transmitting material containing sexually explicit acts in electronic form. Punishment = 5-7 years + 10 Lakh fine.
    - Section 66F (IT Act): Cyber Terrorism. Definition: Acts done with intent to threaten unity, integrity, or security of India via computer. Punishment = LIFE IMPRISONMENT.
    - Section 66E (IT Act): Violation of Privacy. Definition: Intentionally capturing or publishing private images of any person without consent. Punishment = Up to 3 years / up to 2 Lakh fine.
    - Section 66C (IT Act): Identity Theft. Definition: Fraudulently/dishonestly using another person’s electronic signature, password, or unique identification. Punishment = Up to 3 years + up to 1 Lakh fine.
    - Section 66D (IT Act): Cheating by Personation. Definition: Cheating by personation using any communication device/computer resource. Punishment = Up to 3 years + up to 1 Lakh fine.
    - Section 66B (IT Act): Stolen Computer Resource. Punishment = Up to 3 years / up to 5 Lakh fine.
    - Section 43 (IT Act): Civil Compensation. Definition: Unauthorized access/damage or unauthorised downloading/copying, etc. Punishment = Compensation ONLY (civil).
    - Section 43A (IT Act): Corporate Data Negligence. Definition: Failure by a body corporate to implement reasonable security practices for sensitive data. Punishment = Compensation ONLY (civil).
    """

def _justice_lens_case_history() -> str:
    return """
    HISTORICAL PRECEDENTS (USE FOR SCENARIOS):
    - Hacking/Unauthorized Access: State of Tamil Nadu vs. Suhas Katti (2004).
    - Privacy Violations: Justice K.S. Puttaswamy (Retd.) vs. Union of India (2017).
    - Financial Fraud: CBI vs. Arif Azim (Sony Sambandh Case).
    """

def _contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    h = str(haystack or "").lower()
    return any(n.lower() in h for n in needles)

def _is_phishing_portal_or_deepfake(user_input: str) -> bool:
    return _contains_any(user_input, (
        "phishing", "phish", "fake login", "spoof", "credential harvest", "otp page", "login page", "portal", "malicious link",
        "deepfake", "synthetic", "ai-generated", "ai generated", "morphed", "voice clone", "face swap", "impersonation video",
        "sgi", "synthetically generated",
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
        - 2026 Intermediary Takedown Rules: If the user mentions an active phishing portal or deepfake content, you MUST mention the IT Amendment Rules 2026.
          State that intermediaries/hosting platforms must remove unlawful "Synthetically Generated Information" (SGI) within 3 hours of a valid order/notice to maintain their "Safe Harbor" immunity under Section 79.
          Include this as a concrete takedown step in ACTION PLAN.
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
    JUSTICE LENS — 2026 LEGAL LOGIC UPDATES (APPLY TO ALL SCENARIO RESPONSES):
    - Phishing/identity theft/personation: Lead with IT Act Sections 66C (Identity Theft) and 66D (Cheating by Personation). Treat Section 43/43A as secondary civil-compensation remedies.
    - RBI compensation (2026 draft directions): If the user’s monetary loss is <= ₹50,000, explicitly mention they may be eligible for 85% compensation (capped at ₹25,000) if they report to the bank AND the 1930 helpline within 5 days (advise confirming current bank/RBI circular applicability).
    - Golden Hour: In ACTION PLAN, emphasize that financial fraud should be reported within the first 2 hours via the 1930 helpline or CFCFRMS (via cybercrime.gov.in) to maximize lien/freeze chances.
    - Liability nuance: Do NOT claim “0% liability” as a blanket rule. Clarify victim is not liable for hacker’s subsequent scams, but has a duty to report promptly and secure the breach (passwords/2FA/session revokes) to mitigate further harm.
    - Evidence strategy (primary): Advise preserving Email Headers, UPI Transaction IDs, and URL Metadata, and referencing Section 65B (Indian Evidence Act) for admissibility of electronic records.
    """

def _ensure_intermediary_takedown_mention(answer: str) -> str:
    if not answer:
        return answer

    already_mentions = (
        _contains_any(answer, ("it amendment rules 2026", "intermediary", "intermediaries")) and
        _contains_any(answer, ("3 hour", "three hour")) and
        _contains_any(answer, ("section 79", "safe harbor", "safe harbour"))
    )
    if already_mentions:
        return answer

    insertion = (
        '4. (Intermediary takedown) For an active phishing portal/deepfake: cite the IT Amendment Rules 2026—'
        'intermediaries must remove unlawful "Synthetically Generated Information" (SGI) within 3 hours of a valid order/notice '
        'to retain "Safe Harbor" under Section 79; file a takedown/abuse report with the host/platform and seek a cyber-cell order if needed.'
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

    return updated

def _normalize_intent_category(raw_category: str) -> str:
    upper = str(raw_category or "").strip().upper()
    for known in ("PHYSICAL", "CYBER_SCENARIO", "CYBER_EXPLAIN", "NON_LEGAL"):
        if known in upper:
            return known
    return "NON_LEGAL"

def get_intent_category(user_input):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    classifier_prompt = f"""
    Analyze the user input: "{user_input}"
    Categories:
    1. PHYSICAL: Related to physical crimes (theft, assault).
    2. CYBER_SCENARIO: A real-life cyber problem/victim situation.
    3. CYBER_EXPLAIN: A direct request for legal definitions (e.g. "Explain 70").
    4. NON_LEGAL: General/site/developer questions not asking cyber legal help.
    Respond with ONLY the category name.
    """
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": classifier_prompt}],
        "temperature": 0.0
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        raw = response.json()['choices'][0]['message']['content']
        return _normalize_intent_category(raw)
    except:
        return "PHYSICAL"

def ask_groq_lawyer(user_input, law_evidence, category):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    case_history = _justice_lens_case_history()

    legal_anchor = _justice_lens_legal_anchor()

    if "EXPLAIN" in category:
        system_prompt = f"""
        {legal_anchor}
        You are a Precise Legal Reference Tool.
        - Provide: OFFICIAL TITLE, DEFINITION, and EXACT PUNISHMENT.
        - STRICT RULE: DO NOT provide 'Win Probability', 'Action Plan', or 'Case History'.
        - Use the definitions exactly as provided in the INTERNAL REFERENCE.
        """
    else:
        dynamic_rules = _justice_lens_dynamic_scenario_rules(user_input)
        system_prompt = f"""
        {legal_anchor}
        {case_history}
        {_justice_lens_2026_scenario_logic()}
        {dynamic_rules}
        You are an Expert Cyber Law Consultant. Use this EXACT format:
         RELEVANT SECTIONS: [Cite sections]
         PUNISHMENTS: [List jail/compensation]
         CASE HISTORY: [Cite landmark case]
         WIN PROBABILITY: [Percentage] - [Reasoning]
        ACTION PLAN:
        1. (Golden Hour) If ANY money moved/was attempted (UPI/card/netbanking): report within 2 hours via 1930 or cybercrime.gov.in (CFCFRMS) and ask your bank to place a lien/freeze + block instruments; also report to bank within 5 days for compensation eligibility where applicable.
        2. Secure the breach immediately: change passwords, enable 2FA, revoke sessions/devices, reset UPI PINs, and monitor accounts to mitigate further harm.
        3. Preserve primary evidence for Section 65B: Email headers, UPI transaction IDs, URL metadata (full URL + redirects), screenshots/chats/call logs; then file the cybercrime.gov.in complaint and (if an organization) report to CERT-In within required timelines; consider a forensic auditor for large loss.
        """

    full_prompt = f"{system_prompt}\nUSER QUERY: {user_input}\nDATABASE EVIDENCE: {law_evidence}"

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.0
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=18)
        return response.json()['choices'][0]['message']['content']
    except:
        return "âš ï¸ AI Engine Error."

def _validate_ai_answer(category: str, answer: str) -> bool:
    if not answer or not isinstance(answer, str):
        return False

    upper = answer.upper()

    if "EXPLAIN" in str(category).upper():
        banned = ("WIN PROBABILITY", "ACTION PLAN", "CASE HISTORY")
        if any(x in upper for x in banned):
            return False
        required = ("DEFINITION", "PUNISH")
        return any(x in upper for x in required)

    required_sections = (
        "RELEVANT SECTIONS",
        "PUNISHMENTS",
        "CASE HISTORY",
        "WIN PROBABILITY",
        "ACTION PLAN",
    )
    return all(x in upper for x in required_sections)

def _repair_ai_answer(user_input: str, law_evidence: str, category: str, bad_answer: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    legal_anchor = _justice_lens_legal_anchor()

    category_upper = str(category).upper()
    if "EXPLAIN" in category_upper:
        repair_prompt = f"""
        {legal_anchor}
        You are a Precise Legal Reference Tool.
        Rewrite the following draft to STRICTLY comply:
        - Output ONLY these three fields, in this order:
          1) OFFICIAL TITLE:
          2) DEFINITION:
          3) EXACT PUNISHMENT:
        - Do NOT include: Win Probability, Action Plan, Case History, steps, URLs, or extra sections.
        - Use definitions and punishments exactly as provided in INTERNAL REFERENCE.

        USER QUERY: {user_input}
        DATABASE EVIDENCE: {law_evidence}
        DRAFT (FIX THIS): {bad_answer}
        """
    else:
        case_history = _justice_lens_case_history()
        dynamic_rules = _justice_lens_dynamic_scenario_rules(user_input)
        repair_prompt = f"""
        {legal_anchor}
        {case_history}
        {_justice_lens_2026_scenario_logic()}
        {dynamic_rules}
        Rewrite the following draft to STRICTLY follow this exact format (include all headings):
        RELEVANT SECTIONS: ...
        PUNISHMENTS: ...
        CASE HISTORY: ...
        WIN PROBABILITY: ...
        ACTION PLAN:
        1. ...
        2. ...
        3. ...

        USER QUERY: {user_input}
        DATABASE EVIDENCE: {law_evidence}
        DRAFT (FIX THIS): {bad_answer}
        """

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": repair_prompt}],
        "temperature": 0.0,
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=18)
        return response.json()["choices"][0]["message"]["content"]
    except Exception:
        return bad_answer

def ask_groq_lawyer_validated(user_input: str, law_evidence: str, category: str) -> str:
    answer = ask_groq_lawyer(user_input, law_evidence, category)
    if _validate_ai_answer(category, answer):
        return _apply_high_priority_refinements(user_input, category, answer)

    repaired = _repair_ai_answer(user_input, law_evidence, category, answer)
    final = repaired if _validate_ai_answer(category, repaired) else answer
    return _apply_high_priority_refinements(user_input, category, final)

# --- SIDEBAR UI ---
with st.sidebar:
    st.image(LOGO_SOURCE, use_container_width=True)
    
    if not st.session_state.user:
        auth_tab = st.tabs(["Login", "Create Account"])
        with auth_tab[0]:
            e_val = st.text_input("Email", key="login_email")
            p_val = st.text_input("Password", type="password", key="login_pass")
            if st.button(" Authenticate"):
                valid, u_obj = authenticate(e_val, p_val)
                if valid:
                    if check_ban(u_obj.uid): st.error("Access Forbidden.")
                    else:
                        st.session_state.user = {"name": u_obj.display_name or e_val.split('@')[0], "email": e_val, "uid": u_obj.uid}
                        st.session_state.view = "AI Assistant"
                        sync_user(st.session_state.user)
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
                except Exception as ex: st.error(str(ex))
                
        if st.button("Guest User"):
            gid = str(uuid.uuid4())[:8]
            st.session_state.user = {"name": f"Guest_{gid}", "email": "guest@justicelens.io", "uid": f"guest_{gid}"}
            st.rerun()

        st.markdown("---")
        st.caption("Resources")
        public_pages = ["AI Assistant", "About", "Terms", "Cyber Rules 2026"]
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
        st.markdown(f"Connected: **{st.session_state.user['name']}**")
        
        if st.session_state.user['email'] == "d3ztudio@gmail.com":
            st.markdown('<span style="color:var(--jl-primary); font-weight:800; font-size:0.7rem; letter-spacing:0.12em;">SYSTEM COMMANDER</span>', unsafe_allow_html=True)
            if not st.session_state.admin_mode:
                pin = st.text_input("PIN", type="password", placeholder="Enter PIN")
                if pin == "1923": 
                    st.session_state.admin_mode = True
                    st.rerun()
        
        opts = ["AI Assistant", "Vision & Mission", "About", "Terms", "Cyber Rules 2026"]
        if st.session_state.admin_mode: opts.append("Admin Dashboard")
        
        st.session_state.view = st.radio("NAVIGATION", [x.strip() for x in opts])
        
        st.markdown("---")
        if st.button("TERMINATE SESSION"):
            st.session_state.user = None
            st.session_state.admin_mode = False
            st.session_state.chat_history = []
            st.rerun()

# --- MAIN CONTENT ---
if not st.session_state.user:
    if st.session_state.view in ("About", "Terms", "Cyber Rules 2026"):
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
                        <h3 style="margin-top:0;">What this is</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                            Justice Lens is a cyber-law assistant designed to produce structured, scenario-ready legal summaries
                            (sections, punishments, case history, win probability, action plan) for common cyber incidents in India.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif st.session_state.view == "Terms":
                st.markdown(
                    """
                    <div class="jl-card">
                        <h3 style="margin-top:0;">Important</h3>
                        <ul>
                            <li>This is informational guidance, not a substitute for a licensed lawyer.</li>
                            <li>Verify timelines and requirements with your bank, platform, and current government notifications.</li>
                            <li>Do not share passwords, OTPs, or sensitive personal data in chat.</li>
                        </ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:  # Cyber Rules 2026
                st.markdown(
                    """
                    <div class="jl-card">
                        <h3 style="margin-top:0;">Cyber Rules 2026</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                            For active phishing portals or deepfake/SGI content, Justice Lens includes a takedown step referencing the
                            IT Amendment Rules 2026 and intermediary obligations to act within 3 hours on a valid order/notice to retain
                            Section 79 safe-harbor protections.
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

            st.write("")
            f1, f2, f3 = st.columns(3)
            with f1:
                st.markdown(
                    """
                    <div class="jl-feature">
                        <div class="kicker">Always On</div>
                        <div class="headline">24/7 Support</div>
                        <p class="desc">Rapid triage, evidence preservation, and next-step guidance when time matters.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with f2:
                st.markdown(
                    """
                    <div class="jl-feature">
                        <div class="kicker">Grounded</div>
                        <div class="headline">Verified Legal Logic</div>
                        <p class="desc">Responses structured around IT Act sections, punishments, and scenario-ready action plans.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with f3:
                st.markdown(
                    """
                    <div class="jl-feature">
                        <div class="kicker">Tactical</div>
                        <div class="headline">Incident Response</div>
                        <p class="desc">Golden-hour steps, takedowns, and escalation paths tailored to common cyber incidents.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.write("")
            cta_l, cta_m, cta_r = st.columns([2, 3, 2])
            with cta_m:
                if st.button("Start", key="start_researching_btn", use_container_width=True):
                    st.session_state.start_researching_flow = True
                    st.rerun()
            if st.session_state.start_researching_flow:
                st.markdown("### Login to Start Researching")
                entry_tabs = st.tabs(["Login", "Join"])
                with entry_tabs[0]:
                    me = st.text_input("Email", key="main_login_email")
                    mp = st.text_input("Password", type="password", key="main_login_pass")
                    if st.button("CONTINUE TO AI", key="main_login_btn"):
                        valid, u_obj = authenticate(me, mp)
                        if valid:
                            if check_ban(u_obj.uid):
                                st.error("Access Forbidden.")
                            else:
                                st.session_state.user = {
                                    "name": u_obj.display_name or me.split('@')[0],
                                    "email": me,
                                    "uid": u_obj.uid
                                }
                                st.session_state.view = "AI Assistant"
                                st.session_state.start_researching_flow = False
                                sync_user(st.session_state.user)
                                st.rerun()
                        else:
                            st.error("Invalid Credentials.")
                with entry_tabs[1]:
                    mnu = st.text_input("Full Name", key="main_signup_name")
                    meu = st.text_input("Email", key="main_signup_email")
                    mpu = st.text_input("Create Password", type="password", key="main_signup_pass")
                    if st.button("CREATE ACCOUNT", key="main_signup_btn"):
                        try:
                            auth.create_user(email=meu, password=mpu, display_name=mnu)
                            st.success("Account Ready! Use Login.")
                        except Exception as ex:
                            st.error(str(ex))
                if st.button("CONTINUE AS GUEST", key="main_guest_btn"):
                    gid = str(uuid.uuid4())[:8]
                    st.session_state.user = {
                        "name": f"Guest_{gid}",
                        "email": "guest@justicelens.io",
                        "uid": f"guest_{gid}"
                    }
                    st.session_state.view = "AI Assistant"
                    st.session_state.start_researching_flow = False
                    st.rerun()

else:
    page = st.session_state.view
    if page == "AI Assistant":
        # --- PROJECTS (lightweight, UI-only) ---
        if "projects" not in st.session_state:
            # Migrate existing chat_history into a default project
            existing = list(st.session_state.chat_history) if st.session_state.get("chat_history") else []
            st.session_state.projects = {"Default": existing}
        if "active_project" not in st.session_state:
            st.session_state.active_project = "Default"
        if st.session_state.active_project not in st.session_state.projects:
            st.session_state.projects[st.session_state.active_project] = []

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

            if category == "PHYSICAL":
                ans = "⚠️ This tool handles cyber crimes only. For other types of crimes, file an FIR under IPC."
            elif category == "NON_LEGAL":
                ans = (
                    "ℹ️ I can only help with cyber-law topics (IT Act / cybercrime). "
                    "Ask a legal question about a cyber issue and I’ll help."
                )
            else:
                with st.spinner("Querying legal database..."):
                    dataset_evidence = "General context."
                    try:
                        idx, emb = get_backend()
                        if idx and emb:
                            v = emb.embed_query(user_msg)
                            m = idx.query(vector=v, top_k=5, include_metadata=True)
                            dataset_evidence = " ".join(
                                [x.get("metadata", {}).get("text", "") for x in m.get("matches", [])]
                            ) or "General context."
                    except Exception:
                        pass

                with st.spinner("Generating legal report..."):
                    ans = ask_groq_lawyer_validated(user_msg, dataset_evidence, category)

            history.append({"role": "assistant", "content": ans})

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
        _, clear_col = st.columns([5, 1])
        with clear_col:
            if st.button("Clear chat", use_container_width=True):
                history.clear()
                st.rerun()

        with st.container():
            st.markdown(
                """
                <div class="jl-hero">
                    <div class="title">Justice Lens</div>
                    <div class="subtitle">Professional cyber-law assistant for scenarios and IT Act references.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        g1, g2, g3 = st.columns(3)
        with g1:
            st.markdown(
                """
                <div class="jl-feature">
                    <div class="kicker">Always On</div>
                    <div class="headline">24/7 Support</div>
                    <p class="desc">Fast guidance for reporting, preserving evidence, and immediate containment.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with g2:
            st.markdown(
                """
                <div class="jl-feature">
                    <div class="kicker">Grounded</div>
                    <div class="headline">Verified Legal Logic</div>
                    <p class="desc">Structured outputs: relevant sections, punishments, case history, win probability, action plan.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with g3:
            st.markdown(
                """
                <div class="jl-feature">
                    <div class="kicker">Tactical</div>
                    <div class="headline">Incident Response</div>
                    <p class="desc">Golden-hour steps and escalation paths (bank, cyber cell, intermediaries).</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        main_col, right_col = st.columns([4, 1], gap="large")

        # Right panel (Projects)
        with right_col:
            st.markdown("### Projects")
            new_name = st.text_input("New project", placeholder="e.g. Incident Notes", key="jl_new_project")
            if st.button("Create", use_container_width=True, key="jl_create_project"):
                name = (new_name or "").strip()
                if name and name not in st.session_state.projects:
                    st.session_state.projects[name] = []
                    st.session_state.active_project = name
                    st.rerun()

            project_names = list(st.session_state.projects.keys())
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
                    key="jl_project_radio",
                )
                if chosen != st.session_state.active_project:
                    st.session_state.active_project = chosen
                    st.rerun()

            st.markdown("---")
            st.caption("Tip: Use Projects to separate different incident chats.")

        # Main chat area
        with main_col:
            # Welcome tiles when empty
            if not history:
                st.markdown("""
                    <div class="jl-card" style="text-align:center;">
                        <h2 style="margin:0;">Welcome</h2>
                        <p style="margin:0.35rem 0 0; color: var(--jl-muted) !important; font-weight:600;">Start with a scenario or ask for an IT Act section explanation.</p>
                    </div>
                """, unsafe_allow_html=True)

                t1, t2 = st.columns(2)
                with t1:
                    if st.button("Report UPI scam", use_container_width=True):
                        st.session_state.jl_pending_msg = "I was scammed via UPI. What sections apply?"
                        st.rerun()
                    if st.button("Account hacked", use_container_width=True):
                        st.session_state.jl_pending_msg = "My account was hacked and my data leaked. What should I do?"
                        st.rerun()
                with t2:
                    if st.button("Explain Section 66F", use_container_width=True):
                        st.session_state.jl_pending_msg = "Explain Section 66F"
                        st.rerun()
                    if st.button("Privacy violation", use_container_width=True):
                        st.session_state.jl_pending_msg = "Someone posted my private photos without consent. What are the punishments?"
                        st.rerun()

            # Process any pending message (from tiles)
            pending = st.session_state.pop("jl_pending_msg", None)
            if pending:
                _handle_user_message(pending)
                st.rerun()

            for chat in history:
                role = "user" if chat.get("role") == "user" else "assistant"
                with st.chat_message(role):
                    st.markdown(chat.get("content", ""))

            user_msg = st.chat_input("Describe a cyber incident, or ask e.g. “Explain Section 66F”")
            if user_msg:
                _handle_user_message(user_msg)
                st.rerun()

    elif page == "Vision & Mission":
        st.title("Our Core Principles")
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("""<div class="jl-card"><h3 style="margin-top:0;">Our Vision</h3><p style="color: var(--jl-muted) !important;">To make cyber-law guidance accessible and actionable for every citizen.</p></div>""", unsafe_allow_html=True)
        with v2:
            st.markdown("""<div class="jl-card"><h3 style="margin-top:0;">Our Mission</h3><p style="color: var(--jl-muted) !important;">Use AI + retrieval to translate cyber provisions into structured, cited, scenario-ready steps.</p></div>""", unsafe_allow_html=True)

    elif page == "About":
        st.title("About")
        st.markdown(
            """
            <div class="jl-card">
                <h3 style="margin-top:0;">Justice Lens</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    A cyber-law assistant that generates structured outputs (sections, punishments, case history, win probability,
                    action plan) and emphasizes evidence preservation and escalation paths.
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
                <ul>
                    <li>This tool provides informational guidance only and is not legal advice.</li>
                    <li>For emergencies or high-stakes matters, consult a qualified lawyer and contact authorities.</li>
                    <li>Avoid sharing passwords, OTPs, card CVV, or sensitive personal data in chat.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif page == "Cyber Rules 2026":
        st.title("Cyber Rules 2026")
        st.markdown(
            """
            <div class="jl-card">
                <h3 style="margin-top:0;">Intermediary takedown (2026)</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    When a scenario involves an active phishing portal or deepfake/SGI content, the assistant includes a takedown step
                    referencing the IT Amendment Rules 2026 and the 3-hour removal expectation for intermediaries on a valid order/notice,
                    tied to Section 79 safe-harbor.
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

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Total Users", total_users)
            s2.metric("Active Users", active_users)
            s3.metric("Banned Users", banned_users)
            s4.metric("Guest Users", guest_users)

            f1, f2 = st.columns([2, 1])
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
                    "DOWNLOAD USER LIST (CSV)",
                    data=export_df.to_csv(index=False),
                    file_name="justice_lens_users.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            st.markdown("### User Directory")
            if not filtered_users:
                st.info("No users match the current filter.")
            for ud in filtered_users:
                last_active = format_app_time(ud["last_active"], '%d %b, %H:%M IST')
                status_color = "#ef4444" if ud["is_banned"] else "#22c55e"

                st.markdown(f"""
                    <div class="admin-data-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div><b>{ud['name']}</b><p>{ud['email']}</p><p>Last Active: {last_active}</p></div>
                            <div><span class="status-badge" style="background:{status_color}; color:white !important;">{'BANNED' if ud['is_banned'] else 'ACTIVE'}</span></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    b_label = "UNBAN" if ud["is_banned"] else "BAN"
                    if st.button(b_label, key=f"ban_{ud['doc_id']}"):
                        u_ref.document(ud["doc_id"]).update({"is_banned": not ud["is_banned"]})
                        st.rerun()
                with c_btn2:
                    if st.button("DELETE", key=f"del_{ud['doc_id']}"):
                        try:
                            auth.delete_user(ud["doc_id"])
                        except:
                            pass
                        try:
                            u_ref.document(ud["doc_id"]).delete()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.error("Database not available.")
                    
