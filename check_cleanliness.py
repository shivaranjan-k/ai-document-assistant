from pathlib import Path

target_file = Path("backend/rag_engine.py")
content = target_file.read_text(encoding="utf-8")
lines = content.splitlines()

forbidden = [
    "shivaranjan",
    "sara holidays",
    "rag-based ai document assistant",
    "rag project",
    "document assistant",
    "backend/main.py",
    "sessions = {}",
    "collection.query",
    "chapter ",
    "tutorial:",
    "beginner-to-advanced guide",
    "what is rag",
    "what is an llm",
    "what is an embedding",
    "what is a cross-encoder"
]

print("SEARCH RESULTS IN backend/rag_engine.py:")
print("=" * 60)
found_any = False
for pattern in forbidden:
    matches = []
    for idx, line in enumerate(lines, 1):
        if pattern in line.lower():
            matches.append((idx, line.strip()))
    if matches:
        found_any = True
        print(f"[FOUND] '{pattern}':")
        for line_num, l_content in matches:
            print(f"  Line {line_num}: {l_content}")
    else:
        print(f"[CLEAN] '{pattern}': None found")
print("=" * 60)
