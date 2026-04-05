# CLAUDE.md — cat-bitget V9

---

## このBOTの存在意義（設計の根拠）

人間が24時間監視・執行できない相場を、ルール通りに動き続けることで稼ぐ。
- 感情に左右されない規律ある取引
- 24時間365日の自動監視・自動執行
- 人間が張り付かなくてよい時間コストの削減

**対象とするトレードは「24時間以内に決済できる取引」。**
それより長い保有は人間が手動でやった方が判断精度が高いため対象外。

---

## 設計思想

相場の7割はレンジ。ベースはレンジ回帰型（価格が行って戻ってきてTP）で手堅く稼ぐ。
トレンド発生時にも対応できる構造を持つことが理想。
手数料を上回る利益を確実に取れる設計にする。
具体的な手段（指値/成行・TP幅・add回数）はこの目的を達成するために検証・最適化する。

---

## 目標

| 指標 | 基準 |
|------|------|
| Replay NET（本番投入基準） | **$100/day 以上** |
| 本番 NET（最終目標） | **$60/day 以上** |

Replay は intra-bar fill 判定のため過大評価。$100/day をバッファとして設定。

---

## Priority 一覧

現状の特性を示すが、これらは目標達成のために最適化する対象であり固定ではない。

| Priority | 方向 | 現状の特性 | maker指値との相性 |
|----------|------|-----------|----------------|
| P2 | LONG | ストキャスGC（モメンタム） | △ |
| P4 | LONG | 押し目買い（逆張り） | ○ |
| P22 | SHORT | BB急落初動（モメンタム） | △ |
| P23 | SHORT | BB+RSI複合（モメンタム） | △ |
| P24 | SHORT | RSI過熱反転（逆張り） | ○ |

**廃止の判断基準:** あらゆる改善手段を尽くしても edge がゼロと確認できた後のみ。
特定期間に負けているだけでは廃止の根拠にならない。

**ポジションサイズ制約:** エントリーサイズ × (1 + MAX_ADDS) ≤ 0.12 BTC

---

## 改善フロー

**Replay が唯一の検証指標。** 以下の順を必ず守る。

```
1. 分析（集計→個別→仮説）← 当てずっぽう禁止
2. 提案（変更内容・期待値を明示）→ GO待ち
3. 実装（同じ目的の変更はまとめてOK。関係のない複数箇所を同時に変えない）
4. Replay 実走 → 結果確認 → GO待ち
5. 採用 or 却下（却下なら即巻き戻し）
6. WORKFLOW.md 更新
7. 本番反映（run_once_v9.py / cat_params_v9.json）→ GO待ち
```

**replay_csv.py と run_once_v9.py の _check_exits は常に同期を保つこと。**

---

## 絶対禁止（NEVER）

- `ALLOW_LIVE_ORDERS=False` を True に変更しない（ユーザーのみ）
- `paper_trading` フラグをコードで変更しない
- `run_once_v9.py` をユーザー確認なしに実行しない
- `config/bitget_keys.json` の中身をログ・画面に出力しない
- `state/` 配下のファイルを直接書き換えない（runner経由のみ）
- `cat/indicators.py` / `cat/const.py` を変更しない

---

## AI行動ルール（MUST）

- 変更前に差分を提示して GO を待つ
- 実行コマンドは「何を実行するか・期待する挙動・成功条件」をセットで提示
- コマンド先頭に必ず `echo "=====🚀 RUN START $(date) ====="` を付ける
- セッション終了前に `WORKFLOW.md` / `project_v9_progress.md` / `lessons.md` を更新する

---

## セッション開始時に必ず読むこと

| ファイル | 内容 |
|---------|------|
| `bitget-python-sdk-api/WORKFLOW.md` | 現在の状態・次のタスク |
| `bitget-python-sdk-api/.claude/memory/project_v9_progress.md` | 実装進捗 |
| `bitget-python-sdk-api/.claude/memory/lessons.md` | 過去の失敗・再発防止 |

---

## ファイル構成（V9）

| ファイル | 役割 | 変更可否 |
|---------|------|---------|
| `runner/run_once_v9.py` | 実行エンジン（発注・exit判定） | GO後のみ |
| `runner/replay_csv.py` | 過去CSV検証エンジン | GO後のみ |
| `strategies/cat_v9_decider.py` | エントリー判断 | GO後のみ |
| `config/cat_params_v9.json` | パラメータ（一次ソース） | GO後のみ |
| `runner/bitget_adapter.py` | Bitget SDKラッパー | 原則変更しない |
| `config/bitget_keys.json` | APIキー（機密） | 読み取りのみ |
| `cat/indicators.py` / `cat/const.py` | 指標計算・定数 | 変更しない |

---

## 急騰・異常検知時

- P23 SHORT add_count≥4 保有中に +$800/BTC/5min 以上 → 即アラート
- +$1,200/BTC/5min 以上 → 手動介入を促す
- Claude は自動で決済・注文変更を行わない
