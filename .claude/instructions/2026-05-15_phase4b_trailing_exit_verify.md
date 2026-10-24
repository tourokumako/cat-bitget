# 【タスク】Phase 4-b trailing exit 実装 verify（audit#12 波及範囲確認）

発行日: 2026-05-15
承認: まこさん（明示的 GO）
読了ゲート通過: 2026-05-15（コア5本＝WORKFLOW.md / CLAUDE.md / cc_ml_design_spec.md / handoff v5 / lessons_active.md）
self_check (A) 通過: 2026-05-15
本ルート: WORKFLOW.md 改訂11 §🔴現在のフェーズ「次のタスク」Step 1 / handoff v6 §4-1

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-15_phase4b_trailing_exit_verify.md`
- 完了報告: `.claude/instructions/2026-05-15_phase4b_trailing_exit_verify_completion.md`
- 着手前に `.claude/instructions/` 配下の直近の同種（verify・leak確認系）指示書を一覧表示し、フォーマットを踏襲すること

## このタスクの性質（最重要・厳守）

**これは「verify（確認）」タスクであり「修正」タスクではない。**
- `run_phase4b_phase5_rolling_option5.py` を**読んで、leak があるか・ないか・別の問題があるかを特定する**だけ。
- **コードを修正しない。**「ついでに直す」を禁止する（何が問題だったか追跡不能になる・CLAUDE.md L-5 1ターン1変更）。
- 修正は本ルート Step 2（trailing exit 修正後に Phase 4-b/5 再実行）で、別タスクとして行う。
- このタスクではコミットは発生しない（コード修正なし・読解と報告のみ）。

> 注: WORKFLOW.md L464 の「L274」→「L273」修正は CC が commit `339bde7` で実施済み（WORKFLOW.md 内の L274 参照はゼロ）。本指示書では扱わない。

---

## 着手前必読（省略禁止・L-179/L-180/L-181）

1. `WORKFLOW.md` §🔴現在のフェーズ（改訂11・L273-301）
2. `cc_ml_design_spec.md` §3 Exit設計（3.1-3.3）/ §8 制約・禁止事項
3. `.claude/rules/false_positive_incident_policy.md` §2 類型A（look-ahead leak）/ 類型F（proxy 偽装）/ §5 関所B（全工程の未来参照 verify・変数の因果性宣言）
4. `.claude/instructions/handoff_to_web_claude_v6_session_20260515.md` §3（audit#12 の内容）
5. `lessons_active.md` L-179（未来データ参照 leak・コメントの「look-ahead 防止」を信用しない）/ L-182（バックテスト採用ロジックの未来情報 leak）

## Step 0-1: 必読ファイル引用（読んだふり防止・false_positive_incident_policy §2 類型G）

以下を完了報告に現物引用すること。期待値と一致しない/省略 → STOP：
a. `false_positive_incident_policy.md` §5 関所B 全文（「PnL・判定の計算式の入力変数を列挙させ、各変数が推論時点 t で因果的に存在するかを1行ずつ宣言させる」の箇所）
b. handoff v6 §3 から audit#12 の「発覚内容」（trailing exit が MFE スカラーを直接 PnL に流用 → $6,499/day・勝率90.4%）の行を引用
c. `cc_ml_design_spec.md` §3.1 から trailing exit（トレーリング）の定義行を引用
d. `lessons_active.md` L-179 から「コードコメントの『look-ahead 防止』表記を信頼しない。実装で守られているかを必ず verify」の行を引用

---

## 背景（audit#12 の判定）

audit#12 は **Phase 5 の trailing exit が、未来由来の MFE スカラーを PnL 計算式に直接流用する look-ahead leak** と判定した（$6,499/day・勝率90.4%＝目標の108倍）。Phase 5 の月次 PnL 数値は無効。

このタスク（本ルート Step 1）は、その**波及範囲の確認**である。具体的には：
- audit#12 が指摘した leak は Phase 5 の Replay PnL 集計で発覚した
- しかし `run_phase4b_phase5_rolling_option5.py` は Phase 4-b（Exit 選定）と Phase 5（Replay）を**同一スクリプトで実行**している
- handoff v6 §3 は「Phase 4-b の trailing exit シミュレーションも同様の漏れの可能性（要確認）」と明記している
- → **Phase 4-b 側の trailing exit シミュレーション実装にも、同じ leak が入っているか**を確認する

---

## タスク本体：verify 手順

### V1. スクリプト全文を読む

`scripts/priority_rebuild/run_phase4b_phase5_rolling_option5.py` を `view` で全文読む（grep・部分 view での代替禁止）。総行数（`wc -l`）を完了報告に記載。

### V2. trailing exit シミュレーション部分の特定と引用

trailing exit の PnL を計算しているコード部分を特定し、該当行を**行番号付きで現物引用**する。Phase 4-b 側（Exit 選定時のシミュレーション）と Phase 5 側（Replay）の両方。コメントに「look-ahead 防止」等と書かれていても**信用せず実装で確認**（L-179）。

### V3. PnL 計算式の入力変数を全列挙し、因果性を1行ずつ宣言（false_positive_incident_policy §5 関所B）

trailing exit の PnL 計算式に入る**入力変数を全て列挙**する。各変数について以下を1行で宣言：

```
変数名 | その変数が何を表すか | 推論時点 t（ポジション保有中の各 bar）で因果的に確定済みか（YES/NO）| 根拠
```

特に確認すべき点：
- MFE / MAE 系の未来由来スカラー（変数名は `mfe_te` / `best_return` / `max_favorable` / `peak` 等、**名前は何でもありうる**。変数名 grep ではなく「その変数の中身が未来を見ているか」で判定する）が PnL 計算式に直接入っていないか
- trailing exit の「高値追従」が、各 bar を時系列順に1本ずつ進めて更新しているか、それとも保有期間全体の max を一括で取っているか（後者は未来参照）

### V4. 範囲を trailing exit に限定しない（まこさん指示「あらゆる手を尽くせ」）

trailing exit 以外も同じ §5 関所B の観点で確認する。範囲を狭めない：
- 固定 TP / 時間 Exit の PnL 計算（同じ leak パターンがないか）
- Entry 判定（rolling q99 閾値の適用が `shift(1)` で過去のみ参照か）
- Phase 5 Replay の月次集計ロジック（採用判定で期間全体ソートを使っていないか・L-182）

### V5. NET の実体確認（false_positive_incident_policy §5 関所C）

PnL 計算で `net_pnl` 等の列を作っている場合、それが**コスト控除後**か確認する：
- 手数料（exchange_spec.md の Maker 0.00014 確定値）
- Funding（8h 毎）
- スリッページ
これらが実装で実際に控除されているか、計算式を引用して示す。

### V6. 結論

V2-V5 を踏まえ、以下を明示：
- Phase 4-b 側の trailing exit シミュレーションに audit#12 と**同じ leak があるか / ないか**
- あるなら、どの変数が・どこで未来を参照しているか
- trailing exit 以外（固定TP・時間Exit・Entry・Replay集計・NET控除）に**別の問題があるか / ないか**
- 結論を「proxy」「近似」「仮定」等の語で曖昧化しない（false_positive_incident_policy §2 類型F）。leak は leak と書く

---

## 完了報告 必須証跡

1. Step 0-1 の必読ファイル引用 a-d（読んだ証跡）
2. V1: スクリプト総行数（`wc -l`）
3. V2: trailing exit PnL 計算部分の行番号付き現物引用（Phase 4-b 側・Phase 5 側 両方）
4. V3: PnL 入力変数の全列挙表（変数名 / 意味 / 推論時点 t で確定済みか YES/NO / 根拠）
5. V4: 固定TP・時間Exit・Entry・Replay集計それぞれの未来参照チェック結果
6. V5: net_pnl のコスト控除 verify（手数料・Funding・スリッページの控除箇所の引用）
7. V6: 結論（leak あり/なし/別問題・曖昧語禁止）
8. 異常値スメルテスト: このタスクは数値を生成しない（verify のみ）ため「該当なし（実装読解 verify のみ・新規数値生成なし）」と明記

### 不正防止ガード（false_positive_incident_policy.md 準拠）

- **読んだふり禁止（類型G）**: コード引用・必読引用は実際に `view` した現物とする
- **重大度の偽装禁止（類型F）**: leak・未来参照を「proxy」「近似」「仮定」で呼ばない
- **verify と fix の分離**: コードを修正しない。「直しました」を禁止する。このタスクではコミットは発生しない
- **コメント信用禁止（L-179）**: 「look-ahead 防止」等のコメントを根拠にしない。実装の動作で判定する
- **完了の自己申告禁止**: 「verify 完了」を証跡（行引用・変数表）なしに主張しない

---

## 完了後

Web Claude が完了報告をレビュー（self_check B）し、V6 の結論を確認する：
- leak あり → 本ルート Step 2「trailing exit 修正後に Phase 4-b/5 再実行」の指示書作成。修正方針が audit#9 撤回級の重大判断を含むなら監査経路を通す
- leak なし → audit#12 の波及範囲は Phase 5 のみと確定。Step 2 の修正範囲を Phase 5 に限定できるか再評価
- 別問題が見つかった → false_positive_incident_policy §4 の発見時手順に従い、まこさんに報告
