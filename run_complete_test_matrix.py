import sys
import os
import re
import json
import time
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from rag_engine import ask_question, stream_question, ingest_pdf, collection, FALLBACK_RESPONSE
from reportlab.pdfgen import canvas

def print_banner(text):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)

test_results = {}
failures = []

def record_test(test_id, name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    test_results[test_id] = {"name": name, "status": status, "details": details}
    if not passed:
        failures.append((test_id, name, details))
    print(f"[{test_id}] {name} => {status}")
    if details:
        print(f"    Details: {details}")

print_banner("RUNNING COMPLETE 28-TEST MATRIX FOR DOCUMENT-AGNOSTIC RAG CORE")

# Ingest all standard PDFs in documents directory
pdf_folder = BASE_DIR / "documents"
for pdf_file in pdf_folder.glob("*.pdf"):
    ingest_pdf(str(pdf_file), pdf_file.name)

# -------------------------------------------------------------
# TEST 1: Direct Factual Query
# -------------------------------------------------------------
q1 = "What is inheritance?"
res1 = ask_question(q1, [])
t1_pass = (
    "class" in res1["answer"].lower() or "object" in res1["answer"].lower() or "subclass" in res1["answer"].lower() or "superclass" in res1["answer"].lower() or "extends" in res1["answer"].lower() or "inherit" in res1["answer"].lower()
) and len(res1["sources"]) > 0
record_test("TEST 1", "Direct Factual Query ('What is inheritance?')", t1_pass, f"Answer: {res1['answer'][:100]}...")

# -------------------------------------------------------------
# TEST 2: Pronoun Follow-up
# -------------------------------------------------------------
history2 = [
    {"role": "user", "content": "What is inheritance?"},
    {"role": "assistant", "content": res1["answer"]}
]
res2 = ask_question("Explain it simply.", history2, return_details=True)
t2_pass = (
    "inheritance" in res2.get("search_query", "").lower()
    and res2["answer"] != FALLBACK_RESPONSE
)
record_test("TEST 2", "Pronoun Follow-up ('Explain it simply.')", t2_pass, f"Resolved Query: {res2.get('search_query')}")

# -------------------------------------------------------------
# TEST 3: Elliptical Follow-up
# -------------------------------------------------------------
res3 = ask_question("Give me an example.", history2, return_details=True)
t3_pass = (
    "inheritance" in res3.get("search_query", "").lower()
    and res3["answer"] != FALLBACK_RESPONSE
)
record_test("TEST 3", "Elliptical Follow-up ('Give me an example.')", t3_pass, f"Resolved Query: {res3.get('search_query')}")

# -------------------------------------------------------------
# TEST 4: Elliptical Advantages Follow-up
# -------------------------------------------------------------
res4 = ask_question("What are the advantages?", history2, return_details=True)
t4_pass = (
    "inheritance" in res4.get("search_query", "").lower()
)
record_test("TEST 4", "Elliptical Advantages ('What are the advantages?')", t4_pass, f"Resolved Query: {res4.get('search_query')}")

# -------------------------------------------------------------
# TEST 5: Mechanism Follow-up
# -------------------------------------------------------------
res5 = ask_question("How does it work?", history2, return_details=True)
t5_pass = (
    "inheritance" in res5.get("search_query", "").lower()
)
record_test("TEST 5", "Mechanism Follow-up ('How does it work?')", t5_pass, f"Resolved Query: {res5.get('search_query')}")

# -------------------------------------------------------------
# TEST 6: Topic Switch
# -------------------------------------------------------------
res6 = ask_question("What is RAG?", history2, return_details=True)
t6_pass = (
    "rag" in res6.get("search_query", "").lower()
    and "inheritance" not in res6.get("search_query", "").lower()
)
record_test("TEST 6", "Topic Switch ('What is RAG?')", t6_pass, f"Resolved Query: {res6.get('search_query')}")

# -------------------------------------------------------------
# TEST 7: Topic Switch + Follow-up
# -------------------------------------------------------------
history7 = [
    {"role": "user", "content": "What is inheritance?"},
    {"role": "assistant", "content": res1["answer"]},
    {"role": "user", "content": "What is RAG?"},
    {"role": "assistant", "content": res6["answer"]}
]
res7 = ask_question("Give me an example.", history7, return_details=True)
t7_pass = (
    "rag" in res7.get("search_query", "").lower()
    and "inheritance" not in res7.get("search_query", "").lower()
)
record_test("TEST 7", "Topic Switch + Follow-up (Expected Topic: RAG)", t7_pass, f"Resolved Query: {res7.get('search_query')}")

# -------------------------------------------------------------
# TEST 8: Reverse Topic Switch
# -------------------------------------------------------------
history8 = [
    {"role": "user", "content": "What is RAG?"},
    {"role": "assistant", "content": res6["answer"]},
    {"role": "user", "content": "What is inheritance?"},
    {"role": "assistant", "content": res1["answer"]}
]
res8 = ask_question("Explain it simply.", history8, return_details=True)
t8_pass = (
    "inheritance" in res8.get("search_query", "").lower()
    and "rag" not in res8.get("search_query", "").lower()
)
record_test("TEST 8", "Reverse Topic Switch (Expected Topic: inheritance)", t8_pass, f"Resolved Query: {res8.get('search_query')}")

# -------------------------------------------------------------
# TEST 9: Explicit Topic Override
# -------------------------------------------------------------
res9 = ask_question("What is RAG used for?", history8, return_details=True)
t9_pass = (
    "rag" in res9.get("search_query", "").lower()
    and "inheritance" not in res9.get("search_query", "").lower()
)
record_test("TEST 9", "Explicit Topic Override ('What is RAG used for?')", t9_pass, f"Resolved Query: {res9.get('search_query')}")

# -------------------------------------------------------------
# TEST 10: Standalone Protection
# -------------------------------------------------------------
res10 = ask_question("What is Java?", history8, return_details=True)
t10_pass = (
    res10.get("search_query", "").strip().lower() == "what is java?"
)
record_test("TEST 10", "Standalone Protection ('What is Java?')", t10_pass, f"Resolved Query: {res10.get('search_query')}")

# -------------------------------------------------------------
# TEST 11: Absent Fact Fallback
# -------------------------------------------------------------
res11 = ask_question("What is the refund policy for orbital spaceflights under section 4.2?", [])
t11_pass = (
    res11["answer"] == FALLBACK_RESPONSE
    and res11["sources"] == []
)
record_test("TEST 11", "Absent Fact Fallback", t11_pass, f"Answer: {res11['answer']}, Sources: {res11['sources']}")

# -------------------------------------------------------------
# TEST 12: General Skill vs Specific Entity (Cross-Document Isolation)
# -------------------------------------------------------------
pdf_a_path = BASE_DIR / "documents" / "Test_DocA_Skills.pdf"
pdf_b_path = BASE_DIR / "documents" / "Test_DocB_Entity.pdf"
try:
    c_a = canvas.Canvas(str(pdf_a_path))
    c_a.drawString(100, 750, "Technical Profile Catalog")
    c_a.drawString(100, 720, "Supported Technologies: HyperLedger, GraphQL, Rust, WebAssembly")
    c_a.save()

    c_b = canvas.Canvas(str(pdf_b_path))
    c_b.drawString(100, 750, "System Architecture Spec: Project Zeta")
    c_b.drawString(100, 720, "Project Zeta is a distributed microservice for financial clearing.")
    c_b.drawString(100, 700, "Database: SQLite. Language: C++.")
    c_b.save()

    ingest_pdf(str(pdf_a_path), "Test_DocA_Skills.pdf")
    ingest_pdf(str(pdf_b_path), "Test_DocB_Entity.pdf")

    res12 = ask_question("Does Project Zeta use HyperLedger?", [])
    t12_pass = (
        res12["answer"] == FALLBACK_RESPONSE
        and res12["sources"] == []
    )
    record_test("TEST 12", "General Skill vs Specific Entity Isolation", t12_pass, f"Answer: {res12['answer']}, Sources: {res12['sources']}")
finally:
    try:
        collection.delete(where={"source": "Test_DocA_Skills.pdf"})
        collection.delete(where={"source": "Test_DocB_Entity.pdf"})
    except Exception:
        pass
    if pdf_a_path.exists(): pdf_a_path.unlink()
    if pdf_b_path.exists(): pdf_b_path.unlink()

# -------------------------------------------------------------
# TEST 13: Multiple Documents Source Attribution
# -------------------------------------------------------------
res13 = ask_question("Explain polymorphism in Java.", [])
t13_pass = any("java-oop-notes.pdf" in s["source"].lower() for s in res13["sources"])
record_test("TEST 13", "Multiple Documents Source Attribution", t13_pass, f"Sources: {res13['sources']}")

# -------------------------------------------------------------
# TEST 14: Source Fidelity
# -------------------------------------------------------------
res14 = ask_question("What is RAG?", [])
t14_pass = (
    len(res14["sources"]) > 0
    and all(s["source"] and s["page"] for s in res14["sources"])
)
record_test("TEST 14", "Source Fidelity Verification", t14_pass, f"Sources: {res14['sources']}")

# -------------------------------------------------------------
# TEST 15: Streaming Parity
# -------------------------------------------------------------
sync_res = ask_question("What is an LLM?", [])
stream_tokens = []
stream_sources = []
for item in stream_question("What is an LLM?", []):
    if item["type"] == "token":
        stream_tokens.append(item["content"])
    elif item["type"] == "sources":
        stream_sources = item["sources"]
stream_ans = "".join(stream_tokens).strip()

t15_pass = (
    len(sync_res["sources"]) == len(stream_sources)
    and (sync_res["answer"] == FALLBACK_RESPONSE) == (stream_ans == FALLBACK_RESPONSE)
)
record_test("TEST 15", "Streaming Parity (/ask vs /ask/stream)", t15_pass, f"Sync Ans: {sync_res['answer'][:60]}... | Stream Ans: {stream_ans[:60]}...")

# -------------------------------------------------------------
# TEST 16: Arbitrary New PDF Ingestion & Supported Q
# -------------------------------------------------------------
policy_pdf = BASE_DIR / "documents" / "Test_Company_Policy_2026.pdf"
try:
    c_p = canvas.Canvas(str(policy_pdf))
    c_p.drawString(100, 750, "Acme International Remote Work Policy 2026")
    c_p.drawString(100, 720, "Section 1: Work Hours")
    c_p.drawString(100, 700, "Core collaboration hours are 10:00 AM to 4:00 PM Eastern Time.")
    c_p.drawString(100, 680, "Section 2: Equipment Allowance")
    c_p.drawString(100, 660, "Employees receive an annual stipend of twelve hundred dollars for home office equipment.")
    c_p.save()

    ingest_pdf(str(policy_pdf), "Test_Company_Policy_2026.pdf")

    res16 = ask_question("What is the annual home office equipment stipend under company policy?", [])
    t16_pass = (
        ("twelve hundred" in res16["answer"].lower() or "1200" in res16["answer"])
        and any(s["source"] == "Test_Company_Policy_2026.pdf" for s in res16["sources"])
    )
    record_test("TEST 16", "Arbitrary New PDF Ingestion & Supported Q", t16_pass, f"Answer: {res16['answer']}, Sources: {res16['sources']}")

    # -------------------------------------------------------------
    # TEST 17: Arbitrary Unsupported Q against New PDF
    # -------------------------------------------------------------
    res17 = ask_question("What is the company policy on pet travel insurance?", [])
    t17_pass = (
        res17["answer"] == FALLBACK_RESPONSE
        and res17["sources"] == []
    )
    record_test("TEST 17", "Arbitrary Unsupported Q against New PDF", t17_pass, f"Answer: {res17['answer']}")

    # -------------------------------------------------------------
    # TEST 18: Follow-up Questions against Arbitrary New PDF
    # -------------------------------------------------------------
    history18 = [
        {"role": "user", "content": "What are the core collaboration hours under company policy?"},
        {"role": "assistant", "content": "Core collaboration hours are 10:00 AM to 4:00 PM Eastern Time."}
    ]
    res18 = ask_question("What about equipment allowance?", history18, return_details=True)
    t18_pass = (
        "equipment" in res18.get("search_query", "").lower()
        and ("twelve hundred" in res18["answer"].lower() or "1200" in res18["answer"])
    )
    record_test("TEST 18", "Follow-up Questions against Arbitrary New PDF", t18_pass, f"Resolved Query: {res18.get('search_query')}, Ans: {res18['answer']}")

finally:
    try:
        collection.delete(where={"source": "Test_Company_Policy_2026.pdf"})
    except Exception:
        pass
    if policy_pdf.exists(): policy_pdf.unlink()

# -------------------------------------------------------------
# TEST 19: Contradictory Evidence Test
# -------------------------------------------------------------
pdf_contra = BASE_DIR / "documents" / "Test_Contradictory_Doc.pdf"
try:
    c_c = canvas.Canvas(str(pdf_contra))
    c_c.drawString(100, 750, "System Deployment Manual: Core Service")
    c_c.drawString(100, 720, "Module A: Primary Database is PostgreSQL.")
    c_c.drawString(100, 700, "Module B: Primary Database is MySQL.")
    c_c.save()

    ingest_pdf(str(pdf_contra), "Test_Contradictory_Doc.pdf")

    res19 = ask_question("Which primary database does Core Service use?", [])
    t19_pass = (
        ("postgresql" in res19["answer"].lower() and "mysql" in res19["answer"].lower())
        or res19["answer"] == FALLBACK_RESPONSE
    )
    record_test("TEST 19", "Contradictory Evidence Handling", t19_pass, f"Answer: {res19['answer']}")
finally:
    try:
        collection.delete(where={"source": "Test_Contradictory_Doc.pdf"})
    except Exception:
        pass
    if pdf_contra.exists(): pdf_contra.unlink()

# -------------------------------------------------------------
# TEST 20: Entity Ambiguity Test
# -------------------------------------------------------------
pdf_ambig = BASE_DIR / "documents" / "Test_Ambiguity_Doc.pdf"
try:
    c_m = canvas.Canvas(str(pdf_ambig))
    c_m.drawString(100, 750, "Multi-Project Spec")
    c_m.drawString(100, 720, "Project Alpha uses Python for backend operations.")
    c_m.drawString(100, 700, "Project Beta uses Java for backend operations.")
    c_m.save()

    ingest_pdf(str(pdf_ambig), "Test_Ambiguity_Doc.pdf")

    res20 = ask_question("What language does it use?", [])
    t20_pass = (
        res20["answer"] == FALLBACK_RESPONSE
        and res20["sources"] == []
    )
    record_test("TEST 20", "Entity Ambiguity Protection", t20_pass, f"Answer: {res20['answer']}")
finally:
    try:
        collection.delete(where={"source": "Test_Ambiguity_Doc.pdf"})
    except Exception:
        pass
    if pdf_ambig.exists(): pdf_ambig.unlink()

# -------------------------------------------------------------
# TEST 21: Conversational Branching
# -------------------------------------------------------------
branch_history = []
q21_1 = "What is Java?"
r21_1 = ask_question(q21_1, branch_history)
branch_history.append({"role": "user", "content": q21_1})
branch_history.append({"role": "assistant", "content": r21_1["answer"]})

q21_2 = "What is inheritance?"
r21_2 = ask_question(q21_2, branch_history)
branch_history.append({"role": "user", "content": q21_2})
branch_history.append({"role": "assistant", "content": r21_2["answer"]})

q21_3 = "Give me an example."
r21_3 = ask_question(q21_3, branch_history, return_details=True)
branch_history.append({"role": "user", "content": q21_3})
branch_history.append({"role": "assistant", "content": r21_3["answer"]})
topic3 = r21_3.get("search_query", "").lower()

q21_4 = "What about Java interfaces?"
r21_4 = ask_question(q21_4, branch_history)
branch_history.append({"role": "user", "content": q21_4})
branch_history.append({"role": "assistant", "content": r21_4["answer"]})

q21_5 = "Give me an example."
r21_5 = ask_question(q21_5, branch_history, return_details=True)
topic5 = r21_5.get("search_query", "").lower()

t21_pass = (
    "inheritance" in topic3
    and ("interface" in topic5 or "java" in topic5)
    and "inheritance" not in topic5
)
record_test("TEST 21", "Conversational Branching Active Topic Update", t21_pass, f"Topic 3: {topic3} | Topic 5: {topic5}")

# -------------------------------------------------------------
# TEST 22: Reference Resolution Cases A, B, C
# -------------------------------------------------------------
pdf_ref = BASE_DIR / "documents" / "Test_Reference_Doc.pdf"
try:
    c_r = canvas.Canvas(str(pdf_ref))
    c_r.drawString(100, 750, "Projects Summary")
    c_r.drawString(100, 720, "Project Alpha is built using Python.")
    c_r.drawString(100, 700, "Project Beta is built using Go.")
    c_r.save()

    ingest_pdf(str(pdf_ref), "Test_Reference_Doc.pdf")

    # Case A: Project Alpha -> What language does it use?
    h_a = [{"role": "user", "content": "What is Project Alpha?"}, {"role": "assistant", "content": "Project Alpha is built using Python."}]
    r22_a = ask_question("What language does it use?", h_a, return_details=True)
    pass_a = "python" in r22_a["answer"].lower() and "alpha" in r22_a.get("search_query", "").lower()

    # Case B: Project Alpha -> Project Beta -> What language does it use?
    h_b = [
        {"role": "user", "content": "What is Project Alpha?"}, {"role": "assistant", "content": "Project Alpha is built using Python."},
        {"role": "user", "content": "What is Project Beta?"}, {"role": "assistant", "content": "Project Beta is built using Go."}
    ]
    r22_b = ask_question("What language does it use?", h_b, return_details=True)
    pass_b = "go" in r22_b["answer"].lower() and "beta" in r22_b.get("search_query", "").lower()

    # Case C: What language does it use? (No context)
    r22_c = ask_question("What language does it use?", [])
    pass_c = r22_c["answer"] == FALLBACK_RESPONSE and r22_c["sources"] == []

    t22_pass = pass_a and pass_b and pass_c
    record_test("TEST 22", "Reference Resolution (Cases A, B, C)", t22_pass, f"A: {pass_a}, B: {pass_b}, C: {pass_c}")
finally:
    try:
        collection.delete(where={"source": "Test_Reference_Doc.pdf"})
    except Exception:
        pass
    if pdf_ref.exists(): pdf_ref.unlink()

# -------------------------------------------------------------
# TEST 23: Code Audit for Hardcoded Patterns
# -------------------------------------------------------------
files_to_audit = [
    BASE_DIR / "backend" / "rag_engine.py",
    BASE_DIR / "backend" / "main.py",
    BASE_DIR / "pdf_rag_final.py"
]

forbidden_terms = [
    r"\bshivaranjan\b",
    r"\bsara\s+holidays\b",
    r"\bprompt\s+engineering\b",
    r"\bbuilt\s+a\s+full-stack\b",
    r"\bfreelance\b",
    r"\bcandidate\s+resume\b",
    r"\bmy\s+resume\b",
]

audit_passed = True
for fpath in files_to_audit:
    if not fpath.exists():
        continue
    content = fpath.read_text(encoding="utf-8")
    for term in forbidden_terms:
        matches = re.findall(term, content, re.IGNORECASE)
        if matches:
            audit_passed = False
            print(f"❌ AUDIT FAILURE in {fpath.name}: Found hardcoded pattern '{term}' (Matches: {matches})")

record_test("TEST 23", "Code Audit for Hardcoded Patterns", audit_passed, "Zero document-specific patterns")

# -------------------------------------------------------------
# TEST 24: Multi-Chunk Support
# -------------------------------------------------------------
pdf_multi = BASE_DIR / "documents" / "Test_MultiChunk_Doc.pdf"
try:
    c_mc = canvas.Canvas(str(pdf_multi))
    c_mc.drawString(100, 750, "Project Omega Feature Spec Part 1")
    c_mc.drawString(100, 720, "Project Omega supports biometric authentication.")
    c_mc.showPage()
    c_mc.drawString(100, 750, "Project Omega Feature Spec Part 2")
    c_mc.drawString(100, 720, "Project Omega supports hardware key encryption.")
    c_mc.save()

    ingest_pdf(str(pdf_multi), "Test_MultiChunk_Doc.pdf")

    res24 = ask_question("What security features does Project Omega support?", [])
    t24_pass = (
        ("biometric" in res24["answer"].lower() or "hardware" in res24["answer"].lower() or "encryption" in res24["answer"].lower())
        and any(s["source"] == "Test_MultiChunk_Doc.pdf" for s in res24["sources"])
    )
    record_test("TEST 24", "Multi-Chunk Evidence Support", t24_pass, f"Answer: {res24['answer']}, Sources: {res24['sources']}")
finally:
    try:
        collection.delete(where={"source": "Test_MultiChunk_Doc.pdf"})
    except Exception:
        pass
    if pdf_multi.exists(): pdf_multi.unlink()

# -------------------------------------------------------------
# TEST 25: Unrelated Keyword Distractor
# -------------------------------------------------------------
pdf_distractor = BASE_DIR / "documents" / "Test_Distractor_Doc.pdf"
try:
    c_d = canvas.Canvas(str(pdf_distractor))
    c_d.drawString(100, 750, "System Administration Log")
    c_d.drawString(100, 720, "The server administrator configured Java version 17 on the build machine.")
    c_d.save()

    ingest_pdf(str(pdf_distractor), "Test_Distractor_Doc.pdf")

    res25 = ask_question("What is inheritance in Java?", [])
    t25_pass = (
        any("java-oop-notes.pdf" in s["source"].lower() for s in res25["sources"])
        and not any("test_distractor_doc.pdf" in s["source"].lower() for s in res25["sources"])
    )
    record_test("TEST 25", "Unrelated Keyword Distractor Filter", t25_pass, f"Sources: {res25['sources']}")
finally:
    try:
        collection.delete(where={"source": "Test_Distractor_Doc.pdf"})
    except Exception:
        pass
    if pdf_distractor.exists(): pdf_distractor.unlink()

# -------------------------------------------------------------
# TEST 26: Resolvable Reference
# -------------------------------------------------------------
h26 = [
    {"role": "user", "content": "What is Project Alpha?"},
    {"role": "assistant", "content": "Project Alpha is a search engine."}
]
res26 = ask_question("What language does it use?", h26, return_details=True)
t26_pass = "alpha" in res26.get("search_query", "").lower()
record_test("TEST 26", "Resolvable Reference (Project Alpha)", t26_pass, f"Resolved Query: {res26.get('search_query')}")

# -------------------------------------------------------------
# TEST 27: Recency Reference
# -------------------------------------------------------------
h27 = [
    {"role": "user", "content": "What is Project Alpha?"},
    {"role": "assistant", "content": "Project Alpha is a search engine."},
    {"role": "user", "content": "What is Project Beta?"},
    {"role": "assistant", "content": "Project Beta is a web app."}
]
res27 = ask_question("What language does it use?", h27, return_details=True)
t27_pass = "beta" in res27.get("search_query", "").lower() and "alpha" not in res27.get("search_query", "").lower()
record_test("TEST 27", "Recency Reference Resolution (Project Beta)", t27_pass, f"Resolved Query: {res27.get('search_query')}")

# -------------------------------------------------------------
# TEST 28: Unresolvable Reference
# -------------------------------------------------------------
res28 = ask_question("What language does it use?", [])
t28_pass = (
    res28["answer"] == FALLBACK_RESPONSE
    and res28["sources"] == []
)
record_test("TEST 28", "Unresolvable Reference Fallback", t28_pass, f"Answer: {res28['answer']}, Sources: {res28['sources']}")

# -------------------------------------------------------------
# FINAL REPORT SUMMARY
# -------------------------------------------------------------
print_banner("FINAL SUMMARY")
total_tests = len(test_results)
passed_tests = sum(1 for v in test_results.values() if v["status"] == "PASS")
failed_tests = total_tests - passed_tests

print(f"Total Tests Run: {total_tests}")
print(f"Passed:           {passed_tests}")
print(f"Failed:           {failed_tests}")

if failed_tests == 0:
    print("\n" + "*" * 75)
    print("  CORE RAG IS NOW DOCUMENT-AGNOSTIC AND READY TO FREEZE.")
    print("*" * 75 + "\n")
else:
    print("\nFAILURES DETECTED:")
    for test_id, name, details in failures:
        print(f" - [{test_id}] {name}: {details}")
