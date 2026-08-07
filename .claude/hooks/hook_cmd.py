#!/usr/bin/env python3
"""hook_cmd.py — hook が Bash コマンドを「検知」するときの共通の下ごしらえ（2026-08-07 新設）。

なぜ在るか（next_step §6.5 の21番）
  hook は Bash のコマンド文字列の中にスクリプト名が在るかどうかで「何を走らせたか」を判定する。
  ところが、走らせていないのに名前が出てくる場面がある。
    ・git commit のメッセージをヒアドキュメント（<<EOF … EOF）で書いたとき、その本文
    ・echo や printf の引用符の中
  2026-08-07 に、commit メッセージの本文に入っていた score.py の文字列を
  track_fastmode_data_read.sh が「分析を回した」と誤検知し、ターンが止まった（この日 2回）。
  2026-07-20 にも同じ型が起きていて、そのときは「session_worklog を含むコマンドは除外」という
  その場しのぎで塞いだ（同ファイル15行）。原因は同じなので、ここで1本にまとめる。

★実装を1本にする理由
  同じ下ごしらえを hook ごとに書き分けると、片方だけ直って片方が古いまま残る。
  2026-08-07 に engine_tuner_gen の件数の門で同じことが起きた（第1段と第2段に別々に書かれていた）。

★何を失うか（正直に）
  1. ヒアドキュメントの中で shell を書き、その中で python を実行する形は検知できなくなる
     （例＝bash <<'SH' … python3 e38_x.py … SH）。このプロジェクトでは使っていない形。
     python3 - <<'PY' … PY（本体を標準入力で渡す形）は、中身が python のコードなので
     「python3 何とか.py」の形にならない＝除去しても検知に影響しない。
  2. スクリプト名を引用符で囲んで実行する形（python3 'score.py'）は検知できなくなる。
     これは 2026-06-29 の引用符除去のときからの既知の限界で、今回 変えていない。
"""
from __future__ import annotations

import re
import sys

# ヒアドキュメント1個ぶん＝開始（<<TAG / <<'TAG' / <<-TAG）から、同じ TAG だけの行まで。
# 非貪欲（.*?）なので、最初に現れる閉じの行で止まる＝複数個あっても1個ずつ消える。
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1[^\n]*\n.*?\n[ \t]*\2[ \t]*(?=\n|$)",
    re.S,
)

# 引用符の中身（2026-06-29 から在る処理・ここへ集約しただけで中身は同じ）
_DQ = re.compile(r'"[^"]*"')
_SQ = re.compile(r"'[^']*'")


def normalize_cmd(cmd: str) -> str:
    """検知に使う形へ整える＝ヒアドキュメントの中身と引用符の中身を空白に置き換える。"""
    return _DQ.sub(" ", _SQ.sub(" ", HEREDOC.sub(" ", cmd or "")))


def runs_python(cmd_x: str, names: str) -> bool:
    """python で実際に走らせたかを見る（名前がコマンドの中に在るだけでは true にしない）。

    names＝正規表現の断片（例 "score|report|analyze"）。pdca_mark.py と同じ書き方にそろえてある。
    """
    return bool(re.search(r"python[0-9.]*[ \t]+[^|&;\n]*(" + names + r")", cmd_x))


# ══ 番人（既知答え・わざと壊すメタ確認つき）═══════════════════════════════════════════
_CASES = [
    # (説明, コマンド, 審判/分析を走らせたと判定してよいか)
    ("git commit のメッセージ（ヒアドキュメント）の本文に score.py の語が在るだけ",
     "git commit -F- <<'EOF'\nfeat: score.py に決済の名前を登録した\nEOF", False),
    ("ヒアドキュメントの本文に report.py と analyze.py の語が在るだけ",
     "cat >> memo.md <<'MSG'\nreport.py と analyze.py を回す予定\nMSG", False),
    ("引用符の中に score.py の語が在るだけ（2026-06-29 からの既存の動き）",
     "echo 'score.py は審判です'", False),
    # ★この1件がヒアドキュメントの除去の決め手（2026-08-07 に番人が鳴らず、弱さが分かって足した）。
    #   このプロジェクトの記録（worklog・defects・commit メッセージ）は、再現のコマンドを逐語で貼る。
    #   だから「python3 ….py …」の形が本文にそのまま入る。引用符の除去だけでは、これを止められない。
    ("ヒアドキュメントの本文に、再現のコマンドが逐語で貼ってある（記録の書き方そのもの）",
     "git commit -F- <<'EOF'\nfix: 誤検知を塞いだ\n再現＝python3 score.py trades_x_score.csv\nEOF", False),
    ("worklog に走行の逐語を貼る（cat >> の形・2026-07-20 の事案と同じ型）",
     "cat >> .claude/state/note.md <<'MSG'\n実行した: python3 analyze.py trades_x_score.csv --vs y.csv\nMSG", False),
    ("★本物の審判の実行（過剰に消していないこと）",
     "python3 score.py trades_x_score.csv", True),
    ("★本物の分析の実行（前後比較つき）",
     "python3 report.py trades_x_score.csv --vs trades_y_score.csv", True),
    ("★ヒアドキュメントの後ろに続く本物の実行（閉じたあとを消していないこと）",
     "cat <<'EOF' > /tmp/note.txt\nscore.py\nEOF\npython3 analyze.py trades_x_score.csv", True),
    ("python の本体を標準入力で渡す形（中身は python のコード＝実行の形ではない）",
     "python3 - <<'PY'\nimport score\nprint(score.__name__)\nPY", False),
]
_NAMES = r"score[A-Za-z0-9_]*\.py|report\.py|analyze\.py|[A-Za-z0-9_]+_probe\.py|[A-Za-z0-9_]+_deep_analysis\.py"


def _selftest() -> int:
    ng = []
    for label, cmd, want in _CASES:
        got = runs_python(normalize_cmd(cmd), _NAMES)
        mark = "✅" if got == want else "❌"
        print(f"  {mark} {label} → 判定 {got}（期待 {want}）")
        if got != want:
            ng.append(label)
    print()
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass（既知答え9件）")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        print("hook_cmd 自己検査（ヒアドキュメントと引用符の中身を検知に使わない）")
        raise SystemExit(_selftest())
    # 標準入力のコマンド文字列を整えて返す（.sh から使う）
    sys.stdout.write(normalize_cmd(sys.stdin.read()))
