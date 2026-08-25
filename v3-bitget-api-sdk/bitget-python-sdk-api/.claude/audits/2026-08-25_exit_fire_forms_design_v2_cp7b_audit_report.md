# 【監査報告】実行器の出口の発火条件を「形ごとの評価」にする設計 v2（97番・`.claude/state/acceptance.md`・cp7 NO-GO の反映版）cp7b

- 監査日: 2026-08-25
- 依頼書: `.claude/audits/inputs/2026-08-25_exit_fire_forms_design_v2_cp7b_audit_request.md`（176行・ハッシュ値の先頭16桁 `2d6d55cc4ece07b4`）
- 反映元: `.claude/audits/2026-08-25_exit_fire_forms_design_cp7_audit_report.md`（274行・`5fbd7ce1bff68332`）
- 監査区分: cp7b＝**設計 v2 だけの監査・実装前**（実装は1行も入っていない＝exec・gen のハッシュ値が cp7 と同じ）
- 監査の体制: auditor セッションの CC が Plan サブエージェントを cold start で起こし、**返ってきた所見を auditor 側の CC が実物のコードと自分の再現で1件ずつ裏取りした**（下の「8. 二重の確認の記録」）
- **Verdict: OTHER＝条件つき GO**（下の改善1・改善2 を設計書に追記した版を承認する。追記なしで承認するなら、設計書自身の基準「直した先に黙って別物を残さない・fail-closed」に照らして NO-GO）
- 指摘の件数＝**Critical 0件・Major 2件・Minor 5件**

---

## ★まこさんへ｜3行の結論

1. **cp7 の8件は全部、意味を変えずに反映されています（8/8）。**cp7 が見つけた5件の「検査が通す × 実行が黙って別物」（strict・状態の pre・not・ref・混在）は、v2 の検査6つと `not` の追加で全部 止まります（実物の関数に当てはめて確認。直す前は5件とも「通った」を私が実測）。
2. **新しい穴が1件 残ります（Major）**＝材料が「列」なのか「玉の状態」なのかを決める規則が、検査（`_material_name`:514-533 の優先順）と実行（`_ev`:2094 の `m.get("state")`）で違います。1つの材料に種別の鍵を2つ書くと、検査は列として通し、実行は玉の状態を評価します（私の実測＝legacy_col＋state・geo＋state の2通り）。露出＝生成器はこの形を作りません。直すのは検査1行＋設計書の3か所の書き方です。
3. **完成の条件 C6（恒等）が「空の成立」を許します（Major）**＝走らせるレシピが固定されておらず、付け替える枝が1回も発火しなくても「一致」になります。直し＝レシピの保存とハッシュ値・付け替える枝の発火件数 ≥1 を条件に足す。

**いま実害は出ていません**（歯止め＝探索の本走をしない・net ゼロ）。**改善1・2 を足せば承認に進める内容です。**

---

## 1. Step -1 監査対象の型宣言

**文書型（設計書 v2）・実装前。**

| 型 | 対象 | 行数 | 何を見たか |
|---|---|---|---|
| 文書型（監査対象） | `.claude/state/acceptance.md`（v2） | 279 | §1b の対応表（ア〜キ・:27-37）／§2 の実物の表（:41-79）／やること5件（:88-98）／完成の条件 C1〜C13（:100-116）／§7 入っていないもの (a)〜(k)（:122-136）／SPEC |
| 文書型（反映元） | `.claude/audits/…_cp7_audit_report.md` | 274 | §6 の8件（改善方向性）・§3 の実測①〜⑩ |
| コード型（直す対象・読んだだけ） | `scripts/priority_rebuild/engine_tuner_exec.py` | 4,004 | `FORM_SPEC`・`SIDES`・`_walk`・`_material_name`・`_check_value`・`_check_cond`・`_side_cmp`・`_vnum`・`_vnum_q`・`_col_array`・`_eval_cond`・`validate_recipe` の出口の検査・`_collect_fire_cols`・`_exit_fire_ok`・`_md5_trades`・`run_identity`／`_l1`／`_s1`・`selftest` |
| コード型（今回は触らない・読んだだけ） | `scripts/priority_rebuild/engine_tuner_gen.py` | 5,402 | `strip_marks`・`_state_cond`・`_exit_indicator_cond`・`_cond_keys`／`needed_qkeys`・`run_trial_guarded`・`synth_df`・T6 |
| データ型 | `.claude/ratchet/exit_families_rules.json`／`recipes/identity_s1_legacy.json` | — | 出口の枝19件／恒等レシピ S1 の出口 fire の材料 |
| 文書型（経緯） | `.claude/state/session_worklog_20260825.md` §32・§33 | — | 起案 CC の裏取りと v2 の記録 |

**独立性**＝Plan サブエージェントには依頼書のパス・必読5件・Q1〜Q4・外部検索の要請だけを渡した。起案 CC への確認質問は0回。リポジトリのファイルは1つも書き換えていない（git HEAD `68360c6`）。

---

## 2. Step 0 指摘前提確認

### 2-1. 事実データの verify（auditor 側の CC が自分で実測・2026-08-25）

