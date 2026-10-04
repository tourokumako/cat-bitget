# 監査結果 cp61 — CP61 — 指標の修正の1回目＝作りの直し。M2-C-15（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-04_m2c15_indicator_six_items_20261004_impl_cp61_audit_request.md`
- 依頼書のハッシュ値: 1e33fe8b3b2be5da4c75e3aaa3979afe2746568b004501c0d5c18374ccbb3320
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 3c2e6d07378a5c42655fcadc647b77694d38b2320aa27a86dc52c28b1314636f
- 監査が照らしたハッシュ値: 3c2e6d07378a5c42655fcadc647b77694d38b2320aa27a86dc52c28b1314636f（`shasum -a 256 .claude/state/acceptance.md` の出力。依頼書のハッシュ値と同じ。Plan のサブエージェントと、呼び出し元の CC が、それぞれ1回ずつ計算した）
- 実施日: 2026-10-04

この結果の読み方を先に書きます。

- 判定（YES／NO・重さ・結論）は、Plan のサブエージェントが、依頼書と着手前必読の23件を独立に読んで出しました。呼び出し元の CC は判定を変えていません。
- Plan のサブエージェントは、ファイルを1つも作れない決まりで動いていました。そのため、写しを作って走らせる測り（Q11 の本数・Q12 の壊すプログラム3本・Q9 の b129）を走らせられませんでした。
- その測りは、呼び出し元の CC が作業場の写しで走らせました。各所見の中に「呼び出し元の CC が写しで測った結果」と見出しを付けて、出力をそのまま書いています。判定の文は足していません。


## 2. 監査対象の型宣言

コード型（.py・.json・.sh の差分の照合）と、文書型（設計書・やることの表・型の表・記録）です。数値型は該当しません（net などの数値の判定は、この監査に在りません）。


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

依頼書の表と実物は合います。

- 設計書の 4-20（`.claude/state/acceptance.md` の 412〜871行）の「対象のファイル」と「直す箇所」は、依頼書 146〜159行の14件と同じです。
- 直す箇所の行番号は、`git diff HEAD` の塊の見出しと合います。observe_diag.py は -1472・-1861・-3857・-3901・-7321・-7437・-6915・-7963。indicator_reference_diag.py は -1061・-4899。observe_config.json は -156。
- 依頼書と実物が違う所が1件 在ります。結論には効きません。依頼書 248行と254行は「HEAD の commit 8272260」と書いています。実物の HEAD は ef13a68 です（`git log --oneline -3` の1行目）。`git diff 8272260 HEAD --name-only` を、対象のファイルの置き場（SDK の scripts と、根の .claude/breaks）に絞ると、出力は空です。対象の6ファイルは、8272260 と HEAD で同じです。

### 当てた記録（applied_fixes.json の名前 design:m2c15-indicator-six-items-20261004）

依頼書の表と実物は合います。

- 場所＝`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/applied_fixes.json` の 2041〜2138行。
- report が `design:m2c15-indicator-six-items-20261004` の行は14件です（`grep -c -F` の出力＝14）。
- num は 1〜14。at は14件とも `2026-10-04T17:36:50`。how は14件とも「当てた」です。

### 必読に要るファイル（道具が設計書と実装から拾った）

10件とも実在します。Plan のサブエージェントが、10件を全部 開きました。

あわせて確かめた事実を1つ書きます。CC の見直し表（`.claude/state/reviews/acceptance.review.md`）の1行目の doc_sha256 は `5e0127e5…` で、いまの設計書（3c2e6d07…）とは違います。見直し表の70行目は「状態は全部「未着手」」と書いています。見直し表は、承認のプログラムが 7-6 に「✅済」を書く前の版を見ています。


## 4. 所見

### 一般の観点

該当なし（依頼書のとおり）

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

答え＝YES。

- 走らせたコマンド＝`python3 -B .claude/tools/apply_audit_fix.py --design --dry`。rc=0。出力は「承認の印と一致: はい」「修正 1〜11: もう当て終わっている（直した後の文字が実物に在る）」「修正 12〜14: もう当て終わっている（新しいファイルが同じ中身で在る）」「当たる 0 件／当てない 14 件（実物と合わない件は0）」でした。
- `git diff HEAD --numstat` の出力＝observe_diag.py は 88行 足す・14行 消す。indicator_reference_diag.py は 7・1。observe_config.json は 2・0。
- 14件の指示から数えた行数＝observe_diag.py は、実装 1（+6 −4）・2（+4）・3（+13 −7）・4（+2 −2）・5（+1 −1）・9（+1）・10（+59）・11（+2）で +88 −14。indicator_reference_diag.py は、実装 7（+5）・8（+2 −1）で +7 −1。observe_config.json は、実装 6（+2）。3ファイルとも、git の行数と同じです。
- 壊すプログラム3本は git に無いファイルです（`git status --short` で `??`）。実装の前には無く、全文が指示の中身です。
- 依頼書が例に挙げた確かめ方（git show で実装の前の版を出し、置き替えて diff を取る）は、Plan のサブエージェントが使えませんでした。hook（require_design_contract_before_run.sh）が、`python3 -B -` の形を止めたためです。上の2つ（当てる道具の --dry と、行数の照合）に替えています。

修正の番号＝なし

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

答え＝無い。

