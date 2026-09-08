"""監査 cp32｜G2 の印が、いまのコードと合っているかを読むだけで確かめる。

★G2 には H2 のような「印を照らす口」（`--check-fingerprint`）が無いので、
  `enforce_g2_pass.py` の中の `fingerprint` をそのまま呼んで照らす（読むだけ・何も書かない）。
★印を取り直す（`gen_signal_families.py --verify`）ことはしない＝監査は本物の記録を書き替えない。
"""
import importlib.util
import json
import pathlib

REPO = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
HOOK = REPO / ".claude/hooks/enforce_g2_pass.py"

spec = importlib.util.spec_from_file_location("_g2_readonly", HOOK)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

rec = json.loads((REPO / ".claude/state/g2_pass.json").read_text(encoding="utf-8"))
files, fp = rec["files"], rec["fingerprint"]
now = mod.fingerprint(files)
lack = [m for m in mod.MUST if m not in files]

print(f"印の値   = {fp[:16]}…（対象 {len(files)} 件・{rec['when']}）")
print(f"いまの値 = {now[:16]}…")
print(("✅ 一致" if now == fp else "❌ 食い違い") + f" ／ 必須ファイルの欠け {len(lack)} 件"
      + ("" if not lack else f"＝{lack}"))
