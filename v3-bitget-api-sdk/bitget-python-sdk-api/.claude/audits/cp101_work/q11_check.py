#!/usr/bin/env python3
"""CP101 の Q3・Q10 の4つ目・Q11 の1つ目と2つ目の確かめ（読むだけ・本物には1バイトも書かない）。"""
import hashlib, json, os, re, subprocess, sys

sys.dont_write_bytecode = True
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
PR = os.path.join(SDK, "scripts", "priority_rebuild")
REL = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json"


def show(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True).stdout.decode("utf-8")


print("==== Q3 当てた記録")
rec = json.load(open(os.path.join(SDK, ".claude/audits/applied_fixes.json"), encoding="utf-8"))
rows = [r for r in rec["applied"] if r.get("report") == "design:m2c15-laws-rows-20261103"]
print("行の数", len(rows), "how の内訳", {h: sum(1 for r in rows if r.get("how") == h) for h in {r.get("how") for r in rows}})
print("時刻の種類", sorted({r.get("at") for r in rows}))
print("番号", [r.get("num") for r in rows])
cp100 = [r for r in rec["applied"] if "cp100" in str(r.get("report"))]
print("CP100 の記録の番号", sorted((r.get("num") for r in cp100), key=lambda x: int(x)), "how", {r.get("how") for r in cp100})

print("==== Q10 の4つ目 記録の数と列を作る組")
new = json.load(open(os.path.join(PR, "indicators/indicators.json"), encoding="utf-8"))
old = json.loads(show("bf699d9f", REL))
for k in ("指標の記録", "使い方の記録", "部品の記録"):
    print(k, "前", len(old[k]), "後", len(new[k]))
print("指標の記録が同じ", old["指標の記録"] == new["指標の記録"], "部品の記録が同じ", old["部品の記録"] == new["部品の記録"],
      "使い方の先頭16行が同じ", old["使い方の記録"] == new["使い方の記録"][:16])
print("足した4行")
for r in new["使い方の記録"][16:]:
    print("  ", json.dumps(r, ensure_ascii=False)[:600])
other = {k: (old.get(k) == new.get(k)) for k in set(old) | set(new)}
print("一番外の鍵ごとに同じか", other)

print("==== Q11 の1つ目 G2・H2 の対象のハッシュ値")
for name in ("g2_pass.json", "h2_pass.json"):
    p = os.path.join(ROOT, ".claude/state", name)
    d = json.load(open(p, encoding="utf-8"))
    files = d["files"]
    print(name, "when", d.get("when"), "fingerprint", str(d.get("fingerprint"))[:16], "本数", len(files), "型", type(files).__name__, "missing", d.get("missing"))
    items = files.items() if isinstance(files, dict) else [(f, None) for f in files]
    bad = []
    for f, h in items:
        for base in (ROOT, SDK, PR):
            q = os.path.join(base, f)
            if os.path.exists(q):
                break
        if not os.path.exists(q):
            bad.append(("無い", f))
            continue
        now = hashlib.sha256(open(q, "rb").read()).hexdigest()
        if h is not None and not str(now).startswith(str(h)[:12]):
            bad.append(("違う", f))
    print("  合わない", bad)
    # ★files は名前の一覧なので、上の照らしは在る・無しだけ。enforce_g2_pass.fingerprint・leak_causality_diag.h2_fingerprint と同じ式で指紋を作って比べる
    fp = hashlib.sha256()
    for rel in sorted(files):
        q = os.path.join(ROOT, rel)
        fp.update(rel.encode())
        if os.path.exists(q):
            fp.update(hashlib.sha256(open(q, "rb").read()).digest())
        else:
            fp.update(b"<missing>")
    print("  指紋を作り直した結果", fp.hexdigest()[:16], "記録", str(d.get("fingerprint"))[:16], "同じ=", fp.hexdigest() == d.get("fingerprint"))
    names = " ".join(str(f) for f, _h in items)
    print("  laws.json が対象に在る", "laws.json" in names, "／laws.py", "laws.py" in names, "／indicators.json", "indicators.json" in names)

print("==== Q11 の2つ目 法則の中の数の出どころ")
laws = json.load(open(os.path.join(PR, "laws/laws.json"), encoding="utf-8"))
cache = {}


def lines_of(rel):
    if rel in cache:
        return cache[rel]
    for base in (PR, os.path.join(SDK, ".claude/ratchet")):
        q = os.path.join(base, rel)
        if os.path.exists(q):
            cache[rel] = open(q, encoding="utf-8").read().split("\n")
            return cache[rel]
    cache[rel] = None
    return None


for row in laws["法則の中の数"]:
    src = row.get("出どころ", "")
    m = re.match(r"^(\S+?):(\d+)$", src)
    val = row.get("代表の値")
    rng = row.get("範囲")
    if not m:
        print(f"文 {row.get('名前')} | {src} | 範囲={rng} 代表={val}")
        continue
    ls = lines_of(m.group(1))
    n = int(m.group(2))
    text = ls[n - 1].strip() if ls and n <= len(ls) else None
    v = val.get("スキャル") if isinstance(val, dict) else val
    hit = None
    if text is not None and v is not None:
        hit = bool(re.search(r"(?<![\d.])" + re.escape(str(v)) + r"(?![\d])", text)) or (
            isinstance(v, float) and v == int(v) and bool(re.search(r"(?<![\d.])" + str(int(v)) + r"(?![\d.])", text)))
    print(f"{'値が在る' if hit else '値が無い'} {row.get('名前')} | {src} | 代表={v} | 行={str(text)[:240]}")
