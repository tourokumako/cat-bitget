# 監査依頼 CP27 — M2-D の「需給を順位に入れる」工事が、設計書どおりにできているか

## ⚠️ auditor 宣言ブロック

**あなたは auditor session の CC です。**メインの CC ではありません。auto-load される文書（CLAUDE.md・cc_role.md ほか）は参考であり、**着手前の必読は この依頼書に書いた8件だけ**です。確認質問をせず、すぐ Plan agent を起動してください。

## 0. この監査で答えてほしいこと（★1つだけ）

> **M2-D｜場面を分ける材料の順位を engine_tuner に渡す。そのうち今回の工事＝需給3列（taker_ls・L-S比・CVD）を、場面を分ける材料の成績表 `material_ranking.json` に足し、生成器が順位からその3列を読めるようにする。**

**これが設計書（承認済み・iter="demand-in-ranking-20260907"）どおりにできているかどうか。それが、この監査の結論です。**

### 結論（GO / NO-GO）の決め方

**結論を決めるのは、下の①と②の2つだけです。**

承認の仕組み・設計書の形・記録の書き方・依頼書の書き方について気づいたことは、書いてください。ただし、別枠の指摘として §6 に置き、結論には効かせないでください。①と②ができていれば GO です。

**★例外**＝その仕組みの不備が、①か②の達成を実際に妨げている場合は、結論に効かせてください。そのときは「どう妨げているか」を実物で示してください。

### ①と②の中身

| # | 要件 | 何が言えたら「できている」か |
|---|---|---|
| **①** | 需給3列が、指標と同じ物差しで成績表の順位に載っている | **`material_ranking.json` の sufficiency（型の表で系統「需給」を持つ役割）に、需給3列が、正解ラベル3本（強さ・向き・大きさ）× 先読み2本（24・288）の全18組で載っている。**分離力は、同じ入力で `rank_separation` を直に呼んだ値と一致する（＝式を書き写していない）。値決め窓だけで測っている。**指標の列（6,101本）の分離力と順位は、足す前後で1つも変わっていない。** |
| **②** | 生成器が、順位から需給3列を読める | **`engine_tuner_gen.ranked_materials("sufficiency")` に需給3列が出る。**印（`indicator_switch.json` の `demand_on`）から1件 外すとその列だけ消え、戻すと出る。`ranked_groups("sufficiency")` に需給の組が出て、`ranked_groups("location")` と `ranked_groups("env")` には1つも混ざらない（場面の判定の束が使う順位は location と env だけ＝そこは変わっていない）。 |

**★この工事の範囲の外（結論に入れない）**＝需給を場面の判定の束（`sample_regime_build`）に引く道は作っていません（M2-E で相場の法則から決める）。需給が net に効くかも測っていません。詳しくは §4。

## 1. 着手前に読むもの（8件）

| # | ファイル | どこを |
|---|---|---|
| 1 | `.claude/ratchet/acceptance_archive/demand-in-ranking-20260907.md` | 全文（承認済みの設計書・2回目の版＝完成の条件3行が「済」・機械が壊すプログラム3本を走らせた記録つき） |
| 2 | `.claude/state/session_worklog_20260904.md` | **§49-13〜§49-25**（決定の経緯・読んだ実物・実装・走行の実測・T25 の調べ・承認の後に番人が見つけた不備2件と直し） |
| 3 | `scripts/priority_rebuild/observe_diag.py` | `DEMAND_RANK_TF`・`_demand_rank_name`・`rank_demand_for_regime`・`merge_demand_into_ranking`・`add_demand_to_ranking`・`selftest_rank_demand`・`__main__` の `--add-demand` と `--selftest-rank-demand` の分岐。比べる相手＝既存の `rank_materials_for_regime`・`rank_separation`・`_regime_labels`・`_independent_step`・`_role_lineage_table`・`load_demand` |
| 4 | `scripts/priority_rebuild/engine_tuner_gen.py` | `ranked_materials`（需給の枝）・`_family_tf_from_col`（需給の枝）・`ranked_groups`（触っていないが挙動が変わる）・`_ranked_material_at`（説明2行だけ）・`selftest_rank_demand`・`main` の `--selftest-rank-demand` |
| 5 | `.claude/breaks/` | `b38_rank_demand_reader_gone.sh`・`b39_rank_demand_merge_gone.sh`・`b40_rank_demand_touch_indicator.sh`・`lib.sh` |
| 6 | `.claude/audits/m2d1_ranking_scan.py` | `assert_demand`（`--assert-demand`）・`diff_before`（`--diff-before`）・⑥b（需給3列の生の順位） |
| 7 | `.claude/ratchet/material_ranking.json` と同じ場所の `material_ranking.before_add_demand.json` | 足した後と、足す前（控え） |
| 8 | `.claude/ratchet/signal_families.json` の `extra_parts.demand` と `.claude/ratchet/indicator_switch.json` の `demand_on` | 需給の役割（sufficiency）と印 |

