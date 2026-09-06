# 設計書｜ToDo ゲートの状態ファイル3つを、セッションごとの置き場に分ける（2セッションの並走で互いを止めない）

TARGET: .claude/hooks/enforce_todo_declaration.py, .claude/hooks/reset_read_log.sh, .claude/breaks/b27_todo_per_session.sh, .claude/breaks/b28_todo_no_session_stops.sh

NEW_FILE: .claude/breaks/b27_todo_per_session.sh, .claude/breaks/b28_todo_no_session_stops.sh

MODEL: .claude/breaks/lib.sh, .claude/breaks/b12_no_record.sh

REQUIREMENTS: R17（CC が要件どおりに作っているかを、プログラムが確かめられるようにする）＝並走する2つのセッションが、互いの検査（ToDo ゲート）を壊さないようにする。

BASEUP_EXEMPT（この設計は hook の置き場の直しで、売買の net に関わらない＝クオンツ文献のベースアップの対象外・2026-06-22 の除外の決まり）

**承認の状態＝未承認。往復：1回目／上限1回／net に直結するか：しない。**

<!-- ARC order=1 iter="todo-gate-per-session-20260906" 前提="2026-09-05〜06 に2つのセッションを並走させた。ToDo ゲートの状態ファイル（session_todo.md・session_todo_posted・session_todo_shown）が .claude/state に1組しか無く、片方が ToDo を書くと もう片方の hook が止まった（実測＝85回目の worklog 20260904 §37（3）・§39）" 採否="未定" 狙い="状態ファイルをセッションごとの置き場（.claude/state/sessions/<セッションの id>/）に分け、SessionStart は自分のセッションの分だけを消す＝並走しても互いを止めない" 内容="enforce_todo_declaration.py（置き場の解決・入口の例外・止めたときの案内・--check の口・番人4件）＋reset_read_log.sh（自分のセッションの置き場を作り、自分の分だけ消し、置き場を画面に出す）＋壊すプログラム2本（b27・b28）" 方法="--selftest の番人 N13〜N16 と、壊すプログラム b27・b28 の終了コード。完成の判定は監査（恒久の決まり64番）" -->

---

## 0｜まこさんの決定（逐語・2026-09-06）

| # | 逐語 | この設計のどこに効くか |
|---|---|---|
| 1 | 「今後は並走するのでToDo ゲートの状態ファイルをセッションごとに分ける直しをやってほしい」 | この設計書そのもの（§3） |
| 2 | 「承認を求めるときは、冒頭に必ず次の2行を書いてください。往復：N回目／上限1回／net に直結するか：する／しない。net に直結しない工事は、承認1回で閉じなければ打ち切って本線に戻ります。条件は承認を求める前に全部 出すこと。後から足さないこと。」（2026-09-05） | 冒頭の2行・§12（条件を先に全部 出す） |

**★この設計書では、私は「直った」「効いている」を1件も判定しません**（恒久の決まり64番・§0-3）。壊すプログラムの終了コードと、--selftest の件数と、監査が判定します。

---

## 1｜いまの状態（実物・Read tool で開いた行）