- `git diff HEAD` の塊は、observe_diag.py が11個、indicator_reference_diag.py が2個、observe_config.json が1個です。Plan のサブエージェントが、全部の ± の行を読みました。14件の指示の「直す前の文字」「直した後の文字」の外の行は0行です。行数も Q1 のとおり同じです。
- 乱数＝差分の + の行に、`random`・`rng`・`seed`・`shuffle`・`choice(` は0件です。壊すプログラム3本にも0件です。

修正の番号＝なし

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

答え＝YES。

- 根拠＝applied_fixes.json の 2042〜2137行。14件とも how は「当てた」です。「もう当て終わっていた」は0件です。入っていない件は0件です。
- 番号（num 1〜14）と対象のファイルは、依頼書 165〜178行の表と1件ずつ同じです。

修正の番号＝なし

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（問い2）（優先度 A）

答え＝YES。満たしていない要望は0件です。

- 要望1（この工事は K-1・K-8・G-2・RCI だけ。指標を改ざんする直しが入っていない）＝YES。
  - 差分は Q2 のとおり14件だけです。
  - K-1 は、commit 4656de3 と同じ文です（Q8）。
  - K-8 の式は、監査 CP60 の修正68 と同じです（CP60 の結果ファイルの 1743行「s.index = src.index + pd.Timedelta(TF_RULE[tf]) - (bars.index[1] - bars.index[0])」）。
  - RCI の mako の欄の文は、まこさんの逐語のファイル req_v9_indicators_on_20261004.txt の「V9で使ってる指標は入れるようにしてほしい」と同じです。
- 要望2（指標の名前に値を入れて数を増やさない）＝YES。Q11 のとおりです。
- 要望3（V9 の指標を、使う指標に入れる。名前はそのまま）＝YES。
  - V9 が計算する指標の種類は、observe_diag.py の 4794〜4801行の対応に在る15種類です（RCI・ADX・DI差・ATR%・RSI・BB%b・BB幅・close vs EMA・EMA傾き・Stoch%K・Stoch%D・MACD線%・MACDヒスト%・MACDシグナル線%・fib位置）。15種類とも、indicator_switch.json の on（23〜69行）に在ります。RCI は37行目です。
  - 名前＝signal_families.md の29行目に、RSI7・RSI9・RSI14・RSI21・RCI7・RCI9・RCI26・RCI52 が在ります。型の表の差分（Q13）に、RSI・RCI・Stoch・BB・ADX・ATR・MACD・close vs EMA の名前の変更は0件です。
  - 事実として1点 書きます。EMA の傾き4種の名前には「(5)」が付いています。これは151回目の変更で、この工事の差分ではありません。observe_diag.py の 4795行は EMA傾き を V9 の種類に数えています。V9 のコード（strategies/cat_v9_decider.py の 249〜413行）が使うのは EMA20 の水準（`ema_20`）だけで、EMA の傾きは使っていません。設計書は 4-13 の4番（acceptance.md の394行）で、この名前が残ることと、次の工事で扱うことを書いています。

修正の番号＝なし

### Q8 — K-1 の直しは、7種を修正13 の前と同じ材料に戻したか（優先度 A）

答え＝YES。

- `git show 4656de3` の observe_diag.py の 1397〜1407行と、いまの observe_diag.py の 1472〜1484行は、for の文と addf の11行が同じです。違いは、説明のコメント2行だけです。
- 引数の並び＝COPC は `(g_, f_, s_)`。FISHER と FISHERシグナル は `(f_, g_)`。KSTシグナル は `(g_)`。KDJ の3種は `(n, g_)`。4656de3 と同じです。
- 設定＝observe_config.json の 152〜158行の macd_params は `[12,26,9]` の1組です。161〜166行の ao_params は `[5,34]` の1組です。
- 在る・無い＝signal_families.md で、`COPC(9,12,26)` は2行、`FISHER(12,9)` は1行に在ります。`COPC(9,5,34)`・`FISHER(5,9)`・`FISHERシグナル(5,9)` は0行です。
- KSTシグナル と KDJ＝設定の組が1つずつなので、for の場所が変わっても引数は同じです（g_＝9）。名前は KSTシグナル9・KDJ%K(5,9) ほかです（signal_families.md の27行目と29行目）。
- AO% の2組＝observe_diag.py の 1473行（macd の組）と 1488行（ao_params の組）で作られます。signal_families.md の27行目に、`AO%(12,26)` と `AO%(5,34)` が両方 在ります。

呼び出し元の CC が写しで測った結果（Q11 と同じ測り）＝実装の前の版（HEAD）の写しと、いまの版の写しで、材料の一覧の名前を書き出して diff を取りました。実装の前だけに在る名前は `COPC(9,5,34)`・`FISHER(5,9)`・`FISHERシグナル(5,9)` の3つ。いまだけに在る名前は `COPC(9,12,26)`・`FISHER(12,9)`・`FISHERシグナル(12,9)` の3つ。`AO%(5,34)` は両方に在り、並びの場所だけが変わりました。

修正の番号＝なし

### Q9 — K-8 の上位足の切り替え（bar_close）は未来を使わないか。検査は、未来を使う壊し方を見つけるか（優先度 A）

答え＝YES（bar_close は未来を使わない。既定は now）。検査が b129 の壊し方を見つけるかは、Plan のサブエージェントは走らせていません（読みでは見つける）。呼び出し元の CC が写しで測った結果は rc=1 です（下に出力）。