## 2. CC の自己申告（打ったコマンドと出力のそのまま・2026-09-07）

| # | 何を見るか | 打ったコマンド | 出力（そのまま） |
|---|---|---|---|
| 1 | ① 差分の口の自己検査 | `python3 scripts/priority_rebuild/observe_diag.py --selftest-rank-demand` | `T-f 需給を成績表に足す（差分の口）: ①直に呼んだ値と一致 ②需給の系統を持つ役割 ['sufficiency'] にだけ3列 ③指標の列は不変 ④先読み違いは止まる ／ 採点できた列 3 本 ／ ❌ 0 件`（3秒・rc=0） |
| 2 | ① 差分の走行 | `python3 scripts/priority_rebuild/observe_diag.py --rank-regime --add-demand data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv` | `足す前＝測れた列 6101 ／ 載った列 5981` → `★足した後＝測れた列 6104 ／ 載った列 5984（足した行 18 件・列 3 本）`／`経過時間＝読み込み 0.9秒 ／ 採点（ラベル作りを含む） 3.9秒 ／ 足す 0.1秒 ／ 書く 0.1秒`／被覆＝taker_ls・L-S比 `2021-04-01〜2026-06-30 / 対象期間の被覆 100.0%`・CVD `2024-03-01〜2026-06-30 / 対象期間の被覆 100.0%`／`⚠️ 重複のふるい（_dup_pairs・法則 C2・C3）は需給に未適用（設計書 §7 の補3）`（8秒） |
| 3 | ① 需給が順位に載ったか（完成の条件1） | `python3 .claude/audits/m2d1_ranking_scan.py --assert-demand` | `需給 3 列のうち成績表の順位に載っているのは 3 列: 載っている=['CVD', 'L-S比', 'taker_ls'] 載っていない=[]`（rc=0。走らせる前は rc=1） |
| 4 | ① 指標の列が不変か | `python3 .claude/audits/m2d1_ranking_scan.py --diff-before` | `需給以外の順位の中身: 一致 ／ 窓・行数・先読み・時間足・役割外の列: 一致`／`測れた列 6101 → 6104 ／ 載った列 5981 → 5984 ／ 省いた列 4 → 4`（rc=0） |
| 5 | ② 生成器の読む側の自己検査（完成の条件3） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest-rank-demand` | `T23-demand 需給の列を順位から読む: ①sufficiency に3列 ②印から外すと消える ③戻すと出る ④列名→(名前, 5m) ⑤location・env の組に混ざらない ／ ダメだった件 0`（3秒・rc=0） |
| 6 | ② 生成器の自己テスト全部 | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | T23 `location の並び 10482 本（降順）／ 1位 S-Rタッチ数(144,0.006)__15m（分離力 0.743）／ ★突き合わせ＝型の表の列 6105 本のうち順位に載っているのは 5981 本`／T32 `env「強さ」の1位＝KST×1d`／T33 `使う 141 種／使わない 116 種`／❌＝**T24②・T25・T26・T30 の4件**（6分32秒）。★T24②・T26・T30 は M2-E の既知。**T25 は下の §4 の6** |
| 7 | 直す前と後で結果が同じか（S2） | `python3 scripts/priority_rebuild/engine_tuner_exec.py --identity` | `[恒等検収まとめ] ✅ 全部一致`・md5 `7b01f51b5a9b29b3c05a7b340c203ba1`（2026-09-04 の S2 と同じ値・6秒） |
| 8 | 印（§4 の9の直しの後に取り直した値） | `python3 scripts/priority_rebuild/gen_signal_families.py --verify` ／ `python3 scripts/priority_rebuild/leak_causality_diag.py`（`pre_audit_check.py --run` の中で走った） | G2 rc=0・指紋 `0a6f1479a4a6574c…`（25.2秒）／H2 rc=0・指紋 `988d0c8d49e2b630…`（291.7秒）。直す前（14:33〜14:39）の値は G2 `b84181ca…`・H2 `cef08202…`＝`注記なし未来参照 0 件 / 打ち切り再現テストの食い違い 0 件` |
| 9 | 足すだけか | `git diff -U0 -- observe_diag.py engine_tuner_gen.py` の `-` で始まる行 | **0本**（既存の行を1行も消していない・書き換えていない） |
| 10 | 承認のとき機械が測ったもの（★§4 の9の直しの前のコード） | `bash .claude/hooks/approve_impl.sh .claude/state/acceptance.md`（まこさんが打った） | `b39 rc=1`・`b40 rc=1`・`b38 rc=1`（壊すと止まる）／`#1〜#3 済＝壊すと rc=1／条件のコマンド rc=0`／`impl_functions: 12 件を凍結`／`機械で照らせる 12件／照らせない 9件（手で書いた名前 5件／bash の判定 3件／設計書に書いた理由 1件）` |
| 11 | 監査に出す前のチェック（§4 の9の直しの後・2回目） | `python3 .claude/tools/pre_audit_check.py --run` → `--verify` | 10本 全部 rc=0（`gen_indicator_switch.py --write`・`gen_materials.py --write`・G2・H2・`gen_materials.py --verify`／`--selftest`・`gen_indicator_switch.py --verify`・`gen_exit_families.py --verify`・`engine_tuner_exec.py --selftest` 8.0秒・`observe_diag.py --selftest` 110.1秒）／`監査に出せます（チェックの1枚が新しく、全部 rc=0）`・指紋 `23724c9351dd2997…`。**1回目（直す前）は `engine_tuner_exec.py --selftest` と `observe_diag.py --selftest` が rc=1 だった**（§4 の9） |