| # | 何 | 実物の場所 | いま何が起きるか |
|---|---|---|---|
| 1 | 状態ファイル3つの置き場が1組 | `.claude/hooks/enforce_todo_declaration.py` 53〜55行＝`TODO`・`MARK`・`SHOWN` が `.claude/state/` の固定の3ファイル | 2つのセッションが同じ3ファイルを読み書きする |
| 2 | SessionStart が印と表示の記録を消す | `.claude/hooks/reset_read_log.sh` 16〜17行＝`rm -f session_todo_posted`・`session_todo_shown` | 新しいセッションを開くと、動いている別のセッションの印が消え、そのセッションは次の操作で止まる |
| 3 | 入口の例外 | 同 .py 399行＝`if fpath in (TODO, MARK) or "session_todo" in cmd: sys.exit(0)` | ToDo のファイルと印だけは書ける（固定の置き場） |
| 4 | 止めたときの案内 | 同 .py 330〜352行 `fail()`＝全文と shasum のコマンドを固定の置き場で出す | 別のセッションの ToDo が画面に出る（85回目の実測） |
| 5 | 書く前に確かめる口 | 同 .py 361〜379行 `cli_check()`＝固定の置き場を読む | どのセッションの ToDo を見ているかが決まらない |
| 6 | 会話の記録の読み方 | 同 .py 63〜88行 `chat_texts(transcript)`＝hook の入力の `transcript_path` が在ればそれを読む。無ければ いちばん新しい jsonl | ★ここは既にセッションごと（入力の transcript_path を使う）。直さない |
| 7 | 並走の実測 | worklog 20260904 §37（3）・§39（1）＝私のセッション開始で別セッションの印が消えた。私の ToDo の書き込みで別セッションが止まった。逆も起きた | 並走のたびに、どちらかが1回以上 止まる |
| 8 | ほかで名前を使っている所 | `.claude/hooks/enforce_chat_writing.py` 241行＝`SKIP_FILES` にファイル名だけ（置き場は見ない）／`.claude/hooks/enforce_purpose_gate.py` 486行・`.claude/hooks/forbid_interpretation_file.py` 109行＝番人の見本の文字列だけ | 置き場を変えても、この3本は直さなくてよい（ファイル名は変えないため） |

**実測のコマンド（この設計書を書く前に打った）**＝`grep -ln "session_todo" .claude/hooks/*.sh .claude/hooks/*.py .claude/tools/*.py` → 5本（reset_read_log.sh・enforce_chat_writing.py・forbid_interpretation_file.py・enforce_purpose_gate.py・enforce_todo_declaration.py）。`grep -ln "session_id" .claude/hooks/*.py` → 0本（いまは どの hook もセッションの id を使っていない）。

---

## 2｜深掘り4点

### ① 真因（root cause）

**状態ファイルの置き場が「リポジトリに1組」で、セッションという単位を持っていないこと。**hook は毎回の入力でセッションを区別できる（`transcript_path`・`session_id`）のに、書く先・読む先・消す先が全部 固定のパスになっている。

### ② 期待値分解

**この設計書は売買のコードを1行も変えない。**勝率・平均利益・敗率・平均損失は1つも動かない。動くのは「並走したときに片方の hook が もう片方を止める回数」だけ（85回目の実測＝1セッションで私が別セッションを2回 止め、別セッションが私を1回 止めた）。

### ③ root か symptom か

**root。**symptom の直し方＝「並走しない」「書く順番を人が決める」「印が消えたら貼り直す」。どれも人の運用で、まこさんが並走すると決めた以上 毎回 起きる。root＝置き場をセッションごとに分け、SessionStart が自分の分だけを消す。

### ④ ベースアップ（このセッションで Read tool を使って開いたもの）

| 何を確かめたか | 出どころ |
|---|---|
| 状態ファイルの定数・入口の例外・止めたときの案内・--check の口・番人の作り | .claude/hooks/enforce_todo_declaration.py（1〜60行・440〜600行） |
| SessionStart が消すもの・画面に出す文 | .claude/hooks/reset_read_log.sh（全文） |
| 目的ゲートが session_todo の名前を使う所（番人の見本だけ） | .claude/hooks/enforce_purpose_gate.py（470〜500行） |
| チャットの検査が session_todo の名前を使う所（ファイル名だけ） | .claude/hooks/enforce_chat_writing.py（236〜247行） |
| 解釈ファイルの門が session_todo の名前を使う所（番人の見本だけ） | .claude/hooks/forbid_interpretation_file.py（100〜113行） |
| 壊すプログラムの共通の部品と見本 | .claude/breaks/lib.sh・.claude/breaks/b12_no_record.sh（全文） |
| 設計書を書く瞬間の必読2本 | v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/cat_requirements.md（1〜30行）・exchange_spec.md（1〜20行） |
| 起点と台帳と恒久の決まり | .claude/state/next_step.md・.claude/ratchet/adopted_strategies.md・.claude/rules/permanent_rules.md |

**★WebSearch は使っていません。**うちの hook の置き場の話で、外の文献は要らないためです。

---

## 3｜何を作るか

### 3.1 `.claude/hooks/enforce_todo_declaration.py`

