"""periods.py — 検証期間の【唯一の正本】（学習・捨て(embargo)・採点・封印の区切り）。

★これがプロジェクト全体で期間を定義する唯一の場所。全戦略・審判(score.py)・地面スクリプトは
  ここから import し、日付を自前で書かない（ハードコード禁止＝ズレ再発防止・require_period_source hook）。
  数値が複数箇所に分散して食い違う事故（2026-06-18 発覚＝採点窓が 2025-04〜12／2025-06〜2026-02／
  2025-06〜2025-12 の3版並存・E35 が部分反映で第3窓を作った）の構造的対策（single source of truth / DRY）。

値の出所（変更はまこさん承認＋ledger 記録が必須・勝手に変えない）:
  E31（2026-06-13 まこさん確定・ledger E31「検証期間を2ヶ月後ろ倒し」）
    学習 〜2025-02 / 捨て 2025-03〜05 / 採点 2025-06〜2026-02 / 封印 2026-03〜05
  根拠: 期間分割を決めて約2ヶ月経過 → 新2ヶ月(2026-01/02)を採点に取り込み、検証窓を後ろ倒し。
       SHORT 地面 P21$401.51 / P23$241.72 / E32b$616.55 は全てこの窓で測定。
  leak 原則（false_positive §0-1 / H2 / H8）: 学習末 < 採点始（embargo を挟む）を下の assert で物理保証。

旧窓（2025-04〜12 等）はここに定義しない（混在の芽を断つ）。旧窓との一致確認が要る時は
  score.py の --legacy-window 明示フラグで扱う（既定では旧窓では採点できない）。
"""
import pandas as pd

# ── 学習期間: < TRAIN_END（2021-04〜2025-02 でモデル/閾値を fit）──
TRAIN_END = pd.Timestamp("2025-03-01")        # 学習は TRAIN_END 未満（= 〜2025-02 末）

# ── 捨て(embargo): leak 防止の緩衝・学習にも採点にも使わない（2025-03〜05）──
EMBARGO_START = pd.Timestamp("2025-03-01")
EMBARGO_END = pd.Timestamp("2025-06-01")       # = SCORE_START（捨ては採点開始の直前まで）

# ── 採点期間: [SCORE_START, SCORE_END]（inclusive・2025-06〜2026-02）= 公式 net を測る窓 ──
SCORE_START = pd.Timestamp("2025-06-01")
SCORE_END = pd.Timestamp("2026-02-28")         # inclusive（E31 再現 CLI `--end 2026-02-28` と一致）

# ── 封印: 過剰適合の独立チェック用・iteration 中は不参照（2026-03〜05）──
SEAL_START = pd.Timestamp("2026-03-01")

# ── CLI / 文字列比較用（score.py の --start/--end 照合に使う・YYYY-MM-DD）──
SCORE_START_STR = "2025-06-01"
SCORE_END_STR = "2026-02-28"

# ── 整合の自己検証（import 時に必ず走る＝窓の不整合を1箇所で物理検出）──
assert TRAIN_END <= EMBARGO_START < SCORE_START < SEAL_START, "期間の前後関係が壊れている"
assert EMBARGO_END == SCORE_START, "捨て(embargo)の終端が採点開始と一致しない"
assert SCORE_END < SEAL_START, "採点終了が封印開始より前でない（採点と封印が重なる）"
assert TRAIN_END < SCORE_START, "学習末 < 採点始 でない（leak・H2/H8 違反）"
assert SCORE_START_STR == SCORE_START.strftime("%Y-%m-%d") and SCORE_END_STR == SCORE_END.strftime("%Y-%m-%d"), \
    "CLI 文字列が Timestamp と不一致"
