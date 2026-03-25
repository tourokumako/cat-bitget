# release_guide.md — 本番リリース手順書（Phase 4）

本番切り替えはユーザーが手動実施。Claude は実施しない。

---

## Step 1: Go/No-Go チェック（全項目 ✅ で次へ）

| # | 確認項目 | 確認方法 |
|---|---------|---------|
| G-1 | デモ稼働テスト完了・WORKFLOW.md が Phase 4 | WORKFLOW.md 冒頭を確認 |
| G-2 | デモポジションなし | Bitget デモ画面 |
| G-3 | 本番口座にオープンポジション・未約定注文がない | Bitget 本番画面 |
| G-4 | 本番口座の証拠金残高を確認 | Bitget 本番画面 |
| G-5 | state/ 配下に open_position.json / pending_entry.json がない | `ls state/` |
| G-6 | api_failure_count.json を backups/ に退避 | `mv state/api_failure_count.json backups/`（なければスキップ） |

---

## Step 2: 本番 API キー設定

`config/bitget_keys.json` をエディタで直接編集する（Claude には見せない）。

変更する項目:
- `apiKey` / `secretKey` / `passphrase` → 本番用に変更
- `paper_trading` → `false`

編集後、paper_trading だけ確認（秘密情報は出力しない）:
```bash
python3 -c "import json; d=json.load(open('config/bitget_keys.json')); print('paper_trading:', d['paper_trading'])"
```
→ `paper_trading: False` が出ること

---

## Step 3: ALLOW_LIVE_ORDERS 確認

```bash
grep "ALLOW_LIVE_ORDERS" runner/run_once_v9.py
```
→ `ALLOW_LIVE_ORDERS = True` であること

---

## Step 4: 本番 API 疎通・権限確認

### ① read 系疎通確認

```bash
.venv/bin/python3 -c "
import json, sys
sys.path.insert(0, '.')
cfg = json.load(open('config/bitget_keys.json'))
from runner.bitget_adapter import BitgetAdapter
a = BitgetAdapter(cfg)
candles = a.get_candles('BTCUSDT', 'USDT-FUTURES', '5m', limit=1)
print('candles OK, latest close:', candles[-1][4])
pos = a.get_position('BTCUSDT', 'USDT-FUTURES', 'long')
print('position OK, total:', pos.get('total', '0') if pos else '0 (no position)')
"
```
→ `candles OK` / `position OK` が出ること。エラーなら APIキーを再確認。

### ② APIキー権限確認（Withdraw なし）

Bitget の API 管理画面（本番）を開き、使用する API キーの権限を目視確認:
- ✅ `Read` — 必須
- ✅ `Trade` — 必須
- ❌ `Withdraw` — **オフであること（必須）**

### ③ crontab の python パス確認

```bash
crontab -l | grep run_once
```
→ `.venv/bin/python3` を使っていること（`python3` だけでは venv 外を叩いてしまう）

---

## Step 5: 初回手動実行

```bash
echo "=====🚀  RUN START $(date) =====" && .venv/bin/python3 runner/run_once_v9.py
```

**成功条件:**
- `CONFIG_LOADED: paper_trading: false`
- `STATE_DECLARED: mode=live, paper_trading=false`
- `MARKET_SANITY_OK`
- STOP / ERROR が出ない
- `RUN_SUMMARY: action=NOOP` または `ENTRY_SEND: code=00000`

---

## Step 6: cron 稼働確認

```bash
crontab -l
```
→ `tools/monitor.sh`（STOP/ERROR → iPhone 通知）が登録されていること

---

## Step 7: 初回エントリー後の確認（エントリーが入ったら）

- Bitget 本番画面でポジション・TP・SL を目視確認
- `state/open_position.json` の内容と取引所が一致していること
- add_count=2 以降で SL が設定されていること

---

## 緊急停止手順

1. cron を無効化: `crontab -e` → runner 行をコメントアウト
2. `runner/run_once_v9.py` の `ALLOW_LIVE_ORDERS = True` → `False` に変更（ユーザーのみ）
3. Bitget 本番画面で手動決済（必要な場合）
4. `state/open_position.json` を確認・取引所と照合してから削除

---

## 本番稼働後の残タスク（急がない）

- **S-7② SL_FILLED**: SL 約定後に `EXIT_EXTERNAL(SL_FILLED)` が出ることを実API確認（Change A）
- **S-1⑤**: API失敗時に pending_entry.json が残らないことを確認
- 詳細: `project_v9_progress.md` の「残タスク」参照