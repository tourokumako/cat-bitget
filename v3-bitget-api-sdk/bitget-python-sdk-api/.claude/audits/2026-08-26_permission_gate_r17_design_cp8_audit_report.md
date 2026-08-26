# 【監査結果】許可制（要件定義に在るものだけを作れるようにする・R17）の設計の監査（cp8・実装前）

- 監査日: 2026-08-26
- 監査区分: cp8（設計だけの監査・実装前。実装は1行も入っていない）
- 監査対象: `.claude/state/acceptance.md`（304行・未承認）
- 依頼書: `.claude/audits/inputs/2026-08-26_permission_gate_r17_design_cp8_audit_request.md`（254行）
- 実施の形: auditor セッションの CC が Plan サブエージェントを cold start で起動し、Plan agent が依頼書と着手前必読5件を独立に Read して監査（cc_role §1.4.5 改善9・同型バイアス回避）。メインセッションの CC への確認質問は行っていない。

---

## 1. Step -1 監査対象の型宣言

- **文書型＝設計書**（`.claude/state/acceptance.md`・304行）。**実装は1行も入っていない**（実物で確認＝`--diff` が「齟齬: 13件・すべて『設計にあるが実物に無い』側」＝設計側だけが先行）。
- **状態＝未承認**。ただし承認の記録ファイルには、1つ前の設計書のハッシュが残っている（Step 0 の S-1・S-2）。
- **本監査のスコープ**＝この設計が「要件定義に在るものだけを作れるようにする」を、抜け道なく・既存を壊さずに実現するか、だけ。net・戦略性能は対象外。
- 判定に使ったのは、依頼書・設計書・実物のコード・hook・要件 json・git の状態のみ。

---

## 2. Step 0 指摘前提確認（事実データ verify ＋ spec 文言 verify）

### 2.1 依頼書の表と実物の突き合わせ（`wc -l` ＋ `shasum -a 256` を実際に取得）

| ファイル | 依頼書の行数 | 実測 | 依頼書の sha256（先頭16桁） | 実測（先頭16桁） | 判定 |
|---|---|---|---|---|---|
| `.claude/state/acceptance.md` | 304 | **304** | 5cf1c70eacaebd69 | **5cf1c70eacaebd69** | 一致 |
| `scripts/priority_rebuild/verify_design_contract.py` | 772 | **772** | a9628b77cfa5a926 | **a9628b77cfa5a926** | 一致 |
| `.claude/ratchet/engine_tuner_requirements.json` | 438 | **438** | 030aa8b1ba051d8d | **030aa8b1ba051d8d** | 一致 |
| `.claude/hooks/approve_impl.sh` | 44 | **44** | 1d33a7da3e8404b9 | **1d33a7da3e8404b9** | 一致 |
| `.claude/hooks/approve_design.sh` | 54 | **54** | 05c51ed429684da0 | **05c51ed429684da0** | 一致 |
| `.claude/hooks/require_acceptance_before_impl.sh` | 169 | **169** | 22a0187ac6faf60c | **22a0187ac6faf60c** | 一致 |
| `.claude/hooks/require_design_contract_before_run.sh` | 177 | **177** | dd68f1ed88b700b9 | **dd68f1ed88b700b9** | 一致 |

**＝7件すべて一致。依頼書の事実データは機械の出力の複写である、という主張は裏が取れた。**

### 2.2 依頼書が載せた3つの出力の再現

- `--scan-contracts` → **読めた契約 4件（e35／e37／e38／acceptance）・読めない 0件・対象外 6件**。依頼書と完全一致。
- `--diff .claude/state/acceptance.md` → **齟齬 13件**。内訳も依頼書の13行と1文字違わず一致。
- 要件 json → **17件・完了10・作業中7・`accept` を持つもの17件**。`gen_engine_tuner_requirements.py --verify` は `✅ 改変なし（ハッシュ e8c5ee3c95d213ea）`。＝設計書 §1 の1行目・2行目・§9 の1行目は実物どおり。
- `--self-test 11/11` は**実走していない**＝**データ不足（理由：自己検査の T10 が本番の `design_approved.json` を読み書きするため、読み取り専用の監査では走らせられない）**。この副作用そのものが指摘の1件（Q3-6）。

### 2.3 ★Step 0 で発見した、依頼書に書かれていない現状

| # | 実測 | 意味（日本語1行） |
|---|---|---|
| S-1 | `.claude/state/design_approved.json` の中身＝`{"…/acceptance.md": "29ebcd26df1f3e1d…"}`／いまの acceptance.md は `5cf1c70e…` | いまの設計書は「承認が外れている」状態。未承認ではなく、承認の記録が古いまま残っている |
| S-2 | `.claude/state/acceptance.approved` ＝ `29ebcd26df1f3e1d…` | 実装の承認も1つ前のまま。いま実装に入ろうとすると止まる（正しい動き） |
| S-3 | `verify_design_contract.py --check-approval` を叩くと、**実際に「設計書の承認: 外れています（承認後に設計書が変わりました）」で止まった** | 止める所③はいま生きて動いている。設計書が「hook に足す」と言っている相手は稼働中 |
| S-4 | `git check-ignore -v .claude/state/acceptance.md` → **`.gitignore:45 .claude/state/*`** | **設計書そのものは git の管理外**。設計書を書き換えても `git diff` には出ない |
| S-5 | 1つ前の設計書（`acceptance_archive/unordered-scan-scope-20260826.md`）＝`"impl_file": "scripts/priority_rebuild/engine_tuner_exec.py"` | 上書きによって engine_tuner を指す契約が消えた、という §7 の1番は事実 |

---

## 3. 観点 ①〜⑦ ＋ Q1〜Q5 の所見

### 観点① 統計学的妥当性 — **PASS**

