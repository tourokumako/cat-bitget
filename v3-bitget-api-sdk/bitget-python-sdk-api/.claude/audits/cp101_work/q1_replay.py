#!/usr/bin/env python3
"""CP101 の Q1・Q2・Q3・Q9 の確かめ（監査の作業場だけに書く。本物には1バイトも書かない）。

設計書（承認の控え）の 4-20 を、実装の前の版（bf699d9f）の写しへ番号の順に当て、実装の後の版（8ed860d0）と比べる。
"""
import difflib, hashlib, json, os, subprocess, sys

sys.dont_write_bytecode = True
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, ".claude", "tools"))
import apply_audit_fix as a  # noqa: E402

BEFORE, AFTER = "bf699d9f", "8ed860d0"
SDK = "v3-bitget-api-sdk/bitget-python-sdk-api"


def show(rev, path):
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


design = os.path.join(ROOT, SDK, ".claude/ratchet/acceptance_archive/m2c15-laws-rows-20261103.md")
fixes = a.read_design_fixes(open(design, encoding="utf-8").read())
print("実装の指示の件数:", len(fixes))
targets = []
for f in fixes:
    if f["対象のファイル"] not in targets:
        targets.append(f["対象のファイル"])
cur = {p: (show(BEFORE, p) or "") for p in targets}
existed = {p: show(BEFORE, p) is not None for p in targets}
for f in fixes:
    p = f["対象のファイル"]
    before = f["直す前の文字"]
    kinds = [k for _a, k, _b in f["4つ目"]]
    if before.strip() == "なし" and not existed[p]:
        body = f["4つ目"][0][2]
        n = "新"
        cur[p] = body
        how = "新しいファイル"
    else:
        n = cur[p].count(before)
        cur[p], how = a.apply_one(f, cur[p])
    head = show(AFTER, p) or ""
    work = open(os.path.join(ROOT, p), encoding="utf-8").read()
    body = f["4つ目"][0][2]
    print(f"実装 {f['番号']:>2} {kinds} 当たり={n} {how} 後の版に在る={body in head} いまの実物に在る={body in work} 状態={f.get('状態')} {p}")

out = os.path.join(WORK, "q1_applied")
print("---- 当てた結果と実装の後の版の比べ")
for p in targets:
    head = show(AFTER, p)
    os.makedirs(os.path.dirname(os.path.join(out, p)), exist_ok=True)
    with open(os.path.join(out, p), "w", encoding="utf-8") as fh:
        fh.write(cur[p])
    same = head == cur[p]
    work = open(os.path.join(ROOT, p), encoding="utf-8").read()
    print(f"{'同じ' if same else '違う'} 作業ツリーと後の版={'同じ' if work == head else '違う'} sha={hashlib.sha256(cur[p].encode()).hexdigest()[:12]} {p}")
    if not same:
        d = list(difflib.unified_diff(cur[p].splitlines(), (head or "").splitlines(), "当てた結果", "実装の後", lineterm="", n=0))
        print(f"  差の行数={len(d)}")
        for ln in d[:80]:
            print("  " + ln[:260])

print("---- req_trace_src.json を、22行の「済＝208番」を先に入れた版で当て直す")
RT = ".claude/state/req_trace_src.json"
base = show(BEFORE, RT).split("\n")
head_lines = show(AFTER, RT).split("\n")
print("  前の行数", len(base), "後の行数", len(head_lines))
pre = list(base)
changed = 0
for i, ln in enumerate(pre):
    # 割り当ての行の "工事" の中の "208" を「済＝208番」にする（経緯の4つ目の文の変更）
    if '"工事"' in ln and '"208"' in ln:
        pre[i] = ln.replace('"208"', '"済＝208番"')
        changed += 1
print("  \"208\" を直した行の数:", changed)
txt = "\n".join(pre)
for f in fixes:
    if f["対象のファイル"] != RT:
        continue
    n = txt.count(f["直す前の文字"])
    txt, how = a.apply_one(f, txt)
    print(f"  実装 {f['番号']:>2} 当たり={n} {how}")
print("  22行を先に入れて当てた結果と後の版が同じ:", txt == show(AFTER, RT))
if txt != show(AFTER, RT):
    d = list(difflib.unified_diff(txt.splitlines(), show(AFTER, RT).splitlines(), "当てた結果", "実装の後", lineterm="", n=0))
    for ln in d[:60]:
        print("   " + ln[:260])
print("  後の版に残る \"208\" の行:", [i + 1 for i, ln in enumerate(head_lines) if '"208"' in ln])

print("---- Q2 差分のあるファイルのうち、対象の外（直す相手の外で実装の前後で変わったファイル）")
names = subprocess.run(["git", "diff", "--name-only", "-z", BEFORE, AFTER], cwd=ROOT, capture_output=True, text=True).stdout.split("\0")
names = [n for n in names if n]
print("差分のファイルの本数:", len(names))
for n in names:
    if n not in targets and "/verbatim/" not in n and "acceptance_archive" not in n:
        print("  対象の外:", n)

print("---- Q3 当てた記録")
rec = json.load(open(os.path.join(ROOT, SDK, ".claude/audits/applied_fixes.json"), encoding="utf-8"))
key = "design:m2c15-laws-rows-20261103"


def find(obj):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find(v)
            if r is not None:
                return r
    return None


row = find(rec)
print("記録の型:", type(row).__name__, "件数:", len(row) if row is not None else None)
items = row if isinstance(row, list) else (row.get("fixes") or row.get("items") or row) if row else []
if isinstance(items, dict):
    items = [dict(v, 番号=k) if isinstance(v, dict) else {"番号": k, "値": v} for k, v in items.items()]
by = {str(i.get("番号", i.get("num"))): i for i in items}
for f in fixes:
    i = by.get(str(f["番号"]))
    ok = i is not None
    tgt = (i or {}).get("file") or (i or {}).get("対象のファイル")
    print(f"  実装 {f['番号']:>2} 記録に在る={ok} 相手が同じ={tgt == f['対象のファイル'] if tgt else '欄なし'} {json.dumps(i, ensure_ascii=False)[:160] if i else ''}")
extra = [k for k in by if k not in {str(f['番号']) for f in fixes}]
print("記録にだけ在る番号:", extra)
