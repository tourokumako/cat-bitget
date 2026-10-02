<!-- gen_audit_docs request-design kind=impl design_sha256=4067f16f7c3eb1233f2b604fa48a1cc5bebbbc8d08bc7a4248e5b4be8d5df033 src_sha256=f75c1581a33aba83bc7f519889b91a8bac76084af2e79d073d509fc6b9df57ff body_sha256=b7d60a1abdd814a51ffe2c661d9a668cabd4b1e615e8f5257b5162b2f1820e8e -->
<!-- 項目: メタ -->
日付: 2026-10-02
task: m2f_label_callers_20261002_impl
cp: cp59
題: CP59 — 観察の道具と測る道具を、札の部品 regime_label.py を呼ぶ形に切り替え、札の版の名前を順位表・落ちた候補・成績表に書く＝14a の工事 B（実装の監査）
依頼者: CC（起案者）
監査区分: 実装の監査
監査対象タスク: M2-F-6d・M2-F-5／設計書 m2f-label-callers-20261002
監査の相手: .claude/state/acceptance.md
売買に触るか: はい

<!-- 項目: 作業場の指示 -->
**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp59_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q13）です。

<!-- 項目: 結論を決める問い -->
- **問い1**＝設計書の実装の指示（30 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q13 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

- **問い2**＝この工事の後の実装が、下に並べた まこさんの要望（4 件）を満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。1つでも満たしていなければ NO（Q7 で照らす）。
  1. 目的：札が不適切だと分かったとき、直しやすい状態にする。工事 B が受け持つのは、札を作る場所を1つにすることと、どの版の札で選んだかを成績表の側に残すこと
  2. 札を作る場所を1つにする。観察の道具の中にある式を、⑪タブの道具と成績表の道具が別々に呼ぶ形をやめる（⑪タブの道具の切り替えは工事 C）
  3. どの版の札で作った成績表かを、成績表の側に残す。順位表と落ちた候補のファイルに、札の版の名前を書く
  4. 札の数字は設定ファイルに置き、値を書き替えて走らせ直せば札を作り直せる（工事 A で作った設定を、観察の道具と測る道具も読む）

<!-- 項目: 結論の決め方 -->
- **GO**＝問い1 と 問い2 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 と 問い2 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 と 問い2 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

<!-- 項目: この監査の前提 -->
1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-callers-20261002/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

<!-- 項目: 経緯 -->
1. **この工事は何のためか**＝札（正解ラベル）が正しいかは、最後に M2-L で入口と出口を固定して売買し、net を見るまで分からない。外れていたら、札を直して段1から並べ直す。だから札は、売買の結果を見て不適切だと分かったときに、直しやすい構造にする（2026-09-28 まこさん決定・やることリスト M2-F-6d の注意）
   直しやすい構造のうち、工事 B が受け持つのは2つ。①札を作る場所を1つにする（観察の道具と測る道具が、それぞれの式で札を作っていると、札を直したときに片方だけ変わる）②どの版の札で選んだかを、順位表・落ちた候補・成績表の側に残す（売買の結果を見て札を疑うときに、どの札で選んだ束かをたどれる）。あわせて、役割ごとの札のときは役割ごとに測り、段ごとに役割ごとに上位を残す（OK された表の L-6・worklog 20260928 §51 の1）。工事 A は札を作る部品と設定を作った。⑪タブは工事 C
2. **この工事は何か**＝M2 は、4つの場面（レンジ・上げ・下げ・スパイク）の判定を、全部の戦略のために組む段です。組んだ判定の良し悪しは、答え合わせに使う札（そのバーが後から見て実際にレンジだったかの答え）と照らして測ります。工事 A で、札を作る部品 regime_label.py と設定 recipes/regime_label.json を作りました。しかし、観察の道具（observe_diag.py の _regime_labels）と測る道具（regime_r9_diag.py の _labels_for）は、まだ自分の式と search_limits.json の本数で札を作っています。札を直しても、片方だけが変わる形のままです。この工事 B は、2つの道具を部品を呼ぶ形に切り替え、どの版の札で作ったかを順位表・落ちた候補・成績表に書き、役割ごとの札のときは役割ごとに上位を残すようにします。採点に使う版は er_median のままなので、札・順位表・成績表の数字は変わりません。⑪タブは工事 C です。（やることの番号 M2-F-6d・M2-F-5）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-F｜段ごとに測って並べ、上位を次の段へ渡す（段1〜段4）＝1本ずつの成績と順位を出す → M2-F-6d｜案B の4＝直す（M2-F-6c で変えると決まったときだけ）＝正解の作り方と測る道具を直し、指標の成績表を作り直す → M2-F-5｜実走＝段1 の束を数本 測り、3つの割合の表・順位表・落ちた候補の理由が5つの場面とも出ることを確かめる → この工事

