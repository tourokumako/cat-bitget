"""監査 cp30｜文書を整える道具の番人（15件）を、監査のセッションから走らせる。

★なぜ別のファイルから呼ぶか＝Bash から `python3 .claude/tools/tidy_next_step.py --selftest` と
  打つと、土台ゲート（`.claude/tools/*.py` を Bash で触らせない hook）が止める。
  読み込んで関数を呼ぶ形なら、ファイルには一切 触らない。
"""
import pathlib
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
sys.path.insert(0, str(ROOT / ".claude" / "tools"))
import tidy_next_step as t  # noqa: E402

rc = t.selftest()
print(f"[監査 cp30] tidy_next_step.selftest() の終了コード＝{rc}（0＝全部 pass）")
sys.exit(rc)
