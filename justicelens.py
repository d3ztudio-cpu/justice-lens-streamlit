import streamlit as st
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Justice Lens | AI Cyber Legal Expert",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ADVANCED UI STYLING (Modern Dashboard) ---
st.markdown("""
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }
    section[data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    
    /* Cards and Containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }

    /* Buttons - Premium Action Style */
    .stButton > button {
        width: 100%;
        border-radius: 0.75rem;
        border: none;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
        color: white;
    }

    /* AI Chat Interface */
    .chat-scroll {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
        padding: 1rem;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .message {
        padding: 1.25rem 1.5rem;
        border-radius: 1rem;
        max-width: 80%;
        line-height: 1.5;
        font-size: 0.95rem;
        position: relative;
    }

    .user-message {
        background: #0f172a;
        color: #ffffff !important;
        align-self: flex-end;
        border-bottom-right-radius: 0.25rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
    }

    .ai-message {
        background: white;
        color: #1e293b !important;
        align-self: flex-start;
        border-bottom-left-radius: 0.25rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }

    /* Auth Inputs */
    .stTextInput input {
        border-radius: 0.5rem !important;
        border: 1px solid #cbd5e1 !important;
        padding: 0.75rem !important;
    }

    /* Header Colors */
    h1, h2, h3 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #dcfce7;
        color: #166534;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FIREBASE INITIALIZATION ---
def init_firebase():
    project_id = "justicelens-law"
    if not firebase_admin._apps:
        try:
            # 1. Attempt using Streamlit Secrets
            if "firebase" in st.secrets:
                fb_secrets = st.secrets["firebase"]
                
                # Check if the secrets are nested in a 'service_account' string (JSON)
                if "service_account" in fb_secrets:
                    raw_json = fb_secrets["service_account"]
                    key_dict = json.loads(raw_json) if isinstance(raw_json, str) else dict(raw_json)
                else:
                    # Otherwise, assume flat TOML keys (type, project_id, etc.)
                    key_dict = dict(fb_secrets)
                
                # Strict check for the 'type' field required by Firebase
                if "type" not in key_dict:
                    st.error("Firebase Configuration Error: The 'type' field is missing from your secrets.")
                    return None
                    
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred, {'projectId': project_id})
                return firestore.client()
            
            # 2. Local fallback
            if os.path.exists("serviceAccountKey.json"):
                cred = credentials.Certificate("serviceAccountKey.json")
                firebase_admin.initialize_app(cred, {'projectId': project_id})
                return firestore.client()
                
        except Exception as e:
            st.error(f"Error initializing Firebase: {str(e)}")
            return None
    return firestore.client()

# Store reference to db
db = init_firebase()

# --- SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- AUTH LOGIC ---
def handle_login(email, password):
    if not firebase_admin._apps:
        st.error("System error: Firebase not initialized.")
        return False
    try:
        user_record = auth.get_user_by_email(email)
        st.session_state.user = {
            "email": user_record.email, 
            "uid": user_record.uid, 
            "name": user_record.display_name or user_record.email.split('@')[0]
        }
        return True
    except Exception as e:
        st.error(f"Authentication Failed: {str(e)}")
        return False

def handle_signup(email, password, name):
    if not firebase_admin._apps:
        st.error("System error: Firebase not initialized.")
        return False
    try:
        user_record = auth.create_user(
            email=email, 
            password=password, 
            display_name=name
        )
        st.session_state.user = {
            "email": user_record.email, 
            "uid": user_record.uid, 
            "name": name
        }
        return True
    except Exception as e:
        st.error(f"Signup Failed: {str(e)}")
        return False

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://dffijjxsicbmyyufqozf.supabase.co/storage/v1/object/public/Elements/JUSTICE%20LENS.jpg", use_container_width=True)
    st.markdown("---")
    
    if not st.session_state.user:
        auth_mode = st.tabs(["Login", "Sign Up"])
        
        with auth_mode[0]:
            email_in = st.text_input("Email", key="login_email")
            pass_in = st.text_input("Password", type="password", key="login_pass")
            if st.button("SIGN IN", key="login_btn"):
                if email_in and pass_in:
                    if handle_login(email_in, pass_in):
                        st.rerun()
                else:
                    st.warning("Please enter credentials.")
                    
        with auth_mode[1]:
            new_name = st.text_input("Full Name", key="signup_name")
            new_email = st.text_input("Email", key="signup_email")
            new_pass = st.text_input("Password", type="password", key="signup_pass")
            if st.button("CREATE ACCOUNT", key="signup_btn"):
                if new_name and new_email and new_pass:
                    if handle_signup(new_email, new_pass, new_name):
                        st.success("Account created successfully!")
                        st.rerun()
                else:
                    st.warning("Please fill all fields.")
    else:
        st.markdown(f"### 👤 {st.session_state.user['name']}")
        st.markdown(f"<small>{st.session_state.user['email']}</small>", unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("DASHBOARD", ["🤖 Legal Assistant", "📖 Vision & Goals", "🛡️ Team Profile"])
        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state.user = None
            st.session_state.chat_history = []
            st.rerun()

# --- MAIN DASHBOARD ---

if not st.session_state.user:
    # Professional Landing Experience
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        st.markdown("""
            <div class="glass-card" style="text-align: center;">
                <h1 style="font-size: 3rem; margin-bottom: 0;">Justice Lens</h1>
                <p style="font-size: 1.2rem; color: #64748b; margin-bottom: 2rem;">Next-Gen AI Cyber Legal Assistant</p>
                <div style="text-align: left; background: #f8fafc; padding: 1.5rem; border-radius: 1rem; border: 1px solid #e2e8f0;">
                    <h3 style="margin-top:0;">Secure Consultation Platform</h3>
                    <p>Access specialized insights into the <b>Information Technology Act, 2000</b>. Our AI provides instant analysis for cyber-legal queries, ensuring citizens know their rights in the digital age.</p>
                    <ul style="color: #475569;">
                        <li>Encrypted Data Management</li>
                        <li>Automated Case Reference</li>
                        <li>Penalty Analysis</li>
                    </ul>
                </div>
                <p style="margin-top: 2rem; font-weight: 600;">Please Sign In or Create an Account to proceed.</p>
            </div>
        """, unsafe_allow_html=True)
else:
    if menu == "🤖 Legal Assistant":
        st.markdown('<div class="status-badge">System Status: AI Online</div>', unsafe_allow_html=True)
        st.title("🤖 Cyber Legal AI")
        st.write("Submit your query regarding cybercrime, digital fraud, or IT Act sections.")

        # Chat display area
        chat_container = st.container()

        with chat_container:
            st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
            for chat in st.session_state.chat_history:
                msg_class = "user-message" if chat["role"] == "user" else "ai-message"
                st.markdown(f"""
                    <div class="message {msg_class}">
                        {chat['content']}
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Floating Input Bar
        with st.form("query_bar", clear_on_submit=True):
            user_input_val = st.text_input("Enter your query...", placeholder="e.g., What is the penalty for identity theft under Section 66C?")
            submit = st.form_submit_button("CONSULT AI")
            
            if submit and user_input_val:
                st.session_state.chat_history.append({"role": "user", "content": user_input_val})
                
                # Dynamic response logic
                ai_response = f"I am analyzing your query about '{user_input_val}'. Based on the IT Act 2000, I will provide a detailed legal breakdown once my backend processing is enabled."
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                
                if db:
                    try:
                        db.collection("artifacts").document("justicelens-law").collection("public").document("data").collection("ai_conversations").add({
                            "uid": st.session_state.user['uid'],
                            "user": st.session_state.user['name'],
                            "query": user_input_val,
                            "response": ai_response,
                            "timestamp": datetime.now()
                        })
                    except Exception as e:
                        pass
                st.rerun()

    elif menu == "📖 Vision & Goals":
        st.markdown("""
            <div class="glass-card">
                <h1>📖 Vision & Strategic Goals</h1>
                <hr>
                <h3>Democratizing Cyber Justice</h3>
                <p>Justice Lens is not just an app; it's a movement to ensure that no Indian citizen is left vulnerable due to a lack of legal awareness. We aim to translate complex legislative structures into actionable digital advice.</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                    <div style="padding: 1rem; border: 1px solid #e2e8f0; border-radius: 10px;">
                        <h4 style="margin:0;">Awareness</h4>
                        <p style="font-size: 0.9rem;">Bridging the gap between victims and legal remedies.</p>
                    </div>
                    <div style="padding: 1rem; border: 1px solid #e2e8f0; border-radius: 10px;">
                        <h4 style="margin:0;">Accessibility</h4>
                        <p style="font-size: 0.9rem;">24/7 AI-powered legal guidance at no cost.</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    elif menu == "🛡️ Team Profile":
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.title("🛡️ Project Developers")
        st.write("Group 4 | ICCS College of Engineering")
        st.markdown("---")
        
        t1, t2 = st.columns(2)
        with t1:
            st.info("**Archana V S** — Legal Research & Logic")
            st.info("**RoseSaniya P X** — Frontend Architect")
        with t2:
            st.info("**Dolus K Shyju** — Technical & Backend Lead")
            st.info("**Sreeraj S P** — System Design & Deployment")
        st.markdown('</div>', unsafe_allow_html=True)