<!-- 項目: 着手前必読 -->
**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `.claude/state/acceptance.md` — 監査の相手（設計書・プログラムが作った）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.01.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
4. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2f-label-callers-20261002 の行）
5. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-callers-20261002/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
6. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900・単月判定・通算でない）と全体戦略（§1.2・§1.2.1）、ハード制約（§4.6＝H2 未来参照なし・H6 価格非依存ほか）。この工事が目標と制約に沿っているかを照らす
7. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-103） — engine_tuner の目的と、作ってはいけないもの（乱数ほか）
8. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:95-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
9. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:3-46・:498-619・:1342-1392・:2021-2368） — M2 のミッションと作っている物・M2 の一覧（§0-0）・正解の作り方を決めた段（M2-A）・この工事が入っているフロー（M2-F と M2-F-6d の行）
10. `SDK/.claude/ratchet/m2_todo.json`（:1155-1170） — M2-F-6d の注意＝札の構造の文の原文（札を作る場所を1つにする・どの版の札で作った成績表かを残す）。Q8・Q10 で照らす
11. `.claude/state/session_worklog_20260928.md`（:1402-1439） — §50・§51＝役割ごとに測って、段ごとに役割ごとに10本ずつ残す（§51 の1）・成績表にも札の版を書く理由（§51 の2）。Q11 で照らす
12. `SDK/scripts/priority_rebuild/regime_r9_diag.py`（全文） — 測る道具。札を部品から受け取る（_labels_for）・列の名前・役割ごとの並べ（rank_key・rank_rows）・札の版を書く（write_outputs）・差し戻しの止め（run_sweep）・自己検査⑤⑫⑬
13. `SDK/scripts/priority_rebuild/observe_diag.py`（:108-120・:5786-5850・:6071-6125・:6266-6315） — 観察の道具。部品の読み込み・先を見る本数と札（_regime_horizons・_regime_labels）・成績表の書き出しに札の版（_insp_regime_rank・add_demand_to_ranking）
14. `SDK/scripts/priority_rebuild/regime_label.py`（全文） — 札の部品（工事 A で作った）。呼ぶ側の口（keys・labels_for_key・labels_at_bars・bars_keys・version_tag・groups）と、足した自己検査 T6
15. `SDK/scripts/priority_rebuild/recipes/regime_label.json`（全文） — 札の設定。採点に使う版（er_median）と、版2 の使う値（空）。Q8・Q11 で書き替える相手
16. `SDK/scripts/priority_rebuild/engine_tuner_gen.py`（:1340-1355） — 成績表を読む側 load_material_ranking。成績表に札の版の欄を足しても読めるか（Q10）
17. `.claude/breaks/b122_obs_formula_copied.sh` — 壊すプログラム。観察の道具に札の式を書き写すと、自己検査 T6 が落ちるか（Q12）
18. `.claude/breaks/b123_label_tag_dropped.sh` — 壊すプログラム。順位表に札の版を書かないと、自己検査⑬が落ちるか（Q12）
19. `.claude/breaks/b124_role_keep_off.sh` — 壊すプログラム。役割ごとに残さないと、自己検査⑫が落ちるか（Q12）

