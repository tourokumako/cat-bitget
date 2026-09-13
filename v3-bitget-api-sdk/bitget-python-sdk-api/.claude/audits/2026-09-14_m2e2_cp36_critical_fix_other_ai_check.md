# 確認の依頼｜監査 cp36 の Critical 3件は、本当に直ったか（別の AI に見てもらう・2026-09-14）

- 頼む相手＝この会話を知らない別の AI（別セッションの Claude Code か Web Claude）。**監査ではない**（まこさん決定 2026-09-13「設計書は監査に出さなくて良い→ Critical 3件修正後に、本当に修正できているのかを別AIに確認させる」）。
- 出した人＝CC（98回目のセッション）。まこさんがこの依頼書を別の AI に渡す。
- 置き場＝`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/`（依頼書の置き場 `inputs/` は監査の依頼書のゲートが掛かるので使っていない）。

## 1. 何を確かめてほしいか（1つだけ）

**監査 cp36（`.claude/audits/2026-09-13_m2e2_impl_cp36_audit_report.md`）が出した Critical 3件（C-1・C-2・C-3）が、いまのコードで本当に直っているか。**C-1〜C-3 のそれぞれについて「直った／直っていない／判断できない」と、その根拠になった実物の行かコマンドの出力を書いてください。

## 2. 前提（これだけ読めば足りる）

| 何 | どこ |
|---|---|
| 監査 cp36 の Critical 3件の逐語 | レポート §0-3 の表（40〜42行）。C-1＝実際に組まれる束（2本目）に `drop_tfs`・§2.2 の元データの絞り・符号を取り去る前処理が掛かっていない ／ C-2＝「候補を全部 並べ、上位を次の段へ渡す」の「渡す」が実装されていない ／ C-3＝完成の条件 #1 を測る自己テストが無い（T24⑤・T35 が0件） |
| 直したコード | `scripts/priority_rebuild/engine_tuner_gen.py`＝`build_stage_candidates`（1本目・候補の一覧）／新設 `stage_keep_of`・`_stage_pick`／`stage_counts`／`sample_regime_build`（2本目・実際の束）／自己テスト T24⑤・T42・T35（`selftest()` の中・見出しの行を `grep -n "══ T24⑤\|══ T42\|══ T35"` で探す） |
| 設計書（承認済み） | `.claude/state/acceptance.md`（目印 `m2e2-cp36-critical-20260913`・承認の印 `.claude/state/acceptance.approved`＝`5ca86b458773d43a…`）。完成の条件＝7-6 の表（#1〜#4・#8 が ✅済・#5〜#7 は壊すプログラムを持たない行） |
| 直す前のコード | git の commit `31f0547`（2026-09-13・監査に出した版）。`git diff 31f0547 -- scripts/priority_rebuild/engine_tuner_gen.py` で差分が見える |
| 私（CC）の記録 | `.claude/state/session_worklog_20260913.md` §23〜§27・`session_worklog_20260914.md` §28〜§32 |

## 3. 確かめ方（走らせられるなら、この順に）

