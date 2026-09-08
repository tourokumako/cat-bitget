#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b57 — 印の対象のコードを1行 変えると、指紋を照らす口が「違う」と言うか
#
#   守っているもの＝設計書 iter="insp5-frame-and-table-tidy-20260908" の完成の条件 #5
#     （H2 の印を取り直したことを、機械で確かめる）。
#   何を守るか＝enforce_h2_pass.py の --check-fingerprint が、印（h2_pass.json）と
#     いまのコードの指紋を実際に数え直して照らすこと。
#   ★なぜ要ったか（Web Claude の2回目の重い2）＝直す前は、この行を tidy_next_step.py の
#     検査 (c) で測っていた。ところが (c) が照らすのは「next_step.md に書いてある文字」と
#     「json の中の文字」だけで、いまのコードの指紋は1行も見ていない
#     ＝コードを書き替えて印を放置しても通ってしまった。
#   壊し方＝印の対象である observe_diag.py の末尾に、コメントを1行 足す（中身は何も変えない）。
#   測るもの＝`enforce_h2_pass.py --check-fingerprint`。
#   期待＝壊すと「印と、いまのコードが違う」で 1 になる。
#
# ★前提＝走らせる前に、印が いまのコードと一致していること（やること I で取り直す）。
#   一致していなければ、壊さなくても 1 が返るので、この壊すプログラムは何も測っていない。
#   下でそれを先に確かめ、一致していなければ 97 で落とす（黙って「守れた」と言わない）。
#
# ★時間について＝承認のときの打ち切りは 120秒。実測（2026-09-08）＝1秒 未満。
#
# 限界（正直に書く）
#   ①印そのものを手で偽造されたら見抜けない（見張り本体と同じ限界）
#   ②このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

HOOK="$ROOT/.claude/hooks/enforce_h2_pass.py"
OBS="$PR/observe_diag.py"

python3 "$HOOK" --check-fingerprint >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 壊す前から印が合っていない＝この壊すプログラムは何も測れない（先に印を取り直す）" >&2
    exit 97
fi

guard "$OBS"
printf '\n# b57 が足したコメント（壊すプログラムが必ず消します）\n' >> "$OBS"

measure python3 "$HOOK" --check-fingerprint
finish
