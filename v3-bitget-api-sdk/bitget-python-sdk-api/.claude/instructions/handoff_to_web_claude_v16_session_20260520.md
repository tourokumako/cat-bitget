# handoff_to_web_claude_v16_session_20260520

セッション: 2026-05-20 (学習内容 v3 確定 + exchange_spec.md 準拠化)
作成者: Web Claude
保存先: `.claude/instructions/handoff_to_web_claude_v16_session_20260520.md`

---

## §0 前提認識 (v14 / v15 §0 を全件継承)

v14 §0.1〜§0.6 + v15 §0.7 / §0.8 を継承。本 v16 で **新規追加**:

### §0.9 (本セッションで判明) 「ML 設計を古い情報のまま進めた」事故と訂正

開始時の Web Claude memory に古い情報(16 ラベル / K=12/24/48/96 / Funding 0.01% 固定 / メンテ時間帯あり / n_sim 上限 718 / 削除類型 11 種)が残置しており、まこさんから「すべてやり直し」「ML 設計を古い情報のまま進めた」「28 軸でやれと言った(→ 23 軸の打ち間違い)」と指摘。

**経緯**:
1. コア 5 本 + 関連 15 本(合計 20 本・7,328 行)を全文 view で読了ゲート通過
2. まこさんが学習内容 v3 (修正版) を提示・「メンテはナシ」のみ訂正済 + 「exchange_spec.md が正・学習内容を合わせろ」と指示
3. Web Claude が学習内容 v3 と exchange_spec.md の矛盾箇所 7 件を洗い出してまこさんに確認
4. まこさん OK → 7 件機械反映で学習内容 v3 完成版確定
5. memory #28 を学習内容 v3 完成版に合わせて update

**対応**: 次セッション開始時に **memory が古くても学習内容 v3 文書 + handoff v16 を優先参照**。memory と正本文書が矛盾したら正本文書を優先(self_check §「知識として持っているのに起動されない」L174 同型再発防止)。

---

## §1 本セッション確定事項

### §1.1 学習内容 v3 確定 (2026-05-20 まこさん承認)

学習内容 v3 完成版は別ファイル参照: `/mnt/user-data/outputs/learning_design_v3_final.md` (本セッション生成・exchange_spec.md 準拠化済)。

**v3 = v2 + exchange_spec.md 準拠化 (7 件機械反映)**:

