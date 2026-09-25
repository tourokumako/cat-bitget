#!/bin/bash
# run.sh — 写しの中のプログラムを走らせる入口（監査 cp42 の作業場・本物は触らない）
#   bash run.sh aaf <args>        → 写しの apply_audit_fix（例: --selftest ／ --design <設計書> --dry）
#   bash run.sh acc <args>        → 写しの gen_acceptance（例: --selftest ／ --verify ／ --dry-run）
#   bash run.sh gad <args>        → 写しの gen_audit_docs
#   bash run.sh tool <名前> <args> → 写しの .claude/tools/<名前>.py（.py は付けない）
#   bash run.sh break <bNN_name>   → 写しの壊すプログラム（.sh は付けても付けなくてもよい）
#   ── 写しのファイルを直接 壊す・戻す ──
#   鍵＝aaf / gen_acc / gad / acc / approved / src / b101 / b102 / lib
#   bash run.sh path <鍵> ／ hash <鍵> ／ restore <鍵> ／ restore-all
#   bash run.sh patch <鍵> <前の文字> <後の文字>   → 1か所だけ置き換える（1か所に定まらなければ止まる）
#   bash run.sh pyedit <鍵> <python の文>          → p（パス）・s（中身）・json・re を渡して走らせる
#   ★作業場所は写しの根（mirror）。hook の都合で、コマンドの文字列に本物の道具のパスを書かない形にしてある
set -u
W="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work"
M="$W/mirror"
T="$M/.claude/tools"
cmd="${1:-}"; shift || true
case "$cmd" in
  aaf)   cd "$M" && exec python3 "$T/apply_audit_fix.py" "$@";;
  acc)   cd "$M" && exec python3 "$T/gen_acceptance.py" "$@";;
  gad)   cd "$M" && exec python3 "$T/gen_audit_docs.py" "$@";;
  tool)  n="${1%.py}"; shift; cd "$M" && exec python3 "$T/$n.py" "$@";;
  break) b="${1%.sh}"; shift; cd "$M" && exec bash "$M/.claude/breaks/$b.sh" "$@";;
  path|hash|restore|restore-all|patch|pyedit)
        exec python3 "$W/mirror_edit.py" "$cmd" "$@";;
  *) echo "usage: run.sh aaf|acc|gad|tool|break|path|hash|restore|restore-all|patch|pyedit ..." >&2; exit 2;;
esac
