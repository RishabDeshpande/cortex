import streamlit as st
from utils.rag_engine import summarize_document
from utils.embeddings import get_indexed_files


def show_summary():
    st.markdown('<p class="section-header">Document Summaries</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-subtitle">Get AI-generated summaries of any uploaded document</p>',
        unsafe_allow_html=True
    )

    # ─── Empty State ─────────────────────────────────────────
    indexed = get_indexed_files()

    if not indexed:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:2rem;color:#1e3a5f;margin-bottom:8px;">&#9670;</div>
            <h3>No Documents Found</h3>
            <p>Upload your notes first to get summaries</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Upload", use_container_width=True, type="primary"):
            st.session_state.current_page = "upload"
            st.rerun()
        return

    # ─── Document Stats Overview ──────────────────────────────
    total_chunks = sum(f["chunks"] for f in indexed)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="label">Documents</div>
            <div class="value" style="color:#60a5fa">{len(indexed)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="label">Total Chunks</div>
            <div class="value" style="color:#06b6d4">{total_chunks}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="label">Summaries Generated</div>
            <div class="value" style="color:#34d399">
                {len(st.session_state.get('document_summaries', {}))}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ─── Summarize All Button ─────────────────────────────────
    if st.button("Summarize All Documents", use_container_width=True, type="primary"):
        for f in indexed:
            if f["file"] not in st.session_state.document_summaries:
                with st.spinner(f"Summarizing {f['file']}..."):
                    summary = summarize_document(f["file"])
                    st.session_state.document_summaries[f["file"]] = summary
        st.success("All documents summarized.")
        st.rerun()

    st.divider()

    # ─── Individual Document Cards ────────────────────────────
    st.markdown("### Your Documents")

    for f in indexed:
        with st.expander(f"{f['file']} — {f['chunks']} chunks"):

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"""
                <div style="padding:8px 0;">
                    <span class="source-badge">{f['chunks']} chunks indexed</span>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.button(
                    "Summarize",
                    key=f"sum_{f['file']}",
                    use_container_width=True
                ):
                    with st.spinner(f"Summarizing {f['file']}..."):
                        summary = summarize_document(f["file"])
                        st.session_state.document_summaries[f["file"]] = summary
                    st.rerun()

            # Show summary if exists
            if f["file"] in st.session_state.get("document_summaries", {}):
                st.markdown("#### Summary")
                st.markdown(f"""
                <div style="background:rgba(59,130,246,0.04);border:1px solid rgba(59,130,246,0.1);
                border-radius:10px;padding:16px;color:#d1d5db;line-height:1.8;white-space:pre-wrap">
                {st.session_state.document_summaries[f['file']]}
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "Download Summary",
                        data=st.session_state.document_summaries[f["file"]],
                        file_name=f"summary_{f['file']}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"dl_{f['file']}"
                    )
                with col2:
                    if st.button(
                        "Ask Questions About This",
                        key=f"chat_{f['file']}",
                        use_container_width=True
                    ):
                        st.session_state.current_page = "chat"
                        st.session_state.pending_question = f"Tell me about the key topics in {f['file']}"
                        st.rerun()
            else:
                st.markdown("""
                <p style="color:#4b5563;font-size:14px">
                Click "Summarize" to generate an AI summary of this document
                </p>
                """, unsafe_allow_html=True)