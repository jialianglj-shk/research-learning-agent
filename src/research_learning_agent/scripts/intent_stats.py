import json
from collections import Counter
from pathlib import Path


p = Path("data/intent_events.jsonl")
c = Counter()
n = 0
low = 0


for line in p.read_text(encoding="utf-8").splitlines():
    e = json.loads(line)
    c[e["intent"]] += 1
    n += 1
    if e["confidence"] < 0.65:
        low += 1
    

print("Total:", n)
print("Intent distribution:", c)
print("Low confidence rate:", low / max(n, 1))