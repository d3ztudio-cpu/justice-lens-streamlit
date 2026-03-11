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
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings

# ==========================================
# ⚙️ CONFIGURATION & API KEYS
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
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- PREMIUM NEAT & LOGO-MATCHED UI (Navy & Gold) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
    
    :root {
        --bg: #071228;
        --bg-soft: #0D1B35;
        --panel: #0F1F3D;
        --panel-2: #13274B;
        --text: #E6EEFF;
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
            linear-gradient(180deg, #061022 0%, #091730 45%, #08162D 100%) !important;
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
        background: #0E2448 !important;
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
        border-radius: 11px !important;
        padding: 0.58rem 0.76rem !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="input"] {
        align-items: center !important;
        border-radius: 11px !important;
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
        color: #0A1A37 !important;
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
            font-size: 0.7rem !important;
            padding: 0.5rem 0.7rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- BOOTSTRAP / INITIALIZATION ---
@st.cache_resource(show_spinner=False)
def init_backend():
    try:
        splash = st.empty()
        with splash.container():
            st.markdown(f"""
                <div style="text-align:center; padding:80px 20px; background:white; border-radius:1rem; border:1px solid var(--border); margin: 50px auto; max-width: 600px; box-shadow: 0 10px 40px rgba(0,0,0,0.05);">
                    <h2 style="color:#0F172A; margin-bottom:10px; font-weight:900;">⚖️ JUSTICE LENS</h2>
                    <p style="color:#C5A059; font-weight: 700; margin-bottom: 25px; font-size: 0.95rem; letter-spacing: 1px;">ESTABLISHING SECURE CONNECTION...</p>
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
if "view" not in st.session_state: st.session_state.view = "🤖 AI Lawyer"
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
        return response.json()['choices'][0]['message']['content'].strip().upper()
    except:
        return "PHYSICAL"

def ask_groq_lawyer(user_input, law_evidence, category):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    case_history = """
    HISTORICAL PRECEDENTS (USE FOR SCENARIOS):
    - Hacking/Unauthorized Access: State of Tamil Nadu vs. Suhas Katti (2004).
    - Data Negligence: Shreya Singhal vs. Union of India (2015).
    - Financial Fraud: CBI vs. Arif Azim (Sony Sambandh Case).
    """

    legal_anchor = """
    INTERNAL REFERENCE (ABSOLUTE TRUTH):
    - Section 70: Protected Systems. Definition: Unauthorized access to systems declared as critical infrastructure by the Government. Punishment = Up to 10 years.
    - Section 67A: Sexually Explicit Content. Definition: Publishing or transmitting material containing sexually explicit acts in electronic form. Punishment = 5-7 years + 10 Lakh fine.
    - Section 66F: Cyber Terrorism. Definition: Acts done with intent to threaten unity, integrity, or security of India via computer. Punishment = LIFE IMPRISONMENT.
    - Section 66E: Violation of Privacy. Definition: Intentionally capturing or publishing private images of any person without consent. Punishment = 3 years / 2 Lakh fine.
    - Section 43A: Corporate Data Negligence. Definition: Failure by a body corporate to implement reasonable security practices for sensitive data. Punishment = Compensation ONLY.
    - Section 66B: Stolen Computer Resource. Punishment = 3 years / 5 Lakh fine.
    """

    if "EXPLAIN" in category:
        system_prompt = f"""
        {legal_anchor}
        You are a Precise Legal Reference Tool.
        - Provide: OFFICIAL TITLE, DEFINITION, and EXACT PUNISHMENT.
        - STRICT RULE: DO NOT provide 'Win Probability', 'Action Plan', or 'Case History'.
        - Use the definitions exactly as provided in the INTERNAL REFERENCE.
        """
    else:
        system_prompt = f"""
        {legal_anchor}
        {case_history}
        You are an Expert Cyber Law Consultant. Use this EXACT format:
        ⚖️ RELEVANT SECTIONS: [Cite sections]
        ⚖️ PUNISHMENTS: [List jail/compensation]
        📚 CASE HISTORY: [Cite landmark case]
        📊 WIN PROBABILITY: [Percentage] - [Reasoning]
        🚀 ACTION PLAN:
        1. Notify CERT-In (www.cert-in.org.in) within 6 hours.
        2. File complaint at www.cybercrime.gov.in.
        3. Appoint a Cyber Forensic Auditor.
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
        return "⚠️ AI Engine Error."

# --- SIDEBAR UI ---
with st.sidebar:
    st.image(LOGO_SOURCE, use_container_width=True)
    
    if not st.session_state.user:
        auth_tab = st.tabs(["Login", "Create Account"])
        with auth_tab[0]:
            e_val = st.text_input("Email", key="login_email")
            p_val = st.text_input("Password", type="password", key="login_pass")
            if st.button("AUTHENTICATE"):
                valid, u_obj = authenticate(e_val, p_val)
                if valid:
                    if check_ban(u_obj.uid): st.error("Access Forbidden.")
                    else:
                        st.session_state.user = {"name": u_obj.display_name or e_val.split('@')[0], "email": e_val, "uid": u_obj.uid}
                        st.session_state.view = "🤖 AI Lawyer"
                        sync_user(st.session_state.user)
                        st.rerun()
                else: st.error("Invalid Credentials.")
        
        with auth_tab[1]:
            nu = st.text_input("Full Name")
            eu = st.text_input("Email", key="s_email")
            pu = st.text_input("Create Password", type="password", key="s_pass")
            if st.button("REGISTER"):
                try:
                    auth.create_user(email=eu, password=pu, display_name=nu)
                    st.success("Account Ready! Use Login.")
                except Exception as ex: st.error(str(ex))
                
        if st.button("👤 Continue as Guest"):
            gid = str(uuid.uuid4())[:8]
            st.session_state.user = {"name": f"Guest_{gid}", "email": "guest@justicelens.io", "uid": f"guest_{gid}"}
            st.rerun()
    else:
        st.markdown(f"👤 Connected: **{st.session_state.user['name']}**")
        
        if st.session_state.user['email'] == "d3ztudio@gmail.com":
            st.markdown('<span style="color:#C5A059; font-weight:900; font-size:0.7rem; letter-spacing:1px;">[ SYSTEM COMMANDER ]</span>', unsafe_allow_html=True)
            if not st.session_state.admin_mode:
                pin = st.text_input("PIN", type="password", placeholder="Enter PIN")
                if pin == "1923": 
                    st.session_state.admin_mode = True
                    st.rerun()
        
        opts = ["🤖 AI Lawyer", "Vision & Mission"]
        if st.session_state.admin_mode: opts.append("🚨 Admin Dashboard")
        
        st.session_state.view = st.radio("CORE PORTAL", opts)
        
        st.markdown("---")
        if st.button("TERMINATE SESSION"):
            st.session_state.user = None
            st.session_state.admin_mode = False
            st.session_state.chat_history = []
            st.rerun()

# --- MAIN CONTENT ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        l1, l2, l3 = st.columns([1, 2, 1])
        with l2:
            st.image(LOGO_SOURCE, width=300)
        st.markdown("""
            <div class="glass-card hero-panel" style="text-align: center;">
                <h1 style="color:#EAF2FF !important;">Justice Lens</h1>
                <p style="color:#C5A059 !important; font-weight:700; font-size:1rem; letter-spacing:2px; margin-top:-10px;">SECURE AI CYBER LEGAL DEFENSE</p>
                <div class="light-panel" style="background:rgba(255,255,255,0.92); padding:2rem; border-radius:1rem; border:1px solid #BBD3F3; text-align:left; margin: 2rem 0;">
                    <h3 style="margin-top:0;">Expert Advocacy</h3>
                    <p>Protect your digital footprint under the <b>Indian IT Act 2000</b>. Our engine provides instant legal reports using context-aware AI retrieval.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        cta_l, cta_m, cta_r = st.columns([2, 3, 2])
        with cta_m:
            if st.button("START RESEARCHING", key="start_researching_btn"):
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
                            st.session_state.view = "🤖 AI Lawyer"
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
                st.session_state.view = "🤖 AI Lawyer"
                st.session_state.start_researching_flow = False
                st.rerun()

else:
    page = st.session_state.view

    if page == "🤖 AI Lawyer":
        st.title("⚖️ Expert AI Consultation")
        st.markdown('<div class="chat-container"><div class="bubble-container">', unsafe_allow_html=True)
        if not st.session_state.chat_history:
            st.markdown('<div style="display:flex;flex-direction:column;align-items:flex-start;"><div class="role-label">JUSTICE LENS</div><div class="chat-bubble ai-bubble">Describe your cybercrime scenario (e.g., fraudulent banking, social media threat) for a legal breakdown.</div></div>', unsafe_allow_html=True)
        
        for chat in st.session_state.chat_history:
            side = "flex-end" if chat["role"] == "user" else "flex-start"
            lbl = "YOU" if chat["role"] == "user" else "JUSTICE LENS"
            bub = "user-bubble" if chat["role"] == "user" else "ai-bubble"
            st.markdown(f'''
                <div style="display:flex; flex-direction:column; align-items: {side}; width: 100%;">
                    <div class="role-label">{lbl}</div>
                    <div class="chat-bubble {bub}">{chat["content"]}</div>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        with st.form("query_form", clear_on_submit=True):
            user_msg = st.text_input("Enter scenario...", placeholder="Describe situation here...")
            if st.form_submit_button("ANALYZE LEGAL CONTEXT"):
                if user_msg:
                    st.session_state.chat_history.append({"role": "user", "content": user_msg})
                    with st.spinner("Analyzing Scope..."):
                        category = get_intent_category(user_msg)
                        if "PHYSICAL" in category:
                            ans = "⚠️ This tool handles Cyber Crimes only. For physical theft, file an FIR under IPC."
                        elif "NON_LEGAL" in category:
                            ans = (
                                "ℹ️ Sorry, I don't have that information. Could you please provide more context about your cyber crime query?"
                            )
                        else:
                            with st.spinner("Querying Legal Database..."):
                                dataset_evidence = "General context."
                                try:
                                    idx, emb = get_backend()
                                    if idx and emb:
                                        v = emb.embed_query(user_msg)
                                        m = idx.query(vector=v, top_k=5, include_metadata=True)
                                        dataset_evidence = " ".join(
                                            [x.get('metadata', {}).get('text', '') for x in m.get('matches', [])]
                                        ) or "General context."
                                except:
                                    pass
                                ans = ask_groq_lawyer(user_msg, dataset_evidence, category)
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    if db:
                        db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("logs").add({
                            "uid": st.session_state.user['uid'], "user": st.session_state.user['name'],
                            "query": user_msg, "report": ans, "timestamp": utc_now()
                        })
                    st.rerun()

    elif page == "Vision & Mission":
        st.title("📖 Our Core Principles")
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("""<div class="glass-card"><h3 style="color:#C5A059 !important;">Our Vision</h3><p>To establish a digital fortress in India where legal intelligence is accessible to every citizen.</p></div>""", unsafe_allow_html=True)
        with v2:
            st.markdown("""<div class="glass-card"><h3 style="color:#C5A059 !important;">Our Mission</h3><p>Utilizing AI to translate complex legislative acts into actionable, cited legal reports for the public.</p></div>""", unsafe_allow_html=True)

    elif page == "🚨 Admin Dashboard" and st.session_state.admin_mode:
        st.title("🚨 System Oversight")
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

            st.markdown("### 👥 User Directory")
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
                    b_label = "✅ UNBAN" if ud["is_banned"] else "🚫 BAN"
                    if st.button(b_label, key=f"ban_{ud['doc_id']}"):
                        u_ref.document(ud["doc_id"]).update({"is_banned": not ud["is_banned"]})
                        st.rerun()
                with c_btn2:
                    if st.button("🗑️ DELETE", key=f"del_{ud['doc_id']}"):
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
                    
