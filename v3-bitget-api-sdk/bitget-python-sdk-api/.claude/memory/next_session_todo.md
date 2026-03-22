---
name: next_session_todo
description: 次セッション開始時に最初に確認・対応するタスク
type: project
---

## 最優先確認事項（セッション開始直後に実施）

### posMode 整合確認

**Why:** CLAUDE.md の目的「CAT_v9_regime.py のロジックを本番で再現可能な範囲で一致させて移植」に反しない状態にするため。V9 は one-way mode 設計のはずだが、現在のデモ環境は hedge_mode で動作している。

**How to apply:**
1. `cat-swing-sniper/strategies/CAT_v9_regime.py` を確認し、posMode（one-way/hedge）の設定を特定
2. `runner/run_once_v9.py` / `runner/bitget_adapter.py` / `exchange_spec.md` の設定と照合
3. 乖離があれば one-way mode に統一する（差分提示 → GO → 変更）

**注意:** one-way mode に変更した場合、`tradeSide: "open"/"close"` の要否・`posSide` パラメータの扱いも再確認が必要。