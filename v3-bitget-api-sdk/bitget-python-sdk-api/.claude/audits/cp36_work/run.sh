#!/bin/bash
# run.sh — 写しの中のプログラムを走らせる入口（監査 cp36 の作業場・本物は触らない）
#   bash run.sh gen  <args>      → 写しの engine_tuner_gen.py
#   bash run.sh exec <args>      → 写しの engine_tuner_exec.py
#   bash run.sh r9   <args>      → 写しの regime_r9_diag.py
#   bash run.sh count            → 写しの数える道具（count_builder_literals）
#   bash run.sh kb <args>        → 写しの gen_regime_kb（例: --write stage ／ --verify）
#   bash run.sh acc <args>       → 写しの gen_acceptance（例: --verify）
#   bash run.sh rb <args>        → 写しの run_breaks（例: --selftest）
#   bash run.sh old-gen / old-r9 / old-kb → mirror_old（0e1f1be の版）
#   bash run.sh break <bNN_name>  → 写しの壊すプログラム（.sh は付けても付けなくてもよい）
#   bash run.sh old-break <bNN_name> → mirror_old の壊すプログラム
#   ★hook の都合で、コマンドの文字列に .py を書かない形にしてある（写しの中のプログラムだけを走らせる）
set -u
W="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work"
M="$W/mirror"; O="$W/mirror_old"
SDK="v3-bitget-api-sdk/bitget-python-sdk-api"
PR="$M/$SDK/scripts/priority_rebuild"; OPR="$O/$SDK/scripts/priority_rebuild"
T="$M/.claude/tools"; OT="$O/.claude/tools"
cmd="${1:-}"; shift || true
case "$cmd" in
  gen)   exec python3 "$PR/engine_tuner_gen.py" "$@";;
  exec)  exec python3 "$PR/engine_tuner_exec.py" "$@";;
  r9)    exec python3 "$PR/regime_r9_diag.py" "$@";;
  count) exec python3 "$T/count_builder_literals.py" "$@";;
  kb)    exec python3 "$T/gen_regime_kb.py" "$@";;
  acc)   exec python3 "$T/gen_acceptance.py" "$@";;
  rb)    exec python3 "$T/run_breaks.py" "$@";;
  old-gen)  exec python3 "$OPR/engine_tuner_gen.py" "$@";;
  old-r9)   exec python3 "$OPR/regime_r9_diag.py" "$@";;
  old-kb)   exec python3 "$OT/gen_regime_kb.py" "$@";;
  break)     b="${1%.sh}"; shift; exec bash "$M/breaks/$b.sh" "$@";;
  old-break) b="${1%.sh}"; shift; exec bash "$O/breaks/$b.sh" "$@";;
  # ── 写しのファイルを直接 壊す・戻す（追加の壊し方を試すため）──
  #   鍵＝gen / exec / r9 / laws / cands / acc / mile / kb / rb / count / limits
  #   bash run.sh path <鍵>                 → 写しの中のそのファイルのパスを出す
  #   bash run.sh hash <鍵>                 → いまのハッシュ値と、組み立て直後（pristine）のハッシュ値
  #   bash run.sh restore <鍵>              → pristine から戻す（戻したあとハッシュ値を照らす）
  #   bash run.sh restore-all               → 全部の鍵を戻す
  #   bash run.sh patch <鍵> <前の文字> <後の文字>  → 文字を1か所だけ置き換える（1か所に定まらなければ止まる）
  #   bash run.sh pyedit <鍵> <python の文>  → p（パス）・s（中身）・json・re を渡して python の文を走らせる。
  #                                            s を書き替えて `open(p,'w').write(s)` するか、json を書き戻す
  path|hash|restore|restore-all|patch|pyedit)
        exec python3 "$W/mirror_edit.py" "$cmd" "$@";;
  *) echo "usage: run.sh gen|exec|r9|count|kb|acc|rb|old-gen|old-r9|old-kb|break|old-break|path|hash|restore|restore-all|patch|pyedit ..." >&2; exit 2;;
esac
