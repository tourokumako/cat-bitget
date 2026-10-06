# 監査結果 cp62 — CP62 — 指標の修正の2つ目の工事＝パラメータを、名前に出さない引数で受け取る形にする。M2-C-15（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_request.md`
- 依頼書のハッシュ値: e3aaa02223dd9cd5431c28d13d5caf114914e410c96650ff7090ad28a8db1b6e
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 9c82c505833fd09a06f98bca7b4c981fe1a9fea6d2ceb850336cbd52e8012753
- 監査が照らしたハッシュ値: 9c82c505833fd09a06f98bca7b4c981fe1a9fea6d2ceb850336cbd52e8012753（`shasum -a 256 .claude/state/acceptance.md`・2123行）。依頼書の値と合う。承認の印（acceptance.approved）と承認の控え（acceptance_archive/m2c15-hidden-params-20261004.md）も同じ値。
- 実施日: 2026-10-06

★監査の途中（14:39:18）に、監査人以外の手で commit 3a75088 が入り、HEAD が e353f27 から変わった（中身＝hook・try_hooks.py・permanent_rules.md・gen_acceptance.py・設計書の控え .01／.02）。Q1 は `e353f27:` を名指しして走らせ直し、同じ結果だった。直す対象の9本は e353f27 と 3a75088 で差が無い（`git diff --stat` が空）。続いて 14:43:32 に commit 8b1777e（155回目の引き継ぎ＝next_step.md・next_step_src.json・session_worklog_20261004.md・session_worklog_20261006.md・lessons_active.md）が入った。直す対象の observe_diag.py・indicator_reference_diag.py・observe_config.json・b128・applied_fixes.json は、e353f27 と 8b1777e で差が無い（`git diff --stat e353f27 HEAD` が空）。


## 2. 監査対象の型宣言

- コード型＝observe_diag.py・indicator_reference_diag.py・observe_config.json・壊すプログラム6本・apply_audit_fix.py（Q12）
- 数値型＝574列の一致・n_eff・件数（56件・47種類・引数150個）
- 文書型＝設計書・承認の控え3版・やることの表・見直し表・観察の説明書・型の表


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

- 依頼書の表56行を、設計書と1行ずつ照らした（作業場の q0_facts.py）。違う行は0。
- 監査人の読み方・当てる道具の read_design_fixes・工事のフォルダの元（impl_src_mismatch）の3つとも56件で、違いは0（q1_toolparse.py）。
- 番号は1〜56が連続し、見出しは全部「直した後の文字」、状態は全部「確定」。
- ファイルごとの件数＝observe_diag.py 41・indicator_reference_diag.py 7・observe_config.json 2・b128 1・新しい壊すプログラム 5。

### 当てた記録（applied_fixes.json の名前 design:m2c15-hidden-params-20261004）

- 56行で、番号1〜56が1回ずつ。全部「当てた」で、時刻は全部 2026-10-06T11:21:19。「もう当て終わっていた」は0件。
- 対象のファイルは設計書と全部同じ。
- `git diff HEAD` で見ると、記録の差分は足した行だけ（消した行0）で、足した56件は全部この工事の名前。
- 依頼書の表との違いは0行。

### 必読に要るファイル（道具が設計書と実装から拾った）

- 依頼書の表の13本は全部 実在し、着手前必読26件に入っている。直す相手（TARGET）の9本は、Q1・Q2 で全部を照らした。
- 監査の結果、直す相手として表に無いファイルが4本 出た（observe_diag_manual.md＝修正3・apply_audit_fix.py＝修正4・gen_review.py＝修正10・やることの表.md＝修正1・5・8）。どれも監査人が実物を開いて写した。


## 4. 所見

### 一般の観点

該当なし（依頼書のとおり）

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**NO。**

- 確かめ方＝作業場の写し（q1_apply.py）で、e353f27 の対象9本に56件を番号の順に当てた（各件で直す前の文字は1か所）。そのあと作業中の実物と比べた。
- 結果＝8本は1文字も同じ。observe_diag.py だけ1行違う。
  - 実物 observe_diag.py:7057「if "AO%" not in _nm_k1 or any(_x8.startswith("AO%(") for _x8 in sorted(_nm_k1)):」
  - 設計書 acceptance.md:1225（実装41）は `for _x8 in _nm_k1` の形。
- 違いの中身＝恒久74番（permanent_rules.md:436）に基づく、まこさんの手直し。名前の候補7個の組み合わせ128組で、sorted の有無で真偽が違う組は0。写しを設計書の形に戻しても、軽い口は rc=0。
- 原因＝実装41 の形は、engine_tuner_exec.py の番人 unordered_iteration_scan（engine_tuner_exec.py:4052）に止められる形だった。設計書の形を写しのソースに掛けると1件止められる（7057行「set の変数 _nm_k1（7007行で作成）を上から順に見ている」）。いまの実物は0件。CC は案を写しで確かめたときに、この番人を走らせていなかった（session_worklog_20261006.md:64）。
- 重さ＝Critical（問い1 の「1文字でも違う」に当たる）。

