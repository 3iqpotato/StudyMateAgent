from app.services.document_service import search_documents

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_memory",
        "description": "Търси в качените документи и запомнената информация за отговор на въпрос.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Какво да се търси в документите"
                }
            },
            "required": ["query"]
        }
    }
}


def search_memory(query: str, conversation_id: str = None, **kwargs) -> str:
    if not conversation_id:
        return "Няма активен разговор за търсене."

    results = search_documents(query, conversation_id)

    if not results:
        return "Не намерих информация по тази тема в качените документи."

    return "Намерена информация:\n\n" + "\n---\n".join(results)