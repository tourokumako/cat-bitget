#!/bin/bash
# b18 — hook の埋め込み python の中に $( と逆引用符が1つも無いか
#        （完成の条件 #23・設計書 §3.9・まこさん指示 2026-09-03）
#
# なぜ要るか（3回 起きたため）
#   1回目＝require_acceptance_before_impl.sh の102行（逆引用符）＝監査 cp15 の C-9①
#   2回目＝同じファイルの188行（逆引用符・a496c10 で新しく持ち込んだ）＝監査 cp17 の G-7・P-17
#   3回目＝同じファイル（$(）＝hook の文法が壊れ、Bash も Edit も Write も使えなくなった。
#          まこさんに git checkout を1回 打っていただいて戻した。
#   まこさんの逐語＝「4回目を機械で止められます。3回 起きたなら例外にすべきです。」
#
# ★★ この壊すプログラムだけ、ほかの12本と扱いが違います（設計書 §6 の ※4）。
#   ほかは「本物を壊して、trap で戻す」形です。
#   b18 は、生きている hook に1文字も書きません。写しを作って、写しのほうを壊します。
#   理由＝壊す相手が、壊れた瞬間に Bash も Edit も Write も全部 止まるファイルだからです。
#   まこさんの逐語＝「b18 が、生きている hook を壊します」「ここだけ扱いを変えてください」。
#
# 測る順（5つ）
#   1. 生きている hook を、一時の場所へ写す（読むだけ）
#   2. 生きている hook を読んで、埋め込み python の二重引用符の区間に
#      $( と逆引用符が 0個 であることを確かめる（1個でも在れば、その時点で 0 を返す）
#   3. 写しのほうへ $( を1文字 入れて、写しに bash -n を掛け、0 以外が返ることを確かめる
#   4. 逆引用符でも、同じことを写しに対してやる
#   5. 写しを消す（lib.sh の trap がまとめて消す）
#
# ★1文字を入れる場所＝埋め込み python の二重引用符の区間。
#   コメントの中や単引用符の中に入れると bash -n が通ってしまい、意図した測り方になりません。
# ★1通りでも抜けたら 0 を返し、抜けた道の名前を最後の行に出します。
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
CP="$BK_TMP/copy_under_test.sh"
PY="$BK_TMP/embed.py"

NG=0
LEAK=""

if [ ! -f "$H" ]; then
    MEASURED=0
    echo "抜けた道: 相手の hook が在りません"
    finish
fi

# 区間を探して、数える／写しへ1文字 入れる部品
#   ★この中にも $( と逆引用符を1文字も書きません（chr() で作ります）。
cat > "$PY" <<'PYEOF'
import re, sys

DOL = chr(36) + chr(40)          # $(
BQ = chr(96)                     # 逆引用符
DQ = chr(34)                     # 二重引用符
NL = chr(10)


def regions(s):
    # 埋め込み python の二重引用符の区間＝ python3 -c " から、閉じる " まで。
    #
    # ★2026-09-04 に直した（承認②で 37個 と出た＝数え方の誤り）。
    #   直す前の誤り2つ
    #     ①コメントの中の python3 -c " を区間の始まりと読んだ
    #       （この hook は自分の説明文の中で python3 -c に触れている）
    #     ②終わりを「行頭の "」で探した＝1行で書いた埋め込みを閉じられず、
    #       次の区間の終わりまで飲み込み、間に在る bash のコードまで数えた
    #   直した後
    #     ①行の先頭が # の行は見ない
    #     ②開いた " の次から1文字ずつ進み、逆斜線で escape していない " で閉じる
    out = []
    lines = s.split(NL)
    base = 0
    for ln in lines:
        if not ln.lstrip().startswith('#'):
            for m in re.finditer(r'python[0-9.]*\s+-c\s+' + DQ, ln):
                st = base + m.end()
                i = st
                while i < len(s):
                    if s[i] == chr(92):          # 逆斜線＝次の1文字は飛ばす
                        i += 2
                        continue
                    if s[i] == DQ:
                        break
                    i += 1
                if i < len(s):
                    out.append((st, i))
        base += len(ln) + 1
    return out


mode = sys.argv[1]
src = open(sys.argv[2], encoding='utf-8').read()
regs = regions(src)

if mode == 'count':
    n = 0
    for st, e in regs:
        body = src[st:e]
        n += body.count(DOL) + body.count(BQ)
    print(str(len(regs)) + ' ' + str(n))
elif mode == 'inject':
    if not regs:
        sys.exit(3)
    ch = DOL if sys.argv[3] == 'dol' else BQ
    st, e = regs[0]
    with open(sys.argv[4], 'w', encoding='utf-8') as f:
        f.write(src[:e] + ch + src[e:])
else:
    sys.exit(4)
PYEOF

# 1・2 ＝ 生きている hook を読むだけ
OUT=$(python3 "$PY" count "$H" 2>/dev/null)
REGN=$(printf '%s' "$OUT" | awk '{print $1}')
CNT=$(printf '%s' "$OUT" | awk '{print $2}')

if [ -z "$REGN" ] || [ "$REGN" -lt 1 ]; then
    MEASURED=0
    echo "抜けた道: 埋め込み python の区間が1つも見つかりません"
    finish
fi

if [ -z "$CNT" ] || [ "$CNT" -ne 0 ]; then
    MEASURED=0
    echo "抜けた道: いまの hook の埋め込みに ${CNT} 個 在ります（0個であるはず）"
    finish
fi

# 3・4 ＝ 写しのほうを壊して測る（生きている hook には1文字も書かない）
for W in dol bq; do
    rm -f "$CP" 2>/dev/null
    if ! python3 "$PY" inject "$H" "$W" "$CP" 2>/dev/null; then
        NG=1
        LEAK="$LEAK ${W}（写しを作れない）"
        continue
    fi
    bash -n "$CP" >/dev/null 2>&1
    if [ "$?" -eq 0 ]; then
        NG=1
        LEAK="$LEAK ${W}（入れても bash -n が通った）"
    fi
done

if [ "$NG" -eq 0 ]; then
    MEASURED=1
else
    MEASURED=0
    echo "抜けた道:$LEAK"
fi
finish
