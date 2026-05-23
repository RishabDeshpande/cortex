import os
import shutil
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Free local embedding model
embeddings_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)


def get_user_email():
    email = st.session_state.get("user_email")

    if not email:
        raise ValueError("No logged in user found")

    return email.replace("@", "_at_").replace(".", "_")


def get_user_base_path():
    email = get_user_email()
    base = os.path.join("data", "users", email)
    os.makedirs(base, exist_ok=True)
    return base


def get_faiss_index_path():
    base = get_user_base_path()
    path = os.path.join(base, "faiss_index")
    os.makedirs(path, exist_ok=True)
    return path


def chunk_documents(pages: list[dict]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )

    docs = []

    for page in pages:
        splits = splitter.split_text(page["text"])

        for split in splits:
            docs.append(
                Document(
                    page_content=split,
                    metadata={
                        "source": page["source"],
                        "page": page["page"]
                    }
                )
            )

    return docs


def save_to_vectorstore(docs: list[Document]):
    faiss_path = get_faiss_index_path()

    if os.path.exists(os.path.join(faiss_path, "index.faiss")):
        existing = FAISS.load_local(
            faiss_path,
            embeddings_model,
            allow_dangerous_deserialization=True
        )

        existing.add_documents(docs)
        existing.save_local(faiss_path)

    else:
        vectorstore = FAISS.from_documents(docs, embeddings_model)
        vectorstore.save_local(faiss_path)


def load_vectorstore():
    faiss_path = get_faiss_index_path()

    if not os.path.exists(os.path.join(faiss_path, "index.faiss")):
        return None

    return FAISS.load_local(
        faiss_path,
        embeddings_model,
        allow_dangerous_deserialization=True
    )


def load_index():
    vectorstore = load_vectorstore()

    if vectorstore is None:
        return None, []

    docs = list(vectorstore.docstore._dict.values())

    chunks = []

    for doc in docs:
        chunks.append({
            "text": doc.page_content,
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", 1)
        })

    return vectorstore, chunks


def search_similar_chunks(query: str, top_k: int = 5):
    vectorstore = load_vectorstore()

    if vectorstore is None:
        return []

    results = vectorstore.similarity_search_with_score(query, k=top_k)

    chunks = []

    for doc, score in results:
        confidence = max(0, min(100, int((1 / (1 + score * 0.1)) * 100)))

        chunks.append({
            "text": doc.page_content,
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", 1),
            "confidence": confidence
        })

    return chunks


def get_indexed_files():
    vectorstore = load_vectorstore()

    if vectorstore is None:
        return []

    docs = list(vectorstore.docstore._dict.values())
    file_stats = {}

    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        file_stats[source] = file_stats.get(source, 0) + 1

    return [{"file": k, "chunks": v} for k, v in file_stats.items()]


def delete_document(file_name: str):
    vectorstore = load_vectorstore()

    if vectorstore is None:
        return False

    all_docs = list(vectorstore.docstore._dict.values())

    remaining_docs = [
        doc for doc in all_docs
        if doc.metadata.get("source") != file_name
    ]

    faiss_path = get_faiss_index_path()

    if os.path.exists(faiss_path):
        shutil.rmtree(faiss_path)

    if remaining_docs:
        new_store = FAISS.from_documents(remaining_docs, embeddings_model)
        new_store.save_local(faiss_path)

    return True


def clear_vectorstore():
    faiss_path = get_faiss_index_path()

    if os.path.exists(faiss_path):
        shutil.rmtree(faiss_path)