| # | 修正箇所 | 旧 (v2) | 新 (v3) |
|---|---|---|---|
| 1 | 本番再現性 #6 | メンテ時間帯 火/水/木 05-08 UTC | メンテなし (24/7) |
| 2 | D-η Funding | 8h 毎 0.01% | median +0.0002%/8h baseline / p95 0.01%/8h stress |
| 3-8 | A-6 MAX_ADDS n_sim 上限 | 718 / 359 / 239 / 143 / 89 / 71 | **150 / 75 / 50 / 30 / 18 / 15** (maxPositionNum=150 反映) |
| 9 | 制約セット | MAX_ADDS × n_sim ≤ 718 | MAX_ADDS × n_sim ≤ 150 |
| 10 | B-8 cap | (物理上限言及なし) | MAX_ADDS × n_sim ≤ 150 絶対遵守を追記 |
| 11 | 削除類型 | 11 種 (#10 メンテ時間帯混入 / #11 価格依存違反) | **10 種** (旧 #10 削除・旧 #11 を #10 に繰り上げ) |

**変更なし (まこさん明示確認)**:
- 23 軸振り分け表の構造
- A-6 MAX_ADDS バリエーション表構造
- per-add 配分 6 方式並列
- add トリガ条件
- Phase 別優先順位 (Phase 0-1〜Phase 6-7)
- 手動 Priority スタートライン到達 verify 表

### §1.2 exchange_spec.md は正本・触らない (まこさん明示指示)

学習内容 v3 と exchange_spec.md の整合性は「exchange_spec.md が正・学習内容を合わせる」が確定方針。今後 exchange_spec.md の数値(Funding / 最大同時保有 / 最大レバ等)を学習内容 v3 側から再判断・再議題化しない。

### §1.3 memory #28 更新 (本セッション)

旧 memory #28 (「ラベル 28・特徴量 1414・現フェーズ Phase 0 v3 Step 3d 待ち」のみ) → 新 memory #28 (上記 7 件機械反映の数値を含む完全版)。

---

## §2 本セッション commit / 成果物

| 成果物 | パス | 内容 |
|---|---|---|
| 学習内容 v3 完成版 | `/mnt/user-data/outputs/learning_design_v3_final.md` | exchange_spec.md 準拠化済・本セッション生成 |
| memory #28 | (Web Claude memory) | 学習内容 v3 完成版に合わせて update |
| handoff v16 | `.claude/instructions/handoff_to_web_claude_v16_session_20260520.md` | 本ファイル |

本セッションはコード commit なし (設計確定 + ドキュメント生成のみ)。

---

## §3 pending tasks (次セッション優先順位固定)

### §3.1 優先 1: Phase 0 v3 Step 3d フル実行 (未着手なら) or 完了レビュー本体 (完了済なら)

v15 §3.1 継承。Phase 0 v3 Step 3d (`build_labels_pct.py` フル実行・8-12h 想定) の現状確認:
- 実行済なら → Phase 0 完了レビュー本体に進む (公式 source 物理 view 義務・v14 §4.9 / v15 §4.13)
- 未実行なら → コマンド実行 (handoff v13 §3.1 参照)

レビュー観点 (v14 §3.3 / v15 §3.1 継承):
- 行数差分 (起点 07:55 → 23:55 / 終点 03-31 15:50 → 03-30 23:50 各 192 bars) の実装上の理由
- K288 max 35-40% の該当日付特定
- ラベル対称性 (LONG_MFE_pct = SHORT_MAE_pct) の公式 source 実物 verify
- 異常値スメル ⚠️ 2 件が §0 サマリ「全条件クリア」に反映されていない問題
- メンテ flag 不使用前提でのレビュー

### §3.2 優先 2: Phase 0 v3 spec sweep 本体 (v14 §3.2 / v15 §3.2 継承)

cc_ml_design_spec.md / WORKFLOW.md / phase_compliance_checklist.md の **「16 ラベル」→「28 ラベル」機械反映**が未完。

**追加修正対象 (本セッション学習内容 v3 確定で発生)**:
- cc_ml_design_spec.md §5 Phase 5-e Funding は v15 で更新済 (median baseline) → 学習内容 v3 と整合済
- phase_compliance_checklist.md L94「Funding rate 動的化」暫定値 → median baseline に置換要
- ml_axis_catalog.md L576「Funding Rate: 8h 毎 0.01%」→ median baseline に置換要
- 2026-05-19_ml_design_proposal_v2.md / Phase -1 addendum / self_check addendum の古い記述 (火/水/木メンテ / Funding 0.01% / 最大レバ 125x) は「v2 系・archive 注記追加」または「v3 化で機械反映」

機械的タスク (新規判断ゼロ) なので light テンプレ (80-120 行) で書く (memory ルール 24 / L-198)。

### §3.3 優先 3: Phase 1 着手指示書発注

Phase 0 完了レビュー合格後 → **学習内容 v3 §B-15 準拠**で Phase 1 (28 ラベル LightGBM 学習) 指示書発注。

**学習内容 v3 で確定済の Phase 1 要件**:
- B-15 目的関数: RMSE + 直接 PnL (NET_PnL_pct) + Sharpe maximizing custom objective を **Phase 1 から並列実装**
- B-9 ハイパラ Optuna: num_leaves={7,15,31,63,127} × max_depth={3,5,7,10,-1} × min_data_in_leaf={50,100,200,500}
- B-12 特徴量変換: Fractional diff / PCA / Wavelet / MTF 4 方式 (監査経路で比較)
- 28 ラベル独立回帰モデル (旧 16 ラベル版は archive)

監査経路 (audit#18) で custom objective 数式 verify を経由 (handoff v13 §3.4 継承)。

### §3.4 (将来) Phase 7-d 着手前 maxMarketOrderQty paper trading test

v15 §3.4 継承。`phase_compliance_checklist.md` Phase 7-d セクション記録済。

---

## §4 次セッション Web Claude (私) への警告

v14 §4.1〜§4.13 + v15 §4.11〜§4.13 を全件継承。本 v16 で **新規追加**:

### §4.14 (本セッション §0.9) memory が古くても正本文書を優先

開始時の memory に古い情報 (16 ラベル / K=12/24/48/96 / Funding 0.01% / メンテあり / n_sim 718 / 削除類型 11 種) が残置していたら、**memory より正本文書 (学習内容 v3 完成版 + exchange_spec.md + handoff v16) を優先参照**。memory と正本が矛盾したら正本側の数値で動く。

検知方法:
- 学習内容 v3 完成版を毎セッション開始時に view (本ファイル §1.1 参照)
- memory ルール 23 / 27 / 28 と正本の数値を機械的に照合

### §4.15 (本セッション) exchange_spec.md と学習内容の整合性議論を勝手にしない

「exchange_spec.md が正・学習内容を合わせる」がまこさん確定方針。学習内容内の数値と exchange_spec.md の数値が違って見えても、Web Claude が勝手に「整合性問題」と騒がない・「Phase 5 着手時に再判断」のような越権メモを残さない。整合性確認はまこさんが判断する。

### §4.16 (本セッション) 修正箇所の事前確認

外部仕様 (exchange_spec.md) と学習内容の不整合を見つけたら、勝手に書き換えず **まこさんに矛盾箇所を一覧で提示して指示を仰ぐ**。本セッションで成功したパターン: 矛盾 7 件を表で提示 → まこさん OK → 機械反映。

---

## §5 セッション履歴サマリ (本セッション 2026-05-20)

| 時刻概算 | 出来事 |
|---|---|
| 開始 | handoff v15 受領 (実体はまこさん指示「すべてやり直し」が起点) |
| 序盤 | まこさんから「ML 設計を古い情報のまま進めた」「28 軸でやれと言った (→ 23 軸の打ち間違い)」「必要書類を全部読め」と複数回叱責 |
| 中盤 | コア 5 本 + 関連 15 本 (合計 20 本・7,328 行) を全文 view で読了ゲート通過 |
| 中盤 | まこさんが学習内容 v3 (修正版) を提示 + 「メンテはナシ」訂正済 |
| 中盤 | Web Claude が学習内容 v3 完成版・memory update・handoff v16 の 3 つを並走実施提案 |
| 中盤 | Web Claude が「Funding 整合性注記を Phase 5 で再判断」と越権メモを書き、まこさんから撤回指示 |
| 後半 | まこさんから「私の意図を書き出せ」指示 → Web Claude が意図 6 項目書き出し → OK |
| 後半 | まこさんから「exchange_spec.md が正・学習内容を合わせろ」明示指示 |
| 後半 | Web Claude が矛盾箇所 7 件を表で提示 → まこさん OK |
| 後半 | 学習内容 v3 完成版 .md 生成 → memory #28 update (1 回 500 文字超過失敗 → 短縮版で成功) → 完成版 present_files |
| 終盤 | handoff v16 作成 (本ファイル) |

---

## §6 改訂履歴

| バージョン | 日付 | 内容 |
|---|---|---|
| v14 | 2026-05-20 | Phase 0 v3 完了報告レビュー + L-196 緊急訂正 |
| v15 | 2026-05-20 | audit#19 全工程完了 + L-198 指示書サイズ規律 |
| **v16** | **2026-05-20** | **学習内容 v3 確定 (exchange_spec.md 準拠化・7 件機械反映) + memory #28 update + §0.9 「ML 設計を古い情報のまま進めた」事故と訂正記録 (本ファイル)** |
