"""Quick summary of CV analysis JSON files."""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
files = sorted(HERE.glob("cv_*.json"))
print(f"{'file':<12} score struct swiss crit adv conc actn tips  summary")
print("-" * 100)
for f in files:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"{f.name:<12} ERR: {e}")
        continue
    sc = d.get("overall_score", "?")
    st = (d.get("structure") or {}).get("score", "?")
    sw = (d.get("swiss_fit") or {}).get("score", "?")
    crit = len(d.get("critical_issues", []))
    adv = len((d.get("swiss_fit") or {}).get("advantages", []))
    conc = len((d.get("swiss_fit") or {}).get("concerns", []))
    actn = len((d.get("swiss_fit") or {}).get("actions", []))
    tips = len(d.get("tips", []))
    summary = (d.get("summary") or "")[:80].replace("\n", " ")
    print(f"{f.name:<12} {sc:>5} {st:>6} {sw:>5} {crit:>4} {adv:>3} {conc:>4} {actn:>4} {tips:>4}  {summary}")
