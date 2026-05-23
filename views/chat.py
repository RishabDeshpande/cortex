import streamlit as st
from utils.rag_engine import ask_question


def show_chat():
    st.markdown('<p class="section-header">Chat with Your Documents</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-subtitle">Ask anything — your AI answers only from your uploaded study materials</p>',
        unsafe_allow_html=True
    )

    # ─── Empty State ─────────────────────────────────────────
    from utils.embeddings import load_vectorstore
    vectorstore = load_vectorstore()

    if vectorstore is None:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:2rem;color:#1e3a5f;margin-bottom:8px;">&#9670;</div>
            <h3>No Documents Loaded</h3>
            <p>Upload your notes and documents first to start chatting</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Go to Upload", use_container_width=True, type="primary"):
            st.session_state.current_page = "upload"
            st.rerun()
        return

    # ─── Input Box (top for better UX) ───────────────────────
    col1, col2 = st.columns([5, 1])

    with col1:
        question = st.text_input(
            "Ask a question",
            placeholder="e.g. What is normalisation in DBMS? What are PYQ questions on OS scheduling?",
            label_visibility="collapsed",
            key="question_input"
        )

    with col2:
        ask_btn = st.button("Ask", use_container_width=True, type="primary")

    # Handle suggested question click
    if "pending_question" in st.session_state:
        question = st.session_state.pending_question
        del st.session_state.pending_question
        ask_btn = True

    # ─── Process Question ─────────────────────────────────────
    if ask_btn and question.strip():
        with st.spinner("Searching your documents and generating answer..."):
            result = ask_question(
                question=question,
                chat_history=st.session_state.chat_history
            )

        # Add to history
        st.session_state.chat_history.append({
            "question":   question,
            "answer":     result["answer"],
            "sources":    result["sources"],
            "confidence": result["confidence"]
        })

        st.rerun()

    st.divider()

    # ─── Chat History Display ─────────────────────────────────
    chat_container = st.container()

    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center;padding:40px;color:#4b5563">
                <p style="font-size:15px;">Ask your first question above</p>
                <p style="font-size:13px;color:#374151;">Try: "Summarise the main topics" or "What are PYQ questions on X?"</p>
            </div>
            """, unsafe_allow_html=True)

            # Suggested questions
            st.markdown("### Suggested Questions")
            suggestions = [
                "What are the main topics in my notes?",
                "Explain the most important concept",
                "What are likely exam questions?",
                "Summarise everything I've uploaded",
            ]
            cols = st.columns(2)
            for i, suggestion in enumerate(suggestions):
                with cols[i % 2]:
                    if st.button(suggestion, use_container_width=True, key=f"sug_{i}"):
                        st.session_state.pending_question = suggestion
                        st.rerun()
        else:
            for turn in st.session_state.chat_history:
                # User message
                st.markdown(f"""
                <div class="user-message">
                    <b style="color:#60a5fa">You</b><br>
                    {turn['question']}
                </div>
                """, unsafe_allow_html=True)

                # Confidence badge
                conf = turn.get("confidence", 0)
                if conf >= 70:
                    conf_color = "#34d399"
                    conf_label = "High"
                elif conf >= 40:
                    conf_color = "#fbbf24"
                    conf_label = "Medium"
                else:
                    conf_color = "#f87171"
                    conf_label = "Low"

                # AI message header
                st.markdown(f"""
                <div class="ai-message">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                        <b style="color:#60a5fa">Cortex</b>
                        <span style="background:rgba(0,0,0,0.3);border-radius:20px;
                        padding:2px 10px;font-size:12px;color:{conf_color}">
                            {conf_label} — {conf}%
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(turn['answer'])

                # Sources
                if turn.get("sources"):
                    with st.expander(f"View Sources ({len(turn['sources'])} referenced)"):
                        for src in turn["sources"]:
                            st.markdown(f"""
                            <div style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.12);
                            border-radius:8px;padding:12px;margin:6px 0">
                                <b style="color:#60a5fa">{src['file']}</b>
                                <span style="color:#4b5563;font-size:12px"> — Page {src['page']}</span><br>
                                <small style="color:#6b7280">"{src['preview']}"</small>
                            </div>
                            """, unsafe_allow_html=True)

                st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.04)'>",
                            unsafe_allow_html=True)

    # ─── Clear / Export ───────────────────────────────────────
    if st.session_state.chat_history:
        st.divider()
        col1, col2, col3 = st.columns([3, 1, 1])
        with col2:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        with col3:
            chat_text = "\n\n".join([
                f"Q: {t['question']}\nA: {t['answer']}"
                for t in st.session_state.chat_history
            ])
            st.download_button(
                "Export",
                data=chat_text,
                file_name="chat_history.txt",
                mime="text/plain",
                use_container_width=True
            )