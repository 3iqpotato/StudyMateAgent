import chromadb
from app.core.config import settings

_client = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
    return _client


def get_collection(conversation_id: str):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=f"conv_{conversation_id.replace('-', '_')}",
        metadata={"hnsw:space": "cosine"}
    )


def delete_collection(conversation_id: str):
    client = get_chroma_client()
    try:
        client.delete_collection(f"conv_{conversation_id.replace('-', '_')}")
    except Exception:
        pass