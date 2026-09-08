#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b49 — 他のプログラムが書く囲みを差し戻す処理を消すと、相手の検査が落ちるか
#
#   守っているもの＝next_step §6 の154番（設計書 iter="approval-audit-plumbing-20260907" の
#     完成の条件 #10）。
#   何を守るか＝regime_detection_kb.md の §11・§12 は gen_regime_kb.py が丸ごと書くが、
#     その中に gen_materials.py が書く囲みが2つ入っている。
#     直す前＝gen_regime_kb.py --write は毎回 その囲みを目印ごと消していた。
#     実測（2026-09-07・CC が実際に踏んだ）＝17行が古い数字に戻った
#     （部品 555件 → 551件・指標 257種 → 256種 ほか）。git で戻した。
#   壊し方＝keep_foreign を、何も差し戻さない形にする。
#   測るもの＝`gen_regime_kb.py --write` を走らせたあと `gen_materials.py --verify`。
#     壊れていれば「印が無い」で落ちる。
#   期待＝壊すと相手の検査が落ちて終了コードが 0 以外になる。
#
# ★このプログラムは、走らせると本物の文書を書き換える。だから触るファイルを3本とも
#   guard に入れる（lib.sh が控えを取り、終わったら必ず戻し、ハッシュ値で照らす）。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。
#   実測（2026-09-07）＝--write 約1秒＋相手の --verify 約5秒。
#
# 限界（正直に書く）
#   ①壊すのは差し戻しの1か所だけ（指紋から囲みを外す処理を消す壊し方は、この1本では測れない）
#   ②相手の検査のほかの枝は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/gen_regime_kb.py"
KB="$SDK/.claude/memory/regime_detection_kb.md"
M2="$SDK/.claude/ratchet/engine_tuner_milestones2.md"
guard "$T" "$KB" "$M2"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace('    out = new_body\n    for _head, _end in _FOREIGN:\n',
              '    return new_body\n    for _head, _end in _FOREIGN:\n', 1)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b49 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 壊した状態で正本を作り直す（囲みが消える）
python3 "$T" --write >/dev/null 2>&1

# 測る＝相手のプログラムの検査。囲みが消えていれば落ちる
measure python3 "$PR/gen_materials.py" --verify
finish