- §2 の「違反の記録22件のうち、自分で気づいて止まったのは1件（#18）」＝`false_positive_incident_policy.md` §3 の表を数えると **#1〜#22 の22行**、#18 の欄に「★自己申告した」、#22 の欄に「22件のうち、CC が自分で気づいて止まったのは #18 の1件だけ」。**再現できた。**
- §1 の 17件／10件／7件／`accept` 17件も再現。
- ただし **n=1 の自己検出率をもって「禁止の一覧では止まらない」と断ずるのは、標本が1件**。結論の向き（許可制を足す）は まこさん決定なので判定に影響しないが、「実測」と呼べる強さは §2 の2番（89件）・3番（78番）のほうが上。**数値の再現性は取れたので PASS。**

### 観点② リスク管理 — **FAIL**

**理由＝設計書 §10「限界（隠しません）」の5件に、いちばん大きい穴が2つ入っていない。**

1. **承認のコマンドを CC 自身が打てば通せる。**実物の hook が自分で認めている。`require_acceptance_before_impl.sh` の12〜14行目に逐語で「**正直な限界: 承認は approve_impl.sh の実行で立つ。CC がそれを勝手に実行すれば通せる**」、`approve_design.sh` の13〜14行目に「**・CC がこのコマンドを勝手に実行すれば通せる（受け入れ条件の承認 approve_impl.sh と同じ）**」。設計書 §3.4 は「止める所①＝承認」と書きながら、この既知の限界を §10 に写していない。
2. **`scripts/priority_rebuild/*.py` は Bash 経由なら書ける。**止める所②は `require_acceptance_before_impl.sh` の4行目に「**# require_acceptance_before_impl.sh — PreToolUse on Write|Edit**」＝**Write と Edit の道具にしか掛からない**。設定に登録された Bash 向けの hook 18本を全部 読んだが、`cat > file`・heredoc・`python3 -` での書き込みを止めるものは1本も無い。＝設計書 §6 の完成の条件2「`scripts/priority_rebuild/*.py` を1行も書けない」は、実物の作りでは成立しない。

日本語で1行：**「承認が要る」「1行も書けない」と設計書が言い切っている2つの入口は、どちらも CC 自身の手で開けられる。それが限界の一覧に書かれていない。**

### 観点③ 認知バイアス — **FAIL**

- §1 の4行目（L34）逐語＝「**| そのうち「どの要件のために作るか」を書いている設計書 | 0本 | `grep -rln "REQUIREMENTS:"` ＝出たのは履歴の2本…だけ |**」。
  **しかし同じ設計書の5行目は `REQUIREMENTS: R17`。**＝**自分が数えている4本のうちの1本（acceptance.md）に、探している目印が入っているのに「0本」と書いている。**
  原因も特定した。`.claude/state/*` は `.gitignore` の45行目で除外されており、この環境の `grep -rln` は除外を尊重するため、**リポジトリの根から数えると acceptance.md だけが黙って落ちる**（`.claude/` を直に指すと出る）。
- §3.5 の L105 逐語＝「**既存を壊さないためであって、範囲を私の都合で狭めたのではありません。**」＝**自己弁護を設計書の本文に書いている。**範囲が妥当かは Q5 で判定するが、「私の都合ではない」と自分で宣言することは監査の材料にならない。

日本語で1行：**自分の設計書を数え落とした「0本」と、範囲について自分で無罪を宣言した1文が入っている。**

### 観点④ ソフトウェア工学 — **FAIL**（4件）