| 何を | どう変えるか |
|---|---|
| 置き場の解決（新設 `session_id_of(data)`） | hook の入力（stdin の json）から `session_id` を読む。無ければ `transcript_path` のファイル名（`.jsonl` を除いた部分）。どちらも無ければ `None` |
| 置き場（新設 `paths_of(sid)`） | `.claude/state/sessions/<sid>/session_todo.md`・`session_todo_posted`・`session_todo_shown` の3つを返す。置き場のディレクトリが無ければ作る |
| `hook_main()` | 先に `sid = session_id_of(data)`。`None` なら **止める**＝「セッションの id が hook の入力に無い（session_id も transcript_path も無い）＝fail-closed」。入口の例外＝`fpath` が自分のセッションの ToDo か印のとき、または `"session_todo" in cmd`（いままでどおり）。検査は自分のセッションの3ファイルで行う |
| `check(transcript, sid)`・`read_shown_body(sid)` | 固定の定数の代わりに `paths_of(sid)` を読む。判定の中身（4行の型・表・★いまここ・✅済 の §NN・貼ったか・印）は1文字も変えない |
| `fail(reason, sid)` | 全文と shasum のコマンドを、**自分のセッションの置き場**で出す。1行目に「このセッションの ToDo の置き場＝…」を足す |
| `cli_check()`（`--check`） | `--session <sid>` を受ける。無ければ `.claude/state/sessions/*/session_todo.md` のうち いちばん新しく書かれたものを見て、**どの置き場を見たかを1行目に出す** |
| 番人（`--selftest`） | 既存 N1〜N12 はそのまま（一時の置き場を1つ作って走らせる）。新しく N13〜N16（§3.4） |
| 触らない所 | `body_problems`・`todo_rows`・`worklog_sections`・`chat_texts`・`pasted_in_chat`・`changed_lines`・`heads_in_chat`・`PASS_FLAGS`＝1文字も変えない |

### 3.2 `.claude/hooks/reset_read_log.sh`（SessionStart）

| 何を | どう変えるか |
|---|---|
| 16〜17行（固定の置き場の印と表示の記録を消す） | 消すのをやめる。代わりに **stdin の json から `session_id`（無ければ `transcript_path` の名前）を読み**、`.claude/state/sessions/<sid>/` を作り、**その中の** `session_todo_posted` と `session_todo_shown` だけを消す。stdin の読み方は、ほかの hook と同じヒアドキュメント（`'PYEOF'` の引用符つき）の python |
| 画面に出す文 | 「=== [ToDo ゲート] このセッションの ToDo の置き場＝.claude/state/sessions/<sid>/session_todo.md ===」を1行 足す＝CC が自分の置き場を知る道 |
| id が読めないとき | 置き場を作らず「⚠️ セッションの id が読めない＝ToDo ゲートは最初の操作で止まる（fail-closed）」と出す |
| 8行（`read_log.txt` を空にする） | **変えない**（同じ型の衝突だが、この設計の1変更の外＝§9 の R） |

### 3.3 壊すプログラム（新設2本・`.claude/breaks/`・手本＝lib.sh と b12）

| # | 何を測るか | 終了コードの決め方 |
|---|---|---|
| b27_todo_per_session.sh | セッション A の置き場に正しい ToDo・印・表示の記録を作る。①A の入力（`session_id`=A・Write・別のファイル）で hook を呼ぶ → 0 ②同じ ToDo が無いセッション B の入力で呼ぶ → 2 ③B の置き場に別の ToDo と印を作って B で呼ぶ → 0、そのあと A で呼んでも 0（互いに影響しない） | ①②③が全部 期待どおりのときだけ 1。作った置き場は必ず消す |
| b28_todo_no_session_stops.sh | `session_id` も `transcript_path` も無い入力で hook を呼ぶ | 終了コードが 2 で、stderr に「セッションの id」が在れば 1 |

### 3.4 番人（`--selftest` に足す・4件）

