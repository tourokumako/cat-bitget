# 【タスク】正本矛盾の解消 — cc_ml_design_spec §1.6.2 / WORKFLOW.md 旧記述 / handoff v6

発行日: 2026-05-15
承認: まこさん（明示的 GO）
読了ゲート通過: 2026-05-15（コア5本＝WORKFLOW.md / CLAUDE.md / cc_ml_design_spec.md / handoff v5 / lessons_active.md）
self_check (A) 通過: 2026-05-15

---

## 背景

WORKFLOW.md §🔴現在のフェーズが改訂11（2026-05-15）に更新され、このセッションの経緯（rolling 365採用・選択肢5採用・Phase 4-b/5実行・audit#12 leak判定・ガバナンス文書整備）を反映済み。しかし改訂11を最上部に追加しただけで、下位の古い記述・cc_ml_design_spec・handoff が追従していない。lessons_active.md L-181（設計転換時の旧記述放置の禁止・まこさんが「命令」と明記）に該当する状態。

本ルート（Phase 4-b の trailing exit verify）に進む前に、この矛盾を解消する。矛盾した正本のまま Phase 4-b 作業に入ると、CC が cc_ml_design_spec §1.6.2 の「rolling 不採用」を読んで混乱する。

---

## 修正対象 3 件

### 修正1: cc_ml_design_spec.md §1.6.2 — rolling 採用への書き換え

§1.6.2 を「audit#9 の rolling 却下を、まこさん明示承認のもとで撤回し、rolling 365日を採用した」という経緯の事実の記録に書き換える。

- rolling 採用を正当化する記述にしない（「優れているから採用」ではなく「まこさん指示を受けて撤回・採用」）
- 却下時に挙がっていた懸念（信号品質全面低下・§1.6.1 メタルール抵触疑い）を「未解消の留意事項」として残す
- audit#12 で trailing exit leak が発覚したことも記載
- 旧「spec 追記のみ・実装側無変更」は削除

### 修正2: WORKFLOW.md L451-456「セッション確定事項」と L459- 旧記述

- L451-456 の項目2（固定維持）・項目3（選択肢 5 vs 7 再評価）を改訂11（L273）へのポインタ付き注記で旧記述化
- L463 のポインタ「L274」→「L273」に更新

### 修正3: handoff v6 の作成

`.claude/instructions/handoff_to_web_claude_v6_session_20260515.md` を新規作成する。

---

## 完了証跡（このファイル保存後の作業記録）

1. 着手前必読5項目の引用:
   - WORKFLOW.md L273: `## 🔴 現在のフェーズ（2026-05-15 改訂11・Phase 4-b/5 実行済み・trailing exit leak 要修正）`
   - WORKFLOW.md L454: `2. ✅ 絶対閾値 drift = **固定維持 + K96 SHORT q99 除外**確定 (audit#9)`
   - cc_ml_design_spec.md L118: `### 1.6.2 絶対閾値 drift 対処方針 (2026-05-14 audit#9 確定)`
   - handoff v5 L53: `**選択肢 5 vs 7 の再評価**`
   - lessons_active.md L243: `### L-181: 設計転換時の旧記述放置を「毎回やってる」とまこさんに命令で禁止（2026-05-13）`
   - false_positive_incident_policy.md §2 類型G・§5 関所F: 確認済み

2. grep sweep 全件（`grep -n "固定維持\|選択肢 5 vs 7" WORKFLOW.md`）:
   - L454: `2. ✅ 絶対閾値 drift = **固定維持 + K96 SHORT q99 除外**確定 (audit#9)` → **旧記述**（注記追加）
   - L455: `3. ✅ 次のタスク = **選択肢 5 vs 7 の再評価** (監査経路を通す・handoff §3 参照)` → **旧記述**（注記追加）
   - L462: `> 2026-05-14 セッション末の drift 対処確定 (固定維持 + K96 SHORT q99 除外) 後、` → 🧊 セクション内の旧記述。現行扱いなし・追加処理不要
   - L463: `> 次のタスクは **「選択肢 5 vs 7 の再評価」** に更新済み (§🔴 現在のフェーズ L274 参照)。` → ポインタ L274→L273 更新

3. 異常値スメルテスト: 該当なし（ドキュメント整合性修正のみ・数値生成なし）