**需給3列の、成績表の生の順位（⑥b の出力そのまま・sufficiency は 2,104本）**

| 役割 | ラベル | 先読み | 列 | 分離力 | 位置 |
|---|---|---|---|---|---|
| sufficiency | 強さ | 24 | CVD__5m | 0.484 | 208 位 |
| sufficiency | 強さ | 24 | taker_ls__5m | 0.493 | 662 位 |
| sufficiency | 強さ | 24 | L-S比__5m | 0.499 | 1944 位 |
| sufficiency | 強さ | 288 | taker_ls__5m | 0.466 | 396 位 |
| sufficiency | 強さ | 288 | L-S比__5m | 0.533 | 411 位 |
| sufficiency | 強さ | 288 | CVD__5m | 0.523 | 760 位 |
| sufficiency | 向き | 24 | L-S比__5m | 0.507 | 1645 位 |
| sufficiency | 向き | 24 | CVD__5m | 0.497 | 1923 位 |
| sufficiency | 向き | 24 | taker_ls__5m | 0.501 | 2060 位 |
| sufficiency | 向き | 288 | taker_ls__5m | 0.475 | 878 位 |
| sufficiency | 向き | 288 | L-S比__5m | 0.505 | 1893 位 |
| sufficiency | 向き | 288 | CVD__5m | 0.497 | 1992 位 |
| sufficiency | 大きさ | 24 | taker_ls__5m | 0.488 | 747 位 |
| sufficiency | 大きさ | 24 | CVD__5m | 0.505 | 1428 位 |
| sufficiency | 大きさ | 24 | L-S比__5m | 0.499 | 2035 位 |
| sufficiency | 大きさ | 288 | taker_ls__5m | 0.478 | 791 位 |
| sufficiency | 大きさ | 288 | CVD__5m | 0.502 | 1991 位 |
| sufficiency | 大きさ | 288 | L-S比__5m | 0.498 | 1992 位 |

