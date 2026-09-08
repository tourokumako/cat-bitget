"""監査 cp30｜H2 と G2 の印が、いまのコードと一致しているか（読むだけ）。

設計書 §7 の補9 が「G2 の印も古くなった＝取り直した」と書いている。
H2 には照らす口（--check-fingerprint）が新しく足されたが、G2 には無い。
そこで、G2 の見張りの中の指紋の計算をそのまま呼んで、印と照らす。
★何も書かない。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))

print("=" * 100)
print("監査 cp30｜H2 と G2 の印が、いまのコードと一致しているか")
print("=" * 100)

for name, mod_name, mark in (("H2", "enforce_h2_pass", "h2_pass.json"),
                             ("G2", "enforce_g2_pass", "g2_pass.json")):
    p = ROOT / ".claude" / "state" / mark
    rec = json.loads(p.read_text(encoding="utf-8"))
    mod = __import__(mod_name)
    now = mod.fingerprint(rec["files"])
    ok = now == rec["fingerprint"]
    print(f"\n■ {name}（{mark}）")
    print(f"   取り直した日時 : {rec['when']}")
    print(f"   対象のファイル : {len(rec['files'])} 件")
    print(f"   印にある指紋   : {rec['fingerprint'][:24]}…")
    print(f"   いまの指紋     : {now[:24]}…")
    print(f"   → {'✅ 一致' if ok else '❌ 食い違い（取り直しが要る）'}")

print("=" * 100)