| ファイル | 依頼書の行数 | 実測 | 依頼書のハッシュ値 | 実測 | 判定 |
|---|---|---|---|---|---|
| `.claude/state/acceptance.md`（v2） | 279 | **279** | 8eff7af3b2c16ada | **8eff7af3b2c16ada** | ✅ 一致 |
| `engine_tuner_exec.py` | 4,004 | **4004** | 8a606184d6ed4cf8 | **8a606184d6ed4cf8** | ✅ 一致（cp7 と同じ＝未実装） |
| `engine_tuner_gen.py` | 5,402 | **5402** | 6bf0bc251d9ea521 | **6bf0bc251d9ea521** | ✅ 一致（cp7 と同じ） |

### 2-2. spec 文言の verify

- 依頼書「§1b からの複写」（依頼書:83）＝`acceptance.md`:37 と逐語一致。
- v2 §1b の表（:29-35）の7件（ア〜キ）＝cp7 §3 の実測⑤〜⑩・Q3 #1 と1件ずつ対応。
- worklog §32（:463）・§33（:492）は見出しとして実在。
- 依頼書の行番号＝関数の定義行を grep で照合＝`_material_name` :485・`_check_value` :642・`_check_cond` :746・`_side_cmp` :1471・`_vnum` :1482・`_vnum_q` :1494・`_col_array` :1575・`_md5_trades` :2529・`run_identity` :2537・`run_identity_l1` :2729・`run_identity_s1` :2866／gen `strip_marks` :813・`_qspec` :2352・`needed_qkeys` :2396・`_cond_keys` :2404・`run_trial_guarded` :2739・`synth_df` :3386。**案1本を走らせる関数の except は :2760**（依頼書・v2:70・v2:31・worklog §32 は :2759＝1行ずれ。cp7 の :2760 が正しかった）。
- 出口の表＝19枝／REVERSE_IND（cross・level・slope・diff・resting）／BREAKOUT（level・slope・diff・on_close）／状態だけの枝7件・条件11個＝v2:76 と一致（cp7 で私が数えたものと同じ）。

### 2-3. 承認の状態

- `acceptance.approved`・`design_approved.json` の指紋＝`abff2bce…`（60回目の版）。v2 の指紋＝`8eff7af3…`＝**未承認**（依頼書・v2:5 と一致）。

---

## 3. 観点 ①〜⑦ ＋ Q1〜Q4 の所見

### 観点 ①〜⑦

| 観点 | 判定 | 根拠（実物の行番号・私の実測） |
|---|---|---|
| ①統計学的妥当性 | **PASS** | v2:120「この設計は新しい数字を1つも作らない」＝閾値・分位・net の主張ゼロ。C1〜C13 は全部 機械の真偽で決まる。注記＝C2 の「5形×na 2通り＝10組」のうち、cross は na=pass を無視する（**私の実測**＝最終バー NaN・na=pass → False・:1719 `fin &`）・candle_dir は NaN を持たない＝**判別できる組は8**。 |
| ②リスク管理 | **FAIL（Major 1件・追記で消える）** | cp7 の5件は v2 の (c)(d)・やること2・(e)(f) で全部 止まる（Q2）。**新しく1件**＝材料の種別を決める規則が検査と実行で違う（Q2 新1・私の実測あり）。露出＝生成器は作らない（cp7 の Critical と同じ露出ゼロ級）。歯止め（v2:16）は妥当。 |
| ③認知バイアス | **PASS（注記1件）** | v2 は §7 に入れないもの11件・§1b に v1 が外していた7件を明示＝矮小化の型（#13）に当たらない。注記＝v2:34「恒等ハーネス（:2605）の出口の材料も state だけ」・:58「★指標の材料は0件」は **cp7 の主張を写した誤り**＝S1 の恒等レシピ（`recipes/identity_s1_legacy.json`）の出口 fire には **legacy_col の指標の材料が3枝（MTFCUT・V59DOWN・V59FLAT）在る**（私の実測・Q4 #2）。worklog §32:474 の裏取りは exec.py だけを grep していた。誤りの向きは有利側（恒等の網は書いてあるより広い）。 |
| ④ソフトウェア工学 | **PASS（方向は正・注記1件）** | `_eval_cond` への一本化・canonical JSON の鍵・numpy の型は RecipeError（**私の実測**＝`json.dumps(np.int64)` → TypeError／`np.float64` は通る＝v2:92 の対処は要る）・fail-closed の検査6つ＝正しい。注記＝**材料の種別の判定が2か所に残る**（検査＝`_material_name` :514-533 の優先順 legacy_col→geo→state→time→family／実行＝`_ev` :2094 の `m.get("state")`）＝v2:83 が戒める「同じ式を2か所に持つと片方が腐る」の型が、材料の種別で残る。 |
| ⑤再現性 | **FAIL（Major＝C6 のレシピが固定されていない）** | C6(i)(iii)（v2:109）は合成データ（`synth_df(3000, seed=7)`）と種は書いたが、**走らせるレシピそのもの（JSON・ハッシュ値・どこに保存するか）が書いていない**＝直す前後で「同じレシピ」を走らせた証拠を出せない。ハッシュの取り方も未指定（実物には `_md5_trades`:2529-2534＝`to_csv` の md5 が在る）。C3(ii)・C8・C12・C13 は再現できる（種・設定・鍵1つ・直呼びが書いてある）。 |
| ⑥実行プロセス | **PASS** | 手順「実物を読む → 量を出す → 設計書 → 監査 → 承認 → 実装」（v2:15）を守っている。**恒等の基準値を実装の前に測る（やること5・v2:96）**＝golden master の標準手順と一致（§4）。審判整合 D（:141）・H の照合（:142）・疑似シミュ由来の固定値ゼロ（:120）あり。cp7 の外部検索を §3④ に取り込んだ（:86）。 |
| ⑦主エージェントバイアス | **PASS（注記1件）** | cp7 の8件を「意味を変えずに」反映（Q1）。監査の主張を機械的に写した箇所が1件（③の注記＝「state だけ」）＝主張が及ぶ範囲（json の恒等レシピ）まで自分で確かめていない。結論への影響は無い。 |