## 3. 何を作ったか（設計書 §4 の A〜I・全部「足すだけ」）

| # | ファイル | 何を足したか |
|---|---|---|
| A | `observe_diag.py` | `rank_demand_for_regime`＝値決め窓で `load_demand` の3列を作り、列名を `名前__5m` にし、全走の本体と同じ関数（`_regime_labels`・`_independent_step`・`rank_separation`）で採点する。重複のふるい（`_dup_pairs`）は掛けない |
| B | 同 | `merge_demand_into_ranking(rank, r)`＝いまの成績表に足す。窓・先読み・時間足が違えば止める。役割は `_role_lineage_table` で系統「需給」を持つものだけ。|分離力−0.5| の降順に並べ直す。足す前後で需給以外の中身を照らし、変わっていれば止める |
| C | 同 | `add_demand_to_ranking`＋CLI `--rank-regime --add-demand`＝控えを書き → A → B → 書き戻す。被覆率と「重複のふるいは未適用」を印字し、`需給の被覆` を json に残す |
| D | 同 | `selftest_rank_demand`（T-f ①〜④）＋`--selftest-rank-demand` |
| E | `engine_tuner_gen.py` | `ranked_materials` に需給の枝（`iref.DEMAND_REF` に在れば `ex.demand_enabled` で見る）。`_family_tf_from_col` に需給の枝（参照表を通さず `(名前, 時間足)` を返す）。`_ranked_material_at` は説明2行だけ（需給は今までどおり飛ぶ） |
| F | 同 | `selftest_rank_demand`（T23-demand ①〜⑤）＋`--selftest-rank-demand` |
| G | `.claude/hooks/require_design_contract_before_run.sh` | 「確認のための走行」の旗に `--selftest-rank-demand` と `--add-demand` |
| H | `.claude/breaks/b38・b39・b40` | 壊すプログラム3本（承認のとき機械が走らせ、3本とも rc=1） |
| I | `.claude/audits/m2d1_ranking_scan.py` | `--assert-demand`・`--diff-before`・⑥b |

## 4. ★CC が塞げていないこと（正直に・9件）