| # | 何を試すか | 期待 |
|---|---|---|
| N13 | 2つの sid（A・B）。A に正しい ToDo・印・表示の記録。`check(transcript, sid="B")` | 止まる（B の置き場に ToDo が無い） |
| N14 | `session_id_of({})`／`session_id_of({"transcript_path": "/x/abc.jsonl"})` | `None`／`"abc"` |
| N15 | 固定の置き場（`.claude/state/session_todo.md`）にだけ ToDo が在り、自分の置き場に無い | 止まる。理由の文に自分の置き場のパスが在る |
| N16 | `--check --session A` と `--check`（省略・A が最新） | どちらも A の置き場を見て、1行目にそのパスを出す |

### 3.5 触らないもの

- `enforce_chat_writing.py`（`SKIP_FILES` はファイル名だけ＝置き場が変わっても当たる）・`enforce_purpose_gate.py`（番人の見本の文字列だけ）・`forbid_interpretation_file.py`（同）。
- `read_log.txt` を SessionStart が空にする行（§9 の R）。`next_step.md` の (0-b-2) の印（§9 の S）。
- `.claude/settings.json`＝登録は変えない（同じ2本を同じ場所で呼ぶ）。
- 売買のコード・法則の正本・成績表・審判。

---

## 3-2｜★疑似シミュ由来の固定値ゼロ

- **疑似シミュ（probe）を1回も使っていません。**この設計書に出てくる数字は、実物の行番号と、番人の件数（いま 24件・足して 28件）と、85回目の実測の回数だけです。
- **閾値・段数・確率の数字を1つも作っていません。**足す判定は「セッションの id が在るか」「自分の置き場に在るか」の2値です。
- **採否は score.py の数字で決めます。**ただしこの工程は hook の置き場の直しで、売買の採否は M2-L 以降です。

---

## 4｜★§1.4.6.4 の形式（検査ごとに「止める／出すだけ」と「止まらないとき何が通るか」）

> **§1.4.6.4 「止める」と「出す」を分けて宣言する義務**（監査 cp20 §7 の逐語）＝強制の仕組みを新設・改訂するとき、各検査について ①止める検査か、出すだけの検査か ②止まらないとき何が通ってしまうか、を1行ずつ書く。

| # | どこ | 検査 | 止める／出すだけ | 通ってしまうもの（fail-open の内容） | この設計で変わるか |
|---|---|---|---|---|---|
| 1 | enforce_todo_declaration.py hook_main | セッションの id が入力に無い | **止める（exit 2）** | （止める側にするので無し） | **★新設。**直す前＝id を見ていない＝固定の置き場を読んだ |
| 2 | 同 | 自分の置き場に ToDo が無い | 止める（exit 2） | — | 変えない（置き場だけ自分のセッションへ） |
| 3 | 同 | 4行の型・表・★いまここ・✅済 の §NN | 止める（exit 2） | — | 変えない |
| 4 | 同 | 貼ったか（会話の記録・表示の記録・変わった行） | 止める（exit 2） | — | 変えない。会話の記録は入力の `transcript_path`（既にセッションごと） |
| 5 | 同 | 印（shasum）が一致しない | 止める（exit 2） | — | 変えない（置き場だけ自分のセッションへ） |
| 6 | 同 | 入口の例外（自分の ToDo と印への書き込み・`session_todo` を含む Bash） | 通す（exit 0） | 自分の ToDo と印は検査なしに書ける（いままでと同じ） | 置き場を自分のセッションに限る＝**別のセッションの ToDo を書く道は例外から外れる**（止まる側へ） |
| 7 | 同 `--check` | どの置き場を見たか | 出すだけ（1行目に印字） | `--session` を省くと、いちばん新しい置き場を見る＝並走中に別のセッションの ToDo を見る可能性 | ★新設（§9 の K） |
| 8 | reset_read_log.sh | セッションの id が読めない | 出すだけ（⚠️ を印字） | SessionStart は止められない（Claude Code の作り）。ただし最初の操作で 1 が止める | ★新設 |
| 9 | reset_read_log.sh | 自分の置き場の印と表示の記録を消す | 出すだけ（処理） | 別のセッションの印は消さない＝**直す前は消していた**（並走の止まりの原因） | **★変える** |

**★「出すだけ」の 7・8 を「担保」「守っている」とは書きません。**

---

