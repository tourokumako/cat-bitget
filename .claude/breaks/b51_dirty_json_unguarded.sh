#!/bin/bash
# EXPECT_RC: 1
# MEANS: ★この1本だけ向きが裏返っている＝土台ゲートが通した（守りが消えた）。ほかの11本の「検査が落ちた」とは意味が反対
# b51 — 汚れの記録を守る1行を消すと、その形のファイルへの Write が素通りするか
#
#   守っているもの＝監査 cp28 の C-1（Critical）。設計書 iter="approval-audit-plumbing-20260907"
#     の完成の条件 #12。やること N。
#   何を守るか＝承認のときに「汚れていた .py」を凍結する記録（<設計書の名前>.dirty.json）は、
#     承認の道具だけが書く。CC が書けると、照合A(双方向) が読む「数えない一覧」に
#     任意の .py を足せる＝設計書に書いていない .py を触っても照合が落ちない。
#     兄弟2本（.breaks.json・.frozen.json）は 2026-09-04（監査 cp17 の G-1）で守りに入ったが、
#     3本目のこの記録は 2026-09-07 に作ったとき、足し忘れていた。
#   壊し方＝Write 側の場合分け（case）から `*.dirty.json|` を消す。
#   測るもの＝土台ゲート自身に「その形のファイルへ Write する」入力を渡して呼ぶ。
#
# ★判定が裏返っていることの説明（ほかの壊すプログラムと違う所）
#   ほかの11本は「守りを消すと、検査が落ちる（終了コードが 0 以外になる）」を測る。
#   この1本の相手は『止める』守りなので、消すと逆に **通ってしまう**（終了コードが 0 になる）。
#   だから、この中で裏返す＝**hook が通したら 1 を返す（守りが消えた＝壊し方が効いた）／
#   hook が止めたら 0 を返す（壊し方が効いていない＝この番人の前提が変わった）**。
#   承認の道具は「終了コードが 0 以外」を「壊すと落ちる」の証拠にするので、この向きで合う。
#
# ★なぜ hook を直に呼ぶか＝壊すプログラムは PreToolUse の外で走るので、
#   ファイルを書いても hook は掛からない。だから hook そのものに入力を渡して測る（b45 と同じ）。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-08）＝1秒未満。
#
# 限界（正直に書く）
#   ①壊すのは Write 側の1行だけ（Bash 側の一覧 BASE_SUFFIX を消す壊し方は、この1本では測れない）
#   ②hook が返す文言は見ない（終了コードだけを見る）
#   ③記録を手で偽造する道は、これでは止められない（承認の道具が上書きするまで残る）
#   ④このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
guard "$H"

# 壊す＝Write 側の場合分けから *.dirty.json を消す
python3 - "$H" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace('*.breaks.json|*.frozen.json|*.dirty.json|\\\n',
              '*.breaks.json|*.frozen.json|\\\n', 1)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b51 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝hook に「汚れの記録の形のファイルへ Write する」入力を渡す
printf '%s' "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$BK_TMP/zz_probe.dirty.json\",\"content\":\"x\"}}" \
    | bash "$H" >/dev/null 2>&1
_RC=$?

# ★裏返す（上の説明のとおり）
if [ "$_RC" = "0" ]; then
    MEASURED=1   # 通った＝守りが消えた＝壊し方が効いた
else
    MEASURED=0   # 止まった＝壊し方が効いていない（前提が変わった）
fi
finish