| # | 中身 |
|---|---|
| 1 | **差分で足した分離力が、全走に需給を含めた場合と同じかは、全走（2時間17分）を走らせないと直接は比べられません。**代わりに T-f の①（同じ入力で `rank_separation` を直に呼んだ値と一致）で確かめています |
| 2 | **成績表の指標の列は json をそのまま読んで足しています。**指標の列が偽造されていても、この工事では見抜けません（足す前後で変わらないことだけを確かめる） |
| 3 | **需給を場面の判定の束に引く道は作っていません。**需給の役割は型の表で sufficiency で、場面の判定の束が順位から引くのは location と env だけです。需給を束に引くのは M2-E |
| 4 | **重複のふるい（`_dup_pairs`・法則 C2・C3）を需給に掛けていません。**需給が指標のどれか（CVD と OBV傾き など）と「実質 同じもの」でも落ちません。走行のたびに「未適用」と印字しています |
| 5 | **型の表の rule「時間足には展開しない」を「入口の条件の材料についての決まり」と読んだのは CC の解釈です。**成績表の列名 `__5m` については何も書いていません。別の読み方を採るなら、列名から `__5m` を外し、読む側で「時間足の無い列＝5m」と扱う形に直します（採点の中身は変わりません） |
| 6 | **生成器の自己テスト T25（静的検査 `lint_provenance`）が ❌ です。**原因は別セッションが M2-C で新設した `_check_extra_gate()` が見本の関数 `_thr_fixture("q70")` を呼んでいること（HEAD 650b452 にも同じ行が在り、この工事の前から ❌。`.claude/audits/m2d_lint_check.py` で実測）。この設計書は「足すだけ」で承認されているので直していません。next_step §6 の149番（直し方の案2つ・決めるのは まこさん） |
| 7 | **需給3列の分離力は全部 0.466〜0.533 で、0.5（分けられない）に近い値です。**上位15組には入りません。この数字は需給を単独の材料として先の値動きの性質と照らしたもので、束の中で効くかは M2-F〜H で測ります。CC は良し悪しを決めていません |
| 8 | **`must_use` の5件は CC が手で書いた名前です**（正本の一覧が無いため）。承認のプログラムは「機械で照らせない 9件」に数えています |
| 9 | **2回目の承認の後に、監査に出す前のチェック（`pre_audit_check.py --run`）が私のコードの不備を2件 見つけ、直しました。**①H2 の番人「並びの決まらない入れ物」＝`selftest_rank_demand`（生成器）と `merge_demand_into_ranking` で set を上から順に見ていた → `sorted` で並べてから回す形にした ②read-only 診断の番人＝`selftest_rank_demand`（observe_diag）が偽の需給ファイルを `to_csv` で書いていた → 検査6と同じ `write_text` にした。**直したのは今日 足した関数の中だけ**（凍結した `impl_functions` の中・既存の行は消していない・設計書は変えていない）。直した後に印（G2・H2）と出す前のチェックを取り直しました（§2 の8・11）。**★承認のときの壊すプログラムの測り（b38〜b40 rc=1）は、この直しの前のコードで測ったものです。**直しの後に壊すプログラムが今も止まるかは、監査自身で走らせて確かめてください（CC は Bash から `.claude/breaks/*.sh` を走らせられません） |

## 5. 監査への問い（2つ）

1. **① 需給3列が、指標と同じ物差しで成績表の順位に載っているか。**監査自身で、`material_ranking.json` と `material_ranking.before_add_demand.json` を比べ、需給以外の列（6,101本）の分離力と順位が1つも変わっていないこと、需給3列が sufficiency の18組に載っていること、を測ってください。**分離力が `rank_separation` を直に呼んだ値と一致するか**（式を書き写していないか）も、`rank_demand_for_regime` の実物を読んで確かめてください。値決め窓の外を1バーも使っていないか（`_assert_search_window_only`）も見てください。

2. **② 生成器が、順位から需給3列を読めるか。**監査自身で、`ranked_materials("sufficiency")` に需給3列が出ること、印（`demand_on`）から外すと消えて戻すと出ること、`ranked_groups("location")` と `ranked_groups("env")` に需給の組が混ざらないこと、を測ってください。**location の1位（S-Rタッチ数(144,0.006)__15m・0.743）が変わっていないこと**も見てください。

**この2つの答えが、結論（GO / NO-GO）です。**

## 6. 別枠の指摘（結論には効かせない）

承認の仕組み・設計書の形・記録の書き方・依頼書の書き方について気づいたことが在れば、この節に書いてください。**結論には効かせないでください。**ただし、それが①か②の達成を実際に妨げている場合は、§5 の答えの中で、どう妨げているかを実物で示してください。

**★§4 の6（T25）と 4（重複のふるい）と 7（分離力が 0.5 に近い）は、この工事の範囲の外です。**指摘は歓迎しますが、①②の判定には入れないでください。

## 7. 結果ファイル

`.claude/audits/2026-09-07_m2d_cp27_audit_report.md` に、①②の判定（実測つき）・Verdict（GO / NO-GO）・別枠の指摘、の順で書いてください。**監査が走らせたコマンドと出力を、そのまま貼ってください。**実装ファイル・設定ファイル・やることリストは変えないでください（測るためのプログラムを `.claude/audits/` に置くのは可）。

---

依頼書終わり。

## まこさん向け呼びかけ例文（新規セッション起動時）

```
監査してほしい
.claude/audits/inputs/2026-09-07_m2d_cp27_audit_request.md
```