## 5｜わざと壊して止まるか試すテスト（標準出力をそのまま貼る・私は「通った」と文章で書かない）

| # | 何を試すか | 期待する結果 | 誰が走らせるか |
|---|---|---|---|
| 1 | `python3 .claude/hooks/enforce_todo_declaration.py --selftest` | N13〜N16 が ✅・件数 28件（いま 24件＋4） | 私（実装の直後・出力を貼る） |
| 2 | 1 のあと、`hook_main` の「id が無ければ止める」の分岐を一時的に外して `--selftest` | N14 か N15 が ❌ になる。戻して 28件 ✅ | 私（外した行は必ず戻す・`git diff` が実装分だけになることを貼る） |
| 3 | `bash .claude/breaks/b27_todo_per_session.sh; echo rc=$?` | rc=1（§3.3 の①②③が全部 期待どおり） | 承認スクリプト（run_breaks.py）。私も承認の前に1回 走らせて出力を貼る |
| 4 | `bash .claude/breaks/b28_todo_no_session_stops.sh; echo rc=$?` | rc=1 | 同上 |
| 5 | `bash .claude/hooks/hook_health_check.sh` | ✅（登録・構文・エラーログ・合言葉0件） | 私（出力を貼る） |
| 6 | `grep -c "_OK=1" .claude/hooks/enforce_todo_declaration.py .claude/hooks/reset_read_log.sh` | 0・0 | 私（出力を貼る） |
| 7 | 並走の実走＝別のセッションを1つ開き、両方で ToDo を書いて印を作り、両方で Edit を1回ずつ行う | どちらも相手に止められない。SessionStart の画面に置き場のパスが出る | 私と まこさん（別のセッションを開くのは まこさん） |

**★壊すプログラムは承認の後にしか書けない**（書き込みの門が `.claude/breaks/*.sh` を止める＝G-2）。だから承認は2回 要ります＝①この設計書の承認（壊すプログラム2本は「MISSING」と記録される）②実装と壊すプログラムを書いたあとの再承認（凍結に2本が入り、走って終了コードが記録される）。**②は設計の変更ではなく、機械の記録のためです。**まこさんの決まり（承認1回）に照らして、この②を「1回」の中に含めるかは、まこさんが決めてください（§12）。

---

## 6｜何ができたら完成か

<!-- ACCEPT_TABLE_START -->

**★「経路」＝`実経路`（hook をその入力で呼んだ）か `部品`（関数を直接 呼んだ）。**
**★「壊すプログラム」＝承認スクリプトが走らせ、終了コードを控えに残す（0 以外のときだけ「済」の印を書ける）。私は「済」の印を書かない＝判定は監査（恒久の決まり64番）。**

| # | 完成の条件 | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|
| 1 | セッション A の ToDo と印が在っても、セッション B の入力では止まる。B が自分の置き場に ToDo と印を作れば B は通り、A も通ったまま（AUDIT-1） | 実経路 | §5 の3（B の置き場を空にして呼ぶ） | b27_todo_per_session.sh | 対象 | **未着手** |
| 2 | セッションの id が入力に無いと止まり、理由の文に「セッションの id」が在る | 実経路 | §5 の4（id の欄を消した入力で呼ぶ） | b28_todo_no_session_stops.sh | — | **未着手** |
| 3 | 止めたときの案内が、自分のセッションの置き場のパスを出す（固定の置き場は出さない） | 実経路 | §5 の3 の②の stderr を見る | b27_todo_per_session.sh | — | **未着手** |
| 4 | 番人 N13〜N16 が ✅・id の分岐を外すと N14 か N15 が ❌ | 実経路 | §5 の2（分岐を一時的に外す） | — | — | **未着手** |
| 5 | SessionStart が自分の置き場だけを作り、その中の印と表示の記録だけを消す。別の置き場は触らない | 実経路 | 2つの置き場に印を置き、片方の id で SessionStart を呼ぶ → 片方だけ消える | b27_todo_per_session.sh | — | **未着手** |
| 6 | 合言葉（`_OK=1`）の通し道が 0件・hook の健全性の検査が ✅ | 実経路 | §5 の5・6 | — | — | **未着手** |
| 7 | 並走の実走で、どちらのセッションも相手に止められない（AUDIT-2） | 実経路 | §5 の7 | — | 対象 | **未着手** |

