import os
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib import colors
from reportlab.pdfgen import canvas

BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)
PDF_PATH = DOCUMENTS_DIR / "RAG-Based-AI-Document-Assistant-Project-Knowledge-Base.pdf"

class NumberedCanvas(canvas.Canvas):
    """Canvas that performs a two-pass calculation for accurate total page counts."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            return
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Header
        self.drawString(54, 11 * 72 - 36, "RAG-Based AI Document Assistant — Authoritative Project Knowledge Base")
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)
        
        # Footer
        self.line(54, 48, 8.5 * 72 - 54, 48)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 34, page_text)
        self.drawString(54, 34, "CONFIDENTIAL & AUTHORITATIVE — VERIFIED CODEBASE IMPLEMENTATION")
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1A365D")   # Deep navy
    c_secondary = colors.HexColor("#2B6CB0") # Medium slate blue
    c_dark = colors.HexColor("#2D3748")      # Dark charcoal text
    c_light = colors.HexColor("#F7FAFC")     # Light background
    c_border = colors.HexColor("#CBD5E0")    # Border gray

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=8
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceAfter=15
    )

    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568")
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14.5,
        textColor=c_secondary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=c_dark,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_dark,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=5
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2C5282")
    )

    story = []

    # Title Block
    story.append(Spacer(1, 10))
    story.append(Paragraph("RAG-Based AI Document Assistant", title_style))
    story.append(Paragraph("Authoritative Project Knowledge Base & Technical Implementation Specification", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=c_primary, spaceBefore=2, spaceAfter=10))

    meta_table_data = [
        [
            Paragraph("<b>Document Title:</b> RAG-Based AI Document Assistant Project Knowledge Base", meta_style),
            Paragraph("<b>Source Identifier:</b> RAG-Based-AI-Document-Assistant-Project-Knowledge-Base.pdf", meta_style)
        ],
        [
            Paragraph("<b>Scope:</b> Verified Implementation Architecture & Technical Parameters", meta_style),
            Paragraph("<b>Status:</b> Complete, Authoritative Reference Document", meta_style)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Grounding Notice
    notice_text = (
        "<b>AUTHORITATIVE GROUNDING DIRECTIVE:</b> This document contains verified technical facts extracted directly from the "
        "current project codebase and architecture. All details distinguish strictly between verified project implementation, general RAG concepts, "
        "and unsupported items. If something cannot be verified from the code, it is marked: 'Not explicitly verified in the current implementation.'"
    )
    notice_table = Table([[Paragraph(notice_text, callout_style)]], colWidths=[504])
    notice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#3182CE")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(notice_table)
    story.append(Spacer(1, 12))

    # =========================================================================
    # Section 1: Project Overview
    # =========================================================================
    story.append(Paragraph("1. Project Overview", h1_style))
    story.append(Paragraph(
        "<b>What is the RAG-Based AI Document Assistant?</b><br/>"
        "The RAG-Based AI Document Assistant is an enterprise-grade, locally executed Retrieval-Augmented Generation (RAG) system "
        "engineered for privacy-preserving, hallucination-resistant question answering over domain-specific PDF documents. "
        "Running entirely on local compute infrastructure, the application enables users to upload PDF documents, automatically index "
        "them into vector storage, and query them through an interactive web interface. Every answer generated by the assistant is "
        "strictly grounded in the verified textual content of the uploaded PDF knowledge base, accompanied by transparent document filename "
        "and page-level citations.",
        body_style
    ))
    story.append(Paragraph(
        "The system combines an asynchronous FastAPI backend, a persistent ChromaDB vector store, dense vector embeddings via SentenceTransformers "
        "(all-MiniLM-L6-v2), two-stage cross-encoder reranking (cross-encoder/ms-marco-MiniLM-L-6-v2), and local LLM inference powered by "
        "Ollama running Llama 3.2 3B (llama3.2:3b). Real-time response streaming is delivered via Server-Sent Events (SSE) to a Vanilla JavaScript frontend.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 2: Problem Statement
    # =========================================================================
    story.append(Paragraph("2. Problem Statement", h1_style))
    story.append(Paragraph(
        "Standard pre-trained Large Language Models (LLMs) suffer from several critical shortcomings when applied to enterprise document analysis: "
        "<br/>1. <i>Hallucinations and Fabrications:</i> LLMs generate confident but factually inaccurate answers when encountering unfamiliar or domain-specific concepts. "
        "<br/>2. <i>Knowledge Staleness:</i> General LLMs lack access to private, proprietary, or recently updated PDF documents. "
        "<br/>3. <i>Lack of Verifiable Citations:</i> Standard LLMs cannot furnish verifiable page-level evidence for their claims. "
        "<br/>4. <i>Conversational Drift:</i> In multi-turn dialogues, follow-up queries with ambiguous pronouns ('it', 'that project', 'what tech it uses') frequently cause retrieval to pull irrelevant documents or incorrectly attribute general resume skills to specific projects. "
        "<br/>5. <i>Naive RAG Inadequacy:</i> Standard single-stage vector retrieval suffers from low precision, returning noisy chunks that mislead the generator.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 3: Project Objectives
    # =========================================================================
    story.append(Paragraph("3. Project Objectives", h1_style))
    story.append(Paragraph("• <b>Local Document Privacy:</b> Process, embed, store, and query documents locally with zero data leakage to third-party cloud APIs.", bullet_style))
    story.append(Paragraph("• <b>Strict Context Grounding:</b> Constrain the LLM to generate answers solely from verified PDF text, returning 'I don't have enough information to answer that.' when evidence is missing.", bullet_style))
    story.append(Paragraph("• <b>Two-Stage Precision Retrieval:</b> Implement dense vector retrieval (n_results=15) coupled with cross-encoder reranking and a strict -4.0 score threshold to eliminate irrelevant chunks.", bullet_style))
    story.append(Paragraph("• <b>Transparent Citations:</b> Return exact document name and 1-indexed page citations with clickable browser deep-links (#page=N) for every response.", bullet_style))
    story.append(Paragraph("• <b>Robust Conversation Memory:</b> Accurately resolve conversational references to the most recently established entity while strictly prohibiting query-level fact injection.", bullet_style))
    story.append(Paragraph("• <b>Dynamic Document Lifecycle:</b> Support uploading, listing, and deleting PDF documents with synchronized ChromaDB chunk lifecycle management.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 4: High-Level Architecture
    # =========================================================================
    story.append(Paragraph("4. High-Level Architecture", h1_style))
    story.append(Paragraph(
        "The application architecture comprises six decoupled functional layers:",
        body_style
    ))
    story.append(Paragraph("1. <b>Presentation Layer:</b> Vanilla HTML5, CSS3, and modern JavaScript running on port 5500. Handles chat rendering, SSE stream consumption, document upload, and document deletion.", bullet_style))
    story.append(Paragraph("2. <b>API Gateway Layer:</b> FastAPI backend running on Uvicorn (port 8000), exposing REST endpoints and mounting static document files.", bullet_style))
    story.append(Paragraph("3. <b>Query Rewriting Engine:</b> Analyzes conversational dependency (is_context_dependent) and resolves pronouns via Ollama (llama3.2:3b) with recency priority and no fact injection.", bullet_style))
    story.append(Paragraph("4. <b>Dense Vector Retrieval Layer:</b> SentenceTransformers (all-MiniLM-L6-v2) generates 384-d vectors; ChromaDB persistent collection ('pdf_knowledge') retrieves top 15 candidate chunks.", bullet_style))
    story.append(Paragraph("5. <b>Cross-Encoder Reranking Layer:</b> Cross-Encoder (cross-encoder/ms-marco-MiniLM-L-6-v2) scores query-chunk pairs, discards candidates below -4.0, selects Top-K (3), and enforces evidence checks.", bullet_style))
    story.append(Paragraph("6. <b>Generative Synthesis Layer:</b> Ollama runtime running Llama 3.2 3B produces grounded answers, streaming tokens via SSE.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 5: Verified Technology Stack
    # =========================================================================
    story.append(Paragraph("5. Verified Technology Stack", h1_style))
    story.append(Paragraph(
        "<b>What technologies are used in this project?</b><br/>"
        "The verified technologies used in this project, inspected directly from the codebase, are:<br/>"
        "• <b>FastAPI:</b> Asynchronous Python web framework for backend REST API and SSE streaming endpoints (backend/main.py).<br/>"
        "• <b>Uvicorn:</b> High-performance ASGI web server hosting the FastAPI backend on port 8000.<br/>"
        "• <b>ChromaDB:</b> Persistent local vector database (chromadb.PersistentClient) managing the 'pdf_knowledge' collection stored in chroma_db/.<br/>"
        "• <b>SentenceTransformers (all-MiniLM-L6-v2):</b> Dense vector embedding model producing 384-dimensional embeddings for document chunks and search queries.<br/>"
        "• <b>Cross-Encoder (cross-encoder/ms-marco-MiniLM-L-6-v2):</b> Deep transformer cross-attention reranker for precision scoring.<br/>"
        "• <b>Ollama:</b> Local model runtime hosting and executing the Meta Llama 3.2 3B model (llama3.2:3b).<br/>"
        "• <b>Llama 3.2 3B (llama3.2:3b):</b> Local Large Language Model used for query rewriting and response generation.<br/>"
        "• <b>pypdf (PdfReader):</b> Pure Python PDF extraction library for page text extraction and indexing.<br/>"
        "• <b>Vanilla JavaScript / HTML5 / CSS3:</b> Client-side frontend with native Fetch API and Server-Sent Events (SSE) streaming.<br/>"
        "• <b>Python http.server:</b> Lightweight static HTTP server serving the frontend interface on port 5500.<br/>"
        "<i>Boundary Note:</i> External databases (MongoDB, PostgreSQL, MySQL, Redis), container runtimes (Docker, Kubernetes), and cloud providers are <b>Not explicitly verified in the current implementation</b>.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 6: PDF Upload and Ingestion Process
    # =========================================================================
    story.append(Paragraph("6. PDF Upload and Ingestion Process", h1_style))
    story.append(Paragraph(
        "<b>How does the document ingestion process work?</b><br/>"
        "The document ingestion process in the RAG-Based AI Document Assistant works through an automated 7-step pipeline:<br/>"
        "1. <b>File Validation:</b> The client uploads a file via POST /upload. The backend inspects the filename to ensure it ends with '.pdf' (case-insensitive); invalid files are rejected immediately.<br/>"
        "2. <b>Filesystem Storage:</b> The validated PDF stream is saved to the local documents/ directory using shutil.copyfileobj.<br/>"
        "3. <b>Idempotent Chunk Clearing:</b> To prevent duplicate embeddings, the ingestion engine calls collection.delete(where={'source': safe_filename}) on ChromaDB, removing any previous chunks for this document.<br/>"
        "4. <b>Page Extraction:</b> pypdf.PdfReader reads the PDF page-by-page (1-indexed), extracting raw text from each page.<br/>"
        "5. <b>Text Cleaning:</b> Each page's text undergoes whitespace normalization, line-level space collapsing, and paragraph boundary preservation.<br/>"
        "6. <b>Overlapping Chunking:</b> Cleaned text is partitioned into overlapping chunks using create_chunks(text, chunk_size=1000, overlap=200).<br/>"
        "7. <b>Embedding & Storage:</b> Dense 384-dimensional embeddings are generated for all chunks using embedding_model.encode(all_chunks).tolist(). "
        "The chunks, embeddings, metadata ({'source': source_name, 'page': page_number}), and unique IDs ({source_name}_{page_number}_{chunk_id}) are stored in the ChromaDB 'pdf_knowledge' collection.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 7: PDF Text Extraction
    # =========================================================================
    story.append(Paragraph("7. PDF Text Extraction", h1_style))
    story.append(Paragraph(
        "Text extraction is performed using pypdf (pypdf.PdfReader). The reader iterates sequentially through reader.pages, "
        "tracking 1-indexed page numbers (enumerate(reader.pages, start=1)). For each page, page.extract_text() is invoked. "
        "If a page yields empty or whitespace-only text (such as scanned bitmap pages lacking an OCR layer), it is skipped. "
        "Extracted text retains its association with the exact page number, which is preserved in chunk metadata for accurate citation generation.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 8: Text Cleaning
    # =========================================================================
    story.append(Paragraph("8. Text Cleaning", h1_style))
    story.append(Paragraph(
        "Extracted raw text undergoes deterministic normalization to eliminate formatting artifacts while preserving semantic structure:<br/>"
        "• <b>Line Splitting:</b> Text is split into lines via text.splitlines().<br/>"
        "• <b>Whitespace Trimming:</b> Each line is stripped of leading and trailing whitespace (line.strip()).<br/>"
        "• <b>Space Normalization:</b> Multiple consecutive spaces within a line are collapsed into a single space using ' '.join(line.split()).<br/>"
        "• <b>Paragraph Preservation:</b> Empty lines are retained to maintain natural paragraph separation.<br/>"
        "• <b>Re-joining:</b> Lines are recombined using newlines ('\\n'.join(lines)).<br/>"
        "• <b>Break Compaction:</b> Excessive consecutive line breaks ('\\n\\n\\n') are iteratively compacted to double newlines ('\\n\\n').<br/>"
        "• <b>Final Trim:</b> The complete text block is stripped of outer whitespace.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 9: Chunking Strategy
    # =========================================================================
    story.append(Paragraph("9. Chunking Strategy", h1_style))
    story.append(Paragraph(
        "Chunking is handled by create_chunks(text, chunk_size=1000, overlap=200) in backend/rag_engine.py. "
        "The strategy employs hierarchical boundary-aware segmentation:<br/>"
        "• <b>Chunk Size:</b> Exactly 1000 characters maximum.<br/>"
        "• <b>Chunk Overlap:</b> Exactly 200 characters overlap between consecutive chunks.<br/>"
        "• <b>How chunks are created:</b><br/>"
        "  1. <i>Paragraph Splitting:</i> Text is first split into natural blocks on double newlines ('\\n\\n').<br/>"
        "  2. <i>Line Subdivision:</i> If a paragraph block exceeds 1000 characters, it is subdivided by line breaks ('\\n').<br/>"
        "  3. <i>Sentence Subdivision:</i> If any line exceeds 1000 characters, it is split on sentence boundaries using regex re.split(r'(?<=[.!?])\\s+', line).<br/>"
        "  4. <i>Word Boundary Fallback:</i> If an individual sentence exceeds 1000 characters, it is split at the last space before the 1000-character boundary.<br/>"
        "  5. <i>Overlapping Aggregation:</i> Units are assembled until adding another unit exceeds 1000 characters. The chunk is saved, and an overlap slice of the trailing 200 characters (current_chunk[-overlap:]) is extracted, trimmed to the first space to avoid partial words, and used as the prefix for the next chunk.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 10: Embedding Model
    # =========================================================================
    story.append(Paragraph("10. Embedding Model", h1_style))
    story.append(Paragraph(
        "<b>What embedding model does the project use?</b><br/>"
        "The project uses the <b>all-MiniLM-L6-v2</b> embedding model from SentenceTransformers (EMBEDDING_MODEL = 'all-MiniLM-L6-v2').<br/>"
        "• <b>Dimensionality:</b> 384 dimensions.<br/>"
        "• <b>Architecture:</b> A 6-layer MiniLM transformer mapping sentences to a 384-dimensional dense vector space.<br/>"
        "• <b>Role in Pipeline:</b> Used symmetrically for two operations: (1) encoding all document text chunks during ingestion into ChromaDB vectors, and (2) encoding the rewritten search query at query time for nearest-neighbor similarity search.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 11: ChromaDB Configuration
    # =========================================================================
    story.append(Paragraph("11. ChromaDB Configuration", h1_style))
    story.append(Paragraph(
        "• <b>Client Initialization:</b> chromadb.PersistentClient(path=CHROMA_PATH) where CHROMA_PATH points to chroma_db/ at the project root.<br/>"
        "• <b>Collection Name:</b> Exactly 'pdf_knowledge' (collection = client.get_or_create_collection(name='pdf_knowledge')).<br/>"
        "• <b>Storage Backend:</b> Persistent SQLite and Parquet files stored locally on disk.<br/>"
        "• <b>Metadata Schema:</b> Each chunk record contains metadata dictionary: {'source': source_name, 'page': page_number}.<br/>"
        "• <b>ID Schema:</b> Formatted as {source_name}_{page_number}_{chunk_id}.<br/>"
        "• <b>Single Collection Architecture:</b> All ingested PDFs reside in this single collection; multi-collection partitioning is <i>Not explicitly verified in the current implementation</i>.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 12: Similarity Search / Retrieval
    # =========================================================================
    story.append(Paragraph("12. Similarity Search / Retrieval", h1_style))
    story.append(Paragraph(
        "Initial candidate retrieval is executed via ChromaDB vector similarity search. The rewritten query is encoded into a 384-dimensional vector "
        "via embedding_model.encode(search_query).tolist(). ChromaDB is queried with:<br/>"
        "<code>results = collection.query(query_embeddings=[query_embedding], n_results=15, include=['documents', 'distances', 'metadatas'])</code><br/>"
        "The system retrieves exactly <b>15 candidate chunks</b> (n_results=15). This broad candidate pool ensures high recall, capturing candidate chunks "
        "that may use different phrasing, which are subsequently evaluated and filtered by the cross-encoder reranker.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 13: Cross-Encoder Reranking
    # =========================================================================
    story.append(Paragraph("13. Cross-Encoder Reranking", h1_style))
    story.append(Paragraph(
        "• <b>Model Name:</b> cross-encoder/ms-marco-MiniLM-L-6-v2 loaded via CrossEncoder(RERANKER_MODEL).<br/>"
        "• <b>Mechanism:</b> While bi-encoders encode query and document independently, the cross-encoder passes the query and document chunk simultaneously through transformer cross-attention layers, scoring exact semantic relevance.<br/>"
        "• <b>Document Context Prepending:</b> To provide context to the reranker, each document chunk is formatted before scoring with its document title: "
        "<code>Document: {clean_title}\\n{doc}</code> (and annotated with <code>(Candidate / Subject: Shivaranjan K)</code> if the source is a resume).<br/>"
        "• <b>Scoring & Ordering:</b> reranker.predict(pairs) produces a relevance logit score for every candidate. Candidates are sorted in descending order of score.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 14: Reranking Threshold
    # =========================================================================
    story.append(Paragraph("14. Reranking Threshold", h1_style))
    story.append(Paragraph(
        "<b>What is the reranking threshold?</b><br/>"
        "The reranking threshold in this project is exactly <b>-4.0</b> (RERANK_THRESHOLD = -4.0).<br/>"
        "• <b>Filtering Logic:</b> Only chunks with a cross-encoder score >= -4.0 are marked as PASS. Chunks scoring < -4.0 are discarded as FAIL.<br/>"
        "• <b>Top-K Selection:</b> From the passing chunks, at most <b>TOP_K = 3</b> top-scoring chunks are admitted into the final LLM context.<br/>"
        "• <b>Threshold Rejection:</b> If zero chunks score >= -4.0, or if evidence checks fail, retrieval terminates immediately and returns: "
        "<i>'I don't have enough information to answer that.'</i>",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 15: Query Rewriting
    # =========================================================================
    story.append(Paragraph("15. Query Rewriting", h1_style))
    story.append(Paragraph(
        "<b>How does query rewriting work?</b><br/>"
        "Query rewriting is executed by rewrite_query(query, messages) in backend/rag_engine.py:<br/>"
        "1. <b>Dependency Detection:</b> is_context_dependent(query, messages) inspects the query for conversational indicators ('it', 'its', 'this', 'that', 'that project', 'the project', 'tell me more', 'what technologies does it use', 'which one') and first-person pronouns ('who am i', 'my skills', 'my projects'). Standalone domain questions (e.g. 'what is rag', 'what is an llm') bypass rewriting.<br/>"
        "2. <b>Recency Priority & Entity Resolution:</b> The rewriter uses recent conversation turns (messages[-6:]) and the list of available documents (get_available_documents()). It prioritizes the most recently established entity in conversation history, resolving pronouns to that entity.<br/>"
        "3. <b>Strict No-Fact-Injection Rule:</b> The rewriter is strictly prohibited from guessing, injecting, or hallucinating technologies, tools, or claims into the rewritten search query. For example, 'what tech it uses' rewrites to 'What technologies and tools are used in the RAG-Based AI Document Assistant project?', NEVER injecting unmentioned tools.<br/>"
        "4. <b>First-Person Rephrasing:</b> Converts first-person questions into queries about candidate Shivaranjan K.<br/>"
        "5. <b>Output:</b> Returns a single natural-language standalone search question without Boolean operators.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 16: Conversation Memory
    # =========================================================================
    story.append(Paragraph("16. Conversation Memory", h1_style))
    story.append(Paragraph(
        "• <b>Implementation:</b> Managed in backend/main.py via an in-memory dictionary: sessions = {}.<br/>"
        "• <b>Session Identification:</b> Keyed by client-supplied session_id (e.g. 'user1').<br/>"
        "• <b>Data Structure:</b> Maps session_id to a list of message dicts: [{'role': 'user'|'assistant', 'content': '...'}].<br/>"
        "• <b>Usage:</b> Passed to rewrite_query() for entity resolution and included in the generation prompt under PREVIOUS CONVERSATION:.<br/>"
        "• <b>Persistence Status:</b> In-memory only; resets upon backend restart. Persistent database storage is <i>Not explicitly verified in the current implementation</i>.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 17: LLM Generation
    # =========================================================================
    story.append(Paragraph("17. LLM Generation", h1_style))
    story.append(Paragraph(
        "<b>How does the project generate answers?</b><br/>"
        "The project generates answers through an authoritative, multi-stage grounded generation pipeline:<br/>"
        "1. <b>Query Pre-Processing:</b> The user's query and session history are evaluated by rewrite_query() to produce a standalone search query.<br/>"
        "2. <b>Vector Retrieval:</b> The search query is embedded via all-MiniLM-L6-v2 and used to retrieve the top 15 candidate chunks from ChromaDB collection 'pdf_knowledge'.<br/>"
        "3. <b>Cross-Encoder Scoring & Thresholding:</b> The cross-encoder (cross-encoder/ms-marco-MiniLM-L-6-v2) scores candidate query-chunk pairs. Chunks below the -4.0 threshold are filtered out, and the top-scoring chunks (up to TOP_K = 3) are selected.<br/>"
        "4. <b>Evidence Validation:</b> Deterministic checks (check_project_tech_evidence, check_unsupported_named_tech) confirm that the chunks contain explicit factual evidence.<br/>"
        "5. <b>Context & Prompt Assembly:</b> The selected chunks are concatenated as PDF CONTEXT and combined with PREVIOUS CONVERSATION and USER QUESTION inside a strict grounding prompt.<br/>"
        "6. <b>LLM Inference:</b> Ollama executes Llama 3.2 3B (llama3.2:3b) to synthesize a direct, concise answer derived ONLY from the provided PDF context.<br/>"
        "7. <b>Citation Attachment:</b> Source document names and 1-indexed page numbers are appended and returned to the client.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 18: Ollama Configuration
    # =========================================================================
    story.append(Paragraph("18. Ollama Configuration", h1_style))
    story.append(Paragraph(
        "• <b>Runtime Environment:</b> Local Ollama service daemon running on the host machine at http://127.0.0.1:11434.<br/>"
        "• <b>Python Client:</b> Official Python ollama package (from ollama import chat).<br/>"
        "• <b>Designated Model:</b> LLM_MODEL = 'llama3.2:3b' (Meta Llama 3.2 3B parameters).<br/>"
        "• <b>Invocation Modes:</b> Synchronous invocation for query rewriting and ask_question(); streaming invocation (stream=True) for stream_question().",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 19: Grounding Rules
    # =========================================================================
    story.append(Paragraph("19. Grounding Rules", h1_style))
    story.append(Paragraph(
        "To guarantee complete factual reliability, the system enforces multi-layered grounding rules:<br/>"
        "1. <b>Strict Context Confinement:</b> Answers must be derived SOLELY from the provided PDF CONTEXT.<br/>"
        "2. <b>History Non-Contamination Rule:</b> Previous conversation is used ONLY to resolve conversational references; it must NEVER be used as factual evidence.<br/>"
        "3. <b>Resume Skills Isolation:</b> General resume sections ('TECHNICAL SKILLS', 'Developer Tools') must NEVER be attributed to a specific project.<br/>"
        "4. <b>Educational Guide Isolation:</b> General educational guides (e.g. 'LLMs & RAG: From Zero to Advanced') must NEVER be cited as project implementation facts.<br/>"
        "5. <b>Deterministic Evidence Verification:</b> check_project_tech_evidence() scans candidate chunks for explicit project bullet points or action verbs (built, designed, implementing) before LLM generation.<br/>"
        "6. <b>Named Entity Guard:</b> check_unsupported_named_tech() detects inquiries about unmentioned tools (e.g. PostgreSQL), immediately returning 'I don't have enough information to answer that.'",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 20: Streaming Response
    # =========================================================================
    story.append(Paragraph("20. Streaming Response", h1_style))
    story.append(Paragraph(
        "Real-time streaming is implemented via POST /ask/stream using FastAPI's StreamingResponse(media_type='text/event-stream'). "
        "The generator stream_question() in backend/rag_engine.py yields Server-Sent Events (SSE) in standard format (data: <json>\\n\\n):<br/>"
        "• <b>Token Events:</b> {'type': 'token', 'content': chunk.message.content} emitted token-by-token as Ollama generates.<br/>"
        "• <b>Direct Answer Events:</b> {'type': 'answer', 'content': 'I don\\'t have enough information to answer that.'} when evidence is absent.<br/>"
        "• <b>Sources Event:</b> {'type': 'sources', 'sources': [{'source': filename, 'page': page_num}]} emitted upon completion.<br/>"
        "In the frontend, app.js reads the response stream using ReadableStream reader (response.body.getReader()), progressively updating the DOM.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 21: Source/Page Citation Handling
    # =========================================================================
    story.append(Paragraph("21. Source/Page Citation Handling", h1_style))
    story.append(Paragraph(
        "• <b>Metadata Extraction:</b> Every chunk stored in ChromaDB records its source filename and 1-indexed page number.<br/>"
        "• <b>Deduplication:</b> The engine deduplicates citations across selected chunks using (source, page) tuples.<br/>"
        "• <b>UI Rendering:</b> Citations are displayed below assistant messages as a collapsible card: '📚 Sources (N)'.<br/>"
        "• <b>Deep Linking:</b> Each source card is rendered as an anchor link pointing to: "
        "<code>http://127.0.0.1:8000/documents/{filename}#page={page}</code>, opening the PDF directly at the cited page in a new browser tab.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 22: Document Management
    # =========================================================================
    story.append(Paragraph("22. Document Management", h1_style))
    story.append(Paragraph(
        "<b>How does document deletion work?</b><br/>"
        "In the RAG-Based AI Document Assistant, document deletion is executed through the <code>DELETE /api/documents/{filename}</code> endpoint in backend/main.py. "
        "The document deletion process operates in two coordinated phases:<br/>"
        "1. <b>Filesystem Deletion:</b> The backend receives the document filename, sanitizes it using <code>Path(filename).name</code> to prevent path traversal attacks, locates the file in the <code>documents/</code> folder, and unlinks it from disk using <code>file_path.unlink()</code>.<br/>"
        "2. <b>ChromaDB Vector Purging:</b> Immediately after the file is removed, the backend purges all corresponding vector embeddings and text chunks from the ChromaDB collection using <code>collection.delete(where={'source': safe_filename})</code>.<br/>"
        "This two-phase deletion ensures that deleted documents are completely eliminated from both physical storage and vector retrieval, preventing ghost chunks or stale responses.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Document Upload and Listing:</b><br/>"
        "• <b>Document Listing:</b> <code>GET /api/documents</code> scans the documents/ directory and returns a JSON list of all available PDF filenames.<br/>"
        "• <b>Document Upload:</b> <code>POST /upload</code> accepts multipart PDF files, saves them to documents/, and triggers ingest_pdf() to index them into ChromaDB.<br/>"
        "• <b>Static Serving:</b> The documents/ directory is mounted at /documents via FastAPI StaticFiles for browser access.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 23: Backend API Endpoints
    # =========================================================================
    story.append(Paragraph("23. Backend API Endpoints", h1_style))
    story.append(Paragraph(
        "The following table details all verified endpoints exposed by backend/main.py:",
        body_style
    ))

    endpoint_data = [
        ["Method", "Endpoint Path", "Request Format", "Response Format", "Description"],
        ["GET", "/health", "None", "JSON: {status: 'running'}", "Health check and service status"],
        ["GET", "/api/documents", "None", "JSON: {documents: [string]}", "Lists all uploaded PDF documents"],
        ["POST", "/upload", "Multipart form: file", "JSON: {success, chunks, filename}", "Uploads and ingests a PDF into ChromaDB"],
        ["DELETE", "/api/documents/{filename}", "URL path parameter", "JSON: {success, message}", "Deletes PDF file and purges ChromaDB chunks"],
        ["POST", "/ask", "JSON: {session_id, question}", "JSON: {answer, sources}", "Synchronous question answering endpoint"],
        ["POST", "/ask/stream", "JSON: {session_id, question}", "SSE (text/event-stream)", "Streaming token and source citation endpoint"],
        ["GET", "/documents/{filename}", "URL path parameter", "Binary PDF file stream", "FastAPI StaticFiles mount for document viewing"]
    ]
    t_endpoints = Table(endpoint_data, colWidths=[45, 120, 115, 115, 109])
    t_endpoints.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('BACKGROUND', (0, 1), (-1, -1), c_light),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_endpoints)
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 24: Current Limitations
    # =========================================================================
    story.append(Paragraph("24. Current Limitations", h1_style))
    story.append(Paragraph("• <b>In-Memory Session Volatility:</b> Sessions are stored in a Python dictionary (sessions = {}) and reset upon backend server restart.", bullet_style))
    story.append(Paragraph("• <b>Non-OCR Text Extraction:</b> Scanned image PDFs without an embedded text layer yield empty text via pypdf.", bullet_style))
    story.append(Paragraph("• <b>Fixed Character Chunking:</b> The 1000-character chunk window with 200-character overlap does not perform table-aware or structural layout analysis.", bullet_style))
    story.append(Paragraph("• <b>Single Shared Collection:</b> All indexed PDFs share a single ChromaDB collection ('pdf_knowledge') without multi-tenant user isolation.", bullet_style))
    story.append(Paragraph("• <b>Local Hardware Dependency:</b> Reranker and LLM inference speeds depend entirely on the host machine's CPU/GPU capabilities.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 25: Future Improvements
    # =========================================================================
    story.append(Paragraph("25. Future Improvements", h1_style))
    story.append(Paragraph("• <b>Persistent Database Session Storage:</b> Integrate SQLite, PostgreSQL, or Redis to persist conversation history across server restarts.", bullet_style))
    story.append(Paragraph("• <b>OCR Integration:</b> Incorporate OCR engines (e.g. Tesseract or Surya) to extract text from scanned PDFs and document images.", bullet_style))
    story.append(Paragraph("• <b>Hybrid Retrieval (BM25 + Dense Vectors):</b> Implement hybrid search combining sparse keyword matching (BM25) with dense vector similarity.", bullet_style))
    story.append(Paragraph("• <b>Layout-Aware Chunking:</b> Adopt document structure parsing for tables, charts, and hierarchical headings.", bullet_style))
    story.append(Paragraph("• <b>User Authentication & Multi-Tenancy:</b> Add user identity management, role-based access control, and workspace-isolated ChromaDB collections.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # Section 26: Interview Explanation
    # =========================================================================
    story.append(Paragraph("26. Interview Explanation", h1_style))
    story.append(Paragraph(
        "<b>Architectural Rationale & Engineering Walkthrough:</b><br/>"
        "When explaining this project in a technical interview, highlight the design decisions that distinguish it from standard RAG tutorials:<br/>"
        "1. <i>Why Two-Stage Retrieval?</i> Dense vector retrieval (all-MiniLM-L6-v2) excels at fast bi-encoder approximate search across thousands of chunks, but lacks fine-grained semantic discrimination. Adding a Cross-Encoder (ms-marco-MiniLM-L-6-v2) performs joint query-document cross-attention, re-scoring candidates with high semantic accuracy.<br/>"
        "2. <i>Why a Negative Rerank Threshold (-4.0)?</i> Naive RAG pipelines always return the top-K chunks regardless of relevance, forcing the LLM to answer even when the documents contain zero pertinent information. A hard threshold (-4.0) guarantees that irrelevant chunks are discarded before reaching the generation phase.<br/>"
        "3. <i>How Was Conversational Drift Solved?</i> Multi-turn RAG systems often suffer when users ask follow-up questions ('What tech it uses?'). We implemented a query rewriting stage using Ollama (Llama 3.2 3B) that prioritizes entity recency while strictly forbidding query-level fact injection.<br/>"
        "4. <i>How Is Grounding Guaranteed?</i> Through a defense-in-depth approach combining strict prompt constraints, programmatic evidence checks (check_project_tech_evidence), and named-entity safeguards (check_unsupported_named_tech). If evidence is missing, the system deterministically replies: 'I don't have enough information to answer that.'<br/>"
        "5. <i>Full Local Privacy:</i> The entire pipeline—ingestion, embeddings, vector database, reranking, and generative synthesis—runs locally with zero cloud API dependencies.",
        body_style
    ))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF at: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
