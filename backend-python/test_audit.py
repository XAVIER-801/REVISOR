"""Test script to run audit and debug results."""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from services.word_engine import WordAuditEngine

# Use a test file
test_file = '/app/test.docx'

print(f"Testing with: {test_file}")
print(f"File size: {os.path.getsize(test_file)} bytes")

try:
    engine = WordAuditEngine(test_file)
    result = engine.run_audit()
    stats = result['stats']
    results = result['results']
    print(f"\nStats: {json.dumps(stats, indent=2)}")
    print(f"Total results: {len(results)}")
    for r in results:
        print(f"  [{r['status']}] {r['category']}: {r['rule'][:60]}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