### Q1 — cp7 の8件は、意味を変えずに反映されたか

**判定＝一致（8件とも ①反映されている）。**

| cp7 §6 | cp7 の要求（要旨） | v2 の該当（逐語・行） | 判定 |
|---|---|---|---|
| Critical-1 | 検査 (c)＝slope/slope_avg/diff の strict を拒否。C1 に strict の実測。入口の穴を next_step に新番号 | v2:94 (c)「form が slope・slope_avg・diff で side が above_strict／below_strict なら拒否（101番が直るまで）」／:104 C1「strict…は検査（G6）で拒否される」／:110 C7「slope の above_strict／diff の below_strict」／next_step.md:204 に **101** 実在 | ①反映 |
| Critical-2 | 検査 (d)＝state＋pre を拒否・pre_ok=False の形＋pre を拒否。C7 に偽レシピ | v2:94 (d)「材料に state が在って pre も在れば拒否／pre_ok=False の形の材料に pre が在れば拒否」／:110 C7「state＋pre／slope（pre_ok=False）＋pre」／next_step.md:208 に **105**（入口側） | ①反映 |
| Major-3 | `_ev` に not を足すか validate で拒否。§4-2 に明記 | v2:93 やること2(ii)「木の歩きに not を足す…入口の `_eval_tree`（:1765）と同じ意味」／:116 C13「not が評価される…KeyError が出ない」（評価する側を選んだので C7 でなく C13＝意味は同じ） | ①反映 |
| Major-4 | C6＝付け替える道（level の枝）を固定の種の合成データで直す前後 比較・--identity 3本・生成関数と種を条件に | v2:109 C6 (i)「付け替える道＝BREAKOUT on_close・REVERSE_IND resting…`synth_df(3000, seed=7)`」(ii)「--identity L1・S1・S2」(iii)「触らない道」／:96 やること5「基準値を実装の前に測る」 | ①反映（残る穴＝レシピの固定と空の成立＝Q3） |
| Major-5 | C8 を exec と gen の2本に分ける。C3 に種・設定と「cross の案 ≥1本」 | v2:111 C8＝exec と gen の2本＋T6・18マス・--lint-provenance／:106 C3(ii)「`synth_df(3000, seed=7)`・seed=11・第1段10本・第2段6本…cross を含む案が ≥1本…（0本なら未判定）」。実物＝gen:3807 `df = synth_df()`・:3852-3854 `trials1=10, trials2=6, top_k=2, seed=11` と一致 | ①反映 |
| Major-6 | C11 の文を直す（「入口と同じ on_close」と書かない・resting の順序は範囲外＝新番号） | v2:114 C11「配列方式は新しい未来参照を増やさない…これは H2 全体の担保ではない＝resting の枝が…既存の作りで、この設計の範囲外（102番）」／next_step.md:205 に **102**。v2 全文で「入口と同じ on_close」は v1 の引用（:35）だけ | ①反映 |
| Major-7 | 分位の直呼びの条件。§7(a) の範囲を限定。slope の th の鍵の無さを next_step に | v2:115 C12／:126 §7(a)「level・band・diff・cross(列1本) の分だけ」／:134 §7(i)／next_step.md:206 に **103** | ①反映 |
| Minor-8 | 混在は拒否・ref は拒否・12→11・:45 の行番号・numpy の型 | v2:94 (e)(f)／:76「条件11個」／:67「:1712-1715」／:92「numpy の型…明示の RecipeError」 | ①反映 |

### Q2 — 直した先に「検査が通す × 実行が黙って別物」が残っていないか

**判定＝cp7 の5件は全部 止まる（静的判定）／新しい穴 1件（Major）＋軽微 3件。**

**直す前の実測（Plan agent のヒアドキュメント・出口の文脈 `where="exit枝TEST"`・lane legacy・逐語。★印は私も同じ結果を実測）**

```
  validate (a) band in exit -> 通った★ / (a) slope_avg -> 通った / (a) streak -> 通った / (a) hysteresis -> 通った
  validate (b) state×slope -> 通った★ / (b) candle_dir に state 材料 -> 通った
  validate (c) slope above_strict -> 通った★ / (c) diff below_strict -> 通った
  validate (d) state+pre ts_max -> 通った★ / (d) slope(pre_ok=False)+pre -> 通った★ / (d) cross(pre_ok=False)+同単位pre -> 通った
  validate (e) value に ref -> 通った / (e) slope の th に ref -> 通った
  validate (f) 混在 diff(RSI, state) -> 通った / (f) 混在 diff(state, RSI) -> 通った
  validate _walk(not) の条件数 -> 1★
  実行: not(hold_min≥60) -> 例外 KeyError: 'if'★
  実行: state+pre ts_max -> True / pre なし -> True★                     ← pre が黙って無視
  実行: 混在 diff(state mfe_pct=0, RSI=90) ≥5 -> False / diff(RSI=90, state) ≥5 -> True   ← 2本目が黙って無視・順で結果が変わる
  _eval_cond slope side=above_strict 下がる列/上がる列 -> (True, False)★   ← 逆
```