- 式＝observe_diag.py の 1865行「s.index = src.index + pd.Timedelta(TF_RULE[tf])」。1868〜1869行で、設定が bar_close のときだけ、5分足1本ぶんを引きます。1870行で ffill します。
- 15分足＝足の始まりを T とします。足が閉じる時刻は T+15分です。bar_close の値が当たり始める行は T+10分です。行 T+10分 が閉じる時刻は T+15分です。行 T+5分 に当たるのは、1つ前の足（閉じた時刻 T）です。
- 2時間足＝値が当たり始める行は T+115分です。その行が閉じる時刻は T+120分です。
- どちらも、「行 R が閉じる時刻（R+5分）までに閉じた上位足」だけを使います。
- 前提（事実）＝式は、bars の先頭の2行の間隔（`bars.index[1] - bars.index[0]`）を、5分足1本ぶんとして使います。
- 既定＝observe_config.json の159行は「"htf_shift_mode": "now",」です。1868行は `cfg.get("htf_shift_mode", "now") == "bar_close"` なので、既定では足した2行を通りません。K-8 の直しで、既定の設定の列は1つも変わりません。
- H2＝h2_pass.json のハッシュ値は、いまの実物と合います（Q13）。対象の24件に、observe_diag.py と observe_config.json が入っています。
- b129（2本ぶん早める）を検査が見つけるか＝Plan のサブエージェントは走らせていません。読みでは見つけます。検査（6952〜6964行）は、最後の3本（15分足）と24本（2時間足）で切り詰めて計算し直すからです。承認のプログラムが測った記録（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-indicator-six-items-20261004.breaks.json` の2行目）は「code: 1」「❌ 2 件」「match: true」です。

呼び出し元の CC が写しで測った結果＝作業場の写し（b129）で、1869行に当たる行を `s.index = s.index - 2 * (bars.index[1] - bars.index[0])` に置き替え、`python3 -B <写し>/observe_diag.py --selftest-catalog` を走らせました。壊す前は rc=0（❌ 0 件）。壊した後は rc=1 で、出力は次の3行でした。

```
  ❌ K-8: 上位足のずらし bar_close で、切り詰めると値が変わる（15m・時点 2026-03-21 19:50:00・未来参照の疑い）
  ❌ K-8: 上位足のずらし bar_close で、切り詰めると値が変わる（2h・時点 2026-03-21 19:50:00・未来参照の疑い）
  K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ 2 件
