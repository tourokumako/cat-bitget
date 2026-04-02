# セッション引き継ぎ（2026-04-03 終了時）

## 方針（最重要）

**cat-bitget 側だけで改善を進める。cat-swing-sniper（BT）は触らない。**

最終目標: Bitget本番で NET ≥ $120/day / 15日累計 ≥ $1,800

改善サイクル:
1. `replay_csv.py`（= run_once_v9.py の CSV 版）で過去データ検証
2. 改善確認 → `cat_params_v9.json` / `run_once_v9.py` に直接反映
3. BT（cat-swing-sniper）は参照しない

---

## 今日やったこと

### 1. 方針整理・CLAUDE.md 更新
- 「Replay = run_once_v9.py の CSV 版」として一本化
- `CLAUDE.md` の「現在のアプローチ」を更新
- Exit ロジック同期確認: `_check_exits_replay` と `_check_exits` が完全一致 ✅

### 2. P23 SHORT の構造調査
- MIDTERM_CUT（hold≥240min, PnL<-$25）を試したが悪化 → 却下・リバート
  - 原因: 240min が価格の最悪点付近で、360min TIME_EXIT より大きい損失を固定
  - L-15 に教訓記録済み
- P23 SHORT add=1 に制限（MAX_ADDS_BY_PRIORITY に "23":1 追加）→ 5日 NET -$147→-$81 改善
  - GROSS がプラス転換（ADD が構造的損失の原因と確認）

### 3. 90日 Replay 実行（最重要な発見）
- データ: 2026-01-01〜04-01（26,057 bars、18ファイル結合済み）
- **NET: -$7,711 / 90日（-$85.7/day）**
- 5日テストで「P2 LONG は機能している」と判断したのは誤り（偶然の好調期）
- 90日で P2 LONG は -$4,583（全体最大の損失源）

---

## 90日 Replay 基準値

```
CSV: BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv（90日）
NET: -$7,711（-$85.7/day）
GROSS: -$6,080（手数料前からマイナス = 構造的問題）

Exit理由別:
  TP_FILLED      1,184件  +$6,827（勝率 70%）
  MAE_CUT           63件  -$6,385（avg -$101 ← P2 LONG add=4 が主因）
  TIME_EXIT        260件  -$5,087（avg  -$20）
  MIDTERM_CUT       53件  -$2,450（avg  -$46 ← P4 LONG）
  SL_FILLED          1件    -$313

Priority別:
  P2-LONG    572件  -$4,583（-$51/day）
  P23-SHORT  746件  -$1,597（-$18/day）
  P4-LONG    367件  -$1,571（-$17/day）
```

---

## 結論・次にやること（G: エントリー精度改善）

パラメータ調整では目標達成不可能。**ADD 設計かエントリーシグナルの根本見直し**が必要。

検討候補（優先順）:

1. **全 Priority add=1 に統一してシグナル純粋評価**
   - ADD を除いたときのシグナル自体の勝率・期待値を測る
   - P2/P23/P4 それぞれのシグナルが単独で機能するか判断する

2. **P2 LONG の MAE_CUT 対策**（90日で最大損失 -$6,385）
   - add=4（0.096 BTC）時の大損を防ぐ
   - add 上限削減 or MAE 条件変更

3. **トレンドフィルターの追加**
   - 逆行中のエントリーを大局トレンドで絞る（bb_mid_slope / EMA方向等）

---

## 重要なファイル

| ファイル | 役割 |
|---------|------|
| `runner/replay_csv.py` | Replay エンジン（改善検証はここ） |
| `config/cat_params_v9.json` | パラメータ（現状: MAX_ADDS_BY_PRIORITY={"2":4,"23":1}） |
| `data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` | 90日結合データ（cat-swing-sniper/data/） |
| `results/replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` | 90日 Replay 基準値 |

Replay 実行コマンド（90日）:
```bash
cd v3-bitget-api-sdk/bitget-python-sdk-api
source .venv/bin/activate
python runner/replay_csv.py /Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv
```

---

## 注意事項

- **本番 BOT は停止中**
- `cat_params_v9.json` は Replay 検証後に本番反映（run_once_v9.py に自動読み込み）
- `cat_v9_decider.py` のロジック変更は BOT 停止中なので実施可能
