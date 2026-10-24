# 【タスク】第二の最大級規定「ポジション上限 0.12 BTC 合計厳守」を 6 箇所に埋め込み

発行日: 2026-05-15
承認: まこさん（明示的 GO）
位置づけ: Prime Directive（本番再現性）と並列の **2 大絶対規定** として固定

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-15_position_limit_embed.md`
- 完了報告: `.claude/instructions/2026-05-15_position_limit_embed_completion.md`
- 着手前に `.claude/instructions/2026-05-15_prime_directive_embed.md`（前回 5 箇所埋め込み）を参照しフォーマット踏襲

## このタスクの位置づけ（最重要）

CLAUDE.md「合計 0.12 BTC（1 ポジあたりではなく合計上限・cap=N なら 1pos = 0.12/N BTC）」と明文で書かれていたにもかかわらず、`run_phase4b_phase5_rolling_option5.py` が `POSITION_BTC=0.12` を全エントリーに直接掛ける実装で動き、cap=none で 19 combo 同時発火時に **規定の 19 倍（合計 2.28 BTC）の実効エクスポージャー**となっていた。

これは Prime Directive（本番再現性）違反と同じ重さの事故であり、leak と並んで「**明文化された運用上限を実装が逸脱する**」インシデント類型として最大級扱いする。

「気をつける」「指示書に毎回書く」では止まらないことが過去 7 回の同種事故で実証済み。**Prime Directive と完全に同じ構造（6 箇所への冗長配置・実装前ゲート・違反の最重大インシデント定義）で固定する**。

Prime Directive とポジション上限厳守は、本タスク完了後、**プロジェクトの 2 大絶対規定**として並列に扱う。
