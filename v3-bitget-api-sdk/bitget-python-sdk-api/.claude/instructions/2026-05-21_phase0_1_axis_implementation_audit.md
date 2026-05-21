# 【CC タスク】Phase 0-1 軸実装監査 + Phase 0 v4 + Phase 1-a 再学習 実装計画書作成

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-21 |
| 発行者 | まこさん (Web Claude は本タスクで設計者から外れ・機械照合役のみ) |
| タスク種別 | full 枠 (300-400 行) |
| 想定所要 | 実装計画書作成: 1-2 時間 / Phase 0 v4 再生成 + Phase 1-a 再学習: 後続別タスク |
| 保存先 | `.claude/instructions/2026-05-21_phase0_1_axis_implementation_audit.md` |
| 完了報告 | `.claude/instructions/2026-05-21_phase0_1_axis_implementation_audit_completion.md` |

---

## §0. 本タスクの背景 (CC が必ず読む)

### §0.1 本タスクが発注された経緯

2026-05-15 〜 2026-05-21 の 1 週間、Web Claude (ML 設計担当) が下記の同型ミスを 4 回繰り返した:

1. **2026-05-15**: handoff v7 で「未学習 8 指標追加 = Layer 1 ④ 最優先」を確定 → 後続セッションで実施されず放置
2. **2026-05-19**: ML 設計 v2 (Tier 1-5) 提案 → まこさんから「23 軸全部一気が正解とは限らない」と却下・「核は A-1×A-3×A-4×A-5」決めつけで撤回
3. **2026-05-20**: learning_design_v3.md 確定 (まこさん承認) → §Phase 別優先順位 で「Phase 0-1 で扱う軸 = A-1 / A-3 / A-4 / A-5 / B-12 / B-14 / B-15」と明記
4. **2026-05-19〜21**: Phase 0 v3 / Phase 1-a / Phase 1-c を Web Claude が指示書発注 → **正本 (learning_design_v3) に明記された 7 軸のうち 4 軸を指示書に書かなかった**

結果、Phase 1-c smoke で「entropy lift 2.2% = ボラ予測しかできない」と判明したが、これは learning_design_v3 通りの実装をしていない状態での smoke 失敗であり、学習設計の限界判定として根拠不足。

### §0.2 本タスクの目的

**learning_design_v3.md §Phase 別優先順位 (L107-116) に書かれた Phase 0-1 行の 7 軸を、正本通りに実装する**。

新規設計は一切行わない。learning_design_v3.md 本文をそのまま実装仕様として使う。Web Claude の判断・推奨・提案は本タスクで参照しない。

### §0.3 Web Claude (ML 設計担当) の本タスクでの位置づけ

本タスクで Web Claude は **設計者から外れ・機械照合役** に降格。

- ❌ Web Claude がやらないこと: 新規軸追加・正本指定の軸削減・優先順位変更・実装方針改変
- ✅ Web Claude がやること: CC 完了報告と learning_design_v3.md の機械照合 (差分があれば指摘するのみ)

---

## §1. 着手前必読 (機械的証跡 = wc -l + 該当行物理引用 を完了報告に必須記載)

