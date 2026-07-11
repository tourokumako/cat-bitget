# session_log 2026-07-11 — E37 基本原則③の照合分析 → v18 TP2 反対側ゾーン（詳細は ledger ARC33）

- まこさん指示「Exit 側を状態機械のやり方で少しずつ改善」「_check_exits_replay を見て理解し直せ」→ 理解し直し（V9 は含み益が残っているうちに確定・枝は分業・常設）→ candle replay 7変種で守り枝常設化は両窓中立と実測（回収≈巻き込み・L-334）→ 伸ばす側の取り逃し $4,311 実在 → v18（TP2 反対側・1レバー・選定0回）承認→実装→本走→precheck FAIL＝採点温存（平均勝ち +20%・参考 +$7→+$94・件数 −8%）。
- 記録: ledger ARC33／next_step 上書き（ARC 表 36 iter 再生成）／WORKFLOW 改訂128／lessons L-334／台帳 E37 行・entry_exit_matrix #21 試済化。
- 運用メモ: list_banned_words.py は実在（.claude/tools/・SessionStart の「❌欠落」表示が誤り＝verify_handoff_paths の参照ズレ）。
