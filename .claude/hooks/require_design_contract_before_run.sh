#!/bin/bash
# ★2026-08-23（55回目・まこさん指示）＝fast-mode の一時無効化の行を外した＝safety へ格上げ。
#   まこさんの逐語＝「設計と実装と齟齬をなくすをまず作れっていったんだけど」「これをやれって言ってると思うんだが」。
#   経緯＝2026-07-15 に fast-mode が ON になってから、この hook は1回も動いていなかった（55回目に実測）。
#   その間、engine_tuner の実装は「設計と実装の照合なし」で書かれ続けた（違反＝場面の判定の束のパラメータ）。
#   ★fast-mode 自体は ON のまま（まこさん指示「全部起動しないでほしい」）＝外したのはこの hook の1行だけ。
#
# ★2026-08-23（56回目・まこさん承認 97598f50ee8d…・受け入れ条件 C-2）＝黙って素通りする道を消した。
#   直す前の穴（55回目・56回目に実測）:
#     ① DESIGN_CONTRACT が読めなくても、何も言わずに通っていた（旧 72行目 `[ -z "$HIT_MD" ] && exit 0`）
#     ② DESIGN_CONTRACT が無い .py も、何も言わずに通っていた＝engine_tuner を指す契約は0本
#     ③ 設計書の SPEC と実物の中身を突き合わせる所が無かった
#   ＝「照合が走らなかった」と「照合が通った」が、外から区別できなかった。
#   直した後: ①読めない契約が1本でも在れば止める ②engine_tuner は契約が無ければ止める（fail-closed）
#             ③設計書に SPEC が在れば `--diff` で両方向に突き合わせ、齟齬が在れば止める。
#   ★確認のための走行は通す（この道を塞ぐと、直すこと自体ができなくなる）。
#
# require_design_contract_before_run.sh — PreToolUse on Bash
# 戦略スクリプト（設計書に DESIGN_CONTRACT を持つ実装）を python で実行する前に、
# 設計書 ↔ 実装 の機械照合（verify_design_contract.py）を走らせ、FAIL なら exit 2 でブロック。
#
# 目的（まこさん命令 2026-06-15「hookで物理強制して設計書通りに実装をするようにして」):
#   CC は設計に時間をかけても、まこさんが確認できない工程で設計の核心成分を実装から抜く
#   虚偽（false_positive 類型G・例: E35 設計 §5.2 の RANGE_OK に Jump Model を含むのに実装に無い）
#   を繰り返した。net は score.py が偽れないが「設計通り作った」という工程報告だけは物理チェックが
#   無かった。本 hook はその唯一の穴を塞ぐ＝設計と乖離した実装は trades CSV すら作れない（採点に進めない）。
#
# 限界（正直に）:
#   ・設計書に書く中身が薄ければ、突き合わせも薄い。中身が目的に合っているかは まこさんの目。
#   ・アンダースコアで始まる関数は見ない（内部の小さい関数まで設計書に書くのは現実的でないため）。
#   ・この hook のファイル自体を書き換えれば無効にできる（git diff には必ず出る）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
RATCHET="$BASE/.claude/ratchet"
VERIFY="$BASE/scripts/priority_rebuild/verify_design_contract.py"
ACC="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md"   # 受け入れ条件リストの contract も照合対象に

INPUT=$(cat)

CMD=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print((d.get('tool_input', {}) or {}).get('command', '') or '')
" 2>/dev/null)

# 0) 確認のための走行は通す（★塞ぐと、齟齬を見ることも直すこともできなくなる）
case "$CMD" in
  *--selftest*|*--self-test*|*--verify*|*--identity*|*--help*|*py_compile*|\
  *--scan-contracts*|*--diff*|*--write*)
    exit 0 ;;
esac

