#!/bin/bash
# ⚠️ fast-mode の早期 exit は「編集対象を判定した後」に移した（2026-07-20）。
#    標準入力は1回しか読めないため、file_path を取る前に exit すると対象別の例外を作れない。
# require_acceptance_before_impl.sh — PreToolUse on Write|Edit
# 戦略実装(scripts/priority_rebuild/*.py)を編集する前に、受け入れ条件リスト(acceptance.md)が在り・
# 対象が一致し・まこさんが承認済(内容指紋一致)であることを確認。無ければ exit 2 でブロック。
#
# 目的（まこさん命令 2026-06-15）:
#   会話の指示も含め「指示→受け入れ条件リスト→合意→実装→照合」を物理強制する。
#   リスト＋まこさんの承認が無いと実装に入れない＝CC が指示を勝手に解釈して別物を作る/部品を抜くを止める。
#
# 正直な限界: 承認は approve_impl.sh の実行で立つ。CC がそれを勝手に実行すれば通せる（完全物理化は
#   まこさんの承認操作が要る）。運用＝承認コマンドはまこさんが打つ。実行はログに残る。中身の骨抜きは
#   score.py の数字＋独立レビューで見る。

# ★2026-09-04（監査 cp18 の J-2）＝相対パスを絶対に直すときの起点
REPO="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LIST="$STATE/acceptance.md"
APPROVED="$STATE/acceptance.approved"

INPUT=$(cat)

# ★2026-09-03（監査 cp16 の実装中に実測して見つけた・Critical）
#   ＝この hook は `LC_CTYPE=UTF-8` が立っていると、何も言わずに全部 通していた。
#   なぜか＝この hook の中の python は `python3 -c "…"` の形で、その中に日本語のコメントが在る。
#     macOS で `LC_CTYPE=UTF-8`（言語の指定が無い形）だと、python がその日本語を読めずに落ちる。
#     落ちたことは `2>/dev/null` で消え、書き込み先が空のまま先へ進み、最後の exit 0 に落ちる。
#   どこで起きるか＝python から子プロセスとして呼ばれたとき（`subprocess.run`）に
#     `LC_CTYPE=UTF-8` が立つ。＝run_breaks.py から呼んだ壊すプログラムは、全部この状態で測っていた。
#   実測＝同じ入力・同じ hook で、そのままなら rc=2、`LC_CTYPE=UTF-8` を立てると rc=0（6通りとも）。
#   直し方＝python を必ず UTF-8 で動かす（locale に左右されない）。
export PYTHONUTF8=1

# ★2026-09-04（監査 cp17 の G-3・G-4・Critical・まこさん指名・承認 435439e9f92e88df）
#   ＝G-3 と G-4 が使う判定を、1か所だけに置く（同じ判定を2か所に書き写さない）。
#   下の2つの埋め込み python が、この変数を読み込んで同じ関数を使う。
#
#   判定＝「この断片は、読み取りだけか」。読み取りだけでなければ False（既定 deny）。
#   ★直す前は「書き込みの語を並べて当てる」形（拒否リスト）でした。
#     並べた語の外は全部 通るので、監査が11通り試すと10通りが素通りしました。
#   外の基準＝GHSA-w7qc-6grj-w7r8『許可された命令が入力の中に部分文字列として
#     現れるかで検証すると、埋め込むだけで迂回できる』
#     ／MITRE ATT&CK T1202『命令を実行できる道具を悪用して、
#       コマンド解釈器の制限を迂回する』。
#
#   ★この中に二重引用符を1文字も書きません（bash の文字列が途中で閉じるため）。
#   ★$( と逆引用符も書きません（3回 壊したため・設計書 §3.9）。要るときは chr() で作ります。
PYJUDGE=$(cat <<'PYJUDGE_EOF'
import re as _re_j
_READONLY_J = ('cat', 'grep', 'egrep', 'fgrep', 'rg', 'ls', 'wc', 'head', 'tail',
               'diff', 'shasum', 'sha256sum', 'md5', 'md5sum', 'stat', 'file',
               'find', 'awk', 'sed', 'echo', 'printf', 'basename', 'dirname',
               'realpath', 'which', 'true', 'test', 'git')
# ★git は、そのファイルの中身を変えられない副命令だけ通す。
#   checkout・restore・stash・clean は中身を変えられるので入れない（監査が実測した抜け道）。
_GIT_OK_J = ('status', 'log', 'diff', 'show', 'add', 'commit', 'ls-files',
             'rev-parse', 'cat-file', 'grep')
_RUN_TOK_J = ('eval', 'xargs', 'source', '.', 'bash', 'sh', 'zsh', 'ksh', 'csh',
              'make', 'perl', 'ruby', 'node', 'osascript', 'env', 'nohup',
              'timeout', 'nice', 'sudo', 'command', 'exec', 'tee', 'cp', 'mv',
              'rm', 'ln', 'touch', 'chmod', 'chown', 'dd', 'install', 'rsync',
              'truncate', 'patch', 'tar', 'ed', 'ex', 'gsed', 'base64', 'open')
# ★2026-09-04（まこさん決定「A」）＝python で走らせてよい道具を、名前で完全一致させる2本だけ。
#   まこさんの逐語＝「list_banned_words.py と gen_impl_functions.py の2本を
#     名前で完全一致させたときだけ通す」「run_breaks.py は入れない。記録を直接 書ける道具だから」。
_TOOL_OK_J = ('list_banned_words.py', 'gen_impl_functions.py')
_RUN_SUB_J = ('-exec', '-execdir', '-ok', '-delete', '-fprint', 'system(',
              'popen(', 'os.system', chr(36) + chr(40), chr(96))
_DEVNULL_J = ('/dev/null', '/dev/stdout', '/dev/stderr', '&1', '&2', '&-')
_SYNTAX_J = ('if', 'then', 'else', 'elif', 'fi', 'for', 'while', 'until', 'do',
             'done', 'case', 'esac', 'in', 'set', 'shopt', 'local', 'return',
             'break', 'continue', 'wait', 'time', 'then')


def _readonly_seg(seg):
    # ①走らせる形が文字として在れば、その時点で False（先頭の語を見るより前）
    for _w in _RUN_SUB_J:
        if _w in seg:
            return False
    # ②リダイレクトの先が捨て先でなければ False
    for _t in _re_j.findall(r'>>?\s*([^\s;|&]+)', seg):
        if _t not in _DEVNULL_J:
            return False
    _toks = seg.split()
    # ③先頭の VAR=値 と、シェルの構文の語を外す
    while _toks and (_re_j.match(r'^[A-Za-z_][A-Za-z_0-9]*=', _toks[0])
                     or _toks[0] in _SYNTAX_J
                     or _toks[0] in ('cd', 'pushd', 'popd')):
        if _toks[0] in ('cd', 'pushd', 'popd'):
            _toks.pop(0)
            if _toks and not _toks[0].startswith('-'):
                _toks.pop(0)
        else:
            _toks.pop(0)
    if not _toks:
        return True
    _head = _toks[0].rsplit('/', 1)[-1]
    # ④文法の確認（bash -n）だけは通す。
    #   ★これを止めると、私は hook の文法を1度も確かめられません（まこさん指示
    #     2026-09-03＝hook を編集したら、次の操作の前に必ず bash -n を通す）。
    #   ★この例外が本当に安全かは、私は確かめていません（設計書 §9 の 1b）。
    #   ★2026-09-04（監査 cp18 の J-1・Critical・まこさん指名・承認 3f22cb79abff786f）
    #     ＝語が ちょうど3つ（先頭・-n・ファイル1つ）のときだけ通す形に狭めた。
    #     監査の逐語＝「bash -c '<コマンド>' -n の -n は、bash にとってオプションではなく
    #       $0（プログラムの名前）になります。bash は -c の中身を実行します。」
    #     直す前＝語のどこかに -n が在れば通した＝bash -c "…" -n が万能の鍵になった
    #       （監査の実測＝承認ゲートも土台ゲートも 6通りとも rc=0）。
    if (_head in ('bash', 'sh', 'zsh') and len(_toks) == 3
            and _toks[1] == '-n'):
        return True
    # ⑤走らせる語・書き込む語は False
    #   ★2026-09-04（まこさん決定「A」）＝python だけ、名前を完全一致させる例外を2本 置く。
    #     なぜ要ったか＝G-4（既定 deny）を入れた後、禁止語チェックのゲートが求める
    #       list_banned_words.py を1本も走らせられず、設計書を1文字も書けない
    #       行き止まりになった（3つのゲートが輪になった）。
    #     ★リダイレクトの判定は、この例外でも外さない＝上の②で既に見ている。
    #     ★危険＝例外そのものが鍵になりうる（設計書 §9 に書く）。
    if _re_j.match(r'^python[0-9.]*$', _head):
        _args = [_t.strip(chr(39) + chr(34)) for _t in _toks[1:]
                 if not _t.startswith('-')]
        if _args and _args[0].rsplit('/', 1)[-1] in _TOOL_OK_J:
            return True
        return False
    if _head in _RUN_TOK_J:
        return False
    # ⑥読み取りの許可リストに無ければ False（★既定 deny＝ここが G-4 の本体）
    if _head not in _READONLY_J:
        return False
    # ⑦git は、2番目の語も見る
    if _head == 'git':
        _rest = [_t for _t in _toks[1:] if not _t.startswith('-')]
        if not _rest or _rest[0] not in _GIT_OK_J:
            return False
    # ⑧sed の書き換え（-i・-i.bak・--in-place）は False
    if _head == 'sed':
        for _t in _toks[1:]:
            if _t.startswith('-i') or _t == '--in-place':
                return False
    return True


def _first_bad_seg(cmd_j):
    # ★断片の1つでも読み取りだけでなければ、その断片を返す（全部 通れば空）
    for _seg in _re_j.split(r'[;|&\n]+', cmd_j):
        if not _seg.strip():
            continue
        if not _readonly_seg(_seg):
            return _seg.strip()
    return ''
PYJUDGE_EOF
)

