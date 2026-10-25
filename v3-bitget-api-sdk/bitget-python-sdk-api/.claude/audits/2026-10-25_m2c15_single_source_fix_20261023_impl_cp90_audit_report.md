# 監査結果 cp90 — CP90 — 指標の情報を1つのデータに集約する修正（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-25_m2c15_single_source_fix_20261023_impl_cp90_audit_request.md`
- 依頼書のハッシュ値: 6b2d697d0ddc2fa7225cdf508bf353c03db7e59e62a580eb054112d7ccc54e8e
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 376b9c8291f886e729245d9074bb672bcced1325fd526130d187d963bb4afe48
- 監査が照らしたハッシュ値: 376b9c8291f886e729245d9074bb672bcced1325fd526130d187d963bb4afe48（shasum -a 256 で測った。依頼書・`.claude/state/acceptance.approved`・4回目の控え `m2c15-single-source-fix-20261023.md` の3つと同じ）
- 実施日: 2026-10-25


## 2. 監査対象の型宣言

- コード型：写すプログラム `.claude/state/indicator_review/gen_indicators_draft.py`（699行）と、壊すプログラム8本（`.claude/breaks/ss1_f1〜f8`）。
- 数値型：写すプログラムが書いた `scripts/priority_rebuild/indicators/indicators.json`（記録314種・23の欄・表3つ）の値。
- 文書型：設計書 `.claude/state/acceptance.md` と、承認の控え4本・当てた記録 `applied_fixes.json`。


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

- 依頼書の表と合う。設計書の ACC_IMPL の囲み（acceptance.md:547〜1694）に、実装1〜9 が在る。
- 実装1 は写すプログラムの全文の書き替え、実装2〜9 は壊すプログラムの新しいファイル8本。
- 監査人は、9件の「直した後の文字」を awk で作業場（`cp90_work/impl/`）に取り出して、実物と比べた。

### 当てた記録（applied_fixes.json の名前 design:m2c15-single-source-fix-20261023）

- 依頼書の表と合う。jq で `.applied[]` のうち report が design:m2c15-single-source-fix-20261023 の行を出すと9件。
- num 1〜9 と file が実装の指示の9件と1件ずつ同じ。how は全部「当てた」、at は全部 2026-10-25T14:02:26。

### 実装の前と後の版（git）

- 依頼書のとおり、実装の前は commit fdf27e65。
- 依頼書を作った後に、commit 69944a8d（2026-10-25 15:31）が足された。壊すプログラム8本と indicators.json は、この commit に入った。
- 写すプログラム `gen_indicators_draft.py` は、git に入っていない。`.gitignore:78` の `.claude/state/indicator_review/*` で外されている（`git check-ignore -v` で確かめた）。そのため、実装の前の版は git show で出せない。実装の前の全文は、設計書の実装1 の「直す前の文字」に在る（110行の囲み・最後の空行を除いて109行）。

### 必読に要るファイル（道具が設計書と実装から拾った）

- 依頼書の表の14本は、全部 在る。直す相手9本と indicators.json は、着手前必読の14〜23番に入っている。


## 4. 所見

### 一般の観点