<!-- ACCEPT_TABLE_END -->

**★「完成」の判定は私がしません**（恒久の決まり64番）。終了コードと標準出力をそのまま貼るだけです。

---

## 7｜既存を壊さないこと（副作用）

| 何が | どうなるか |
|---|---|
| いま `.claude/state/` に在る固定の3ファイル | hook は読まなくなる。消さない（記録として残る）。次の SessionStart からは各セッションの置き場に書く |
| いま動いているセッション（このセッション） | 実装の直後の最初の操作で1回 止まる（自分の置き場に ToDo が無い）。案内のパスに ToDo を書き直し、印を作る＝1回だけ |
| 別のセッション（止まっている） | 再開したときに同じ＝1回 止まって、自分の置き場に書く |
| `enforce_chat_writing.py` の `SKIP_FILES` | ファイル名で見ているので、置き場が変わっても同じに働く（241行） |
| `hook_health_check.sh` | 登録・構文・合言葉の検査は変わらない |
| H2・G2 の印 | 取り直し不要（探索の道具の経路のコードに触れない。この2本の hook は印の一覧に無い） |
| 番人の件数 | 24件 → 28件 |
| **★この設計書が在る間の `--check`・`--selftest`** | **実測（2026-09-06）**＝この設計書の `impl_file` が `enforce_todo_declaration.py` なので、その .py を python で走らせる操作は、実装が設計書と一致するまで `require_design_contract_before_run` に止められる（FAIL 10件＋承認外れ）。＝**承認と実装が終わるまで、私は ToDo の `--check` を打てない**（hook そのものは Claude Code が呼ぶので止まらない）。§0-4 の1番（書いたら `--check`）は、この間は守れない＝止められてから直す形に戻る |

---

## 8｜照合（群2＝まとめて非該当の1行）

**H1〜H16 と審判整合（群2の18件）は、まとめて非該当です。**理由＝売買のコードを1行も変えず、売買記録を1本も書かず、`score.py` と `eval_engine.py` に1行も触れないためです。

**★1変更か（H16）**＝「ToDo ゲートの状態ファイルの置き場をセッションごとにする」の1つです。hook 2本と壊すプログラム2本は、その1つを作って測るものです。同じ型の衝突がほかに2つ在りますが（§9 の R・S）、この設計には入れません。

**★過去に破棄した失敗の再演か**＝当たりません。2026-08-16 に「印だけ先に作るすり抜け」を塞ぎ、2026-08-27 に「変わった行だけで通す」を足しました。今回は判定を1つも変えず、置き場だけを分けます。

---

## 9｜★正直に書く｜それでも塞げないもの

**塞げないもの（この設計の範囲で残る穴）**

| # | 塞げないもの | なぜ塞げないか | 何が代わりに守るか |
|---|---|---|---|
| I | **セッションの id は hook の入力から読むだけ**＝Claude Code が入力に何を入れるかは、うちのコードでは決められない | hook の入力の欄は Claude Code の側の作り | id が無ければ止まる（fail-closed・§4 の1）。実装の直後に実物の入力で1回 確かめ、出力を貼る |
| J | **別のセッションの置き場に ToDo と印を書く道**＝パスを知っていれば Write できる（入口の例外は自分の置き場だけだが、Write そのものは別の門が見る） | 置き場のパスは画面に出るので隠せない | 書いても自分のセッションの検査には効かない（自分の置き場しか読まない）＝相手を通す手にはなるが、自分を通す手にはならない。最後の関所は まこさんの目 |
| K | **`--check` で `--session` を省くと、いちばん新しい置き場を見る**＝並走中は別のセッションの ToDo を見ることがある | 口（`--check`）は stdin の json を受け取らない | 1行目に見た置き場のパスを出す（§4 の7）。SessionStart が自分の置き場を画面に出すので、`--session` を付けられる |
| L | **`.claude/state/sessions/` に置き場が溜まる** | 消す条件（いつ・どれを）を決めるのは この設計の外 | 記録して次に出す（next_step §6） |
| M | **承認が2回 要る**（§5 の末尾）＝壊すプログラム2本は承認の後にしか書けない | 書き込みの門が `.claude/breaks/*.sh` を止める（G-2） | 2回目は機械の記録のため。含めるかは まこさんが決める（§12） |
| Q | **表示の記録（session_todo_shown）を CC が自分で作る道** | いままでと同じ限界（hook のファイルを書き換えるのと同じ明示の違反） | 最後の関所は まこさんの目 |
| R | **同じ型の衝突＝`read_log.txt` を SessionStart が空にする**（8行）＝新しいセッションを開くと、動いている別のセッションの必読の記録が消える | この設計の1変更の外（同じ hook の別の行・別の門 require_read_before_work が読む） | 記録して次に出す（next_step §6）。害＝別のセッションが必読3本を Read し直すまで止まる（1回） |
| S | **同じ型の衝突＝`next_step.md` の (0-b-2) の印**＝別のセッションが印を取り直すと、こちらの Stop hook が止まる | 印は1組しか無い（正しい作り＝コードは1つ） | 止まったら json の値を写す（85回目に2回 やった） |

