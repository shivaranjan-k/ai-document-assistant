import sys
import os
import re
from pathlib import Path
import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend to path to reuse create_chunks
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))
from rag_engine import create_chunks

# -----------------------------
# Configuration
# -----------------------------
DOCUMENTS_FOLDER = str(BASE_DIR / "documents")
CHROMA_PATH = str(BASE_DIR / "chroma_db")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# -----------------------------
# Find PDF files
# -----------------------------
pdf_files = [
    file for file in os.listdir(DOCUMENTS_FOLDER)
    if file.lower().endswith(".pdf")
]

print(f"PDF files found: {len(pdf_files)}")
for file in pdf_files:
    print(f"- {file}")

if not pdf_files:
    print("No PDF files found.")
    sys.exit()

# -----------------------------
# Load embedding model
# -----------------------------
print("\nLoading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# ChromaDB
# -----------------------------
client = chromadb.PersistentClient(path=CHROMA_PATH)

try:
    client.delete_collection("pdf_knowledge")
    print("Old collection deleted.")
except Exception:
    print("No old collection found.")

collection = client.create_collection("pdf_knowledge")

# -----------------------------
# Process PDFs
# -----------------------------
all_chunks = []
all_metadatas = []
all_ids = []

chunk_id = 0

for pdf_file in pdf_files:
    pdf_path = os.path.join(DOCUMENTS_FOLDER, pdf_file)
    print(f"\nProcessing: {pdf_file}")

    reader = PdfReader(pdf_path)
    print(f"Pages: {len(reader.pages)}")

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        # Preserve paragraph boundaries while cleaning extra spaces
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                line = " ".join(line.split())
                lines.append(line)
            else:
                lines.append("")

        text = "\n".join(lines)
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")

        text = text.strip()

        # Create overlapping chunks preserving boundaries
        page_chunks = create_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

        for chunk in page_chunks:
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": pdf_file,
                "page": page_number
            })
            all_ids.append(f"{pdf_file}_{page_number}_{chunk_id}")
            chunk_id += 1

# -----------------------------
# Create embeddings
# -----------------------------
print(f"\nTotal chunks: {len(all_chunks)}")
print("Creating embeddings...")
embeddings = model.encode(all_chunks).tolist()
print(f"Embeddings created: {len(embeddings)}")

# -----------------------------
# Store in ChromaDB
# -----------------------------
collection.add(
    ids=all_ids,
    documents=all_chunks,
    embeddings=embeddings,
    metadatas=all_metadatas
)

print(f"\nStored {len(all_chunks)} chunks in ChromaDB.")
print("Multi-PDF ingestion completed!")