# 実行コマンドから走らせる .py の basename 一覧を取得
PYS=$(printf '%s' "$INPUT" | python3 -c "
import sys, json, re, os
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
cmd = (d.get('tool_input', {}) or {}).get('command', '') or ''
# python で「実行」する .py だけを対象にする（git add / ls / grep 等のパス言及には反応しない）
for m in re.finditer(r'python[0-9.]*\s+(?:-[A-Za-z]\S*\s+)*([^\s|&;><]+\.py)', cmd):
    print(os.path.basename(m.group(1)))
" 2>/dev/null)

[ -z "$PYS" ] && exit 0

# 1) ★読めない DESIGN_CONTRACT が1本でも在れば止める（2026-08-23・C-2 の①）
#    直す前は、読めない契約が在っても何も言わずに通っていた。
SCAN_OUT=$(python3 "$VERIFY" --scan-contracts 2>&1)
if [ $? -ne 0 ]; then
    echo "🔒 [設計↔実装ゲート] 読めない DESIGN_CONTRACT が在ります（2026-08-23・まこさん承認）。" >&2
    echo "設計書の DESIGN_CONTRACT が読めない状態では、設計どおりに作ったかを確かめられません。" >&2
    echo "書き方を直してから再実行してください（目印の行＝その語だけの行／見出しの行／囲みの見出し）。" >&2
    echo "$SCAN_OUT" >&2
    exit 2
fi

# 各設計書 contract の impl_file basename → 設計書パス の対応を作り、実行 .py と突き合わせる
# ★2026-08-23＝「どれが設計書か」を決める判定を1か所（scan_contracts）にまとめた。
#   直す前＝この中に同じ処理をもう1つ書いていた。片方だけ `.actual.md`（書き出した文書）を
#   外していたので、書き出した文書を設計書として扱い、誤って止めた（実測）。
HIT_MD=$(printf '%s' "$PYS" | python3 -c "
import sys, os
sys.path.insert(0, '$BASE/scripts/priority_rebuild')
from verify_design_contract import scan_contracts
run = set(x.strip() for x in sys.stdin if x.strip())
ok, _ng, _out = scan_contracts()
for path, c in ok:
    impl = os.path.basename(str(c.get('impl_file', '')))
    if impl and impl in run:
        print(path)
" 2>/dev/null)

# 2) ★engine_tuner は、契約が1本も無ければ走らせない（fail-closed・2026-08-23・C-2 の②）
#    直す前は、契約が無い .py を素通りさせていた＝engine_tuner に照合が1回も掛からなかった。
if [ -z "$HIT_MD" ]; then
    if printf '%s' "$PYS" | grep -q '^engine_tuner'; then
        echo "🔒 [設計↔実装ゲート] engine_tuner を指す DESIGN_CONTRACT が1本もありません（fail-closed・2026-08-23・まこさん承認）。" >&2
        echo "走らせようとしたもの: $(printf '%s' "$PYS" | tr '\n' ' ')" >&2
        echo "設計書に DESIGN_CONTRACT（impl_file＝その .py）を書いてから走らせてください。" >&2
        echo "＝設計と実装の照合が1回も掛からないまま engine_tuner が回る状態を止めます（55回目の重大な不正の温床）。" >&2
        exit 2
    fi
    exit 0
fi

# engine_tuner を走らせようとしているか（C-5・C-6 の強い判定を掛ける相手）
IS_ET=0
printf '%s' "$PYS" | grep -q '^engine_tuner' && IS_ET=1

FAILED=0
MSG=""
while IFS= read -r MD; do
    [ -z "$MD" ] && continue
    OUT=$(python3 "$VERIFY" "$MD" 2>&1)
    if [ $? -ne 0 ]; then
        FAILED=1
        MSG="$MSG
$OUT"
    fi

    # 3) ★設計書に SPEC が在るときだけ、両方向に突き合わせる（2026-08-23・C-2 の③）
    #    SPEC がまだ無い設計書（e35/e37/e38）は、この段を飛ばす＝既存を壊さない。
    DOUT=$(python3 "$VERIFY" --diff "$MD" 2>&1)
    DRC=$?
    NOSPEC=0
    printf '%s' "$DOUT" | grep -q "SPEC が設計書に無い" && NOSPEC=1
    if [ "$DRC" -ne 0 ] && [ "$NOSPEC" -eq 0 ]; then
        FAILED=1
        MSG="$MSG
$DOUT"
    fi

    # 4) ★engine_tuner は SPEC が無ければ走らせない（2026-08-23・C-5・まこさん承認 67da88ef9ca8…）
    #    実測＝SPEC が無いと、弱い側（名前が文字として在るか）しか掛からず通ってしまった。
    if [ "$IS_ET" -eq 1 ] && [ "$NOSPEC" -eq 1 ]; then
        FAILED=1
        MSG="$MSG
[STOP] $MD に SPEC がありません（engine_tuner は SPEC が必須）。
    SPEC ＝ 作る関数と、その関数が呼ぶもの・定数・コマンドの旗の一覧。
    これが無いと『名前が文字として在るか』しか見ません＝中身が空でも通ります。
    出発点は次のコマンドで作れます:
      python3 $VERIFY --write $MD
      → 書き出された <設計書>.actual.md の SPEC を設計書へ写し、今回 変える所だけ手で直す。"
    fi

    # 5) ★設計書が、承認どおりのままかを見る（2026-08-23・C-6・まこさん承認 67da88ef9ca8…）
    #    ＝CC が実装に合わせて設計書を書き換えて食い違いを0件にする道を消す。
    AOUT=$(python3 "$VERIFY" --check-approval "$MD" 2>&1)
    ARC=$?
    if [ "$ARC" -ne 0 ]; then
        FAILED=1
        MSG="$MSG
[STOP] $MD
$AOUT"
    fi
    # engine_tuner だけは「承認の記録が無い」も止める（fail-closed）
    if [ "$IS_ET" -eq 1 ] && printf '%s' "$AOUT" | grep -q "記録なし"; then
        FAILED=1
        MSG="$MSG
[STOP] $MD は、まこさんの承認の記録がありません（engine_tuner は承認が必須）。
    承認: bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_design.sh $MD"
    fi
done <<< "$HIT_MD"

if [ "$FAILED" -ne 0 ]; then
    echo "🔒 [設計↔実装ゲート] 設計書通りに実装されていません（まこさん命令 2026-06-15・類型G 物理検出）。" >&2
    echo "設計が要求した成分が実装に無い、または設計書と実物の中身が食い違っています。" >&2
    echo "実装を設計書どおりに直すか、設計書を実物に合わせて直してから再実行してください。" >&2
    echo "$MSG" >&2
    exit 2
fi
exit 0