<!-- 項目: 大目的の注記 -->
⚠️ 本監査スコープ = 設計書 `m2f-label-callers-20261002` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。あわせて、まこさんの要望を、この工事の後の実装が満たしているか（問い2・Q7）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2f-label-callers-20261002` の中身です。

<!-- 項目: 事実データ 名前=設計書の実装の指示の一覧（4-20・当てる道具が当てる相手） -->
| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 11〜14行（<モジュール直下>） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 49行（<モジュール直下>） | 足す文字 |
| 3 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 94〜104行（rank_key） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 107〜127行（rank_rows） | 直した後の文字 |
| 5 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 139行（write_outputs） | 足す文字 |
| 6 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 176〜184行（_labels_for） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 203〜208行（measure） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 534行（run_stage） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 588行（run_sweep） | 直した後の文字 |
| 10 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 639行（run_sweep） | 直した後の文字 |
| 11 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 969行（main） | 直した後の文字 |
| 12 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 780行（selftest） | 足す文字 |
| 13 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 805行（selftest） | 足す文字 |
| 14 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 861行（selftest） | 直した後の文字 |
| 15 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 556行（run_sweep） | 直した後の文字 |
| 16 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 856〜859行（selftest） | 直した後の文字 |
| 17 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 860行（selftest） | 直した後の文字 |
| 18 | `SDK/scripts/priority_rebuild/observe_diag.py` | 115行（<モジュール直下>） | 足す文字 |
| 19 | `SDK/scripts/priority_rebuild/observe_diag.py` | 5791〜5792行（<モジュール直下>） | 直した後の文字 |
| 20 | `SDK/scripts/priority_rebuild/observe_diag.py` | 5806〜5814行（_regime_horizons） | 直した後の文字 |
| 21 | `SDK/scripts/priority_rebuild/observe_diag.py` | 5831〜5848行（_regime_labels） | 直した後の文字 |
| 22 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6090行（_insp_regime_rank） | 直した後の文字 |
| 23 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6119行（_insp_regime_rank） | 足す文字 |
| 24 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6307行（add_demand_to_ranking） | 足す文字 |
| 25 | `SDK/scripts/priority_rebuild/regime_label.py` | 25行（<モジュール直下>） | 直した後の文字 |
| 26 | `SDK/scripts/priority_rebuild/regime_label.py` | 340行（selftest） | 直した後の文字 |
| 27 | `SDK/scripts/priority_rebuild/regime_label.py` | 380行（selftest） | 直した後の文字 |
| 28 | `.claude/breaks/b122_obs_formula_copied.sh` | なし（新しいファイル） | 直した後の文字 |
| 29 | `.claude/breaks/b123_label_tag_dropped.sh` | なし（新しいファイル） | 直した後の文字 |
| 30 | `.claude/breaks/b124_role_keep_off.sh` | なし（新しいファイル） | 直した後の文字 |

<!-- 項目: 事実データ 名前=当てた記録（applied_fixes.json の名前 design:m2f-label-callers-20261002） -->
| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 2 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 3 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 4 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 5 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 6 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 7 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 8 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 9 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 10 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 11 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 12 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 13 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 14 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 15 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 16 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 17 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 18 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 19 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 20 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 21 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 22 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 23 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 24 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 25 | `SDK/scripts/priority_rebuild/regime_label.py` | 当てた | 2026-10-02T08:29:46 |
| 26 | `SDK/scripts/priority_rebuild/regime_label.py` | 当てた | 2026-10-02T08:29:46 |
| 27 | `SDK/scripts/priority_rebuild/regime_label.py` | 当てた | 2026-10-02T08:29:46 |
| 28 | `.claude/breaks/b122_obs_formula_copied.sh` | 当てた | 2026-10-02T08:29:46 |
| 29 | `.claude/breaks/b123_label_tag_dropped.sh` | 当てた | 2026-10-02T08:29:46 |
| 30 | `.claude/breaks/b124_role_keep_off.sh` | 当てた | 2026-10-02T08:29:46 |

<!-- 項目: 事実データ 名前=必読に要るファイル（道具が設計書と実装から拾った） -->
| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-F-6d・M2-F-5） | 入れる |
| `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/regime_label.py` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b122_obs_formula_copied.sh` | 新しく作るファイル（NEW_FILE） | 入れる |
| `.claude/breaks/b123_label_tag_dropped.sh` | 新しく作るファイル（NEW_FILE） | 入れる |
| `.claude/breaks/b124_role_keep_off.sh` | 新しく作るファイル（NEW_FILE） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/regime_label.json` | `SDK/scripts/priority_rebuild/regime_r9_diag.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | `SDK/scripts/priority_rebuild/observe_diag.py` が名前を出す（実装の前後の差分） | 入れない（観察の道具が先を見る本数を読まなくなった元。説明の文に名前が残るだけ（keep を読む stage_keep_range は直していない）） |

<!-- 項目: 監査対象 -->
- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q7：まこさんの要望を、この工事の後の実装が満たしているか（問い2）
- Q8：工事 B の後、札を作る場所が1つになり、札を直すと観察の道具と測る道具の両方が同じ札で動くか
- Q9：採点に使う版が er_median のとき、測る道具と成績表の数字が直す前と同じか
- Q10：札の版の名前が、順位表・落ちた候補・成績表に書かれ、たどれるか
- Q11：採点に使う版が役割を持つとき（band_hold）、役割ごとに測り、段ごとに役割ごとに keep 本ずつ残すか
- Q12：自己検査 T6・⑫・⑬ と壊すプログラム b122〜b124 が、それぞれの判定を外したときに落ちるか
- Q13：観察の道具と札の部品を書き替えたことで、H2 の印が取り直されているか

