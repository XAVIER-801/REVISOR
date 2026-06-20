"""Quick stats from audit test."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from services.word_engine import WordAuditEngine
from collections import Counter

engine = WordAuditEngine('/app/test.docx')
result = engine.run_audit()

cat_counts = Counter(r['category'] for r in result['results'])
print("Category counts:")
for cat, count in cat_counts.most_common():
    print(f"  {cat}: {count}")

status_counts = Counter(r['status'] for r in result['results'])
print(f"\nStatus counts:")
for s, c in status_counts.most_common():
    print(f"  {s}: {c}")

print(f"\nTotal: {len(result['results'])}")