- ①統計学的妥当性：数字の根拠が足りているかを見ます。 ＝ 数え直した数は全部合った（記録314種・オン193・オフ121・名前の違う種類56〔オン32〕・食い違いの記録232件）。ただし、照らす口の「違い0件」は、写すプログラムが読む形に限った数である。by_strategy の範囲が記録に入っていない42種は、どの数にも出ない（R0・Q5 を見る）。修正の番号＝1〜5
- ②リスク管理：損失が出たときや、プログラムが壊れたときの備えが在るかを見ます。 ＝ 写すプログラムと、その写す元の `research/`（2.0M）が、git の外に在る（`.gitignore:76〜79`）。消えると、indicators.json を作り直すことも、照らす口で照らすこともできない。売買の損失に関わる所は、この工事に無い（元のコードを1行も直さない・#11 の git diff が rc 0）。修正の番号＝6
- ③認知バイアス：CC の思い込みで組まれた所が無いかを見ます。 ＝ gen_indicators_draft.py:441 は「選んだ値が空のときは比べない＝値の食い違いの一覧と同じ比べ方」と書く。前の一覧（value_conflicts_20261024.md）の比べ方を正しいものとしてそのまま使ったため、片側だけに値が在る範囲が、一覧にも記録にも残らなかった。修正の番号＝1〜5
- ④ソフトウェア工学：プログラムの作りが正しいかを見ます。重複・壊れやすさ・テストの抜けが、見る物です。 ＝ 見つけたことは5つで、どれも結論は変えない。(1) :570 の314の照らしは、記録を TABLE と EXTRA_OF の鍵から作るので、重なりの止め（:93・:512）が先に効き、この照らしで落ちる道が無い。(2) coverage() は「決まった欄」「自己テストの見本」の行を中身を見ずに通す（:607〜608）。(3) code_copy の「代入が見つからない」は、名前が行の範囲の中に文字として在れば通る（:318）。(4) ss1_f1 は、完成の条件 #1 のコマンド（引数なし）ではなく --verify を測る（ss1_f1_count.sh:24）。(5) 自己テストは decide() の2件だけで、build() の止まる道（:564〜569）は試さない。ただし ss1_f7 が実物で試していて、breaks.json の no 7 は match true。修正の番号＝なし
- ⑤再現性：同じ手順で、同じ結果が出るかを見ます。 ＝ 同じ写す元なら同じ indicators.json になる。監査人が写すプログラムを引数なしで走らせると「もう在り、写す元から作り直した物と同じ（書かない）」と出た。走らせる前と後で indicators.json の sha256 は 71e0b7bf05189f9ed15f29958dae472a4285452f6e46f053365bca01b69383a5 で同じ。ただし、作るプログラムが git の外に在るので、別の手元では同じ手順を踏めない。修正の番号＝6
- ⑥実行プロセス：CC が、決めた流れのとおりに進めたかを見ます。 ＝ 承認4回・当てる道具で9件を当てた・当てた記録9件・完成の条件の状態の欄は承認のプログラムが書いた、の流れは設計書のとおり。依頼書を作った後に commit 69944a8d で indicators.json を入れたので、依頼書の「実装の後＝作業中の変更」と形が違う。scripts/priority_rebuild の下の fdf27e65 からの差は indicators.json の追加だけで、結論には使わない。修正の番号＝なし
- ⑦主エージェントバイアス：CC が、自分に都合よく判定した所が無いかを見ます。 ＝ 照らす口（--verify）は、記録を写すプログラムの作り直しとしか比べない。設計書 7-4 は、この穴を自分で書いている。それでも CC は、依頼書の経緯で「--verify 違い0件」を全部写した根拠のように使っている。その穴の中に、42種の範囲が落ちていた。修正の番号＝1〜5

### R0 — この工事は、要件定義の何番を満たすための物か。要件定義に反する所は無いか（優先度 A）

- R0-1：結ぶ要件（3番の1〜5・4番・5番・6番）は、工事の目的に合う。中身に一番近いのは6番の「誤りは置き場の1か所を直せば済み」（core_requirements_full.md:92〜96）と「指標一覧からだけ呼び出す」（:85）。抜けている要件は無い。
- R0-2：反する所が1つ在る。
  - 4番は「範囲で探せるという上記要件は絶対」と書く。設計書1のゴールは「いまの置き場の値が全部入っていること」（やることの表.md:118）。
  - ところが、オンの42種で、indicator_params_by_strategy.json の「範囲」が、indicators.json のどの欄にも入っていない。
  - 例：LeeMykland の by_strategy の範囲は [{"下限":16,"上限":270}]。記録の「範囲」は null で、「教科書の出どころ」の by_strategy からも外され、「食い違いの記録」にも無い。indicators.json の中の `"上限": 270` は0件。
  - 原因の行は2つ。gen_indicators_draft.py:440〜443 の `skip_empty=True` が、選んだ値（search_limits.json の範囲）が None のときに比べるのをやめる。:494〜495 が、by_strategy の「範囲」を教科書の出どころの欄から外す。
  - 設計書3で by_strategy を消すと、この42種の範囲は indicators.json から戻せない。
- 乱数・CC が決めた数の一覧に当たる所は無い（写すプログラムに random は無い）。

修正の番号＝1・2・3・4・5

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

- 9件とも同じ。
- 監査人は、設計書の9件の「直した後の文字」を取り出して、実物9本と diff した。違いは9本とも、設計書の囲みの最後の空行1行だけだった（例：1_after.txt が700行・実物が699行）。
- 当てる道具は、新しいファイルの全文を `.rstrip("\n") + "\n"` で書く（.claude/tools/apply_audit_fix.py:1024）。新しいファイルが当て終わりかも、rstrip で比べる（:583）。そのため、空行1行の違いは道具の決まりのとおりである。
- 写すプログラムは git に入っていないので、実装の前の版との差は、設計書の実装1 の「直す前の文字」から取った。

修正の番号＝なし

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