**cp7 の5件が v2 で止まるか（実物の関数に当てはめた静的判定）**

| 件 | v2 の手当て | 実物の関数での成立根拠 | 判定 |
|---|---|---|---|
| strict | (c) 拒否 | `validate_recipe` は出口 fire の条件を `_walk`（:1361）で全部 集めて `_check_cond`（:1363）に通す＝(c) を「:1359-1363 の並び」に足せば、not の内側も `_walk`:261 が降りるので漏れない。level の strict は `_side_cmp`（:1471-1479）で正しい | **止まる** |
| 状態の pre | (d) 拒否 | `_pre_of`（:425）＝`m.get("pre")` だけ＝pre の書き場所は1つ。`_material_name`:493-513 が pre の形を検査するので (d) は「在るか」を見るだけでよい | **止まる** |
| not | `_ev` に not | `_walk`:255-262 は not を持ち `_check_not_node`:231-242 が二重否定・余分な鍵を拒否済み＝`_ev` に `"not" in node` を足せば `_eval_tree`:1765-1766 と同じ意味になる | **止まる** |
| ref | (e) 拒否 | `_check_value`:659-672 が ref を「知っている鍵」として通す（出口でも）。ref の在りか＝value 直下・lo・hi・th＝v2:94 (e)「value（lo・hi・th を含む）」で網羅 | **止まる** |
| 混在 | (f) 拒否 | 材料2本の形＝diff・touch・cross。`_material_name` が種別を返す（:527 state）ので「state と 非 state が混ざる」は機械で判定できる | **止まる** |

**新しい穴（cp7 が見ていないもの）**

| # | 何 | 実物の行・実測（逐語） | 日本語の説明 | 重さ |
|---|---|---|---|---|
| **新1** | **材料の「種別」を決める規則が、検査と実行で違う**＝検査は `_material_name` の優先順（:514 legacy_col → :518 geo → :523 state → :528 time → :533 family）／実行の `_ev` は :2094 `nm = m.get("state")` だけ／v2 のやること1・(b)(d)(f) も「材料に state」と書くだけで、どの関数で決めるかを書いていない | **私の実測**（legacy レーン・hold_min=295・RSI 最終値 90・閾値 n=100）＝`材料 {"legacy_col": "RSI14__5m", "state": "hold_min"} → 検査の種別=('legacy_col', 'RSI14__5m') ／ fire_cols の鍵=[] ／ 実行(_ev)=True ／ 入口の評価器 _eval_cond=False`。＝**検査は「指標の列」として通し、実行は「玉の状態」を評価する**。v2 の (b)(d)(f) はこの材料を拒否しない（level・pre なし・1本）。**★起きる組み合わせ（私が4通り×2レーンで実測）＝legacy_col＋state（恒等レーンだけ。探索レーンは :515 の G6 で止まる）と geo＋state（どのレーンでも）の2通り。time＋state・family＋state は検査も state を先に見る（:523 が :528・:533 より先）ので一致する** | 1つの材料に「列の名前」と「玉の状態の名前」を両方 書くと、検査は列だと思って通し、実行は状態だと思って動く。生成器は作らないが、手書きのレシピで黙って別物になる | **Major**（検査1行で消える＝改善1） |
| 新2 | 玉の状態の条件に分位（threshold_q）を書くと検査は通り、実行は `_vnum`（:1491）で止まる | **私の実測**＝`validate state+threshold_q → 通った`／`実行 → RecipeError 値を解決できない {'threshold_q': 'q50'}`。加えて gen `needed_qkeys`:2458-2461 は出口の条件も歩くので `_qspec`（:2352〜）が state の名前を列名として解決表に入れようとする | 状態の条件に「分位」を書けてしまうが、走らせた瞬間に止まる（黙ってはいない＝fail-closed）。止まる理由の文が誤解を招く | Minor |
| 新3 | candle_dir に材料を書いても検査は無視（:835-836 `mats = []`）し、v2 の後は `_eval_cond`:1674-1677 も材料を読まない | Plan agent の実測＝`validate candle_dir に指標材料 → 通った`／`_eval_cond candle_dir 材料つき → True`（陽線）。:835-836 は私が Read で確認 | ローソクの形に材料を書いても、黙って捨てられる（結果は正しいローソク判定）。害は無いが「書いたものが無視される」型 | Minor |
| 新4 | hysteresis・入れ子形（streak 等）を出口 fire に置くと、いまは検査が通り実行が G6 の誤った理由で止まる | Plan agent の実測＝`validate hysteresis in exit → 通った`／`実行 → RecipeError [G6] 材料の2軸（family×tf）が欠けている: {}` | v2 の (a)（exit_ok に無い形は拒否）が正しい理由で止める＝v2 で消える | 消える |

**FORM_SPEC の他の欄が出口で意味を持つか**＝`needs_side`＝:783 は出口の文脈でも効く／`band`＝(a) で消える／`state_free`＝`forms_where("state_free")` の呼び出し **0件**（私が数えた）＝意味を持たない／`slope_n`＝:757 の範囲検査が出口でも効く（lane≠legacy）／`trigger_ok`＝出口は role env 固定（:1363）＝無関係。`any`・`if-then` の中の混在＝`_ev` は葉ごとに評価（:2106-2110）・`_eval_tree` も同じ（:1767-1779）＝葉の中の混在は (f) が止め、葉どうしの混在は正しく評価される＝穴なし。

### Q3 — 完成の条件 C1〜C13 は目的を担保し、書いてあるとおりに測れるか

**判定＝食い違い 5件（①目的に届かない穴 2件・②測れない／曖昧 3件）。**

| # | 条件（逐語・行） | 判定 | 所見 |
|---|---|---|---|
| C6 | :109「(i) 付け替える道＝指標の level の条件を持つ出口の枝…を含むレシピ（synth_df(3000, seed=7)）(ii) --identity L1・S1・S2 (iii) 触らない道」 | **①穴＋②曖昧** | (1) **レシピが固定されていない**＝(i)(iii) のレシピを誰がどう書き、どこに保存し、ハッシュ値を何で取るかが無い（実物には `_md5_trades`:2529-2534 が在る）。(2) **枝が1回も発火しなくても恒等は成立する（空の成立）**＝「付け替える道の枝（BREAKOUT_CUT／REVERSE_IND の理由）が売買記録に ≥1 件」の条件が無い。§4 の文献（Wikipedia／Codurance）「golden master は正しさを保証せず、変化を検出するだけ」＝通らない道の記録は変化を検出しない。(3) 好材料＝(ii) の S1 は出口 fire に指標（legacy_col）の level が3枝 在る（Q4 #2）＝付け替える道を実データで通る。その3枝が恒等の窓で発火するかは**データ不足**（恒等ハーネスは実データが要り、本監査では走らせていない）。(4) 注記＝いまの鍵の衝突（:2049）を v2 は直すので、(i) のレシピに「同じ列に違う pre を掛けた2条件」を入れると恒等は正しく崩れる＝レシピにその型を入れないと書く必要がある |
| C2 | :105「5形 × na=pass の有無 2通り＝10組」 | ②曖昧 | 実装が「配列の i 番目を引く」なら配列との一致は自明＝C2 が守るのは添字のずれと scope・状態の配管。cross は na=pass を無視する（私の実測 False・:1719）・candle_dir は NaN を持たない＝**判別できる組は8**。「10組」を数の根拠にしない |
| C3(ii) | :106「『値を解決できない』の拒否が 0 かつ cross を含む案が ≥1本」 | ②曖昧 | 拒否の数え方が1つの文言に限られる＝新しい検査 (a)〜(f) が生成器の案を別の理由で拒否しても C3(ii) は通る（C8 の T6 が 10/10 で捕まえるので致命ではない）。種は固定（gen:3853 `seed=11`）＝「≥1本」は測れる |
| C7／C1 | :110「偽レシピ8通りが全部 G で拒否される」／:104「検査（G6）で拒否される」 | ②曖昧 | やること3 は拒否コード（G5／G6）を決めていない。実物の `selftest` の `broke()` は `want_code in str(e)` で照合するので、コードを決めないと検査が書けない。既存の慣例＝形・side・値の書式は G5（:783-784）、材料の種別は G6（:855-859） |
| C11 | :114「配列方式は新しい未来参照を増やさない…H2 全体の担保ではない（102番）」 | 届く（限定つき） | 限定の文は正しい。cross＝:1717 `np.roll(a, 1)`・:1718 `pa[0]=NaN`＝過去だけ |
| C12 | :115 | 届く・測れる | Plan agent の実測＝直す前でも `_eval_cond` 直呼びで `q50=70・最終値90 → True`／鍵なし → RecipeError |
| C13 | :116 | 届く・測れる | 私の実測＝いまは `KeyError: 'if'` |

### Q4 — 設計書 v2 と実物は一致しているか

**判定＝一致（行番号・関数名・数のうち 31か所）／食い違い 7件。**

一致（私が Read・grep で確認）＝FORM_SPEC :98-116／exit_ok :92・pre_ok :90／SIDES :136／`_walk` :245-271・not :255-262／`_check_cond` :783・:858-859／`_vnum_q` の ref :1504-1507／`_eval_cond` :1642-1738・strict の3行 :1700・:1708・:1732／`_eval_tree` :1741-1779・not :1765／validate :1334-1387・fire :1359-1363／`_collect_fire_cols` :2036-2052・鍵 :2049・呼び出し :2174／`_exit_fire_ok` :2055-2111・scope :2058-2075・状態 :2079-2089・`_ev` :2091-2110／売買ループ5か所／resting :2361-2371／selftest :3491・:3712・:3714／`_col_array` :1601／gen `strip_marks` :813／`_state_cond` :1632／`_exit_indicator_cond` :1656・コメント :1712-1715・cross の条件 :1697／`_cond_keys` :2404-2450／needed_qkeys の出口 :2456-2461／synth_df :3386／T6 :3841／枝19・REVERSE_IND・BREAKOUT の forms と placement／gen の strict 0件・Δ 0件／exec の pre_ok を守る検査 0件・`forms_where("state_free")` 0件。

