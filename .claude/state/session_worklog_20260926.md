# session_worklog_20260926.md — 120回目の続き（2026-09-25 の §6 の続き・日付が変わったので新しいファイル）

## §1 commit と、47番の説明（2026-09-26・120回目）

### 1-1 commit（まこさん OK「コミットはOK」）

- commit＝`d85942e`（26件）。中身＝コード3本（engine_tuner_exec.py・engine_tuner_gen.py・streak_scope_diag.py）／壊すプログラム3本（b99・b100・b103）／ratchet の元データ acceptance_src.json／承認の控え m2e-bundle1-20260925 の一式（.md・.01.md・.01.diff.txt・.01.sha.txt・.breaks.json・.dirty.json・.frozen.json）／承認のプログラムが書いた breaks_frozen.json・impl_functions_frozen.json／材料の文書 materials.md・materials.json・engine_tuner_milestones.md・engine_tuner_milestones2.md／decisions.md／worklog 20260925／next_step の3ファイル。
- 登録の仕方＝追跡中のファイルは `git add -u <フォルダ>`（engine_tuner の名前をコマンドに書くと設計↔実装ゲートが止めるため＝§6 の156番）。新しいファイルは名前で add。

### 1-2 47番の説明を まこさんに出した

- まこさんの問い（逐語）＝「47番の位置（束2 の後・M2-E-6 の前）で、やることリストに足してよいか。→どういうこと？わかりやすく説明してほしい」。
- 説明の中身＝チャットの返信（やることリストの正本 m2_todo.json に新しい番号を足す位置の話）。

### 1-3 まこさん「この案でOK」→ M2-E-4e を足した（2026-09-26）

- m2_todo.json に M2-E-4e を1件足した（M2-E-4c の後・M2-E-6 の前）。依存の表に M2-E-4e の行を足し、M2-E-6 の依存を「M2-E-3〜M2-E-5 と M2-E-4e が要る」にした。まとまりの分け方の文にも 4e を入れた。
- `gen_regime_kb.py --write todo`＝§3（やることリスト）を engine_tuner_milestones2.md に書いた（本文 1555行・hash=9f4b1339d0d73324）。
- `gen_regime_kb.py --verify all`＝§2・§3・§2.2-0・§11・§12 は ✅。★❌1件＝「R7: 引用の行の前後5行に `wpct_arr` が無い」（file:line 引用の実在検査＝9件のうち ずれ 1件）。`--selftest`＝14/15（落ちたのは T11「引用の実在検査 いまの引用に ❌ が在る」＝同じ件）。
- 原因＝束1 の実装で engine_tuner_exec.py に行が足され、`wpct_arr` の行が動いた。いまは `engine_tuner_exec.py:2669`（sed -n '2664,2672p' で開いた）。古い行番号（2626）の所は、いまは出口の発火条件の評価の中（sed -n '2621,2631p' で開いた）。古い行番号を書いているのは regime_laws.json の758行（R7 の注意）と regime_detection_kb.md の868行（R7 の説明）。★束1 の設計書の影響範囲（4-13）にも、監査 CP39 の B3-c にも無かった影響。
- ★法則ファイルの文字を直す話なので、直す前に まこさんに出した（この工事は「法則ファイルは1文字も触らない」と書いていた）。

### 1-4 まこさん「直してよい」→ R7 のメモの行番号を直した（2026-09-26）

- regime_laws.json の R7 の注意（758行）の `engine_tuner_exec.py:2626` を `:2669` に直した（Edit・行番号の数字だけ・法則の判定の中身は変えていない）。
- regime_detection_kb.md の868行も同じに直した。★この行は `gen_regime_kb.py` が法則ファイルから作る §11 の中だった（道具の "laws": KB）＝手で直す相手ではなかった。`--write laws` で作り直した結果の指紋（a7191b68…）は、手で直した版と同じ。
- `gen_regime_kb.py --verify all`＝全部 ✅・file:line 引用の実在検査＝9件のうち ずれ 0件。
- 法則ファイルを読む道具の自己テスト7本（hook が求めた）＝gen_regime_kb 15/15・gen_composition_rules 全部 pass・gen_indicator_switch 11/11・engine_tuner_exec 全部 pass・leak_causality_diag 全部 pass・gen_acceptance 9/9・engine_tuner_gen 全部 pass。
- H2（`leak_causality_diag.py`）＝注記なし未来参照 0件・打ち切り再現テストの食い違い 0件・印 892e9bac…。`tidy_next_step.py --write` で next_step の印の欄を書き直した。G2 は法則ファイルが印の対象に無いので取り直していない（g2_pass.json に regime_laws.json の名前が0件）。