修正の番号＝1, 2

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**1行 在る。**

- Q1 の比べで出た、実装の指示に当たらない変更は observe_diag.py:7057 の1行（`sorted(` と `)` の8文字）だけ。ほかの8本には0行。
- 所見は Q1 と同じ。

修正の番号＝1, 2

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**YES。**

- 56件が番号・対象のファイルとも合う。抜けは0件。
- 「もう当て終わっていた」は0件で、全件が 11:21:19 の1回の実行で当たっている（q3_record.py）。

修正の番号＝なし

### Q8 — 名前に出さない引数は、47種類の登録で、その列の計算に本当に届いているか（優先度 A）

**YES（Minor 1件）。**

- 届いているか＝q8_reach.py で、実データの最後の2500本を使い、既定つきの引数を1つずつ別の値にした（`**kw` の先の移動平均の関数の引数を含む）。引数のある72種類・引数150個のうち、列が変わったのが150個。届かない引数は0、全部計算できない引数も0。数でない既定の2つ（SQZPRO_ON_WIDE／NARROW の k='WIDE'／'NARROW'）は数えていない。
- 番人と同じやり方で（q8_guard.py）＝届いた149個・届かない0個。番人が除く「別の値が全部 計算できなかった」引数は `low_Z` の `c`（for が取り込んだ列の番号・observe_diag.py:1306〜1308）の1つだけ。open_Z と high_Z の `c` は「届く」に数えられている。
- 除外で見逃しがないか＝計算に使わない引数は、別の値を渡しても例外を起こさない（既定の値で計算が通っている前提）。このため、この除外が「届いていない引数」を隠すことは無い。
- 何も渡さないときの列（q8_cols.py・q8_cmp.py）＝78af94f の写しと実物を、実データの最後の3000本と、決まった式の値動き1500本の2つで比べた。列の数は 577 → 576。同じ列は574、違う列は CKSPl% と CKSPs% の2列だけ。消えた名前・増えた名前は設計書 4-0 の囲み（acceptance.md:238〜239）と同じ。
- 登録と自前の関数＝_vp_levels（361・373・381行）と _mama・_ck・_ps・_ab・_acb・_cel・_hw（641〜673行）は、全部 `**kw` か受け取った引数をそのまま渡している。移動平均の for（1138〜1143行）は `f(d, n, **kw)` と `pct_change(slope_n)`。差分の足した行に `shift(-` と `center=True` は0件（H2）。
- Minor＝設計書 4-0（acceptance.md:227「使う指標のうち 47種類の登録は、資料に在るパラメータを受け取っていません。」）。実物では、引数が増えた登録を印（indicator_switch.json）と照らすと、H-1 の47種類は「オン43＋オフ4（ALMA傾き・MCGD傾き・SSF傾き・T3傾き）」。オフの4種類は、移動平均の for で同じ計算式を共にする登録。道具の数え方は hidden_param_check.py の `done += regs`（close vs X% と X傾き を両方 数える）。「使う指標のうち47種類」の書き方は実物と合わない。

修正の番号＝8, 9

### Q9 — CKSP は TradingView の形（10・1・9・rma）になっているか。引数の既定 None で、ライブラリの既定どおりの列になるか（優先度 A）

**YES。**

- ライブラリの実物＝pandas_ta_classic 0.6.52 の trend/cksp.py:22〜24・35。tvmode=True で p・x・q が None なら、値は 10・1・9、ならし方は rma。引数なしなら 10・3・20 と rma の混ざった組になる。
- 実データの最後の3000本で（q9_cksp.py）＝いまの `_ck` は `cksp(p=10,x=1,q=9,tvmode=True)` と完全に同じ。直す前の引数なしの呼び方は (10,3,20,rma) と同じで、本の形 (10,3,20,sma) とは違う。列の名前は CKSPl_10_1_9。
- 番人⑦＝observe_diag.py:7050〜7052 が p=10・x=1・q=9・tvmode=True で直接呼んだ列と比べている。b133 で落ちることも確かめた（Q10）。
- None の扱い（q9_none.py）＝kst・uo・smc_sweep・squeeze・ao・hwma・mama・psar・aberration・accbands・ce・hwc・pmax・sarext・hilo・massi・alma・jma・kama・mcgd・ssf・t3・stochrsi の全引数を見た。関数の宣言の既定が全部 None。決め方は「値が在り 0 より大きければ使う、でなければ既定」の形（例＝kst.py:36〜44 の `_pos_int(roc1, 10)`、sarext.py:161〜168）。このため None は引数なしと同じになる。574列の一致がその実測。

修正の番号＝なし

### Q10 — 完成の条件6行は、設計書の4つの直し（H-1〜H-4）を全部 覆っているか。壊すプログラム6本は、直しを外したときだけ落ちるか（優先度 A）

**YES（Minor 1件）。**

- 確かめ方＝壊すプログラムは本物を一時的に書き替える作りなので、本物では走らせていない。q10_breaks.py で、各 .sh の old→new を作業場の写しに当て、写しで selftest_catalog を走らせた。
- 壊さないとき＝rc=0（失敗0件・4.1秒）。
- 6本とも＝本物で old が1か所あり、rc=1、宣言した EXPECT_MSG が出力に在った。b128＝K-1（COPC(9,12,26)）／b132＝close vs HWMA% の na／b133＝CKSP／b134＝名前: AO%（ほかに「参照表に無いカタログ列 AO%(5,34)」も出る）／b135＝RCI／b136＝検査2: _insp_resample。
- 覆い方＝#1 が H-1・#2 が H-2・#3 が H-3・#4 と #5 が H-4。H-3 のうち EMA の傾きの名前は、番人⑧（7054〜7056行）が見ている。壊すプログラムは AO だけ。外した設定（ema_slope_lookbacks・ao_params）を読むコードは、scripts・recipes・tools・hooks に0件で、戻されても列は変わらない。
- 番人⑧の sorted＝Q1 のとおり判定は変わらない（128組で違いは0）。
- 番人⑩の取りこぼし（Minor）＝番人⑩（observe_diag.py:7066〜7068）は、関数のソースに文字 `mode="bar_close"` が在るかで見ている。写しで試すと、次の形はどれも rc=0（落ちない）だった。V1＝_insp_resample の呼び出しをコメントにする／V2＝結果を捨てる／V3＝selftest（7483行）の bar_close の呼び出しをコメントにする。構文の木で呼び出しを見る形に替えた写しでは、V1・V3・b136 で rc=1、壊さないときは rc=0 だった（V2 は残る）。

修正の番号＝7

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**YES。**

- .01 と .02 は1バイトも同じ（sha 7c4445eb…）。いまの版と archive の .md は 9c82c505…。
- ACC_IMPL の囲みは4つとも同じ（囲みの sha256 は f87bc8b0…、目印の hash は ec1cb8850e1d0219）。当てた時刻の版は 7c4445eb…（session_worklog_20261006.md:26）。
- 違いは完成の条件の表の6行の入れ替えだけ（1855〜1860行・−6／+6）。実装には効かない。
- 参考＝`gen_acceptance.py --verify` は rc=1。CODEREF の囲みだけ「正本と食い違い」。中身は関数の行の移動（selftest_catalog 6930→6994 ほか）で、設計書自身が「実装すると動きます」（acceptance.md:1881）と書いている。IMPL と囲みの外の行は一致している。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**YES。**

- 要件と実装の指示の対応＝H-1：実装 1〜11・13・14・16〜36、15 の KST／H-2：実装 5・31／H-3：実装 12・15 の AO・37〜39・42〜50・51（b128 の書き直しは 5 の8番の決定）／H-4：実装 40・41・52〜56。
- G-1・G-2 は当てた後の手順で、4-20 の対象ではない。
- 要件に在って指示に無いもの・指示に在って要件に無いものは0件。
- G-1 の範囲は設計書の中で食い違う。4-2（acceptance.md:258）とやることの表 G-1 には観察の説明書が無く、4-13 の2番（acceptance.md:381）には在る。所見は Q11 に書く。

修正の番号＝なし

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**YES。**

- 6行とも、コマンドは `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`。
- 写しでは rc=0（4.1秒）。本物の置き場（SDK で、3a75088 の後）でも rc=0（4.4秒・失敗0件）。
- 壊す側の6本は Q10 のとおり全部 rc=1。
- 3a75088 の前は、本物の置き場で走らせると設計↔実装ゲートが「gen_acceptance.py を触った」で止めた（hook の止め方で、コードの問題ではない）。
- Process 1件＝承認の前の見直し表（`.claude/state/reviews/acceptance.review.md`）は、105行のうち63行が前の工事（m2c15-indicator-six-items-20261004）の中身で、争点の行（6行目）も前の工事の文だった。完成の条件の「✅済」とは別に、承認の前の見直しが、この設計書について行われた根拠にならない。中身と原因は 9 節に書く。

修正の番号＝10

### Q11 — 名前に出さない引数は、探す側のほかに、どこで見えなくなったか。型の表の禁止3（標本不足）が AO% を見逃す件の影響（優先度 B）

**Critical 1件・Minor 1件。**

- 観察の説明書（Critical）＝observe_diag_manual.md は最後の更新が 32dd9a5（151回目より前）で、いまも「### 1. 指標（573種）」（118行）と「AO%(12,26)」（124行）のまま。q11_manual.py で gen_observe_manual.build() を書き出さずに呼ぶと、いまの実物からは「576種・AO%」になり、29行違う。設計書 4-13 の2番（acceptance.md:381「型の表と観察の説明書は、G-1 で作り直します。」）が行われていない。問い1 の「工事ごとの問いで設計書と違う所」に当たる。
- 禁止3（Minor）＝gen_signal_families.py:99〜100 は、名前の数字の最大値を窓とし、数字が無ければ1本とする（100行「win_bars = max(nums) if nums else 1」）。q11_neff.py で値決め窓 549日・n_min 30 として計算した。AO% の 1d は、名前からだと n_eff 549.0、本当の窓 34本なら 16.1。12h は 32.3、6h は 64.6、4h は 96.9 で、禁止に当たるのは 1d だけ。型の表の差は、禁止3 から AO%(12,26)__1d（21.1）と AO%(5,34)__1d（16.1）が消えたこと（git diff）。名前に数字が無い部品は前から同じ扱い（例＝UO の slow 28本なら 1d の n_eff は 549÷28＝19.6）。設計書には書かれていない（next_step §6 の248番のみ）。
- ほかの所（設計書のとおりで、指摘なし）
  - 範囲の表 material_ranges（q11_ranges.py）＝AO% は軸なし、EMA傾き は軸1つ（9〜200）。設計書 4-7 のとおり。名前に出さない引数は、どの種類の軸にも無い（工事2）。
  - 成績表＝AO% は AO%(12,26) の行だけで引けない。EMA 傾きは新しい名前で在る。CKSP は古い値のまま（設計書 3-2 の2番・6-2 の4番のとおり）。
  - 参照表の known＝EMA 傾きは max(60, p[0]×4) に変わったが、前の p[1]+10＝15 は最大になり得ないので値は同じ。AO% に known は無い。
  - 材料の文書の決まった数字の一覧＝40→38（場所1 39→37・milestones の差分）で、設計書 4-13 の2番のとおり。
  - H2 と G2 は、何も渡さない列だけを照らす（設計書 3-1 の2番のとおり）。

修正の番号＝3, 5, 6

### Q12 — 当てる道具（apply_audit_fix.py）に当てる途中で入れた直し2つは、ほかの件の当て方を変えていないか（優先度 B）

**NO（Major）。**

- 自己テストを直しなしで走らせた結果（q12_tool.py）＝44件のまま。3f0ac4c の直し（apply_audit_fix.py:507〜511）だけ外した写し・e353f27 の直し（542〜551行）だけ外した写し・78af94f の版・いまの版の4つとも 44/44 で通った。どちらの直しも自己テストに覆われていない。
- 形ごとの判定（check_one）

| 形 | いま | 3f0ac4c を外す | e353f27 を外す | 78af94f |
|---|---|---|---|---|
| S1 直した後の文字が別の行に偶然在り、直す前の文字は残る | 当てる | もう当て終わり | 当てる | もう当て終わり |
| S2 当てた後に、後の件が直す前の文字を別の所に足した | 当てる（二重に当てる） | もう当て終わり | 当てる | もう当て終わり |
| S3 行を消す直しを当てた後・記録あり | もう当て終わり | もう当て終わり | 0か所 | 0か所 |
| S4 行を消す直しをまだ当てていないのに・記録あり | もう当て終わり（当てずに飛ばす） | 同じ | 当てる | 当てる |
| S5 行を消す直しを当てた後・記録なし | 0か所 | 0か所 | 0か所 | 0か所 |

- 2つの直しは、狙った形（S1・S3）のほかに、S2（二重に当てる）と S4（当てずに飛ばす）の判定も変える。
- 修正4 の T45・T46 を写しに足すと 46/46 で通る。直しを1つ外すと、その場面だけが落ちる（45/46）。
- S2・S4 は修正4 では変わらない。直すかは、まこさんが決める（恒久65番）。

修正の番号＝4


## 5. 外部検索

該当なし（依頼書のとおり）


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

合っている。.01（7c4445eb…）といまの版（9c82c505…）の違いは、囲みの外の12行（1855〜1860行の −6／+6＝完成の条件の表の状態「未着手」→「✅済」と #6 の説明文）。ACC_IMPL は同じ（囲みの sha256 は f87bc8b0…）。ただし worklog §5（session_worklog_20261006.md:50）の「#6 の文は古いまま残る」とは違い、#6 の説明文も新しい b128 の MEANS に書き替わっている。

### 自己申告 2

合っている。.02 は .01 と1バイトも同じ（sha 同じ）なので、違いも同じ12行で、ACC_IMPL も同じ。

### 自己申告 3

挙げた4本はどれも TARGET の外で、実装の指示は触っていない。Q1・Q2 は対象の9本だけで比べた。補足3つ。

- (a) gen_acceptance.py は監査中の 3a75088（14:39:18）でコミットされた。それまでは設計↔実装ゲートが、本物の置き場での完成の条件のコマンドを止めていた。
- (b) 4本のほかにも、実装の指示の外の作業中の変更が在る。いずれも記録・道具の出力で、4-20 は触っていない。permanent_rules.md の恒久74番（3a75088 でコミット済み）／next_step.md・next_step_src.json・session_worklog_20261004.md・decisions.md／gen_materials の出力（regime_detection_kb.md・engine_tuner_milestones*.md）／G-1 の表、承認のプログラムの記録（breaks_frozen.json・impl_functions_frozen.json）。
- (c) やることの表.md は承認の後に2か所 書き替えられている（H-1 の出どころ・Y-4 の書き方）。`--verify` では囲みの外の行と IMPL は変わっていない。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ NO（根拠＝①observe_diag.py:7057 が実装41（acceptance.md:1225）と `sorted(`・`)` だけ違う。真偽は同じで、恒久74番の手直し。②設計書 4-13 の2番（acceptance.md:381）の「観察の説明書は G-1 で作り直します」が行われていない（observe_diag_manual.md:118 が「指標（573種）」、:124 が AO%(12,26) のまま）。ほかの問い（Q3・Q4・Q5・Q6・Q8・Q9・Q10）では、設計書と実装の違いは見つからなかった）

### 結論と件数

- 結論＝NO-GO
- Critical＝2
- Major＝1
- Minor＝3
- Process＝1


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-hidden-params-20261004/やることの表.md
直す箇所: 70行（### §1 概要）
直す前の文字:
~~~
最後に表を作り直し、型の表を再承認していただき、自己テスト・G2・H2 を取り直します。
~~~
足す文字:
~~~
★承認の後に、まこさんが番人⑧の1行（observe_diag.py:7057）を、材料の名前の set を sorted(_nm_k1) で回す形に手で直した（恒久74番・engine_tuner_exec.py の unordered_iteration_scan＝並びの決まらない入れ物の番人に止められたため）。実装の指示41 の直した後の文字とは「sorted(」と「)」だけ違い、番人⑧の判定は変わらない（監査 CP62 の Q1・Q10）。実装の指示41 そのものを直すには【4-20】を書いた次の案に まこさんの OK が要り、承認の後の工事のフォルダには書けない（gen_verbatim.py:293〜295）ので、新しい工事名で行う。
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:7057「if "AO%" not in _nm_k1 or any(_x8.startswith("AO%(") for _x8 in sorted(_nm_k1)):」
状態: 未決

#### 修正 2
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-hidden-params-20261004 --write
~~~
根拠の抜き書き: .claude/state/acceptance.md:13「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-hidden-params-20261004 --write`」（監査は --write を走らせていない＝本物の設計書を書くため。同じ工事の --verify は 8.5秒・rc=1（CODEREF の行の移動のみ）。作り直すと承認の印と合わなくなり、承認の打ち直しが要る）
状態: 未決

#### 修正 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/observe_diag_manual.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
cd v3-bitget-api-sdk/bitget-python-sdk-api && python3 scripts/priority_rebuild/gen_observe_manual.py --write
~~~
根拠の抜き書き: .claude/state/acceptance.md:381「型の表と観察の説明書は、G-1 で作り直します。」（監査が書き出さずに build() を呼んだ時間＝3.0秒・いまの説明書と29行違う。説明書は G2・H2 の対象のファイルではない＝g2_pass.json・h2_pass.json に0件）
状態: 確定

### Major

#### 修正 4
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 1656行（selftest の T44 の後ろ）
直す前の文字:
~~~
                fails.append(f"❌ 行を消す直し T{total}: 前={ok44a}/{pre44} 後={ok44b}/{post44} {why44a} {why44b}")
~~~
足す文字:
~~~

            # T45（監査 CP62 の Q12・3f0ac4c）＝直した後の文字と同じ文字が別の行に在っても、直す前の文字が残っていれば当て終わりと見ない
            total += 1
            open(code, "w", encoding="utf-8").write("k = p[0]\nq = p[1] + 10\n")
            f45 = {"番号": "1", "重さ": "Critical", "対象のファイル": rel, "状態": "確定", "直す前の文字": "q = p[1] + 10\n",
                   "根拠の抜き書き": "", "4つ目": [("", "直した後の文字", "k = p[0]\n")]}
            ok45, why45, _c = check_one(f45)
            if ok45 and not already_applied(f45):
                ok += 1
                print(f"   T{total} 直した後の文字が別の行に在っても、直す前の文字が残っていれば当てる → pass")
            else:
                fails.append(f"❌ 別の行の同じ文字 T{total}: {ok45} {why45}")

            # T46（監査 CP62 の Q12・e353f27）＝行を消す直し（直した後の文字が空）は、当てた記録に在れば当て終わり・無ければ実物と合わない件
            total += 1
            open(code, "w", encoding="utf-8").write("a = 1\n")
            f46 = {"番号": "46", "重さ": "Critical", "対象のファイル": rel, "状態": "確定", "直す前の文字": "b = 2\n",
                   "根拠の抜き書き": "", "4つ目": [("", "直した後の文字", "")]}
            globals()["CURRENT_REPORT"] = "design:zz46"
            try:
                ok46a, why46a, _c = check_one(f46)
                _record_applied([{"report": "design:zz46", "num": "46", "file": rel, "how": "当てた"}])
                ok46b, why46b, _c = check_one(f46)
            finally:
                globals()["CURRENT_REPORT"] = ""
            if (not ok46a and why46a.startswith("直す前の文字が実物に 0 か所") and not ok46b
                    and why46b == "もう当て終わっている（当てた記録に在る）"):
                ok += 1
                print(f"   T{total} 行を消す直しは、当てた記録に在れば当て終わり・無ければ実物と合わない件 → pass")
            else:
                fails.append(f"❌ 行を消す直しと当てた記録 T{total}: 記録なし={why46a} 記録あり={why46b}")
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:510「if kind == "直した後の文字" and before in cur and before not in body:」（写しで当てた結果＝46/46 pass・3f0ac4c を外すと T45 だけ落ちて 45/46・e353f27 を外すと T46 だけ落ちて 45/46・1.3秒）
状態: 確定

### Minor

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-hidden-params-20261004/やることの表.md
直す箇所: 96行（### 3-1 やらないこと の最後の行）
直す前の文字:
~~~
| 検査2 の確かめそのものを強くすること（今は、決まった2つの時刻だけを見る） | この工事は、今の確かめが外されないように守る番人を足すだけ。確かめを強くするのは、上位足のずらしを切り替えて比べる前（M2-F-10f）に決める | 監査 CP61 の Q10 の4点目・worklog 20261004 §50 |
~~~
足す文字:
~~~

| 型の表の禁止3（標本不足）が、名前に出さない引数の窓を数えること（AO% の 1日足は、名前に数字が無いので n_eff を 549.0 と見る。本当の窓 34本なら 16.1 で n_min 30 を下回る・gen_signal_families.py:93〜101） | 名前に出さない引数を探す側が渡す仕組み（工事2）と一緒に、禁止3 も引数の既定から窓を計算する形にする。名前に数字が無い部品（UO・KST ほか）は前から同じ扱い | next_step §6 の248番・監査 CP62 の Q11 |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_signal_families.py:100「win_bars = max(nums) if nums else 1」
状態: 確定

#### 修正 6
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-hidden-params-20261004 --write
~~~
根拠の抜き書き: .claude/state/acceptance.md:13「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-hidden-params-20261004 --write`」（監査は --write を走らせていない・--verify は 8.5秒）
状態: 確定

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 7066〜7068行（selftest_catalog の番人⑩）
直す前の文字:
~~~
    for _fn10 in (_insp_resample, selftest):
        if 'mode="bar_close"' not in _in10.getsource(_fn10):
            ng.append(f"検査2: {_fn10.__name__} が、上位足のずらし bar_close の形を確かめていない")
