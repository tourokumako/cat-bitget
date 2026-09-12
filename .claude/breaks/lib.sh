#!/bin/bash
# _lib.sh — 壊すプログラムが全部 使う共通の部品（監査 cp16 の E-12・まこさん指名 2026-09-03）
#
# 壊すプログラムの決まり（4つ・設計書 §3.2）
#   1. 触るファイルを、走らせる前に控えへ写す
#   2. 壊して、測る対象のコマンドを走らせ、その終了コードを覚える
#   3. 必ず控えから戻す（trap で、途中で落ちても戻す）
#   4. 戻したあとハッシュ値を照らし、元と1文字でも違えば exit 99 で大きく落ちる
#
# 使い方（各プログラムの先頭で読み込む）
#   source "$(dirname "$0")/_lib.sh"
#   guard <触るファイル> [<触るファイル> ...]     # 1と3と4を一度に仕掛ける
#   ... 壊す ...
#   measure <測るコマンド...>                      # 2（終了コードを $MEASURED に入れる）
#   finish                                          # 終了コードを返して終わる
#
# ★この部品自身も凍結の対象です（.claude/breaks/*.sh を全部 凍結するため）。

set -u

ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK="$ROOT/v3-bitget-api-sdk/bitget-python-sdk-api"
PR="$SDK/scripts/priority_rebuild"
VERIFY="$PR/verify_design_contract.py"
BK_TMP="$(mktemp -d)"
BK_FILES=()
MEASURED=0

_hash () { shasum -a 256 "$1" 2>/dev/null | awk '{print $1}'; }

_restore () {
    local rc_keep=$?
    local i=0
    for f in "${BK_FILES[@]:-}"; do
        [ -z "$f" ] && continue
        if [ -f "$BK_TMP/$i.bak" ]; then
            cp -p "$BK_TMP/$i.bak" "$f" 2>/dev/null
        elif [ -f "$BK_TMP/$i.gone" ]; then
            rm -f "$f" 2>/dev/null
        fi
        i=$((i + 1))
    done
    # ★戻したあとハッシュ値を照らす（決まり4）
    i=0
    for f in "${BK_FILES[@]:-}"; do
        [ -z "$f" ] && continue
        if [ -f "$BK_TMP/$i.bak" ]; then
            if [ "$(_hash "$f")" != "$(cat "$BK_TMP/$i.sha")" ]; then
                echo "❌ 元に戻せていません: $f" >&2
                rm -rf "$BK_TMP"
                exit 99
            fi
        fi
        i=$((i + 1))
    done
    rm -rf "$BK_TMP"
    return $rc_keep
}
trap _restore EXIT

guard () {
    local i=0
    for f in "$@"; do
        BK_FILES+=("$f")
        if [ -f "$f" ]; then
            cp -p "$f" "$BK_TMP/$i.bak"
            _hash "$f" > "$BK_TMP/$i.sha"
        else
            : > "$BK_TMP/$i.gone"
        fi
        i=$((i + 1))
    done
}

# ★2026-09-12（まこさん承認）＝測ったコマンドの出力を、捨てずに残す。
#   なぜ直したか（実測 2026-09-11）＝直す前は `>/dev/null 2>&1` で全部 捨てていた。
#     ところが 2026-09-11 に まこさんが決めた案A で、走らせる道具が
#     「出力に `EXPECT_MSG` の文字が在るか」を照らす形になった。
#     ＝捨てていると照らす相手が無く、**16本とも「期待と違う」になった**（走らせて確認）。
#   実測で確かめた3点（2026-09-12）
#     ①`> /dev/null` は画面に出ない ②`$(... 2>&1)` は変数に取れる
#     ③`$(...)` のあとも終了コードは失われない（`Y=$(exit 7)` で 7 が取れた）
MEASURED_OUT=""

measure () {
    MEASURED_OUT="$("$@" 2>&1)"
    MEASURED=$?
}

# ★hook を「その入力で呼んだらどうなるか」で測るための部品
measure_hook () {
    local hook="$1"; shift
    MEASURED_OUT="$(printf '%s' "$1" | bash "$hook" 2>&1)"
    MEASURED=$?
}

finish () {
    # ★測ったコマンドの出力を、走らせる道具へ渡す（`EXPECT_MSG` の照合に使う）
    printf '%s\n' "$MEASURED_OUT"
    exit "$MEASURED"
}