- 無い。
- 写すプログラムの699行は、実装1 の全文書き替えに全部入る（Q1 の diff で、空行1行のほかの差は0行）。壊すプログラム8本も、新しいファイルの全文に全部入る。
- 依頼書の自己申告4の5本（作業中の変更）は、この工事の対象のファイルではないので、差分に入れていない。

修正の番号＝なし

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

- 合う。report=design:m2c15-single-source-fix-20261023 の9件は、num 1〜9 と file が、実装の指示の9件と1件ずつ同じ。
- how は9件とも「当てた」。「もう当て終わっていた」の件は0件なので、どの実行で当たったかを確かめる件は無い。
- 時刻は9件とも 2026-10-25T14:02:26。indicators.json の更新の時刻（14:02）と合う。

修正の番号＝なし

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（優先度 A）

要望1「指標の情報を1つのデータに集約して、そこからしか指標の情報を取れない状態にする」を、2つに分けて判定した。

- 「そこからしか取れない」：設計書1の範囲の外である。
  - やることの表.md の Y-03（:29）・Y-04（:30）と、経緯「設計書は3本に分けました（まこさん 2026-10-24「じゃあ３本にして」）」（:113）、「設計書1では、2159件は減りません」（:119）が、この半分を設計書2・3に回している。
  - 要件定義の9番は、実装の監査で見るのを「設計書のとおりか」だけにしている。そのため、この半分が未達なことを Critical にしない。
- 「1つのデータに集約」：設計書1の範囲の中で、満たしていない所が1つ在る。
  - オンの42種で、by_strategy の範囲が indicators.json に入っていない（R0 に書いた）。
  - 42種＝AO%・KST・STC・STCstoch・PSAR加速・UO・SQZ_ON・HWC幅%・MASSI・THERMO%・swing高値距離・swing安値距離・SMC_SWEEP・close vs HILO%・close vs HWMA%・close vs MAMA%・close vs FAMA%・close vs CKSPl%・close vs CKSPs%・close vs PSAR%・PSAR反転・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・LeeMykland・帯スイング・帯スイング1時間ATR・帯pivot・帯pivot1時間ATR・帯pivot前週・帯pivot前週1時間ATR・帯VA・帯VA1時間ATR・LeeMykland_E36版・THERMO原作%・SQZ_ON_Carter・close vs MAMA_HL%・close vs FAMA_HL%（監査人が jq で数えた・42種とも オン）。
  - やることの表.md:17 の F-6 は「選ばなかった側の値と置き場は、記録の「食い違いの記録」の欄に残す」と書く。実装は、この文に反している。
  - 実装は設計書の 4-20 の文字のとおりだが、4-20 の文字そのものが、同じ設計書の F-6 とゴールに反している。
  - 依頼書の Q7 の決まり（1つでも満たしていない要望があれば Critical）により、Critical とする。
- 同じ「選んだ値が空なら比べない」で、ほかの欄の値が落ちていないかも数えた。列を作る値が空で、by_strategy の今の値か observe_config.json の material_params に値が在る種類は0種だった。落ちているのは範囲の42種だけである。

修正の番号＝1・2・3・4・5

### Q8 — 承認のプログラムが測れない完成の条件の5行は、設計書のとおりに通るか（優先度 A）

- 5行とも、設計書の条件の文のとおりに通る（監査人が SDK の置き場で走らせた）。
  - #2：`! grep -n '"indicators_draft' …` ＝ rc 0（当たる行0件）。
  - #7：`! grep -n -e '"順張り値"' -e '"行き過ぎ"' …` ＝ rc 0。後ろの --verify も rc 0。写すプログラムの中の区分の名前は、:48 の「向きつき」だけ。
  - #8：--selftest ＝ 2件とも ✅・rc 0・2秒。
  - #10：jq ＝ true・rc 0。
  - #11：`git diff --quiet -- scripts/priority_rebuild` ＝ rc 0。
- 承認のプログラムが測れる形に直す必要は無い。
  - #2 と #7 は、壊すプログラムがもう守っている（breaks.json の no 2・no 7 が code 1・expect 1・match true）。
  - #8 は、それ自体が自己テストである。
  - #10 と #11 は、読むだけの決まった判定で、rc で確かめられる。
- 注意が1つ在る。indicators.json は commit 69944a8d で git に入った。そのため、修正5 で作り直した後は、#11 の git diff が indicators.json の差を拾う。#11 の文（いま在るファイルに差が無い）は、作り直しの後に commit するまで成り立たない。

修正の番号＝なし

### Q9 — indicators.json の記録が、設計書の 4-8 の形と1件の例のとおりか（優先度 A）

