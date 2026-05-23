import streamlit as st
import os
from utils.document_processor import process_uploaded_file
from utils.embeddings import (
    chunk_documents,
    save_to_vectorstore,
    get_indexed_files,
    delete_document,
    get_user_base_path
)


def get_upload_dir():
    user_base = get_user_base_path()
    upload_dir = os.path.join(user_base, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def show_upload():
    st.markdown("## Upload Documents")
    st.markdown("Add PDFs, scanned notes, or images to your study workspace.")

    uploaded_files = st.file_uploader(
        "Select files",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Supports PDFs and image-based notes"
    )

    upload_dir = get_upload_dir()

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) ready**")

        if st.button("Process Documents", use_container_width=True):
            all_success = True

            for file in uploaded_files:
                status = st.empty()
                status.info(f"Processing {file.name}")

                temp_path = os.path.join(upload_dir, file.name)

                file_bytes = file.read()

                if not file_bytes:
                    status.error(f"{file.name} appears to be empty.")
                    all_success = False
                    continue

                with open(temp_path, "wb") as f:
                    f.write(file_bytes)

                pages = process_uploaded_file(temp_path)

                if not pages:
                    status.error(f"Could not process {file.name}")
                    all_success = False
                    continue

                docs = chunk_documents(pages)
                save_to_vectorstore(docs)

                status.success(f"{file.name} processed successfully")

            if all_success:
                st.success("All documents processed successfully")

    indexed = get_indexed_files()
    has_docs = len(indexed) > 0

    st.markdown("### Workspace Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "Open Chat",
            use_container_width=True,
            key="go_chat",
            disabled=not has_docs
        ):
            st.session_state.current_page = "chat"
            st.rerun()

    with col2:
        if st.button(
            "Generate Quiz",
            use_container_width=True,
            key="go_quiz",
            disabled=not has_docs
        ):
            st.session_state.current_page = "quiz"
            st.rerun()

    with col3:
        if st.button(
            "Summarize",
            use_container_width=True,
            key="go_summary",
            disabled=not has_docs
        ):
            st.session_state.current_page = "summary"
            st.rerun()

    if indexed:
        st.markdown("### Indexed Documents")

        for f in indexed:
            col1, col2 = st.columns([5, 1])

            with col1:
                st.markdown(f"**{f['file']}**")

            with col2:
                if st.button(
                    "Remove",
                    key=f"del_{f['file']}",
                    help=f"Remove {f['file']}"
                ):
                    with st.spinner(f"Removing {f['file']}..."):
                        delete_document(f["file"])

                    if f["file"] in st.session_state.get("document_summaries", {}):
                        del st.session_state.document_summaries[f["file"]]

                    try:
                        file_path = os.path.join(upload_dir, f["file"])

                        if os.path.exists(file_path):
                            os.remove(file_path)

                    except:
                        pass

                    st.success(f"Removed {f['file']}")
                    st.rerun()

    if st.session_state.get("pending_continue_chat"):
        st.info("Documents restored. Continue previous chat.")

        if st.button("Continue Chat", use_container_width=True):
            st.session_state.chat_history = (
                st.session_state.pending_continue_chat.copy()
            )
            st.session_state.pending_continue_chat = None
            st.session_state.current_page = "chat"
            st.rerun()