# ★2026-09-03（監査 cp16 の E-3・Critical・まこさん指名・承認 36051934db6eede3）
#   ＝承認スクリプトを、CC の Bash から打てなくする。
#   監査の逐語＝「approve_impl.sh と approve_design.sh の実行を PreToolUse で rc=2 にし、
#     まこさんだけが端末から直接 動かす」。
#   直す前の実測（監査 cp16 の Q2 の6番）＝道具を壊す → CC が承認を打つ → 照合が
#     rc=1 から rc=0 に戻った。＝3コマンドで、道具の改ざんの検出が消えた。
#   ★まこさんの端末は Claude Code の hook を通らないので、影響を受けません。
#   ★引用符の中も見ます（文章で触れただけを許すと、そこに隠せるため）。
#   ★サブエージェントの素通りより前に置きます＝サブエージェントも打てません。
#   外の基準＝SLSA v1.0 Levels『Build L1 の provenance は trivial to bypass or forge。
#     L2 で初めて a hosted build platform that generates and signs the provenance になる』
#     ＝作る本人が署名すると意味が無い。
#   ★2026-09-03 に実測して狭めた＝「名前が出たら全部 止める」だと git add まで止まった。
#     いまは区切り（; | & 改行）で断片に分け、断片ごとに見る。
#     読むだけの先頭の語（git・cat・grep・ls・shasum・wc・head・tail・diff ほか）と
#     文法確認（bash -n）は通す。それ以外は止める（既定 deny）。
#   ★2026-09-04（監査 cp17 の G-3・Critical・まこさん指名・承認 435439e9f92e88df）
#     ＝「断片の先頭の語だけ見る」短絡をやめた。
#     監査の逐語＝「82-83行の if toks[0] in READONLY: continue を、断片の全体に
#       承認スクリプトの名前が在るかで判定する形に変える
#       （読み取りの語で始まっても -exec・system() で走らせられる）」。
#     直す前の実測（監査 cp17）＝find の -exec で rc=0・awk の system() で rc=0。
#     直した後＝名前がどこかに在れば、断片を全部 上の共通の判定に掛ける。
#       1つでも読み取りだけでなければ止める（既定 deny）。
APPROVE_CMD=$(printf '%s' "$INPUT" | python3 -c "
import sys, json, re
$PYJUDGE
try:
    d = json.load(sys.stdin)
except Exception:
    print('')
    sys.exit(0)
cmd = ((d.get('tool_input', {}) or {}).get('command') or '')
hit = ''
if 'approve_impl.sh' in cmd or 'approve_design.sh' in cmd:
    hit = _first_bad_seg(cmd)
print(hit)
" 2>/dev/null)
case "$APPROVE_CMD" in
  ?*)
    echo "🔒 [承認ゲート] 承認スクリプトは、CC の Bash からは打てません" >&2
    echo "   （2026-09-03・監査 cp16 の E-3・Critical・まこさん指名）。" >&2
    echo "   ＝直す前は、照合の道具を壊してから CC が承認を打つと、壊した版の指紋が" >&2
    echo "     新しい正解として記録され、改ざんの検出が消えました（監査の実測）。" >&2
    echo "   ★まこさんが、ご自分の端末から打ってください（hook を通りません）:" >&2
    echo "       bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh" >&2
    exit 2
    ;;
esac

# 1) サブエージェント(Workflow/Agent 内)かどうかを、ここでは「覚えるだけ」にする。
# ★2026-09-03（監査 cp16 の E-11・まこさん指名・承認 36051934db6eede3）＝ここで通していたのをやめた。
#   監査の逐語＝「23-24行の『サブエージェントは通す』を、土台5ファイルの判定の後ろへ動かす
#   （監査ができなくなる恐れがあるのは戦略の .py だけで、土台5ファイルをサブエージェントが
#   書く理由は無い）」。
#   直す前の実測（監査 cp16 の Q2 の8番）＝agent_type を入れると、土台5ファイルも
#   戦略の .py も、そのまま rc=0 で書けた。
#   直した後＝通すのは「土台のファイルの判定」を抜けた後だけ（下の『サブエージェントはここで通す』）。
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)

# 2) 編集対象を取得。戦略実装(scripts/priority_rebuild/*.py)だけ対象（hook/設計書/state は対象外）
# ★2026-09-04（監査 cp18 の J-2・Critical・まこさん指名・承認 3f22cb79abff786f）
#   ＝file_path を、下の case に掛ける前に1つの絶対パスへ直す。
#   監査の実測＝先頭に / を付けない相対の Write が、hook・道具・戦略の .py の3つとも rc=0。
#   直し方＝引用符を外す ／ 相対ならリポジトリの場所に足す ／ スラッシュの重なりと . と .. を畳む。
FILE=$(printf '%s' "$INPUT" | python3 -c "
import sys, json, os
try:
    _p = (json.load(sys.stdin).get('tool_input', {}) or {}).get('file_path', '') or ''
except Exception:
    _p = ''
if _p:
    _p = _p.strip().strip(chr(39)).strip(chr(34))
    _p = _p.replace(chr(39) + chr(39), '').replace(chr(34) + chr(34), '')
    if not os.path.isabs(_p):
        _p = os.path.join('$REPO', _p)
    _p = os.path.normpath(_p)
print(_p)
" 2>/dev/null)

# ★計器・レポートツールは fast-mode でも承認必須（2026-07-20 まこさん指示「report.pyは勝手に変更できないようにしてよ」）
#   旧仕様＝report.py / plot_trades.py / analyze.py は「表示専用で net 判定も戦略実装もしない」として
#   完全免除だった（2026-06-21 まこさん承認・2026-07-02 に analyze.py 追加）。**2026-07-20 に撤回。**
#   撤回の理由＝CC が「自作 hook を通すため」に report.py の月平均の表示桁を GO なしで書き換えた。
#   表示専用でも勝手に変えれば まこさんが判断に使う数字の見え方が変わる＝判断材料が CC の都合で動く。
case "$FILE" in
  */report.py|*/plot_trades.py|*/analyze.py|*/score.py|*/eval_engine.py|*/precheck.py) TOOLGATE=1 ;;
  *) TOOLGATE=0 ;;
esac

