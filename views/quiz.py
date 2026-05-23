import streamlit as st
from utils.rag_engine import generate_quiz
from utils.embeddings import load_vectorstore

def show_quiz():
    st.markdown('<p class="section-header">Generate Quiz</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-subtitle">AI generates exam-style questions directly from your uploaded documents</p>',
        unsafe_allow_html=True
    )

    # ─── Empty State ─────────────────────────────────────────
    from utils.embeddings import load_vectorstore
    vectorstore = load_vectorstore()

    if vectorstore is None:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:2rem;color:#1e3a5f;margin-bottom:8px;">&#9670;</div>
            <h3>No Documents Found</h3>
            <p>Upload your notes first to generate quizzes</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Upload", use_container_width=True, type="primary"):
            st.session_state.current_page = "upload"
            st.rerun()
        return

    # ─── Quiz Settings ────────────────────────────────────────
    st.markdown("### Settings")

    col1, col2 = st.columns([2, 1])

    with col1:
        topic = st.text_input(
            "Topic or Subject",
            placeholder="e.g. DBMS Normalisation, OS Scheduling, Python OOP...",
            help="Enter the topic you want quiz questions about"
        )

    with col2:
        num_questions = st.selectbox(
            "Number of Questions",
            options=[5, 10, 15, 20],
            index=0
        )

    st.divider()

    # ─── Options Row ──────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);
        border-radius:8px;padding:12px 16px;margin-bottom:8px;">
            <span style="color:#60a5fa;font-weight:600;font-size:13px;">Question Type</span>
        </div>
        """, unsafe_allow_html=True)
        q_type = st.radio(
            "Type",
            ["Short Answer", "Long Answer", "Mixed"],
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);
        border-radius:8px;padding:12px 16px;margin-bottom:8px;">
            <span style="color:#06b6d4;font-weight:600;font-size:13px;">Difficulty</span>
        </div>
        """, unsafe_allow_html=True)
        difficulty = st.radio(
            "Difficulty",
            ["Easy", "Medium", "Hard"],
            index=1,
            label_visibility="collapsed"
        )

    with col3:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);
        border-radius:8px;padding:12px 16px;margin-bottom:8px;">
            <span style="color:#34d399;font-weight:600;font-size:13px;">Exam Style</span>
        </div>
        """, unsafe_allow_html=True)
        exam_style = st.radio(
            "Exam Style",
            ["University Exam", "Interview Prep", "Quick Revision"],
            label_visibility="collapsed"
        )

    st.divider()

    # ─── Generate Button ─────────────────────────────────────
    if st.button("Generate Quiz", use_container_width=True, type="primary"):
        if not topic.strip():
            st.error("Please enter a topic first.")
            return

        with st.spinner(f"Generating {num_questions} {difficulty.lower()} questions on {topic}..."):
            quiz_prompt = f"{topic} — {difficulty} level — {q_type} — {exam_style} style"
            result = generate_quiz(
                topic=quiz_prompt,
                num_questions=num_questions
            )

        st.session_state.quiz_result = result
        st.session_state.quiz_topic  = topic

    # ─── Display Quiz ─────────────────────────────────────────
    if st.session_state.get("quiz_result"):
        st.divider()
        st.markdown(f"### Quiz: {st.session_state.get('quiz_topic', 'Your Topic')}")

        st.markdown(f"""
        <div style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.12);
        border-radius:12px;padding:24px;white-space:pre-wrap;color:#d1d5db;line-height:1.8">
        {st.session_state.quiz_result}
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                "Download Quiz",
                data=st.session_state.quiz_result,
                file_name=f"quiz_{st.session_state.get('quiz_topic','topic').replace(' ','_')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        with col2:
            if st.button("Regenerate", use_container_width=True):
                st.session_state.quiz_result = None
                st.rerun()

        with col3:
            if st.button("Discuss in Chat", use_container_width=True):
                st.session_state.current_page = "chat"
                st.session_state.pending_question = f"Explain the answers to quiz questions about {st.session_state.get('quiz_topic', 'this topic')}"
                st.rerun()