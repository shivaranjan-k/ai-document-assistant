import re
from pypdf import PdfReader
from backend.rag.vector_store import collection
from backend.rag.embeddings import embedding_model


def create_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Splits text into chunks of at most chunk_size characters with overlap."""
    if not text or not text.strip():
        return []

    raw_blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    units = []

    for block in raw_blocks:
        if len(block) <= chunk_size:
            units.append(block)
        else:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            current_unit = ""
            for line in lines:
                if len(line) > chunk_size:
                    sentences = re.split(r"(?<=[.!?])\s+", line)
                    for sent in sentences:
                        sent = sent.strip()
                        if not sent:
                            continue
                        if len(current_unit) + len(sent) + 1 <= chunk_size:
                            current_unit = (current_unit + " " + sent).strip()
                        else:
                            if current_unit:
                                units.append(current_unit)
                            while len(sent) > chunk_size:
                                split_pt = sent.rfind(" ", 0, chunk_size)
                                if split_pt == -1:
                                    split_pt = chunk_size
                                units.append(sent[:split_pt].strip())
                                sent = sent[split_pt:].strip()
                            current_unit = sent
                else:
                    if len(current_unit) + len(line) + 1 <= chunk_size:
                        current_unit = (current_unit + "\n" + line).strip()
                    else:
                        if current_unit:
                            units.append(current_unit)
                        current_unit = line
            if current_unit:
                units.append(current_unit)

    chunks = []
    current_chunk = ""

    for unit in units:
        unit = unit.strip()
        if not unit:
            continue

        if not current_chunk:
            current_chunk = unit
        elif len(current_chunk) + len(unit) + 1 <= chunk_size:
            current_chunk += "\n" + unit
        else:
            chunks.append(current_chunk.strip())
            overlap_text = (
                current_chunk[-overlap:]
                if len(current_chunk) > overlap
                else current_chunk
            )
            first_nl = overlap_text.find("\n")
            if first_nl != -1 and first_nl < len(overlap_text) // 2:
                overlap_text = overlap_text[first_nl + 1:]
            else:
                first_space = overlap_text.find(" ")
                if first_space != -1 and first_space < len(overlap_text) // 2:
                    overlap_text = overlap_text[first_space + 1:]
            current_chunk = (overlap_text + "\n" + unit).strip()

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def ingest_pdf(pdf_path: str, source_name: str) -> dict:
    """Ingests a PDF file into ChromaDB, creating vector embeddings."""
    print(f"\n📄 Ingesting: {source_name}")

    reader = PdfReader(pdf_path)

    all_chunks = []
    all_metadatas = []
    all_ids = []
    chunk_id = 0

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

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
        page_chunks = create_chunks(text, chunk_size=1000, overlap=200)

        for chunk in page_chunks:
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": source_name,
                "page": page_number
            })
            all_ids.append(f"{source_name}_{page_number}_{chunk_id}")
            chunk_id += 1

    if not all_chunks:
        return {
            "success": False,
            "message": "No readable text found in PDF."
        }

    try:
        collection.delete(where={"source": source_name})
        print(f"🗑️ Removed old chunks for: {source_name}")
    except Exception as e:
        print(f"Note on clearing old chunks: {e}")

    print(f"📦 Chunks created: {len(all_chunks)}")

    embeddings = embedding_model.encode(all_chunks).tolist()
    collection.add(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas
    )

    print(f"✅ Stored {len(all_chunks)} chunks in ChromaDB.")

    return {
        "success": True,
        "chunks": len(all_chunks),
        "message": "PDF ingested successfully."
    }
