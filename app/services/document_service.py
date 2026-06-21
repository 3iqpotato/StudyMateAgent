import fitz  # pymupdf
import docx
import uuid
from app.core.chroma import get_collection

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def extract_text_from_docx(file_bytes: bytes) -> str:
    import io
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c) > 50]


async def store_document(
    file_bytes: bytes,
    filename: str,
    conversation_id: str,
    user_id: str
) -> int:
    # Извлечи текста
    if filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    elif filename.lower().endswith(".txt"):
        text = file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Неподдържан формат: {filename}")

    if not text.strip():
        raise ValueError("Файлът е празен или не може да се прочете")

    chunks = chunk_text(text)

    collection = get_collection(conversation_id)

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "filename": filename,
            "chunk_index": i
        }
        for i in range(len(chunks))
    ]

    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )

    return len(chunks)


def search_documents(query: str, conversation_id: str, n_results: int = 3) -> list[str]:
    collection = get_collection(conversation_id)
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []