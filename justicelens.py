import streamlit as st
import pandas as pd
from datetime import datetime
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* 1. THEME VARIABLES */
    :root {
        --navy: #0F172A;
        --gold: #C5A059;
        --slate: #1E293B;
        --border: #E2E8F0;
        --bg-light: #F8FAFC;
    }

    /* 2. TEXT VISIBILITY FIX */
    /* Force Navy for content, but allow white for buttons */
    html, body, [data-testid="stMarkdownContainer"] p, 
    .stMarkdown, label, li, h1, h2, h3 { 
        font-family: 'Inter', sans-serif !important;
        color: var(--navy) !important; 
    }
    
    .stApp { background: #FFFFFF; }

    /* 3. SIDEBAR TOGGLE & ICON CLEANUP */
    [data-testid="stSidebarCollapseButton"] button, 
    [data-testid="stHeader"] button {
        background-color: transparent !important;
        border: none !important;
        position: relative !important;
    }

    /* Target and hide the glitchy icon text labels permanently */
    [data-testid="stSidebarCollapseButton"] button div p, 
    [data-testid="stHeader"] button div p,
    [data-testid="stExpander"] summary div p,
    span:contains("keyboard_"),
    div:contains("keyboard_"),
    span:contains("arrow_right"),
    div:contains("arrow_right") {
        font-size: 0px !important;
        color: transparent !important;
        display: none !important;
        visibility: hidden !important;
    }

    [data-testid="stSidebarCollapseButton"] button::before {
        content: '<<';
        color: #FFFFFF !important;
        font-weight: 900 !important;
        font-size: 1.2rem !important;
        visibility: visible !important;
    }

    [data-testid="stHeader"] button::before {
        content: '>>';
        color: var(--navy) !important;
        font-weight: 900 !important;
        font-size: 1.2rem !important;
        visibility: visible !important;
    }

    /* 4. HIDE STREAMLIT BRANDING */
    [data-testid="stStatusWidget"], .st-emotion-cache-zt53z0 {
        display: none !important;
        visibility: hidden !important;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0) !important;
        border: none !important;
    }

    /* 5. SIDEBAR DESIGN */
    section[data-testid="stSidebar"] {
        background-color: var(--navy) !important;
        border-right: 1px solid var(--slate);
    }
    section[data-testid="stSidebar"] * { 
        color: #FFFFFF !important; 
        font-size: 0.85rem !important; 
    }
    div[data-testid="stSidebarUserContent"] .st-at {
        background-color: var(--gold) !important;
        border-radius: 6px;
    }

    /* 6. NEAT COMPONENTS */
    .glass-card {
        background: #FFFFFF !important;
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid var(--border);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    h1 { font-size: 2rem !important; font-weight: 800 !important; }
    h2 { font-size: 1.3rem !important; font-weight: 700 !important; margin-bottom: 0.8rem !important; }
    h3 { font-size: 1rem !important; font-weight: 700 !important; color: var(--gold) !important; margin-top: 0 !important; }

    /* 7. THEMED BUTTONS - CRITICAL VISIBILITY FIX */
    .stButton > button {
        width: 100%; border-radius: 6px; border: none; padding: 0.5rem 1rem;
        font-weight: 700; background: var(--navy);
        color: #FFFFFF !important; /* Force White Text */
        transition: 0.3s;
        text-transform: uppercase; letter-spacing: 1px;
        font-size: 0.75rem !important;
    }
    .stButton > button:hover { 
        background: var(--gold); 
        color: #FFFFFF !important;
        transform: translateY(-1px); 
    }

    /* 8. ELITE CHAT INTERFACE */
    .chat-container {
        max-width: 900px; margin: 0 auto;
        padding: 1.5rem; background: #FFFFFF; border-radius: 1rem;
    }
    .bubble-container { display: flex; flex-direction: column; gap: 1.2rem; }
    .chat-bubble {
        padding: 1rem 1.4rem; border-radius: 1.25rem; font-size: 0.95rem; line-height: 1.5;
        max-width: 85%; box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .user-bubble {
        background: var(--navy); color: #FFFFFF !important;
        align-self: flex-end; border-bottom-right-radius: 4px;
    }
    .ai-bubble {
        background: var(--bg-light); color: var(--navy) !important;
        align-self: flex-start; border-bottom-left-radius: 4px;
        border: 1px solid var(--border);
    }
    .role-label { 
        font-size: 0.6rem; font-weight: 900; color: var(--gold) !important; 
        margin-bottom: 3px; text-transform: uppercase; letter-spacing: 2px;
    }

    /* 9. ADMIN DASHBOARD CARDS */
    .admin-data-card {
        background: white !important; border: 1px solid var(--border) !important;
        border-radius: 12px; padding: 1.25rem; margin-bottom: 0.8rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    .admin-data-card b, .admin-data-card p { color: var(--navy) !important; }
    .admin-data-card p { margin: 0; font-size: 0.8rem !important; opacity: 0.8; }
    
    .status-badge {
        font-weight: 800; font-size: 0.65rem; padding: 2px 8px; border-radius: 4px;
        color: white !important;
    }

    /* 10. PROGRESS BAR */
    .stProgress > div > div > div > div { background-color: var(--gold) !important; }
    
    /* Expander visibility fix */
    [data-testid="stExpander"] summary p { 
        font-weight: 700 !important; 
        color: var(--navy) !important; 
        font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BOOTSTRAP / INITIALIZATION ---
@st.cache_resource
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
pinecone_index, legal_embeddings = init_backend()

# --- SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "admin_mode" not in st.session_state: st.session_state.admin_mode = False
if "view" not in st.session_state: st.session_state.view = "🤖 AI Lawyer"

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
                "last_active": datetime.now(),
                "is_banned": user_data.get('is_banned', False)
            }, merge=True)
        except: pass

def check_ban(uid):
    if not db: return False
    doc = db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("users").document(uid).get()
    return doc.to_dict().get("is_banned", False) if doc.exists else False

# --- AI LOGIC ---
def get_scope(text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Respond ONLY 'CYBER' or 'PHYSICAL'. Online scams = CYBER. Physical theft = PHYSICAL."},
            {"role": "user", "content": text}
        ], "temperature": 0.0
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=8)
        return res.json()['choices'][0]['message']['content'].strip().upper()
    except: return "PHYSICAL"

def legal_brain(text, context):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = f"SCENARIO: {text}\nLAW DATA: {context}\nRole: Expert Indian Cyber Lawyer. Markdown Citations: 📜 SECTIONS, ⚖️ PUNISHMENTS, 📊 WIN PROBABILITY, 🚀 ACTION PLAN."
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}], "temperature": 0.2
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=12)
        content = res.json()['choices'][0]['message']['content']
        return content.replace("**", "")
    except: return "⚠️ AI Engine Error."

