import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from utils.embeddings import load_vectorstore, search_similar_chunks

load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=2048
)

# ─── RAG Prompt ───────────────────────────────────────────────
RAG_PROMPT = PromptTemplate(
    template="""You are an expert study assistant helping a college student understand their study material.

Use the context below from the student's uploaded documents to answer the question thoroughly.

Context:
{context}

Question: {question}

Instructions:
- Give a detailed, well structured answer
- Use headings, bullet points, and examples where helpful
- Explain concepts clearly like a teacher would
- If the context has relevant information, use it fully
- Cite the source document naturally in your answer
- If you need to elaborate beyond the context to make the explanation complete, do so

Answer:""",
    input_variables=["context", "question"]
)


def format_docs(docs) -> str:
    """Formats retrieved documents into a single context string."""
    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page   = doc.metadata.get("page", 1)
        parts.append(f"[Source: {source}, Page {page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def ask_question(question: str, chat_history: list = []) -> dict:
    if chat_history is None:
        chat_history=[]
    """
    Main RAG function using modern LangChain LCEL chain.
    """
    # Get relevant chunks with confidence scores
    chunks = search_similar_chunks(question, top_k=8)

    if not chunks:
        return {
            "answer":     "No documents uploaded yet. Please upload your notes or PDFs first!",
            "sources":    [],
            "confidence": 0,
        }

    # Load vectorstore and build retriever
    vectorstore = load_vectorstore()
    if vectorstore is None:
        return {
            "answer":     "No documents indexed yet. Please upload files first!",
            "sources":    [],
            "confidence": 0,
        }

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 8}
    )

    # Add chat history context to question
    if chat_history:
        last_turns = chat_history[-3:]
        history_text = "\n".join([
            f"Previous Q: {t['question']}\nPrevious A: {t['answer'][:200]}..."
            for t in last_turns
        ])
        full_question = f"Chat history:\n{history_text}\n\nCurrent question: {question}"
    else:
        full_question = question

    # Build LCEL chain
    chain = (
        {
            "context":  retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )

    # Run chain
    answer = chain.invoke(full_question)

    # Extract sources
    source_docs = retriever.invoke(full_question)
    sources = []
    seen = set()
    for doc in source_docs:
        key = f"{doc.metadata.get('source')} — Page {doc.metadata.get('page')}"
        if key not in seen:
            seen.add(key)
            sources.append({
                "file":    doc.metadata.get("source", "Unknown"),
                "page":    doc.metadata.get("page", 1),
                "preview": doc.page_content[:150] + "..."
            })

    # Average confidence
    avg_confidence = sum(c["confidence"] for c in chunks) // len(chunks)

    return {
        "answer":     answer,
        "sources":    sources,
        "confidence": avg_confidence,
    }

def generate_quiz(topic: str, num_questions: int = 5) -> str:
    vectorstore = load_vectorstore()
    if vectorstore is None:
        return "No documents found. Please upload your study materials first!"

    # Search across ALL documents not just recent
    results = vectorstore.similarity_search_with_score(topic, k=15)
    
    if not results:
        return "Could not find relevant content for this topic."

    context = "\n\n".join([
        f"[{doc.metadata.get('source')}, Page {doc.metadata.get('page')}]\n{doc.page_content}"
        for doc, score in results
    ])

    messages = [
        SystemMessage(content=f"""You are an expert exam question generator.
Generate exactly {num_questions} exam-style questions based on the context below.
Draw questions from ALL sources mentioned in the context, not just one document.

Format each question exactly like this:
Q1. [Question]
Answer: [Detailed Answer]
Explanation: [Why this is important]
Source: [Which document this came from]

Context:
{context}"""),
        HumanMessage(content=f"Generate {num_questions} questions about: {topic}")
    ]

    response = llm.invoke(messages)
    return response.content


def summarize_document(filename: str) -> str:
    vectorstore = load_vectorstore()
    if vectorstore is None:
        return "No documents uploaded yet."

    # Get ALL chunks from this specific file using metadata filter
    all_docs = vectorstore.docstore._dict.values()
    file_docs = [
        doc for doc in all_docs
        if doc.metadata.get("source") == filename
    ]

    if not file_docs:
        # Fallback to similarity search
        file_docs = vectorstore.similarity_search(filename, k=15)
        file_docs = [d for d in file_docs if d.metadata.get("source") == filename]

    if not file_docs:
        return f"Could not find content for {filename}. Try re-uploading."

    # Sort by page number
    file_docs = sorted(file_docs, key=lambda d: d.metadata.get("page", 0))

    context = "\n\n".join([
        f"[Page {d.metadata.get('page')}]\n{d.page_content}"
        for d in file_docs[:20]  # first 20 chunks
    ])

    messages = [
        SystemMessage(content="""You are an expert study assistant.
Summarize the document content clearly and thoroughly.
Include:
- Main topics covered
- Key concepts and definitions  
- Important points to remember
- Any formulas, theorems, or rules mentioned
Format with clear headings and bullet points."""),
        HumanMessage(content=f"Summarize this document:\n\n{context}")
    ]

    response = llm.invoke(messages)
    return response.content