- 形と1件の例は、4-8 のとおりである。
  - RSI：列を作る値 [[5],[7],[9],[14],[21]]・範囲 int 2〜21・代表の固定値 [[7]]／[[14]]・出口の水準 RSI_OB・RSI_OS（70／30・Wilder 1978）・V9 の名前 RSI・食い違いの記録に by_strategy の今の値 [[7],[9],[14],[21]]。4-8 の例と同じ。
  - STC：コードの中の既定値 tcl 10・f_ 12・s_ 26・fac 0.5。4-8 の例と同じ。
  - 転換線：名前に出ない軸の最初の値がスキャル・デイトレとも [[9,26,52]]。4-8 の例と同じ。
  - LeeMykland：方向の区分「向きつき」・性質 ["trend"]。3-2 の11件目と同じ。
  - ADXR（オフ）：オン/オフ「オフ」・性質 ["none"]。
- 別枠の材料13種（CVD・L-S比・taker_ls・W%・mid・res_hi・res_lo・sup_hi・sup_lo・下半分位置・帯内位置%・時刻・曜日）：
  - 同上の置き換え：res_lo・sup_hi・sup_lo の流儀は res_hi と同じ文、mid の方向の区分は「価格水準」。曜日の流儀は時刻の文。
  - 方向の区分：W% は「状態量」。時刻は「状態量（セッションの癖の材料）」である。TIME_REF の houkou に「＝」が無いので、split("＝")[0] で文がそのまま入る。これは engine_tuner_gen.py:1278 の _kubun_of と同じ取り方で、4-8 の文のとおり。
  - レンジ幾何のパラメータの置き場5つ：W% の「ほかの置き場の値」に、V25_K 0.5（e37_scalp.py:213）・ZONE_TOL 0.003・ZONE_TOUCH 2・ZONE_LOOKBACK 168（build_range_gate_dashboard.py:50〜52）・_adaptive_tol_1h の lo 0.0015・hi 0.006（build_regime_gate_rg.py:262）が在る。
  - 時刻の閾値の範囲：[{lo 6, hi 18, kind int, 出どころ hour_range}]。閾値の範囲が null でないのは時刻だけ。
- 4-8 と違う所が4つ在る。どれも値は失われていないので、結論に使わない（修正の指示は出さない）。
  - (1) 4-8 の「ほかの置き場の値」は「4-4 の1〜8 に無い置き場」を写すと書く。実物は、CVD に DEMAND_REF、W% ほか8種に RANGE_GEO_REF、時刻・曜日に TIME_REF も写している（OWN〔:50〜51〕にこの3つが無いため）。
  - (2) 置き場の書き方がそろっていない。一覧の行は scripts/priority_rebuild からの相対（例 `observe_diag.py:5092`）、CP89 の5つは scripts からの相対（`priority_rebuild/e37_scalp.py:213`）。
  - (3) 「式の文」は lambda だけでなく、`_reg(...)` の行の全体が入る。
  - (4) 3-2 の1件目は、V9 の名前と VWAP の違いを「記録の注記に残す」と書く。実物は「食い違いの記録」の欄に残している。

修正の番号＝なし

### Q11 — 設計書の監査 CP88・CP89 の修正が、監査の書いた中身のとおりに実装に出ているか（優先度 A）

1つ目（実装に関わる修正の1件ずつ）：全部、監査の書いた中身のとおりに出ている。

- CP88 の修正1：OWN から CONST_REGISTRY を外した（gen:50〜51）。CONST_REGISTRY は区分の言葉の表に入る。
- CP88 の修正5（案A）：DECIDED_PROP の性質が ["trend"]（gen:48）。LeeMykland の記録の性質も ["trend"]。
- CP88 の修正9（案A）：F-7 の grep は「向きつき」を見ない。写すプログラムの中の区分の名前は :48 だけ。
- CP88 の修正10：別枠の13種の記録を足した（gen:507〜544）。まこさんの「全部修正する」「ok」の後の決めたとおり。
- CP88 の修正11：閾値の2つの欄を足した（gen:45・:499〜500・:538〜539）。
- CP88 の修正13：F-2 の grep を `'"indicators_draft'` にした（ss1_f2_out.sh:26）。
- CP88 の修正15：indicators.json を作り直した（14:02）。
- CP88 の修正6（まこさんが当てないと決めた）：当てた記録に「まこさんが当てないと決めた」と在り、実装はそれと矛盾しない。
- CP89 の修正1（gen:545〜563）・修正5（gen:529）・修正6（gen:82〜94）・修正10（gen:691）・修正11（gen:687）：監査の「直した後の文字」と同じ文字が実物に在る。