~~~
直した後の文字:
~~~
    for _fn10 in (_insp_resample, selftest):
        # ★監査 CP62（2026-10-06）＝文字ではなく構文の木で、_insp_close_leak(…, mode="bar_close") の呼び出しが在るかを見る
        #   （直す前は文字で見たので、呼び出しをコメントにしても通った＝写しで実測）。
        import ast as _ast10
        if not any(isinstance(_c10, _ast10.Call) and getattr(_c10.func, "id", "") == "_insp_close_leak"
                   and any(_k10.arg == "mode" and isinstance(_k10.value, _ast10.Constant) and _k10.value.value == "bar_close"
                           for _k10 in _c10.keywords)
                   for _c10 in _ast10.walk(_ast10.parse(_in10.getsource(_fn10)))):
            ng.append(f"検査2: {_fn10.__name__} が、上位足のずらし bar_close の形を確かめていない")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:7067「if 'mode="bar_close"' not in _in10.getsource(_fn10):」（写しで当てた結果＝壊さない rc=0・b136 と V1・V3 で rc=1・結果を捨てる V2 は rc=0 のまま・合計 22.9秒。設計書 3-1 の10番＝確かめを強くする時期は M2-F-10f の前に決める）
状態: 未決

#### 修正 8
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-hidden-params-20261004/やることの表.md
直す箇所: 70行（### §1 概要）
直す前の文字:
~~~
傾きの比べる本数も同じ形にする（H-1）。
~~~
足す文字:
~~~
（受け取る形にした登録は47種類＝印がオンの43種類と、移動平均の for で close vs ◯% と同じ計算式を使う印がオフの4種類（ALMA傾き・MCGD傾き・SSF傾き・T3傾き）。4-0 の「使う指標のうち 47種類」の内訳・監査 CP62 の Q8）
~~~
根拠の抜き書き: .claude/state/acceptance.md:227「使う指標のうち 47種類の登録は、資料に在るパラメータを受け取っていません。」
状態: 未決