# ★2026-08-23（55回目・まこさん指示）＝fast-mode の一時無効化を外した＝safety へ格上げ。
#   まこさんの逐語＝「これをやれって言ってると思うんだが」。
#   経緯＝2026-07-15 に fast-mode が ON になってから、この hook は1回も動いていなかった（55回目に実測）。
#   その間、engine_tuner の実装は「受け入れ条件＋まこさんの承認」の物理強制なしで書かれ続けた。
#   ★fast-mode 自体は ON のまま（まこさん指示「全部起動しないでほしい」）＝外したのはこの hook の分岐だけ。
#   ★旧仕様＝fast-mode かつ TOOLGATE=0 のとき通していた（下の TOOLGATE=1 は fast-mode でも通さない扱いだった）。
# 診断レーン免除（2026-07-14 まこさん承認）: *_diag.py ＝ read-only の検証/診断（戦略の実関数を import で再利用・
#   print/集計のみ）。改善フロー（新レバー提案）でない検証実装に acceptance ゲートは過剰＝report/analyze と同じ思想。
#   ★歯止め（骨抜き防止）: 新内容 or 既存ファイルに 売買記録CSV出力(to_csv/write_sidecar)・score 呼び出し(import score/
#   score.score)・採用書き出し(_output_and_report/ratchet_io) のいずれかが在れば免除しない＝通常ゲートへ落とす
#   （＝read-only でなければ実験扱い）。採用戦略ファイル(e37_range_scalp.py 等)は別名で今まで通り全ゲート対象＝
#   診断からは採用パイプラインを1文字も変えられない。
case "$FILE" in
  *_diag.py)
    NEWC=$(printf '%s' "$INPUT" | python3 -c "import sys,json;d=(json.load(sys.stdin).get('tool_input',{}) or {});print((d.get('content') or d.get('new_string') or ''))" 2>/dev/null)
    EXIST=""; [ -f "$FILE" ] && EXIST=$(cat "$FILE" 2>/dev/null)
    if printf '%s\n%s' "$NEWC" "$EXIST" | grep -qE 'to_csv|write_sidecar|import score|from score|score\.score|_output_and_report|ratchet_io'; then
      : # CSV/score/採用書き出しを触る＝read-only でない＝下の通常ゲートへ（実験扱い）
    else
      exit 0
    fi
    ;;
