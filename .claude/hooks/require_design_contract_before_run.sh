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

# ★2026-09-02（監査 cp13 の A-2・Critical）＝直す前は穴が2つ在った。
#   ①旧 49-53行が「コマンドの文字列 全体」に対する部分一致だった。
#     ＝コマンドの末尾に `# --help` と書き足すだけで、照合A〜D が1つも走らなかった（監査が実測）。
#   ②旧 40-47行・旧 69行が「読めない入力」を黙って通していた。
#   直した後（監査の逐語「走らせる .py と旗の完全一致へ」「読めない入力は通すを止める側へ」）:
#     ・コメント（# から行末・引用符の中は除く）を先に落とす＝旗の偽装を消す
#     ・区切り（; | &）で断片に分け、断片ごとに『走らせる .py』と『その .py に付いた旗』を見る
#     ・旗は独立した語として一致したときだけ「確認のための走行」と見なす
#     ・入力が読めないときは止める（fail-closed）。python 実行が1つも無いときは通す
SCAN=$(printf '%s' "$INPUT" | python3 -c "
import sys, json, re, os
CHECK = set(['--selftest', '--self-test', '--verify', '--identity', '--help',
             '--scan-contracts', '--diff', '--write', '--dry-run'])
Q = chr(39) + chr(34)
try:
    d = json.load(sys.stdin)
except Exception:
    print('UNREADABLE')
    sys.exit(0)
cmd = (d.get('tool_input', {}) or {}).get('command', '') or ''
clean = []
for ln in cmd.splitlines():
    q = None
    buf = []
    for ch in ln:
        if q:
            buf.append(ch)
            if ch == q:
                q = None
            continue
        if ch in Q:
            q = ch
            buf.append(ch)
            continue
        if ch == '#':
            break
        buf.append(ch)
    clean.append(''.join(buf))
cmd = '\n'.join(clean)
runs = []
saw = False
# ★2026-09-03（監査 cp14 の B-4・Major）＝解析できなかったコマンドは止める。
#   監査の逐語＝『本物のシェル構文解析へ移す（bashlex 等）。それが重い場合の代替＝
#   「解析できなかったコマンドは止める」を上流ゲートにも入れる（いまは通している：97-99行）。
#   あわせて CHECK 旗9個は「その .py が実際にその旗を持つとき」だけ免除する』。
#   ★第一案は使えない（実測＝bashlex が入っていない）ので、書かれた代替を実装した。
#   実測（監査 Q2 の14）＝sh -c／bash -lc／変数経由／xargs／shebang 直実行／旗の追加 の6通りが素通りした。
INDIRECT = re.compile(r'(?:^|[\s;|&(])(?:sh|bash|zsh|env|xargs|eval|nohup|timeout|watch)\s')
# ★2026-09-03（監査 cp15 の C-6）＝.sh の包み紙は、.py が出てこなくても止める。
#   監査の逐語＝「INDIRECT に source ／ . ／ 行頭の ./…\.sh を足す」。
#   実測（監査 cp15）＝'source /tmp/x.sh' と './run.sh' は rc=0 で素通りした。
#   ★中身（.sh の中で何を走らせるか）はここから読めないので、止める側に倒す。
#   ★'bash 何とか.sh' は、走らせる相手がはっきりしているので、いままでどおり通す。
SH_WRAP = re.compile(r'(?:^|[\s;|&(])source\s+\S+'
                     r'|(?:^|[\s;|&(])\.\s+\S+\.sh'
                     r'|(?:^|[\s;|&(])\./\S+\.sh')
VARRUN = re.compile(r'^\s*\\\$\{?\w+')
# ★引用符の中身は「走らせる形」ではなく「文字」として扱う（2026-09-03 に実測して足した）。
#   直す前＝printf で見本の JSON を作るだけのコマンドが、その文字列に python3 と書いてあるだけで
#   止まった（誤検出）。＝実際に走らせているかを、引用符の外だけで判定する。
#   ★ただし sh -c \"...\" の中の .py は見る＝間接的に走らせる形は、外側の語で見つける。
# ★2026-09-03（監査 cp15 の C-7）＝行継続（\ ＋ 改行）を1行につなぐ。
#   直す前＝つないでいなかったので、続きの行の先頭に .py のパスが来ると
#   「shebang での直実行」と誤判定した。実測（監査 cp15）＝読み取りだけの20通りのうち
#   2通り（10%）が止まり、監査の最初のコマンド（wc -l で行数を数えるだけ）も止まった。
cmd = re.sub(r'\\\n', ' ', cmd)
blank = []
q = None
for ch in cmd:
    if q:
        blank.append(' ' if ch != q else ch)
        if ch == q:
            q = None
        continue
    if ch in Q:
        q = ch
    blank.append(ch)
blanked = ''.join(blank)
segs_raw = re.split(r'[;|&\n]+', cmd)
segs_blank = re.split(r'[;|&\n]+', blanked)
if len(segs_raw) != len(segs_blank):
    segs_raw = segs_blank
unparsed = []
for seg, seg_raw in zip(segs_blank, segs_raw):
    m = re.search(r'python[0-9.]*\s+(.*)', seg)
    if not m:
        toks = seg.split()
        if toks and toks[0].rstrip('/').endswith('.py'):     # shebang での直実行
            saw = True
            runs.append(os.path.basename(toks[0]))
            continue
        if SH_WRAP.search(seg):                              # source / . / ./x.sh（中身が読めない）
            unparsed.append(seg_raw.strip())
        elif INDIRECT.search(seg) and '.py' in seg_raw:      # sh -c / xargs / env 経由
            unparsed.append(seg_raw.strip())
        elif VARRUN.match(seg):                              # 変数から組み立てて走らせる
            unparsed.append(seg.strip())
        continue
    args = m.group(1).split()
    # ★2026-09-03（監査 cp16 の E-5・Critical・まこさん指名・承認 36051934db6eede3）
    #   ＝免除は「位置と語の完全一致」でだけ与える。
    #   監査の逐語＝『139行 if 'py_compile' in args をやめ、-m の直後の語が py_compile の
    #     ときだけ免除する』。
    #   直す前の実測（監査 cp16）＝'python3 …/engine_tuner.py --purpose py_compile' が rc=0。
    #     引数の一覧のどこに在っても免除されるので、語を1つ足すだけで上流ゲート全体が外れた。
    #   外の基準＝GHSA-w7qc-6grj-w7r8『許可された命令が入力の中に部分文字列として現れるかで
    #     検証すると、埋め込むだけで迂回できる』。
    _mi = args.index('-m') if '-m' in args else -1
    if _mi >= 0 and _mi + 1 < len(args) and args[_mi + 1] == 'py_compile':
        saw = True
        continue
    # ★2026-09-03（監査 cp15 の C-6）＝-m の免除を外す。py_compile のときだけ通す。
    #   実測（監査 cp15）＝'python3 -m runpy <道具>' / '-m pdb <道具>' / '-m engine_tuner' の
    #   3通りとも rc=0 で素通りした。B-4 が定義した「走らせる .py を確定できない形」に
    #   いちばん素直に当てはまるのに、明示で免除していた。
    if _mi >= 0:
        saw = True
        unparsed.append(seg_raw.strip())
        continue
    pys = [a for a in args if a.endswith('.py')]
    if not pys:
        saw = True
        unparsed.append(seg.strip())     # ★python の実行は在るのに .py を確定できない
        continue
    saw = True
    flags = [a for a in args if a.startswith('-')]
    hit = CHECK & set(flags)
    if hit:
        # ★その .py が実際にその旗を持つときだけ免除する（監査 N-f＝--identity を足すと外れた）
        src = ''
        for cand in (pys[0], os.path.join('$BASE/scripts/priority_rebuild', os.path.basename(pys[0]))):
            try:
                src = open(cand, encoding='utf-8', errors='ignore').read()
                break
            except Exception:
                continue
        if src and any(f in src for f in hit):
            continue
        # 実装が持っていない旗＝免除しない（下の runs に足す）
    runs.append(os.path.basename(pys[0]))
if unparsed:
    print('UNPARSED')
    for u in unparsed[:5]:
        print(u)
    sys.exit(0)
if not saw:
    print('NO_PY')
    sys.exit(0)
print('OK')
for r in runs:
    print(r)
")

STATUS=$(printf '%s\n' "$SCAN" | head -1)
PYS=$(printf '%s\n' "$SCAN" | tail -n +2)

# ★読めない入力は止める（監査 A-2・旧 40-47行の直し）。判定そのものが落ちたときも止める。
if [ "$STATUS" = "UNREADABLE" ] || [ -z "$STATUS" ]; then
    echo "🔒 [設計↔実装ゲート] 入力を読み取れませんでした（2026-09-02・監査 cp13 の A-2）。" >&2
    echo "   直す前は、読めない入力を黙って通していました。いまは止めます（fail-closed）。" >&2
    exit 2
fi

# ★2026-09-03（監査 cp15 の C-7）＝発火したコマンドと理由を1行 残す。
#   監査の逐語＝「発火したコマンドと理由を .claude/state/design_gate_fires.log に1行 残す」。
#   なぜ要るか＝直す前は、止めた記録がどこにも残らず、「3回 止まった」を第三者が検算できなかった。
FIRE_LOG="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/design_gate_fires.log"
log_fire () {
    printf '%s\t%s\t%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" \
        "$(printf '%s' "$INPUT" | tr '\n' ' ' | cut -c1-300)" >> "$FIRE_LOG" 2>/dev/null
}

# ★解析できなかったコマンドは止める（2026-09-03・監査 cp14 の B-4）
if [ "$STATUS" = "UNPARSED" ]; then
    log_fire "UNPARSED（走らせる .py を確定できない）"
    echo "🔒 [設計↔実装ゲート] 走らせる .py を確定できないコマンドです（2026-09-03・監査 cp14 の B-4）。" >&2
    echo "   間接的に走らせる形（sh -c・bash -c・xargs・env・eval・変数から組み立てる）や、" >&2
    echo "   python の実行が在るのに .py を1つに決められない形は止めます。" >&2
    echo "   ＝直す前は、この6通りが照合を1つも通さずに素通りしていました（監査が実測）。" >&2
    echo "   対処＝走らせる .py を、そのままコマンドに書いてください。" >&2
    printf '%s\n' "$PYS" | sed 's/^/   すり抜けようとした断片: /' >&2
    exit 2
fi

# python 実行が1つも無いコマンド（ls・git・grep 等）は、いままでどおり通す
[ "$STATUS" = "NO_PY" ] && exit 0

# 確認のための走行だけだった（--self-test 等が付いている）＝通す
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
    log_fire "照合が落ちた（設計書どおりに実装されていない）"
    echo "🔒 [設計↔実装ゲート] 設計書通りに実装されていません（まこさん命令 2026-06-15・類型G 物理検出）。" >&2
    echo "設計が要求した成分が実装に無い、または設計書と実物の中身が食い違っています。" >&2
    echo "実装を設計書どおりに直すか、設計書を実物に合わせて直してから再実行してください。" >&2
    echo "$MSG" >&2
    exit 2
fi
exit 0
