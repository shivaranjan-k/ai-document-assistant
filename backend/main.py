import sys
import json
import shutil
from pathlib import Path

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

from backend.rag_engine import (
    ask_question,
    stream_question,
    ingest_pdf,
    collection
)

# --------------------------------------------------
# App
# --------------------------------------------------

app = FastAPI()


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_FOLDER = BASE_DIR / "documents"


# Make sure documents folder exists
DOCUMENTS_FOLDER.mkdir(exist_ok=True)


# --------------------------------------------------
# Serve PDF documents
# --------------------------------------------------

app.mount(
    "/documents",
    StaticFiles(directory=str(DOCUMENTS_FOLDER)),
    name="documents"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Conversation sessions
# --------------------------------------------------

sessions = {}


# --------------------------------------------------
# Request model
# --------------------------------------------------

class Question(BaseModel):
    session_id: str
    question: str


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "running"
    }

@app.get("/api/documents")
def list_documents():

    documents = []

    for file in DOCUMENTS_FOLDER.iterdir():

        if file.is_file() and file.suffix.lower() == ".pdf":
            documents.append(file.name)

    return {
        "documents": documents
    }


# --------------------------------------------------
# Normal question endpoint
# --------------------------------------------------

@app.post("/ask")
def ask(data: Question):

    # Create session if it doesn't exist
    if data.session_id not in sessions:
        sessions[data.session_id] = []

    # Get conversation history
    messages = sessions[data.session_id]

    # Ask RAG engine
    result = ask_question(
        data.question,
        messages
    )

    # Store user message
    messages.append({
        "role": "user",
        "content": data.question
    })

    # Store assistant response
    messages.append({
        "role": "assistant",
        "content": result["answer"]
    })

    return result


# --------------------------------------------------
# Streaming question endpoint
# --------------------------------------------------

@app.post("/ask/stream")
def ask_stream(data: Question):

    # Create session if it doesn't exist
    if data.session_id not in sessions:
        sessions[data.session_id] = []

    # Get conversation history
    messages = sessions[data.session_id]

    def generate():

        full_answer_parts = []

        try:
            for item in stream_question(
                data.question,
                messages
            ):
                if item.get("type") == "token":
                    full_answer_parts.append(item.get("content", ""))
                elif item.get("type") == "answer":
                    full_answer_parts.append(item.get("content", ""))

                yield f"data: {json.dumps(item)}\n\n"

            assembled_answer = "".join(full_answer_parts).strip()
            if assembled_answer:
                messages.append({
                    "role": "user",
                    "content": data.question
                })
                messages.append({
                    "role": "assistant",
                    "content": assembled_answer
                })
        except Exception as e:
            print(f"Error during stream generation: {e}")
            raise e

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )



# --------------------------------------------------
# PDF upload endpoint
# --------------------------------------------------

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    try:

        print("\n==============================")
        print("UPLOAD REQUEST RECEIVED")
        print("Filename:", file.filename)
        print("==============================")

        safe_filename = Path(file.filename).name

        # Check file type
        if not safe_filename.lower().endswith(".pdf"):
            return {
                "success": False,
                "message": "Only PDF files are allowed."
            }

        # Create file path
        file_path = DOCUMENTS_FOLDER / safe_filename

        print("Saving PDF to:")
        print(file_path)

        # Save PDF
        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        print("✅ PDF saved successfully")

        # Ingest PDF into ChromaDB
        print("Starting PDF ingestion...")

        result = ingest_pdf(
            str(file_path),
            safe_filename
        )

        print("✅ PDF ingestion completed")

        return {
            "filename": safe_filename,
            **result
        }

    except Exception as e:

        print("\n❌ UPLOAD ERROR")
        print(type(e).__name__)
        print(str(e))

        return {
            "success": False,
            "error": type(e).__name__,
            "message": str(e)
        }
@app.delete("/api/documents/{filename}")
def delete_document(filename: str):

    try:
        # Prevent path traversal
        safe_filename = Path(filename).name

        file_path = DOCUMENTS_FOLDER / safe_filename

        # Check if PDF exists
        if not file_path.exists():
            return {
                "success": False,
                "message": "Document not found."
            }

        # Delete PDF from documents folder
        file_path.unlink()

        # Delete its chunks from ChromaDB
        collection.delete(
            where={
                "source": safe_filename
            }
        )

        return {
            "success": True,
            "message": f"{safe_filename} deleted successfully."
        }

    except Exception as e:
        print("\n❌ DELETE ERROR")
        print(type(e).__name__)
        print(str(e))

        return {
            "success": False,
            "error": type(e).__name__,
            "message": str(e)
        }


# --------------------------------------------------
# Serve Frontend Static Files
# --------------------------------------------------

FRONTEND_FOLDER = BASE_DIR / "frontend"

if FRONTEND_FOLDER.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_FOLDER), html=True),
        name="frontend"
    )