esac
# ★2026-09-02（まこさん承認 iter="impl-lock-20260902"）＝Bash で .py を書く道を塞ぐ。
#   なぜ要るか＝この hook は Write と Edit にしか登録されておらず、Bash（リダイレクト・tee・cp・mv・sed -i）で
#   .py を書けば、承認なしで実装できた。2026-08-26 の監査 cp8 が実測で再現した穴（指摘②）。
#   ここでは Bash の command から書き込み先の .py を取り出し、FILE として下の通常ゲートへ落とす。
#   ★引用符とヒアドキュメントの中身は外してから見る＝文章の中でファイル名に触れただけでは止めない
#     （forbid_interpretation_file と同じ考え方）。
if [ -z "$FILE" ]; then
  CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(((json.load(sys.stdin).get('tool_input',{}) or {}).get('command') or ''))" 2>/dev/null)
  if [ -n "$CMD" ]; then
    # ★2026-09-02（監査 cp13 の A-6・Major）＝「正規表現の列挙」から
    #   「書き込み先を確定できないコマンドは止める（既定 deny）」へ。
    #   直す前＝決まった5通りの書き方しか拾えず、12通り試して9通りが抜けた（監査の抜け道13）。
    #   直した後＝①先が取れたら、それを下の通常ゲートへ
    #             ②書き込む動きが在り、かつ scripts/priority_rebuild と .py の両方が出てくるのに
    #               先を1つに決められないときは ?UNKNOWN? を返す（下で止める）
    #             ③読むだけの動きは、いままでどおり通す
    FILE=$(printf '%s' "$CMD" | python3 -c "
import os, re, sys
$PYJUDGE
cmd = sys.stdin.read()
bare = re.sub(r'<<\s*[\'\"]?(\w+)[\'\"]?.*?^\1', ' ', cmd, flags=re.S | re.M)  # ヒアドキュメントの中身を外す
pats = [r'>>?\s*([^\s;|&]+\.py)', r'\btee\s+(?:-a\s+)?([^\s;|&]+\.py)',
        r'\bcp\s+[^\s;|&]+\s+([^\s;|&]+\.py)', r'\bmv\s+[^\s;|&]+\s+([^\s;|&]+\.py)',
        r'\bsed\s+-i[^\s]*\s+(?:[^\s;|&]+\s+)?([^\s;|&]+\.py)',
        r'\bpatch\s+(?:[^\s;|&]+\s+)*([^\s;|&]+\.py)',
        r'\binstall\s+(?:-\S+\s+)*[^\s;|&]+\s+([^\s;|&]+\.py)',
        r'\bdd\b[^;|&]*\bof=([^\s;|&]+\.py)']
for p in pats:
    m = re.search(p, bare)
    if m:
        print(m.group(1)); sys.exit(0)
# ★書き込む動きの語（リダイレクトは上のパターンで先を見るので、ここには入れない）
#   ★単語の境界で見る（2026-09-03 に実測して直した）。
#     直す前は 'ed ' のような文字の一部で当てていたので、'sed -n'（読むだけ）を
#     書き込みと判定して、読み取りのコマンドを誤って止めた。
WRITE_RE = (r'(?:^|[\s;|&(])(?:tee|cp|mv|patch|dd|install|truncate|ed|ex|tar)\s'
            r'|(?:^|[\s;|&(])sed\s+-i'
            r'|(?:^|[\s;|&(])perl\s+-'
            r'|python[0-9.]*\s+-c'
            # ★2026-09-03（監査 cp14 の B-4）＝間接的に走らせる形も、書き込み先を決められない扱いにする。
            #   監査の実測＝変数経由／相対パスに移ってから書く／python のヒアドキュメント／tar 展開 が抜けた。
            # ★「-c で中身を渡す形」「xargs」「eval」だけを見る。'bash 何とか.sh' のように
            #   走らせる相手がはっきりしている形は、いままでどおり通す（2026-09-03 に実測して直した）。
            # ★2026-09-04＝上の2文字は逆引用符だった（監査 cp17 の G-7）。単引用符に直した。
            #   まこさん指示「直す」。b18 が「埋め込みに 2 個 在ります」と出したのが、この2文字。
            r'|(?:^|[\s;|&(])(?:sh|bash|zsh)\s+-[a-z]*c\b'
            r'|(?:^|[\s;|&(])(?:xargs|eval)\s')
# ★2026-09-03（監査 cp16 の E-1・Critical・まこさん指名・承認 36051934db6eede3）
#   ＝Bash から土台のファイルを書く道を塞ぐ。
#   監査の逐語＝『Bash の抽出（78-114行）を、.py のパターンだけでなく、
#     土台5ファイルの名前が現れ、かつ書き込む動きが在れば ?UNKNOWN? で止める形にする。
#     .claude/hooks/*.sh と .claude/tools/*.py も Bash の対象に入れる』。
#   直す前の実測（監査 cp16 の Q2 の8番）＝Write・Edit・MultiEdit は9通り全部 rc=2 なのに、
#     Bash は8通り全部 rc=0（echo > ／ cp ／ sed -i ／ tee ／ 変数 ／ ヒアドキュメント ／ python3 -c）。
#     原因＝下の判定が『scripts/priority_rebuild と .py の両方』を求めるので、
#     土台のファイル（.json・.approved）には1つも当たらなかった。
#   ★土台は6つ（breaks_frozen.json は 2026-09-03 の E-12 で足す）。
# ★2026-09-04（監査 cp17 の G-1・G-2・G-4・Critical・まこさん指名・承認 435439e9f92e88df）
#   G-4＝語の拒否リストを、読み取りだけの許可リスト＋既定 deny へ反転する。
#     監査の逐語＝『土台の名前が現れたら、cat・grep・ls・wc・head・tail・diff・
#       shasum・stat・git status|log|diff|show 以外は全部 ?BASE?
#       （いまは書き込みの語を列挙して当てている）』。
#     直す前の実測（監査 cp17）＝11通り試して10通りが rc=0
#       （rsync・ln -sf・touch・git checkout・git restore・別の .py・
#         base64 で復元して走らせる・gsed -i・rm -f・chmod）。
#     直した後＝断片を全部 上の共通の判定（PYJUDGE）に掛け、
#       1つでも読み取りだけでなければ止める。
#   G-1＝壊し方の記録（<iter>.breaks.json ／ <iter>.frozen.json）を土台に足す。
#     直す前の実測＝Write rc=0・Bash のリダイレクト rc=0
#       ＝run_breaks.py を1回も走らせずに、終了コードを好きな値で書けた。
#   G-2＝.claude/breaks/*.sh を、守る場所に足す。
BASE_NAMES = ('impl_functions_frozen.json', 'spec_lists.json', 'breaks_frozen.json',
              'acceptance.approved', 'verify_tool.approved', 'design_approved.json')
# ★G-1＝名前が iter ごとに変わるので、末尾で見る
BASE_SUFFIX = ('.breaks.json', '.frozen.json')
GATE_RE = re.compile(r'\.claude/hooks/[^\s;|&]*\.sh|\.claude/tools/[^\s;|&]*\.py'
                     r'|\.claude/breaks/[^\s;|&]*\.sh')
raw_cmd = cmd
# ★ヒアドキュメントの中身を見るのは、それを何かに食わせているときだけ
#   （2026-09-03 に実測して狭めた＝git commit の本文に道具の名前が出ただけで止まった）。
INTERP = re.compile(r'(?:^|[\s;|&(])(?:python[0-9.]*|perl|ruby|node|sh|bash|zsh)\b')
feeds = bool(INTERP.search(bare))
# ★名前は『ヒアドキュメントを外した後』で探す。外す前の生も見るのは、
#   ヒアドキュメントを何かに食わせているときだけ（隠した名前を拾うため・監査の実測③）
hit_base = [n for n in BASE_NAMES if (n in bare or (feeds and n in raw_cmd))]
if not hit_base:
    _look = bare + ' ' + (raw_cmd if feeds else '')
    for _t in re.findall(r'[^\s;|&()<>]+', _look):
        if _t.strip(chr(39) + chr(34)).endswith(BASE_SUFFIX):
            hit_base = [_t]
            break
hit_gate = bool(GATE_RE.search(bare)) or (feeds and bool(GATE_RE.search(raw_cmd)))
# ★2026-09-04（監査 cp18 の J-2・Critical・まこさん指名・承認 3f22cb79abff786f）
#   ＝パスらしい語を1つの絶対パスに直してから、守る場所の一覧と照らす。
#   監査の実測＝cd してから相対名で書く3通り・スラッシュ2つ・空の引用符 の5通りとも rc=0。
#   監査の逐語＝「GATE_RE は .claude/hooks/ で始まって .sh で終わる形を探すので、
#     書き込み先が同じファイルでも、書き方を変えると当たりません。」
_GATE_ABS = re.compile(r'^' + re.escape('$REPO')
                       + r'/\.claude/(hooks/[^/]+\.sh|tools/[^/]+\.py|breaks/[^/]+\.sh)$')
_cwd = '$REPO'
_abs_hit = False
for _seg in re.split(r'[;|&\n]+', raw_cmd):
    _tk = _seg.split()
    if _tk and _tk[0] == 'cd' and len(_tk) > 1:
        _d = _tk[1].strip(chr(39)).strip(chr(34))
        _cwd = os.path.normpath(_d if os.path.isabs(_d) else os.path.join(_cwd, _d))
        continue
    for _t in re.findall(r'[^\s;|&()<>]+', _seg):
        _t = _t.strip(chr(39)).strip(chr(34))
        _t = _t.replace(chr(39) + chr(39), '').replace(chr(34) + chr(34), '')
        if not _t or _t.startswith('-'):
            continue
        if not (_t.endswith(('.sh', '.py', '.json', '.approved')) or '/' in _t):
            continue
        _a = os.path.normpath(_t if os.path.isabs(_t) else os.path.join(_cwd, _t))
        if _GATE_ABS.match(_a):
            _abs_hit = True
            break
    if _abs_hit:
        break
if hit_base or hit_gate or _abs_hit:
    # ★生のコマンド（ヒアドキュメントの中身も含む）を見る＝隠す道を残さない
    if _first_bad_seg(raw_cmd):
        print('?BASE?')
        sys.exit(0)
# ★リダイレクトの先が .py のときだけ「書き込み」とみなす（> out.txt は関係ない）

redir_py = [t for t in re.findall(r'>>?\s*([^\s;|&]+)', bare) if t.endswith('.py')]
# ★見るのはヒアドキュメントの中身を外した後（既存の考え方＝文章の中でファイル名に触れただけでは
#   止めない）。★限界＝python のヒアドキュメントの中に書き込みを隠す道は残る（設計書 §9）。
whole = bare
if 'scripts/priority_rebuild' in whole and '.py' in whole:
    if redir_py or re.search(WRITE_RE, whole):
        print('?UNKNOWN?')
" 2>/dev/null)

    FILE_RC=$?
    # ★2026-09-03（監査 cp16 の実装中に実測して足した・Critical）＝読み取りに失敗したら止める。
    #   直す前＝ここの python が落ちても 2>/dev/null で消え、書き込み先が空のまま先へ進み、
    #   最後の exit 0 に落ちていた（＝この hook が丸ごと no-op になっていた）。
    #   実測＝LC_CTYPE=UTF-8 を立てると、6通り全部が rc=0 で通った。
    if [ "$FILE_RC" -ne 0 ] && [ -n "$CMD" ]; then
      echo "🔒 [受け入れ条件ゲート] コマンドの読み取りに失敗しました（2026-09-03・fail-closed）。" >&2
      echo "   ＝判定できないので止めます。直す前は、黙って通していました。" >&2
      exit 2
    fi

    # ★2026-09-03（監査 cp16 の E-1）＝Bash から土台のファイル・hook・道具を書く道を塞ぐ。
    if [ "$FILE" = "?BASE?" ]; then
      echo "🔒 [土台ゲート・Bash] 強制の土台になるファイルを、Bash で書こうとしています" >&2
      echo "   （2026-09-03・監査 cp16 の E-1・Critical）。" >&2
      echo "   対象＝impl_functions_frozen.json ／ spec_lists.json ／ breaks_frozen.json ／" >&2
      echo "         acceptance.approved ／ verify_tool.approved ／ design_approved.json ／" >&2
      echo "         <iter>.breaks.json ／ <iter>.frozen.json（2026-09-04・G-1）／" >&2
      echo "         .claude/hooks/*.sh ／ .claude/tools/*.py ／ .claude/breaks/*.sh（G-2）" >&2
      echo "   ＝直す前は、書き込みの語を並べて当てていたので、監査が11通り試すと10通りが" >&2
      echo "     通りました（rsync・ln -sf・touch・git checkout・git restore・別の .py ほか）。" >&2
      echo "   ★2026-09-04（G-4）＝読み取りだけの語を並べ、それ以外は全部 止める形にしました。" >&2
      echo "   ★通るもの＝cat・grep・ls・wc・head・tail・diff・shasum・stat・find・awk・sed（-i なし）" >&2
      echo "     ／ git status・log・diff・show・add・commit・ls-files・rev-parse・cat-file・grep" >&2
      echo "     ／ bash -n（文法の確認）。リダイレクトは /dev/null 以外 止まります。" >&2
      echo "   直す道＝①hook と道具は Write / Edit ツールで書く（承認の確認が掛かります）" >&2
      echo "           ②土台のファイルは、まこさんに承認を打ってもらう" >&2
      exit 2
    fi

    # ★書き込み先を1つに決められないときは止める（既定 deny・監査 A-6）
    if [ "$FILE" = "?UNKNOWN?" ]; then
      echo "🔒 [受け入れ条件ゲート] 書き込み先を確定できないコマンドです（2026-09-02・監査 cp13 の A-6）。" >&2
      echo "   コマンドに scripts/priority_rebuild と .py が出てきて、書き込む動きが在りますが、" >&2
      echo "   書き込み先の .py を1つに決められませんでした。" >&2
      echo "   ＝直す前は、決まった5通りの書き方しか拾えず、12通り試して9通りが抜けていました。" >&2
      echo "   対処＝Write / Edit ツールで書いてください（承認の確認が正しく掛かります）。" >&2
      exit 2
    fi
  fi
fi

# ★2026-09-03（監査 cp14 の P-5）＝承認と食い違う設計書のままでは、監査依頼書を作らせない。
#   監査の逐語＝「監査依頼書を作る道具が、acceptance.md の指紋と acceptance.approved を照合し、
#   食い違ったら依頼書を作らせない」。
#   ★道具（gen_audit_request.py）だけに置くと素通りする＝cp13・cp14 の依頼書は道具を使わず
#     Write ツールで手で書いた。だから書き込みの道にも同じ判定を置く。
case "$FILE" in
  */.claude/audits/inputs/*.md)
    NOWSHA=$(shasum -a 256 "$LIST" 2>/dev/null | awk '{print $1}')
    WANTSHA=$(cat "$APPROVED" 2>/dev/null)
    if [ -z "$WANTSHA" ] || [ "$NOWSHA" != "$WANTSHA" ]; then
      echo "🔒 [監査依頼書ゲート] 設計書が承認と食い違うので、依頼書を作れません（2026-09-03・監査 cp14 の P-5）。" >&2
      echo "   承認された値: ${WANTSHA:0:16}… ／ いまの設計書: ${NOWSHA:0:16}…" >&2
      echo "   ＝79回目に、承認の後に設計書の3行を書き換えて監査に出しました（監査 P-5）。" >&2
      echo "   対処＝まこさんに再承認を打ってもらってから、依頼書を書いてください。" >&2
      exit 2
    fi
    ;;
esac

# ★2026-09-03（監査 cp15 の C-2・Critical）＝強制の土台になるファイルは、承認の道具だけが書く。
#   監査の逐語＝「凍結ファイル・承認の印・照合の道具・ゲートの hook を、書き込みの関所の対象にする」。
#   実測（監査 cp15）＝これら5つへ Write を掛け、登録された 32本すべてを走らせたが、
#   中身を見て止めるものは 0本だった。＝B-1 の土台が、承認なしで書き換えられる状態だった。
#   ★ここで止めるのは Write / Edit / MultiEdit（＝CC が直接 書き換える道）。
#     承認スクリプト（approve_impl.sh／approve_design.sh）は Bash で走るので止まらない。
#   ★2026-09-03（監査 cp16 の E-1）＝Bash 経由も上で塞いだ（?BASE?）。
#   ★2026-09-03（監査 cp16 の E-12）＝breaks_frozen.json（壊すプログラムの凍結）を足して6つにした。
#   ★2026-09-04（監査 cp17 の G-1・Critical・まこさん指名・承認 435439e9f92e88df）
#     ＝壊し方の記録（<iter>.breaks.json）と、承認のときの控え（<iter>.frozen.json）を足した。
#     監査の逐語＝「BASE_NAMES に .breaks.json と .frozen.json を足し、case にも足す」。
#     直す前の実測＝<iter>.breaks.json へ Write rc=0・Bash のリダイレクト rc=0。
#     ＝run_breaks.py を1回も走らせずに終了コードを書けたので、
#       E-12（壊し方を機械が走らせて記録に残す）の記録が根拠にならなかった。
case "$FILE" in
  */.claude/ratchet/impl_functions_frozen.json|*/.claude/ratchet/spec_lists.json|\
*/.claude/ratchet/breaks_frozen.json|\
*.breaks.json|*.frozen.json|\
*/.claude/state/acceptance.approved|*/.claude/state/verify_tool.approved|\
*/.claude/state/design_approved.json)
    echo "🔒 [土台ゲート] このファイルは、承認の道具だけが書きます（2026-09-03・監査 cp15 の C-2）。" >&2
    echo "   対象＝$FILE" >&2
    echo "   ＝凍結された期待値・承認の印・正本の一覧・壊すプログラムの凍結は、強制の土台です。" >&2
    echo "   CC が直接 書き換えられると、照合の結果を好きな値にできます（監査の実測）。" >&2
    echo "   直す道＝まこさんに承認を打ってもらう: bash .claude/hooks/approve_impl.sh" >&2
    exit 2
    ;;