**★強制の土台そのものの穴（監査 cp14 の Q5 の5件・cp19 で「閉じない部分」として確定＝`lessons_active.md` の L-586。この設計は1つも塞がない・受け入れ条件ゲートが毎回 書かせる）**

| # | 塞げないもの | この設計での扱い |
|---|---|---|
| D | **照合D が実経路で1度も走っていない**（監査 Q5 の1） | この設計書も `spec_lists` は空（理由は §10 の `no_spec_lists_reason`）＝照合D はこの回も走らない |
| E | **照合の道具と印を、私が書ける場所に置いたまま**（監査 Q5 の2） | 触らない。J-6（外部CI）は まこさん決定で着手しない（L-586） |
| F | **照合A・B の期待値が、実装から作られる**（監査 Q5 の3） | この回の `impl_functions` は「触る関数」を手で列挙したもの＝実装から作っていない（§10 の `generated_from`） |
| G | **語を並べて迂回を塞ぐやり方は、原理的に閉じない**（監査 Q5 の4） | 触らない。この設計は書き込みの門の語の一覧を1つも変えない |
| H | **承認の記録を全部 消したときを測っていない**（監査 Q5 の5） | 測らない（まこさんの一覧の外・cp19 で確定） |

---

## 10｜DESIGN_CONTRACT

**★`impl_functions` は「この回で触る関数」だけを列挙したものです（手書き・9件＝新設2件＋直す7件）。**理由＝照合A（触った関数 ⊆ impl_functions）と照合B（impl_functions ⊆ 触った関数）の定義に合わせるため。

```json
{
  "impl_file": ".claude/hooks/enforce_todo_declaration.py",
  "impl_functions": {
    ".claude/hooks/enforce_todo_declaration.py": [
      "<モジュール直下>",
      "session_id_of",
      "paths_of",
      "read_shown_body",
      "check",
      "fail",
      "cli_check",
      "hook_main",
      "selftest"
    ]
  },
  "self_check_calls": [
    "session_id_of",
    "paths_of",
    "セッションの id",
    "sessions"
  ],
  "must_use": {
    "hook_main": ["session_id_of", "paths_of"],
    "check": ["paths_of"],
    "fail": ["paths_of"],
    "cli_check": ["paths_of"],
    "selftest": ["session_id_of", "paths_of"]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この設計書は hook の状態ファイルの置き場を直すもの。照合D の相手になる正本の配列（機械が読む一覧）は存在しない。",
  "generated_from": {
    "impl_functions": "手書き＝この回で触る関数9件（<モジュール直下>＝定数3つを関数に替える／session_id_of・paths_of＝新設／read_shown_body・check・fail・cli_check・hook_main＝置き場を自分のセッションへ／selftest＝N13〜N16）。実物の全関数の写しではない",
    "must_use": "手書き＝§3.1 の設計から（入口・検査・案内・口・番人が置き場の解決を通る）",
    "self_check_calls": "手書き＝新設の関数名2つ・止めるときの文の一部・置き場のディレクトリ名（4つとも実装の後に文字として在るはずのもの）",
    "spec_lists": "無し（理由は no_spec_lists_reason）"
  }
}
```

