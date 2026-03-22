# core_rules.md — 実装の MUST / NEVER

## NEVER（理由を問わず従う）

- `ALLOW_LIVE_ORDERS = False` を True に変更しない（ユーザーのみ）
- `paper_trading` / `allow_paper_orders` フラグをコードで変更しない
- `config/bitget_keys.json` の中身をログ・画面に出力しない
- `state/` 配下のファイルを run_once_v9.py 経由以外で変更しない
- `runner/run_once.py` / `strategies/cat_live_decider.py` は削除済み（V8完全移行完了）。復元しない
- `cat/indicators.py` / `cat/const.py` を変更しない（V9正本との一致を保証）
- ユーザー確認なしに run_once_v9.py を実行しない
- 1回のターンで2箇所以上コードを変更しない

## 実弾テスト前チェックリスト（MUST）

デモ・本番を問わず API が実際に呼ばれるコードを実行する前に、
以下を1手ずつ確認してからユーザーの GO を得る。

1. `paper_trading` フラグが `true` か（ユーザーが目視確認）
2. `ALLOW_LIVE_ORDERS = False` か（Claude が run_once_v9.py を Read）
3. `open_position.json` の現状（Claude が Read）
4. 実行コマンドをチャットに提示 → GO 待ち　← ここで必ず止まる
5. 実行後、ログを提示してユーザーと確認してから次の手へ

いきなり実行しない。確認→GO→1手、を繰り返す。

## MUST

- セッション終了前・新セッション切り替え前に `WORKFLOW.md` と `.claude/memory/project_v9_progress.md` を最新状態に更新する
- コード変更前に差分を提示してユーザーの GO を待つ
- 各 Phase のテストリスト（test_checklist.md）を全て合格してから次フェーズへ
- 全アクション（ENTRY/EXIT/NOOP/STOP/ERROR）を JSON 形式でログ出力する
- state ファイルの変化は必ずログに記録する
- API レスポンスは必ずログに記録する
- 未知の state ファイルを見つけたら削除前に必ず確認する