esac

# ★2026-09-03（監査 cp16 の E-11・まこさん指名）＝サブエージェントはここで通す。
#   ＝土台のファイルの判定（上の2つ＝Bash の ?BASE? と、この case）を抜けた後だけ。
#   なぜここか＝監査ができなくなる恐れがあるのは戦略の .py と hook・道具の方であって、
#   土台のファイルをサブエージェントが書く理由は無い（監査の逐語）。
#   ★2026-09-04（監査 cp17 の G-2・承認② の実測で見つけた）
#     ＝壊すプログラム（.claude/breaks/*.sh）だけは、サブエージェントでも通さない。
#     承認② の実測＝`b16_breaks_write.sh` が rc=0（記録の note＝「抜けた道: サブエージェントのWrite」）。
#     原因＝ここの通り抜けが、承認ゲートの case より手前に在った。
#     ＝壊すプログラムは 土台ゲートではなく承認ゲートに入れた（設計書 §3.4）ので、
#       サブエージェントは素通りしていた。
#   ★2026-09-04（監査 cp18 の J-3・Critical・まこさん指名・承認 3f22cb79abff786f）
#     ＝通さない相手を、壊すプログラムだけから4つへ広げた。
#     監査の逐語＝「.claude/hooks/*.sh が素通りするということは、
#       require_acceptance_before_impl.sh そのものを1回の Write で空にできるということです。
#       そうすれば、G-1〜G-4 も、承認ゲートも、土台ゲートも、同時に消えます。」
#     監査の実測＝agent_type を入れた Write が hook・道具・戦略の .py の3つとも rc=0。
#     ★監査のサブエージェントは読むだけなので、監査は今までどおり行える。
case "$FILE" in
  */.claude/breaks/*.sh|*/.claude/hooks/*.sh|*/.claude/tools/*.py|*scripts/priority_rebuild/*.py) ;;
  *)
    if [ -n "$AGENT_TYPE" ]; then
      exit 0
    fi
    ;;
esac

# ★2026-09-03（監査 cp15 の C-2）＝承認ゲートの対象を、hook 本体と道具にも広げる。
#   直す前＝scripts/priority_rebuild/*.py だけが対象で、hook や道具は承認なしで書けた。
#   直した後＝設計書の TARGET に書いて承認をもらわないと書けない（判定は下の既存のものを使う）。
#   ★2026-09-04（監査 cp17 の G-2・Critical・まこさん指名・承認 435439e9f92e88df）
#     ＝壊すプログラム（.claude/breaks/*.sh）を、この関所の相手に足した。
#     監査の逐語＝「同じ2か所に .claude/breaks/[^\s;|&]*\.sh を足す」。
#     直す前の実測＝Write rc=0・Bash のリダイレクト rc=0。
#     凍結（breaks_frozen.json）は承認の「後」にしか効かないので、
#     承認の「前」に壊すプログラムを骨抜きにできた。
#     ★ここは土台ゲート（承認の道具だけが書く）ではなく、承認ゲートにする。
#       理由＝私が書かないと、壊すプログラムそのものを作れなくなるため。
case "$FILE" in
  *scripts/priority_rebuild/*.py) ;;
  */.claude/hooks/*.sh) ;;
  */.claude/tools/*.py) ;;
  */.claude/breaks/*.sh) ;;
  *) exit 0 ;;
esac

GUIDE="流れ: ①CC が $LIST に「TARGET: <対象.py>」と受け入れ条件(やること)を書く ②チャットで提示 ③まこさんが内容OKなら『bash .claude/hooks/approve_impl.sh』を実行 ④実装"

# 3) リスト存在
if [ ! -f "$LIST" ]; then
  echo "🔒 [受け入れ条件ゲート] 実装の前に受け入れ条件リストがありません: $LIST" >&2
  echo "$GUIDE" >&2
  exit 2
fi

# 4) TARGET 一致（複数 TARGET 行 or カンマ区切りを許可・2026-06-22 まこさん承認＝
#    1 acceptance で複数ファイルをまとめて承認できる＝承認の往復を減らす。各 TARGET いずれかに一致すれば通す）
TARGETS=$(grep -E '^TARGET:' "$LIST" | sed 's/^TARGET:[[:space:]]*//' | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$')
if [ -z "$TARGETS" ]; then
  echo "🔒 [受け入れ条件ゲート] $LIST に『TARGET: <対象.py>』がありません。" >&2
  echo "$GUIDE" >&2
  exit 2