---

## 11｜SPEC（★`verify_design_contract.py --write .claude/state/acceptance.md` が 2026-09-06 に hook の実物から書き出したもの＝公開する関数 14件・定数 4件・旗 2件。手で足したのは今回 新設する2件（`session_id_of`・`paths_of`）と、その2件を呼ぶ側の6か所だけ。★契約の節（§10）の後ろに置く）

**手で足した所（実物にはまだ無い＝承認の前に打った `--diff .claude/state/acceptance.md` は「齟齬: 10件」＝新設の2件と、その2件を呼ぶ8か所。10件とも `session_id_of` か `paths_of` を指す。実装の後に 0件 になる）**

| どこ | 何を足したか |
|---|---|
| `public_functions` | `session_id_of: []`・`paths_of: []`（新設） |
| `read_shown_body`・`check`・`fail`・`cli_check` | 呼ぶ名前に `paths_of` |
| `hook_main`・`selftest` | 呼ぶ名前に `session_id_of`・`paths_of` |
| `constants`・`cli_flags` | 変えていない（`--check --session` は `--check` の下の引数＝新しい旗ではない） |

SPEC

```json
{
 "impl_file": ".claude/hooks/enforce_todo_declaration.py",
 "public_functions": {
  "session_id_of": [],
  "paths_of": [],
  "chat_texts": [],
  "pasted_in_chat": [
   "chat_texts"
  ],
  "changed_lines": [],
  "heads_in_chat": [
   "chat_texts"
  ],
  "read_shown_body": [
   "paths_of",
   "read"
  ],
  "read": [],
  "todo_rows": [],
  "worklog_sections": [
   "read"
  ],
  "body_problems": [
   "todo_rows",
   "worklog_sections"
  ],
  "check": [
   "body_problems",
   "changed_lines",
   "chat_texts",
   "heads_in_chat",
   "pasted_in_chat",
   "paths_of",
   "read",
   "read_shown_body"
  ],
  "fail": [
   "paths_of",
   "read"
  ],
  "cli_check": [
   "body_problems",
   "paths_of",
   "read"
  ],
  "hook_main": [
   "check",
   "fail",
   "paths_of",
   "session_id_of"
  ],
  "selftest": [
   "body_problems",
   "check",
   "paths_of",
   "read",
   "session_id_of"
  ]
 },
 "constants": {
  "ROOT": "/Users/tachiharamasako/Documents/GitHub/cat-bitget",
  "PASS_FLAGS": "--selftest|py_compile|--help|--verify|--check",
  "STALE": "前のセッションの ToDo を持ち越すと止まる（SessionStart で印と表示の記録が消えるため）",
  "NOSHOW": "★チャットに貼らずに印だけ先に作っても止まる（2026-08-16 の穴ふさぎ）"
 },
 "cli_flags": [
  "--check",
  "--selftest"
 ]
}
```

---

## 12｜まこさんにお願いすること（条件は先に全部 出す）

**往復：1回目／上限1回／net に直結するか：しない。**

1. **承認**＝`bash .claude/hooks/approve_design.sh .claude/state/acceptance.md` と `bash .claude/hooks/approve_impl.sh`（2本とも `.claude/hooks/` に在る＝`ls .claude/hooks/approve_*.sh` で実測）。承認スクリプトは壊すプログラム2本を「MISSING」と記録します（承認の後に書くため）。
2. **決めてほしいこと1つ**＝壊すプログラム2本の凍結と走行のための**再承認（2回目）**を、「承認1回」の決まりの中に含めてよいか。含めないなら、壊すプログラム2本を設計から外し、確かめは §5 の1・2・5〜7（--selftest と実走）だけにします（その場合、完成の条件の1・2・3・5 は E-12 の決まりで「済」にできなくなります＝監査は --selftest の出力で判定することになります）。
3. 実装のあと、§5 の1〜6 の出力を貼ります。§5 の7（並走の実走）は、まこさんが別のセッションを1つ開いてくださったときに行います。
