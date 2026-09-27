# 監査結果 cp47 — CP47 — M2-E-4e の実装（前処理の部品 ts_pos・元データの欄 pre_win・段2c の「動く線」の候補・動く線を使う走行の余白 stage_warm）は、承認済みの設計書 m2e4e-r6-moving-line-20260927 の決めた動きをしているか。設計書と実装の食い違いを、まとめて直せる形で洗い出す

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-27_m2e4e_r6_moving_line_impl_cp47_audit_request.md`
- 依頼書のハッシュ値: a7ae356c1ca8bf90b05941ca7d666c3ba06e98ccc8af920f9d23b5a1d092f241
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 2999e9a8e9de9581a67f327bffbffee3466b751a20879e7b81fc03b6faa16fca
- 監査が照らしたハッシュ値: 2999e9a8e9de9581a67f327bffbffee3466b751a20879e7b81fc03b6faa16fca（`shasum -a 256 .claude/state/acceptance.md` を監査の最初と最後に測った。2回とも依頼書と一致）。控え `SDK/.claude/ratchet/acceptance_archive/m2e4e-r6-moving-line-20260927.md` も同じ 2999e9a8…。元データ `acceptance_src.json` は bcdeabf2c20a2552f1a773aaf4abc24b370a790c0fdb7c1939925a3740a78398（427行・最初と最後で同じ）。設計書は上書きされていなかったので、本物の `.claude/state/acceptance.md` を読んだ。実装は commit 7ab937d に入っている（依頼書の「まだ commit していません」とは違う。`git diff dfea4be` の差は同じものが出る）。
- 実施日: 2026-09-27


## 2. 監査対象の型宣言

- **コード型**＝`engine_tuner_exec.py`（ts_pos・pre_ops・_apply_pre・_mat_key）・`engine_tuner_gen.py`（_make_cond・stage_candidates・pre_win_bars・stage_warm・build_stage_candidates・T1-C6e・T47・run_main）・`condition_parts_diag.py`・`.claude/tools/gen_regime_kb.py`・壊すプログラム b109〜b112・lib.sh。
- **文書型**＝設計書 `acceptance.md`（1,868行）とその元データ `acceptance_src.json`（427行）・`m2_stage_candidates.json`・`condition_parts.json`・`regime_laws.json`（R7 の1行）・`engine_tuner_milestones2.md`（§2.2-0 ほか）。
- **数値型**＝窓 52,596本・余白 242.625日（242 days 15:00:00）・段2c の候補 303本（固定の線 261＋動く線 42）・動く線に届く案の番号 5,994,822（0から数える）。
- ★監査役（Plan サブエージェント）は「ファイルを作らない」決まりで動いたので、作業場 cp47_work に写しを作っていない。壊すプログラムは走らせ直していない（10 に理由）。代わりに、読むだけの走行（自己テスト・--verify・恒等3本・突き合わせ・--diff）を本物で走らせた。


## 3. 監査対象の事実データの確認

### 監査対象の事実データ（依頼を出した CC が走らせたもの・まこさんが打ったもの）

| いつ | コマンド | 監査が確かめた結果 | 一致 |
|---|---|---|---|
| CC | `apply_audit_fix.py --report <CP46> … --choose 1=確定` | CP46 の修正24件＝元データを直す12件＋`gen_acceptance.py --write` 12件。直す12件（1・3・5・7・9・11・13・15・17・19・21・23）は、どれもいまの元データと設計書に入っている（1件ずつ grep で確かめた）。途中の値 c9a875ee… は走らせ直していない | 一致（途中のハッシュ値はデータ不足＝理由：当てる道具は書き込むので走らせない） |
| まこさん | `cp` → ratchet の元データ | いまの元データ・控え `.claude/state/acceptance_src_m2e4e-r6-moving-line-20260927_cp46.json` とも sha256 bcdeabf2… | 一致 |
| まこさん（承認①） | 承認のプログラム | 控え `.01.md` と `.01.sha.txt` がどちらも f18554aa… | 一致 |
| CC | `apply_audit_fix.py --design` | `git diff dfea4be` の中身が、実装の指示 1〜17・23・27・29 の文字と1文字も違わない（1件ずつ照らした）。gen_regime_kb の5か所（18〜22）・壊すプログラム4本（24〜26・28）も設計書の全文と同じ | 一致 |
| CC | `gen_regime_kb.py --write stage` → `--selftest` → `--verify all` | いま `--verify all`＝「file:line 引用の実在検査＝9件のうち ずれ 0件」・`--selftest`＝15/15 pass（どちらも監査が走らせた）。§2.2-0 の BB幅 の行に `ts_pos（6か月・動く線）` | 一致（当時の 14/15 は走らせ直せないのでデータ不足） |
| CC | R7 の行番号を直し `--write laws` | `git show dfea4be` の実行器で `wpct_arr` は2669行、いまは2687行。法則ファイル758行が `:2687` | 一致 |
| CC | `engine_tuner_exec.py --selftest` | 「✅ 全部 pass」rc=0・9秒 | 一致 |
| CC | `engine_tuner_gen.py --selftest` | rc=0・「✅ 全部 pass」・374秒。2回目も rc=0 で T47 の行が逐語で「T47 動く線: ①ts_pos は乱数の道の外 ／ ②既知答え ／ ③段2c の動く線 42 本（BB幅 の固定の線 42 本・窓 5分足 52596本・固定の線の後ろ）／ ⑤余白 242 days 15:00:00＝通った」 | 一致 |
| CC | `condition_parts_diag.py` | rc=0・3〜4秒・「level 直近20本の範囲の中の位置 ≤0.2 4,565 4,565 0」・「✅ 13個の形（29通り）すべて…食い違い 0」 | 一致 |
| CC | `gen_materials.py --write` → `--verify` → `--selftest` | `--verify`＝「✅ 一致」rc=0・6.1秒／`--selftest`＝「✅ 全部 pass（該当なし 1件: S5）」rc=0・71.5秒。`--write` は書き込むので走らせていない | 一致 |
| CC | `gen_signal_families.py --verify` → `leak_causality_diag.py` | 走らせていない（印が変わるため・依頼書の指定）。g2_pass.json＝2026-09-27 11:34:09・指紋 6b971151…／h2_pass.json＝11:39:09・指紋 bf993752…。H2 の印を照らす hook が監査の実行器の走行を止めなかった＝いまのコードの指紋と印が合っている | 一致（走行そのものはデータ不足） |
| CC | 恒等3本 | `--identity`「✅ 全部一致」rc=0・6.5秒／`--identity-l1`「✅ 全部一致」rc=0・3.7秒／`--identity-s1`「✅ 全部一致」rc=0・16.3秒 | 一致 |
| CC | `run_breaks.py --measure-only` | 走らせ直していない（10 に理由）。承認の記録 `m2e4e-r6-moving-line-20260927.breaks.json` で4本とも code 1・expect 1・match true。記録の文＝b109「③動く線 0 本が、BB幅 の固定の線 42 本と合わない」・b110「①入口の案を乱数で作る道の一覧に ts_pos が入っている」・b111「②既知答えと違う: [nan×5, 0.5, 0.3333, 0.0, 0.0, nan]」・b112「⑤…60 days 00:00:00」。壊した行は残っていない（壊す相手の4行が `grep -c -x` でちょうど1件ずつ） | 一致 |
| CC | 完成の条件 #7・#8 | #7＝`grep -c` が 1・rc=0／#8＝SDK の置き場から表のとおりの形で rc=0 | 一致 |
| まこさん（承認②） | 承認のプログラム | 設計書 7-6 の #1〜#4 が「✅済」、#5〜#14 が「未着手」、印 2999e9a8…、acceptance.approved の中身も 2999e9a8… | 一致 |
| CC | `pre_audit_check.py --run` → `--verify` | `--verify`＝「監査に出せます（チェックの1枚が新しく、全部 rc=0）」0.1秒。`--run` は記録を書くので走らせていない | 一致（`--run` の中身はデータ不足） |


## 4. 所見

### 一般の観点

- ①統計学的妥当性 ＝ PASS（ts_pos は R6 の逐語「six-month range の下の方」と StockCharts の %K の形に合う。閾値 q50 は決めてほしいこと1 で まこさんの判断待ちのまま）
- ②リスク管理 ＝ PASS（売買のロジック・H1・審判・score.py に触れていない）
- ③認知バイアス ＝ PASS（net を見て値を選んだ所は無い）
- ④ソフトウェア工学 ＝ FAIL（所見6＝設計書の SPEC が古く本走がゲートで止まる／所見1・2＝T47 の⑤と③が文字や欄の数字だけを見る／所見10＝古い説明の文）
- ⑤再現性 ＝ PASS（恒等3本が全部一致・T47 の行が2回とも同じ）
- ⑥実行プロセス ＝ FAIL（設計書 7-6 の「触る関数の一覧は、実装の後に確定させます」をやっていない＝所見6／H2 が ts_pos を通るかを確かめずに「H2 で測る」と書いた＝所見3）
- ⑦主エージェントバイアス ＝ FAIL（自己申告に、`--diff` の齟齬6件と本走が止まる状態が1行も無い。「H2 で測る」を確かめずに置いた）

### A0 — 壊すプログラム4本（b109〜b112）と番人 T47 が、測ると言っているものを本当に測っているか（優先度 A）

- **A0-a**＝承認の記録（breaks.json）の文は、4本とも宣言どおりの欄（b109＝③・b110＝①・b111＝②・b112＝⑤）で落ちている。記録は「最後の ❌ の1行」なので、T47 より後の番人は落ちていない。T47 より前の番人（T1-C6e ほか）が同時に落ちたかはデータ不足（理由＝写しで走らせ直していない・記録は1行）。b111 の出力 [nan×5, 0.5, 0.3333, 0.0, 0.0, nan] は、最小だけ1本ずらした式で手計算すると合う（6本目＝(3−1)÷(5−1)＝0.5 ほか）。
- **所見1（Major・A0-b）＝T47 の⑤は、本走が「`--build-regime` のときだけ」延ばす形（まこさん決定「案A」）が壊れても落ちない。**T47 は run_main の本文に `_warm, use_cache=not a.no_cache)` の文字が在るかだけを見る（engine_tuner_gen.py:7239）。`_warm = et.WARM`（いつも延ばさない）にしても、`_warm = stage_warm(et.WARM)`（いつも延ばす）にしても、`if not a.build_regime`（逆さま）にしても、この文字は残るので T47 は通る。DESIGN_CONTRACT の must_use（run_main が stage_warm を呼ぶ）は「いつも延ばさない」だけを止め、ほかの2つは止めない。「いつも延ばす」形は、`--build-regime` を付けない本走の土台の数字とキャッシュを黙って変える＝まこさんの決定と違う形が通る。
- **A0-c**＝BB幅 の固定の線が0本になると、動く線は固定の線の繰り返しの中でしか作られないので0本になり、「③段2c の候補に動く線が1本も無い」で落ちる。黙って通る道は無い。
- **所見2（Minor・A0-c）＝T47 の③の「固定の線の後ろ」は、候補の `rank` の欄の数字を比べているだけで、一覧の中の位置を見ていない。**束を組む側は位置で取る（engine_tuner_gen.py:3188「c = cands[r - 1]」）。動く線を繰り返しの中で `out` に足し、`rank` だけ後ろの番号にする形に壊すと、T47 は通り、固定の線の位置がずれていまの束が変わる。いまのコードは位置と `rank` が一致しているので実害は無い。
- **A0-d**＝lib.sh の `guard` は触るファイルを控えに写し、終わると戻してハッシュ値を照らす（合わなければ exit 99）。いまの実物に壊した行は残っていない（3 の表）。PASS。

修正の番号＝1・2・3・10・11・12・13（所見1）／14・15・16・47・48・49・50（所見2）

### A1 — 部品 ts_pos の式が、未来を見ず、最小〜最大の間の位置を出すか（優先度 A）

- **A1-a**＝`_apply_pre` の枝（engine_tuner_exec.py:537〜542）は `lo = s.rolling(n).min()`・`width = s.rolling(n).max() - lo`・`(s - lo) / width.where(width > 0)`。rolling は後ろ向き（いまのバーを含む過去 n本）で未来を見ない。幅0は NaN、窓に NaN が在れば NaN。T47 の既知答えを手で1本ずつ計算した＝5本目 (5−1)÷(5−1)＝1.0／6本目 (3−2)÷(5−2)＝0.333／7〜9本目 0.0／10本目 幅0 で値なし。一致。PASS。
- **A1-b**＝`p_ts_pos`（condition_parts_diag.py:154）は実行器の関数を呼ばない別の書き方（numpy の割り算と `np.where`）。ただし最小・最大は同じ pandas の rolling を使うので、pandas の窓の並びの誤りは両方に同じく出る（並びは A1-a の手計算の既知答えが見ている）。見本は `_BARS = 20000`・n=20 なので、窓 52,596本と「窓の中の値なし」は測らない。PASS（限界は所見9 のリスク8 と同じ）。
- **所見3（Major・A1-c）＝H2（leak_causality_diag.py）は ts_pos の枝を1回も通らない。設計書 4-6 の「T47 の既知答えと H2 で測る」は成り立っていない。**H2 の engine_tuner の経路の検査が走らせる案は、恒等3本と `gen.sample_structure(...)`（束を付けない）だけ（leak_causality_diag.py:325〜336）。入口の乱数の道は `gen_draw=True` で ts_pos を引かない（engine_tuner_gen.py:1805）。ほかの道（1641行）は `same_unit=True` なので ts_pos は入らない。＝H2 の rc=0 は ts_pos が未来を見ないことの証拠にならない。式そのものは A1-a のとおり未来を見ない。
- **A1-d**＝`_mat_key`（engine_tuner_exec.py:2105）は ts_pos を SINCE_OPS・NO_ARG_OPS でない枝で扱い、`ts_pos52596:列名` の形になる。PASS。

修正の番号＝4・5・6・7・8（所見3）

### A2 — `pre_win_bars`・`stage_warm`・本走の余白が、設計書と まこさんの決定のとおりか（優先度 A）

- **A2-a**＝`pre_win_bars` は `round(6 × 365.25 ÷ 12 × 1440 ÷ 5)`＝52,596。`stage_warm` は元データの全部の段の `pre_win` の月の最大を取り、`base_warm + 52,596×5分`（＝242 days 15:00:00・T47 の実測）を返す。`pre_win` が無ければ `base_warm` をそのまま返す。PASS。
- **A2-b**＝実装は `_warm = stage_warm(et.WARM) if a.build_regime else et.WARM`（engine_tuner_gen.py:7840）＝案A のとおり。`dfea4be..HEAD` で変わった .py は3本だけで、ほかの `WARM` を読む所（恒等3本・H2・regime_r9_diag ほか）は1文字も変わっていない。実装は PASS。
- **所見4（Minor・A2-b）＝設計書の文が、案A（`--build-regime` のときだけ）になっていない。**CP46 の修正1 は実装の指示27 の1行だけを直した。元データの次の8か所は「本走は延ばす」のまま＝何を作るか（57行）・4-0 の⑤（85行）・4-3 の run_main の行（132行）・4-11（220行）・4-13 の9番（253行・「60日 → 60日＋182.625日になります」）・4-14 の最後の行（233行）・4-19 の8番（167行）・リスクの6行目（309行）。とくに 4-13 の9番と 4-14 は、付けない本走の土台の数字とデータ量が変わると読める。
- **A2-c**＝`data_fingerprint` は `str(warm)` を指紋に入れる（engine_tuner.py:128）。FINGERPRINT_FILES に組む側・実行器は入っていない。＝キャッシュの作り直しは、余白が変わる `--build-regime` の本走だけで起きる。PASS。

修正の番号＝17・18・19・20・21・22・23・24・25・26・27・28・29・30・31・32（所見4）

### A3 — 段2c の候補の並びと、乱数の道の絞りで、いまの束と入口の案が変わらないか（優先度 A）

- **A3-a**＝`build_stage_candidates` の繰り返しの中で変えたのは、固定の線を `out` に足した後に `_moving` へ写しを足す所だけ。固定の線の `rank` と位置は直す前と同じ。§2.2-0 の表で、段2c のほかの指標の本数（stdev% 42・Donchian幅 42・realized_vol 42・ATR% 45・SQZ_ON 48）は直す前と同じで、BB幅 だけ 42→84、合計 261→303。T42（2本目は一覧の上位から）は「0 件」で通った。順位 1〜261 の3枠目は変わらない。PASS（守りの弱さは所見2）。
- **A3-b**＝`pre_ops` は名前順に並べて返す。`same_unit=False, gen_draw=True` は ['ts_rank','ts_std'] で、直す前の `same_unit=False` と同じ一覧・同じ並び＝`rng.integers(3)` の引き方も同じ。PASS。
- **A3-c**＝`_stage_pick` の記録の「上位」は keep＝候補の本数（303）、`draw["stages"]` も本数を持つので、`--build-regime` の案の指紋は全部変わる。4-13 の11番の書き方（261 → 261＋BB幅 の固定の線の本数）と合う。PASS。

修正の番号＝なし

### A4 — 元データの欄 `pre_win` を読む所（組む側・表を作る道具）が、設計書の形か（優先度 A）

- **A4-a**＝gen_regime_kb.py の5か所は実装の指示18〜22 の文字と同じ（diff で照らした）。形（op と months の2つだけ）・op が前処理の一覧に在るか・months が1以上の整数か、を照らして止める。
- **所見5（Minor・A4-a）＝`expand_stage` は、窓を持たない部品（abs）と状態で区間を決める部品（since_min・since_max・at_entry）を `pre_win` の op に書いても止めない。**止めるのは実行のとき（engine_tuner_exec.py:628・633 の G5「… に n は書けない」）＝元データの段で止まる（fail-closed）という 4-5 の書き方より遅い。いまの元データは ts_pos だけなので実害は無い。
- **A4-b**＝#7 は 1 件（実測）。`gen_stage0_match.py`（.claude/tools）と `regime_r9_diag.py` は `pre` も `pre_win` も読まない（grep 0件）。前者は名前の突き合わせ、後者は候補を `build_stage_candidates` から受け取るだけなので、読まなくて正しい。PASS。

修正の番号＝43（所見5）

### A5 — この実装に、乱数と、新しい数字・点の一覧が0件か（優先度 A）

足した行（.py 3本・gen_regime_kb・元データ2本・壊すプログラム4本）に `random`・`rng`・`shuffle`・`sample(`・`choice`・`integers(` は0件（コメントを除いて grep）。足した数字は、6（逐語）・365.25÷12（暦）・5（H7）・1440（1日の分＝単位の換算）・52,596（その掛け算）・T47 の見本（並び 1〜5・n=5・`[np.nan]*4`）・余白の見本 60日（既存の `WARM` と同じ値）・診断の見本 0.2・20・表示の切り詰め `[:120]`（既存の番人と同じ形）。新しい閾値・範囲・点の一覧は無い。PASS。

修正の番号＝なし

### B1 — 完成の条件のうち「未着手」のまま残った10行（#5〜#14）の閉じ方（優先度 B）

- **B1-a**＝監査が本物で走らせた。#5 rc=0（食い違い0・ts_pos の行 4,565／4,565）／#6 rc=0／#7 1件 rc=0／#8 表のとおりの形で rc=0（ずれ 0件）／#9 rc=0／#10 rc=0（T17 を含む「全部 pass」）／#11・#12・#13 rc=0（3本とも「✅ 全部一致」）。条件の文は満たしている。
- **B1-b**＝走らせなかった行＝**#14**（`gen_signal_families.py --verify`・g2_pass.json を書き替えるため・依頼書の指定）。事実の確認は 3 の表のとおり。

修正の番号＝なし

### B2 — 設計書と実装の食い違いの全件と、その直し方（設計書の側か・実装の側か）（優先度 B）

- **B2-a**＝自己申告は 6 で1件ずつ答えた。
- **所見6（Major・B2-b）＝設計書の 7-7（触る関数と定義の行）と 7-8（SPEC）が、実装の前の中身のまま。そのため engine_tuner_gen.py の本走は、いま設計↔実装ゲートで止まる。**7-7 は `pre_win_bars`・`stage_warm`・`_EXEC_BAR_MIN`・`pre_win` を「（この関数は実物に無い）」、`build_stage_candidates` を2775行（実物は2808行）と書く。設計書 7-6 の文「★触る関数の一覧は、実装の後に確定させます＝`verify_design_contract.py --write` の出力で置き替えます」をやっていない。監査が `false && python3 scripts/priority_rebuild/engine_tuner_gen.py --build-regime`（python は走らない形）で確かめると、hook `require_design_contract_before_run.sh` が「設計書通りに実装されていません…齟齬: 6件」で止めた。＝この工事で直した本走の余白（run_main）は、設計書を作り直して承認し直すまで1回も走らせられない。確認の旗（--selftest・--identity ほか）はゲートを通るので、CC の確かめでは出なかった。前の工事では束1 の最終の控えは0件、束2 の控えは1件残っていた＝同じ抜けが2回目。
- **所見7（Minor・B2-b）＝設計書 4-6 の「法則ファイルは1文字も変えない」と 4-13 の8番「法則…触りません」が、R7 の行番号を直した実物（regime_laws.json:758）と食い違う。**直したこと自体は まこさんの「直す」で正しい。
- ほかの食い違い＝所見3（4-6 の H2）・所見4（案A の8か所）・所見5（4-5 の fail-closed）・所見8（4-13 に無いずれ）・所見9（6-2 リスク8 と 7-4）・所見11（4-7 の段の表）。
- **B2-c**＝`python3 scripts/priority_rebuild/verify_design_contract.py --diff /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md`（SDK の中から・0.43秒・rc=1）の出力（そのまま）:

```
design : /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md
impl   : scripts/priority_rebuild/engine_tuner_gen.py
齟齬: 6件
    実物にあるが設計に無い関数: pre_win_bars
    実物にあるが設計に無い関数: stage_warm
    build_stage_candidates が実物では pre_win_bars を呼んでいるが設計に書いていない
    run_main が実物では stage_warm を呼んでいるが設計に書いていない
    selftest が実物では pre_win_bars を呼んでいるが設計に書いていない
    selftest が実物では stage_warm を呼んでいるが設計に書いていない
```

  ★同じ設計書で `verify_design_contract.py <設計書>`（--diff でない方）は「RESULT: PASS（設計通り）」（2.9秒）。
- **B2-d**＝設計書の側を直すもの＝所見3（4-6）・4・6・7・9 と、所見1・2・3 の実装の指示12。実装の側を直すもの＝所見1・2・3（T47）・5（gen_regime_kb）・10（説明の文）。文書を直すもの＝所見8（milestones2）・11（gen_s22_map）。

修正の番号＝8・9・10・11・12・13・51（所見6）／33・34（所見7）

### B3 — 実装の後に出た、設計書の外の影響と、確かめの道の限界（優先度 B）

- **所見8（Minor・B3-a）＝今回の直しで指す中身が変わった行番号が、R7 のほかに2か所ある。**`engine_tuner_milestones2.md`:60「engine_tuner_gen.py:3714〜3720」（直す前は `needed_qkeys` の中＝いまは51行 下の3765〜3771）と :63「engine_tuner_gen.py:2889〜2893」（直す前は `if stage == "stage2a":` まで＝いまは2929行）。ほかの行番号の引用は、直す前（dfea4be）の時点で既に中身が合っていなかった＝この工事の前からのずれ。KB の R7（regime_detection_kb.md）は 2687 に直っている。
- **B3-b（限界）**＝承認の前の検査の B群（require_design_check_before_approval.py:278〜324）は、やり取りの記録の Bash の結果だけを読む。限界は4つ。①裏で走らせた実行は結果の文字が案内だけなので数えない（自己申告3）。②B2 は「表のコマンドの文字がコマンドに含まれるか」と「止められなかったか（is_error）」だけを見る（:319）。`<表のコマンド> | tail -3` のように後ろにつないだ形は、前の段が落ちても最後の段の終了コードで「止められなかった」になり数えられる。`echo <表のコマンド>` も文字が含まれるので数えられる。③B1 は出力に「期待どおり」と壊すプログラムの名前が在るかを文字で見る。④どのやり取りの記録を読むかは呼び方で決まる＝この監査のセッションでも、読むだけの grep の後に hook `show_design_check_after_write.sh` が監査のやり取りの記録を読んで「不足 9 件」（必読ゲート・B1・B2）を出した。
- **所見9（Minor・B3-c）＝リスク8 を M2-F-2 へ送ったことが、設計書に反映されていない。**6-2 のリスク8 の「どうするか」は「実装の後…数えて記録する」のまま（元データ311行）。7-4（塞げないもの）に「動く線の材料に窓の途中の値なしが在るか＝この工事では数えていない」の行が無い。完成の条件に足す行は無い（数える口が無いので、足すと済にできない行になる）。m2_todo.json:1034 の M2-F-2 には1行 入っている。あわせて、7-4 の1行目の「262位より後ろ」「5,994,822番…より後ろ」は、動く線の最初が262位・案の番号 5,994,822（0から数える）の案が最初に届くので「から後ろ」が正しい。

修正の番号＝39・40（所見8）／53（B3-b）／35・36・37・38（所見9）

### C1 — 名前・説明文・見積もり（優先度 C）

- **所見10（Minor・C1-a）＝直した関数の説明の文が2か所、いまの動きと合わない。**①engine_tuner_exec.py:472「abs は needs_n=False、ほかの7つは欄を持たない」＝ts_pos を足したので8つ。②engine_tuner_gen.py:2813「戻り ＝ 候補の一覧（鍵11個・分離力の高い順）」＝動く線は鍵12個（pre_win）で、固定の線の後ろに続く。ほかに stage_warm の説明「この道具の本走 run_main」は所見4 と同じ（呼ぶ側が `--build-regime` で分ける）。ts_pos・pre_win_bars・動く線の分岐・run_main のコメントは動きと合う。
- **所見11（Minor・C1）＝設計書 4-7 の「§2.2 の段の表」に、§2.2-0（機械が作る展開の表）の行が混ざっている（「段§2.2」「段指標」「段`close」ほか・「段の件数＝125件（§2.2 に在るものを1つも落としていません）」）。**`gen_s22_map.py` の切り出しの終わりの目印が「### §2.2-1」で、間の「### §2.2-0」（milestones2:772）の表まで段として拾うため。束2 の控えから同じ（束1 の控えは0件）＝この工事の前からの道具の不具合。監査が `python3 .claude/tools/gen_s22_map.py --verify` を走らせると「対応表に無い項目が在る: ['段§2.2', '段レンジ幾何', … ]（fail-closed 3）」で止まった（0.08秒）。
- **C1-b**＝見積もり（コード30分・確かめ約20分・壊すプログラム約23分）から外れた原因は3つで、どれも設計書に書けた。①承認の前の検査の B群が「表のとおりの文字で、手前で走らせた結果」しか数えない（自己申告3）＝組む側の自己テストと壊すプログラムの測りが2回ずつになった。②法則ファイル R7 の行番号のずれ（4回目・§6 の93番で既知）＝行番号の引用を grep していれば 4-13 に書けた。③設計書 4-4 の手順8（G2→H2）と手順11（`pre_audit_check.py --run`＝ORDER に G2・H2 が入っている）で、G2・H2 を2回ずつ走らせる順番になっていた。

修正の番号＝41・42（所見10）／44・45・46（所見11）／52・53（C1-b）

### 省いた問い

なし（A0〜C1 を全部 答えた）。


## 5. 外部検索

### 検索 1 — なし

しなかった（依頼書の指定＝外部検索は設計書の監査 CP46 で済んでいる）。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

そのとおり。`git show dfea4be` の実行器で `wpct_arr` は2669行、いまは2687行（18行 下がった）。法則ファイル758行は `:2687`、`gen_regime_kb.py --verify all` はずれ 0件、`--selftest` は 15/15（どちらも監査が走らせた）。ただし、①設計書 4-6 と 4-13 の8番は「法則ファイルは変えない」のまま（所見7）②今回の直しでずれた行番号は R7 だけでなく、milestones2 の60行・63行にも在る（所見8）。

### 自己申告 2

そのとおり。m2_todo.json:1034 に M2-F-2 の1行が在る。ただし設計書 6-2 のリスク8 の「どうするか」と 7-4 は、送った後の形に直っていない（所見9）。

### 自己申告 3

そのとおり（hook の :296〜323 を読んだ）。加えて、B2 は文字の包含と「止められなかったか」だけを見るので、後ろにパイプをつないだ形や `echo` の形も数える＝数えなさすぎと数えすぎの両方の穴が在る（B3-b）。

### 自己申告 4

読みは正しい。py_compile は `.claude/tools/__pycache__` への書き込みを伴うので土台ゲートの相手になる。監査が走らせた `gen_regime_kb.py --verify all`（rc=0）と `--selftest`（15/15）は、この .py を読み込んで動かしているので、構文は通っている。

### 自己申告 5

読みは正しい。型の表・出口の表・印を作る道具（gen_signal_families.py・gen_exit_families.py・gen_indicator_switch.py）は `MATERIAL_PRE`・`pre_ops`・`ts_pos`・`ts_rank` を1回も読まない（grep 0件）。`pre_audit_check.py --verify` は「監査に出せます」（監査が走らせた）。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝①ts_pos は過去 n本の最小〜最大の中の位置を 0〜1 で出し、いまのバーを含め、幅0と値なしは値なし・未来を見ない〔A1-a の手計算と T47 の②〕②入口の乱数の道（1805行）は ts_pos を引かず、ほかの道（1641行）にも入らない〔A3-b〕③段2c の動く線は 42 本＝BB幅 の固定の線 42 本・窓 52,596本・固定の線の後ろ〔T47 と §2.2-0 の表〕④stage_warm は 242 days 15:00:00 を返し、run_main は `--build-regime` のときだけ使う〔7840行〕⑤§2.2-0・突き合わせ・部品の正本に載っている〔#5・#7〕。壊すプログラム4本は宣言どおりの欄で落ちた記録〔breaks.json〕。守りの穴＝T47 の⑤と③は文字と欄の数字だけを見る〔所見1・2〕・H2 は ts_pos を通らない〔所見3〕が、いまの実物は設計書の決めた動きをしている）
- 問い2 ＝ YES（根拠＝食い違いを8種・全件挙げた＝7-7/7-8 の SPEC が古い〔所見6〕・案A が8か所の文に無い〔所見4〕・4-6 の H2 の主張〔所見3〕・4-6/4-13 の法則ファイル〔所見7〕・6-2 リスク8 と 7-4〔所見9〕・4-13 に無い行番号のずれ〔所見8〕・4-5 の fail-closed〔所見5〕・4-7 の段の表〔所見11〕。どれも修正の指示で、設計書の側か実装の側かを分けた）

### 結論と件数

- 結論＝GO
- Critical＝0
- Major＝3
- Minor＝8
- Process＝3


## 8. 修正の指示

### Critical

なし

### Major

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 7239〜7240行（selftest の T47 の⑤）
直す前の文字:
~~~
        if "_warm, use_cache=not a.no_cache)" not in _rm47:
            _ng47.append("⑤本走（run_main）が stage_warm の余白でデータを読んでいない")
~~~
直した後の文字:
~~~
        if ("_warm, use_cache=not a.no_cache)" not in _rm47 or "_warm = stage_warm(et.WARM) if a.build_regime else et.WARM" not in _rm47):
            _ng47.append("⑤本走（run_main）が --build-regime のときだけ stage_warm の余白でデータを読む形になっていない")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
状態: 確定

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 408行（実装の指示12 の中身・T47 の⑤）
直す前の文字:
~~~
if \"_warm, use_cache=not a.no_cache)\" not in _rm47:\n            _ng47.append(\"⑤本走（run_main）が stage_warm の余白でデータを読んでいない\")
~~~
直した後の文字:
~~~
if (\"_warm, use_cache=not a.no_cache)\" not in _rm47 or \"_warm = stage_warm(et.WARM) if a.build_regime else et.WARM\" not in _rm47):\n            _ng47.append(\"⑤本走（run_main）が --build-regime のときだけ stage_warm の余白でデータを読む形になっていない\")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
状態: 確定

#### 修正 3
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 4
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 7212行（selftest の T47 の②の既知答えの行の直後）
直す前の文字:
~~~
            _ng47.append(f"②既知答えと違う: {list(np.round(_g47, 4))}（期待 {list(np.round(_w47, 4))}）")
~~~
足す文字:
~~~

        if not np.allclose(ex._apply_pre(_a47[:-1], {"op": "ts_pos", "n": 5}), _g47[:-1], equal_nan=True):
            _ng47.append("②最後の1本を落とすと、その前の値が変わる（未来のバーを見ている）")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py:336「r = gen.strip_marks(gen.sample_structure(np.random.default_rng([TUNER_SEED, i]), lm, pool, ["5m", "15m"]))」
状態: 確定

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 408行（実装の指示12 の中身・T47 の②）
直す前の文字:
~~~
_ng47.append(f\"②既知答えと違う: {list(np.round(_g47, 4))}（期待 {list(np.round(_w47, 4))}）\")
~~~
足す文字:
~~~
\n        if not np.allclose(ex._apply_pre(_a47[:-1], {\"op\": \"ts_pos\", \"n\": 5}), _g47[:-1], equal_nan=True):\n            _ng47.append(\"②最後の1本を落とすと、その前の値が変わる（未来のバーを見ている）\")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py:336「r = gen.strip_marks(gen.sample_structure(np.random.default_rng([TUNER_SEED, i]), lm, pool, ["5m", "15m"]))」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 115行（4-6 の「未来のデータを使わない」の行）
直す前の文字:
~~~
| 未来のデータを使わない | cat_requirements §4.6 の H2 | rolling の最小・最大は過去 n本だけ。T47 の既知答えと H2（`leak_causality_diag.py`）で測る |
~~~
直した後の文字:
~~~
| 未来のデータを使わない | cat_requirements §4.6 の H2 | rolling の最小・最大は過去 n本だけ。T47 の②（既知答えと、最後の1本を落としても前の値が変わらないこと）で測る。★H2（`leak_causality_diag.py`）が走らせる案（恒等3本と、入口の案を乱数の道で作った案）には ts_pos が入らないので、H2 はこの部品を通らない（監査 CP47） |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:1805「_pre_opts = [None] + ex.pre_ops(same_unit=False, gen_draw=True)   # ★2026-09-27（M2-E-4e）＝乱数の道で引かない部品（ts_pos）を外す」
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
根拠の抜き書き: .claude/state/acceptance.md:1433「**★触る関数の一覧は、実装の後に確定させます**＝`verify_design_contract.py --write` の出力で置き替えます。」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし。7-7・7-8 は `spec_from_impl` で実物から作り直される）
状態: 確定

#### 修正 9
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
cd v3-bitget-api-sdk/bitget-python-sdk-api && python3 scripts/priority_rebuild/verify_design_contract.py --diff /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md
~~~
根拠の抜き書き: .claude/hooks/require_design_contract_before_run.sh:15「③設計書に SPEC が在れば `--diff` で両方向に突き合わせ、齟齬が在れば止める。」（監査が走らせた＝0.43秒・rc=1・齟齬 6件。修正 8 の後に「齟齬: 0件」になることを確かめる）
状態: 確定

#### 修正 10
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
cd v3-bitget-api-sdk/bitget-python-sdk-api && python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest
~~~
根拠の抜き書き: .claude/hooks/require_design_check_before_approval.py:32「B2 その行の「その数字を出したコマンド」を走らせて、止められずに終わったか」（監査が走らせた＝374秒・rc=0）
状態: 確定

#### 修正 11
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/run_breaks.py --design .claude/state/acceptance.md --measure-only
~~~
根拠の抜き書き: .claude/hooks/require_design_check_before_approval.py:31「B1 表に載っている既存の壊すプログラムが、--measure-only で「✅ 期待どおり」だったか」（監査は走らせていない＝本物のファイルを壊して戻すため。CC の実測＝4本まとめて約25分・session_worklog_20260927.md §8）
状態: 確定

#### 修正 12
対象のファイル: .claude/state/acceptance.approved
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:298「- 次＝まこさんに承認（`bash .claude/hooks/approve_impl.sh`）をお願いする（6段の④の前）。」（まこさんが端末から打つ・CC の Bash からは承認ゲートが止める＝監査が実測。時間の実測なし）
状態: 未決

#### 修正 13
対象のファイル: .claude/state/pre_audit_check.json
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/pre_audit_check.py --run
~~~
根拠の抜き書き: .claude/state/acceptance.md:285「11. `python3 .claude/tools/pre_audit_check.py --run` と `--verify` を走らせ（組む側と実行器の指紋が変わるため。ORDER の型の表と出口の表の `--write` は、部品の一覧を読まないので要らない）、「監査に出せます」が出てから実装の監査に出します。」（監査は走らせていない＝G2・H2 の印を書き替えるため。CC の実測＝H2 300.4秒ほか・約8分）
状態: 確定

### Minor

#### 修正 14
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 7231行（selftest の T47 の③・固定の線の後ろか）
直す前の文字:
~~~
        if _mv47 and _fx47 and min(c["rank"] for c in _mv47) <= max(c["rank"] for c in _fx47):
~~~
直した後の文字:
~~~
        if _mv47 and _fx47 and min(i for i, c in enumerate(_c47) if c.get("pre_win")) <= max(i for i, c in enumerate(_c47) if not c.get("pre_win")):
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3188「c = cands[r - 1]」
状態: 確定

#### 修正 15
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 408行（実装の指示12 の中身・T47 の③）
直す前の文字:
~~~
if _mv47 and _fx47 and min(c[\"rank\"] for c in _mv47) <= max(c[\"rank\"] for c in _fx47):
~~~
直した後の文字:
~~~
if _mv47 and _fx47 and min(i for i, c in enumerate(_c47) if c.get(\"pre_win\")) <= max(i for i, c in enumerate(_c47) if not c.get(\"pre_win\")):
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3188「c = cands[r - 1]」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 17
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 57行（何を作るか）
直す前の文字:
~~~
だから動く線を使う走行（組む側の本走 `run_main`）だけ、
~~~
直した後の文字:
~~~
だから動く線を使う走行（`--build-regime` を付けた組む側の本走 `run_main`）だけ、
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 19
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 85行（4-0 の⑤）
直す前の文字:
~~~
「余白の直し方→C」で、動く線を使う走行（組む側の本走 `run_main`）だけ、
~~~
直した後の文字:
~~~
「余白の直し方→C」で、動く線を使う走行（`--build-regime` を付けた組む側の本走 `run_main`・監査 CP46 の修正1「案A」）だけ、
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 21
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 132行（4-3 の run_main の行）
直す前の文字:
~~~
| `engine_tuner_gen.run_main` | 本走のデータを `stage_warm(et.WARM)` の余白で読む | 直す（実装の指示 27） |
~~~
直した後の文字:
~~~
| `engine_tuner_gen.run_main` | `--build-regime` を付けた本走だけ、データを `stage_warm(et.WARM)` の余白で読む（付けないときは `et.WARM`） | 直す（実装の指示 27） |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 23
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 220行（4-11 のデータの前の余白）
直す前の文字:
~~~
**データの前の余白。**動く線を使う走行（組む側の本走 `run_main`）は、
~~~
直した後の文字:
~~~
**データの前の余白。**動く線を使う走行（`--build-regime` を付けた組む側の本走 `run_main`）は、
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 25
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 253行（4-13 の9番）
直す前の文字:
~~~
9. **組む側の本走のデータの余白。**60日 → 60日＋182.625日になります。
~~~
直した後の文字:
~~~
9. **組む側の本走のデータの余白。**`--build-regime` を付けた本走だけ、60日 → 60日＋182.625日になります（付けない本走は60日のまま・監査 CP46 の修正1「案A」）。
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
状態: 確定

#### 修正 26
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 27
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 233行（4-14 の最後の行）
直す前の文字:
~~~
| 本走（run_main）が読むデータの行 |
~~~
直した後の文字:
~~~
| `--build-regime` を付けた本走（run_main）が読むデータの行 |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
状態: 確定

#### 修正 28
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 29
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 167行（4-19 の8番）
直す前の文字:
~~~
8. **余白。**組む側の本走は、値決め窓の開始 2024-03-01 の
~~~
直した後の文字:
~~~
8. **余白。**`--build-regime` を付けた組む側の本走は、値決め窓の開始 2024-03-01 の
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
状態: 確定

#### 修正 30
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 31
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 309行（リスクの6行目）
直す前の文字:
~~~
"中身": "組む側の本走の余白が延びて、
~~~
直した後の文字:
~~~
"中身": "`--build-regime` を付けた組む側の本走の余白が延びて、
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:7840「_warm = stage_warm(et.WARM) if a.build_regime else et.WARM」
状態: 確定

#### 修正 32
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 33
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 118行（4-6 の「法則を決めない」の行）
直す前の文字:
~~~
| 法則を決めない | まこさん 2026-09-09「お前が法則を決めるな」 | 法則ファイルは1文字も変えない。R6 の読みは まこさんの決定のとおり |
~~~
直した後の文字:
~~~
| 法則を決めない | まこさん 2026-09-09「お前が法則を決めるな」 | 法則の中身（判定・逐語・出どころ）は1文字も変えない。R6 の読みは まこさんの決定のとおり。★R7 の注意の文の行番号（`engine_tuner_exec.py:2669` → `:2687`）は、実装で実行器の行が18行 下がったので直した（まこさん「直す」・2026-09-27） |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/regime_laws.json:758「W%＝`wpct_arr`（`engine_tuner_exec.py:2687`）」
状態: 確定

#### 修正 34
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 35
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 311行（リスクの8行目の「どうするか」）
直す前の文字:
~~~
"どうするか": "実装の後、本走の余白で読んだ値決め窓・確認窓で、BB幅 の動く線の材料の値なしの本数を数えて記録する。窓の始まりの後に値なしが在れば止まって まこさんに出す"
~~~
直した後の文字:
~~~
"どうするか": "M2-F-2（段を測る道具の設計書）で、stage_warm の余白で読んだ値決め窓・確認窓の、BB幅 の動く線の材料の値なしの本数を数えて出す口を作る（まこさん決定「案1」・2026-09-27・m2_todo.json の M2-F-2）。この工事では数えていない。窓の始まりの後に値なしが在れば止まって まこさんに出す"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_todo.json:1034「★2026-09-27（M2-E-4e の設計書 6-2 のリスク8・監査 CP46 の修正7・まこさん決定「案1」）＝この設計書に、BB幅 の動く線の材料の値なし（NaN）の本数を、stage_warm の余白で読んだ値決め窓・確認窓で数えて出す口を入れる。」
状態: 確定

#### 修正 36
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 37
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 355行（塞げないものの1行目）
直す前の文字:
~~~
{"問い": "本走（run_main）の束が動く線を実際に使うか", "塞げないこと": "使いません。3枠目の順位は案の番号から決まり（regime_draw_order）、動く線は段2c の 262位より後ろに並ぶので、届くのは案の番号 5,994,822番（C(263,3)×2）より後ろです。動く線を測るのは M2-F-13 の道具で、その余白は M2-F-2 で直します"},
~~~
直した後の文字:
~~~
{"問い": "本走（run_main）の束が動く線を実際に使うか", "塞げないこと": "使いません。3枠目の順位は案の番号から決まり（regime_draw_order）、動く線は段2c の 262位から後ろに並ぶので、届くのは案の番号 5,994,822番（0から数える・C(263,3)×2）から後ろです。動く線を測るのは M2-F-13 の道具で、その余白は M2-F-2 で直します"},
    {"問い": "BB幅 の動く線の材料に、窓の途中の値なしが在るか", "塞げないこと": "この工事では数えていません（まこさん決定「案1」＝M2-F-2 の設計書で数える口を作る）。窓 52,596本の rolling の最小・最大は、窓の中に値なしが1本でも在ると値なしを返すので、在ればその後の6か月が黙って不成立になります"},
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:2359「def regime_draw_order(n: int) -> tuple[int, int, int, str]:」
状態: 確定

#### 修正 38
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 39
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md
直す箇所: 60行
直す前の文字:
~~~
| 分位をまとめて計算 | 入っている | engine_tuner_gen.py:3714〜3720 |
~~~
直した後の文字:
~~~
| 分位をまとめて計算 | 入っている | engine_tuner_gen.py の needed_qkeys の中（★行番号は M2-E-4e の実装で51行 下がったので関数の名前にした・監査 CP47） |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3722「def needed_qkeys(recipes: list[dict]) -> dict[str, tuple]:」
状態: 確定

#### 修正 40
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md
直す箇所: 63行
直す前の文字:
~~~
| §2.2-2 の C（向きを持つ指標の絶対値） | 入っている | engine_tuner_gen.py:2889〜2893 |
~~~
直した後の文字:
~~~
| §2.2-2 の C（向きを持つ指標の絶対値） | 入っている | engine_tuner_gen.py の build_stage_candidates の「if stage == "stage2a":」の枝（★行番号は M2-E-4e の実装で36行 下がったので関数の名前にした・監査 CP47） |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:2929「if stage == "stage2a":」
状態: 確定

#### 修正 41
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py
直す箇所: 472行（pre_ops の needs_n の絞りのコメント）
直す前の文字:
~~~
                  #   abs は needs_n=False、ほかの7つは欄を持たない（＝True とみなす）。
~~~
直した後の文字:
~~~
                  #   abs は needs_n=False、ほかの8つは欄を持たない（＝True とみなす）。
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py:430「"ts_pos": {"desc": "いまの値が 直近 n本の最小〜最大の間のどこか（0〜1・いまのバーを含める）",」
状態: 確定

#### 修正 42
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 2813行（build_stage_candidates の説明の戻り）
直す前の文字:
~~~
    戻り  ＝ 候補の一覧（鍵11個・分離力の高い順）
~~~
直した後の文字:
~~~
    戻り  ＝ 候補の一覧（鍵11個・分離力の高い順。★動く線〔鍵 pre_win を足した12個〕は、固定の線を全部 並べた後ろに同じ順で続く・M2-E-4e）
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:2966「# ★動く線は、固定の線の後ろに順位を続けて並べる（M2-E-4e）」
状態: 確定

#### 修正 43
対象のファイル: .claude/tools/gen_regime_kb.py
直す箇所: 1079行（expand_stage の pre_win の照らし）
直す前の文字:
~~~
                ng.append(f"{_k}: 知らない前処理 → {_f} に {_pw['op']}（前処理の一覧＝{sorted(pres_all)}）")
~~~
足す文字:
~~~

            elif _pw["op"] not in __import__("engine_tuner_exec").pre_ops(needs_state=False, needs_n=True):
                ng.append(f"{_k}: 窓を持たない前処理 → {_f} に {_pw['op']}（窓つきにできるのは本数 n で窓を決める部品だけ）")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py:633「_fail("G5", f"材料の前処理 {pre['op']} に {_k} は書けない"」
状態: 未決

#### 修正 44
対象のファイル: .claude/tools/gen_s22_map.py
直す箇所: 54行（§2.2 の節の切り出しの終わりの目印）
直す前の文字:
~~~
SEC_END = "### §2.2-1"
~~~
直した後の文字:
~~~
SEC_END = "### §2.2-0"          # ★2026-09-27（監査 CP47）＝直す前は §2.2-0（機械が作る展開の表）の表まで段として拾っていた
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md:772「### §2.2-0 ★段ごとの候補を、正本の指標の名前に展開した表（この囲みは機械が作ります）」
状態: 確定

#### 修正 45
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/s22_map.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_s22_map.py --verify
~~~
根拠の抜き書き: .claude/tools/gen_s22_map.py:54「SEC_END = "### §2.2-1"」（監査が直す前に走らせた＝0.08秒・「対応表に無い項目が在る: ['段§2.2', '段レンジ幾何', …]（fail-closed 3＝黙って落とさない）」）
状態: 確定

#### 修正 46
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」（監査は走らせていない＝本物の設計書を書き替える道具のため・時間の実測なし）
状態: 確定

#### 修正 47
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
cd v3-bitget-api-sdk/bitget-python-sdk-api && python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest
~~~
根拠の抜き書き: .claude/hooks/require_design_check_before_approval.py:32「B2 その行の「その数字を出したコマンド」を走らせて、止められずに終わったか」（監査が走らせた＝374秒・rc=0）
状態: 確定

#### 修正 48
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/run_breaks.py --design .claude/state/acceptance.md --measure-only
~~~
根拠の抜き書き: .claude/hooks/require_design_check_before_approval.py:31「B1 表に載っている既存の壊すプログラムが、--measure-only で「✅ 期待どおり」だったか」（監査は走らせていない＝本物のファイルを壊して戻すため。CC の実測＝4本まとめて約25分）
状態: 確定

#### 修正 49
対象のファイル: .claude/state/acceptance.approved
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:298「- 次＝まこさんに承認（`bash .claude/hooks/approve_impl.sh`）をお願いする（6段の④の前）。」（まこさんが端末から打つ・時間の実測なし）
状態: 未決

#### 修正 50
対象のファイル: .claude/state/pre_audit_check.json
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/pre_audit_check.py --run
~~~
根拠の抜き書き: .claude/state/acceptance.md:285「11. `python3 .claude/tools/pre_audit_check.py --run` と `--verify` を走らせ（組む側と実行器の指紋が変わるため。ORDER の型の表と出口の表の `--write` は、部品の一覧を読まないので要らない）、「監査に出せます」が出てから実装の監査に出します。」（監査は走らせていない＝G2・H2 の印を書き替えるため。CC の実測＝約8分）
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 51
対象のファイル: .claude/tools/pre_audit_check.py
直す箇所: 71行（CHECKS の最後の行）
直す前の文字:
~~~
    "engine_tuner_gen.py --selftest-extra-gate",
~~~
足す文字:
~~~

    # ★2026-09-27（監査 CP47 の Process）＝設計書の SPEC と実物の突き合わせ。実装の後に設計書の SPEC を作り直していないと、本走が設計↔実装ゲートで止まる（M2-E-4e で齟齬 6件のまま監査に出た）。
    "verify_design_contract.py --diff /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md",
~~~
根拠の抜き書き: .claude/state/acceptance.md:1433「**★触る関数の一覧は、実装の後に確定させます**＝`verify_design_contract.py --write` の出力で置き替えます。」
状態: 未決

#### 修正 52
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/acceptance_checklist.md
直す箇所: 40行（C 変更の単位の「過去に破棄した失敗」の行の直後）
直す前の文字:
~~~
- ☐ 【群1】 過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行）
~~~
足す文字:
~~~

- ☐ 【群1】 **新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るか**を開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（最後の1本を落としても前の値が変わらない）の確かめを入れる（監査 CP47）
- ☐ 【群1】 **直すファイルの行番号を指している文書**を `git grep -n -E 'engine_tuner_(exec|gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R7 と engine_tuner_milestones2.md の2行が、実装で行が下がって外れた）
~~~
根拠の抜き書き: .claude/state/acceptance.md:239「| 未来のデータを使わない | cat_requirements §4.6 の H2 | rolling の最小・最大は過去 n本だけ。T47 の既知答えと H2（`leak_causality_diag.py`）で測る |」
状態: 未決

#### 修正 53
対象のファイル: .claude/hooks/require_design_check_before_approval.py
直す箇所: 319行（B2 の照らし）
直す前の文字:
~~~
        ok2 = any(ts >= need and not err and cmd_want in cmd for ts, cmd, out, err in runs)
~~~
直した後の文字:
~~~
        ok2 = any(ts >= need and not err
                  and re.search(r"(^|&&|;)\s*" + re.escape(cmd_want) + r"\s*$", cmd.strip())
                  for ts, cmd, out, err in runs)
~~~
根拠の抜き書き: .claude/hooks/require_design_check_before_approval.py:32「B2 その行の「その数字を出したコマンド」を走らせて、止められずに終わったか」
状態: 未決


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

**開いたファイルと行（Plan サブエージェントが Read tool または sed/grep で画面に出したもの）**

- 依頼書：全432行。設計書 `.claude/state/acceptance.md`：全1,868行（Read）。元データ `acceptance_src.json`：1〜288行（Read）・289〜427行（sed）・57・85・115・118・132・167・220・233・253・303〜313・354〜358・408行（grep/sed）。
- `git diff dfea4be -- `（依頼書の7ファイル）の全文・`git diff dfea4be HEAD -- m2_todo.json`・`git diff --stat dfea4be HEAD`。
- engine_tuner_exec.py：400〜549・612〜641・2060〜2134（Read）、472・626〜629（sed）。
- engine_tuner_gen.py：727〜856・2359〜2558・2808〜2977・3150〜3569（Read）、5165〜5200・7212〜7240・3188・2929（sed/grep）、`git show dfea4be` の 2889〜2893・3714〜3720 と関数の定義行。
- condition_parts_diag.py：110〜168・300〜335・425〜445・41。m2_stage_candidates.json：72〜96。condition_parts.json：222〜236（diff）。
- .claude/tools/gen_regime_kb.py：960〜1040・1072〜1082・1193〜1240。gen_s22_map.py：1〜128。gen_acceptance.py：300〜330・370〜390・410〜440・1040〜1060。pre_audit_check.py：40〜110。gen_stage0_match.py（grep のみ）。
- 壊すプログラム b109〜b112（全文）・lib.sh（全101行）。承認の控え `m2e4e-r6-moving-line-20260927.breaks.json`・`.frozen.json`・`.dirty.json`（全文）・`.01.sha.txt`。
- 設計書の監査 CP46 の結果：全615行（Read）。
- regime_laws.json：700〜760。engine_tuner.py：95〜155。engine_tuner_milestones2.md：3〜16・55〜65・725〜771・930〜1000・2055〜2064。m2_todo.json：1034（grep）。
- require_design_check_before_approval.py：1〜40・230〜329。require_design_contract_before_run.sh：1〜120・330〜400。
- session_worklog_20260927.md：149〜357（§5〜§9）。permanent_rules.md：59・64・65・67・69・71番。
- leak_causality_diag.py：1〜80・296〜365。verify_design_contract.py：1770〜1825。acceptance_checklist.md：36〜41（Read）。g2_pass.json・h2_pass.json（先頭）。
- ★cat_requirements.md の §4.6（H2・H6・H7・H16）と acceptance_checklist.md の全文は、セッションに自動で読み込まれた本文で読んだ（Read tool では開いていない）。
- ★依頼書の行番号と実物のずれ＝MATERIAL_PRE 417〜445 → 実物 417〜446／`_apply_pre` 505〜545 → 505〜543／T47 7190〜7250 → 7193〜7249／run_main の読み込み 7835〜7845 → 7838〜7843／`build_stage_candidates` 2808〜2974 → 2808〜2972／T1-C6e 5255〜5295 → 5258〜／`_EXEC_BAR_MIN`〜`stage_warm` 2555〜2580 → 2557〜2579。ほかは合っていた。
- ★結果ファイルを書く前に、監査のセッション（本体）が、修正の指示と所見が引いている行を全部 sed・Read で開き直し、直す前の文字が相手のファイルの中でちょうど1か所に当たることを `grep -c -F`・`grep -o -F | wc -l` で数えた（修正 1・2・4・5・7・14・15・17・19・21・23・25・27・29・31・33・35・37・39・40〜44・51〜53＝全部 1）。

**走らせたコマンドと結果と秒数**

- `shasum -a 256`（設計書・元データ・控え）＝2999e9a8…・bcdeabf2…・f18554aa…（最初と最後で同じ）。
- `verify_design_contract.py --diff <設計書>`（SDK から）＝rc=1・齟齬 6件・0.43秒。`verify_design_contract.py <設計書>`＝RESULT: PASS・2.9秒。
- `engine_tuner_gen.py --selftest`＝rc=0・「✅ 全部 pass」・374秒。2回目（T47 の行を拾うため）＝rc=0・T47 の行は事実データと同じ（秒数は測っていない）。
- `condition_parts_diag.py`＝rc=0・3〜4秒。`engine_tuner_exec.py --selftest`＝rc=0・9秒。完成の条件 #7 の grep＝1。
- `gen_regime_kb.py --verify all`＝rc=0・3.7秒（SDK から表のとおりの形でも rc=0）。`gen_regime_kb.py --selftest`＝15/15・0.2秒。
- `gen_materials.py --verify`＝rc=0・6.1秒。`--selftest`＝rc=0・71.5秒。
- `engine_tuner_exec.py --identity`・`--identity-l1`・`--identity-s1`＝3本とも rc=0「✅ 全部一致」・6.5秒・3.7秒・16.3秒。
- `gen_s22_map.py --verify`＝fail-closed 3（段の混入）・0.08秒。`pre_audit_check.py --verify`＝「監査に出せます」・0.1秒。
- `false && python3 scripts/priority_rebuild/engine_tuner_gen.py --build-regime`（python は走らない形）＝hook require_design_contract_before_run.sh が「齟齬: 6件」で止めた。
- grep・sed・git diff/show/status・stat・cat（読むだけ）。

**走らせられなかったものと理由**

- 作業場 cp47_work への写しの作成と、写しでの b109〜b112 の走らせ直し＝監査役（Plan サブエージェント）は「ファイルを作らない・状態を変えない」決まりで動くため。lib.sh の ROOT は本物のパスに固定なので、写しを作らずに壊すプログラムを走らせると本物のファイルを書き替える＝走らせていない。
- 完成の条件 #14 `gen_signal_families.py --verify` と `leak_causality_diag.py`＝g2_pass.json・h2_pass.json を書き替えるため（依頼書の指定）。
- `gen_acceptance.py --write`・`apply_audit_fix.py`・`pre_audit_check.py --run`・`gen_materials.py --write`・`gen_regime_kb.py --write`＝本物を書き替える道具のため。`approve_impl.sh`＝まこさんだけが打つ（`ls` で名前を見ようとしただけで承認ゲートが止めた）。
- `python3 -c "…"`＝hook require_design_contract_before_run.sh に止められた（逐語「走らせる .py を確定できないコマンドです」）。`for` の繰り返しで .py を走らせる形も同じ hook が止めた。
- 時刻を測る代入と道具のパスを同じ行に書いた形・`2>&1` と `cut` を守りの相手のファイルと同じ行に書いた形・`cd` と道具のパスを含む grep＝hook require_acceptance_before_impl.sh（土台ゲート・Bash）に止められた＝分けて打ち直すか Read tool で開いた。
- 読むだけの grep の後に、hook show_design_check_after_write.sh が監査のやり取りの記録を読んで「不足 9 件」を画面に出した（ファイルは何も変わっていない）。
- ★写しの .py を走らせたときに設計↔実装ゲートが本物の名前で照らして止める件（CP45 の自己申告1）は、写しを作らなかったので起きていない。


## 11. 本物のファイルを書き替えていないこと

監査の最後の `git status --short`（作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work`〜`cp47_work` の未追跡の行は写し・下書きとして省いた）:

```
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
?? .claude/hooks/require_chat_draft_before_long_reply.sh
?? .claude/settings.json.bak_20260819
?? .claude/settings.json.bak_20260826
?? .claude/settings.json.bak_20260902_implock
?? .claude/settings.json.bak_20260903_a6
?? .claude/settings.json.bak_m2_2_2b
?? v3-bitget-api-sdk/bitget-python-sdk-api/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_L1.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_v59.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/results/
```

- 監査を始めたときの `git status --short` と同じ。` M decisions.md` は監査を始める前から在った（更新時刻 12:33:57＝監査の最初のコマンドより前）。
- cp47_work の未追跡の行は `cp47_result.md`（結果の下書き・監査のセッションが道具で作った）の1行だけ。
- ログ4本（*.log）の更新時刻は 7月27日〜8月19日のまま＝監査の走行で書き替わっていない。
- 設計書 2999e9a8…・元データ bcdeabf2… は最初と最後で同じ。監査役はファイルを1つも作っていない・書き替えていない。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-27_m2e4e_r6_moving_line_impl_cp47_audit_request.md request_sha256=a7ae356c1ca8bf90b05941ca7d666c3ba06e98ccc8af920f9d23b5a1d092f241 -->