fi
# ★2026-09-02（まこさん承認 iter="impl-lock-20260902"）＝設計書に impl_functions を書かせる。
#   なぜ要るか＝2026-09-02 に、設計書に「4通り展開する」と書いて実装は2通りだった。
#   既に在る照合は どれも止めなかった。書いてなければ照合しようがないので、書くところを強制する。
#   ★これで塞がるのは「1件も書かない」だけ＝「1件だけ書く」は照合A・B（git の差分と両方向）が塞ぐ。
# ★2026-09-02（監査 cp13 の A-5・Major）＝impl_functions・must_use・spec_lists を必須にし、
#   空の辞書・空の配列を拒否する。
#   直す前＝`grep -q '"impl_functions"'` だけ＝その文字が在れば通り、中身が空でも通った
#   （監査の抜け道2「空の辞書で書く」・抜け道3「must_use・spec_lists を書かない」）。
# ★2026-09-03（監査 cp15 の C-9①）＝埋め込みの python を、二重引用符の中に書くのをやめた。
#   直す前＝`python3 -c "…"` の中に python を書いていたので、bash が中身を先に読んだ。
#   実測（監査 cp15）＝コメントの中の逆引用符がコマンド置換として実行され、
#   書き込みの判定19通りで19回とも stderr に `bash: 何とか.sh: No such file or directory` が出た。
#   直した後＝ヒアドキュメント（'PYEOF' の引用符つき＝展開なし）。$ も ` もそのまま python に渡る。
DC_NG=$(python3 - "$LIST" <<'PYEOF'
import json, os, re, sys
FENCE = chr(96) * 3
# ★2026-09-03（監査 cp16 の E-12）＝壊し方の記録を読むために、場所を1つ持つ
SDK = ("/Users/tachiharamasako/Documents/GitHub/cat-bitget/"
       "v3-bitget-api-sdk/bitget-python-sdk-api")
md = open(sys.argv[1], encoding='utf-8').read()
ng = []
obj = None
for b in re.findall(FENCE + r'json\s*(\{.*?\})\s*' + FENCE, md, re.S):
    try:
        d = json.loads(b)
    except Exception:
        continue
    if 'impl_file' in d:
        obj = d
        break
if obj is None:
    ng.append('  ・DESIGN_CONTRACT（impl_file を持つ json）が読めません')
else:
    impl = obj.get('impl_functions')
    # ★2026-09-03（監査 cp15 の C-4）＝設計の段階では正確に書けないので、空でも通す。
    #   なぜ変えたか（実測・監査 cp14 の N-e）＝まだ触っていないファイルに機械生成の道具を掛けると
    #   空の配列が出る。それを設計書に書くと、直す前の この判定が拒否した。
    #   ＝正直に書くと落ちて、実装からコピーすると通る形だった。だから CC は毎回コピーを選んだ。
    #   直した後＝空でよい。ただし「なぜ空か」と「実装の後に確定させる」を書かせる。
    if not isinstance(impl, dict):
        ng.append('  ・impl_functions がありません')
    elif not impl:
        if not obj.get('no_impl_functions_reason'):
            ng.append('  ・impl_functions が空なのに no_impl_functions_reason'
                      '（なぜ設計の段階で書けないか）がありません（監査 cp15 の C-4）')
        if '実装の後に確定' not in md:
            ng.append('  ・impl_functions が空なので、完成の条件に'
                      '「実装の後に確定させる」を書いてください（監査 cp15 の C-4）')
    else:
        for k, v in impl.items():
            if not isinstance(v, list) or not v:
                ng.append('  ・impl_functions の ' + str(k) + ' が空の配列です')
    mu = obj.get('must_use')
    muf = obj.get('must_use_from')
    # ★2026-09-03（監査 cp15 の C-4 の対）＝impl_functions が空のときは、
    #   どの関数に何を要求するかも決まっていないので、must_use も空でよい。
    #   実装の後に、両方を同時に確定させて凍結する。
    _impl_empty = isinstance(impl, dict) and not impl
    if (not _impl_empty and not (isinstance(mu, dict) and mu)
            and not (isinstance(muf, dict) and muf)):
        ng.append('  ・must_use（または must_use_from）がありません（または空）')
    sl = obj.get('spec_lists')
    if not isinstance(sl, dict):
        ng.append('  ・spec_lists がありません')
    elif not sl and not obj.get('no_spec_lists_reason'):
        ng.append('  ・spec_lists が空なのに no_spec_lists_reason（外から取る一覧が無い理由）がありません')
    # ★方針②（監査 §6-A の2）＝生の一覧を手で書かせず、正本を指させる。
    #   値をそのまま並べた形（配列）は止める。正しい形＝{'from': 正本のファイル, 'kind': ..., 'probe': ...}
    for k, v in (sl if isinstance(sl, dict) else {}).items():
        if not isinstance(v, dict):
            ng.append('  ・spec_lists の ' + str(k) + ' に値をそのまま書いています'
                      '（正本を指す形にする: {\"from\": \"<正本のファイル>\", \"kind\": ..., \"probe\": ...}）')
        elif not v.get('from'):
            ng.append('  ・spec_lists の ' + str(k) + ' に from（正本のファイル）がありません')
    for k, v in (obj.get('must_use_from') or {}).items():
        if not isinstance(v, dict) or not v.get('from'):
            ng.append('  ・must_use_from の ' + str(k) + ' に from（正本のファイル）がありません')
# ★2026-09-03（監査 cp15 の C-1・Critical）＝完成の条件は、機械が読む目印の中だけを見る。
#   監査の逐語＝「設計書の完成の条件の表を <!-- ACCEPT_TABLE_START --> 〜 <!-- ACCEPT_TABLE_END -->
#   で囲み、承認ゲートはその中だけを見る。あわせて『経路』は表の欄として読む」。
#   直す前の実測（監査 cp15）＝見出しを正規表現で探す形だったので、「完成」を含む最初の見出し
#   （直し方の表）を拾い、本物の完成の条件を1文字も見ていなかった。
#   ★目印は「その行だけ」に限る（2026-09-03 に実測して直した）。直す前＝行の途中の文字も拾ったので、
#     機械が作った §0-2 の表に写された監査の逐語（C-1 の説明の中の目印）から読み始めていた。
_m_at = re.search(r'^<!--\s*ACCEPT_TABLE_START\s*-->\s*$(.*?)^<!--\s*ACCEPT_TABLE_END\s*-->\s*$', md, re.S | re.M)
if _m_at is None:
    ng.append('  ・完成の条件の表が、機械が読む目印で囲まれていません'
              '（監査 cp15 の C-1／ACCEPT_TABLE_START 〜 ACCEPT_TABLE_END）')
    _at_body = ''
else:
    _at_body = _m_at.group(1)

# 方針①（監査 cp13 の §6-A の1）＝人が目で確かめる形を、完成の条件にしない。
for w in ('まこさんが確認', 'まこさんの目', 'まこさんが見', '人が見て', '目視'):
    if w in _at_body:
        ng.append('  ・完成の条件に「' + w + '」が在ります'
                  '（人が目で確かめる形を完成の条件にしない＝監査 cp13 の方針①）')
# ★2026-09-03（監査 cp14 の P-4・最優先）＝各機械生成ブロックに「何から作ったか」を必須にする。
#   監査の逐語＝「『機械生成』は正しさの根拠にならない。何から生成したかで決まる。
#   正本から生成＝正しい／実装から生成＝循環」。
if obj is not None:
    gf = obj.get('generated_from')
    if not isinstance(gf, dict) or not gf:
        ng.append('  ・generated_from（各ブロックを何から作ったか）がありません'
                  '（監査 cp14 の P-4／形＝鍵ごとに、その中身を何から作ったかを1行で書く）')
    elif 'impl_functions' not in gf:
        ng.append('  ・generated_from に impl_functions の出どころがありません（監査 cp14 の P-4）')

# ★2026-09-03（監査 cp15 の C-1・P-7）＝「経路」と「壊し方」を、表の欄として読む。
#   直す前＝行に「部品」の文字が在るかで見ていた＝説明の文まで拾った（監査の実測＝3件と出た）。
#   直した後＝表を欄に分け、経路の欄の値が「部品」の行だけを見る。
#   ★P-7（監査 cp15）＝「壊し方」の欄を必須にし、壊し方が書けない行は「済」にできない。
_rows = []
for ln in _at_body.splitlines():
    s = ln.strip()
    if not s.startswith('|'):
        continue
    cells = [c.strip() for c in s.strip('|').split('|')]
    if set(''.join(cells)) <= set('-: '):        # 区切りの行
        continue
    _rows.append(cells)
_head = _rows[0] if _rows else []
def _col(name):
    for i, c in enumerate(_head):
        if name in c:
            return i
    return -1
_i_route, _i_break, _i_state = _col('経路'), _col('壊し方'), _col('いまの状態')
# ★2026-09-03（監査 cp16 の E-12・まこさん指名・承認 36051934db6eede3）
#   ＝壊すプログラムの欄と、その終了コードの記録を見る。
_i_prog = _col('壊すプログラム')
# ★2026-09-03（まこさん指示・§3.2c）＝「監査確認」の欄。値は 対象 か —。
#   対象 を書けるのは、下の合言葉が完成の条件に在る行だけ。合言葉は5つで固定。
#   ★増やすには、この .sh を書き換えることになる＝設計書に書いて、まこさんの承認が要る。
_i_audit = _col('監査確認')
AUDIT_TOKENS = ('AUDIT-1', 'AUDIT-2', 'AUDIT-3', 'AUDIT-4', 'AUDIT-5')
if _at_body:
    if _i_route < 0:
        ng.append('  ・完成の条件の表に「経路」の欄がありません（値＝実経路 か 部品・監査 cp14 の P-6）')
    if _i_break < 0:
        ng.append('  ・完成の条件の表に「壊し方」の欄がありません（監査 cp15 の P-7）')
    if _i_prog < 0:
        ng.append('  ・完成の条件の表に「壊すプログラム」の欄がありません（監査 cp16 の E-12）')
    if _i_audit < 0:
        ng.append('  ・完成の条件の表に「監査確認」の欄がありません'
                  '（値＝対象 か —・まこさん指示 2026-09-03）')
# ★壊し方の記録（承認のたびに機械が書く）を読む
_breaks = {}
_it = re.search(r'iter="([^"]+)"', md)
if _it:
    _bp = os.path.join(SDK, '.claude', 'ratchet', 'acceptance_archive',
                       _it.group(1) + '.breaks.json')
    if os.path.exists(_bp):
        try:
            for _r in (json.load(open(_bp, encoding='utf-8')).get('rows') or []):
                if _r.get('script'):
                    _breaks[str(_r.get('script'))] = _r.get('code')
        except Exception:
            _breaks = {}
_seen_tokens = []
for cells in _rows[1:]:
    _route = cells[_i_route] if 0 <= _i_route < len(cells) else ''
    _brk = cells[_i_break] if 0 <= _i_break < len(cells) else ''
    _state = cells[_i_state] if 0 <= _i_state < len(cells) else ''
    _prog = cells[_i_prog].strip().strip('`') if 0 <= _i_prog < len(cells) else ''
    _prog = re.sub(r'（.*?）', '', _prog).strip().strip('`')
    _aud = cells[_i_audit] if 0 <= _i_audit < len(cells) else ''
    _cond = cells[1] if len(cells) > 1 else ''
    if '部品' in _route and '✅' in _state:
        ng.append('  ・完成の条件で、経路が「部品」の行に「済」が在ります'
                  '（部品だけで確かめた行は済にできない・監査 cp14 の P-6）')
    if '✅' in _state and (not _brk or _brk in ('—', '-', 'なし')):
        ng.append('  ・完成の条件で、壊し方を書いていない行に「済」が在ります'
                  '（壊し方が書けない行は済にできない・監査 cp15 の P-7）')
    # ★E-12＝済にできるのは、壊すプログラムの終了コードが 0 以外だったときだけ
    if '✅' in _state:
        if not _prog or _prog in ('—', '-', 'なし'):
            ng.append('  ・完成の条件で、壊すプログラムが無い行に「済」が在ります'
                      '（監査 cp16 の E-12＝機械が走らせた終了コードだけが根拠）')
        elif _prog not in _breaks:
            ng.append(f'  ・完成の条件の「済」に、壊し方の記録がありません（{_prog}）'
                      '（監査 cp16 の E-12／承認のたびに機械が <iter>.breaks.json に書きます）')
        elif _breaks.get(_prog) in (0, None):
            ng.append(f'  ・完成の条件の「済」の壊すプログラムが止まっていません（{_prog}'
                      f'・終了コード {_breaks.get(_prog)}）'
                      '（監査 cp16 の E-12＝0 以外のときだけ済にできます）')
    # ★監査確認の欄＝対象 を書けるのは、合言葉が在る行だけ・同じ合言葉は1行まで
    if '対象' in _aud:
        _hit = [t for t in AUDIT_TOKENS if t in _cond]
        if not _hit:
            ng.append('  ・監査確認に「対象」と書いた行に、合言葉がありません'
                      '（AUDIT-1〜AUDIT-5 のどれか1つを完成の条件に書く'
                      '・まこさん指示 2026-09-03＝監査に丸投げする道を作らない）')
        for _t in _hit:
            if _t in _seen_tokens:
                ng.append(f'  ・監査確認の合言葉 {_t} が2行に在ります'
                          '（同じ札で何行も逃げられません・まこさん指示 2026-09-03）')
            _seen_tokens.append(_t)

# ★2026-09-03（監査 cp14 の B-5）＝§9「塞げないもの」に、監査 Q5 の5件を書かせる。
sec9 = re.search(r'^#+[^\n]*塞げないもの[^\n]*\n(.*?)(?=\n#+ |\Z)', md, re.S | re.M)
if sec9 is None:
    ng.append('  ・「塞げないもの」の節がありません（監査 cp14 の B-5）')
else:
    # ★5件が書かれているかは、監査の番号そのもので見る（言い回しに寄りかからない）。
    for w in ('Q5 の1', 'Q5 の2', 'Q5 の3', 'Q5 の4', 'Q5 の5'):
        if w not in sec9.group(1):
            ng.append('  ・「塞げないもの」に「監査 ' + w + '」の件が書かれていません'
                      '（監査 Q5 の5件を書く・監査 cp14 の B-5）')

# ★2026-09-03（監査 cp14 の B-6）＝「実測」と書いた行に、実行コマンドが無ければ止める。
#   ★除外＝機械が作った表（監査レポートの逐語）／引用（>）／囲みの中／「逐語」を含む行／
#     「塞げないもの」の節。ここは実測の報告ではなく、相手の文書の写しと限界の一覧のため。
CMDWORD = ('python3', 'python ', 'bash ', 'git ', 'ls ', 'wc ', 'shasum', 'diff ', 'grep ')
lines = md.splitlines()
inblock = False
infence = False
ins9 = False
for _i, ln in enumerate(lines):
    s = ln.strip()
    nxt = lines[_i + 1].strip() if _i + 1 < len(lines) else ''
    if s.startswith('|') and nxt.startswith('|') and set(nxt) <= set('-:| '):
        continue                          # 表の見出しの行は「実測の報告」ではない
    if s.startswith('<!-- AUDIT_TODO_START'):
        inblock = True
    elif s.startswith('<!-- AUDIT_TODO_END'):
        inblock = False
    if s.startswith(chr(96) * 3):
        infence = not infence
    if s.startswith('#'):
        ins9 = '塞げないもの' in s
    if s.startswith('#'):                 # 見出しは「実測の報告」ではない
        continue
    if inblock or infence or ins9 or s.startswith('>') or '逐語' in s:
        continue
    # ★対象＝結果を主張している行だけ（✅ が付いた行 か「実測＝」と書いた行）。
    #   未着手・未検証の行は、まだ結果が無いので対象にしない。
    #   ★限界（正直に）＝「実測」の語を使わずに結果を書けば、この検査には当たらない。
    if ('✅' in s or '実測＝' in s) and not any(c in s for c in CMDWORD):
        ng.append('  ・結果を書いた行に実行コマンドがありません（監査 cp14 の B-6）: '
                  + s[:60])
        break
print('\n'.join(ng))
PYEOF
)

