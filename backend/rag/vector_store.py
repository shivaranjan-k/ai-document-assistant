import warnings
import logging
import chromadb

warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from backend.rag.config import CHROMA_PATH, COLLECTION_NAME

print("Connecting to ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)