<!-- 項目: 監査対象外 -->
- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- ⑪タブの道具 build_regime_label_dashboard.py を部品に切り替えること（9/29 の控えの実装の指示 23〜27）（工事 C でやる）
- 役割ごとの札（band_hold）のときの差し戻し（--sweep）を作ること（差し戻しは「良くなったか」を1つの並べる鍵で比べる。役割ごとの札のとき、どの役割の鍵で比べるかは、まだどの文書にも決まっていない（§51 の1 は段ごとに残す本数だけ）。役割の列を黙って混ぜて比べないよう、band_hold のときは止まる形にし、採点に使う版を切り替えるときに作る）
- 版2 の使う値を選ぶこと・採点に使う版を band_hold に切り替えること（使う値は まこさんが⑪タブの目と検査15 で選ぶ。選ぶまでは版1 のまま）
- 上げ・下げ・スパイクの札を作ること（範囲は M2-M-1 で まこさんが決める）
- 観察の道具の中で _regime_labels と _regime_horizons を呼んでいる8か所を直すこと（呼ぶ名前と戻りの形を変えないので、8か所は直さずに部品を通る）

<!-- 項目: 問い 番号=Q1 優先度=A 理由=違えば、実装は設計書のとおりに作られていない 名前=実装の指示を当てた結果が、実装の後と1文字も同じか -->
実装の前（commit fefb00e）の対象のファイル（`.claude/breaks/b122_obs_formula_copied.sh`・`.claude/breaks/b123_label_tag_dropped.sh`・`.claude/breaks/b124_role_keep_off.sh`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/regime_label.py`・`SDK/scripts/priority_rebuild/regime_r9_diag.py`）に、設計書 4-20 の実装の指示（30 件）を番号の順に当てた結果が、実装の後（commit 19d1bd7）と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

<!-- 項目: 問い 番号=Q2 優先度=A 理由=在れば、設計書に無い変更が実装に混ざっている 名前=実装の指示のどれにも当たらない行（設計書に無い変更）が無いか -->
実装の前（commit fefb00e）と実装の後（commit 19d1bd7）の差分（`.claude/breaks/b122_obs_formula_copied.sh`・`.claude/breaks/b123_label_tag_dropped.sh`・`.claude/breaks/b124_role_keep_off.sh`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/regime_label.py`・`SDK/scripts/priority_rebuild/regime_r9_diag.py`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

<!-- 項目: 問い 番号=Q3 優先度=A 理由=合わなければ、どの件を道具が当てたかを後から確かめられない 名前=当てた記録が、実装の指示の全部と1件ずつ合うか -->
当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2f-label-callers-20261002`）が、実装の指示の 30 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

<!-- 項目: 問い 番号=Q4 優先度=B 理由=当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない 名前=承認した版の設計書どうしで、実装の指示が同じか -->
承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.01.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.md`）と、いまの設計書の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

<!-- 項目: 問い 番号=Q5 優先度=B 理由=要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない 名前=実装の指示が、やることの表の要件を全部 満たすか -->
実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-callers-20261002/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

