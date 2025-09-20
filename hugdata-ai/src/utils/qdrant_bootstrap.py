import os
import asyncio
from typing import Optional


async def ensure_collection(
    name: str,
    vector_size: int = 1536,
    distance: str = "Cosine",
    url: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Ensure a Qdrant collection exists.
    Usage: python -m src.utils.qdrant_bootstrap <collection_name> [vector_size]
    Env: QDRANT_URL, QDRANT_API_KEY
    """
    url = url or os.getenv("QDRANT_URL")
    api_key = api_key or os.getenv("QDRANT_API_KEY")
    if not url:
        raise RuntimeError("QDRANT_URL is not set")

    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams

    client = QdrantClient(url=url, api_key=api_key or None)
    try:
        info = client.get_collection(name)
        if info:
            return True
    except Exception:
        # not existing
        pass

    dist = getattr(Distance, distance.upper(), Distance.COSINE)
    client.recreate_collection(collection_name=name, vectors_config=VectorParams(size=vector_size, distance=dist))
    return True


def _main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.qdrant_bootstrap <collection_name> [vector_size]")
        sys.exit(1)
    name = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 1536
    asyncio.run(ensure_collection(name=name, vector_size=size))
    print(f"Collection '{name}' ensured.")


if __name__ == "__main__":
    _main()