| # | 何を | コマンド（`v3-bitget-api-sdk/bitget-python-sdk-api` で打つ） | 期待（CC の実測 2026-09-14） |
|---|---|---|---|
| 1 | 自己テスト（約8分半） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 最後の行「✅ 全部 pass」。T24⑤ の行＝「変わった ['C6', 'R1', 'R4', 'R5', 'R6', 'R7', 'R8'] ／ 変わらない ['C4', 'R3']」。T42 の行＝「一覧と合わない・外す時間足・abs 無し・keep の食い違い＝0 件／向きを持つ C 22 件」。T35 の行＝「上端 null → keep 336／上端 1 → 案2 は『上位 1 本の外』で組めない／範囲の外 3通りは止まる」 |
| 2 | 実際の束に10分足と abs 無しが残っていないか（C-1） | 監査の作業場の道具を使う＝`.claude/audits/cp36_work/scan_bundles.py` を、写しではなく本物の `scripts/priority_rebuild` を読む形で（`PR` を本物のパスに）200本 走らせる。または自分で `sample_regime_build(lm, pool, tfs, tbl, order_n=n)` を呼んで数える | 帯の枠（B）に 10m が **0本**（監査の実測は 78本）。強さの否定（C）で EMA傾き・MACDヒスト%・DI差 が出た束は全部 `pre: {"op": "abs"}` 付き（監査の実測は 0本） |
| 3 | 2本目が1本目の一覧から取っているか（C-2） | `grep -n "_stage_pick\|build_stage_candidates(" scripts/priority_rebuild/engine_tuner_gen.py` | `sample_regime_build` の中で `build_stage_candidates("stage1"…)`・`("stage2a"…)`・`("stage2c"…)` を呼び、B・C・G を `_stage_pick(…)` で取っている。`fixed` の引数は無い。`keep` は `stage_keep_of(limits, …)`（1 の直書きは無い） |
| 4 | 壊すプログラムが本当に守っているか | 承認④の記録 `.claude/ratchet/acceptance_archive/m2e2-cp36-critical-20260913.breaks.json` | b93・b92・b91・b85・b78 の5本とも `code: 1`。★自分で `bash .claude/breaks/b9x_*.sh` を走らせられるなら、それが一番強い確認（1本 約8分半・コードは自動で元に戻る・戻せなければ exit 99） |
| 5 | 法則番号の直書きと乱数が組む関数に無いか | `python3 ../../.claude/tools/count_builder_literals.py` | 乱数0件・法則番号0件・rc=0 |
| 6 | 診断の束に新しい記録の鍵が出るか | `python3 scripts/priority_rebuild/regime_r9_diag.py --build 3 --no-trades --seed 8` | 束が3本 組める。引いた記録の B・C・G に `候補の一覧`（"stage1" など）と `上位`（本数）の鍵が在る。★種7 は需給の列で3本とも測れない（監査 cp36 の M-4＝別セッション・直っていないのが正しい） |

## 4. 見ないでよいもの（この依頼の外）

- 監査 cp36 の Major 7件（M-1〜M-7）と別枠 8件（S-1〜S-8）＝まこさん決定で別セッション。特に、審査 G7 が前処理 abs を見ない件（§6 A5-b）・組む側が法則 C4 を読まない件（M-3）・設定の欄 `stage_limits`（M-1）・需給の列で止まる件（M-4）は直していない。
- 組んだ束が「良い判定」かどうか（成績）＝M2-F 以降で測る。
- 入口の束・出口の枝の乱数＝M3・M4。

## 5. 答えの形（この表を埋めてください）

| 指摘 | 直ったか（直った／直っていない／判断できない） | 根拠（実物の行番号か、走らせたコマンドと出た行） |
|---|---|---|
| C-1（2本目に3つの絞りが掛かっていない） | | |
| C-2（「渡す」が実装されていない・keep=1 直書き・fixed 未使用） | | |
| C-3（T24⑤・T35 が無い） | | |
| ★CC が「直った」と言っている根拠のうち、あなたが確かめられなかったもの | | |
| ★新しく見つけた問題（在れば） | | |

## 6. CC が正直に書く限界

- CC は自分の Bash から壊すプログラムを走らせられない（土台ゲート）。5本が落ちることは承認のプログラム（まこさんの端末）の記録で見た。
- T42 の abs の検査は、案の番号の範囲（最大200本）に向きを持つ C が出たときだけ測れる（出なければ「測れない」で落ちる作り＝いまの実測は22件 出ている）。
- 法則 C4 と R3 は、1件だけ書き替えても束が変わらない（C4 は組む側が読まない・R3 は R1 が系統を持つ間は読まれない）。T24⑤ はこの2件を「変わらない」と期待に書いている＝監査 cp36 §2 の実測どおり。これを「C-3 が直っていない」と読むかどうかは、あなたの判断を書いてください。
- 設定の欄 `drop_tfs` を空の配列にすると既定の3本に戻る（注記と違う）＝§6 の183番に積んだ・直していない。
