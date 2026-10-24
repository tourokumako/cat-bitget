# project_spec.md — ファイル構成・params一覧

## ファイル構成

| ファイル | 役割 | 変更可否 |
|---------|------|---------|
| `strategies/cat_v9_decider.py` | snapshot→df→判断 | GO後のみ |
| `runner/run_once_v9.py` | 発注・状態管理・Exit | GO後のみ |
| `runner/bitget_adapter.py` | Bitget SDK ラッパー | GO後のみ |
| `config/cat_params_v9.json` | V9パラメータ | GO後のみ |
| `config/bitget_keys.json` | APIキー（機密） | 読み取りのみ |
| `state/pending_entry.json` | 指値待機状態 | runner経由のみ |
| `state/open_position.json` | 保有ポジション | runner経由のみ |
| `cat/indicators.py` | インジケーター計算 | 変更しない |
| `cat/const.py` | 定数 | 変更しない |

## 指値エントリー仕様

- LONG: `close × (1 - 0.0001)` / SHORT: `close × (1 + 0.0001)`
- TTL: 3本（15分）期限切れでキャンセル

## SL発動タイミング

- 初回ENTRY後 → TPのみ設定（SLなし）
- ADD約定後（add_count≥2）→ SL設定追加

## テストリスト

→ `.claude/context/test_checklist.md` 参照