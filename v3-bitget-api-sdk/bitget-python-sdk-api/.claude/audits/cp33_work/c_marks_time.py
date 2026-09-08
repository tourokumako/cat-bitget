#!/usr/bin/env python3
"""監査 cp33 — 印の「時刻」だけを書き替えたときに ❌ が出るか（依頼書 §3.5・別枠 E）。

★本物の next_step.md は1文字も書き替えない。読んだ文字列を記憶の中で書き替えて verify を呼ぶ。
"""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
spec = importlib.util.spec_from_file_location("tidy", ROOT / ".claude" / "tools" / "tidy_next_step.py")
tidy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tidy)

NEXT = ROOT / ".claude" / "state" / "next_step.md"
text = NEXT.read_text(encoding="utf-8")
h2 = tidy._pass(ROOT / ".claude" / "state" / "h2_pass.json")
g2 = tidy._pass(ROOT / ".claude" / "state" / "g2_pass.json")
wd = tidy.latest_worklog_date(ROOT / ".claude" / "state")

print("=" * 76)
print("印の時刻を照らす検査（監査 cp33・依頼書 §3.5）")
print("=" * 76)
print(f"\n印の json＝H2 {h2['fp']}… / {h2['when']} / 対象{h2['n']}件"
      f"  ／ G2 {g2['fp']}… / {g2['when']} / 対象{g2['n']}件")

cases = [
    ("① 素のまま（本物の next_step）", text),
    ("② H2 の時刻だけを1文字 変える", text.replace(h2["when"], h2["when"][:-1] + ("0" if h2["when"][-1] != "0" else "1"), 1)),
    ("③ G2 の時刻だけを1文字 変える", text.replace(g2["when"], g2["when"][:-1] + ("0" if g2["when"][-1] != "0" else "1"), 1)),
    ("④ H2 の指紋だけを1文字 変える", text.replace(h2["fp"], h2["fp"][:-1] + ("0" if h2["fp"][-1] != "0" else "1"), 1)),
]
for name, t in cases:
    changed = (t != text)
    ng = tidy.verify(t, h2, g2, wd)
    c = [x for x in ng if x.startswith("(c)")]
    print(f"\n■ {name}  本文が変わったか={changed}")
    print(f"   ❌ 全部 {len(ng)} 件 ／ そのうち (c) が {len(c)} 件")
    for x in ng:
        print("   " + x[:150])
