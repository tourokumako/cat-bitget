import json, pathlib
b = json.loads(pathlib.Path(".claude/ratchet/regime_laws.json").read_text(encoding="utf-8"))
print("トップの鍵:", list(b.keys()))
for l in b["法則"]:
    if l.get("番号") in ("R1", "R4", "R5", "R7"):
        print("---", l["番号"], "の鍵:", list(l.keys()))
        print(json.dumps(l, ensure_ascii=False)[:700])