<!-- 項目: 問い 番号=Q6 優先度=B 理由=成り立たなければ、承認のときの「済」が根拠にならない 名前=完成の条件が、実装の後に本当に成り立つか -->
設計書の完成の条件（4 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/regime_label.py --selftest`・`python3 scripts/priority_rebuild/regime_r9_diag.py --selftest`・`python3 scripts/priority_rebuild/regime_r9_diag.py --stage stage1 --limit 2 --purpose check`

<!-- 項目: 問い 番号=Q7 優先度=A 理由=満たしていない要望が在れば、まこさんの要望が届いていない（この答えが問い2 の答えになる） 名前=まこさんの要望を、この工事の後の実装が満たしているか（問い2） -->
下に並べた まこさんの要望を、この工事の後の実装が満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。この問いの答えが、結論を決める問い2 の答えになる。

  1. 目的：札が不適切だと分かったとき、直しやすい状態にする。工事 B が受け持つのは、札を作る場所を1つにすることと、どの版の札で選んだかを成績表の側に残すこと
  2. 札を作る場所を1つにする。観察の道具の中にある式を、⑪タブの道具と成績表の道具が別々に呼ぶ形をやめる（⑪タブの道具の切り替えは工事 C）
  3. どの版の札で作った成績表かを、成績表の側に残す。順位表と落ちた候補のファイルに、札の版の名前を書く
  4. 札の数字は設定ファイルに置き、値を書き替えて走らせ直せば札を作り直せる（工事 A で作った設定を、観察の道具と測る道具も読む）

<!-- 項目: 問い 番号=Q8 優先度=A 理由=場所が2つ残っていれば、M2-L で札が外れていたと分かって直したとき、片方だけが変わる（この工事の目的が満たされない） 名前=工事 B の後、札を作る場所が1つになり、札を直すと観察の道具と測る道具の両方が同じ札で動くか -->
写しの作業場で、次の3つを試してください。①regime_label.json の数字だけを書き替える（例＝er_median の先を見る本数）と、コードを1文字も変えずに、observe_diag._regime_horizons・observe_diag._regime_labels と regime_r9_diag._labels_for の3つが同じ新しい札・本数を返すか。②観察の道具と測る道具の中に、札の式（中央値で切る式）や先を見る本数の数字が残っていないか。③札を作る部品以外に、regime_label.json を読む所が無いか。直した後も2か所に残る所や、黙って古い札を使う所が在れば、全部 挙げてください。

<!-- 項目: 問い 番号=Q9 優先度=A 理由=違えば、札の呼び方を変えただけで M2-F-1〜M2-F-5 で測った数と比べられなくなる 名前=採点に使う版が er_median のとき、測る道具と成績表の数字が直す前と同じか -->
同じデータで、直す前（commit c44ac3a の版）と直した後の測る道具（--stage stage1 --limit 2 --purpose check）の3つの割合と列の名前を比べてください（直した後の印字は worklog 20261002 §8 の 8-8 に在る）。観察の道具の _regime_labels と _regime_horizons も、直す前と後で同じ答えを返すかを見てください。

<!-- 項目: 問い 番号=Q10 優先度=A 理由=書かれなければ、売買の結果を見て札を疑うときに、どの札で選んだ束かをたどれない（まこさんの構造の文の3つ目） 名前=札の版の名前が、順位表・落ちた候補・成績表に書かれ、たどれるか -->
順位表と落ちた候補の各行の「札の版」が regime_label.version_tag と同じか。成績表を書く口（_insp_regime_rank）と需給を足す口（add_demand_to_ranking）が札の版を書くか。版の違う成績表に需給を足そうとしたら止まるか。札の版の欄が無い成績表（いまの material_ranking.json）を、版1 で作った物として読むことが正しいか。成績表を読む側（engine_tuner_gen.load_material_ranking）が、札の版の欄を足しても読めるかも見てください。

<!-- 項目: 問い 番号=Q11 優先度=A 理由=役割が違えば使う戦略が違うので、混ぜて並べると片方の役割に合う束が落ちる（worklog 20260928 §51 の1） 名前=採点に使う版が役割を持つとき（band_hold）、役割ごとに測り、段ごとに役割ごとに keep 本ずつ残すか -->
写しの作業場で、regime_label.json の採点に使う版を band_hold にし、役割ごとの「使う値」を範囲の中の1組に書いて、測る道具の --stage を走らせてください。列の名前の括弧の中が役割の名前になるか・rank_rows が役割ごとに keep 本ずつ残すか・差し戻し（--sweep）が止まるか（役割ごとの比べ方は決まっていないので止まる作り）を見てください。観察の道具の先を見る本数（_regime_horizons）が役割ごとの本数を返し、_regime_labels がその役割の札を返すかも見てください。

<!-- 項目: 問い 番号=Q12 優先度=B 理由=判定を外しても落ちなければ、札の式の書き写し・札の版の書き忘れ・役割ごとの残し忘れが黙って入る 名前=自己検査 T6・⑫・⑬ と壊すプログラム b122〜b124 が、それぞれの判定を外したときに落ちるか -->
b122（観察の道具に札の式を書き写す → T6）・b123（順位表に札の版を書かない → ⑬）・b124（役割ごとに残さない → ⑫）を写しの作業場で走らせ、期待どおりに落ちるか、壊す対象の行がちょうど1か所かを見てください。T6 が測る道具の _labels_for も見ているかも確かめてください。

<!-- 項目: 問い 番号=Q13 優先度=B 理由=取り直していなければ、未来参照の検査を通らない形で engine_tuner が回る 名前=観察の道具と札の部品を書き替えたことで、H2 の印が取り直されているか -->
h2_pass.json の指紋が、いまの observe_diag.py と regime_label.py を含む24件と合うかを見てください（enforce_h2_pass.py --check-fingerprint）。G2 の印の対象が38件から39件に増えた理由（増えたファイル）も示してください。


<!-- 項目: 自己申告 -->
**測っていない見積もり**＝自己検査と b122〜b124（測っていない・4-14）

<!-- 項目: 自己申告 -->
**承認の後に設計書を作り直した**＝前の版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.01.md` と いまの版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.md` の違い＝ACC_SPEC の囲みの中で 6 行・囲みの外で 12 行（実装の指示の囲み ACC_IMPL は同じ）

<!-- 項目: 自己申告 -->
**この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）