```

修正の番号＝なし

### Q10 — 完成の条件は、この工事でやると決めた4つを全部 覆っているか。CC の自己申告つき（優先度 A）

答え＝4つのうち、RCI を「使う」にする直し（実装 8）は、完成の条件が覆っていません（CC の自己申告のとおり。依頼書 230行で対象外）。ほかに、覆っていない直しが1つ 在ります（下の4点目・Minor）。設計書の 2-1 と 2-2 に、古い値が残っています（下の2点目・Minor）。

依頼書が挙げた4点に、1つずつ答えます。

- 1点目＝RCI は「使う」に入っているか＝YES。indicator_switch.json の37行目「"RCI",」は on の中に在ります。473行目は sources.mako の中です。14行目は「"使う": 145,」、15行目は「"使わない": 116,」です。off の先頭は170行目の「"zscore",」です。
- 2点目＝RCI が「使う」になって、何が起きるか（事実）
  - 型の表＝RCI の名前の差は0件です。RCI7・9・26・52 は、前の版にも在ります。
  - 出口の型の表＝差は、前期間pivot の3行と、数の2行だけです。RCI の差は0件です。
  - 成績表＝material_ranking.json に、RCI7・RCI9・RCI26・RCI52 の列が、時間足11本ぶん在ります。RCI が「使う」に入ったので、engine_tuner_gen.py の 1358行の ranked_materials が、RCI を外さなくなります。
  - 法則と段の候補＝regime_laws.json・m2_stage_candidates.json・exit_families_rules.json に、「RCI」の文字は0件です。RCI を名指しする法則と段の候補は在りません。
  - 材料の文書＝materials.md の差分に、「engine_tuner が選べる指標の種類 139 → 143」と、「RCI の短期 × 長期：—（材料に無い）→ ✅ 受け付ける」が在ります。
  - 設計書に古い値が残っています（Minor）。acceptance.md の108行目は「**探す指標＝印がオンの 141種**（印を切り替えると、この一覧も設計も変わります）。」です。100行目の結果の欄も、表を作り直す前の値です。実物は「使う」が 145種で、off の先頭は zscore です。
- 3点目＝RCI の mako の欄を消したら、何が止まるか＝何も止まりません。軽い口の検査（observe_diag.py の 6930〜6986行）に、RCI・mako・indicator_switch を見る行は在りません。`.claude/breaks/` の .sh に、「RCI」「mako=」を持つファイルは0本です。変わるのは2つだけです。1つ目は、g2_pass.json のハッシュ値が合わなくなること（indicator_reference_diag.py は G2 の対象）。2つ目は、`gen_indicator_switch.py --verify` が、表との食い違いを出すことです。表を作り直せば、RCI は何も言わずに「使わない」に戻ります。CC の自己申告のとおりです。依頼書 230行で対象外なので、不足には数えません。
- 4点目＝ほかに、完成の条件が覆っていない直し＝在ります（Minor）。実装 3・4・5（検査2 を bar_close の形でも確かめる直し）は、完成の条件3行のコマンド（`--selftest-catalog`）が1行も通りません。`_insp_close_leak` が出てくるのは、3866行（定義）・3916行（_insp_resample）・7393行と7395行（selftest）だけです。全体の自己テストでしか通りません。壊すプログラムも在りません。完成の条件は、まこさんが OK した案の逐語（【7-6】）から作られるので、当てる形の修正は書けません。次の工事で、RCI の検査と一緒に扱う相手です。

CC の自己申告2つ（依頼書 306行）への答え

- 自己申告の1つ目＝申告のとおりです。7-6 は3行です（acceptance.md の 1046〜1048行）。4-3（285〜292行）・4-12（329〜332行）・7-1（963行）に、RCI は在りません。3-1 の13番（221行）に書いてあります。
- 自己申告の2つ目＝申告のとおりです。3-1 の12番（220行）に書いてあります。
- まこさんの決定「C」と「案１でいいよ」の逐語のファイルは、工事のフォルダに在りません（ok_ で始まる7本の中身は「すべて案どおりでよい」「案B」「よい」「いいよ」「OK」「案Bでよい」「分ける」）。根拠は、worklog（490行・505行）と、この2つを書いた設計書を まこさんが承認した記録（ハッシュ値 3c2e6d07…）です。

修正の番号＝2

### Q11 — 指標の名前に値を入れる直し・値違いの材料を足す直しが、この工事で1件も入っていないか（優先度 A）

答え＝YES。名前に値を入れる直しと、値違いの材料を足す直しは、0件です。

- 名前＝変わるのは3種だけです（COPC(9,5,34) → COPC(9,12,26)・FISHER(5,9) → FISHER(12,9)・FISHERシグナル(5,9) → FISHERシグナル(12,9)）。Q8 のとおりです。
- 登録の数＝observe_diag.py の `^_reg(` の行は、HEAD が211、いまが211です。差分に `_reg(` の行は0行です。参照表の `^_r(` の行は、HEAD が261、いまが261です。
- 設定＝足した鍵は、`htf_shift_mode` と、その注記の `_htf_shift_mode` の2行だけです。材料の本数を増やす設定は0件です。
- 本数＝いまの型の表は 577種です（signal_families.md の6行目）。実装の前の版の本数は、Plan のサブエージェントは走らせて数えていません（写しを作れなかったため）。コードの読みでは同じです。K-1 は、addf の13回ぶんを、1組の for から1組の for へ移すだけです。drop_columns（observe_config.json の 178〜209行）に、COPC・FISHER・KDJ・KSTシグナル は在りません。

呼び出し元の CC が写しで測った結果＝作業場に、実装の前の版（`git show HEAD:` で出した3ファイル）の写しと、いまの版の写しを作り、`count_catalog_in_copy.py`（作業場に置いた、数えるだけのプログラム）で数えました。出力は次のとおりです。

```
［実装の前の版の写し］材料の一覧の名前 577 個（重なりを除くと 577 個）／htf_shift_mode（設定の値）＝（鍵が無い）／登録されている指標の種類の数（iref.REFS の family）＝261
［いまの版の写し］　　材料の一覧の名前 577 個（重なりを除くと 577 個）／htf_shift_mode（設定の値）＝now／登録されている指標の種類の数（iref.REFS の family）＝261
```

名前の差（diff の出力）は、Q8 に書いた3種の入れ替わりと、`AO%(5,34)` の並びの場所だけです。

修正の番号＝なし

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

答え＝YES。

- 前の版（.01.md）の sha256 は `c5b9801b…ad72` です（.01.sha.txt の値と同じ）。いまの版（.md）の sha256 は `3c2e6d07…636f` です。いまの版は、`.claude/state/acceptance.md` と1文字も同じです（diff の出力が空）。
- 2つの版の diff に、409〜873行（ACC_IMPL の囲み）の行は0行です。実装の指示は同じです。当てる道具は、どちらの版でも、同じ14件を当てます。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

答え＝1件を除いて YES。

- K-1＝実装 1。K-8＝実装 2〜6（検査は 3〜5 と 10）。G-1 の RCI＝実装 8。対応表の3行（やることの表の36行目）＝実装 7。軽い口と壊すプログラム＝実装 9〜14。G-2（自己テスト → G2 → H2）と、G-1 の表の作り直しは、コマンドで行う手順です（設計書 4-4 の5と6）。
- G-1 の行の後ろの部分（K-3・B-1・S-1・RAINBOW傾き・DPO の対応）は、設計書の 3-1 の2番と6番で「やらない」と書いてあります。
- 要件に在るのに、指示にも手順にも記録にも無いもの（Minor・1件）＝やることの表の13行目「段の候補（m2_stage_candidates.json）と出口の型の表の元データ（exit_families_rules.json）が名前で指す材料が、直した後のカタログに在るかも照らす」。設計書に、この2つのファイル名は0件です。worklog の 447〜573行にも0件です。
- 監査が照らした結果＝2つのファイルに、COPC・FISHER・AO%・KDJ・KSTシグナル・前期間pivot・RCI は0件です。EMA傾き は、種類の名前で指しています（m2_stage_candidates.json の53行目）。この工事で変わった名前を指す行は在りません。当てる形の修正は在りません。
- 指示に在るのに、要件に無いもの＝0件。

修正の番号＝なし

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

答え＝YES。

- 先に、`selftest_catalog`（observe_diag.py の 6930〜6986行）を読みました。ファイルに書く行は在りません。
- 走らせたコマンド（SDK のフォルダで）＝`python3 -B scripts/priority_rebuild/observe_diag.py --selftest-catalog`。rc=0。出力＝「  K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ 0 件」。3.764秒。
- 完成の条件の3行は、同じコマンドです。3行とも成り立ちます。

修正の番号＝なし

### Q12 — 軽い口の検査と壊すプログラム b128・b129・b131 が、それぞれの直しを外したときに落ちるか（優先度 B）

答え＝Plan のサブエージェントは、3本を走らせていません。読みと、承認のプログラムが測った記録では、3本とも期待どおりです。呼び出し元の CC が写しで測った結果は、3本とも rc=1 です（下に出力）。

- 走らせなかった理由＝3本とも、本物のファイルを一時的に書き替える作りです（lib.sh の 61〜73行の guard で控えを取り、b128 の23行目の `open(p,'w')` で書き、終わりに戻す）。本物の上では走らせません。Plan のサブエージェントは、写しを作れませんでした。
- 壊す対象の行が1か所か（`grep -c -F`）＝b129 の old の行は1。b128 の old の中の4行（★K-1 の行・APO の行・ao_params の for・COPC の行）は、それぞれ1。b131 の old の中の4行（★G-2・PP・R1・S1）は、それぞれ1。b128 の old は、observe_diag.py の 1472〜1488行と同じ並びです。
- 承認のプログラムが測った記録＝`…m2c15-indicator-six-items-20261004.breaks.json` の3行とも、code 1・expect 1・match true です（❌ 3件・2件・1件）。3本の sha256 は、breaks_frozen.json の値と同じです（16c5ac34…・e99a59e3…・0410b75b…）。
- G-2 の3行の形＝indicator_reference_diag.py の 4905〜4907行は、`((), "理由の文")` の形です。4883行「"高値からの経過バー": ((), "高値を付けてから何本 経ったか。ライブラリに相当する関数が無い"),」と同じ形です。

呼び出し元の CC が写しで測った結果＝作業場に写しを3つ作り（b128・b129・b131）、壊すプログラムの old を new に置き替える直しを、写しにだけ当てました。本物のファイルは書き替えていません（11節）。壊す前は、3つとも rc=0（❌ 0 件）でした。壊した後の出力は、次のとおりです。

```
  ❌ K-1: COPC(9,12,26) がカタログに無い（macd_params の組で作られていない）
  ❌ K-1: FISHER(12,9) がカタログに無い（macd_params の組で作られていない）
  ❌ K-1: FISHERシグナル(12,9) がカタログに無い（macd_params の組で作られていない）
  K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ 3 件
[b128 壊した後] rc=1 秒=3
  ❌ K-8: 上位足のずらし bar_close で、切り詰めると値が変わる（15m・時点 2026-03-21 19:50:00・未来参照の疑い）
  ❌ K-8: 上位足のずらし bar_close で、切り詰めると値が変わる（2h・時点 2026-03-21 19:50:00・未来参照の疑い）
  K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ 2 件
[b129 壊した後] rc=1 秒=3
  ❌ 検査10 が現状の対応表で不一致を出す（表の直し忘れ）: ['対応表 INDUSTRY_MAP に family『前期間pivotPP』が無い（足すか、無いなら空のタプルと理由を書く）', '対応表 INDUSTRY_MAP に family『前期間pivotR1』が無い（足すか、無いなら空のタプルと理由を書く）', '対応表 INDUSTRY_MAP に family『前期間pivotS1』が無い（足すか、無いなら空のタプルと理由を書く）']
  K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ 1 件
[b131 壊した後] rc=1 秒=2
```

3本の期待の文字（EXPECT_MSG）は、b128 が「❌ K-1:」、b129 が「❌ K-8: 上位足のずらし bar_close で」、b131 が「❌ 検査10 が現状の対応表で不一致を出す」です。上の出力に、3つとも在ります。本物の中の壊す対象の行は、3本とも1か所です（`grep -c -F` の出力＝1・1・1）。

修正の番号＝なし

### Q13 — 表の作り直しと、G2・H2 の取り直しは正しく済んでいるか。再承認された型の表の差は何か（優先度 B）

答え＝H2 と G2 のハッシュ値は、いまの実物と合います。型の表の差は「3つだけ」ではなく、4つです（Major 1件）。この工事で増えた名前は在りません。

- ハッシュ値＝Plan のサブエージェントが、対象のファイルの sha256 を shasum で計算し、決まりの式（名前とハッシュ値を並べて sha256）で組みました。
  - H2＝計算した値は `3062a64c…4093`。h2_pass.json の3行目の値「3062a64c8d22b1828272e487f6eaa7c0372e3fad0828559dafdf7f2edf7e4093」と同じです（対象24件・無いファイル0件・2026-10-04 18:15:36）。
  - G2＝計算した値は `b9d7ea53…4735`。g2_pass.json の3行目の値「b9d7ea53bc17bfce269302e4b1b1c45a5becbe102c06b267e3b89b45f6974735」と同じです（対象39件・無いファイル0件・2026-10-04 18:10:30）。順番は G2 → H2 です。
- 型の表の差（`git diff HEAD` で数えた。md は +14 −13、json は +35 −19）
  1. EMA の傾き4種の名前に「(5)」が付いた。CC の説明の1つ目のとおりです。
  2. AO%(5,34) が増えた（トレンド 190 → 191。禁止3 に「AO%(5,34)｜1d｜16.1」が入り、515 → 516組）。CC の説明の2つ目のとおりです。
  3. close vs 前期間pivotPP%・R1%・S1% が増えた（構造・位置 177 → 180）。CC の説明の3つ目のとおりです。
  4. PPOヒスト(12,26,9) の方向の区分が、「状態量」から「順張り値」に変わり、禁止1 の一覧から外れた（142種 → 141種）。CC の説明に在りません。いまの signal_families.json の3798行目は「  "PPOヒスト(12,26,9)": "順張り値",」です。HEAD の版では、3789行目が「状態量」で、92行目に禁止1 の行が在りました。いまの版に、その禁止1 の行は在りません。
- 4つ目の出どころ＝151回目に当てた、監査 CP60 の修正27 です（CP60 の結果ファイルの 1047〜1066行。1066行「当てると型の表 signal_families.json の指紋が変わるので、まこさんの承認がもう一度 要る」）。
- 依頼書 325行と、worklog の540行は、「3つだけ」「3つとも」と書いています。worklog の539行は、「禁止1 141種（前は 142種）」の数だけを書き、理由を書いていません。
- 効き方＝PPOヒスト は「使う」に入っています（indicator_switch.json の83行目）。向きの条件に使えるようになりました。
- 4つとも、151回目（commit be55ea7）の変更です。この工事の14件で増えた名前と、変わった区分は、0件です。
- 再承認の記録（signal_families_approved.txt の「3f4c239756460f25ba0c580e8d4b8e8d  approved 2026-10-04」）は、4つ目を含む中身に対して打たれています。承認されていない名前が、候補に入ることは在りません。足りないのは、まこさんへの説明です。
- 出口の型の表の差＝json 7行・md 4行（前期間pivot の3行と数）。CC の記録（worklog の541行）のとおりです。

修正の番号＝1


## 5. 外部検索

該当なし（依頼書のとおり）


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

申告のとおりです（承認の後に設計書を作り直した）。Plan のサブエージェントが、2つの版の diff を数えました。ACC_CODEREF の囲みの中が12行、ACC_SPEC の囲みの中が9行、囲みの外が17行です（87行・97〜100行・220〜221行・1046〜1048行）。ACC_IMPL は同じです。囲みの外の中身は、概要に足した④（RCI）・2-1 の結果と RCI の行・3-1 の12番と13番・7-6 の状態（未着手 → ✅済）です。

### 自己申告 2

申告の4件は、4件とも在ります（この工事の外の作業中の変更）。`git status --short` に、` M .claude/hooks/approve_impl.sh`・`?? .claude/hooks/require_chat_draft_before_long_reply.sh`・`?? .claude/hooks/require_request_understood.sh`・`?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json` が出ます。4件とも、14件の指示の対象ではありません。approve_impl.sh の差分の中身は見ていません（その名前を含む Bash を、hook の require_acceptance_before_impl.sh が止めるため）。申告に無い未追跡のファイルは、SDK の scripts/priority_rebuild の .log 3本と、根の session_todo_posted です。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝Q1 は1文字も同じ。Q2 は設計書に無い変更が0行。Q3 は14件が1件ずつ合う。Q8・Q9・Q11 は設計書のとおり。Q13 の4つ目の差は、CC の説明との違いで、設計書と実装の違いではない。Q10 の RCI の抜けは、設計書の 3-1 の13番に書いてあり、依頼書 230行で対象外。Q12 は、設計書と違う所が見つかっていない）
- 問い2 ＝ YES（根拠＝Q7。要望3件とも満たす。満たしていない要望は0件）

### 結論と件数

- 結論＝GO
- Critical＝0
- Major＝1
- Minor＝3
- Process＝0

重さの内訳です。Major は、Q13 の説明の抜け（修正 1）です。Minor は3件です。1件目は、Q10 の2点目の、設計書の 2-1 と 2-2 の古い値（修正 2）。2件目は、Q10 の4点目の、実装 3・4・5 を完成の条件が通らないこと（当てる形の修正は無い）。3件目は、Q5 の、G-1 の照らしの記録が無いこと（当てる形の修正は無い）。


## 8. 修正の指示

### Critical

なし

### Major

#### 修正 1
対象のファイル: .claude/state/session_worklog_20261004.md
直す箇所: 540
直す前の文字:
~~~
今回の工事（K-1・K-8・G-2・RCI）で増えた名前は無い（COPC ほかは前に承認された版と同じ名前に戻った）。
~~~
足す文字:
~~~
★監査 CP61 の指摘（2026-10-04）＝差は4つ在る。④PPOヒスト(12,26,9) の方向の区分が「状態量」から「順張り値」に変わり、禁止1 の一覧から外れた（142種 → 141種）。出どころは、151回目に当てた監査 CP60 の修正27（参照表の PPOヒスト の欄）。まこさんへの再承認の説明（①②③）には入っていなかった。
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families.json:3798「  "PPOヒスト(12,26,9)": "順張り値",」
状態: 確定

### Minor

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-indicator-six-items-20261004/やることの表.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-indicator-six-items-20261004 --write
~~~
根拠の抜き書き: .claude/state/acceptance.md:108「**探す指標＝印がオンの 141種**（印を切り替えると、この一覧も設計も変わります）。」（監査はこのコマンドを走らせていない。本物の設計書を書き替えるため。かかる時間は測っていない）
状態: 未決


## 9. CC プロセス欠陥対策

### Process

なし


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

パスの略＝SDK は `v3-bitget-api-sdk/bitget-python-sdk-api` です。

**Plan のサブエージェントが開いたファイルと行（Read）**

1. 依頼書 1〜480行
2. `.claude/state/acceptance.md` 1〜1300行（必読の1番と11番）
3. 控え2本。.md は acceptance.md と diff が空。.01.md は diff で全行を照らし、違う行を全部 読んだ
4. `SDK/.claude/audits/applied_fixes.json` 2036〜2140行
5. やることの表.md 1〜115行
6. `SDK/.claude/rules/cat_requirements.md` 159〜268行・529〜752行
7. `SDK/.claude/ratchet/engine_tuner_requirements.md` 28〜103行
8. `SDK/.claude/ratchet/engine_tuner_milestones.md` 95〜146行
9. `SDK/.claude/ratchet/engine_tuner_milestones2.md` 3〜46行・1173〜1200行
10. 監査 CP60 の結果ファイル 582〜604行・1734〜1748行・1040〜1067行
11. `SDK/scripts/priority_rebuild/observe_diag.py` 729〜776・1317〜1500・1800〜1881・3864〜3921・4492〜4566・4786〜4815・6880〜7001・7388〜7401・7490〜7516・8022〜8051行
12. `SDK/scripts/priority_rebuild/indicator_reference_diag.py` 1050〜1067・4880〜4929・5054〜5095行
13. `SDK/scripts/priority_rebuild/observe_config.json` 100〜221行
14. `SDK/scripts/priority_rebuild/gen_indicator_switch.py` 240〜301行
15. `SDK/.claude/ratchet/indicator_switch.json` 1〜486行
16. `SDK/.claude/ratchet/signal_families.md` 1〜638行
17. `SDK/scripts/priority_rebuild/e38_logic_parts.py` 56〜75行
18. `.claude/breaks/` の b128・b129・b131 の各 1〜27行と、lib.sh 1〜101行
19. `.claude/state/reviews/acceptance.review.md` 1〜72行
20. `.claude/state/session_worklog_20261004.md` 447〜573行
21. 必読の外＝`.claude/tools/apply_audit_fix.py` 60〜209・410〜967行／`.claude/state/g2_pass.json` と h2_pass.json の全文／leak_causality_diag.py 256〜275行／gen_signal_families.py 920〜935行／逐語3本（req_v9_indicators_on・req_no_value_in_name・ok_hidden_param_next_work_b）／…20261004.breaks.json

**Plan のサブエージェントが走らせたコマンドと結果**

- `shasum -a 256`（設計書・控え2本・壊すプログラム3本・H2 と G2 の対象63件）。結果は4節のとおり。
- `python3 -B .claude/tools/apply_audit_fix.py --design --dry`＝rc=0（先に main の 716〜914行を読み、--dry は書く前に戻ることを確かめた）。秒数は測っていない。
- `python3 -B scripts/priority_rebuild/observe_diag.py --selftest-catalog`（SDK のフォルダで）＝rc=0・3.764秒。
- `git diff HEAD`（--stat・--numstat・-U0）・`git show HEAD:…`・`git show 4656de3:…`・`git diff 4656de3 be55ea7`・`git diff 8272260 HEAD`・`git log`・`git status --short`・`grep`・`diff`・`wc -l`・`ls`・`find -mmin`。全部 読むだけのコマンド。秒数は測っていない。

**呼び出し元の CC が、作業場の写しで走らせたコマンドと結果**

- 写しの作り方＝作業場 `SDK/.claude/audits/cp61_work/` に、フォルダ now・head・b128・b129・b131 を作った。それぞれの `a/b/` に、observe_diag.py・indicator_reference_diag.py・periods.py・ratchet_io.py・regime_label.py・observe_config.json の写しを置いた。head の3ファイル（observe_diag.py・indicator_reference_diag.py・observe_config.json）は、`git show HEAD:` の出力に置き替えた。各フォルダの `data` は、SDK の data フォルダへの近道（シンボリックリンク）で、読むだけに使う。
- `python3 -B SDK/.claude/audits/cp61_work/count_catalog_in_copy.py <写し> <書く先>`＝now の写しは rc=0・2秒。head の写しは rc=0・3秒。出力は Q11 に書いた。読み込んだ observe_diag と indicator_reference_diag が、写しのフォルダの物であることも印字で確かめた。
- `python3 -B <写し>/a/b/observe_diag.py --selftest-catalog`＝壊す前の4つ（now・b128・b129・b131）は、全部 rc=0（2〜3秒）。壊した後の3つ（b128・b129・b131）は、全部 rc=1（2〜3秒）。出力は Q12 に書いた。
- 壊し方の当て方＝壊すプログラムの中の old と new を、Edit で写しにだけ当てた（b128 と b129 は observe_diag.py。b131 は indicator_reference_diag.py）。写しと本物の違う行の数（`diff` の `<` と `>` の行）は、b128 が10、b129 が2、b131 が5。
- 根拠の行の照らし＝`shasum`・`git log`・`git diff --numstat`・`sed -n`・`awk`・`grep -c -F` で、4節の根拠の行を実物で照らした（設計書のハッシュ値・HEAD・行数・signal_families.json の3798行・HEAD の版の92行と3789行・worklog の540行の文が1か所であること・設計書の 100・108・220・221・394・1046〜1048行・indicator_switch.json の 14・15・37・170行・observe_config.json の159行・observe_diag.py の 1865〜1870行と 4794〜4801行・indicator_reference_diag.py の 4883・4905〜4907行・applied_fixes.json の14件・signal_families_approved.txt・h2_pass.json と g2_pass.json の3行目）。違う所は在りませんでした。H2 と G2 のハッシュ値の計算のやり直しは、していません。

**走らせられなかったものと理由**

- 壊すプログラム b128・b129・b131 そのもの（本物の上で）＝本物を一時的に書き替える作りなので、走らせていない。代わりに、同じ壊し方を写しに当てて測った（上）。
- Q1 の「git show で出して、置き替えて、diff を取る」確かめ方＝hook（require_design_contract_before_run.sh）が、`python3 -B -` の形を「走らせる .py を確定できないコマンド」として止めた。当てる道具の `--design --dry` と、行数の照合に替えた。
- `observe_diag.py --selftest`（全体の自己テスト）＝ファイルに書かない作りかを読み切っていないので、走らせていない。
- `gen_signal_families.py --verify`・`leak_causality_diag.py`・`run_breaks.py`・`pre_audit_check.py --run`・`gen_acceptance.py --write`＝本物を書き替えるので、走らせていない。
- hook に止められたコマンド＝Plan のサブエージェントが2件（上の `python3 -B -` と、承認のスクリプトの名前を含む `git diff HEAD --numstat`）。呼び出し元の CC が、写しを作るときに数件（.py を書く先を名前まで決めていない cp・壊すプログラムの名前を含む python の実行・走らせる前の Edit）。どれも、hook を外さず、hook が示した形（書く先を名前まで書く・Edit で書く・先に走らせる）に直して進めた。
- サブエージェントの所見のファイル（cp61_findings.md）＝サブエージェントがファイルを作れないので、在りません。所見の全文は、サブエージェントの返事で受け取り、この結果に写しました。

**かかった時間とトークン**＝Plan のサブエージェントは、968秒・約41万トークン・道具の呼び出し86回でした（起動の記録の値）。


## 11. 本物のファイルを書き替えていないこと

結果ファイルを書く直前に打った `git status --short` は、237行でした（追跡中の変更 57行・未追跡 180行）。全文は、作業場の `git_status_before_report.txt` に置きました。追跡中の変更のうち、工事のフォルダ（acceptance_archive/verbatim/m2c15-indicator-six-items-20261004/）の34行を除いた23行は、次のとおりです。

```
 M .claude/hooks/approve_impl.sh
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/applied_fixes.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/regime_detection_kb.md
A  v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-indicator-six-items-20261004.01.diff.txt
A  v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-indicator-six-items-20261004.01.md
A  v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-indicator-six-items-20261004.01.sha.txt
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/breaks_frozen.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_families.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_families.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_families_approved.txt
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/impl_functions_frozen.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indicator_switch.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families_approved.txt
 M v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py
 M v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
```

未追跡のうち、この監査に関わる行は、次の5行です。

```
?? .claude/breaks/b128_k1_copc_back_in_ao_loop.sh
?? .claude/breaks/b129_htf_bar_close_two_bars.sh
?? .claude/breaks/b131_industry_map_prev_pivot_gone.sh
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp61_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-04_m2c15_indicator_six_items_20261004_impl_cp61_audit_request.md
```

- 追跡中の変更の23行は、Plan のサブエージェントが監査の初めに見た並びと同じです。この工事と、その前の作業の変更です。監査が作った変更は在りません。
- 監査の終わりの sha256（呼び出し元の CC が計算）は、サブエージェントが監査の終わりに計算して返した値（頭の8文字と末尾の4文字）と同じです。observe_diag.py は `aaa9534b836a75eb175bdee64a5a9bf83ec718cb2514aeee750c751a29d81d77`。indicator_reference_diag.py は `6356221ffc108546ecad0e6322bb12bfe6d4a7de51864c79e53ca82cd5a486c3`。observe_config.json は `fa25c0ea3c5fba1ae339f6987fe8bc6772ef9708701d01508d44edd2c6598f19`。h2_pass.json は `ae0efed75192f676c07eddb3ef04900735d14ca1715f3bab7e5e9cb8c6ee1c45`。g2_pass.json は `c3f41d3e1a3cf3271f2422f0599de26302219add58f7d02ee2ef8161948c7c40`。壊すプログラム3本は `16c5ac34…fa4405`・`e99a59e3…fe73e0`・`0410b75b…19dad8` です。
- 監査が新しく作ったファイルは、作業場 `SDK/.claude/audits/cp61_work/` の中と、この結果ファイルと、呼び出し元のセッションの記録（`.claude/state/sessions/02a0b87b-66bc-4881-bb4f-6a57d7be8560/` の ToDo ほか）と、結果の見直し表だけです。hook が自分で書く記録（`.claude/state/` の read_log ほか）は、hook が書き足しています。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-04_m2c15_indicator_six_items_20261004_impl_cp61_audit_request.md request_sha256=1e33fe8b3b2be5da4c75e3aaa3979afe2746568b004501c0d5c18374ccbb3320 -->
