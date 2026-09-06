# 【監査依頼】M2-C-2（指標のオン・オフの切り替え）の検収と、承認の凍結が空だった件（cp20）

> ★この依頼書の本文は、機械の出力の逐語の写しだけです（まこさん指示 2026-09-05・逐語「依頼書に「CC が書いた文章」を1文字も入れないでください」「中身は機械出力の逐語の貼り付けだけにすること」「節ごと そのまま貼ること。抜粋しない」）。
> 写した元＝`.claude/state/session_worklog_20260904.md`（リポジトリ直下）の §8・§14・§15・§18・§19.1。写し方＝`sed -n` で節の行の範囲をそのまま取り出して並べた（打ち直しゼロ）。
> CC が書いたのは、この枠の中と「監査依頼メタ情報」「着手前必読」の表、末尾の「載せなかったもの」の一覧だけ。

---
---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 N 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-XX-XX_<task>_cpN_audit_report.md` を Write
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / NO-GO / PIVOT / OTHER)
   - 最優先指摘 (Critical) 件数

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

---

## 監査依頼メタ情報

- 依頼日: 2026-09-05
- 依頼者: まこさん（CC は写しただけ）
- 監査区分: 検収の監査（M2-C-2）＋ 承認と監査の仕組みの不具合（凍結が空だった件）
- 監査対象タスク: M2-C-2（指標のオン・オフの切り替え・設計書 acceptance_archive/indicator-switch-20260902.01.md＝承認済み）／T25 の直し（acceptance_archive/t25-fixture-off-20260904.md＝承認済み・commit b282902）／承認スクリプトの凍結が空だった件（next_step §6 の131番・未修正）
- 結果ファイル保存先: `.claude/audits/2026-09-05_m2c2_indicator_switch_cp20_audit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-09-05_m2c2_indicator_switch_cp20_audit_request.md`

---

## 監査に必ず含めること（まこさんの逐語・2026-09-05・箇条書きのまま）

1. 凍結が空だった件（原因＝approve_impl.sh が最後の囲みから取る作り）
2. その対策が「SPEC を節の前に置く」という暗黙の並び順である件
3. 過去の設計書のうち、同じ並びで空が凍結されたものが何本あるか（まだ数えていなければ「未調査」と書くこと。推測で書かない）
4. 「使う」140種が意図の範囲かの確認

★1〜3 の実測は下に写した worklog の §15・§18、4 の実測は §8 に在る。

---

## 着手前必読 (省略禁止・auditor 用・9件)

1. `.claude/state/session_worklog_20260904.md`（リポジトリ直下）§8・§14・§15・§18・§19.1 — 下に節ごと写した（元と同じか `sed -n` で確かめられる）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/indicator-switch-20260902.01.md` — M2-C-2 の承認済みの設計書（★`.01.md` が元の設計書。同名の `.md` は 2026-09-04 22:16 の承認で t25 の中身に上書きされた＝§14.1）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/t25-fixture-off-20260904.md` ＋ 同 `.frozen.json`（367 バイト・空） — T25 の直しの設計書と、その凍結
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/identity-l1s1-exec-contract-20260904.md` ＋ 同 `.frozen.json` — 恒等 L1・S1 用の設計書と、その凍結（空でない）
5. `.claude/hooks/approve_impl.sh`（リポジトリ直下）62-73行・105-115行 — 凍結を作る処理
6. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/verify_design_contract.py` 141-236行・882-960行・1622行 — 照合の道具の、目印の取り出しと凍結との突き合わせ
7. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_indicator_switch.py` ＋ `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indicator_switch.json` — 印を作る道具と、いまの印（使う 140種）
8. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` 466-489行・5306-5360行 — T25 の直し（`_mat_fixture` の `off_ok`・T33・T33-f）
9. `.claude/state/next_step.md`（リポジトリ直下）§6 の 127〜131番 — この件の記録

---

## 監査対象の事実データ（★以下は session_worklog_20260904.md の §8・§14・§15・§18・§19.1 の逐語の写し・sed -n で節ごと取り出した・抜粋なし）

## §8 印を作り直した（gen_indicator_switch.py --write・ToDo の2番）

**走らせた順**＝`--verify`（直す前）→ `--write` → `--verify` → `--selftest`。全部 `scripts/priority_rebuild/` で走らせた。

| 何を | 直す前（2026-09-02 16:07 の印） | 直した後（2026-09-04） |
|---|---|---|
| `--verify` | ❌「源が変わっている（いま 7ef4a4a609c0e9f1 ／ 作り直すと dec5519430b997b0）」 | ✅「印は機械が書いたままです（指紋 dec5519430b997b0）」 |
| 使う | 71 種 | **140 種** |
| 使わない | 185 種 | **116 種** |
| 源1 ta | 64 種 | 64 種 |
| 源2 法則 | 9 種（2通り展開の版） | **89 種**（4通り展開＝family・geo・系統・性質） |
| 源3 恒等レシピ | 8 種 | 8 種 |
| 対応が決まらない ta のクラス | 5 件 | 5 件（使わないに倒したまま） |
| `--selftest` | — | **9/9 pass**（T1〜T9） |

**★「使う」が 71 → 140 に増えた理由**＝`source_law` が 2通り（family・geo）から 4通り（＋系統・性質）に直ったため（78回目の直し・設計書 §3.3 の源2 の逐語「4通りを展開」）。**系統（構造・位置）と性質（vol）で名指しされる種類が 80 種ほど在る**ということ。★この数が まこさんの意図（「本来の目的が達成できるまでは、指標一覧はta 43種にする」＋「レンジ判定で必要な指標は入れろ」）に合っているかは、私は判定しない＝§10 で まこさんに出す。
**★定義表の種類は 256 で変わらない**（型の表・行は1つも消していない＝設計書 §3.4）。

**ついでに `--ta-candidates`（読むだけ）を走らせた**＝ta のクラス 43件のうち ①照合式・承認済みで確定 **38件** ②略号の一致で候補が出た **0件** ③候補が出なかった **5件**＝WilliamsRIndicator・CumulativeReturnIndicator・DailyLogReturnIndicator・DailyReturnIndicator・AccDistIndexIndicator。**M2-C-1 の実測（`session_worklog_20260902.md` §3・「うち材料に対応が無いのは5件」）と同じ5件。**＝設計書 §9.1 の案A で まこさんが見る候補は、いま 0件（決めるものが無い）。この5件は材料に無いので「使わない」に倒れたまま（fail-closed）。

**フロー宣言を書いた（ToDo の3番・同じ §8 に記録）**＝`flow_declaration.md` に、段＝M2-C-2／工程＝実装後の確認／実行＝自己テスト2本・恒等3本・G2・H2／数え方＝確認する（累積に数えない）／時間の見込み＝15分未満（合計 約13分）／過去の実測4件（恒等3本 28秒＝worklog 20260825:537・H2 4分38秒と G2 27.6秒＝next_step:229・生成器の自己テスト 約6分＝worklog 20260827:1719・実行器の自己テスト 5.9秒＝worklog 20260830:181）を書いた。同じ内容をチャットにも出した。


---

## §14 承認3回と、実装（iter="t25-fixture-off-20260904"）

### 14.1 承認が3回 要った理由（2回は私の設計書の不足・門に止められて分かった）

| 回 | 時刻 | 何が起きたか |
|---|---|---|
| 1回目 | 22:22 | 承認は入ったが、実装の Edit で受け入れ条件ゲートに止まった＝「塞げないもの」の節が無い（cp14 の B-5）。**★控えが `indicator-switch-20260902` の名前で書かれた**＝REQUIREMENTS の行に前の設計書の名前を `iter="…"` の形で書いていて、承認スクリプトがそれを先に拾った。前の設計書の中身は `indicator-switch-20260902.01.md`（17,955 バイト）に残っている＝失われていない。行を直した |
| 2回目 | 22:2x | §9 に「塞げないもの」A〜C・まこさんの条件（T33-f の加算・§5 の7・§6 の8）を入れて再承認。実装の Edit で再び止まった＝「塞げないもの」に監査 cp14 の Q5 の5件が要る |
| 3回目 | 22:2x | §9 に Q5 の5件（D〜H）を足して再承認。**控え＝`acceptance_archive/t25-fixture-off-20260904.md`・`.frozen.json`・`.breaks.json`** |

**★教訓**＝受け入れ条件ゲートが求める節（「塞げないもの」＋ Q5 の5件）は、cp19 の設計書の §9 の形をそのまま写せば1回で通った。次に設計書を書くときは cp19 の §9 を雛形にする（`lessons_active.md` に足す）。

### 14.2 実装（engine_tuner_gen.py・3か所・25行 追加・3行 削除）

| # | 何を | 行 |
|---|---|---|
| 3.1 | `_mat_fixture` に `off_ok` の引数と分岐（印が「使う」なら `SampleError`・「使わない」なら鍵なしの辞書） | 466-489 |
| 3.2 | T33 の材料の辞書を `_mat_fixture(_off[0], None, "5m", off_ok=True)` に | 5318 |
| 3.3 | T33-f（「使う」の先頭に off_ok=True → 止まれば印字・止まらなければ t33 に append＝ng に加算）＋ 印字の行に (f) | 5338-5348・5356 |

`py_compile` ✅。**恒等 S2＝✅ 完全一致（md5 7b01f51b5a9b29b3c05a7b340c203ba1・22:26）／実行器の自己テスト＝✅ 全部 pass（22:26）。**

### 14.3 走行A＝直した後の生成器の自己テスト（22:26:01〜22:32:08・6分7秒）

```
[--lint-provenance] 引く関数の外で作っている所（0件が合格）
  材料の辞書: 0 件
  合計 0 件 → 合格
  T33-f 実測: SampleError: [見本] ADX は印が「使う」＝off_ok の見本は作れない
  T33 実測: 使う 140 種／使わない 116 種／候補に出た種類 138 種／印の指紋 dec5519430b997b0
  T33 指標のオン・オフの印: (a)候補に出ない (b)審査が捨てる (c)戻せば通る (d)順位から外れる (e)指紋が記録に入る (f)「使う」指標に off_ok は作れない
  ❌ T24②: レンジの束が1本も検査を通らない: {…R4: st': 91, …hysteresis…: 6, …: 3}
  ❌ T26: --gate-matrix が不合格（止まるはずのマスが止まらない・または正しい案が通らない）
  ❌ T30: 場面の判定の束つきの案が、包み（validate_drawn）で1本も通らない（20本 試した）
rc_gen_A=1
```

**＝❌ は T24②・T26・T30 の3件だけ（T25 が消えた）。**

### 14.4 走行B＝止める行（3.1 の `raise`）を一時的に `pass` にして走らせた（22:32:42〜22:38:51・6分9秒・設計書 §5 の7）

```
  T33 指標のオン・オフの印: (a)候補に出ない (b)審査が捨てる (c)戻せば通る (d)順位から外れる (e)指紋が記録に入る (f)「使う」指標に off_ok は作れない
  ❌ T24②: レンジの束が1本も検査を通らない: {…R4: st': 91, …: 6, …: 3}
  ❌ T26: --gate-matrix が不合格（止まるはずのマスが止まらない・または正しい案が通らない）
  ❌ T30: 場面の判定の束つきの案が、包み（validate_drawn）で1本も通らない（20本 試した）
  ❌ T33-f: 「使う」指標 ADX に off_ok=True を渡しても止まらない（fail-closed が崩れている）
rc_gen_B=1
```

**＝❌ が 3件 → 4件（T33-f が加算された）。「T33-f 実測」の印字は出ない（止まらなかったので）。**走行の直後に `raise` を元に戻した（Edit・22:39）。

### 14.5 走行C＝材料の辞書を1行 直に書いて走らせた（22:39:35〜22:45:39・6分4秒・設計書 §5 の4＝静的検査が生きている確認）

```
[--lint-provenance] 引く関数の外で作っている所（0件が合格）
  材料の辞書: 1 件  行=[5320]
  合計 1 件 → ★不合格
  T33-f 実測: SampleError: [見本] ADX は印が「使う」＝off_ok の見本は作れない
  ❌ T24②: …／ ❌ T25: --lint-provenance が不合格（…） ／ ❌ T26: … ／ ❌ T30: …
rc_gen_C=1
```

**＝❌ が 3件 → 4件（T25 が戻った・5320行＝一時的に足した行）。**走行の直後にその行を消した（Edit・22:46）。

### 14.6 一時的な行を戻したあとの差分＝設計書の3か所だけ（git diff・22:46）

`git diff --stat`＝**25行 追加・3行 削除**（走行A の前と同じ）。中身＝3.1（`off_ok` の引数・説明文・分岐 6行）／3.2（材料の辞書 → `_mat_fixture(..., off_ok=True)` の1行）／3.3（T33-f の 11行 ＋ 印字の1行）。**一時的な `pass` と `_tmp_lint_c` は残っていない**（差分に出ない）。`py_compile` ✅。

### 14.7 印＝G2（22:47:09〜22:47:30・21秒）

`gen_signal_families.py --verify`＝**✅ 既知答え 11件 全部 期待どおり・印 `g2_pass.json` 指紋 a9dafad0…（対象38件）**。H2 は 22:47 に裏で開始（結果は §14.8）。

### 14.8 印＝H2（22:47:45〜22:52:29・4分44秒）

`leak_causality_diag.py`（全検査）＝**✅ 番人の結果 全部 pass／検査2 の注記なし未来参照 0件／打ち切り再現テスト（1-a・1-b・1-c）の食い違い 0件。印 `h2_pass.json` 指紋 4ee6ed6b8f39dcf3…・2026-09-04 22:52:29・対象22ファイル。**next_step の (0-b-2) を json の値に合わせた（G2 a9dafad0…・H2 4ee6ed6b…）。

### 14.9 ★測れなかったもの・気になるもの（正直に）

1. **恒等 L1・S1 は未測**＝設計↔実装の門は「走らせる .py と impl_file が同じ」ことを求め、この設計書の impl_file は `engine_tuner_gen.py`、恒等の引数は `engine_tuner_exec.py` に在る。同じ理由で M2-C-2 の検収の残りも未測のまま（next_step §6 の129番＝旗を足すか、exec を指す設計書を承認するか＝まこさんが決める）。S2 は ✅ 完全一致（22:26）。
2. **`verify_design_contract.py acceptance.md`（単体の照合）が、実装の前後とも `[FAIL] impl_functions が承認のときから変わっています（設計書 9bdb794b… ／ 凍結 44136fa3…）` を出す。**一方で、実装の Edit（受け入れ条件ゲート）は3回とも通った。`impl_functions` は承認の前後で1文字も変えていない（関数を足しも消しもしていない＝git diff で確認）。**凍結の側（44136fa3…）が何を指しているか（cp19 の凍結が残っているのか、t25 の凍結か）は、土台のファイルを私が開けないので確かめられない。監査か まこさんが見る件。**
3. 走行A の直後に「設計書の §5 に1行 足す」は行わなかった＝承認後に設計書を変えると承認が外れるため、条件は §5 の7・§6 の8 として承認の前に入れた（3回目の承認に含まれている）。


---

## §15 照合 FAIL の原因の切り分け（まこさん指示・最優先・★直していない・調べただけ）

### 15.1 まず記録＝私の最初の説明は外れていた

- 私は §12 で「impl_functions は凍結と違う（再承認で凍結し直す）」と書いた。**再承認を3回 打っても、単体の照合は同じ FAIL（設計書 9bdb794b… ／ 凍結 44136fa3…）を出し続けた。**＝「再承認で直る」は外れ。
- **まこさんの最初の説明も外れていた**（まこさん自身の言葉・2026-09-04＝「私の最初の説明（凍結が古いだけ）も外れていたので、両方 記録に残してください」）＝凍結は「古い」のではなく「空」だった（§15.2）。**まこさんの受理の逐語**＝「切り分けを受理します。凍結の正体が空の辞書だったこと、その原因が approve_impl.sh の「最後の囲みから取る」作りだったことは、今回いちばん重要な発見です」。

### 15.2 凍結の側（44136fa3…）が何かを、開けるファイルの範囲で追った

| 追ったもの | 開けたか | 分かったこと |
|---|---|---|
| `printf '{}' \| shasum -a 256` | 開ける（計算） | **44136fa355b3678a…＝空の辞書 `{}` の sha256 そのもの** |
| `.claude/ratchet/impl_functions_frozen.json`（凍結の本体・sdk 側）| Read tool で開けた（Bash では名前が土台に当たり止まる） | 中身は `_これは何か`・`_作り方`・`_出どころ` の3つの説明の鍵だけ。**impl_functions の関数の一覧が1件も無い**＝照合が `_` で始まる鍵を外すと `{}` になる |
| `acceptance_archive/t25-fixture-off-20260904.frozen.json`（3回目の承認の控えの凍結） | Read tool で開けた | 同じ＝説明3つだけ・367 バイト |
| `acceptance_archive/impl-lock-fix-cp19-20260904.frozen.json` | ls で大きさだけ | 367 バイト＝同じ中身の見込み（cp19 は impl_functions が本当に `{}` だったので、これは正しい） |
| `.claude/state/acceptance.approved`・`design_approved.json` | **Bash では開けない**（土台ゲート＝名前が出た瞬間に止まる）。ls の時刻＝22:24 | 承認は3回とも入っている（Edit が通ったことが証拠） |

**＝凍結には、3回とも「空」が書かれた。私の設計書の impl_functions（65件・9bdb794b…）は1回も凍結されていない。**

### 15.3 なぜ空が凍結されたか（承認スクリプトを Read tool で読んだ＝直していない）

`approve_impl.sh` の 62〜73行＝設計書の中の ```json の囲みを**全部** 集め、`impl_file` を持つ辞書を見つけるたびに `obj` を上書きする（`break` が無い）＝**最後の1つが勝つ**。
私の設計書には `impl_file` を持つ json の囲みが **2つ** 在る＝§10 の DESIGN_CONTRACT（275行）と、**§12 の SPEC（445行・`--write --dry-run` の書き出しをそのまま貼ったもの・impl_functions を持たない）**。承認スクリプトは §12 の SPEC を `obj` にし、`obj.get("impl_functions") or {}`＝**空を凍結した**。
**cp19 の設計書では impl_functions が本当に空（`{}`）だったので、凍結の中身が偶然 同じ（44136fa3…）になった＝「再承認しても変わらない」ように見えた本当の理由。**

### 15.4 実装のゲートと、単体の照合が、それぞれ何と何を比べているか（1行ずつ）

| 仕組み | 何と何を比べるか | impl_functions の凍結を見るか |
|---|---|---|
| ① `require_acceptance_before_impl.sh`（Write/Edit の門・3回とも通した） | (a) 設計書の中で **最初に** `impl_file` を持つ json（＝§10）の**形**（impl_functions が空でないか・must_use・spec_lists・generated_from・「塞げないもの」・Q5 の5件・完成の条件の表の欄） (b) 設計書の sha256 と `acceptance.approved` (c) 編集先が TARGET に在るか | **見ない**（凍結ファイルを1度も読まない） |
| ② `verify_design_contract.py <設計書>`（単体の照合＝走らせる門 `require_design_contract_before_run` も同じ関数を呼ぶ） | 設計書の `DESIGN_CONTRACT` の目印で取り出した json（§10）の impl_functions と、**`ratchet/impl_functions_frozen.json`** の中身（承認スクリプトが書いたもの） | **見る**（凍結が空なので 9bdb794b… ≠ 44136fa3… で FAIL） |
| ③ `approve_impl.sh`（承認・まこさんが打つ） | 設計書の json の囲みのうち **最後に** `impl_file` を持つもの（§12 の SPEC）から impl_functions を取り出して凍結に書く | **書く側**（今回は空を書いた） |

**＝①は「最初の impl_file の囲み」、③は「最後の impl_file の囲み」、②は「DESIGN_CONTRACT の目印の後ろの囲み」を見る。同じ設計書に impl_file の囲みが2つ在ると、①が通した中身と③が凍結した中身が別物になり、②が食い違いを出す。**

### 15.5 影響と、この記録の扱い

- **走らせる門**（`require_design_contract_before_run`）は②を呼ぶので、`engine_tuner_gen.py` を「確認の旗（--selftest 等）以外」で走らせると止まる状態が続いている（例＝`--lint-provenance` 単体）。今回の実測では、自己テストは確認の旗なので走れた。
- **直していない**（まこさん指示「直そうとしないでください」）。直すなら別の設計書（案＝承認スクリプトが DESIGN_CONTRACT の目印で取る／または SPEC の json から `impl_file` を外す）。
- **T25 の設計書そのものは、この件の影響を受けていない**＝①の形の検査と承認の指紋は通っており、実装した3か所は設計書どおり（§14.6 の git diff）。


---

## §18 過去の承認がどこまで空だったかを数えた（まこさん指示の3・調べるだけ・直していない）

**数え方**＝`acceptance_archive/*.md`（`.actual.md` を除く 121本）を `grep -n -m1` で1本ずつ見て、DESIGN_CONTRACT の目印の行（見出し・その語だけの行・囲みの見出し）と SPEC の目印の行の、最初の行番号を比べた。凍結は `ls -la` の大きさと、Read tool で開いた中身で見た（367 バイト＝説明の鍵3つだけ＝空）。

### 18.1 SPEC の節が DESIGN_CONTRACT より後ろに在る設計書＝**21本**（控えの連番 .01 を含む・SPEC の目印が在る 24本のうち）

| 設計書（iter） | DC の行 | SPEC の行 | 凍結ファイル | 凍結の中身 |
|---|---|---|---|---|
| t25-fixture-off-20260904.md | 269 | 437 | 在る（367 バイト・22:24） | **空**（Read tool で確認） |
| t25-fixture-off-20260904.01.md | 259 | 427 | （.01 は前の版の控え・凍結は上と同じファイル） | — |
| indicator-switch-20260902.md（★1回目の承認で t25 の中身に上書きされたもの） | 248 | 416 | 在る（367 バイト・22:16） | **空**（Read tool で確認） |
| exit-fire-forms-20260825 | 194 | 237 | 無い | 凍結の仕組みが無かった（2026-09-03 に新設） |
| four-elements-gate-20260824 | 191 | 204 | 無い | 同上 |
| four-elements-gate-v2-drawn-only-20260825 | 237 | 252 | 無い | 同上 |
| gen-minimize-loss-20260826 | 152 | 185 | 無い | 同上 |
| m2-b-2b-range-laws-20260830 | 11 | 171 | 無い | 同上 |
| m2-b0-law-reader-20260830 | 9 | 156 | 無い | 同上 |
| m2-b3-audit-fixes-20260901 | 8 | 85 | 無い | 同上 |
| purpose-gate-add-only-20260829 | 7 | 106 | 無い | 同上 |
| regime-build-callers-and-usable-groups-20260827 | 225 | 261 | 無い | 同上 |
| regime-label-oneway-20260829 | 9 | 117 | 無い | 同上 |
| regime-label-synthetic-20260829 | 9 | 114 | 無い | 同上 |
| selftest-standalone-20260824 | 112 | 127 | 無い | 同上 |
| tidy-next-step-20260828 | 182 | 214 | 無い | 同上 |
| unapproved-four-elements-gate-v58-20260825 | 234 | 247 | 無い | 同上 |
| unordered-scan-scope-20260826 | 330 | 371 | 無い | 同上 |
| 67da88ef9ca8 | 5 | 142 | 無い | 同上 |

（SPEC が DC より**前**に在る3本＝exit-fire-forms-probe-fix-20260826・forbidden-check-auto-20260826・req-map-r17-20260826。どれも凍結の仕組みの前。）

### 18.2 凍結ファイルが在る承認＝6本（凍結の仕組みは 2026-09-03 の cp14 B-1 から）

| 凍結ファイル | 大きさ | 中身 | その設計書に SPEC の節 | 空の理由 |
|---|---|---|---|---|
| impl-lock-fix-cp15-20260903.frozen.json | 908 | 関数の一覧あり（ls の大きさから・開いていない） | 無し | — |
| impl-lock-fix-cp16-20260903.frozen.json | 1,380 | 同上（開いていない） | 無し | — |
| impl-lock-fix-cp17-20260903.frozen.json | 964 | **関数の一覧あり**（Read tool で開いた＝run_breaks.py 9件・gen_audit_request.py 20件） | 無し | — |
| impl-lock-fix-cp19-20260904.frozen.json | 367 | **空**（Read tool で開いた） | 無し | 設計書の impl_functions が本当に `{}`（.sh だけ触る回）＝**正しい空** |
| indicator-switch-20260902.frozen.json（t25 の1回目） | 367 | **空** | **在り（DC より後ろ）** | **承認スクリプトが SPEC の囲みから取った＝誤った空** |
| t25-fixture-off-20260904.frozen.json | 367 | **空** | **在り（DC より後ろ）** | 同上 |

**★結論（数字だけ）**＝凍結の仕組みが在る6本のうち、空は3本。そのうち「誤った空」（SPEC が後ろに在って承認スクリプトが空を取った）は **2本＝どちらも今日の t25**。cp19 の空は正しい空。**それより前の18本（SPEC が後ろ）は凍結の仕組みが無かったので、空だったかは存在しない**（比べる相手が無い）。
**開けなかったもの**＝無し（凍結は6本とも Read tool で開けるが、cp15・cp16 の2本は大きさだけで判定し、中身は開いていない）。`.claude/state/acceptance.approved`・`design_approved.json`・`verify_tool.approved` は Bash では名前が出ると止まるので、ls の時刻だけ見た。
**限界**＝目印の行は grep の1件目で見た。見出しの文の中で「SPEC」「DESIGN_CONTRACT」に触れただけの行を拾っている可能性が在る（照合の道具の `extract_block` と同じ判定ではない）。数え直すなら道具の関数を呼ぶ必要が在るが、python -c は門が止めるので、この回は grep で数えた。


---

### 19.1 承認（2回目・23:24）のあとの実測（★設計書 §5 の1〜4・全部 標準出力そのまま）

- **凍結**＝`ratchet/impl_functions_frozen.json` 2,406 バイト・関数の行 **100件**（`grep -c` ＝ `<モジュール直下>` を含めて 101件・Read tool で開いた中身は §19 の冒頭と同じ）。**空ではない。**

```
python3 engine_tuner_exec.py --identity-l1（23:25:18〜23:25:24）
[恒等 L1] 現行 L1（run_long_support）: 367 行 md5 96a9102ec8a34f94cf01e9e463f6aade
[恒等 L1] レシピ実行器: 367 行 md5 96a9102ec8a34f94cf01e9e463f6aade → ✅ 完全一致
[恒等検収 L1 まとめ] ✅ 全部一致

python3 engine_tuner_exec.py --identity-s1（23:25:36〜23:25:53）
[恒等 S1]現行（run_continuous_v11・里程標1 構成）: 6569 行 md5 18b3d31a5fe71c4a4b5f83cf1771a46c
[恒等 S1]レシピ実行器: 6569 行 md5 18b3d31a5fe71c4a4b5f83cf1771a46c → ✅ 完全一致
[恒等検収 S1 まとめ] ✅ 全部一致

python3 engine_tuner_exec.py --identity（23:26:27〜23:26:34）
[恒等1 separate] 現行 S2: 165 行 md5 7b01f51b5a9b29b3c05a7b340c203ba1
[恒等1 separate] レシピ実行器: 165 行 md5 7b01f51b5a9b29b3c05a7b340c203ba1 → ✅ 完全一致
[恒等検収まとめ] ✅ 全部一致

python3 verify_design_contract.py acceptance.md
  [PASS] 自己チェック配線あり: run_identity／run_identity_l1／run_identity_s1／identity_l1_recipe／identity_s1_recipe
  [INFO] engine_tuner_exec.py: 差分がゼロ（commit 済み）＝照合B だけをファイルの中の全関数（100件）と行いました。照合A は判定できません
  [PASS] must_use main: 全部あり ['run_identity_l1', 'run_identity_s1']
RESULT: PASS（設計通り）
```

**＝3本とも 2026-08-05 以来の基準値（7b01f51b…／96a9102e…／18b3d31a…）と同じ。M2-C-2 の設計書 §5 のテスト5（恒等3本）が、これで3本とも測れた。**
- **次の設計書（恒等 L1・S1 用）での回り道**＝★最初に試した「SPEC の json から `impl_file` を外す」は**使えなかった**＝`--diff` の入口（`verify_design_contract.py`:1622）が SPEC の impl_file を読んで `FileNotFoundError: impl_file の欄が空` で落ちた（23:15 に実測）。**使った回り道＝SPEC の節を DESIGN_CONTRACT の節より前に置く**（③が最後に見る impl_file の囲みが DESIGN_CONTRACT になる。②は目印の行＝見出しで取り出すので順番に影響されない・`verify_design_contract.py`:141-236）。**道具は1文字も変えない。**承認のあとの単体の照合が PASS になるか、凍結の関数の件数が 0 でないかで確かめる。 設計書 §6 の完成の条件5つのうち、私の実測で数字が出たのは 1（7つのテストのうち 生成器の5つ＝T33 pass・印の改変検出＝--verify ✅・印を消すと止まる＝exec :168）・2（S2 だけ一致・L1/S1 は未測）・3（候補に出た種類 138）・4（手書きの行 0＝`built_by` の欄）・5（H2・G2 pass）。**「完成」かどうかは私が言わない** |

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-XX-XX_<task>_cpN_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言** (混合型: 数値型 + コード型 + 文書型 / 該当する型を明示)
2. **Step 0 指摘前提確認** (事実データ verify + spec 文言 verify)
3. **観点 ①〜⑦ + Q1-QN の所見** (各観点・各 Q に対し「数値根拠ある断言」or「データ不足 (理由)」)
   - 観点 = PASS / FAIL 明示
   - Q = 業界整合 / 改善余地 N 件 明示
4. **外部検索結果サマリー** (検索クエリ + 主要発見 5-10 件・URL or 論文出典)
5. **総合判定**:
   - Verdict: GO / NO-GO / PIVOT / OTHER
   - 業界基準・学術根拠を伴う根拠
6. **改善方向性** (具体提案 3-7 件・優先度明示 Critical/Major/Minor)
7. **CC プロセス欠陥対策** (cc_role §1.4.6 改訂提案・該当があれば)

---

## 必ず守ること (auditor 守則)

- **目標 ($1,900/月) 達成可能性判定は対象外**の場合は明示
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (auditor_template L20)
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- **外部検索は WebSearch / WebFetch ツールで必ず実施**
- 内部文書だけでなく、トレードについての外部認知 (Crypto futures algo trading の業界実情) を踏まえる

---

依頼書終わり。

---

## 載せなかったもの（全部・ファイル名と節番号・なぜ載せなかったか）

| # | 載せなかったもの | なぜ載せなかったか |
|---|---|---|
| 1 | `session_worklog_20260904.md` §1〜§6（80〜81回目＝強制の工事 cp13〜cp19） | まこさん指示の貼る範囲（§8・§14・§15・§18・§19.1）の外。強制の工事は cp19 で終了済み |
| 2 | 同 §7（必読と ToDo） | 同上。作業の手順の記録で、監査の材料ではない |
| 3 | 同 §9（自己テストの ❌4件の切り分け＝T24②・T25・T26・T30 の原因） | 貼る範囲の外。★T25 の原因は §14 に、T24②・T26・T30（M2-E・未着手）は next_step §6 の128番に在る |
| 4 | 同 §10（H2 の印の1回目の取り直し）・§11（判断待ちの一覧） | 貼る範囲の外。印の最終の値は §14.7・§14.8 に在る |
| 5 | 同 §12・§13（T25 の設計書を書いた経緯・まこさんの条件） | 貼る範囲の外。設計書そのものは着手前必読の3 |
| 6 | 同 §16・§17（恒等 L1・S1 用の設計書を書いた経緯・コミット） | 貼る範囲の外。設計書そのものは着手前必読の4 |
| 7 | 同 §19 の冒頭（19.1 の前＝凍結の件数と、見出しの穴 L） | 貼る範囲が §19.1 だったため。★凍結の件数（101件）と、見出しに目印の語を書くと契約が空と読まれる件（L）はここに在る＝監査が見るなら開く |
| 8 | `session_worklog_20260902.md`（78回目＝M2-C-2 の実装と、印を作り直さなかった経緯） | 貼る範囲の外。M2-C-2 の実装の経緯はここ |
| 9 | `.claude/state/acceptance.md`（いま在る設計書＝恒等 L1・S1 用・承認済み） | 控えが着手前必読の4に在る（同じ中身） |
| 10 | 生成器の自己テストの生ログの全文（走行A・B・C の各 50行） | §14.3〜14.5 に「lint・T33・❌ の行」だけを写した（CC が抜粋した＝まこさん指示の「抜粋しない」は節に対する指示と読んだ。生ログの全文は `/private/tmp/claude-501/…/tasks/` の一時ファイルに在り、セッションが終わると消える） |

★上の10件のほかに、省いたものはありません。

---

## まこさん向け呼びかけ例文 (新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
.claude/audits/inputs/2026-09-05_m2c2_indicator_switch_cp20_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。