| # | v2 の記述（逐語・行） | 実物 | 種別 |
|---|---|---|---|
| 1 | :58「:2605 恒等ハーネス（**L1**）の出口 fire の材料」 | :2605 を含む関数＝`run_identity`（:2537〜）＝**S2**。`run_identity_l1` は :2729 | 関数名の取り違え（Minor） |
| 2 | :34「恒等ハーネス（:2605）の出口の材料も state だけ」／:58「★指標の材料は0件」 | `recipes/identity_s1_legacy.json` の出口 fire＝MTFCUT（state 1本＋**legacy_col 2本**）・V59DOWN（legacy_col）・V59FLAT（legacy_col）＝**指標の材料が3枝に在る**（私がプログラムで数えた） | 事実の食い違い（Minor・向きは有利＝C6(ii) の S1 は付け替える道を通る） |
| 3 | :70「:2759 案1本を走らせる関数の except」／:31「gen:2759」 | `run_trial_guarded` :2739〜・except は **:2760** | 1行ずれ（Trivial） |
| 4 | :51「:1494-1507 `_vnum_q`＝分位・定数・ref の解決」 | 関数は :1494〜（分位・定数への落とし先は :1507 より後） | 範囲の不足（Trivial） |
| 5 | :50「:1471-1481 `_side_cmp`」／:65「:813-820 strip_marks」／:72「:3841-3877 T6」 | 1471-1479／813-821／3841-3879（次の T7 が :3881） | 末尾の行ずれ（Trivial） |
| 6 | :104 C1「検査（G6）で拒否される」 vs :94 やること3（コード未指定） vs :110 C7「G で拒否」 | 実物の慣例では側の不備は G5（:783-784） | 内部の不一致（Minor） |
| 7 | :93 やること2「玉の状態の条件の道…は1文字も変えない」 vs :92 やること1「材料に state を含まない条件」 | 状態か指標かを分ける行は :2093-2095 の1か所で両方の道が共有＝「1文字も変えない」を守ると Q2 新1 の判定規則（`m.get("state")`）がそのまま残る＝v2 の中で「状態の道は触らない」と「検査と実行の規則を揃える」が両立していない | 内部の矛盾（Major の根＝改善1で解く） |

---

## 4. 外部検索結果サマリー（Plan サブエージェントが WebSearch／WebFetch で実施・auditor 側の CC は URL を開き直していない）

クエリ1: `refactoring characterization test golden master hash comparison before after`
クエリ2: `validation allowlist vs denylist fail-closed design rule engine`
クエリ3（拡張）: `golden master test pitfalls test does not exercise changed code path vacuous pass mutation testing`

| # | 発見 | 本設計への当てはめ | 出典 |
|---|---|---|---|
| 1 | 「入力を与えて出力を記録する＝それが Golden Master。コードを変え、テストを走らせ、記録した出力と比べる」 | v2 やること5（実装の前に基準値を測る）＝この手順と一致 ✅ | Fabrizio Duroni（Medium）／Codurance「Testing legacy code with Golden Master」 |
| 2 | 「Golden master は結果の正しさを推論しない＝変更の望まない影響を検出するだけ」 | C6 は「変化の検出」であって「正しさ」ではない＝通らない道（発火しない枝）の恒等は何も検出しない → C6 に「枝の発火 ≥1」を足す根拠 | Wikipedia「Characterization test」 |
| 3 | 「繰り返せることに依存する＝揮発する値・非決定の値は両方から除く」 | 合成データ・種固定＝適合。ただし**レシピを固定していない**と「同じ入力」にならない（Q3 C6） | Steven Schwenke「What is the Golden Master Technique」 |
| 4 | 「golden master を検分せずに受け入れてはならない」 | 基準値は「直す前の実物」の出力＝level の道は正しい（実測）ので基準として妥当。ただし鍵の衝突（:2049）を含むレシピだと基準が既存バグ込みになる → (i) のレシピからその型を除く | 同上／SitePoint |
| 5 | 「golden master の生成と比較を手で切り替える設計は、人の手順を自動テストに持ち込む」 | やること5 の基準値と C6 の比較を、同じ関数の切り替えでなく別の入口にする＝実装時の注意 | The Code Whisperer「How Not To Write Golden Master Tests」 |
| 6 | 「悪い入力を全部 列挙するのは不可能＝新しい型は denylist を抜ける。期待する形（schema）を宣言して検証する」 | v2 の (a)（exit_ok に在る形だけ許す）と (b)（state は level だけ）は allowlist ✅。(c)(d)(e)(f) は denylist（名指しで弾く）＝**Q2 新1 は名指しの外に在った型**＝denylist が抜けられる実例。材料の「形」を schema で1つに決める（種別の鍵はちょうど1つ）のが allowlist 側の直し方 | VibeAppScanner「Input Validation」 |
| 7 | 「denylist は上流が変わった瞬間に fail-open になる。allowlist は名前を挙げたものだけ通す」 | FORM_SPEC に形を足したとき＝(a) は `forms_where("exit_ok")` を読むので自動で追随 ✅。(c) は形の名前を直書き＝新しい needs_side の形が増えたら抜ける → (c) を `forms_where("needs_side")` − {level} で書く方が閉じる | MCP Manager「Feature Governance」／Agent Patterns「Allowlist vs Blocklist」 |
| 8 | 「default deny＝新しいものは明示の許可が無い限り使えない」 | v2 の思想（fail-closed）と一致。残る denylist 4件を「材料の schema＋形の性質表からの導出」に寄せるほど、名指しの外が減る | Agent Patterns／Signzy |
| 9 | 「Vacuity（空の成立）は弱い assertion の失敗の型。mutation testing は注入した誤った挙動に対する判別力を問う」 | C7 の偽レシピ8通り＝mutation の考え方 ✅。C6 には vacuity の穴（発火しない枝の恒等）＝改善2 | arXiv 2606.21451／The Code Whisperer「Golden Master and Sampling」 |