# --- SIDEBAR UI ---
with st.sidebar:
    st.image("https://dffijjxsicbmyyufqozf.supabase.co/storage/v1/object/public/Elements/JUSTICE%20LENS.jpg", use_container_width=True)
    
    if not st.session_state.user:
        auth_tab = st.tabs(["Login", "Join"])
        with auth_tab[0]:
            e_val = st.text_input("Email", key="login_email")
            p_val = st.text_input("Password", type="password", key="login_pass")
            if st.button("AUTHENTICATE"):
                valid, u_obj = authenticate(e_val, p_val)
                if valid:
                    if check_ban(u_obj.uid): st.error("Access Forbidden.")
                    else:
                        st.session_state.user = {"name": u_obj.display_name or e_val.split('@')[0], "email": e_val, "uid": u_obj.uid}
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
        
        opts = ["🤖 AI Lawyer", "Vision & Mission", "Project Team"]
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
        st.markdown("""
            <div class="glass-card" style="text-align: center;">
                <h1 style="color:#0F172A !important;">Justice Lens</h1>
                <p style="color:#C5A059 !important; font-weight:700; font-size:1rem; letter-spacing:2px; margin-top:-10px;">SECURE AI CYBER LEGAL DEFENSE</p>
                <div style="background:#F8FAFC; padding:2rem; border-radius:1rem; border:1px solid #E2E8F0; text-align:left; margin: 2rem 0;">
                    <h3 style="margin-top:0;">Expert Advocacy</h3>
                    <p>Protect your digital footprint under the <b>Indian IT Act 2000</b>. Our engine provides instant legal reports using context-aware AI retrieval.</p>
                </div>
                <p style="font-weight:800; color:#94A3B8; font-size:0.8rem !important; letter-spacing:1px;">AUTHENTICATE VIA SIDEBAR TO BEGIN</p>
            </div>
        """, unsafe_allow_html=True)

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
                        scope = get_scope(user_msg)
                        if "PHYSICAL" in scope:
                            ans = "⚠️ REJECTION: Physical crime detected. Justice Lens handles digital crimes ONLY under the IT Act 2000. Contact local police."
                        else:
                            with st.spinner("Querying Legal Database..."):
                                ctx = "General context applied."
                                try:
                                    v = legal_embeddings.embed_query(user_msg)
                                    m = pinecone_index.query(vector=v, top_k=1, include_metadata=True)
                                    if m['matches'] and m['matches'][0]['score'] > 0.4:
                                        ctx = m['matches'][0]['metadata'].get('text', '')
                                except: 
                                    pass
                                ans = legal_brain(user_msg, ctx)
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    if db:
                        db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("logs").add({
                            "uid": st.session_state.user['uid'], "user": st.session_state.user['name'],
                            "query": user_msg, "report": ans, "timestamp": datetime.now()
                        })
                    st.rerun()

    elif page == "Vision & Mission":
        st.title("📖 Our Core Principles")
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("""<div class="glass-card"><h3 style="color:#C5A059 !important;">Our Vision</h3><p>To establish a digital fortress in India where legal intelligence is accessible to every citizen.</p></div>""", unsafe_allow_html=True)
        with v2:
            st.markdown("""<div class="glass-card"><h3 style="color:#C5A059 !important;">Our Mission</h3><p>Utilizing AI to translate complex legislative acts into actionable, cited legal reports for the public.</p></div>""", unsafe_allow_html=True)

    elif page == "Project Team":
        st.title("🛡️ The Core Developers")
        team = [{"n": "Archana V S", "r": "Legal Logic Architect"}, {"n": "Dolus K Shyju", "r": "Technical Lead"}, {"n": "RoseSaniya P X", "r": "UI Engineering"}, {"n": "Sreeraj S P", "r": "Database Design"}]
        cols = st.columns(4)
        for i, m in enumerate(team):
            cols[i].markdown(f'''<div style="background:white; padding:1.5rem; border-radius:1rem; text-align:center; border:1px solid #E2E8F0; box-shadow:0 4px 10px rgba(0,0,0,0.03);"><div style="font-size:3rem; margin-bottom:10px;">👤</div><h3 style="font-size:1rem !important; border:none; padding:0;">{m["n"]}</h3><p style="color:var(--gold) !important; font-weight:800; font-size:0.8rem !important; margin-top:5px;">{m["r"]}</p></div>''', unsafe_allow_html=True)

    elif page == "🚨 Admin Dashboard" and st.session_state.admin_mode:
        st.title("🚨 System Oversight")
        if db:
            u_ref = db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("users")
            
            st.markdown("### 👥 Active User Directory")
            for u in u_ref.stream():
                ud = u.to_dict()
                last_active = ud.get('last_active').strftime('%d %b, %H:%M') if ud.get('last_active') else "N/A"
                status_color = "#ef4444" if ud.get('is_banned') else "#22c55e"
                
                # USER CARD WITH FORCED NAVY TEXT
                st.markdown(f"""
                    <div class="admin-data-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div><b>{ud.get('name')}</b><p>{ud.get('email')}</p><p>Last Active: {last_active}</p></div>
                            <div><span class="status-badge" style="background:{status_color}; color:white !important;">{'BANNED' if ud.get('is_banned') else 'ACTIVE'}</span></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    b_label = "✅ UNBAN" if ud.get('is_banned') else "🚫 BAN"
                    if st.button(b_label, key=f"ban_{u.id}"):
                        u_ref.document(u.id).update({"is_banned": not ud.get('is_banned')})
                        st.rerun()
                with c_btn2:
                    if st.button("🗑️ DELETE", key=f"del_{u.id}"):
                        try:
                            auth.delete_user(u.id)
                        except:
                            pass
                        try:
                            u_ref.document(u.id).delete()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            st.markdown("---")
            # Consultation stream fixed visibility and always visible header
            st.markdown("### 📋 Consultation Stream")
            logs = db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("logs").stream()
            for l in logs:
                ld = l.to_dict()
                # Use label with forced visibility for expander summary
                with st.expander(f"Case: {ld.get('user')} | {ld.get('timestamp').strftime('%H:%M:%S')}"):
                    st.markdown(f"""<div style="color:var(--navy) !important; font-size:0.85rem; padding:10px; background:#f8fafc; border-radius:8px;">
                        <b>Scenario:</b><br>{ld.get('query')}<br><br>
                        <b>AI Report:</b><br>{ld.get('report')}
                    </div>""", unsafe_allow_html=True)

                    