if [ -n "$DC_NG" ]; then
  echo "🔒 [受け入れ条件ゲート] DESIGN_CONTRACT の中身が足りません（2026-09-02・監査 cp13 の A-5）。" >&2
  echo "$DC_NG" >&2
  echo "   なぜ＝空で書けると、中身の照合を丸ごと省略できます（監査の抜け道2・3）。" >&2
  echo '   形: "impl_functions": {"<file>.py": ["関数名", ...]} ／ "must_use": {"関数名": ["名前", ...]}' >&2
  echo '        "spec_lists": {"鍵": {"from": "<正本のファイル>", "kind": "...", "probe": "モジュール:関数"}}' >&2
  exit 2
fi

MATCH=0
while IFS= read -r tgt; do
  [ -z "$tgt" ] && continue
  case "$FILE" in *"$tgt") MATCH=1; break ;; esac
done <<EOF
$TARGETS
EOF
if [ "$MATCH" -ne 1 ]; then
  echo "🔒 [受け入れ条件ゲート] 編集対象($FILE)がリストの TARGET($(echo "$TARGETS" | tr '\n' ' '))のいずれとも一致しません。" >&2
  echo "$GUIDE" >&2
  exit 2
fi

# 5) 機械照合用の部品リスト(DESIGN_CONTRACT)が在るか（書き忘れ防止＝明文化できる範囲を機械で漏れなく）
if ! grep -q "DESIGN_CONTRACT" "$LIST"; then
  echo "🔒 [受け入れ条件ゲート] $LIST に機械照合用の部品リスト(DESIGN_CONTRACT ブロック)がありません。" >&2
  echo "やること(自然言語)に加え、実装と機械照合できる部品リスト(DESIGN_CONTRACT の json: impl_file / self_check_calls / must_combine)を必ず書いてください。" >&2
  exit 2
