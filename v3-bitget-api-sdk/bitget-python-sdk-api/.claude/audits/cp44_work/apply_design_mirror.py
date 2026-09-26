#!/usr/bin/env python3
"""apply_design_mirror.py — 束2 の設計書の「実装の指示」を、作業場の写し（mirror）にだけ当てる（監査 CP44 の修正19）。

手本＝監査 CP39 の作業場の apply_design_all.py。
  ★読み取り・確かめ・当て方は、写しの当てる道具（mirror/.claude/tools/apply_audit_fix.py＝根のパスを写しに
    向けたもの）の関数をそのまま使う＝本物の当てる道具と同じ判定。
  ★壊すプログラム（守りの仕組み＝当てる道具は書かない）は、欄の「足す文字」を写しの .claude/breaks に新しいファイルとして書く。
  ★書き先は写しの下だけ（assert で止める）。承認の印は写しでも照らす（写しの印＝本物の印の写し）。
  ★限界＝写しの当てる道具は、根拠の抜き書きのファイルを置き場の中から探すとき audits の下を飛ばすので、
    写しの中では対象のファイル以外の根拠の行を照らせない（対象のファイルと同じ名前の根拠は照らす）。
"""
import hashlib, os, pathlib, sys

W = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp44_work")
M = W / "mirror"
sys.path.insert(0, str(M / ".claude" / "tools"))
import apply_audit_fix as aaf  # noqa: E402

assert aaf.ROOT == str(M), f"写しの当てる道具の根が写しでない: {aaf.ROOT}"
g = aaf.g
design = M / ".claude" / "state" / "acceptance.md"
text = design.read_text(encoding="utf-8")
ok, why = aaf.approved_ok(str(design), str(M / ".claude" / "state" / "acceptance.approved"))
print(f"設計書 sha256 {hashlib.sha256(design.read_bytes()).hexdigest()[:16]}… ／ 承認の印と同じか: {ok} {why}")
if not ok:
    raise SystemExit(1)
blocks = aaf.read_design_blocks(text)
errs = sum((g.item_errors(n, b) for n, b in blocks), [])
fixes = aaf.read_design_fixes(text)
bad = aaf.impl_src_mismatch(fixes, str(M / "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json"))
print(f"件数 {len(fixes)} ／ 欄の形の誤り {len(errs)} ／ 元データとの食い違い {len(bad)} {bad[:3]}")
if errs or bad:
    raise SystemExit(1)
targets = aaf.design_targets(text)
ready, stopped = [], []
for f in fixes:
    ok1, why1, _cur = aaf.check_one(f, {})
    if ok1 and os.path.realpath(aaf.repo_path(f["対象のファイル"] or "")) not in targets:
        ok1, why1 = False, "TARGET の外"
    (ready if ok1 else stopped).append((f, why1))
hard = [x for x in stopped if not x[1].startswith("守りの仕組みなので")]
print("当てる件:", [f["番号"] for f, _w in ready])
print("写しに新しいファイルとして書く件（壊すプログラム）:", [f["番号"] for f, w in stopped if w.startswith("守りの仕組みなので")])
if hard:
    for f, w in hard:
        print(f"   ❌ 実装 {f['番号']}: {w}")
    raise SystemExit(1)
mem = {}
for f, _w in ready:
    p = aaf.repo_path(f["対象のファイル"])
    mem.setdefault(p, open(p, encoding="utf-8").read())
    if not aaf._recheck(f, mem[p]):
        raise SystemExit(f"実装 {f['番号']}: 先の件を当てた後で、直す前の文字がちょうど1か所でない")
    new, what = aaf.apply_one(f, mem[p], "")
    if new == mem[p]:
        raise SystemExit(f"実装 {f['番号']}: 当てても中身が変わらない")
    mem[p] = new
    print(f"   ✅ 実装 {f['番号']}: {what} → {os.path.relpath(p, M)}")
for p, s in mem.items():
    assert p.startswith(str(M)), p
    open(p, "w", encoding="utf-8").write(s)
n_new = 0
for f, w in stopped:
    dst = M / f["対象のファイル"]
    assert str(dst).startswith(str(M)), dst
    body = [b for _a, k, b in f["4つ目"] if k == "足す文字"][0]
    dst.write_text(body.replace('ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"', f'ROOT="{M}"'), encoding="utf-8")
    os.chmod(dst, 0o755)
    n_new += 1
    print(f"   ✅ 実装 {f['番号']}: 写しに新しいファイルを書いた → {os.path.relpath(dst, M)}")
print(f"当てた {len(ready)} 件 ／ 新しいファイル {n_new} 本（書き先は全部 写しの下）")
