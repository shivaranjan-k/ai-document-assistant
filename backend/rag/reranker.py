import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

from sentence_transformers import CrossEncoder
from backend.rag.config import RERANKER_MODEL

print("Loading reranker...")
reranker = CrossEncoder(RERANKER_MODEL)