fi

# 5.5) 深い分析＋ベースアップの必須化（まこさん命令 2026-06-15「分析と改善のフローが一番重要・深掘りしてから改善案」）
#   難しい問題に最易パッチを当てる前に、損の真因・期待値のどれを動かすか・root か symptom か・参照KB を書かせる。
#   ＝雑な分析のまま改善案を実装するのを物理ブロック。中身の質はまこさん30秒チェックが担保。
MISS_KW=""
for kw in "真因" "期待値" "symptom" "ベースアップ"; do
  grep -q "$kw" "$LIST" || MISS_KW="$MISS_KW $kw"
done
if [ -n "$MISS_KW" ]; then
  echo "🔒 [深い分析ゲート] $LIST に深掘り4点の見出しがありません（不足:$MISS_KW）。改善案の前に必須:" >&2
  echo "   ①真因(root cause・損/不足の構造的原因) ②期待値分解(勝率/平均利益/敗率/平均損失 のどれを動かすか)" >&2
  echo "   ③root を直すか symptom か(Y/N+理由・symptom 患い＝最易パッチを防ぐ) ④ベースアップ(参照した KB/検索の証跡・記憶ベース禁止)" >&2
  exit 2
fi

# 5.6) 疑似シミュ由来の固定値ゼロ宣言の必須化（まこさん承認 2026-06-26）
#   probe(疑似シミュ・静的後処理)で出た特定の数値を設計の固定値/閾値/段数に焼き込むのを物理ブロック。
#   背景: 2026-06-26 add ゲート設計で probe の θ≤0.4 / 段数3 / AUC0.83 を「クリア」扱いし acceptance に固定値で焼き込み
#   →まこさん指摘（疑似シミュは あたり付け専用＝決定的根拠でない）。設計の各閾値/段数の出所を1つずつ書かせる。
#   正直な限界: hook は「宣言が在るか」までを機械強制。中身が本当に probe 値を焼いていないかはまこさんの目＋番人。
if ! grep -qE "疑似シミュ由来の固定値ゼロ|固定値ゼロ宣言" "$LIST"; then
  echo "🔒 [疑似シミュ固定値ゼロゲート] $LIST に『★疑似シミュ由来の固定値ゼロ宣言』の見出しがありません（まこさん承認 2026-06-26）。" >&2
  echo "   probe(疑似シミュ)は あたりを付ける専用＝決定的根拠でない。設計の閾値/段数/パラメータの出所を1つずつ明示してください:" >&2
  echo "   ・各値は probe で出した特定数値でなく、実エンジンの学習窓選定 or 分析の構造由来の a-priori か" >&2
  echo "   ・probe の数値（θ=X・段数=N・AUC=Y 等）を設計の固定値に焼いていないか" >&2
  echo "   ・採否は probe でなく実エンジン両窓 score.py の数字で決めると明記しているか" >&2
  exit 2
fi

# 5.7) crude(疑似シミュ)を承認材料にするなら メリット・デメリットをセットで（まこさん承認 2026-07-14「不正をしたという記録をしろ・対策の hook 化」）
#   背景: E37 v24 で crude が「resting maker 利確を足した分 +$724」という良い数字だけを承認材料にし、
#   「STOCH_REVERSE を廃止して届かない玉が TIME/RANGE_BREAK で被る損」という失う分を隠した楽観値を提示
#   →実エンジン net −$477＝v23 −$420 から悪化。crude で「足す分」だけ見て「失う分」を見ない＝良く見せる不正。
#   v21 も同型（入口フィルタで TREND_CONT 出血 +$1,980 圧縮を出したが PARTIAL_TP −$1,724 巻き込みを隠した）。
#   ＝置換に限らず汎用: crude/probe 由来の改善数字を acceptance の承認材料に書くなら、必ずセットで
#   「この変更で失う分（副作用・巻き込み・廃止する枝の損）の試算」を書く。片方（メリットだけ）は承認材料にできない。
#   正直な限界: キーワード検出＝デメリット語を形だけ書けばすり抜ける。中身の妥当性は実エンジン両窓 score.py＋まこさんの目。
# 精密化（2026-07-14 番人でケースC 誤ブロック検出→是正）: 「crude の語が在るだけ」で発火しない＝
#   crude系の語と 改善の数字（対現状／+$金額）が【同じ行に一緒に】出る時だけ＝crude を改善数字の出所として承認材料にした行のみ拾う。
#   grep は行単位＝`.*` は改行を跨がない。「crude は使わない」等の言及だけの行（数字なし）は素通り。
HAS_CRUDE_MERIT=$(grep -qE '(crude|あたり付け|疑似シミュ).*(対現状|\+\$[0-9])|(対現状|\+\$[0-9]).*(crude|あたり付け|疑似シミュ)' "$LIST" && echo 1)
if [ "$HAS_CRUDE_MERIT" = "1" ]; then
  if ! grep -qE 'デメリット|失う分|副作用|巻き込み|反対側.{0,6}試算' "$LIST"; then
    echo "🔒 [crude はメリット・デメリットのセット ゲート] $LIST は crude/probe の改善数字（メリット）を承認材料にしていますが、対になる『この変更で失う分（デメリット）の試算』がありません（まこさん承認 2026-07-14・E37 v24 の +\$724 不正の再発防止）。" >&2
    echo "   crude で『足す分（メリット）』だけを承認材料にするのは不正。必ずセットで書いてください:" >&2
    echo "   ・メリット＝この変更で足す/稼ぐ分の crude 試算（既に有り）" >&2
    echo "   ・デメリット＝この変更で失う分の crude 試算＝副作用/巻き込み（フィルタで減る玉の稼ぎ）や、" >&2
    echo "     廃止・置換する枝が今まで実CSVで出していた損益と、その玉が廃止後どの exit_reason へ流れ何を被るか" >&2
    echo "   ・crude の対現状改善は『メリット − デメリット』の差引で出す（片方だけを承認材料にしない）" >&2
    echo "   ・採否は crude でなく実エンジン両窓 score.py で決めると明記" >&2
    exit 2
  fi
fi

# 6) 承認(内容指紋一致)確認
if [ ! -f "$APPROVED" ]; then
  echo "🔒 [受け入れ条件ゲート] 未承認です。リストを提示し、まこさんに『bash .claude/hooks/approve_impl.sh』を実行してもらってください。" >&2
  echo "$GUIDE" >&2
  exit 2
fi
CUR=$(shasum -a 256 "$LIST" | awk '{print $1}')
OKD=$(cat "$APPROVED" 2>/dev/null)
if [ "$CUR" != "$OKD" ]; then
  echo "🔒 [受け入れ条件ゲート] リストが承認後に変更されています(内容指紋が不一致)。再承認が必要: bash .claude/hooks/approve_impl.sh" >&2
  exit 2
fi
exit 0