2つ目（CC が手で入れた所・そろえた所）：監査の指示からのずれは見つからなかった。照らした所は、CP88 の修正10・11・15・17、CP89 の修正4・9・12・13、やることの表の F-3・4-4 の9行目・4-5 の行。

- 補足：CP88・CP89 のどちらも、by_strategy の範囲が片側だけに在る種類を見つけていない。Q7 の Critical は、2回の設計書の監査の後にも残っていた穴である。

修正の番号＝なし

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

- 実装の囲み（ACC_IMPL_START〜END）の sha256 は、.02・.03・4回目の控え・いまの設計書で同じ（4d63e2c8…）。
- .01 だけ違う（6de4bdf1…）。違いは、実装1 の「根拠の抜き書き」の1行と、囲みの頭の hash の1行だけで、コードの文字は同じ。
- 控えの sha256 は、それぞれの .sha.txt と同じ。4回目の控えは、承認の印とも同じ。
- そのため、どの版で当てても実装は同じになり、違いは実装に影響しない。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

- 一覧の F-1〜F-8 と、4-4 の処理の流れ、4-5 の止まる条件11行は、写すプログラムに全部在る。
  - F-1＝:570〜571・:679〜685／F-2＝:40／F-3＝:79・:356〜371・:574〜586・:546〜563／F-4＝:42〜46・:472〜503・:504〜505／F-5＝:379〜391／F-6＝:438〜471／F-7＝:48・:220〜229・:373〜376・:564〜569／F-8＝:620〜647。
  - 4-5 の止まる条件＝:65〜69・:270〜271（読めない）／:318〜319（代入が無い）／:594〜617・:676〜678（入らない行）／:390〜391（つながらない）／:570〜571（記録の数）／:512〜513・:91〜93（重なり）／:557〜558（置き場5つ）／:564〜569（方向・役割）／:644〜647（値の違い）。
- 一覧に在るのに満たしていない物が1つ在る。
  - F-6（やることの表.md:17）の「選ばなかった側の値と置き場は、記録の「食い違いの記録」の欄に残す」。42種の by_strategy の範囲が、どこにも残っていない（Q7）。
- 結論に使わない違いが2つ在る。
  - 4-4 の5「52種」と F-5「56種（オンでは32種）」の数を、プログラムの中で照らしていない。書く走行の画面に出るだけ（:687・:692）。いまの値は jq で 56／32 と合う。
  - 4-5「写す元のファイルが読めない」の一部（module_assign の :99・:552 の read_text・:72〜78 の import）は、決めた文で止まらず、Python のトレースバックで落ちる。トレースバックにパスは出る。
- 実装の指示に在るのに、一覧に無い物は無い。

修正の番号＝1・2・3・4・5

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

- 11行とも rc 0（監査人が SDK の置き場で走らせた）。
  - #1＝「もう在り、写す元から作り直した物と同じ（書かない）」・21秒。
  - #3〜#6・#9＝--verify「照らした＝記録 314 種 × 23 欄・表 3つ・直す相手の一覧の「①写す」の行 730 行／✅ 違い 0 件」・18秒。
  - #2・#7・#8・#10・#11 は Q8。
- 条件の文の数も、実物で照らして合った（記録314・名前の違う種類56〔オン32〕・食い違いの記録232件）。
- ただし #3・#6・#9 の「写す元と違わない」は、写すプログラムが読む形に限って成り立つ。42種の by_strategy の範囲は、どの行も見つけない。#6 の「選ばなかった側が食い違いの記録に在る」は、この42種では成り立たない。

修正の番号＝1・2・3・4・5

### Q10 — 4回の承認の間に、当てた実装と設計書が食い違っていないか（優先度 B）

- いまの写すプログラムと壊すプログラム8本は、4回目に承認した設計書の実装の指示と、1文字も同じ（Q1・設計書の囲みの最後の空行を除く）。
- 3回目の控え（.03.md）と4回目の控えの diff は、完成の条件の #1・#3・#4・#5・#6・#9 の状態の欄の6行だけ（未着手 → ✅済）。CC の diff と同じ。
- 写すプログラムは「git に入っていない」のではなく、.gitignore で外されている（`.gitignore:78`）。写す元の `research/` も同じ（②・⑤）。

修正の番号＝6


## 5. 外部検索

### 検索 1 — 指標の分類の外の標準