| # | ファイル | 必読範囲 | 確認内容 |
|---|---|---|---|
| 1 | `.claude/memory/learning_design_v3.md` | **全文 174 行** | §Phase 別優先順位 L107-116 + §A-1 / §A-3 / §A-5 / §B-12 該当行 |
| 2 | `WORKFLOW.md` | §🔴 現在のフェーズ | Phase 0 v3 完了 commit (4df8924) 後の状態確認 |
| 3 | `CLAUDE.md` | L130-135 必読リスト | プロジェクト全体ルール最高位 |
| 4 | `.claude/rules/false_positive_incident_policy.md` | §0-1 / §0-2 / §2 類型 G / 類型 H | 2 大絶対規定 + 虚偽報告 + 運用上限逸脱の禁止 |
| 5 | `.claude/rules/exchange_spec.md` | 全文 | 本番再現性 7 項目 (audit#19 確定値) |
| 6 | `.claude/instructions/handoff_to_web_claude_v17_session_20260521.md` | §1.4 / §1.5 / §1.6 | Phase 1-a 観測 (K288 定数寄り) + Phase 1-b NO-GO + audit#18 |
| 7 | 既存指示書 (参考): `.claude/instructions/2026-05-19_ml_implementation_phase0_1.md` | 該当部分のみ | Phase 0 v3 で実装した内容 (= 本タスクで「現状実装」として記録する基準) |

---

## §2. タスク本体 (3 ステップ)

### Step 1: 7 軸の現状実装状態調査 (機械的・新規判断ゼロ)

learning_design_v3.md §Phase 別優先順位 L107-116 で Phase 0-1 行に指定された **7 軸** について、各軸の正本指定内容と現状実装を 1 行ずつ表で照合する。

**正本指定 (learning_design_v3.md 引用・行番号付き)**:

| 軸 | 正本行 | 正本指定内容 |
|---|---|---|
| A-1 Entry 指標 | L34 | `A 全投入: 1432 指標 + 業界カタログ拡張 (TA-Lib / pandas-ta / Murphy / Lopez de Prado)` |
| A-3 閾値・パラメータ | L36 | `A 全投入 + C 学習: パラメータ違い並列展開 + 閾値は LightGBM 自動分割 + D-γ 統合 (location_prev / entry_risk_score を特徴量化)` |
| A-4 時間軸 K | L37 | `B 探索: K = {6, 12, 24, 48, 96, 144, 288} 並列 = 14 ラベル` |
| A-5 時間足 bar | L38 | `A 全投入: 6 TF (5m/15m/30m/1h/4h/1d) + 1w/1M 追加 = 8 TF (3m は Layer 2 検討・1m は禁止)` |
| B-12 特徴量変換 | L45 | `A 全投入 + B 探索: Fractional diff (d=0.3/0.5) + PCA + Wavelet 追加 + MTF 4 方式 (ffill / 5m rolling / アンカー補間 / 複数特徴量分解) を監査経路で比較` |
| B-14 学習データ範囲 | L47 | `D 期間固定 + B 探索: 期間分割は固定 (train 2021-04〜2024-12 / 仮 test 2025 / 本 test 2026 Q1) + Walk-forward / Purged K-fold / CPCV を Layer 3 で探索` |
| B-15 目的関数 | L48 | `D 主目的固定 + B 探索: 合格 = 月次 NET ≥ $1,900 全月固定 / train 目的関数は RMSE + Triple Barrier 3 クラス multiclass + EV フィルタを並列実装 (Sharpe maximizing は Phase 2 以降に延期)` |

**CC がやること**:

各軸について以下を表形式で出力 (合計 7 行):

| 軸 | 正本指定 (L#引用) | 現状実装 (Phase 0 v3 + Phase 1-a 完了時点) | 未実装項目 | 出典 (実装ファイル/コミット) |
|---|---|---|---|---|

例 (A-1 の場合):

| A-1 | L34 `1432 指標 + 業界カタログ拡張 (TA-Lib / pandas-ta / Murphy / Lopez de Prado)` | `build_labels_pct.py` で 1432 指標 (Phase 0 v3 commit 4df8924) | **業界カタログ拡張未実施** (TA-Lib 全 158 関数 / pandas-ta 全 130 関数 / Murphy 系 / Lopez de Prado AFML 系から未学習分の抽出が 0 件) | scripts/priority_rebuild/build_labels_pct.py (commit 4df8924) |

**禁止事項**:
- 「これも追加した方が良い」「これは外しても良い」等の判断追記
- learning_design_v3.md に書かれていない指標・変換・時間足の提案
- Web Claude が過去セッションで言及した「8 指標」等の部分集合への矮小化

### Step 2: 未実装項目の実装計画書作成

Step 1 で抽出された未実装項目について、**learning_design_v3.md 本文をそのまま実装仕様として使った実装計画書** を作成する。

**実装計画書の必須記載事項**:

1. **Phase 0 v4 再生成タスク**
   - A-1 業界カタログ拡張: TA-Lib / pandas-ta / Murphy / Lopez de Prado の各ライブラリから未学習関数を抽出する手順 + 追加列数見積もり + 価格非依存性 verify (% / 比率 / 無次元か)
   - A-3 パラメータ違い並列展開: 既存指標 (RSI / RCI / Stochastic / BB / ATR / MACD 等) について手動 Priority カバレッジ穴埋め + 一般的パラメータレンジで並列展開 + 追加列数見積もり
   - A-5 1w 足 + 1M 足追加: 既存 6 TF 指標を 2 TF 拡張する実装手順 + 追加列数見積もり
   - B-12 特徴量変換 4 方式: Fractional diff (d=0.3, 0.5) / PCA (上位 N 成分) / Wavelet (Daubechies 等) / MTF 4 方式 (ffill / 5m rolling / アンカー補間 / 複数特徴量分解) の実装手順 + 追加列数見積もり
   - leak 4 点チェック (新規追加列全てに対して): shift(-N) / L-128 MA70 ルックアヘッド / L-179 fractal j±2 / center=True rolling

2. **Phase 1-a 再学習タスク**
   - 既存 Phase 1-a スクリプトを Phase 0 v4 出力で再実行
   - 14 ラベル (LONG_MFE/MAE × K=7) 既存 artifact は **再生成不要** (Phase 0 v3 §3.2 bit-exact 確認済・対称性活用)
   - 合格基準: rmse_ratio < 1.5 が 14/14 + leak 全 PASS

3. **観察軸 (合否ではなく現象記録)**
   - top20 に新 4 軸追加分のいずれかが入っているか (= ボラ系 dominance が下がったか)
   - K288 LONG_MFE pred_std/label_std が Phase 1-a 旧値 0.07 から改善したか
   - atr14_pct__5m dominance が Phase 1-a 旧値 33-65% から下がったか

4. **想定所要時間 + 追加列数合計見積もり**

**実装仕様の出所制約**:
- A-1 / A-3 / A-5 / B-12 の各実装仕様は **learning_design_v3.md 本文の文言をそのまま引用** する (新規言い換え禁止)
- 引用箇所は learning_design_v3 の行番号付き

### Step 3: 完了報告作成 + Web Claude 機械照合への引き継ぎ

完了報告は `.claude/instructions/2026-05-21_phase0_1_axis_implementation_audit_completion.md` として保存し、以下を含める:

- §1 7 軸現状実装表 (Step 1 成果物)
- §2 未実装項目実装計画書 (Step 2 成果物)
- §3 完了報告必須証跡 (本指示書 §4 参照)
- §4 Web Claude 機械照合用チェックリスト (§5 参照)

---

## §3. 禁止事項 (false_positive_incident_policy §2 類型 G / 類型 H 該当)

1. **新規設計の追加禁止**: learning_design_v3.md に書かれていない軸・指標・変換・時間足を実装計画に含めない
2. **正本指定の差し引き禁止**: learning_design_v3.md に書かれている軸を「実装難度が高い」「他軸で代替可能」等を理由に削減しない
3. **Web Claude 判断の参照禁止**: 過去セッションで Web Claude が提案した「8 指標」「Tier 1-5」「核は X」「+1200-2000 列」等の表現を本タスク完了報告に登場させない
4. **「読んだフリ」「確認したフリ」禁止**: 必読 7 ファイルの物理引用 (機械的証跡) を完了報告に必須記載
5. **本番再現性 7 項目違反禁止**: 新規追加列が exchange_spec.md 仕様 (本番再現性) に違反しないことを 1 列ずつ verify

---

## §4. 完了報告必須証跡 (7 点)

1. **着手前必読 7 ファイルの機械的証跡**: 各ファイルの `wc -l` + sha256 + 該当行物理引用
2. **7 軸現状実装表 (Step 1)**: 表形式・正本行番号付き
3. **未実装項目実装計画書 (Step 2)**: learning_design_v3 本文引用付き・行番号明記
4. **追加列数合計見積もり**: A-1 / A-3 / A-5 / B-12 の各内訳 + 合計
5. **価格非依存性 verify**: 新規追加列全てが % / 比率 / 無次元 / BTC 単位のいずれかであることを 1 列ずつ確認
6. **leak 4 点 verify 計画**: 新規追加列に対する leak チェック手順
7. **self-grep 結果**: 完了報告内に「新規」「提案」「推奨」「私の判断」「Web Claude」「8 指標」「Tier」「核は」等の禁止語彙が含まれていないことを self-grep で確認

---

## §5. Web Claude 機械照合用チェックリスト (完了報告受領後・Web Claude 実施)

Web Claude は CC 完了報告受領後、以下のチェックリストのみ実施する (新規判断追加禁止):

| # | 照合項目 | 判定基準 | 違反時の対応 |
|---|---|---|---|
| 1 | 7 軸全て表に記載されているか | A-1 / A-3 / A-4 / A-5 / B-12 / B-14 / B-15 の 7 行 | 不足軸を CC に指摘 |
| 2 | 各軸の「正本指定」が learning_design_v3 該当行と bit-exact 一致するか | 引用文字列 = 正本文字列 | 不一致を CC に指摘 |
| 3 | 未実装項目が正本指定と矛盾していないか | 「未実装」と書かれた項目が実は実装済でないか / 「実装済」が実は未実装でないか | 誤分類を CC に指摘 |
| 4 | 実装計画書の各項目が learning_design_v3 本文引用に基づいているか | 引用なき新規記述が含まれていないか | 新規設計を CC に指摘 (本タスクの趣旨違反) |
| 5 | 価格非依存性 verify が新規追加列全てに対して実施されているか | 列ごと 1 行 verify | 漏れを CC に指摘 |
| 6 | 禁止語彙 self-grep が実施されているか + 全件 0 件か | grep 結果記載あり + 全件 0 件 | 残存語彙を CC に指摘 |
| 7 | 機械的証跡 (必読 7 ファイル wc -l + 物理引用) が記載されているか | 7 ファイル全て | 不足を CC に指摘 |

**Web Claude が機械照合中にやらないこと**:
- 「これも追加した方が良い」等の追加提案
- 「これは外しても良い」等の削減提案
- 軸の優先順位変更
- 実装方針の改変

機械照合 PASS 後の動き: まこさんに「機械照合 PASS」報告 → まこさんが Phase 0 v4 再生成タスクの発注判断。

---

## §6. 本タスク完了後の動き

| Step | 担当 | 内容 |
|---|---|---|
| 1 | CC | 本指示書実行 → 完了報告提出 |
| 2 | Web Claude | 機械照合 (§5 チェックリスト) のみ実施 |
| 3 | まこさん | 機械照合 PASS 後、Phase 0 v4 再生成タスクの発注判断 |
| 4 | (将来) | Phase 0 v4 再生成 → Phase 1-a 再学習 → 結果に基づき Phase 1-c 再開判定 |

Phase 1-c smoke 結果 (entropy lift 2.2%) の解釈は、Phase 0 v4 + Phase 1-a 再学習結果が出てから再判定する (現時点では「learning_design_v3 通りの実装をしていない状態での smoke」のため判定材料として不十分)。

---

## §7. handoff v17 への追記事項 (本タスク完了時に CC 側で実施)

本タスク完了 commit に以下を含める:

- `.claude/instructions/handoff_to_web_claude_v17_session_20260521.md` §3 に新規項目追加:
  ```
  ### §3.0 (最優先・本セッション末確定) Phase 0-1 軸実装監査タスク

  2026-05-21 にまこさんが CC へ直接発注。Web Claude は本タスクで設計者から外れ・
  機械照合役のみ。背景: Web Claude が learning_design_v3 §Phase 別優先順位 で
  「Phase 0-1 で 7 軸全部入れる」と確定したにもかかわらず、Phase 0 v3 / Phase 1-a /
  Phase 1-c で 4 軸 (A-1 / A-3 / A-5 / B-12) を実装しなかった構造的問題への対処。

  詳細: .claude/instructions/2026-05-21_phase0_1_axis_implementation_audit.md
  ```

- Web Claude の役割降格 (設計者 → 機械照合担当) を明文化

---

## §8. 想定 Q&A

**Q1**: 新規設計禁止と言っても、「業界カタログ拡張」「パラメータ違い並列展開」を具体化する時点で判断が入るのでは?

**A1**: 「具体化」は learning_design_v3 本文の文言を物理引用した上で、その文言に書かれた範囲内で実装する。例えば A-1 は `TA-Lib / pandas-ta / Murphy / Lopez de Prado` と書かれているので、これら 4 ライブラリ以外を追加しない。各ライブラリ内のどの関数を入れるかは「未学習分を全て」が原則で、選別判断は入れない (全関数を valid な特徴量として処理可能か実装側で機械判定)。

**Q2**: 追加列数が膨大 (数千列) になる場合、計算リソース制約で全部入らないかもしれない。

**A2**: その場合は実装計画書に「リソース制約により段階実装」と明記し、段階の根拠 (メモリ上限 / 学習時間上限) を数値で示す。判断基準は技術制約であって「Web Claude の推奨」ではない。

**Q3**: B-14 (学習データ範囲) に Walk-forward / Purged K-fold / CPCV が「Layer 3 で探索」と書かれているが、本タスクの範囲内か?

**A3**: 範囲外。learning_design_v3 §Phase 別優先順位 で B-14 は「期間固定」部分のみが Phase 0-1 で扱われ、Walk-forward 等は Layer 3 (= 後続フェーズ)。本タスクでは「期間固定 = 実装済」と記載するのみ。

**Q4**: B-15 (目的関数) で Triple Barrier multiclass + EV フィルタが Phase 1-c で smoke 失敗している。本タスクで再判定するか?

**A4**: 再判定しない。本タスクの目的は「Phase 0-1 で扱う 7 軸を learning_design_v3 通りに実装すること」であり、目的関数の妥当性判定は Phase 0 v4 + Phase 1-a 再学習後に別タスクで実施。

---

## §9. 連絡先 / エスカレーション

本指示書の解釈で疑義が生じた場合:
- まこさんに直接質問 (Web Claude を経由しない)
- learning_design_v3.md 本文の引用で答えられる質問のみ受付 (新規設計につながる質問は受付不可)

---

以上。
