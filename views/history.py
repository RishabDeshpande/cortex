import streamlit as st
import json
import os
from langchain_core.documents import Document


def get_user_email():
    email = st.session_state.get("user_email")

    if not email:
        raise ValueError("No logged in user")

    return email.replace("@", "_at_").replace(".", "_")


def get_history_file():
    email = get_user_email()
    user_dir = os.path.join("data", "users", email)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "chat_history.json")


def load_saved_chats() -> list:
    history_file = get_history_file()

    if not os.path.exists(history_file):
        return []

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_chats_to_disk(chats: list):
    history_file = get_history_file()

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(chats, f, indent=2)


def show_history():
    st.markdown("## Chat History")
    st.markdown("Your saved conversations")

    saved = load_saved_chats()

    if not saved:
        st.info("No saved chats yet.")
        return

    st.markdown(f"**{len(saved)} saved conversation(s)**")

    for i, chat in enumerate(reversed(saved)):
        idx = len(saved) - 1 - i

        with st.expander(f"{chat['name']} — {len(chat['history'])} messages"):

            rename_key = f"renaming_{idx}"

            if st.session_state.get(rename_key):
                new_name = st.text_input(
                    "New name",
                    value=chat["name"],
                    key=f"rename_input_{idx}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Save Name", key=f"save_name_{idx}", use_container_width=True):
                        saved[idx]["name"] = new_name
                        save_chats_to_disk(saved)
                        st.session_state[rename_key] = False
                        st.rerun()

                with col2:
                    if st.button("Cancel", key=f"cancel_rename_{idx}", use_container_width=True):
                        st.session_state[rename_key] = False
                        st.rerun()

            else:
                if st.button("Rename", key=f"rename_btn_{idx}"):
                    st.session_state[rename_key] = True
                    st.rerun()

            st.markdown("**Documents used:**")

            for f in chat.get("files", []):
                st.markdown(f"- {f}")

            if not chat.get("history"):
                st.markdown("No messages in this chat")

            else:
                for turn in chat["history"]:
                    st.markdown(f"**You:** {turn['question']}")
                    st.markdown(f"**AI:** {turn['answer']}")
                    st.divider()

            col1, col2, col3 = st.columns(3)

            with col1:
                chat_text = "\n\n".join([
                    f"Q: {t['question']}\nA: {t['answer']}"
                    for t in chat.get("history", [])
                ])

                st.download_button(
                    "Download",
                    data=chat_text,
                    file_name=f"{chat['name']}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key=f"dl_{idx}"
                )

            with col2:
                if st.button("Continue", key=f"continue_{idx}", use_container_width=True):
                    st.session_state.chat_history = chat["history"].copy()

                    from utils.embeddings import (
                        get_indexed_files,
                        save_to_vectorstore,
                        load_vectorstore
                    )

                    indexed = get_indexed_files()
                    indexed_names = [f["file"] for f in indexed]
                    missing = [
                        f for f in chat.get("files", [])
                        if f not in indexed_names
                    ]

                    if missing and chat.get("chunks"):
                        docs = []
                        seen = set()

                        for c in chat["chunks"]:
                            if c["source"] not in missing:
                                continue

                            key = (c["source"], c["page"], c["text"])

                            if key in seen:
                                continue

                            seen.add(key)

                            docs.append(
                                Document(
                                    page_content=c["text"],
                                    metadata={
                                        "source": c["source"],
                                        "page": c["page"]
                                    }
                                )
                            )

                        if docs:
                            save_to_vectorstore(docs)

                    elif missing and not chat.get("chunks"):
                        st.warning("This old chat requires re-uploading documents.")
                        st.session_state.current_page = "upload"
                        st.rerun()
                        return

                    vectorstore = load_vectorstore()

                    if vectorstore is None:
                        st.warning("Documents not restored.")
                        st.session_state.current_page = "upload"
                        st.rerun()
                        return

                    st.session_state.current_page = "chat"
                    st.rerun()

            with col3:
                if st.button("Delete", key=f"del_{idx}", use_container_width=True):
                    saved.pop(idx)
                    save_chats_to_disk(saved)
                    st.rerun()