- URL：https://sentimentrader.com/education/technical-indicators（監査人が WebFetch で開いた）
- 逐語：「This section groups commonly used indicators into four main categories — Trend, Momentum, Volatility, and Volume」
- 照らした結果：外の4つの群は、indicators.json の役割の区分の表（7行＝向き・強さ・勢い・行き過ぎ・値動きの幅・出来高・位置）に全部当たる（Trend＝向き・強さ／Momentum＝勢い・行き過ぎ／Volatility＝値動きの幅／Volume＝出来高）。欠けている区分は無い。
- 方向から性質への対応の表（5行）に、momentum に当たる性質は無い。ただし、この工事は いまの置き場の値を写す工事で、表の元（gen_indicator_table.py:51 の HOUKOU2PROP）と1件も違わないことが照らす口で確かめられている。表に1行を足すのは、indicators.json を正本にした後（設計書 F-7 の文）なので、この実装の欠陥ではない。

### 検索 2 — 1つのデータに集める作りの外の標準

- URL：https://cdn.jsdelivr.net/npm/@tansuasici/claude-code-kit@1.21.0/tasks/lessons/2026-07-08-generated-config-single-source.md（監査人が WebFetch で開いた）
- 逐語：「Two hand-maintained sources of the same structure always drift.」「commit the generated file.」「a CI `--check` that regenerates and diffs」
- 照らした結果：
  - 合う所：照らす口（gen_indicators_draft.py:620〜647）は、写す元から作り直して1件ずつ比べる＝「regenerates and diffs」と同じ作り。作った indicators.json は commit 69944a8d で git に入った＝「commit the generated file」と同じ。
  - 合わない所：作る側（写すプログラムと写す元の research/）が git の外に在る（.gitignore:78）。作った物だけが残り、作り直す手段が残らない（修正6）。
  - 合わない所：照らす口は「作り直した物」とだけ比べるので、作る側が読み落とした値（42種の範囲）は、照らしても見つからない（修正1〜5）。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

確かめないまま進めてよい。.01 といまの版の違いのうち、実装の囲みの差は、実装1 の根拠の抜き書きの1行と囲みの頭の hash の1行だけで、コードの文字は同じ（Q4）。ほかの差（7-7 の「<モジュール直下>」・ACC_CHECKLIST・SPEC）は、照合の数え方の直しで、実装の文字に関わらない。

### 自己申告 2

確かめないまま進めてよい。実装の囲みの sha256 は .02 といまの版で同じ（4d63e2c8…）。

### 自己申告 3

確かめないまま進めてよい。.03 と4回目の控えの違いは、完成の条件の状態の欄の6行だけ（Q10）。.03.diff.txt が0バイトなのは、承認のプログラムが測った後に状態の欄を書いたためで、実装に関わらない。

### 自己申告 4

確かめないまま進めてよい。5本は、この工事の実装の指示が当てた物ではない。Q1・Q2 は、対象の9本だけで取った。承認の瞬間に汚れていた .py（dirty.json）は2本（require_design_check_before_approval.py・gen_acceptance.py）で、どちらもインフラの直しである。


## 7. 総合判定

### 結論と件数

