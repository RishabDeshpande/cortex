import streamlit as st
import os
import datetime

os.environ["STREAMLIT_WATCH_EXCLUDE_PATTERNS"] = "torch.*"
from dotenv import load_dotenv

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    from views.auth import show_auth
    show_auth()
    st.stop()

load_dotenv()

st.set_page_config(
    page_title="CORTEX",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;0,500;1,400&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
[data-testid="stSidebar"], [data-testid="collapsedControl"], #MainMenu, footer, header { display:none !important; visibility:hidden; }
.stApp { background:#111114; color:#e8e6f0; }
.block-container { max-width:1200px !important; padding:2rem 2.5rem 3rem !important; }
.topbar-brand { font-family:'Playfair Display', serif; font-size:1.9rem; color:#f2f0eb; letter-spacing:0.12em; text-transform:uppercase; }
.topbar-brand i { color:#9d8df1; }
.topbar-sub { font-size:0.62rem; letter-spacing:0.28em; color:#44445a; text-transform:uppercase; }
.account-pill { display:flex; align-items:center; gap:.65rem; background:#18181f; border:1px solid #23232e; border-radius:50px; padding:.4rem .9rem .4rem .5rem; }
.account-avatar { width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg,#9d8df1,#6d5bd4); display:flex; align-items:center; justify-content:center; font-size:.68rem; font-weight:600; color:white; }
.account-name { font-size:.78rem; color:#c8c6d8; }
.nav-label { font-size:.6rem; letter-spacing:.25em; text-transform:uppercase; color:#44445a; margin-bottom:.6rem; }
.stButton > button { font-size:.72rem !important; letter-spacing:.1em !important; border-radius:6px !important; border:1px solid #1e1e26 !important; background:transparent !important; color:#55556b !important; padding:.65rem 1rem !important; }
.stButton > button:hover { border-color:#2e2e3e !important; color:#a09dc0 !important; background:rgba(157,141,241,.04) !important; }
.stButton > button[kind="primary"] { background:rgba(157,141,241,.12) !important; border-color:rgba(157,141,241,.3) !important; color:#c5bdf8 !important; }
.session-panel { background:#18181f; border:1px solid #23232e; border-radius:10px; padding:1rem; margin-bottom:2rem; }
.session-text { color:#8a89a3; font-size:.8rem; padding-top:.6rem; }
@media (max-width: 768px) {
  .block-container { max-width:100% !important; padding:1rem !important; }
  .topbar-brand { font-size:1.35rem; letter-spacing:.08em; }
  .topbar-sub { font-size:.5rem; letter-spacing:.18em; }
  .account-name { font-size:.65rem; }
  .stButton > button { font-size:.65rem !important; padding:.7rem .6rem !important; }
}
</style>
""", unsafe_allow_html=True)

defaults = {
    "chat_history": [],
    "uploaded_files": [],
    "current_page": "upload",
    "quiz_result": None,
    "document_summaries": {},
    "saved_chats": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

username = st.session_state.get("username", "User")
user_initials = "".join(w[0].upper() for w in username.split()[:2]) if username else "U"

left_col, right_col = st.columns([1, 1])
with left_col:
    st.markdown(f"<div class='topbar-brand'>Cor<i>tex</i></div><div class='topbar-sub'>Private AI Workspace</div>", unsafe_allow_html=True)
with right_col:
    pill_col, logout_col = st.columns([3, 1])
    with pill_col:
        st.markdown(f"<div style='display:flex; justify-content:flex-end; margin-top:.4rem;'><div class='account-pill'><div class='account-avatar'>{user_initials}</div><div class='account-name'>{username}</div></div></div>", unsafe_allow_html=True)
    with logout_col:
        if st.button("Log out", key="logout_btn"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

st.markdown("<div style='border-bottom:1px solid #1e1e26; margin-bottom:2rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)

pages = [("Upload","upload"),("Chat","chat"),("Quiz","quiz"),("Summary","summary"),("History","history")]
nav_cols = st.columns(len(pages))
for i, (label, key) in enumerate(pages):
    with nav_cols[i]:
        btn_type = "primary" if st.session_state.current_page == key else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            st.session_state.current_page = key
            st.rerun()

from utils.embeddings import get_indexed_files, load_vectorstore, clear_vectorstore
from views.history import load_saved_chats, save_chats_to_disk
indexed = get_indexed_files()

st.markdown('<div class="session-panel">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([4, 1.4, 1.4])
with col1:
    st.markdown(f"<div class='session-text'>{len(indexed)} document(s) loaded</div>", unsafe_allow_html=True)
with col2:
    if st.button("Save Chat", use_container_width=True):
        if not st.session_state.chat_history:
            st.warning("No chat to save yet.")
        else:
            vectorstore = load_vectorstore()
            stored_chunks = []
            if vectorstore:
                for doc in list(vectorstore.docstore._dict.values()):
                    stored_chunks.append({"text": doc.page_content, "source": doc.metadata.get("source"), "page": doc.metadata.get("page", 1)})
            chats = load_saved_chats()
            chats.append({
                "name": f"Chat — {datetime.datetime.now().strftime('%d %b %Y %I:%M %p')}",
                "history": st.session_state.chat_history.copy(),
                "files": [f["file"] for f in indexed],
                "date": datetime.datetime.now().strftime('%d %b %Y'),
                "chunks": stored_chunks,
            })
            save_chats_to_disk(chats)
            st.success("Chat saved")
with col3:
    if st.button("New Session", use_container_width=True):
        clear_vectorstore()
        st.session_state.chat_history = []
        st.session_state.document_summaries = {}
        st.session_state.quiz_result = None
        st.session_state.current_page = "upload"
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.current_page == "chat":
    from views.chat import show_chat
    show_chat()
elif st.session_state.current_page == "upload":
    from views.upload import show_upload
    show_upload()
elif st.session_state.current_page == "quiz":
    from views.quiz import show_quiz
    show_quiz()
elif st.session_state.current_page == "summary":
    from views.summary import show_summary
    show_summary()
elif st.session_state.current_page == "history":
    from views.history import show_history
    show_history()