（Plan agent の注記＝#5 の WebFetch は要約が本文の一部に留まった。#6〜#8 は本文から逐語を取得。）

---

## 5. 総合判定

**Verdict: OTHER＝条件つき GO**（下の改善1・改善2 を設計書に追記した版を承認する。追記なしで承認するなら、設計書自身の基準「直した先に黙って別物を残さない・fail-closed」（ARC の狙い:8）に照らして NO-GO）。

根拠:
1. **cp7 の8件は全部、意味を変えずに反映されている**（Q1＝8/8。next_step.md に 101〜105 が実在）。cp7 が「直せば GO」と書いた条件（検査2→6・C1/C3/C6/C8/C11 の書き直し）は満たされた。
2. **cp7 の5件（strict・pre・not・ref・混在）は v2 の検査と `_ev` の not で全部 止まる**（Q2＝実物の `_walk`／`_check_cond`／`_check_value`／`_material_name` に当てはめて静的に確認。直す前は5件とも「通った」を実測）。
3. **新しい穴が1件 残る**（Q2 新1・Major）＝材料の種別を決める規則が検査（`_material_name`:514-533）と実行（`_ev`:2094）で違い、v2 はどちらで決めるかを書いていない。私の実測で「検査は列・実行は状態」を再現（legacy_col＋state・geo＋state の2通り）。露出＝生成器は作らない。直し＝検査1行（種別の鍵は1つだけ）＋やること1・(b)(d)(f) に判定関数を明記。
4. **C6（恒等）が空の成立を許す**（Q3・Major）＝レシピが固定されておらず、付け替える枝が1回も発火しなくても一致する。直し＝レシピの保存とハッシュ値・枝ごとの発火件数を §9 に書く。
5. 好材料（維持）＝`_eval_cond` への一本化・canonical JSON の鍵・(a)(b) の allowlist 型・基準値を実装前に測る手順・§7 の11件の明示・`--identity` S1 が付け替える道（legacy_col の指標 level 3枝）を実データで通る（v2 が書いているより恒等の網は広い）。

---

## 6. 改善方向性

| 優先 | # | 提案（設計書に足す・変える所） | 根拠の行 |
|---|---|---|---|
| **Major** | 1 | やること3 に **(g)** を足す＝「材料の辞書に、種別の鍵（legacy_col・geo・state・time・family）が2つ以上 在れば拒否（入口・出口とも・G6）」。加えて やること1・(b)(d)(f) の「材料に state」を「`_material_name(m, lane)[0] == "state"` で決める（`"state" in m` で決めない）」と明記し、`_ev` の :2094 も同じ関数で分ける（＝やること2 の「状態の道は1文字も変えない」を「値の評価の式は変えない・種別の判定は `_material_name` に寄せる」に書き直す）。日本語＝**材料が「列」なのか「玉の状態」なのかを決める規則を1つにする** | exec:514-533・:2093-2095／私の実測（Q2 新1） |
| **Major** | 2 | C6 を3点 足す＝(1) (i)(iii) のレシピを JSON で保存し、その sha256 と売買記録のハッシュ値（`_md5_trades`:2529）を §9 に書く (2) 売買記録の exit_reason ごとの件数を §9 に書き、**付け替える枝（BREAKOUT_CUT／REVERSE_IND の理由）が ≥1 件**を条件にする（0件なら「未判定」と書く）(3) (i) のレシピに「同じ列に違う pre を掛けた2条件」を入れない（鍵の衝突を直すので恒等が正しく崩れる）。日本語＝**直す前後で「同じレシピ」を走らせた証拠と、「その枝が実際に動いた」証拠を残す** | v2:96・:109／exec:2049・:2529-2534／§4 #2・#3・#9 |
| Minor | 3 | (c) を名指し（slope・slope_avg・diff）でなく性質表から導く＝「`forms_where("needs_side")` のうち level 以外で strict なら拒否」。理由＝形が増えたとき denylist が抜ける（§4 #7）。101番が直ったら外す判断は まこさん（v2 のとおり） | exec:783・:1700・:1708・:1732 |
| Minor | 4 | (b) に「玉の状態の条件の value は n・const・legacy だけ（threshold_q・ref は拒否・理由＝状態の値は分位の解決表を持たない）」を足す。いまは validate 通過 → 実行で RecipeError（Q2 新2）＝止まる場所と理由を検査に前倒しする | exec:1482-1491／gen:2458-2461 |
| Minor | 5 | C2 の「10組」を「8組（cross・candle_dir は na=pass が効かないことを入口と同じと確認）」に直す。C3(ii) の拒否の数え方を「理由を問わず 0」にする | 私の実測（cross NaN na=pass → False）／exec:1719 |
| Minor | 6 | やること3 に各検査の拒否コード（G5＝形・側・値の書式／G6＝材料の種別）を書き、C1 の「G6」と C7 の「G」を揃える（`broke()` が文字列で照合するため） | exec:783-784・:855-859 |
| Minor | 7 | Q4 の7件を直す＝:2605 は `run_identity`（S2）／S1 の恒等レシピの出口 fire に legacy_col の指標 level が3枝 在る（C6(ii) の説明に書く＝好材料）／gen:2760／`_vnum_q` の範囲／末尾の行ずれ3件／C1・C7 のコード | 本報告 Q4 |

---

## 7. CC プロセス欠陥対策（cc_role §1.4.6 への追記案・3件）

