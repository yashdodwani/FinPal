"""Simple abstraction for in-memory/vector search (TODO)."""

class VectorStore:
    """Stub vector store."""
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def search(self, query):
        return {"status": "todo", "query": query, "count": len(self.items)}

