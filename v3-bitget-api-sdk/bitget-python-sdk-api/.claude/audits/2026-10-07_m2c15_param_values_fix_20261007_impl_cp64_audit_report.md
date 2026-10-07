# 監査結果 cp64 — CP64 — 監査 CP63 の修正1・4・6 を案 A で直す。M2-C-15（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_request.md`
- 依頼書のハッシュ値: 156ade13d32a9789acd8ab811cfcc26a1db06b93fd46bf641ac80951c6d7addd
- 監査の相手と版（依頼書に書いてあるもの）: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-fix-20261007.md` ／ ハッシュ値 ccc86b5472fea2eb970c7933580e2788145af1782444ab47138673068bfe284d
- 監査が照らしたハッシュ値: ccc86b5472fea2eb970c7933580e2788145af1782444ab47138673068bfe284d（`shasum -a 256` で測った。依頼書の値と一致する。この控えはコミット 85b7e1f で git に入り、`git diff 85b7e1f -- <控え>` の差は0行）
- 実施日: 2026-10-07

★監査の途中で HEAD が動いた。依頼書を作った時（16:45）の HEAD は a6f8167 で、実装は未コミットだった。監査の途中の 16:59 に実装が 85b7e1f でコミットされ、いまの HEAD は f38759b である。そのため「実装の前」は依頼書どおり a6f8167 に固定して照らした。


## 2. 監査対象の型宣言

- 対象の型: 混合型（コード型＋数値型）
- 判定根拠: 直した相手は、コード（engine_tuner_gen.py・observe_diag.py・壊すプログラム b140・b141）と、範囲の数字の設定（search_limits.json・observe_config.json）の両方である。
- 使用観点: 依頼書の固有の問い Q1〜Q11 だけを使う（一般の観点①〜⑦は依頼書のとおり該当なし）。
- 証跡要求: sha256 あり（設計書の控え）・grep の数え上げあり（直す前の文字が1か所か）・行番号つきの逐語引用あり。


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

設計書の 4-20 に実装の指示は16件ある。番号・対象のファイル・直す箇所は、依頼書の表と同じである。

- 番号1〜2 は observe_diag.py、3〜4 は observe_config.json、5〜12 は search_limits.json、13〜14 は engine_tuner_gen.py である。
- 番号15〜16 は、新しく作るファイル b140・b141 である。

### 当てた記録（applied_fixes.json の名前 design:m2c15-param-values-fix-20261007）

applied_fixes.json の 2735〜2845行に、名前 `design:m2c15-param-values-fix-20261007` の行が16件ある（`grep -c` で16）。

- num は1〜16 で、file は上の表と1件ずつ同じである。
- 時刻は全部 "2026-10-07T11:43:47"、how は全部 "当てた" である。「もう当て終わっていた」の行は無い。

### 必読に要るファイル（道具が設計書と実装から拾った）

依頼書の表と同じ10件を確かめた。直す相手の6本（engine_tuner_gen.py・observe_config.json・observe_diag.py・search_limits.json・b140・b141）は全部 実在する。material_ranking.json は、依頼書のとおり必読に入れていない（この工事で作り直していない成績表）。ただし Q8 の数え上げのために、読むだけで開いた。


## 4. 所見

### 一般の観点

該当なし（依頼書のとおり）

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**YES。1文字も違わない。**

- 確かめ方: 設計書 4-20 から、当てる道具（apply_audit_fix.py）と同じ規則で直す前の文字と直した後の文字を切り出した。`git show a6f8167:<パス>` の中身に、この工事の16件を番号の順に当てた。続けて、後の工事 m2c15-rci-pivot-sources-20261007 の5件も当て、いまのファイルと比べた。
- 結果: 直す前の文字は21件とも、当てる前の中身にちょうど1か所あった。当てた結果といまのファイルは、6つの対象ファイルで全バイト同じだった（observe_diag.py＝562310 バイト・observe_config.json＝31100 バイト・search_limits.json＝35580 バイト・engine_tuner_gen.py＝572575 バイト・b140＝1473 バイト・b141＝1524 バイト。`wc -c` と同じ）。
- 比べ方が違いを見分けられることの確かめ: 基にする版を実装を含む版に替えて同じことをすると、observe_diag.py は 475066 バイト目、engine_tuner_gen.py は 32248 バイト目で違いが出た。

修正の番号＝なし

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**YES。どの実装の指示にも当たらない行は0行である。**

- Q1 で、2つの工事の指示を重ねて当てた結果が、いまのファイルと全バイト同じだった。
- `git log -- <対象6本>` では、a6f8167 の後に対象を触ったコミットは 85b7e1f だけである。ほかの変更は混ざっていない。
- 足した行に乱数は0件だった（恒久67番に当たらない）。

修正の番号＝なし

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**YES。** 16件が、番号・対象のファイルとも1件ずつ合う。「もう当て終わっていた」の行は無い（3 の当てた記録のとおり）。

修正の番号＝なし

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（問い2）（優先度 A）

**YES。2件とも満たしている。**

- **要望1（監査 CP63 の修正を全部 直す）:** 満たしている。
  - 修正1・4・6 は、この工事で当てた（engine_tuner_gen.py:469「`if not param_in_range(family, m["param"], ranges)[0]:`」・search_limits.json:60〜62・141・145）。
  - 修正2・5・7 は、設計書の 3-1 の5番のとおり、この工事の設計書で受けている。
  - 修正3 は a6f8167 で直っている。require_design_check_before_approval.py「`if l.strip().startswith("❌ ") and not re.match(r"❌ \d+ 件", l.strip())]`」（re は63行で読み込み済み）。
  - 修正13 は a6f8167 で直っている。gen_acceptance.py「`… and (not old or old not in src_text or old in it["中身"]):`」（old は696行で定義済み）。
  - 修正8 は observe_diag.py:7121〜7123、修正9 は r3_draft_build.py:136、修正10 は gen_materials.py:1581、修正11 は materials.md:100、修正12 は engine_tuner_gen.py:240 に入っている。
  - Minor-5・6 は、監査 CP63 が修正の指示を書いていないので、設計書の 3-1 の6番で外している。
- **要望2（修正1・4・6 を案 A で直す）:** 満たしている。範囲を作る道具を元から直している（r3_draft_build.py:76〜78 の AXIS_MAP「`"TSI": [1, 0, 2]`」と apply_param_rule.py）。範囲が変わったのは、TSI の3種・StochRSI の2種・ALMA・MCGD・SSF・VIDYA の9種と T3 である（`git diff a6f8167 -- search_limits.json` の差のとおり）。

修正の番号＝なし

### Q8 — 段の候補は、範囲の外の列を全部の呼ぶ所で外すか。外したことで、通る案が変わっていないか（優先度 A）

**6か所とも外れる。軸ごとの照らしも正しい。ただし「通る案は変わらない」は、仕組みの上で成り立たない（Major）。**

- **6か所とも外れる理由:** 範囲の照らしは _group_usable_col の中にある（engine_tuner_gen.py:469「`if not param_in_range(family, m["param"], ranges)[0]:`」・次の470行は `return False`）。呼ぶ6か所（2347・2899・3053・3100・3140・6710行）は、どれもこの関数を通る。
- **数字が2つ以上の列:** param_in_range（309〜324行）は、数字の個数が軸の数と違えば False を返す。合っていれば、軸ごとに下限・上限と整数かを照らす。MACDヒスト%(12,26,9) は、軸1 3〜12・軸2 10〜26・軸3 1〜9 の各軸に照らされる。
- **問題1＝範囲の中の列まで、組ごと候補から消える。** 照らすのは、組（種類×時間足）の代表の列＝並びの1本目だけである。ranked_groups は組の列の1本目を代表にする（engine_tuner_gen.py:2320「`rows.append((abs(med - 0.5), fam, tf, lab, hor, med, len(items), items[0][0]))`」・2322行「`out = [(fam, tf, lab, hor, med, n, col) for _s, fam, tf, lab, hor, med, n, col in rows]`」）。成績表 material_ranking.json を読んで数えると、ROC の組は84あり、代表の列が範囲 9〜24 の外の組は36である（sufficiency 28・trigger 8）。この36組は、どれも同じ組の中に範囲の中の列（ROC9・ROC12・ROC24）がある。それでも組ごと候補から消える。
- **問題2＝範囲の外の組より後ろの順位は、別の組を引く。** _ranked_material_at（2347行のあと `n += 1`）と build_stage_candidates（`rank += 1`）は、使えない組を数えない。そのため、範囲の外の組より後ろの順位は、直す前より後ろの組を引く。設計書 4-13 の2「止まる所が前に来るだけで、通る案は変わらない見込み」は、仕組みの上で成り立たない。実際の案がいくつ変わるかは、データ不足（理由＝段の本走は M2-F で、この監査では走らせていない）。
- **実装は設計書のとおりである。** 設計書の 4-3「列の数字が範囲の外なら使わない」のとおりに作られている。外れているのは、設計書が「見込み・走らせて確かめていない」と書いた効果の説明である。だから問い1 の NO の根拠にせず、Major とした。直し方は、組の代表の選び方を変えるか（A）、このまま受け入れて説明を実物に合わせるか（B）の2つがあり、まこさんが決める。
- **修正2 を走らせる前の注意:** 修正2 のコマンド（gen_acceptance.py --work m2c15-param-values-fix-20261007 --write）は `.claude/state/acceptance.md` に書く。いまの acceptance.md には、別の工事 g2-sentinel-material-pick-20261007 の設計書が入っている（`ARC iter="g2-sentinel-material-pick-20261007"`）。走らせると、その設計書を上書きする。

修正の番号＝修正1・修正2

### Q9 — TSI の3種の範囲は、名前の軸に正しく当たっているか。範囲を作る道具の直しで、ほかの種類の範囲が誤って変わっていないか（優先度 A）

**AXIS_MAP の [1, 0, 2] は正しい。修正対応表で9行だけ変わったかは、データ不足である。**

- **ライブラリの実物:** /usr/local/lib/python3.13/site-packages/pandas_ta_classic/momentum/tsi.py（.venv の版と差0）。46行「`slow_ema = ema(close=diff, length=slow, **kwargs)`」・49行「`fast_slow_ema = ema(close=slow_ema, length=fast, **kwargs)`」。slow を先に、fast を後に掛ける。
- **名前の軸:** observe_diag.py:1085〜1086「`_pta6.tsi(close=d.close, fast=f_, slow=s_, signal=g_)`」。
- **当て方:** 名前の軸0（fast＝後にならす短い方）は資料の軸1（second）に、名前の軸1（slow）は資料の軸0（first）に当たる。修正対応表の TSI の行は「7〜26・4〜13・7〜12」（資料の軸の順）で、[1,0,2] で並べ替えると search_limits.json:60 の「4〜13・7〜26・7〜12」と同じになる。正しい。
- **9行だけ変わったか:** 直す前の修正対応表は git の外（.gitignore の `.claude/state/*`）にある。worklog §3 が書いた控えの before_r4/ は、find で0件だった。残っている indicator_params_by_strategy.before_153.md は 2026-10-04 の版で、差は301行あり、ほかの工事の差が混ざる。そのため、表の9行だけが変わったことは直接は確かめられない（データ不足・理由＝直す前の表が残っていない）。
- **間接の確かめ:** 表から写した search_limits.json の範囲で、a6f8167 から変わったのは、上の9種と T3（広げる決まり）だけである（RCI は後の工事の分）。_material_params_pending から外れたのは、StochRSI%K・%D・MCGD・SSF・VIDYA の5件だけである（後の工事の RCI と前期間pivot の3件を除く）。

修正の番号＝なし

### Q10 — VIDYA と T3 の範囲は、カタログの列の数字を全部 含むか。番人⑬を広げたことで、見逃す形が残っていないか（優先度 A）

**含む。見逃す種類も、いまは残っていない。**

- **カタログの数字:** VIDYA と T3 は material_params に無いので、カタログは sma_periods [20,50,200] から作られる（observe_diag.py:1574〜1577）。VIDYA の範囲 14〜200 と T3 の範囲 8〜200 は、20・50・200 を全部 含む。ほかの7種もカタログの数字を含む（TSI(12,26,9) は軸ごとに範囲の中・StochRSI14・ALMA9/10・MCGD10・SSF10 も範囲の中）。
- **⑬の飛ばし:** 設定の範囲が無い種類は、material_ranges（engine_tuner_gen.py:294〜303）がカタログの最小〜最大を範囲に使う。だからカタログの数字は必ず範囲の中にある。指標ごとの一覧の種類は、observe_diag.py:7122〜7123 が止める。⑬の飛ばしで見逃す形は、いまは無い。
- **広げる決まり（r3_draft_build.py:213〜225）:** 道具の記録 r4_names.json の「広げた範囲」は2件だけだった（「ROC の軸1 … 9〜24 に広げる」「close vs T3% の軸1 … 8〜200 に広げる」）。設計書 4-0 の⑥のとおり、ROC・T3 の2軸だけに効いている。
- **参考（修正の指示は書かない）:** r3_draft_build.py の LIM_NOTE（380〜392行）には、実装12 で足した注記の文が無い。r4_draft_build.py:113〜116 が置き換えで足している。r3 の書き出しを単独で走らせ直すと、注記は元の文に戻る。check_indicator_sources.py は範囲の塊しか比べないので、この食い違いは検出されない。

修正の番号＝なし

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**YES。** 承認した版の控えと監査の相手は同じファイルで、ハッシュ値も同じである（1 のとおり）。`.claude/state/acceptance.md` は、依頼書のとおり比べていない。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**要件の抜けは無い。実装の指示に対応する要件の行が無いものが1件ある（Minor）。**

- 要件と指示の対応: F-4 は指示5、F-6 は指示1・10・11・12、F-1 は指示2・13・14 が満たす。F-0 の結果（範囲）は指示4・6〜9 に写っている。F-0 の道具の直しそのものは、やることの表の「順番」の1のとおり、承認の前に git の外で済ませた扱いである。G-1・G-2 は当てた後の手順で、4-20 の対象ではない。
- 指示3（material_keep に MACDヒスト%(12,26,9) が入る。元は監査 CP63 の修正9）は、設計書の 4-9 には書いてある（m2c15-param-values-fix-20261007.md:388）。しかし、やることの表の一覧（F-0〜G-2）に対応する行が無い。
- 修正4 のコマンドを走らせる前の注意は、Q8 の修正2 と同じである（いまの acceptance.md に入っている別の工事の設計書を上書きする）。

修正の番号＝修正3・修正4

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**YES。2行とも成り立つ。**

- 完成の条件の2行（設計書 7-6 の ACCEPT_TABLE の1行目 F-1・2行目 F-6）は、どちらも同じコマンド `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` で測る。
- 監査の CC が SDK のフォルダで走らせた結果＝「K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ 0 件」・終わりの番号0・21.53秒（`/usr/bin/time -p` の real）。
- 読んで分かる範囲でも、⑭は ROC3 が範囲 9〜24 の外、ROC12 が中なので、狙いどおりに働く作りである。
- ★Plan エージェントが走らせたときは、block_repeat_kind.sh に止められた（このセッションの Stop hook の差し戻しが2回あったため）。監査の CC が、このセッションの lessons.md と diagnosis.md を書いて止めを解き、試しの道具で止める hook 0本を確かめてから走らせた。

修正の番号＝なし

### Q11 — 壊すプログラム2本は、直しを外したときだけ落ちるか。監査 CP63 のほかの修正の扱いは正しいか（優先度 B）

**壊す対象はどちらもちょうど1か所で、宣言した文で落ちる作りである。CP63 のほかの修正の扱いも正しい。ただし2本とも走らせていない。**

- **b140:** 壊す行「`    if not param_in_range(family, m["param"], ranges)[0]:`」は `grep -c -F` で1か所（engine_tuner_gen.py:469・次の行は `        return False`）。落ちたときの文「修正1:」を出すのは、observe_diag.py の 7134行と 7136行だけである。
- **b141:** 壊す行「`    "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}],`」は1か所（search_limits.json:141）。上限を34に戻すと、⑬（observe_diag.py:7127）が「P-2: close vs T3%50 …」「P-2: close vs T3%200 …」を出す。宣言の「❌ P-2: close vs T3%」と合う。
- **走らせていない理由:** 2本とも、本物のファイルを lib.sh の guard で一時的に書き替える作りである。依頼書の禁止（本物のファイルを書き替えない）に当たるので走らせず、中身を読んで確かめただけである。
- **CP63 のほかの修正:** 修正2・5・7・3・13 の扱いは、Q7 のとおり正しい。

修正の番号＝なし


## 5. 外部検索

該当なし（依頼書のとおり）


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

この工事の6本の対象ファイルとは重ならない。Q1・Q2 は6本だけで取っているので、結論に影響は無い。

ただし、自己申告の書き方はいまの状態と合っていない。

- `.claude/tools/` の4本（check_indicator_sources.py・gen_acceptance.py・gen_audit_docs.py・pre_audit_check.py）は、430641c でコミット済みである。
- gen_signal_families.py は、85b7e1f（g2-sentinel の工事）でコミット済みである。
- いま作業中の変更として残っているのは、hook の2本と e38_logics.backup だけで、どれも未追跡（??）である。
- 依頼書を作った（16:45）後の 16:59 にコミットされ、依頼書の「HEAD＝a6f8167・実装は未コミット」も古くなった。監査 CP63 の Process-2 と同じ形のずれである。1つのファイルの文字に落とせないので、修正の指示は書いていない。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝Q1〜Q3 で、1文字の違い・設計書に無い変更・当てた記録の抜けは0件。Q6 の完成の条件は2行とも成り立つ。Q8 の Major は、設計書が「見込み・走らせていない」と書いた効果の説明が外れている所で、実装は設計書の 4-3 のとおり。Q4・Q9・Q10・Q11 で設計書と違う所は無い）
- 問い2 ＝ YES（根拠＝Q7 のとおり、要望1・2 とも満たしている）

### 結論と件数

- 結論＝GO
- Critical＝0
- Major＝2
- Minor＝2
- Process＝0


## 8. 修正の指示

### Critical

なし

### Major

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-fix-20261007/やることの表.md
直す箇所: 102行
直す前の文字:
~~~
| 目的の照合（purpose_check.md）の条件の書き方 | 事実だけを書く。パラメータ＝「TSI・VIDYA・T3 ほかの探す範囲が変わる（4-0 の③の表）。段の候補は範囲の外の列を使わない」。閾値＝「今のまま」。時間足＝「今のまま」 | 前の工事の 3-2 |
~~~
足す文字:
~~~

| 監査 CP64 の Q8＝段の候補の絞り（_group_usable_col）は、種類×時間足の組の代表の列（ranked_groups の1本目）だけを照らす。成績表の sufficiency・trigger の ROC の組84のうち36組は代表の列が ROC3 か ROC6 で、36組とも同じ組に範囲の中の列（ROC9・ROC12・ROC24）が在るが、組ごと候補から消える。また _ranked_material_at・build_stage_candidates の順位の数え方から外れた組が抜けるので、範囲の外の組より後ろの順位は直す前と違う組を引く（4-13 の2「通る案は変わらない見込み」は成り立たない） | 未決（A＝組の中で範囲の中の最初の列を代表にする実装の指示を足す／B＝このままとし、成績表を作り直す M2-D-8 まで受け入れ、4-13 の2と 4-19 の文を実物の動きに合わせる） | 監査 CP64 の Q8 |
~~~
根拠の抜き書き: engine_tuner_gen.py:2322「out = [(fam, tf, lab, hor, med, n, col) for _s, fam, tf, lab, hor, med, n, col in rows]」
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
python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-fix-20261007 --write
~~~
根拠の抜き書き: m2c15-param-values-fix-20261007.md:13「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-fix-20261007 --write`。」（監査は走らせていない＝本物を書き替えるため・秒数なし）
状態: 未決

### Minor

#### 修正 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-fix-20261007/やることの表.md
直す箇所: 15行
直す前の文字:
~~~
| F-1 | 修正1（Critical）＝段の候補を作る所（engine_tuner_gen.py の _group_usable_col）が、成績表の列の数字が範囲の外なら使わない形にする。説明の文（_mat_from_col の「範囲を狭めていない」）を事実に合わせる。軽い口に⑭（範囲の外の列を使わない・範囲の中の列は使う）を足す | 監査 CP63 の修正1・Q11・まこさん「全部直す」 |
~~~
足す文字:
~~~

| F-9 | 監査 CP63 の修正9（r3_draft_build.py の正規表現）の結果を写す＝残す名前（observe_config.json の material_keep）の「採用中の戦略と確認のレシピ」に、確認のレシピの MACDヒスト%(12,26,9) が入る（カタログの列は変わらない） | 監査 CP63 の修正9・設計書 4-9 |
~~~
根拠の抜き書き: m2c15-param-values-fix-20261007.md:388「**observe_config.json で変えるもの。**_material_params_pending（値を埋めずに並べる種類）と material_keep（残す名前＝監査の修正9 で正規表現を直したので、確認のレシピの MACDヒスト%(12,26,9) が入る。カタログの列は変わらない）。」
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
python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-fix-20261007 --write
~~~
根拠の抜き書き: m2c15-param-values-fix-20261007.md:13「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-fix-20261007 --write`。」（監査は走らせていない＝本物を書き替えるため・秒数なし）
状態: 未決


## 9. CC プロセス欠陥対策

### Process

なし


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

**開いたファイル（全部 読むだけ）**

- 依頼書（全454行・監査の CC と Plan エージェントの両方）
- 設計書の控え m2c15-param-values-fix-20261007.md（1〜1215行の全文・Plan エージェント）／13行・213行・388行・970〜990行（監査の CC）
- やることの表.md（全文・Plan エージェント）／15行・102行（監査の CC）
- 後の工事 m2c15-rci-pivot-sources-20261007 の設計書（420〜559行）
- applied_fixes.json（2735〜2845行）
- 監査 CP63 の結果ファイル（59〜378行）
- engine_tuner_gen.py（225〜474行・1365〜1461行・2296〜2352行・2817〜3145行の該当部分・6690〜6715行）
- observe_diag.py（1085〜1091行・1500〜1600行・7011〜7145行）
- search_limits.json（44〜160行）
- observe_config.json（101〜300行の該当部分）
- r3_draft_build.py（56〜100行・128〜136行・180〜240行・378〜395行）
- indicator_params_by_strategy.md（1〜17行・30〜45行・130〜150行）
- pandas_ta_classic/momentum/tsi.py（1〜90行）
- b140・b141（全文）・lib.sh（1〜80行）
- session_worklog_20261007.md（1〜105行）
- apply_audit_fix.py と gen_audit_docs.py の item_fields（切り出しの規則）
- hook 3本の判定の部分
- material_ranking.json（Q8 の数え上げ）

**読まなかった必読（正直に書く）**

- cat_requirements.md・engine_tuner_requirements.md・engine_tuner_milestones.md・engine_tuner_milestones2.md の4本は読んでいない。結論は、実物の照合だけで決まる問い（Q1〜Q11）で出している。
- apply_param_rule.py の 250〜300行は開いていない。Q9 は、その出力（修正対応表と search_limits.json）で照らした。

**走らせたコマンドと結果と秒数**

- `shasum -a 256`（設計書の控え）＝一致・1秒未満
- `git log` ／ `git show` ／ `git diff` ／ `git status`＝各1秒未満
- awk で当てて比べる照合を3回（HEAD で比べた1回・違いを見分けられるかの試し1回・a6f8167 で比べた1回＝全部同じ）＝各数秒（秒数は測っていない）
- awk で成績表の ROC の組を数えた（84・36・36）＝数秒
- `grep -c -F` で、壊す対象と修正の直す前の文字が1か所かを確かめた＝全部1
- `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`（SDK のフォルダ・監査の CC）＝「❌ 0 件」・終わりの番号0・real 21.53秒

**hook に止められたもの（Plan エージェント・止めた文のまま）**

- `python3 -B -` と `python3 -B -c "print(1)"`＝require_design_contract_before_run.sh「🔒 [設計↔実装ゲート] 走らせる .py を確定できないコマンドです（2026-09-03・監査 cp14 の B-4）。」
- perl で当てる照合・`L=$(grep …)` の形・`paste` を使う形・`python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`＝block_repeat_kind.sh「🔒 [同じ種類の失敗を2回] このセッションで、同じ種類の失敗を2回 起こしています。…種類: enforce_next_step_tidy.sh [next_step の形・Stop hook]」
- `od` と `for` の繰り返しを含むコマンド＝require_acceptance_before_impl.sh（土台ゲート・Bash）
- ★--selftest-catalog は、監査の CC が止めを解いてから走らせた（Q6）。

**走らせなかったもの**

- b140・b141＝本物のファイルを guard で一時的に書き替える作りなので、依頼書の禁止に当たる。
- gen_acceptance.py --write（修正2・4）＝本物の設計書を書き替える。いまの acceptance.md は別の工事の設計書である。


## 11. 本物のファイルを書き替えていないこと

`git status --short --untracked-files=no` の出力は0行である（追跡中のファイルの変更 M は0件）。

`git status --short` の未追跡（??）は176行で、この監査で足したのは次の1行だけである（ほかは監査の前から在る、過去の監査の作業場・控え・ログ）。

```
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp64_work/
```

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_request.md request_sha256=156ade13d32a9789acd8ab811cfcc26a1db06b93fd46bf641ac80951c6d7addd -->
