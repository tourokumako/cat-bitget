# 監査結果 cp46 — CP46 — M2-E-4e の設計書（前処理の部品 ts_pos・元データの欄 pre_win・段2c の「動く線」の候補・動く線を使う走行の余白 stage_warm）は、法則 R6 の逐語とまこさんの決定どおりの形になるか。書いたとおりに「実装の指示」をプログラムが当てられるか

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-27_m2e4e_r6_moving_line_design_cp46_audit_request.md`
- 依頼書のハッシュ値: c9d0301bbd8db079545a027de93ab1c3b54423b91627e7e6b478eb9530b30245
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 22287788eef776fc83caeb466605559c3649ade6a62ed99f66e0ce4890c57baa
- 監査が照らしたハッシュ値: 22287788eef776fc83caeb466605559c3649ade6a62ed99f66e0ce4890c57baa（`shasum -a 256 .claude/state/acceptance.md` を監査の最初・監査役の最後・結果を書く前の3回測った。3回とも依頼書と一致）。元データ `acceptance_src.json` は 0053a412bc8598c598fee8f4b6b61b5393720aad67a698848f957ab31cbba7bb で、commit dfea4be の本文の値と一致し、`git diff HEAD` の差は0。
- 実施日: 2026-09-27

## 2. 監査対象の型宣言

- **文書型**＝設計書 `acceptance.md`（1,843行）と、その元データ `acceptance_src.json`（421行）。
- **コード型**＝実装の指示28件が当たる相手（`engine_tuner_exec.py`・`engine_tuner_gen.py`・`condition_parts_diag.py`・`gen_regime_kb.py`・`m2_stage_candidates.json`・`condition_parts.json`・壊すプログラム b109〜b112）。
- **数値型**＝窓の本数 52,596本・余白 242.625日・案の番号の届く順位。
- ★監査役（Plan サブエージェント）は読み取りだけの決まりで動いたので、写しを作って走らせることはしていない。コード型の判定は、全部 実物を読んで流れを追った静的なもの。

## 3. 監査対象の事実データの確認

### 監査対象の事実データ（依頼を出した CC が走らせたもの）

| # | コマンド | 監査が打った結果 | 一致 |
|---|---|---|---|
| 1 | `grep -c 'near the low end of its six-month range' …/regime_laws.json` | 1 | 一致 |
| 2 | `grep -n 'if stage == "stage2a":' …/engine_tuner_gen.py` | 2893 | 一致 |
| 3 | `grep -c 'pre_win' …/m2_stage_candidates.json` | 0 | 一致 |
| 4 | `grep -c '"ts_pos"' …/engine_tuner_exec.py` | 0 | 一致 |
| 5 | `grep -n -F '_pre_opts = [None] + ex.pre_ops(same_unit=False)' …/engine_tuner_gen.py` | 1805 | 一致 |
| 6 | `grep -n 'WARM = pd.Timedelta' …/engine_tuner.py` | 99 | 一致 |
| 7 | `grep -rn "WARM\b" scripts --include='*.py'` | 読む所は12か所＝gen:7731（本走）・exec:3071/3352/3627（恒等3本）・leak_causality_diag:315（H2）・regime_r9_diag:309（M2-F）・ほか6か所（fire_diag:377・streak_scope_diag:128・dashboard/build_regime_from_tuner:177・tuner_backcalc:235・tuner_window_diag:167・engine_tuner.py:577） | 一致 |
| 8 | 依頼書と同じ語で `.claude/breaks` を grep -rln | b78・b92・b93・b79・b82 | 一致 |
| 9 | `git diff HEAD -- （直すファイル6本） \| grep -c '^@@'` | 0 | 一致 |
| 10 | `gen_acceptance.py --write` | 走らせていない（本物の設計書を書き替えるため） | データ不足（理由＝書き込む道具） |
| 11 | `require_design_check_before_approval.py --try` | 走らせていない（監査役は読み取りだけ） | データ不足（理由＝読み取りだけの決まり） |
| 12 | `pre_audit_check.py --run` | 走らせていない（記録を書くため） | データ不足（理由＝書き込む道具） |
| 13 | `pre_audit_check.py --verify` | 走らせていない（同上） | データ不足（理由＝同上） |

- 追加で確かめたこと＝実装の指示の「直す前の文字」24件を `grep -c -F` で数えた。24件ともちょうど1件。複数行のもの（2・10・11・27）は1行目が1件で、組にしても1件。10の2行目は単独だと3件、11の1行目は単独だと3件在るが、組にすれば1件。

## 4. 所見

### 一般の観点

- ①統計学的妥当性 ＝ PASS（最小〜最大の間の位置は、R6 の逐語と StockCharts の Bollinger の定義に合う。閾値 q50 は決めてほしいこと1 に残っている）
- ②リスク管理 ＝ PASS（売買のロジック・H1・審判に触れない）
- ③認知バイアス ＝ PASS（値を選ぶために数字を拾う形は無い）
- ④ソフトウェア工学 ＝ FAIL（A2 の所見1・A3 の所見2＝本走の余白の相手と、案の指紋の変化）
- ⑤再現性 ＝ FAIL（A3 の所見2＝再開の鍵と重複の判定がずれる）
- ⑥実行プロセス ＝ FAIL（依頼を出した CC は当てた後のコードを1つも走らせていない。L-605 の grep の語が足りない。監査に出す前のチェックの手順が無い）
- ⑦主エージェントバイアス ＝ FAIL（「本走＝動く線を使う走行」を、届く順位を計算せずに決めている＝所見1・P2）

### A0 — 完成の条件14行の壊し方と壊すプログラム4本（新設 b109〜b112）が、条件の文そのものを壊して測れる形か（優先度 A）

- **A0-a**＝静的には、b109 と b112 は ❌ T47 になる。b111 は5本目が NaN になって期待の 1.0 と違うので ② が落ちる。b110 は乱数の道に ts_pos が入って案が変わるが、selftest の途中に早い return は無く（最初の return は gen:7634）、T1-C6e は `_lv_ops[0]`＝ts_pos でも検証を通るので、T47 まで届く。**4本とも走らせていない（データ不足・理由＝監査役は読み取りだけ）。**
- **所見3（Minor）**＝T47 の⑤は、関数 `stage_warm` の戻り値しか見ていない。本走が `et.WARM` で読むまま（実装の指示27を当てない形）でも T47 は通る。守っているのは DESIGN_CONTRACT の must_use の「名前が在るか」だけ。
- **A0-b**＝成績表や型の表から BB幅 の固定の線が0本になると、T47 の③は「1本も無い」で落ちる。落ちる側に倒れるので、黙って通る道は無い。
- **A0-c**＝見本「直近20本の範囲の中の位置 ≤0.2」は、実行器（`_eval_cond` → `_apply_pre`）と独立の実装 `p_ts_pos` を実データの RSI7__5m で比べる形。ただし `_BARS = 20000`（condition_parts_diag.py:41）なので、窓 52,596 は測らない。走る時間の実測は worklog に見つからなかった（データ不足）。
- **所見8（Minor・A0-d）**＝恒久71番（permanent_rules.md:388「…完成の条件に載せない」）に照らすと、#7・#8（`.claude/tools/gen_regime_kb.py`＝読むための道具）を完成の条件に載せていることが外れる。さらに #8 の文は「自己テストと検出」なのに、コマンドは `--verify all` だけで、gen_regime_kb の selftest は stage を測っていない（gen_regime_kb.py:1396 の kinds に stage が無い）。

修正の番号＝5・6・15・16

### A1 — 部品 ts_pos の式（実装の指示 1〜4）が、未来を見ず、最小〜最大の間の位置を出すか（優先度 A）

- **A1-a**＝式 `(s−min)/(max−min)` は StockCharts の %K と同じ形で、×100 をしない。rolling は過去 n本だけで、いまのバーを含む。既知答えは手で1本ずつ計算して一致した（1.0・1/3・0・0・0・NaN）。未来は見ない。
- **所見4（Minor・A1-b）**＝pandas の rolling は、窓の中に NaN が1本でも在ると NaN を返す（既定の min_periods＝窓の長さ）。材料の列の途中に値なしが在ると、その後の 52,596本（6か月）が黙って値なしになる。実データの値なしの本数は走らせていないのでデータ不足。設計書のリスクの表に書かれていない。
- **A1-c**＝`_mat_key` は `ts_pos52596:列名` になる（exec:2098）。`build_qtable` は `ex._apply_pre` を呼んでから窓で切る。PASS。
- **A1-d**＝水準の形では、単位が変わる前処理を使ってよい（exec:1072 で拒否されるのは列2本の形だけ）。PASS。

修正の番号＝7・8

### A2 — 窓の本数（pre_win_bars）と余白（stage_warm・本走の読み込み）が、値決め窓と確認窓の最初のバーから動く線を出せる形か（優先度 A）

- **所見1（Major）＝余白を延ばす相手が、動く線を実際には使わない走行になっている。**
  - 実装の指示27は、`run_main` で必ず `stage_warm(et.WARM)` を使う形。
  - `--build-regime` を付けないとき（engine_tuner_gen.py:7777「ap.add_argument("--build-regime", action="store_true",」・既定は off）は、場面の判定の束を1本も組まない（gen:3483「if build_regime:」）。それでも余白は 60日 から 242.625日 に延びる。
  - `--build-regime` を付けても、3枠目の順位は `regime_draw_order` で決まる（gen:2359）。動く線は段2c の 262位より後ろに並ぶ。そこへ届く案の番号は、和 s=264 の最初＝C(263,3)=2,997,411 組の後ろで、向きが2つなので ×2＝5,994,822番。本走の案は数十〜数千本なので、本走の束は動く線を1本も使わない。
  - 一方で、動く線を実際に測る M2-F-13 の道具（regime_r9_diag.py:309）は 60日 のまま（やらないこと11）。
  - まこさんの決定の逐語は「動く線を使う走行だけ、余白を長くする」（acceptance_src.json:44）。延ばすのは、使わない本走の側だけになっている。その結果、動く線を使わないのに、本走の土台と全試行の結果が変わる（設計書 4-13 の9）。
- **A2-a**＝前処理は5分足の並びの列に掛かる、という読みは正しい（exec:2058 で素の列を作ってから `_apply_pre`）。上位足の値は5分足へ前の値を引き継いで載るので、窓を5分足の本数で数えるのは妥当。
- **A2-b**＝本走では、読み始めが SEARCH_START（2024-03-01）−242.625日＝2023-07-02 09:00 になり（設計書 4-19 の「2023-07-05 ごろ」とは違う＝所見7）、最初のバーから窓がそろう形。窓の中に値なしが無いことが前提（所見4）。走らせて確かめてはいない。
- **A2-c**＝余白の長さを前提にしている所は `data_fingerprint`（engine_tuner.py:128 で余白を指紋に入れる＝キャッシュが作り直される）だけ。分位の解決表は窓で切ってから計算する（gen の build_qtable の mask）。売買の記録も窓で切る（gen:4083）。
- **A2-d**＝60日 で読む12か所のうち、動く線を含む案を評価できるのは regime_r9_diag（`--recipe`）と dashboard/build_regime_from_tuner。どちらも窓の最初の約4か月が黙って値なしになる。設計書は 4-5 の最後の行で認めている。
- **所見P2（Process）**＝「本走が動く線を使う」を、届く順位を計算せずに前提にした（上の所見1 の原因）。

修正の番号＝1・2・23・24

### A3 — 段2c の候補の並び（固定の線の後ろ）と、乱数の道の絞り（gen_draw）で、いまの束と入口の案が1本も変わらないか（優先度 A）

- **所見2（Major）＝束の中身（条件）は変わらないが、`--build-regime` の案の指紋は全部 変わる。**
  - `sample_regime_build` は引いた記録に `draw["stages"] = stage_counts(...)` を入れる（gen:3346）。`_stage_pick` の記録の「上位」には keep＝候補の本数を入れる。
  - 段2c の本数が 261 から 261＋BB幅 の固定の線の本数に増えるので、`meta.regime_draw` が変わる。`recipe_hash` は meta を含めて計算する（gen:3518）。
  - そのため全部の束の案で指紋が変わり、重複の判定（gen:4427）と再開の鍵（gen:4484「key = f"s1/{si}/{recipe_hash(r)}"」）がずれる。
  - 設計書 4-13 にこの影響が書かれていない。
- **A3-a**＝静的には、順位 1〜261 の3枠目の条件は1本も変わらない。T42 の「G が一覧の r_g 位と同じ」も成り立つ。写しでの比較は走らせていない（データ不足）。
- **A3-b**＝`stage_counts`・§2.2-0 の表・`gen_stage0_match` は本数と指標の名前を数えるだけ。gen_stage0_match は `pre` も `pre_win` も読まない。
- **A3-c**＝`pre_ops` は名前順で返す。`gen_draw=True` の結果は ["ts_rank","ts_std"] で、直す前の `same_unit=False` と同じ。`same_unit=True` で引く所（gen:1616/1641）には ts_pos は入らない。入口の案の乱数の消費は、静的には変わらない。
- **A3-d**＝`pre_win` は m2_stage_candidates の BB幅 の語だけに書かれる。組む側は汎用の作りだが、T47 の③が family を BB幅 に限って測る。PASS。

修正の番号＝3・4

### A4 — 「実装の指示」28件が、当てる道具でそのまま当てられ、当てた後のコードが動くか（優先度 A）

- **A4-a**＝写しでは走らせていない（データ不足・理由＝監査役は読み取りだけ）。
- **A4-b**＝同じファイルに当てる件の順番（7・8・9・10・11・12・27）では、先の件が後の件の「直す前の文字」を消さない。道具は当てた後の中身で見直してから書く（apply_audit_fix.py:497-510）。gen_regime_kb（18〜22）は TARGET の外かつ NEVER_WRITE なので止まるだけで、全件を止める理由にはならない（:470-476）。
- **A4-c**＝`pd` は gen:39 で読み込み、`SampleError` は gen:1249 で定義。`stage_warm` は呼ぶときに名前を解決するので、読み込み時には止まらない。
- **A4-d**＝探す文字と当てた後の行の字下げを照らした。b109 は12空白・b110 は15空白・b111 は8空白・b112 は4空白で、どれも1か所に当たる。いまの実物では4つとも0件で、ぶつからない。
- **A4-e**＝JSON の3か所（16・17・23）は要素の区切りの形として正しい。`gen_materials.condition_parts` の番人②は未使用の部品を表に出すだけで、落ちにはしない（:885）。
- **所見5（Minor）**＝m2_stage_candidates.json:88 の「MATERIAL_PRE の8つ＝…abs」が、実装の後に古くなる（9つになる）。§2.2-0 の表（milestones2:971）にも同じ文がそのまま出る。★修正9 を当てると実装の指示は29件になり、当てる道具が当てるのは20件になる。設計書 4-4 の1番・4-20・見積もりの文の「19件」「28件」の書き替えは、この結果の修正の指示には入っていない（監査役が直しの文を出していない）。
- **所見6（Minor）**＝実装の指示23の src「pine:ta.stoch」は、pine の出どころの記録（condition_parts.json:50「取れた名前＝ta.sma・…・ta.vwma」）に無い名前。設計書も「リファレンスの本文の式は開けていない」と書いている。

修正の番号＝9・10・11・12

### A5 — この設計に、乱数と、新しい数字・点の一覧が0件か（優先度 A）

- **A5-a**＝新しいコード（部品・`_moving`・`stage_warm`・T47・見本）には乱数が0件。count_builder_literals の範囲に入る `pre_win_bars`・`stage_warm` にも、rng と法則の番号は無い。
- **A5-b**＝足される数字は、6（逐語）・365.25/12（暦）・5（H7）・1440（1日の分＝単位の換算）と、番人の見本の値（並び 1〜5・n=5・th 0.2・n=20）。見本の値は探す値でも売買の値でもなく、前からある見本 0.8・20 と同じ扱いなので Critical と判定しない。窓を1点にしたことは逐語の six-month に従ったもので、要件の「作ってはいけないもの」2番には当たらない。

修正の番号＝なし

### B1 — 部品を足したあとの作り直しの道具と順番に、抜けや誤りが無いか（優先度 B）

- **B1-a**＝部品の一覧を読むのは exec・gen・gen_materials・gen_regime_kb・b98 だけ（リポジトリ全体を grep）。抜けは無い。
- **B1-b**＝gen_signal_families は MATERIAL_PRE・pre_ops を読まない（同じ grep で0件）。型の表を作り直さなくてよい、という読みは正しい。
- **所見9（Minor・B1-c）**＝設計書 4-4 の手順に `pre_audit_check.py --run`／`--verify` が無い。このチェックは指紋（pre_audit_check.py:78 の FINGERPRINT_FILES に gen・exec が入っている）が変われば取り直しになるので、実装の監査の前に要る。手順の並びは ORDER（:45-54）と矛盾しない。

修正の番号＝17・18

### B2 — 設計書 4-13（影響範囲）と「やらないこと」に、見落としと、成り立たない理由が無いか（優先度 B）

- **B2-a**＝探す文字を、この工事で触る文字列まで広げて grep した。当たったのは b82 のコメントの行と、b98 の `NO_ARG_OPS` の行（`_mat_key` は触らない）だけで、壊れる所は無い。
- **所見P1（Process）**＝依頼を出した CC の grep の語（設計書の「なぜ作るか」の10行目・L-605）は、実装の指示4・11・12・27 が触る文字を含んでいなかった。
- **B2-b**＝`pre_win` を読み落とす読み手は無い。組む側は読み、gen_stage0_match は読む必要が無く、§2.2 の表は実装の指示22で読む。
- **B2-c**＝DESIGN_CONTRACT の触る関数と must_use は、4-3 の表と合っている。

修正の番号＝21・22

### C1 — 名前・文書・見積もり（優先度 C）

- **C1-a**＝`_material_name` が pre に許す鍵は op・n・state で、ts_pos は n を使うので合う。名前のぶつかりも無い（gen に `_pw`・`_moving`・`_EXEC_BAR_MIN` は0件）。ただし b11_subagent.sh が在るので、番号の前方一致で探す道具があれば b110〜b112 を取り違える（名前全体で指定するなら問題にならない）。
- **C1-b**＝§2.2-0 の表の「実際の候補」の本数は、BB幅 が 84本（固定の線と動く線の合計）になり、区別できない。`regime_r9_diag --candidates` も前処理を表示しない（Minor の件数には数えず、直しも付けない）。
- **所見10（Minor・C1-c）**＝設計書 4-14 に、本走の読み込みが増える分が書かれていない。値決め窓の行は (549+242.625)/(549+60)＝1.30倍、確認窓は (181+242.625)/(181+60)＝1.76倍 になる。
- **所見7（Minor）**＝設計書 4-19 の8番の「2023-07-05 ごろ」は、計算すると 2023-07-02 09:00。

修正の番号＝13・14・19・20


## 5. 外部検索

### 検索 1 — 指標が直近の一定期間の範囲（最小〜最大）の中のどこに在るかを、判定の条件に使う形

- 検索＝WebSearch「Bollinger BandWidth "six-month range" low end squeeze StockCharts」＋ WebFetch 4件。
- https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze ＝「Ideally, BandWidth should be near the low end of its six-month range.」「The BandWidth is near the low end of its six-month range.」
- https://www.luxalgo.com/library/concept/bollinger-squeeze/ ＝「John Bollinger defines the Squeeze as BandWidth at its lowest level in about six months, roughly 125 daily bars.」「Flag a squeeze when BandWidth reaches its lowest level over your lookback window.」「percentile variants flag readings near the bottom of their historical range」
- https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth ＝「BandWidth values should be gauged relative to prior BandWidth values over a period of time.」「BandWidth is considered narrow as it approaches the lows of this range and wide as it approaches the high end.」「an eight- to 12-month chart」
- https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/stochastic-oscillator-fast-slow-and-full ＝「%K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100」「The Stochastic Oscillator measures the level of the close relative to the high-low range over a given period.」
- 結論＝標準の形は「窓の中の最小を基準にする（最安値を更新したか／範囲の下の方か）」で、最小〜最大の間の位置で表せる形＝ts_pos と合う。分位（順位）で測る形は「変種」として書かれていた。125本は株の営業日で数えた6か月なので、24時間365日の BTC では暦の 182.625日で数える方が合う。

## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

そのとおり。この監査も走らせていない（監査役は読み取りだけの決まり）。①〜⑤は静的には通る見込みだが、確かめたことにはならない。実装の後に走らせて確かめる必要は残る。

### 自己申告 2

24件とも1件だった。中身（直した後の文字）の側の問題は、所見1・2・3・6 として見つかった。どれも grep では見つからない型の問題。

### 自己申告 3

同じ型の落としは実在する。余白を延ばすべき道具（regime_r9_diag・build_regime_from_tuner）は60日のままで、延ばした本走は動く線に届かない（所見1）。

### 自己申告 4

設計書の中に残っている同じ型は、所見9（手順の抜け）と P1（grep の語の抜け）。

### 自己申告 5

「本走＝動く線を使う走行」も CC が決めたもので、まこさんの決定の逐語より広く当てている（所見1）。まこさんが決める件（修正1＝未決）。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝ts_pos は未来を見ずに、最小〜最大の間の位置〔0〜1・幅0は値なし〕を出す。R6 の逐語と「２，案①」どおり。52,596本も正しい。本走では最初のバーから値が出る形〔静的・窓に値なしが無いことが前提〕。ただし余白を延ばす相手を間違えている〔所見1・Major〕）
- 問い2 ＝ YES（根拠＝固定の線の後ろに同じ本数が並ぶ。束の条件と入口の案の作り方は変わらない。BB幅 だけに付く形も守られる。ただし案の指紋は変わる〔所見2・Major〕）
- 問い3 ＝ YES（根拠＝Critical 0件。28件は静的には当てられる。当てた後に動くかは、走らせていないのでデータ不足〔理由＝監査役は読み取りだけ〕）

### 結論と件数

- 結論＝GO
- Critical＝0
- Major＝2
- Minor＝8
- Process＝2


## 8. 修正の指示

### Critical

なし

### Major

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 418行（実装の指示27の中身）
直す前の文字:
~~~
_warm = stage_warm(et.WARM)
~~~
直した後の文字:
~~~
_warm = stage_warm(et.WARM) if a.build_regime else et.WARM
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7777「ap.add_argument("--build-regime", action="store_true",」
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
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

#### 修正 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 252行（4-13 の10番の末尾）
直す前の文字:
~~~
M2-F で段を測る道具（`regime_r9_diag.py`）は M2-F-2 の工事で `stage_warm` を使う形にします。"
~~~
足す文字:
~~~
,
      "11. **束の案の記録と指紋。**場面の判定の束を付けた案（`--build-regime`）は、束の中身（条件）は変わりませんが、案に残す引いた記録（`meta.regime_draw` の G の「上位」と `stages` の段2c の候補の本数＝261 → 261＋BB幅 の固定の線の本数）が変わるので、案の指紋（`recipe_hash`）が全部 変わります。直す前の走行の記録からの再開（R12・鍵 `s1/番号/指紋`）では、同じ案でも走らせ直しになります。"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3346「draw["stages"] = stage_counts(laws, table, tfs, limits)」
状態: 確定

#### 修正 4
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

### Minor

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 403行（実装の指示12の中身・T47 の⑤）
直す前の文字:
~~~
_ng47.append(f\"⑤動く線を使う走行の余白が 60日＋6か月にならない: {_wm47}\")
~~~
足す文字:
~~~
\n        _src47 = pathlib.Path(__file__).read_text(encoding=\"utf-8\")\n        _rm47 = _src47[_src47.index(\"\\ndef run_main\") + 1:]\n        _rm47 = _rm47[:_rm47.index(\"\\ndef \")]\n        if \"_warm, use_cache=not a.no_cache)\" not in _rm47:\n            _ng47.append(\"⑤本走（run_main）が stage_warm の余白でデータを読んでいない\")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7731「et.WARM, use_cache=not a.no_cache)」
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
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 307行（リスクの最後の行）
直す前の文字:
~~~
"どうするか": "記録の段で、m2_todo.json の M2-F-2 の注意に「stage_warm を使う」を1行 足す"}
~~~
足す文字:
~~~
,
    {"中身": "窓 52,596本の rolling の最小・最大は、窓の中に値なし（NaN）が1本でも在ると値なしを返す（pandas の既定 min_periods＝窓の長さ）。材料の列の途中に値なしが在ると、その後の6か月が黙って値なしになる", "どうするか": "実装の後、本走の余白で読んだ値決め窓・確認窓で、BB幅 の動く線の材料の値なしの本数を数えて記録する。窓の始まりの後に値なしが在れば止まって まこさんに出す"}
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:99「最初の n−1本と、幅が0の所と、値の無い所は値なし（NaN）です。」
状態: 確定

#### 修正 8
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

#### 修正 9
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 419行（実装の指示28の末尾）
直す前の文字:
~~~
（余白を延ばさない）\\n'\nopen(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))\nPYEOF\n\nmeasure python3 \"$GEN\" --selftest\nfinish\n", "根拠の抜き書き": ".claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」", "状態": "確定"}
~~~
足す文字:
~~~
,
    {"番号": 29, "対象のファイル": ".claude/ratchet/m2_stage_candidates.json", "直す箇所": "88行（段2c の入れなかったものの1行目）", "直す前の文字": "前処理の一覧（MATERIAL_PRE の8つ＝ts_max・ts_min・ts_rank・ts_std・since_min・since_max・at_entry・abs）", "種類": "直した後の文字", "中身": "前処理の一覧（MATERIAL_PRE の9つ＝ts_max・ts_min・ts_rank・ts_std・since_min・since_max・at_entry・abs・ts_pos）", "根拠の抜き書き": ".claude/ratchet/m2_stage_candidates.json:88「MATERIAL_PRE の8つ＝ts_max・ts_min・ts_rank・ts_std・since_min・since_max・at_entry・abs」", "状態": "確定"}
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_stage_candidates.json:88「前処理の一覧（MATERIAL_PRE の8つ＝ts_max・ts_min・ts_rank・ts_std・since_min・since_max・at_entry・abs）」
状態: 確定

#### 修正 10
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

#### 修正 11
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 414行（実装の指示23の src）
直す前の文字:
~~~
\"pine:ta.stoch\"
~~~
直した後の文字:
~~~
\"alphagen:Max\",\n    \"alphagen:Min\"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/condition_parts.json:50「"detail": "取れた名前＝ta.sma・ta.ema・ta.macd・ta.rsi・ta.supertrend・ta.barssince・ta.crossover・ta.highest・ta.tr・ta.vwma。」
状態: 確定

#### 修正 12
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

#### 修正 13
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 166行（4-19 の8番）
直す前の文字:
~~~
（2023-07-05 ごろ）
~~~
直した後の文字:
~~~
（2023-07-02 09:00）
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/periods.py:94「SEARCH_START = pd.Timestamp("2024-03-01")」
状態: 確定

#### 修正 14
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

#### 修正 15
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 324行（完成の条件 #8）
直す前の文字:
~~~
"条件": "§2.2 の表を作る道具の自己テストと検出が通る"
~~~
直した後の文字:
~~~
"条件": "§2.2 の表を作る道具の検出が通る（読むための道具＝恒久71番の線引きで、動くことを1回 確かめるだけ）"
~~~
根拠の抜き書き: .claude/rules/permanent_rules.md:388「**動くことを1回 確かめるだけ。**壊すプログラムを作らない・完成の条件に載せない」
状態: 確定

#### 修正 16
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

#### 修正 17
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 154行（4-4 の10番）
直す前の文字:
~~~
10. 完成の条件の表の全部のコマンドを走らせ、2回目の承認をお願いし、実装の監査に出します。"
~~~
直した後の文字:
~~~
10. 完成の条件の表の全部のコマンドを走らせ、2回目の承認をお願いします。",
      "11. `python3 .claude/tools/pre_audit_check.py --run` と `--verify` を走らせ（組む側と実行器の指紋が変わるため。ORDER の型の表と出口の表の `--write` は、部品の一覧を読まないので要らない）、「監査に出せます」が出てから実装の監査に出します。"
~~~
根拠の抜き書き: .claude/tools/pre_audit_check.py:45「ORDER = [」
状態: 確定

#### 修正 18
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

#### 修正 19
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 231行（4-14 の最後の行）
直す前の文字:
~~~
| 壊すプログラム b109〜b112 の1本 | 約5分40秒 | 上の1行目と同じ（組む側の自己テストを測る）。打ち切りは600秒 |"
~~~
足す文字:
~~~
,
      "| 本走（run_main）が読むデータの行 | 値決め窓 約1.30倍・確認窓 約1.76倍 | 余白 60日 → 242.625日。値決め窓 549日・確認窓 181日（periods.py）に余白を足した日数の比。走らせて測っていない |"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/periods.py:95「SEARCH_END = pd.Timestamp("2025-09-01")」
状態: 確定

#### 修正 20
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 21
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 69行（なぜ作るかの10行目のコマンド）
直す前の文字:
~~~
-e 'alphagen:Std' .claude/breaks"
~~~
直した後の文字:
~~~
-e 'alphagen:Std' -e 'NO_ARG_OPS' -e 'et.WARM' -e 'load_windows_cached' -e '実行が未実装' -e 'T36: 途中' -e 'rolling(int(n)).std' .claude/breaks"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:54「コードを直したら、その行を探している壊すプログラムが在るかを、必ず grep（2026-09-16・L-605）」
状態: 確定

#### 修正 22
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

#### 修正 23
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 351行（塞げないものの1行目）
直す前の文字:
~~~
{"問い": "動く線と固定の線のどちらが良い判定か"
~~~
直した後の文字:
~~~
{"問い": "本走（run_main）の束が動く線を実際に使うか", "塞げないこと": "使いません。3枠目の順位は案の番号から決まり（regime_draw_order）、動く線は段2c の 262位より後ろに並ぶので、届くのは案の番号 5,994,822番（C(263,3)×2）より後ろです。動く線を測るのは M2-F-13 の道具で、その余白は M2-F-2 で直します"},
    {"問い": "動く線と固定の線のどちらが良い判定か"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:2359「def regime_draw_order(n: int) -> tuple[int, int, int, str]:」
状態: 確定

#### 修正 24
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

**開いたファイルと行（監査役＝Plan サブエージェント）**

- 依頼書：全459行。設計書 acceptance.md：全1,843行。acceptance_src.json：1〜421行（全文）。
- engine_tuner_exec.py：398〜640・2005〜2100。
- engine_tuner_gen.py：1790〜1820・2355〜2390・2460〜2550・2770〜2925・3090〜3150・3165〜3300・3478〜3495・3515〜3530・3740〜3830・4405〜4420・5195〜5245・6451〜6592・6800〜6860・7080〜7200・7495〜7520・7600〜7640・7665〜7782・7899〜7980。
- engine_tuner.py：88〜160。tuner_adapters/e38.py：285〜340。
- condition_parts_diag.py：41・130〜162・285〜320・395〜425・495〜605。condition_parts.json：1〜50・180〜230。
- m2_stage_candidates.json：1〜12・70〜90。engine_tuner_milestones2.md：755〜772・938〜976。
- gen_regime_kb.py：955〜1240・1390〜1480。gen_materials.py：842〜945。gen_stage0_match.py：60〜130。regime_r9_diag.py：165〜215・280〜330。
- 壊すプログラム：lib.sh（全文）・b104（全文）・b78・b82・b93・b98・b79・b92（探す行）。
- apply_audit_fix.py：67〜74・286〜520。pre_audit_check.py：45〜90。count_builder_literals.py：15〜124。permanent_rules.md：381〜392。periods.py：94〜103。
- **開かなかった着手前必読**＝15（CP39 の結果）・16（cat_requirements の §4.6 は自動で読み込まれた本文だけ）・17（engine_tuner_requirements）・18（worklog §5 は grep だけ）。必読の件数に足りていない。

**監査役のセッションが結果を書く前に開き直した行（結果に書く行番号の前後5行・中身が所見と合うことを確かめた）**

- engine_tuner_gen.py：34〜44・1244〜1254・1611〜1621・2354〜2364・3341〜3351・3478〜3488・3513〜3523・4078〜4088・4422〜4489・7629〜7639・7726〜7782。
- engine_tuner_exec.py：1067〜1077・2053〜2103・3066〜3076。engine_tuner.py：123〜133・572〜582。
- condition_parts_diag.py：36〜46。condition_parts.json：45〜55。m2_stage_candidates.json：83〜93。periods.py：89〜100。
- permanent_rules.md：383〜393。pre_audit_check.py：40〜83。regime_r9_diag.py：304〜314。gen_regime_kb.py：1391〜1401。apply_audit_fix.py：492〜502。b104_atr1h_own_tf.sh：1〜6。acceptance_src.json：94〜104。

**走らせたコマンドと結果**

- 監査役＝grep・sed・shasum・git status/diff/log・ls・awk・cat の読み取りだけ（秒数は測っていない）。WebSearch 1件・WebFetch 4件。
- 監査役のセッション＝`wc -l`（依頼書 459行）・`shasum -a 256 .claude/state/acceptance.md`（22287788…・2回）・`gen_audit_docs.py result`（rc=0・節 11・問い 9・事実データ 1・外部検索 1・自己申告 5）・`git status --short`・`git log --oneline -3`。

**走らせられなかったものと理由（そのまま）**

- 写しの作成・28件の当て込み・py_compile・`engine_tuner_gen.py --selftest`（見込み 約5分40秒）・`engine_tuner_exec.py --selftest`（約10秒）・`condition_parts_diag.py`（時間は不明）・`gen_regime_kb.py --write stage`／`--selftest`・b109〜b112（約5分40秒×4）・`gen_acceptance.py --write`・`pre_audit_check.py --run/--verify`・`require_design_check_before_approval.py --try`＝監査役（Plan サブエージェント）が読み取りだけの決まり（ファイルの作成と状態の変更が禁止）で動くため。**依頼書が勧めた写しでの実走は、この監査では1つも行っていない。**
- `python3 -B -c "…"`＝hook `require_design_contract_before_run.sh` に止められた（逐語「走らせる .py を確定できないコマンドです」）。
- 変数を使った grep＝同じ hook に止められた（「設計書の承認: 外れています（承認後に設計書が変わりました）承認された値: 6c68df5b… いまの値: 22287788…」）。
- `cut` を使った grep＝hook `require_acceptance_before_impl.sh`（土台ゲート・Bash）に止められた。

## 11. 本物のファイルを書き替えていないこと

結果を書く前（2026-09-27 02:50）の `git status --short`（前からある作業場 cp36〜cp45 の行は省いた）:

```
?? .claude/hooks/require_chat_draft_before_long_reply.sh
?? .claude/settings.json.bak_20260819
?? .claude/settings.json.bak_20260826
?? .claude/settings.json.bak_20260902_implock
?? .claude/settings.json.bak_20260903_a6
?? .claude/settings.json.bak_m2_2_2b
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp46_work/cp46_result.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_L1.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_v59.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/results/
```

- 変更（M）の行は0件。監査を始めたときに在った ` M`（next_step.md・next_step_src.json・worklog・acceptance_src.json・decisions.md）は、監査の途中にメインのセッションが commit dfea4be（HEAD）を作ったので消えている。監査は1ファイルも書き替えていない。
- 新しく在るのは、作業場の `cp46_work/cp46_result.md`（この結果の下書き）だけ。cp46_work には、監査の前から cp46_src.md が在る（追跡済み）。
- 設計書のハッシュ値は、結果を書く前も 22287788… のまま。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-27_m2e4e_r6_moving_line_design_cp46_audit_request.md request_sha256=c9d0301bbd8db079545a027de93ab1c3b54423b91627e7e6b478eb9530b30245 -->