- 結論＝CONDITIONAL-GO（根拠＝当てた実装は、4回目に承認した設計書の 4-20 と1文字も同じで、当てた記録9件も合い、完成の条件11行も rc 0 で通る。ただし、設計書1の範囲の中の「1つのデータに集約」と、やることの表の F-6「選ばなかった側の値と置き場は、記録の「食い違いの記録」の欄に残す」に、4-20 の文字と実装が反している。オンの42種で、indicator_params_by_strategy.json の範囲が indicators.json のどこにも入っていない。修正1〜5 で埋まり、作りの向き〔いまの置き場から1回写し、作り直して照らす〕は変えずに済むので、NO-GO ではない）
- Critical＝5
- Major＝0
- Minor＝0
- Process＝1


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json
直す箇所: 8
直す前の文字:
~~~
{\"by_strategy の範囲\": [[d.get(\"下限\"), d.get(\"上限\")] for d in b.get(\"範囲\") or []]})
~~~
直した後の文字:
~~~
{\"by_strategy の範囲\": [[d.get(\"下限\"), d.get(\"上限\")] for d in b.get(\"範囲\") or []]}, skip_empty=False)
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-fix-20261023/やることの表.md:17「| F-6 | 置き場どうしで違う値を、1つの値にする | 直す | .claude/state/indicator_review/gen_indicators_draft.py | :90〜94（conflicts を作る所） | 系統だけを、書き替えずに並べて conflicts.json に出す | 系統・パラメータ・範囲・オン/オフは、3-2 の1件目の決め方で1つの値にする。選ばなかった側の値と置き場は、記録の「食い違いの記録」の欄に残す | okd_plan5_20261024.txt:V22・要件定義書 §7 の R11・3-2 の1件目 |」
状態: 確定

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-fix-20261023/okd_an_ev_20261025.txt
直す箇所: 10
直す前の文字:
~~~
impl_4-20_20261024.json sha256=9d10f03c158e6a705d9bf871094c22c4b0b10c1270639a123b801c4e95992c5d
~~~
直した後の文字:
~~~
impl_4-20_20261024.json sha256=<修正1 を当てた後の impl_4-20_20261024.json の sha256>
~~~
根拠の抜き書き: .claude/tools/gen_acceptance.py:343「        bad.append(f"【4-20】＝実装の指示のファイルのハッシュ値が、OK された案と違う（案 {m.group(2)[:12]}… ／ 今 {got[:12]}…）＝ファイルが変わっている")」
状態: 未決

#### 修正 3
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --write
~~~
根拠の抜き書き: .claude/state/acceptance.md:14「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --write`。」（監査人は走らせていない。秒数は測っていない。修正1 で実装の指示のハッシュ値が変わるので、修正2 の後に、まこさんの OK をいただいてから走らせる。作り直した設計書は、まこさんの承認が要る）
状態: 未決

#### 修正 4
対象のファイル: .claude/state/indicator_review/gen_indicators_draft.py
直す箇所: 456
直す前の文字:
~~~
                 {"by_strategy の範囲": [[d.get("下限"), d.get("上限")] for d in b.get("範囲") or []]})
~~~
直した後の文字:
~~~
                 {"by_strategy の範囲": [[d.get("下限"), d.get("上限")] for d in b.get("範囲") or []]}, skip_empty=False)
~~~
根拠の抜き書き: .claude/state/indicator_review/gen_indicators_draft.py:442「        if skip_empty and chosen in (None, "", []):」（選んだ値＝search_limits.json の範囲が None の42種で、by_strategy の範囲を比べずに捨てる行。修正1 と同じ文字を、実装の側に当てる。修正3 の作り直しと、まこさんの承認の後に当てる）
状態: 確定

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
rm v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json && python3 .claude/state/indicator_review/gen_indicators_draft.py && python3 .claude/state/indicator_review/gen_indicators_draft.py --verify
~~~
根拠の抜き書き: .claude/state/indicator_review/gen_indicators_draft.py:683「        raise SystemExit(f"❌ {OUT} はもう在り、写す元から作り直した物と違う（1回だけ書く・違いは --verify で見る）")」（修正4 の後は、書く口が上書きしないので、消してから書く。監査人は走らせていない。見込みは監査人の実測で、書く21秒＋照らす18秒。indicators.json は commit 69944a8d で git に入っているので、消してよいかは まこさんが決める。作り直した後は、完成の条件 #11 の git diff が indicators.json の差を拾うので、commit してから #11 を測る）
状態: 未決

### Major

なし

### Minor

なし


## 9. CC プロセス欠陥対策

### Process

#### 修正 6
対象のファイル: .gitignore
直す箇所: 79
直す前の文字:
~~~
!.claude/state/indicator_review/make_fix_plan.py
~~~
足す文字:
~~~

!.claude/state/indicator_review/gen_indicators_draft.py
!.claude/state/indicator_review/research/
~~~
根拠の抜き書き: .gitignore:76「#   同じフォルダのほかのファイル（調べた結果・表を作るプログラム）は、git に入れるかが まだ決まっていない＝戻さない。」（写すプログラムと写す元の research/〔2.0M〕が git の外に在ると、indicators.json を作り直すことも照らすこともできない。git に入れるかは まこさんが決める）
状態: 未決


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

開いたファイルと行（監査人）
- 依頼書：全文（1〜516）
- `.claude/state/acceptance.md`：544〜560・1360〜1420・471〜503・1910〜1932・見出しの grep
- `.claude/state/indicator_review/gen_indicators_draft.py`：全文（1〜699）
- `.claude/breaks/ss1_f2_out.sh`・`ss1_f3_source.sh`・`ss1_f5_name.sh`・`ss1_f7_prop.sh`：全文
- `.claude/tools/apply_audit_fix.py`：195〜230・570〜600
- 控え .01・.02・.03・4回目：sha256・実装の囲みの sha256・.01／.02 の囲みの diff・.03／4回目の diff・.02.diff.txt
- `m2c15-single-source-fix-20261023.breaks.json`・`.dirty.json`：全文
- `applied_fixes.json`：この工事の9件・CP88／CP89 の行（jq）
- `indicators.json`：RSI・W%・別枠の13種・時刻・CVD・LeeMykland・STC・2つの表・数（jq）
- `scripts/priority_rebuild/engine_tuner_gen.py`：1268〜1290
- `scripts/priority_rebuild/indicator_reference_diag.py`：TIME_REF の houkou の行
- `.claude/state/indicator_params_by_strategy.json`：STC・LeeMykland・42種の数え（jq）
- `やることの表.md`：F-6・ゴールの grep（:17・:41・:116〜118・:188・:269・:285）
- CP89 の結果：298〜381・346〜351・422〜427・478〜491
- `okd_an_ev_20261025.txt`：8〜12
- `.gitignore`：74〜80
- git：status・log・show --stat 69944a8d・check-ignore
- Plan agent が開いた物は、Plan agent の報告の一覧（やることの表.md 全文・lib.sh・ss1 の8本・CP88 38〜497・CP89 45〜492・gen_indicator_table.py ほか）

走らせたコマンドと結果と秒数（全部 SDK の置き場か、リポジトリの根）
- `shasum -a 256 .claude/state/acceptance.md` ＝ 376b9c82…（1秒未満）
- 9件の直した後の文字と実物の diff ＝ 9本とも空行1行の差だけ（1秒未満）
- `python3 .claude/state/indicator_review/gen_indicators_draft.py` ＝ rc 0・「もう在り…同じ（書かない）」・21秒
- `python3 .claude/state/indicator_review/gen_indicators_draft.py --verify` ＝ rc 0・違い0件・18秒
- `python3 .claude/state/indicator_review/gen_indicators_draft.py --selftest` ＝ rc 0・2秒
- `! grep -n '"indicators_draft' …` ＝ rc 0／`! grep -n -e '"順張り値"' -e '"行き過ぎ"' …` ＝ rc 0（1秒未満）
- 完成の条件 #10 の jq ＝ true・rc 0（1秒未満）
- `git diff --quiet -- scripts/priority_rebuild` ＝ rc 0（1秒未満）
- 42種の数え（jq）＝ 42（オン 42）（1秒未満）
- 列を作る値が空で他の置き場に値が在る種類の数え（jq）＝ 0（1秒未満）
- indicators.json の sha256 ＝ 走らせる前後とも 71e0b7bf…383a5
- WebFetch 2件（sentimentrader.com・cdn.jsdelivr.net）＝ 逐語を取れた

走らせられなかったものと理由
- 壊すプログラム8本は、監査人は走らせていない。本物のファイル（indicators.json・observe_diag.py・gen_indicator_table.py・写すプログラム）を一時的に書き替える作りのため。承認のときの記録（breaks.json）で、8本とも match true を確かめた。
- 修正3（設計書の作り直し）と修正5（indicators.json の作り直し）は、本物を書き替えるので走らせていない。
- Plan agent は、WebFetch と grep 2本が「分類器の判定が無い」で止まった。外部検索の逐語は、監査人が WebFetch で取り直した。


## 11. 本物のファイルを書き替えていないこと

監査の間に監査人が書いたファイルは、作業場の `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp90_work/`（cp90_result.md・impl/ の18本）と、hook が書くように求めたセッションの記録2本（`.claude/state/sessions/1d116e4d-8d25-4b80-987d-d15a9597cf87/lessons.md`・`diagnosis.md`）だけである。下の `git status --short` の出力に、この工事の対象のファイル（写すプログラム・壊すプログラム8本・indicators.json）は出ていない。

`git status --short` の出力（2026-10-25・結果ファイルに書く直前）：
- 変更の行（M・D・A）＝0行。`git status --short | grep -v '^??'` の出力は空。
- 未追跡の行（??）＝234行。このうち監査人が作った物は `?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp90_work/` の1行だけ。ほかの233行（過去の監査の作業場・控え・ログほか）は、監査を始める前から在った。
- `git status --short | grep -e cp90_work -e indicator_review -e breaks/ss1 -e indicators/` の出力は、次の1行だけ。

```
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp90_work/
```

- 写すプログラムは .gitignore で外されているので git status に出ない。監査人は書き替えていない（Read と走らせただけ・引数なしの走行は「同じ（書かない）」で終わった）。indicators.json の sha256 は監査の前後とも 71e0b7bf…383a5。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-25_m2c15_single_source_fix_20261023_impl_cp90_audit_request.md request_sha256=6b2d697d0ddc2fa7225cdf508bf353c03db7e59e62a580eb054112d7ccc54e8e -->