1. **監査の所見を裏取りするとき、grep の範囲を「所見の主張が及ぶ全部」にする**＝本件＝cp7「恒等ハーネスの出口 fire の材料は state だけ」を、起案 CC は `engine_tuner_exec.py` だけを grep して「一致」と書いた（worklog §32:474）。主張の対象＝恒等レシピ3本＝`recipes/identity_s1_legacy.json` を含む。監査の主張は「反証を探す対象」であって「写す対象」ではない。
2. **「〇〇を含む条件」と設計書に書くときは、それを決める関数名を書く**＝本件＝「材料に state を含む」を4か所（やること1・(b)(d)(f)）に書きながら、検査（`_material_name`）と実行（`m.get("state")`）で規則が違うことを見ていない。分類の規則が2つ在れば、検査と実行は必ずどこかで別物になる（設計書 §3① が自分で書いている戒め）。
3. **恒等（golden master）を完成の条件に書くときは、「入力の固定（レシピの保存とハッシュ値）」と「通った証拠（付け替える枝の発火件数）」を必ず添える**＝cp7 の §7-1（付け替える道の恒等を必須に）に「空の成立を許さない」を足す。golden master は正しさを保証せず変化を検出するだけ（§4 #2）＝動かなかった道の恒等は何も検出しない。

---

## 8. 二重の確認の記録（auditor 側の CC が Plan サブエージェントの所見を実物で裏取りした結果）

| Plan agent の主張 | 私が測ったこと | 結果 |
|---|---|---|
| 依頼書の事実データ（行数・ハッシュ値）が一致 | wc -l・shasum を自分で実測 | ✅ 一致（3件） |
| v2 の §1b・§2・やること・C1〜C13・§7 の行番号と逐語 | v2 を全文 Read | ✅ 一致（引用の行は全部 実在） |
| cp7 の8件の反映先（やること3(c)(d)(e)(f)・やること2・C1/C3/C6/C7/C8/C11/C12/C13・101〜105番） | v2 の該当行を Read＋next_step.md の 101〜105 を grep | ✅ 一致（8/8） |
| 新1＝材料の種別の規則が検査と実行で違う（:514-533 vs :2094） | 優先順の5行を grep＋`{"legacy_col","state"}` で検査・`_collect_fire_cols`・`_ev`・`_eval_cond` を直呼び | ✅ 一致（検査＝legacy_col／実行＝state・True／評価器＝False） |
| 新1 は「geo＋state・time＋state も同じ順序で起きる＝レーンを問わない」 | 4通り×2レーンで `_material_name` を直呼び | **⚠️ 訂正**＝起きるのは legacy_col＋state（恒等レーンだけ・探索は :515 の G6 で止まる）と geo＋state（どのレーンでも）の**2通り**。time＋state・family＋state は検査も state を先に見る（:523 が :528・:533 より先）＝一致する。**結論（Major）は変わらない** |
| 新2＝状態の条件に threshold_q は検査を通り実行で RecipeError | 直呼び | ✅ 一致 |
| 新3＝candle_dir の材料は :835-836 で `mats = []` | :833-837 を Read | ✅ 一致 |
| `forms_where("state_free")` の呼び出し 0件 | grep -c | ✅ 一致（0） |
| C2 の cross は na=pass を無視 | 最終バー NaN・na=pass で `_eval_cond` 直呼び | ✅ 一致（False） |
| numpy の型＝int64 は TypeError・float64 は通る | json.dumps を直呼び | ✅ 一致 |
| :2605 は `run_identity`（S2）であって L1 ではない | def 行を grep（run_identity :2537／_l1 :2729／_s1 :2866） | ✅ 一致 |
| S1 の恒等レシピの出口 fire に legacy_col の指標が3枝 | `identity_s1_legacy.json` をプログラムで数えた | ✅ 一致（MTFCUT 2本・V59DOWN・V59FLAT） |
| gen の except は :2760（v2 は :2759） | :2758-2761 を出力 | ✅ 一致 |
| T6 の種・本数（gen:3807 `synth_df()`・:3852-3854 seed=11・10本・6本・top_k=2） | 該当行を出力 | ✅ 一致 |
| worklog §32:474 の裏取りは exec.py だけを grep | :470-478 を出力 | ✅ 一致（`grep '"state": "'`＝:2605 の1件） |
| 直す前の validate（8通り）と実行（not・pre・混在・strict）の実測 | 私は cp7 で5通り＋今回 新1・新2 を実測。残り（slope_avg・streak・hysteresis・cross＋pre・ref・混在の実行）は Plan agent の出力のまま | ✅ 私が測った分は一致。測っていない分は静的な読みと整合 |
| 外部検索の9件 | — | **開き直していない**（Plan agent の要約のまま） |

---

## 9. 限界（正直に）

- **直した後のコードは存在しない**。v2 の検査が「止まる」かは、v2 の検査の文を実物の関数（`_walk`・`_check_cond`・`_check_value`・`_material_name`）の挙動に当てはめた静的な判定。実測は「直す前」だけ。
- 恒等ハーネス（`--identity` L1／S1／S2）は実データが要るため、本監査では走らせていない＝S1 の指標の3枝が恒等の窓で発火するかは未測定。
- 外部検索の本文は Plan agent の要約。URL は開き直していない。
- 月次 NET ≥ $1,900 の達成可能性は対象外（本監査は設計の監査）。