#### 修正 9
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-hidden-params-20261004 --write
~~~
根拠の抜き書き: .claude/state/acceptance.md:13「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-hidden-params-20261004 --write`」（監査は --write を走らせていない・--verify は 8.5秒）
状態: 未決


## 9. CC プロセス欠陥対策

### Process

所見＝見直し表 `.claude/state/reviews/acceptance.review.md` は、この設計書の見直しとして中身が合っていない。争点の行（6行目）は前の工事（m2c15-indicator-six-items-20261004）の文。105行のうち63行（1〜47行目・90〜105行目）が前の工事の中身（例＝13行目「577列 → 577列」、34〜47行目の実装1〜14＝K-1・K-8・G-2・RCI、101行目「6-1 3本」、103行目「7-6 3行（K-1・K-8・G-2）」）。原因＝gen_review.py:107〜126 の skeleton が、置き場が全部の工事で同じ表から、同じ見出しの行と争点を引き継ぐこと。r2_review_fill.py:162〜166 は「<書く>」の行だけを埋める。`--check` は中身の正しさを見ないので通っていた（session_worklog_20261006.md:8・:10「見直しで見つけた抜け＝0件」）。

#### 修正 10
対象のファイル: .claude/tools/gen_review.py
直す箇所: 111〜113行（skeleton）
直す前の文字:
~~~
    prev = _rows(old or "")
    issue = next((ln for ln in (old or "").splitlines() if ln.startswith("争点: ")), f"争点: {PLACE}")
    L = [f"{MARK} doc={os.path.relpath(os.path.realpath(doc), ROOT)} doc_sha256={sha(text)} items={len(its)} -->",
~~~
直した後の文字:
~~~
    # ★監査 CP62（2026-10-06）＝前の表は、同じ工事（設計書の ARC の iter）のときだけ引き継ぐ。直す前は、表の置き場が
    #   全部の工事で同じ（acceptance.review.md）なので、前の工事の行の中身と争点の行が残った（CP62＝105行のうち63行）。
    _m = re.search(r'<!-- ARC iter="([^"]+)" -->', text)
    _iter = _m.group(1) if _m else ""
    if old is not None and f" iter={_iter} " not in (old.splitlines() or [""])[0] + " ":
        old = None
    prev = _rows(old or "")
    issue = next((ln for ln in (old or "").splitlines() if ln.startswith("争点: ")), f"争点: {PLACE}")
    L = [f"{MARK} doc={os.path.relpath(os.path.realpath(doc), ROOT)} doc_sha256={sha(text)} items={len(its)} iter={_iter} -->",
~~~
根拠の抜き書き: .claude/tools/gen_review.py:108「"""表の骨組み。old（前の表）が在れば、同じ項目の行の中身と争点の行を残す。"""」（写しで当てた結果＝自己テスト 11/11・いまの表を前の表にすると埋める所 421 で争点も空・同じ工事の表なら埋める所0・別の工事の表なら421・0.5秒）
状態: 確定


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

**開いたファイルと行（着手前必読26件を含む）**

- 依頼書＝1〜544
- acceptance.md＝1〜2124（全文）。承認の控え .01・.02・.md＝sha と diff、ACC_IMPL の囲み
- applied_fixes.json＝この工事の56行。やることの表.md＝1〜107
- cat_requirements.md＝159〜268・529〜752。engine_tuner_requirements.md＝28〜103。engine_tuner_milestones.md＝95〜146。engine_tuner_milestones2.md＝3〜46・995〜1040
- observe_diag.py＝355〜390・630〜684・1098〜1167・1360〜1375・1465〜1495・6920〜7079、790〜1000 の既定つき登録の行
- indicator_reference_diag.py＝315〜320・832〜838・1055〜1072・1433〜1440・2523〜2540。observe_config.json＝128〜160 と HEAD との diff
- gen_signal_families.py＝88〜137。signal_families.md＝1〜26・数の行・git diff。indicator_switch.json＝頭と on／off
- 壊すプログラム6本＝各全文。acceptance.review.md＝1〜115（全文）。session_worklog_20261006.md＝1〜70。session_worklog_20261004.md＝590〜640
- 道具＝apply_audit_fix.py（1〜260・380〜729・1505〜1667）・gen_audit_docs.py（1700〜1830）・gen_acceptance.py（287〜416・563〜594・1775〜1844）・gen_verbatim.py（280〜300・337〜344）・gen_review.py（100〜139・245〜265）・gen_observe_manual.py（499〜598）・r2_review_fill.py（139〜205）・require_design_check_before_approval.py（280〜345）・engine_tuner_exec.py（4050〜4110）
- ライブラリ＝trend/cksp.py（1〜60）・sarext.py（155〜182）。permanent_rules.md＝74番の差分
- observe_diag_manual.md＝118・124行（結果を書く CC が grep で確かめた）

**走らせたコマンドと結果（作業場 cp62_work の写し・乱数なし）**

- q1_apply.py（0.28秒）＝違いは observe_diag.py:7057 の1か所。e353f27 を名指しして走らせ直しても同じ。
- q1_toolparse.py（1.4秒）＝道具の読み方・工事のフォルダの元・監査人の読み方の3つが同じ。
- q3_record.py＝56行・全部「当てた」。q4_impl.py＝ACC_IMPL は4版とも同じ。
- gen_acceptance.py --verify（8.5秒）＝rc=1（CODEREF だけ）。q4_coderef.py＝違いは関数の行の移動。
- q8_cols.py old／new（30.0秒／30.2秒）・q8_cmp.py＝574列が同じ・2列が違う。
- q8_reach.py（9.0秒）＝150個とも届く。q8_guard.py（3.6秒）＝除外は low_Z c の1個。
- q8_count.py／q8_count_cmp3.py＝オン46・オフ21（秒は測っていない）。
- q9_none.py・q9_cksp.py＝None は既定。CKSP は TV と完全一致（秒は測っていない）。
- q10_breaks.py（28.9秒）＝6本とも rc=1 で宣言の文が出る。壊さないときは rc=0。
- q10_evade.py（16.6秒）＝V1〜V3 は rc=0。sorted の有無で違う組は 0／128。
- q10_unordered.py（4.3秒）＝設計の形は1件止められ、いまの実物は0件。q10_fix.py（22.9秒）。
- q11_neff.py（秒は測っていない）。q11_manual.py（3.0秒）＝29行違う。q11_ranges.py（3.0秒）＝143種類。
- q12_tool.py（1.9秒）。q12_add.py（1.3秒）。q_review_fix.py（0.2秒）。q_review_st.py（0.3秒）。
- 本物の置き場で `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`（4.4秒）＝rc=0。3a75088 の前はゲートが止めた。
- chk_main.py（結果を書く CC・1秒未満）＝修正1・4・5・7・8・10 の直す前の文字が、それぞれ実物に1か所だけ在る。

**走らせなかったものと理由**

- 壊すプログラム .sh をそのまま＝本物のファイルを一時的に書き替えるため。写しに同じ old→new を当てて代わりにした。
- 全体の自己テスト `--selftest`（約124秒）＝完成の条件の6行の外で、本物に何も書かないことを確かめていないため。
- G2 `gen_signal_families.py --verify` と H2 `leak_causality_diag.py`＝本物の g2_pass.json・h2_pass.json を書くため。
- `gen_acceptance.py --write`・`gen_observe_manual.py --write`＝本物を書くため。
- `engine_tuner_exec.py --selftest`＝その中の unordered_iteration_scan だけを直接呼んで代わりにした。


## 11. 本物のファイルを書き替えていないこと

- 作業の前に控えた git_status_before.txt（214行）と、作業の後の git_status_after.txt（206行）の差は8行。どれも 14:39:18 のコミット 3a75088（監査人以外）で消えた行（` M .claude/rules/permanent_rules.md`・` M .claude/tools/gen_acceptance.py`・`A  …/m2c15-hidden-params-20261004.01.diff.txt`・`.01.md`・`.01.sha.txt`・`.02.diff.txt`・`.02.md`・`.02.sha.txt`）。
- 監査人が足したのは `?? …/.claude/audits/cp62_work/`（作業場）の中のファイルと、結果を書く CC の hook の記録（`.claude/state/sessions/58d612d0-ef7e-4e7e-944c-86bace22428b/lessons.md`）だけ。
- ハッシュ値は作業の前と同じ＝acceptance.md 9c82c505…／observe_diag.py 67a6100a…／applied_fixes.json eb3c3c17…。
- 結果を書く直前（HEAD＝8b1777e・14:43:32）に取り直した `git status --short`（203行）の主な行（作業場・ほかの監査の作業場・acceptance_archive の point*／audit-fix* の untracked は省略）。next_step.md・next_step_src.json・session_worklog_20261004.md・session_worklog_20261006.md は 8b1777e でコミットされて消えた。lessons_archive.md（14:42:39 に書き替え）は 8b1777e の引き継ぎの作業で、監査人は触っていない。session_todo_posted は 2026-10-01 のファイル。

```
 M .claude/breaks/b128_k1_copc_back_in_ao_loop.sh
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/applied_fixes.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/lessons_archive.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/regime_detection_kb.md
 M ".../verbatim/m2c15-hidden-params-20261004/やることの表.md"
 M .../.claude/ratchet/{breaks_frozen.json,decisions.md,engine_tuner_milestones.md,engine_tuner_milestones2.md,exit_families.json,exit_families.md,exit_families_approved.txt,impl_functions_frozen.json,materials.json,materials.md,signal_families.json,signal_families.md,signal_families_approved.txt}
 M .../scripts/priority_rebuild/{indicator_reference_diag.py,observe_config.json,observe_diag.py}
?? .claude/breaks/b132〜b136（5本）
?? .claude/hooks/require_chat_draft_before_long_reply.sh・require_request_understood.sh
?? session_todo_posted
?? .../audits/inputs/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_request.md
?? .../acceptance_archive/m2c15-hidden-params-20261004.{breaks.json,dirty.json,frozen.json,md}
?? ".../verbatim/m2c15-hidden-params-20261004/監査依頼の手書き（実装の監査）.md"
?? .../scripts/priority_rebuild/e38_logics.backup_20260802_005140.json ほか .log 4本・v3-bitget-api-sdk/results/
```

HEAD は 8b1777e（14:43:32）。結果を書く直前のハッシュ値も observe_diag.py 67a6100a…・applied_fixes.json eb3c3c17…・acceptance.md 9c82c505… で、作業の前と同じ。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_request.md request_sha256=e3aaa02223dd9cd5431c28d13d5caf114914e410c96650ff7090ad28a8db1b6e -->
