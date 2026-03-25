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
import urllib.parse
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
import streamlit.components.v1 as components

# ==========================================
# ⚙️ CONFIGURATION & API KEYS
# ==========================================
PINECONE_KEY = st.secrets.get("PINECONE_KEY", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
FIREBASE_WEB_API_KEY = st.secrets.get("FIREBASE_WEB_API_KEY", "AIzaSyAklh23Fu6-P5vNsGDh2-U9titgRvqzJaU")
INDEX_NAME = "justice-lens"
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
        initial_sidebar_state="collapsed",
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

    /* Remove Streamlit header/toolbar (removes default toggle & deployment chrome) */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    /* Permanently fix sidebar by hiding the collapse controls */
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
    }

    section[data-testid="stSidebar"]{
        position: fixed !important;
        top: 0;
        left: 0;
        height: 100vh !important;
        width: min(320px, 85vw) !important;
        transform: translateX(-105%);
        transition: transform 0.22s ease;
        z-index: 9999;
        box-shadow: var(--jl-shadow);
    }
    body.jl-sidebar-open section[data-testid="stSidebar"]{
        transform: translateX(0);
    }
    .jl-sidebar-overlay{
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.55);
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s ease;
        z-index: 9998;
    }
    body.jl-sidebar-open .jl-sidebar-overlay{
        opacity: 1;
        pointer-events: auto;
    }

    .jl-hamburger{
        display: none;
        width: 40px;
        height: 40px;
        border-radius: 10px;
        border: 1px solid var(--jl-border);
        background: var(--jl-card);
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: var(--jl-shadow-sm);
    }
    .jl-hamburger span{
        display: block;
        width: 20px;
        height: 2px;
        background: var(--jl-text);
        margin: 3px 0;
        border-radius: 2px;
    }

    @media (max-width: 991px){
        .jl-hamburger{
            display: flex;
            position: fixed;
            top: 0.9rem;
            left: 0.9rem;
            z-index: 9501;
        }
    }
    @media (min-width: 992px){
        .jl-sidebar-overlay{ display: none; }
    }
    .main .block-container{
        padding-top: 5.5rem !important;
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

    @media (max-width: 700px){
        .jl-hero .title{ font-size: 1.65rem; }
        .main .block-container{ padding-left: 0.9rem !important; padding-right: 0.9rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "jl_open_sidebar" not in st.session_state:
    st.session_state.jl_open_sidebar = False

if "view" not in st.session_state:
    st.session_state.view = "AI Assistant"

st.markdown(
    """
    <button class="jl-hamburger" data-jl-toggle-sidebar aria-label="Open menu">
        <span></span>
        <span></span>
        <span></span>
    </button>
    """,
    unsafe_allow_html=True,
)

_autopen = "true" if st.session_state.jl_open_sidebar else "false"
components.html(
    f"""
    <div class="jl-sidebar-overlay" data-jl-close-sidebar></div>
    <div data-jl-autopen="{_autopen}" style="display:none;"></div>
    <script>
    (function() {{
        if (window.__jlSidebarInit) return;
        window.__jlSidebarInit = true;
        const body = document.body;
        const OPEN_CLASS = "jl-sidebar-open";
        const openSidebar = () => body.classList.add(OPEN_CLASS);
        const closeSidebar = () => body.classList.remove(OPEN_CLASS);
        const toggleSidebar = () => body.classList.toggle(OPEN_CLASS);
        const stripDefaultToggle = () => {{
            const candidates = Array.from(document.querySelectorAll("button, span, div"));
            candidates.forEach((el) => {{
                const txt = (el.textContent || "").trim();
                if (txt === "double_arrow_right" || txt === "double_arrow_left") {{
                    const btn = el.closest("button");
                    if (btn) {{
                        btn.remove();
                    }} else {{
                        el.remove();
                    }}
                }}
            }});
        }};
        const observeAndStrip = () => {{
            const mo = new MutationObserver(() => stripDefaultToggle());
            mo.observe(document.documentElement, {{ childList: true, subtree: true }});
        }};
        document.addEventListener("click", (e) => {{
            const toggleBtn = e.target.closest("[data-jl-toggle-sidebar]");
            const openBtn = e.target.closest("[data-jl-open-sidebar]");
            const closeBtn = e.target.closest("[data-jl-close-sidebar]");
            const sidebarEl = document.querySelector('section[data-testid="stSidebar"]');
            const clickedInsideSidebar = sidebarEl && sidebarEl.contains(e.target);
            if (toggleBtn) {{
                e.preventDefault();
                toggleSidebar();
                return;
            }}
            if (body.classList.contains(OPEN_CLASS) && !clickedInsideSidebar && !openBtn && !closeBtn) {{
                closeSidebar();
                return;
            }}
            if (openBtn) {{
                e.preventDefault();
                openSidebar();
                return;
            }}
            if (closeBtn) {{
                e.preventDefault();
                closeSidebar();
            }}
        }});

        const maybeAutoOpen = () => {{
            const autoEl = document.querySelector('[data-jl-autopen="true"]');
            if (autoEl) {{
                openSidebar();
            }}
        }};
        setTimeout(() => {{
            stripDefaultToggle();
            observeAndStrip();
            maybeAutoOpen();
        }}, 0);
        setTimeout(stripDefaultToggle, 500);
    }})();
    </script>
    """,
    height=0,
    width=0,
)
if st.session_state.jl_open_sidebar:
    st.session_state.jl_open_sidebar = False

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
        return "⚠️ AI Engine Error."

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
        st.markdown(
            f"<div class='jl-sidebar-connected'>Connected to: <b>{st.session_state.user['name']}</b></div>",
            unsafe_allow_html=True,
        )
        
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
                            <li><strong>Database Retrieval:</strong> It then queries its legal knowledge base, which includes statutory provisions, landmark case law, and dynamic rules updated for 2026, to find the most relevant legal precedents and sections.</li>
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
            else:  # Cyber Rules 2026
                st.markdown(
                    """
                    <div class="jl-card">
                        <h3 style="margin-top:0;">Intermediary Takedown & The 2026 Rules</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                            The "Cyber Rules 2026" is our internal designation for critical legal updates that Justice Lens applies to relevant scenarios, particularly those involving harmful user-generated content online.
                        </p>
                        <h3 style="margin-top:1.5rem;">Key Provision: Intermediary Liability</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                           A core component of these rules is the assistant's handling of scenarios involving active phishing websites, deepfakes, or other forms of "Synthetically Generated Information" (SGI).
                        </p>
                        <ul style="color: var(--jl-muted) !important;">
                            <li><strong>The Law:</strong> Based on amendments to the IT Rules, online platforms like social media networks and hosting providers ("intermediaries") have specific obligations.</li>
                            <li><strong>"Safe Harbor":</strong> Under Section 79 of the IT Act, these intermediaries are granted "safe harbor," which protects them from liability for content posted by their users.</li>
                            <li><strong>The Condition:</strong> To maintain this protection, they must promptly remove unlawful content upon receiving a valid order from a court or government agency. The 2026 ruleset assumes a strict 3-hour timeline for takedown of certain harmful content to avoid liability.</li>
                        </ul>
                         <h3 style="margin-top:1.5rem;">Justice Lens's Analysis</h3>
                        <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                           When the AI detects a relevant scenario, its Action Plan will include a step referencing the IT Amendment Rules 2026. This step advises the user on issuing a takedown notice to the intermediary, highlighting the platform's obligation to remove such material within a very short timeframe to retain their safe harbor status.
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

            btn_l, btn_m, btn_r = st.columns([3, 2, 3])
            with btn_m:
                if st.button("LOGIN", key="jl_login_btn", use_container_width=True):
                    st.session_state.jl_open_sidebar = True
                    st.rerun()

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
                    <div class="headline">24/7 Incident Support</div>
                    <p class="desc">Get immediate, automated guidance for reporting cybercrimes, preserving critical digital evidence, and containing the incident to prevent further harm.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with g2:
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
        with g3:
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

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        main_col, right_col = st.columns([4, 1], gap="large")

        # Right panel (Projects)
        with right_col:
            with st.container(border=True):
                st.markdown("### Chats")
                new_name = st.text_input("New Chats", placeholder="e.g. Incident Notes", key="jl_new_project")
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

                st.caption("Tip: Use Chats to separate different incident chats.")

        # Main chat area
        with main_col:
            # Welcome tiles when empty
            if not history:
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

            for chat in history:
                role = "user" if chat.get("role") == "user" else "assistant"
                avatar = "🧑‍💼" if role == "user" else "⚖️"
                with st.chat_message(role, avatar=avatar):
                    content = chat.get("content", "")
                    st.markdown(content)
                    if role == "assistant" and content:
                        encoded_content = urllib.parse.quote(content)
                        translate_url = f"https://translate.google.com/?sl=auto&text={encoded_content}"
                        st.markdown(f'<a href="{translate_url}" target="_blank" style="text-decoration: none; color: #8B949E; font-size: 0.9em;">Translate</a>', unsafe_allow_html=True)

            user_msg = st.chat_input("Describe a cyber incident, or ask e.g. “Explain Section 66F”")
            if user_msg:
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
                    <li><strong>Database Retrieval:</strong> It then queries its legal knowledge base, which includes statutory provisions, landmark case law, and dynamic rules updated for 2026, to find the most relevant legal precedents and sections.</li>
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

    elif page == "Cyber Rules 2026":
        st.title("Cyber Rules 2026")
        st.markdown(
            """
            <div class="jl-card">
                <h3 style="margin-top:0;">Intermediary Takedown & The 2026 Rules</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                    The "Cyber Rules 2026" is our internal designation for critical legal updates that Justice Lens applies to relevant scenarios, particularly those involving harmful user-generated content online.
                </p>
                <h3 style="margin-top:1.5rem;">Key Provision: Intermediary Liability</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                   A core component of these rules is the assistant's handling of scenarios involving active phishing websites, deepfakes, or other forms of "Synthetically Generated Information" (SGI).
                </p>
                <ul style="color: var(--jl-muted) !important;">
                    <li><strong>The Law:</strong> Based on amendments to the IT Rules, online platforms like social media networks and hosting providers ("intermediaries") have specific obligations.</li>
                    <li><strong>"Safe Harbor":</strong> Under Section 79 of the IT Act, these intermediaries are granted "safe harbor," which protects them from liability for content posted by their users.</li>
                    <li><strong>The Condition:</strong> To maintain this protection, they must promptly remove unlawful content upon receiving a valid order from a court or government agency. The 2026 ruleset assumes a strict 3-hour timeline for takedown of certain harmful content to avoid liability.</li>
                </ul>
                 <h3 style="margin-top:1.5rem;">Justice Lens's Analysis</h3>
                <p style="color: var(--jl-muted) !important; margin-bottom:0;">
                   When the AI detects a relevant scenario, its Action Plan will include a step referencing the IT Amendment Rules 2026. This step advises the user on issuing a takedown notice to the intermediary, highlighting the platform's obligation to remove such material within a very short timeframe to retain their safe harbor status.
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
                    info_col, ban_col, del_col = st.columns([4, 1, 1])
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
        else:
            st.error("Database not available.")
                    
