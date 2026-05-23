import streamlit as st
import re
from utils.auth import create_user, login_user


def show_auth():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;0,500;1,400&display=swap');

    * { box-sizing: border-box; }

    html, body, .stApp {
        background: #111114 !important;
        font-family: 'Sora', sans-serif;
    }

    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    #MainMenu, footer, header { display: none !important; visibility: hidden; }

    /* ── Page layout ── */
    .block-container {
        max-width: 420px !important;
        padding: 3rem 1.5rem 2rem !important;
        margin: 0 auto !important;
    }

    /* ── Brand ── */
    .brand {
        text-align: center;
        margin-bottom: 3rem;
    }
    .brand-name {
        font-family: 'Playfair Display', serif;
        font-size: 2.8rem;
        font-weight: 400;
        color: #f2f0eb;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .brand-name i {
        color: #9d8df1;
        font-style: italic;
    }
    .brand-sub {
        font-size: 0.65rem;
        letter-spacing: 0.3em;
        color: #44445a;
        text-transform: uppercase;
        margin-top: 0.5rem;
        font-weight: 400;
    }

    /* ── Section heading above tabs ── */
    .form-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.6rem;
        font-weight: 400;
        color: #f2f0eb;
        margin-bottom: 0.25rem;
    }
    .form-title i { color: #9d8df1; font-style: italic; }
    .form-sub {
        font-size: 0.75rem;
        color: #44445a;
        letter-spacing: 0.06em;
        margin-bottom: 1.8rem;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 0 !important;
        border-bottom: 1px solid #1e1e26 !important;
        margin-bottom: 1.8rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Sora', sans-serif !important;
        font-size: 0.7rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.18em !important;
        text-transform: uppercase !important;
        color: #44445a !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid transparent !important;
        border-radius: 0 !important;
        padding: 0.75rem 1.2rem !important;
        margin-bottom: -1px;
    }
    .stTabs [aria-selected="true"] {
        color: #f2f0eb !important;
        border-bottom-color: #9d8df1 !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] { display: none !important; }

    /* ── Labels ── */
    .stTextInput > label,
    div[data-testid="stTextInput"] > label {
        font-family: 'Sora', sans-serif !important;
        font-size: 0.65rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.2em !important;
        text-transform: uppercase !important;
        color: #55556b !important;
    }

    /* ── Inputs ── */
    .stTextInput input {
        font-family: 'Sora', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 300 !important;
        background: #18181f !important;
        border: 1px solid #23232e !important;
        border-radius: 6px !important;
        color: #e8e6f0 !important;
        padding: 0.7rem 0.9rem !important;
        letter-spacing: 0.02em;
        transition: border-color 0.15s !important;
        box-shadow: none !important;
    }
    .stTextInput input:focus {
        border-color: #9d8df1 !important;
        box-shadow: 0 0 0 3px rgba(157,141,241,0.08) !important;
        background: #18181f !important;
    }
    .stTextInput input::placeholder { color: #2e2e3a !important; }

    div[data-testid="stTextInput"] { margin-bottom: 1.1rem; }

    /* ── Button ── */
    .stButton > button {
        width: 100% !important;
        font-family: 'Sora', sans-serif !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.2em !important;
        text-transform: uppercase !important;
        background: #9d8df1 !important;
        color: #fff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.85rem 1.5rem !important;
        margin-top: 0.6rem !important;
        transition: background 0.15s, opacity 0.15s !important;
        box-shadow: 0 4px 20px rgba(157,141,241,0.18) !important;
    }
    .stButton > button:hover {
        background: #b5a8f5 !important;
        box-shadow: 0 6px 24px rgba(157,141,241,0.28) !important;
    }
    .stButton > button:active { opacity: 0.85 !important; }

    /* ── Alerts ── */
    div[data-testid="stAlert"] {
        font-family: 'Sora', sans-serif !important;
        font-size: 0.78rem !important;
        border-radius: 6px !important;
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid #23232e !important;
        border-left: 2px solid #9d8df1 !important;
        color: #a0a0b8 !important;
        margin-top: 1rem;
    }

    /* ── Divider between brand and card ── */
    .divider {
        width: 32px;
        height: 1px;
        background: #23232e;
        margin: 0 auto 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Brand ──
    st.markdown("""
    <div class="brand">
        <div class="brand-name">Cor<i>tex</i></div>
        <div class="brand-sub">Private AI Workspace</div>
    </div>
    <div class="divider"></div>
    """, unsafe_allow_html=True)

    login_tab, signup_tab = st.tabs(["Sign In", "Create Account"])

    with login_tab:
        st.markdown("""
            <div class="form-title">Welcome <i>back</i></div>
            <div class="form-sub">Sign in to continue</div>
        """, unsafe_allow_html=True)

        login_email    = st.text_input("Email", key="login_email",    placeholder="you@example.com")
        login_password = st.text_input("Password", key="login_password", placeholder="••••••••", type="password")

        if st.button("Sign In →", key="login_btn"):
            if not login_email or not login_password:
                st.error("Please fill all fields.")
            else:
                result = login_user(login_email, login_password)
                if result["success"]:
                    st.session_state.logged_in  = True
                    st.session_state.user_email = result["email"]
                    st.session_state.username   = result["username"]
                    st.session_state.token      = result["token"]
                    st.rerun()
                else:
                    st.error(result["error"])

    with signup_tab:
        st.markdown("""
            <div class="form-title"><i>Create</i> account</div>
            <div class="form-sub">Set up your workspace</div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username",         key="signup_username", placeholder="yourname")
        email    = st.text_input("Email",            key="signup_email",    placeholder="you@example.com")
        password = st.text_input("Password",         key="signup_password", placeholder="min. 6 characters", type="password")
        confirm  = st.text_input("Confirm Password", key="signup_confirm",  placeholder="repeat password",   type="password")

        if st.button("Create Account →", key="signup_btn"):
            if not username or not email or not password or not confirm:
                st.error("Please fill all fields.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            elif not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                st.error("Enter a valid email address.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                result = create_user(username, email, password)
                if result["success"]:
                    st.success("Account created. Please sign in.")
                else:
                    st.error(result["error"])