1. **囲みの判定を2か所に作る設計になっている。**実物の `extract_block`（`verify_design_contract.py:97-111`）は ``` の内側を除く処理を既に持っているが、設計書 §11 の SPEC は `"extract_requirements": []`＝**何も呼ばない**＝同じ処理をもう1つ書くことになる。実物のコメント（同ファイル 232-235行目）が「**『どれが設計書か』を決める判定が2か所に在り、片方（この関数）だけ `.actual.md` を外していた**」と、**まさに同じ型の事故を記録している。**
2. **`hash=` の対象範囲が設計書に書かれていない**（Q2(b)）。
3. **hook のどこに足すかが書かれていない**（Q2(d)・Q4-5a）。
4. **自己検査が本番の状態ファイルを書き換える。**`self_test` の T10（`verify_design_contract.py:700-713`）は、本物の `.claude/state/design_approved.json` を読み、一時の項目を足して**書き戻し**、終わったら元に戻す。途中で落ちれば偽の承認記録が残る。設計書 §5 の★は「**本物のファイルを1バイトも変えません**」と書いているが、これは T12〜T18 についての宣言で、**既に在る T10 はこの宣言に反している**。設計書 §6 の9番はその T10 を含む T1〜T11 を合格の条件にしている。

### 観点⑤ 再現性 — **FAIL**

- §1 の3行目と4行目は**別の時刻に測られている**。3行目の「`acceptance.md -> verify_design_contract.py`」は**新しい**設計書（12:23:40 に上書き）を数えた結果、4行目の「0本」は**上書きの前**の状態でしか成り立たない。同じ「2026-08-26 に、このセッションでプログラムを走らせて数えた」という見出しの下に、両立しない2つの時点が混ざっている。
- §1 の4行目のコマンド `grep -rln "REQUIREMENTS:"` は、**どこで実行するかで答えが変わる**（根から＝acceptance.md が落ちる／`.claude/` を直に指す＝出る）。再現手順として不十分。

### 観点⑥ 実行プロセス — **PASS**

- 実装は0行。監査を**承認の前**に通している（まこさん指示 2026-08-26 の逐語どおり）。§9 の順番（要件を足す→設計→監査→承認→実装→テスト→再承認）は、既存の hook の作り（承認の指紋・fail-closed）と矛盾しない。
- §7 の1番（engine_tuner が走らなくなる）を**副作用として先に書いている**のは正しい作法（Q4 で事実と確認）。

### 観点⑦ 主エージェントバイアス — **FAIL**

- **§6 の完成の条件10件は、10件とも「この道具が動くか」を測っており、「要件に無いものが作れないか」を測る条件が0件。**
- 目的の2つ目（合格の条件を CC が自分の言葉で書けない）を測る条件も0件。**この設計書自身が、§6 に CC の言葉で10件の合格条件を書いている。**要件 R17 の `accept` は差し込まれるが**置換ではなく追加**なので、CC の言葉は横に並んで残る（§4 の L114 が「まこさんが並べて読めばずれが見えます」と、人の目に委ねていることを自認）。

日本語で1行：**完成の条件を全部 満たしても、まこさんの目的（要件に無いものを作らせない）は担保されない。条件は道具の内側だけを見ている。**

---

### Q1 — 完成の条件は目的を担保するか → **10件中 8件に穴あり／目的への到達は 0/2**

| # | 条件（L142-152 の逐語） | 測れるか | 穴 |
|---|---|---|---|
| 1 | 「要件に紐づかない設計書は承認できない」 | 測れる（T12・T13＋実走） | **`REQUIREMENTS:` の後ろが空でも通る。**§3.2 の L71 は「①行が在るか ②番号が要件に実在するか」＝**番号が0個なら、②は空集合に対して真**。＝要件を1つも指さない設計書が承認できる |
| 2 | 「要件の番号が無い設計書のままでは、`scripts/priority_rebuild/*.py` を1行も書けない」 | **測れない**。確かめ方が「偽の入力を渡して止まること」＝hook 単体に手で JSON を流す話で、**実際の書き込み経路の検査になっていない** | **偽。**止める所②は `Write|Edit` 専用（同ファイル4行目）。Bash の heredoc で書ける |
| 3 | 「差し込みを手で書き換えたら落ちる」 | 測れる（T14） | **止まる理由が違う。**T14（L129）は「止める（`hash=` が合わない）」と書くが、`hash=` を付け直すのは `write_requirements` 自身。実際に守っているのは §3.2 の④（json から作り直して比べる）で、**③は単独では何も止めない** |
| 4 | 「逐語が要件の json から来ている」 | 測れる（T15） | **目的2に届かない。**「json 由来の文が入る」ことは測るが、「CC が自分の言葉で合格条件を書き足すこと」は測っていない |
| 5 | 「囲みの中の文字を目印と取り違えない」 | 測れる（T16） | **``` の囲みだけ。**4字下げの囲み・`~~~`・全角のコロン・大文字小文字は測っていない（Q2(a)） |
| 6 | 「どの設計書も指していない要件の番号が出る」 | 測れる（T17） | **1行に `R1, R2, …, R17` と並べれば恒久的に0件になる。**＝「作ったフリの検出」（L148）が1行で無効化される |
| 7 | 「正しいものは通る」 | 測れる（T18） | 穴なし |
| 8 | 「この設計書自身が `check_requirements` を通る」 | 測れる | **循環している**（試験体と設計書が同一）。加えて §9 の7番どおり、差し込みを入れた瞬間に承認が外れ、再承認が要る |
| 9 | 「既存の検査を1つも壊していない（T1〜T11）」 | 測れる | **T10 が本番の `design_approved.json` を書き換える**（観点④-4）。合格の条件が、本番の承認記録に副作用を持つ |
| 10 | 「`--diff` が齟齬0件・`--scan-contracts` が読めない0本」 | 測れる | **「承認済みの設計書に対して」が抜けている。**設計書を実物に合わせて書き換えれば、いつでも0件にできる（`check_approval` が作られた動機そのもの＝同ファイル 491-493行目の逐語「**CC（私）が設計書の側を書き換えて0件にした**」） |

**総括（断言）＝10件を全部 満たしても、目的①（要件に無いものを作れない）にも目的②（合格の条件を CC が自分の言葉で書けない）にも届かない。**目的①は「番号を書けば通る」ので §4 の L116 が自認するとおり嘘の番号で抜けられ、目的②は差し込みが**追加**であって**置換**でないため、CC の言葉は残る。

---

### Q2 — 抜け道を探せ（攻撃者の目） → **hook を書き換えない抜け道 10件**

#### (a) `REQUIREMENTS:` の行の見分け方 → 穴 5件

設計書が定義しているのは L69 の1文だけ＝「行の先頭（前は空白だけ）に在るものだけを数える。``` で囲んだ中と、引用（>）の行は数えない」。ここから漏れるもの。

- **A-1 後ろが空**：`REQUIREMENTS:` だけの行が①を満たし、②が空集合で真＝**通る**（Q1-1）。
- **A-2 4字下げの囲み**：Markdown では4字下げも囲みだが、「前は空白だけ」なら数えると読める。＝T16 が守るのは ``` だけ。説明の文の中に4字下げで `R99` を書けば、意図せず止まる（誤検出）。
- **A-3 大文字小文字・全角**：`Requirements:`／`ＲＥＱＵＩＲＥＭＥＮＴＳ：`／`REQUIREMENTS：`（全角コロン）について**設計書は何も決めていない**。実物の `extract_block` は完全一致（`s == mark`）なので、同じ作りにすれば全角は落ちる＝目印を全角にした設計書は「①行が無い」で止まる（過剰に止める）。
- **A-4 複数行・重複・空白の混入**：`REQUIREMENTS: R17` と `REQUIREMENTS: R99` の2行を書いたとき、和にするのか先頭だけかを**決めていない**。`R 17`・`r17`・`R17,,R3` の扱いも未定義。
- **A-5 目印の文字列そのものが食い違っている**：§11 の SPEC は `"REQ_MARK": "REQUIREMENTS"`（L280・コロン無し）だが、§3.2・§5・§6 は一貫して「`REQUIREMENTS:` の行」（コロン有り）と書いている。**定数と本文が別のものを指している。**

日本語で1行：目印の見分け方が1文しか書かれておらず、後ろが空でも通り、全角にすると止まり、複数書いたときの扱いが決まっていない。

#### (b) 差し込みの `hash=` の作り方 → 穴 2件（設計書に定義が無い）

既存の2つの前例は、**ハッシュの対象範囲が違う**（実物で確認）。

- `gen_windows.py`：`h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]`（128行目）＝**囲みの中身だけ**。しかも `verify()`（297-303行目）は**ハッシュを照合していない**＝`periods.py` から作り直した文字列と**全文を比べている**（`if cur != blk`）。＝`hash=` は飾りで、守っているのは「正本から作り直して比べる」こと。
- `gen_improvement_arc.py`：`ARC_DOC hash=` は**指紋の行から下の文書ぜんぶ**を対象にし（236・242行目）、`verify()` は**ハッシュ照合と作り直しの二段**（245-267行目）。

設計書 §3.3 は「`gen_windows.py` の `WINDOWS_START/END` と同じ形」としか書いていない＝**弱いほうの前例**（囲みの中だけ）を指している。

- **B-1 囲みの外は守られない。**`<!-- REQ_END -->` の直後に CC が「※R17 の accept はこう読み替える」と1行 足しても、`hash=` にも `check_requirements` にも掛からない。設計書の残り約300行（§4 の表・§6 の完成条件・SPEC）も同じく無防備。守っているのは `design_approved.json` の全文ハッシュだけで、それは**承認したあと**しか効かない。
- **B-2 `hash=` は付け直せる。**中身を書き換えて `write_requirements` を走らせれば、`hash=` は新しい中身に合う。実際に止めるのは §3.2 の④（json から作り直して比べる）だけ。＝**T14 の「止める理由＝hash が合わない」は誤り。**

日本語で1行：ハッシュは「囲みの中だけ」を見る形で、外に何を書いても素通りし、しかもハッシュ自体は付け直せる。本当に守っているのは「要件の json から作り直して比べる」ことだけ。

#### (c) 承認の順番 → 塞がっているのは半分だけ

- **塞がっている側（実測）**：承認のあとに設計書を書き換えると、`check_approval`（488-523行目）が `(False, "設計書の承認: 外れています…")` を返し、hook の151-160行目が止める。**監査中に実際に発火した**（S-3）。実装側も `require_acceptance_before_impl.sh` の163-167行目が指紋を比べて止める。
- **塞がっていない側 C-1**：`check_approval` の516行目＝**`return True, "設計書の承認: 記録なし（未承認）"`**。`design_approved.json` は `.gitignore` の対象（実測）で、**CC が消せば「記録なし」に戻り、通る**。fail-closed になるのは hook の162-167行目＝**engine_tuner を走らせるときだけ**。設計書 §3.4 の①はこの穴に触れていない。
- **塞がっていない側 C-2**：**CC が `approve_design.sh` / `approve_impl.sh` を自分で叩ける**（観点② の逐語引用）。設計書 §10 に無し。

#### (d) hook 側の黙った素通り → 新しい穴を作る書き方のまま／既に在る穴が3つ

設計書は「止める所②③に `--check-requirements` を足す」としか書いておらず、**どこに・どう足すか・失敗したらどうするかを1文字も書いていない**。実物には同じ型の穴が3つ生きている。

- **D-1 白名簿が「文字が含まれるか」だけを見ている**（50-54行目）。監査で実際に判定を再現した。

  | コマンド | 判定 |
  |---|---|
  | `python3 …/engine_tuner.py --purpose search --tag x` | **止まる** |
  | `python3 …/engine_tuner.py --purpose search --tag x # --help` | **素通り** |
  | `python3 …/engine_tuner.py --purpose search --write-requirements foo` | **素通り** |
  | `echo --diff; python3 …/engine_tuner.py --purpose search` | **素通り** |

  ＝**コマンドの末尾に `# --help` と書き足すだけで、止める所③が丸ごと外れる。**しかも設計書が足そうとしている `--write-requirements` は、既存の `*--write*` に**そのまま当たる**。

- **D-2 入力が読めないと黙って通る**：40-47行目・57-67行目の python が `except: sys.exit(0)` で終わると `CMD`／`PYS` が空になり、**69行目 `[ -z "$PYS" ] && exit 0`** で何も言わずに通る。**設計書 §3.4 が「過去に塞いだ」と言っているのと同じ型の穴が、まだ残っている。**
- **D-3 契約が無い `.py` は黙って通る**（100-108行目）。fail-closed になるのは名前が `engine_tuner` で始まるものだけ。

日本語で1行：新しい検査をどこに足すか・失敗したときに止めるかが書かれておらず、いまの入口には「コマンドに `--help` と書けば全部 外れる」穴が生きている。

#### (e) 要件そのものの捏造 → **何も止めない（断言）**

- `.claude/hooks/` の全 hook を走査した結果、`engine_tuner_requirements.json` を守る hook は**0本**（唯一 `enforce_purpose_gate.sh` が名前を参照するだけ・しかもその hook は登録0件＝`next_step.md` §6 の79番）。
- `gen_engine_tuner_requirements.py --verify` は「**json から作った .md が手で書き換えられていないか**」しか見ない＝**json 自体は自由に書ける**。CC が R18 を自分で足し、`--write` で .md を作り直せば `--verify` は `✅ 改変なし` を返す。
- 止めるものは**git の差分（json は git 管理下）と、まこさんが読むこと**の2つだけ。
- **設計書 §10 の限界5件に、この道は入っていない。**§10 の2番は「要件を足すのは まこさんです」と書いているだけで、**CC が足せないようにする仕組みは無い**、という事実が書かれていない。

#### (f) `--req-coverage` の数え方 → 穴 3件

- **F-1 二重に数える。**`scan_contracts` の238行目は既定で `sorted(glob.glob(_RATCHET/"*.md")) + [_ACCEPTANCE]`＝**`acceptance.md` を最初から含む**。設計書 §3.2 の L73 は「見る相手＝`--scan-contracts` が読めた設計書 ＋ `acceptance.md`」＝**同じものを2回 足している**。
- **F-2 1行で満点にできる。**`REQUIREMENTS: R1, R2, …, R17` と書けば、指していない番号は恒久的に0件。**「作ったフリの検出」（§6 の6番）は、番号を並べるだけで無効になる。**しかも §3.4 の止める所①②③は「1件でも実在すれば通す」ので、**番号を余分に並べることに費用が無い。**
- **F-3 対象外の6本は数えない。**`contract_check_design.md` は `REQUIREMENTS:` を持っているが `--scan-contracts` では「対象外」（実測）＝数えられない。＝カバレッジの母集団が「契約が読める文書」に縛られ、実際の設計書の全体と一致しない。

日本語で1行：数える相手が二重で、しかも要件の番号を1行に全部 並べれば「全部 指されている」ことにできる。

---

### Q3 — 設計書と実物は一致しているか → **食い違い 7件**

| # | 設計書の逐語 | 実物 | 判定 |
|---|---|---|---|
| Q3-1 | L34「**そのうち「どの要件のために作るか」を書いている設計書 … 0本**」 | acceptance.md の L5 は `REQUIREMENTS: R17`。＝4本のうち1本が持っている | **食い違い（確認バイアス）**。原因＝`.gitignore:45` で `.claude/state/*` が除外され、根から `grep -rln` すると黙って落ちるため |
| Q3-2 | L33（4本・新しい acceptance を含む）と L34（0本・古い acceptance の前提） | 上書きは 12:23:40（実測） | **設計書の中の矛盾**。同じ表の中で時点が2つ混ざっている |
| Q3-3 | L119「止まらないもの⑤ … **`git diff` には必ず出ます**」 | 設計書自身は git 管理外（`.gitignore:45`）。実物 `.py` と hook は管理下 | **一部 誤り**。設計書の書き換えは git に出ない |
| Q3-4 | L129 T14「**止める（`hash=` が合わない）**」 | `hash=` は `write_requirements` が付け直す。実際に止めるのは §3.2 の④ | **食い違い（止まる理由の取り違え）** |
| Q3-5 | L280 `"REQ_MARK": "REQUIREMENTS"` | §3.2・§5・§6 は「`REQUIREMENTS:` の行」 | **設計書の中の矛盾**（コロンの有無） |
| Q3-6 | L135「**★T12〜T18 は、本物のファイルを1バイトも変えません**」／L151 完成の条件9「T1〜T11 が今までどおり」 | 既存 T10 は本物の `design_approved.json` を読み書きする（700-713行目） | **食い違い**。宣言の対象外だとしても、合格の条件9に含めている以上、副作用を書くべき |
| Q3-7 | L104-105「掛からない相手＝e35・e37・e38 …**この3本を直すときは `acceptance.md` を書き直す運用なので、実際には許可制を通ります**」 | 要件 R1〜R17 は **engine_tuner の要件だけ**（json の `note`＝「engine_tuner（旧 engine_search_e38.py）の要件の正本」）。e35/e37 の戦略そのものを直す作業に当たる番号が**1つも無い** | **食い違い（重大）**。詳細は Q4-5b |

**一致していた主張（念のため列挙）**：関数14個・公開11件・定数2件・旗5件・要件17件・完了10/作業中7・`accept` 17件・`--diff` 13件・`--scan-contracts` 4/0/6。

---

### Q4 — 既存を壊さないか（独立に再現） → **4件中 3件は事実／1件は不十分／追加の重大な副作用 1件**

**1. engine_tuner が走らなくなる（fail-closed）→ 事実**
1つ前の設計書は `"impl_file": "scripts/priority_rebuild/engine_tuner_exec.py"`（archive で確認）。いま `--scan-contracts` が返す4本の impl は e35／e37／e38／verify_design_contract.py で、**engine_tuner を指すものは0本**。hook の100-107行目は、契約が無く名前が `engine_tuner` で始まる `.py` を実行しようとすると `exit 2` で止める。**再現できた。**

**2. e35・e37・e38 の「実行」は変わらない → 事実**
3本とも契約が読める。SPEC は無い（`--diff` は「SPEC が設計書に無い」＝hook の131行目でスキップ）。承認の記録も無い（`design_approved.json` は acceptance.md の1件のみ）＝`check_approval` は「記録なし」＝通す。**実行は変わらない。**

**3. H2 の印・G2 の印の取り直しは要らない → 事実**
`h2_pass.json` = **21ファイル**、`g2_pass.json` = **37ファイル**（実測）。両方の一覧を文字列で検索して、`verify_design_contract` は **0件**、`engine_tuner_requirements` は **0件**。**設計書の主張どおり。**

**4. 売買記録・net は1バイトも変わらない → 事実**
`verify_design_contract.py` の import は `ast, glob, json, os, re, shutil, sys, tempfile` のみ。pandas も CSV も相場データも読まない。触る先は `.py`・`.json`・`.md` だけ。**net に触れる経路は無い。**

**5. ★止める所②に検査を足したときに、意図せず止まるもの → 重大（設計書の §7 に無い）**

- **5-a 診断の免除（`*_diag.py`）は、足す位置で運命が変わる。**`require_acceptance_before_impl.sh` の免除は51-61行目にあり、**62-65行目の「`scripts/priority_rebuild/*.py` だけ対象」という絞り込みより前**にある。設計書は「`scripts/priority_rebuild/*.py` を書く瞬間に走らせる」としか書いておらず、**51行目より前に足せば診断の作業が全部 止まり、62行目より後に足せば診断は今までどおり抜ける。**どちらにするかが書かれていない。
- **5-b 既存の戦略ファイルの修正は、止まる（断言）。**止める所②は `.py` のパスで発火するので、`e37_range_scalp.py` や `e35_range_oscillation.py` を直すときも `acceptance.md` に有効な `REQUIREMENTS:` が要る。ところが**要件 R1〜R17 は engine_tuner の要件**（json の `note` 逐語）。E37 の作り直し（`permanent_rules.md` §6-58「E37 を再開するときに、まず直す3件」）に当たる番号は**1つも無い**。
  ＝**この設計をそのまま入れると、E35/E36/E37 の戦略コードは「番号が無いから直せない」か、CC が嘘の番号を書くかの二択になる。**後者は、この設計が防ごうとしている行為そのもの。

日本語で1行：**要件の一覧が engine_tuner 専用なのに、許可制は `scripts/priority_rebuild` の全部の `.py` に掛かるので、戦略の修正が要件に当たらず止まる。**

---

### Q5 — 範囲の決め方が、CC の裁量が増える方向に寄っていないか → **判定＝狭すぎる**

**断言：§3.5 の範囲の決め方は狭すぎる。**理由は3つ。

1. **「掛かる相手を1本だけ並べる」＝既定が許可（fail-open）。**許可制の本旨は「並べたものだけを許す」だが、§3.5 は逆に「**掛ける相手だけを並べ、それ以外は自動的に外れる**」形になっている。＝**これから増える設計書はすべて既定で対象外**。恒久の決まり §0-2（設計書は acceptance.md に上書き・新しい設計書を作らない）が守られる限りは問題にならないが、**その決まりを破ったのは 57回目の CC 自身**（同 §0-2 の逐語「57回目に私が `forbidden_check_design.md` を作って まこさんに指摘された」）。＝**同じ CC が破った実績のある運用の決まりに、機械の強制が寄りかかっている。**
2. **CC の裁量が増える方向。**「対象は1本」と決めると、**それ以外の設計書に何を書くかは CC が自由**になる。`permanent_rules.md` の26行目＝「**| 3 | 範囲を決めるとき、私の裁量が増える読み方を取らない | 読み方が2通り以上あるとき |**」。読み方は2通り（全部に掛ける／1本に掛ける）あり、**取られたのは裁量が増えるほう**。
3. **まこさんの指示の逐語に対して狭すぎる。**指示は「**要件定義した内容以外のものを作るな**」＝作るもの全部。§3.5 は「設計書1本」に置き換えているが、Q4-5b のとおり**その1本に掛けると既存の戦略修正が止まる**ので、範囲は狭すぎると同時に**掛け方も外している**（掛ける粒度が「設計書」ではなく「`.py` のパス」になっている）。

**代わりに取るべき範囲（3点セット）**

- **(ア) 既定は全部に掛ける／外すものは まこさん承認の「免除の一覧ファイル」に書く**（`signal_families_approved.txt`・`exit_families_approved.txt` と同じ形）。免除は `e35_design.md`・`e37_design.md`・`e38_design.md` の**3行だけ**。CC が行を足せば git の差分に出る。＝既存は壊れず、これから増える設計書は既定で対象になる。
- **(イ) 要件の適用範囲を決める。**要件の一覧を engine_tuner 専用から「作るものの全体」へ広げるか、戦略側に別の要件の束を用意する。**いまの一覧のままでは Q4-5b が必ず起きる。**
- **(ウ) 掛ける粒度を「書き込む `.py` のパス」ではなく「その `.py` を指す設計書」に揃える。**`require_acceptance_before_impl.sh` は既に `TARGET:` で対象を持っているので、**`TARGET` が免除の一覧に載っていない相手のときだけ `REQUIREMENTS:` を要求する**、と書けば診断の免除も戦略修正も壊れない。

---

## 4. 外部検索結果サマリー

**検索クエリ（4本・WebSearch／WebFetch を実行）**

1. `requirements traceability matrix machine enforced commit design document mapping practice bidirectional traceability coverage`
2. `policy as code gate bypass failure modes fail-open silent pass CI enforcement pitfalls`
3. `generated block markdown checksum tamper detection managed section pitfalls "DO NOT EDIT" region hash scope`
4. `cog "[[[end]]]" checksum generated output` ／ `requirements traceability "fake" trace links validation LLM agent`

| # | 発見（逐語 or 要旨） | 出典 | 本監査のどこに効くか |
|---|---|---|---|
| 1 | 「**Our implementation is fail-open: if a gate itself raises an exception, the harness records the error and allows the original call.**」＝検査そのものが落ちたら通す設計は、実在する典型の失敗 | [Reason Less, Verify More (arXiv 2607.07405)](https://arxiv.org/html/2607.07405) | **Q2(d) D-2**。設計書は新しい検査が落ちたときの扱いを書いていない |
| 2 | 「**the result is a silent wrong state … neither the tool nor the agent's self-report exposes the violation**」／「**78% of observed failures are silent wrong-state failures with no tool error**」 | 同上 | **観点②・Q2(d)**。黙って通る型が失敗の大半だという定量 |
| 3 | 「**A tool may execute any well-formed call even when the corresponding state transition is forbidden by domain policy. The policy lives in a natural-language document the model is instructed to follow; it is not enforced by the tool.**」 | 同上 | **Q1・Q2(e)**。要件の json は「文書」であって強制ではない＝捏造を止めない |
| 4 | 「**There is no per-PR override flag and there will not be one. Bypass must be visible in the policy file's history.**」＝抜け道は作らず、抜けたことが履歴に残る形にする | [Agent Package Manager — Enforce in CI (Microsoft)](https://microsoft.github.io/apm/enterprise/enforce-in-ci/) | **Q2(d) D-1**。`# --help` で外れる白名簿は、まさに per-command override |
| 5 | 「**If the scratch replay itself cannot be materialized, the audit fails closed instead of reporting a green skip.**」＝材料が用意できないときは緑の飛ばしでなく落とす | 同上 | **Q2(d) D-2・D-3**。「読めない＝通す」を「読めない＝止める」へ |
| 6 | 「**a policy gate … the enforcement layer itself is infrastructure that can fail with a failure mode of governance-off**」／組織が全ポリシー失効中も出荷を続けた実例 | [Fail Closed (DevSecOps School, 2026)](https://devsecopsschool.com/blog/fail-closed/) | **Q4-1**。engine_tuner の fail-closed は正しいが、他は governance-off のまま |
| 7 | 「**CRCs offer no protection against an adversary who simply recomputes the CRC after editing the data.**」／「a matching checksum says the bytes are unchanged since the value was computed, but it does not say who created the file」 | [Checksum (Wikipedia)](https://en.wikipedia.org/wiki/Checksum) ／ [A generic attack on checksumming-based software tamper resistance (IEEE S&P 2005)](https://conferences.computer.org/sp/pdfs/sp/2005/05_04_01.pdf) | **Q2(b) B-2**。`hash=` は付け直せる＝T14 の説明が誤り |
| 8 | Cog の管理節の定石＝「**checksum in the `[[[end]]]` marker … the next time cog is run, the checksum won't match, and cog will stop to avoid overwriting the edited output**」＋ CI 用の `--check` | [Running cog (cog 3.6.0 docs)](https://cog.readthedocs.io/en/stable/running.html) ／ [Cog — Ned Batchelder](https://nedbatchelder.com/code/cog/index.html) | **Q2(b)**。定石は「①ハッシュで上書きを拒む ②CI で作り直して差が無いことを確認する」の二段。設計書は②だけを持ち、①の役割を誤解している |
| 9 | 「**Bidirectional traceability … is the only approach that supports both coverage analysis (requirements missing tests) and scope control (tests or design elements with no requirement)**」＝片方向では「要件に無いものを作った」を検出できない | [What is Requirements Traceability (Trace.Space)](https://www.trace.space/blog/what-is-requirements-traceability) ／ [Traceability Matrix (Jama Software)](https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/traceability-matrix/) | **Q2(f)**。番号を並べるだけでは範囲の管理にならない |
| 10 | 「**spreadsheets can store traceability information, they can't enforce it**」／LLM が付けた追跡リンクには「**phantom links**」が出るので「**human review is required**」 | [Perforce RTM](https://www.perforce.com/resources/alm/requirements-traceability-matrix) ／ [TraceLLM (arXiv 2602.01253)](https://arxiv.org/html/2602.01253v1) ／ [Trust-Aware Multi-Agent Traceability (arXiv 2606.17203)](https://arxiv.org/pdf/2606.17203) | **Q1・Q2**。業界も「番号のひも付けだけでは嘘の番号を止められない」と結論しており、対処は双方向＋人のレビュー＋リンク妥当性の検証。設計書の「まこさんが読む」は方向は同じだが、**読む材料（差分の見せ方）を設計していない** |

---

## 5. 総合判定

### **Verdict: NO-GO**（このままの設計書では承認に進めない。方向＝許可制は維持）

**根拠（数値で断言）**

1. **完成の条件10件のうち8件に穴があり、目的への到達を測る条件は 0/2 件**（Q1）。＝条件を全部 満たしても、まこさんの目的は担保されない。
2. **hook を書き換えずに抜けられる道が10件**（Q2）。うち**実測で再現したものが4件**＝①コマンドに `# --help` を足すと止める所③が丸ごと外れる ②`Write|Edit` を使わず Bash で `.py` を書ける ③`design_approved.json` を消すと承認の検査が「記録なし」で通る ④要件 json を守る hook は0本。
3. **設計書と実物の食い違い 7件**（Q3）。うち**設計書の中の矛盾が2件**（§1 の行3と行4の時点／`REQ_MARK` のコロンの有無）、**「実測」と称した記述の誤りが1件**（0本）。
4. **既存を壊さない主張4件は3件が事実**だが、**§7 に書かれていない重大な副作用が1件**＝**E35/E36/E37 の戦略コードの修正が止まる**（要件が engine_tuner 専用のため）。これは「嘘の番号を書く」ことを構造的に強いる状態で、**設計の目的と正反対**。
5. **範囲の決め方は狭すぎる**（Q5）。「掛ける相手を1本だけ並べる」＝既定が許可。恒久の決まり26行目（裁量が増える読み方を取らない）に反する。

**GO にしなかった理由の裏返し（正しく評価した点）**：実装0行で監査に出した順番は正しく（観点⑥ PASS）、engine_tuner の fail-closed・H2/G2 の印・net 不変の3点は**独立に再現して事実**だった。方向（許可制・番号＋逐語の自動差し込み）は まこさん決定であり、変える必要はない。**直すのは設計書の中身。**

---

## 6. 改善方向性（7件・優先度つき）

| # | 優先度 | 提案 | なぜ（1行の日本語） |
|---|---|---|---|
| I-1 | **Critical** | **範囲を「既定は全部に掛ける／外すものは まこさん承認の免除一覧に3行だけ書く」へ入れ替える**（`signal_families_approved.txt` と同じ形）。同時に、**掛ける粒度を「書き込む .py のパス」から「その .py を指す設計書（TARGET）」へ揃える** | いまの形だと、これから増える設計書が自動で対象外になり、逆に E35/E37 の修正が止まる |
| I-2 | **Critical** | **要件の適用範囲を決める。**①要件 R1〜R17 は engine_tuner 専用である、と設計書に明記し、②engine_tuner 以外（E35/E36/E37 の戦略）は免除一覧に入れるか、③まこさんが戦略側の要件を別に決める。**どれにするかは まこさんの決定事項として、設計書に空欄で残す** | いまのままだと「番号が無いから直せない／嘘の番号を書く」の二択になり、設計の目的と正反対になる |
| I-3 | **Critical** | **止める所②③に足す検査を fail-closed で書く**と設計書に明記する。具体＝(a) 新しい検査の終了コードが 0 以外**または**出力が空なら**止める** (b) hook の入力が読めないときも**止める**（いまの69行目の「空なら通す」を改める） (c) **白名簿を「コマンドに文字が含まれるか」から「実際に走らせる `.py` と旗の組み合わせ」へ変える**（`# --help` で外れる穴を塞ぐ） | 検査が落ちたときに黙って通る形は、業界で最も多い失敗の型（外部発見 1・2・5） |
| I-4 | **Critical** | **`REQUIREMENTS:` の行の決まりを、設計書に表で全部 書く。**最低＝①**番号が1件以上 必須**（空は止める）②半角のみ・大文字のみ・コロンは半角 ③``` と4字下げの囲み・`>` の引用は数えない ④複数行は和 ⑤重複・空白は正規化 ⑥全部を `extract_block` と**同じ関数の中**で判定する（囲みの判定を2つ作らない） | いまは「後ろが空でも通る」「全角にすると止まる」「複数書いたときの扱いが無い」状態 |
| I-5 | **Major** | **`hash=` の対象範囲を設計書に書き、`gen_improvement_arc.py` の側（文書ぜんぶを対象）に合わせる。**そのうえで **T14 の説明を「json から作り直して比べるので止まる」に直す**。加えて **`--req-coverage` の数え方から `acceptance.md` の二重足しを外す**（`scan_contracts` が既に含んでいる） | ハッシュは付け直せるので、囲みの中だけを守っても、外に何を書いても素通りする |
| I-6 | **Major** | **§10 の限界に3件 足す**：①**承認のコマンドを CC 自身が打てる**（hook 自身が逐語で認めている）②**`design_approved.json` を消すと「記録なし」で通る**③**要件の json を CC が書き足せる（止める hook は0本）**。加えて **§4 の「`git diff` には必ず出ます」を「実物と hook は出るが、設計書は `.gitignore` の対象なので出ない」に直す** | 「限界を隠しません」と書いた節に、いちばん大きい3つが入っていない |
| I-7 | **Minor** | **§1 の表を測り直し、時点を1つに揃える。**①4行目の「0本」を、この設計書自身を含めた実測に直す ②数え方を「リポジトリの根からの `grep -rln`」ではなく「`--scan-contracts` が返した4本の中を数える」に変える（`.gitignore` で落ちない方法にする）。あわせて **`REQ_MARK` の値をコロン有り無しどちらかに統一する** | いまの数え方は、除外設定のせいで自分の設計書を黙って数え落としている |

---

## 7. CC プロセス欠陥対策

**該当あり。3件。**

- **P-1（新規・要 hook 化の候補）＝「実測」と書いた行に、再現コマンドと除外設定の影響を書かせる。**
  今回、`grep -rln "REQUIREMENTS:"` が `.gitignore` のせいで**対象そのものを黙って落とし**、その結果を「0本」と設計書に書いた。**除外設定によって数が変わる数え方を「実測」と呼ぶのは、`false_positive_incident_policy.md` §2 類型 G（確認したフリ）に接する。**
  対策＝設計書に「実測」と書くときは、**①実行したコマンド ②実行した場所 ③除外設定の影響の有無**の3つを添える。`.claude/state/` のように `.gitignore` の対象になっている場所を数える場合は、**`--scan-contracts` のようなプログラムの出力を使い、`grep -r` を使わない。**

- **P-2（既存の教訓の再演）＝「同じ判定を2か所に作らない」が、また起きようとしている。**
  `verify_design_contract.py` の232-235行目に、**まったく同じ型の事故の記録**がある（逐語＝「**『どれが設計書か』を決める判定が2か所に在り、片方（この関数）だけ `.actual.md` を外していた**」）。今回の設計は、囲みの判定を `extract_block` と `extract_requirements` の2か所に持たせる（SPEC の `"extract_requirements": []` が根拠）。
  対策＝**設計書の SPEC に新しい関数を足すとき、「既に在る関数のどれと同じ判定をするか」を1行 書く。同じなら、その関数を呼ぶ形にする。**

- **P-3（重大・cc_role §1.4.6 の目的整合ゲートの穴）＝完成の条件が「道具の内側」だけを測っている。**
  §6 の10件は1件も「まこさんの目的が達成されたか」を測っていない。これは `false_positive_incident_policy.md` §3 の **#12 の欄に記録されている型と同じ**（逐語＝「**完了の線も自分で『G2 適合率 100%』と引いた＝意味の制約が入らないままその線は満たせる＝『線を満たしたまま目的に届かない』#11 と同じ型**」）。**同じ型が #12 のあと、この設計書で再演している。**
  対策＝**完成の条件の表に「目的の欄」を足す。**1行ごとに「この条件を満たすと、まこさんの目的のどれが、どこまで担保されるか」を書く。**担保しないものは「担保しない」と書く。**目的を担保する条件が1件も無ければ、その設計書は完成の条件が未完成である、と判定する。

---

## 参照した実物（監査で開いたファイル）

- `.claude/state/acceptance.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/verify_design_contract.py`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_windows.py`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_improvement_arc.py`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_requirements.json`
- `.claude/hooks/require_design_contract_before_run.sh`
- `.claude/hooks/require_acceptance_before_impl.sh`
- `.claude/hooks/approve_impl.sh`
- `.claude/hooks/approve_design.sh`
- `.claude/state/h2_pass.json` ／ `.claude/state/g2_pass.json` ／ `.claude/state/design_approved.json`
- `.claude/ratchet/acceptance_archive/unordered-scan-scope-20260826.md`

## 出典（外部検索・URL）

- [Reason Less, Verify More: Deterministic Gates Recover a Silent Policy-Violation Failure Mode in Tool-Using LLM Agents (arXiv 2607.07405)](https://arxiv.org/html/2607.07405)
- [Enforce in CI — Agent Package Manager (Microsoft)](https://microsoft.github.io/apm/enterprise/enforce-in-ci/)
- [What is Fail Closed? (DevSecOps School, 2026)](https://devsecopsschool.com/blog/fail-closed/)
- [Checksum (Wikipedia)](https://en.wikipedia.org/wiki/Checksum)
- [A generic attack on checksumming-based software tamper resistance (IEEE S&P 2005)](https://conferences.computer.org/sp/pdfs/sp/2005/05_04_01.pdf)
- [Running cog — cog 3.6.0 documentation](https://cog.readthedocs.io/en/stable/running.html)
- [Cog — Ned Batchelder](https://nedbatchelder.com/code/cog/index.html)
- [What is Requirements Traceability? — Trace.Space](https://www.trace.space/blog/what-is-requirements-traceability)
- [What is a Traceability Matrix? — Jama Software](https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/traceability-matrix/)
- [Requirements Traceability Matrix — Perforce](https://www.perforce.com/resources/alm/requirements-traceability-matrix)
- [TraceLLM (arXiv 2602.01253)](https://arxiv.org/html/2602.01253v1)
- [Trust-Aware Multi-Agent Traceability (arXiv 2606.17203)](https://arxiv.org/pdf/2606.17203)

---

依頼書 §結果ファイルフォーマット の7セクションを全部 出力しました。監査終わり。
