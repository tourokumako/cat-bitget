# セッション引き継ぎ（2026-04-03）

## 方針（最重要）

**cat-bitget 側だけで改善を進める。cat-swing-sniper（BT）は触らない。**

最終目標: Bitget本番で NET ≥ $120/day / 15日累計 ≥ $1,800

現在のアプローチ: **Replay（replay_csv.py）を改善の指標として使う**

---

## 今日やったこと（cat-swing-sniper セッション）

### 1. BT側 MFE追跡を high/low → close に統一（16箇所）
- `strategies/CAT_v9_regime.py` の PROFIT_LOCK ARM/trigger、MAE_CUT trigger 等
- 乖離: $233 → $195（$38縮小）
- コミット済み（cat-swing-sniper: `9c82ae7` の次のコミットに含まれる予定）

### 2. Replay 成行モードテスト
- pending fill を廃止して close で即時約定に変更 → 効果なし（-$191 変わらず）
- **pendingモードに戻した（現状 = 元の状態）**

### 3. P23 SHORT MAX_ADDS 削減テスト
- add=4: MAE_CUT 8→7件、NET -$191→-$171（+$19改善）
- add=3: MAE_CUT 8→2件、TIME_EXIT 10→16件、NET -$191→-$147（+$44改善）
- **元（add=5）に戻した**（TIME_EXITカスケードが大きく、改善余地が小さいと判断）

---

## 乖離の根本原因（結論）

**構造的な差で、個別ロジック修正では解消できない**

```
BT: バーごとループで即時約定 → 61件/5日（高頻度）
Replay: post-only pending → 42件/5日（低頻度）
→ エントリー頻度差 → add積み上がりパターン差 → PROFIT_LOCK/MAE_CUT比率差
```

乖離解消を追うのをやめ、**Replay で改善検証 → 本番反映**のサイクルに切り替え。

---

## Replay の現状（基準値）

```
CSV: BTCUSDT-5m-2026-03-27_04-01_combined.csv（5.1日）
NET: -$190.79（-$37.4/day）

Exit理由別:
  MAE_CUT        8件  -$603（最大の損失源）
  TP_FILLED     73件  +$581
  TIME_EXIT     10件  -$158
  PROFIT_LOCK    1件    -$6
  RSI_EXIT       2件    -$3
  FORCE_CLOSE    2件    -$1

Priority別:
  P23-SHORT     42件  -$221（問題の中心）
  P2-LONG       34件   +$51
  P4-LONG       20件   -$22
```

---

## 次にやること（優先順）

### 最優先: P23 SHORT の MAE_CUT 8件 -$603 を削減する

MAE_CUT の内訳（すべて P23 SHORT）:
- add=5（0.12 BTC）が多い → 300min 保有後に cap_price 到達
- 相場が SHORT に逆行（上昇）している局面でのみ発生

検討アプローチ（まだ未検証）:
1. **P23 SHORT のエントリー条件を絞る**（上昇トレンド中の dead-cross を除外）
   - 例: `bb_mid_slope < X` フィルター（上昇中は SHORT に入らない）
   - ただし BT での lessons: P23 エントリーフィルター追加はカスケード悪化しやすい
2. **MIDTERM_CUT を P23 SHORT に追加**（hold>=120min, PnL<-$XX で早期カット）
   - ただし BT での lessons: SHORT MIDTERM は TP を刈る可能性あり（avg_hold 67min）

### 次点: TIME_EXIT 10件 -$158

---

## 重要なファイル

| ファイル | 役割 |
|---------|------|
| `runner/replay_csv.py` | Replay エンジン（改善検証はここ） |
| `config/cat_params_v9.json` | パラメータ（現状: MAX_ADDS_BY_PRIORITY={"2":4}） |
| `strategies/cat_v9_decider.py` | エントリー条件 |
| `results/replay_BTCUSDT-5m-2026-03-27_04-01_combined.csv` | 最新 Replay 結果（基準値） |
| `data/BTCUSDT-5m-2026-03-27_04-01_combined.csv` | ← cat-swing-sniper 側にある |

Replay 実行コマンド:
```bash
source .venv/bin/activate
python runner/replay_csv.py /Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2026-03-27_04-01_combined.csv
```

---

## 注意事項

- **本番 BOT は稼働中**（変更は慎重に）
- `cat_params_v9.json` は Replay 検証後に本番反映（run_once_v9.py に自動読み込み）
- `cat_v9_decider.py` のロジック変更は BOT 停止後に行う
