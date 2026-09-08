"""監査 cp30｜壊すプログラム5本が「いまも壊せる形か」を、走らせずに確かめる。

★なぜ走らせないか＝Bash から `bash .claude/breaks/b53...sh` と打つと、土台ゲート
  （`.claude/breaks/*.sh` を Bash で触らせない hook・監査 cp16 の E-1）が止める。
  監査のセッションが強制を自分の判断で迂回するのは、恒久の決まり57番に反する。
  ＝走らせる代わりに、「壊す対象の行が、いまのファイルに実在するか」を読むだけで確かめる。
    5本とも、対象の行が見つからなければ `raise SystemExit("壊す対象の行が見つからない")` で
    落ちる作りなので、行が実在することは「いまも壊せる」ことの必要条件になる。

★これは走らせた確認の代わりにはならない（限界は監査レポートに書く）。
"""
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
BREAKS = ROOT / ".claude" / "breaks"
TARGETS = {
    "b53_insp5_frame_and_key_gone.sh": ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py",
    "b54_table_tidy_gone.sh": ROOT / ".claude/tools/tidy_next_step.py",
    "b55_cyc_key_time_gone.sh": ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py",
    "b56_one_min_csv_old.sh": ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py",
    "b57_h2_fingerprint_stale.sh": None,   # 壊し方＝末尾にコメントを足す（対象の行を探さない）
}

print("=" * 100)
print("監査 cp30｜壊すプログラム5本の『壊す対象の行』が、いまのファイルに実在するか")
print("=" * 100)
ng = 0
for name, target in TARGETS.items():
    p = BREAKS / name
    src = p.read_text(encoding="utf-8")
    rc = re.search(r"^# EXPECT_RC:\s*(\d+)", src, re.M)
    means = re.search(r"^# MEANS:\s*(.+)$", src, re.M)
    print(f"\n■ {name}")
    print(f"   宣言: EXPECT_RC={rc.group(1) if rc else '★無し'} ／ MEANS={means.group(1) if means else '★無し'}")
    if target is None:
        print("   壊す対象の行＝無し（末尾にコメントを足す形）／前提＝走らせる前に印が一致していること")
        continue
    body = target.read_text(encoding="utf-8")
    # 壊すプログラムの中の `new = (...)` / `frame_new = (...)` / `key_new = (...)` の文字列を取り出す
    found = 0
    for m in re.finditer(r"^(?:\w+_)?new = \(?\s*\n?((?:\s*'(?:[^'\\]|\\.)*'\s*\n?)+)\)?\s*$", src, re.M):
        lit = "".join(eval(x.strip()) for x in m.group(1).strip().splitlines())  # noqa: S307
        ok = lit in body
        found += 1
        head = lit.strip().splitlines()[0][:80]
        print(f"   対象{found}: {'✅ 実在' if ok else '❌ 見つからない'} … {head}")
        if not ok:
            ng += 1
    if not found:
        print("   ★壊す対象の行を、この監査のプログラムでは取り出せなかった（形が違う）")

print("\n" + "=" * 100)
print(f"まとめ: 見つからない対象 {ng} 件"
      "（0 なら、5本とも『前提が変わった』で落ちることはない＝いまも壊せる形）")
print("★限界＝実際に走らせてはいない（土台ゲートが Bash からの実行を止めるため）。")
print("=" * 100)
sys.exit(1 if ng else 0)
