# Web Claude セルフチェック (指示書発行前・完了報告受領時に機械的に通す)

2026-05-14 監査#8 必須 5 (構造改善)・cc 側の `feedback_pre_execution_premise_check.md` (L-?) と対をなす。

## チェック A: CC に指示書を出す前

- [ ] この指示書が「spec 改訂」を含むなら、対応する「スクリプト改修」も同タスクに含めたか
      (ドキュメントだけ直してスクリプト放置を禁止・2026-05-14 案 G の implementation gap 教訓)
- [ ] 参照する数値・ファイルの「出所」をパスまで特定したか
      (フォルダ名・train/test の別・refit 前後の別)
- [ ] この指示書は前の指示書・正本 (WORKFLOW.md / cc_ml_design_spec.md / phase_compliance_checklist.md) と矛盾しないか
- [ ] 「公式 source: results/.../phaseX_summary.json」を指示書本文または完了報告テンプレートに明記したか
      (WORKFLOW.md「公式判定 source の定義」準拠・2026-05-14 監査#8 必須 3)

## チェック B: CC の完了報告を受け取った時

- [ ] 「完了」と書かれた項目を、completion report の文字でなく証跡 (grep 結果・sha256・実数値) で確認したか
- [ ] 完了報告に出てくる数値の「出所」(どのファイル・train/test) を自分で 1 つ以上 verify したか
- [ ] 「spec 改訂完了」報告なら、スクリプト側も改訂されたか grep したか
      (例: `grep CRITERION_1_POSITIVE_MIN run_phaseX.py` で改訂後 spec の値が入っているか確認)
- [ ] 数値が前提と食い違う時、自分のパス取り違えの可能性を先に潰したか
      (異なるフォルダの同名ファイルを参照していないか・例: ml_phase2/ vs ml_phase2_post_refit/)
- [ ] 公式 source (`phaseX_summary.json` の overall_pass) と完了報告の「総合判定」が一致するか

## 限界の自覚

このチェックリストは初歩ミス (出所確認・実装乖離・完了の額面受け取り) を減らすためのもの。
「Web Claude と CC が同じ結論に収束する」構造的バイアスはこれでは防げない。
**重大判断・前提に関わる判断は引き続き監査経路を通す**。

## 既存指示書テンプレへの統合

新規指示書を発行する際は本ファイルの「チェック A」を通過した旨を冒頭に記載する:
```
self_check (A) 通過: 2026-MM-DD
```

完了報告受領時は「チェック B」を通過した旨を Web Claude のレビュー文に記載する。
