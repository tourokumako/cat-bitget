【/audit 起動依頼】audit#15 — 道B採用判断・失敗データ記録項目・ML学習内容記録項目の独立審査
(2026-05-15・Phase 5 結果確定後の路線判断と記録項目設計)

---

## ⚠️ 新セッション監査者へ（最初に読むこと）

このセッションは監査履歴を完全 reset した独立セッションです。過去 audit の context は引き継いでいません。以下を厳守してください：

- **関連ファイルを自分で read すること**: 本依頼書末尾「参照ファイル」を要約に頼らず原本を読む
- **過去 audit の framing に anchor しないこと**: 下記「経緯」は事実共有のための最小限の要約。過去監査の結論を所与とせず、必要なら過去 audit 結果ファイルそのものを読んで独立に再評価してよい
- **本依頼書を書いた Web Claude の結論・自己申告に同調しないこと**: 本依頼書は Web Claude が「自分の判断に独立評価をかけてほしい」と依頼するもの。Web Claude が自分のバイアスを自分で塞げていない可能性を前提に審査する
- **特に問4 は Web Claude が自分の判断（道B採用）を事後追認している可能性が高い**: 経緯を読んで、Web Claude の判断にバイアスがないか独立評価する

### 経緯（最小限・事実共有）

**2026-05-15 セッション**で以下が発生・確定：

1. audit#12 で trailing exit leak 確定（Phase 5 PnL 無効・$6,499/day = 目標108倍）
2. ガバナンス文書整備（false_positive_incident_policy.md / web_claude_self_check.md・commit a8aa804）
3. 正本矛盾解消（cc_ml_design_spec §1.6.2 rolling採用へ撤回・handoff v6・commit 3d2b077）
4. Prime Directive 5箇所埋め込み（commit fe41b8e）
5. trailing exit / fixed_tp の本番再現可能な実装に書き直し（Phase 5 v2 → 結果 $186,769 だが**ポジション上限0.12BTC合計を 19倍突破**していたことが Web Claude のレビューで発覚）
6. 第二絶対規定（ポジション上限0.12BTC合計厳守）6箇所埋め込み（commit 235633c）
7. Phase 5 v3 を合計0.12BTC厳守で再実行（CSV書き出しバグ修正後の最終結果）

**Phase 5 v3 の最終結果（leak フリー・規定遵守下）**:
- 合計 net_pnl: -$985.35
- 月次達成（≥$1,900）: **0/12 ヶ月**
- 勝率: 53.39% (5705/10686)
- 月次最大: $1,265（2025-10）
- 月次最小: -$1,136（2025-07）
- no_trade率: 87%（position_limit 70,146 / min_size 581 / executed 10,686）

最高の月でも月次$1,900 に届かない状態。

**まこさんの方針確認（直近のやり取り）**:
- 月次NET ≥ $1,900 は絶対の数字・ぶらさない最低限
- 見込みのない路線で続けない
- 期限なし

**Web Claude の現状路線評価**:
- 強い4 combo の合計 +$5,176・最高 combo は K12_SHORT_q90-q95 勝率72.6%
- 「選別＋配分最適化」で2-3倍の改善が現実的上限と見積もり
- 月次$1,900 達成には**約4.4倍**の改善が必要
- 結論: 現状の cc_ml_design_spec 路線（LightGBM × 1432指標 × MFE/MAE予測）の月次$1,900達成見込みは低い

**Web Claude が提案し、まこさんが選んだ道**:
- **道A**: 今すぐ設計組み直し
- **道B**: Phase 6-b まで完走して「なぜダメだったか」を記録し次に活かす ← **まこさんが選択**

ただし Web Claude は正直に注記済み: 「道B 推奨が、まこさんが先に道B寄りの発言をした後の追認である」可能性。

### 過去 audit 結果ファイルの参照先

- audit#12 監査結果（trailing exit leak）: `results/priority_rebuild/` 配下
- audit#14 監査結果（ガバナンス文書審査）: 同上
- 過去全 leak 記録: `results/priority_rebuild/leak_incident_20260513.md`
- 過去教訓: `.claude/memory/lessons_active.md`
- 過去事故8件記録: `.claude/rules/false_positive_incident_policy.md` §3

---

## 監査対象（4問）

### 問1: 失敗データ記録項目の網羅性と優先度（最重点）

**道B（Phase 6-b まで完走）において、次の ML 設計判断に最も有効な「失敗データ」記録項目は何か。**

Web Claude が提案している記録項目:

#### 数値記録（毎 Phase）
- 月次 PnL（fires・traded・no_trade・net_pnl・勝率）
- combo別損益（19 combo それぞれの traded・net・勝率・寄与度）
- exit_type別損益（trailing/fixed_tp/time_exit それぞれの寄与）
- no_trade 統計（position_limit / min_size / cap 到達 等の理由別）
- DD（最大ドローダウン）・連敗記録・連勝記録
- 月別の勝率分布・PnL分布・combo別の月次変動

#### 構造記録（Phase完了時）
- 機能した要素 / 機能しなかった要素
- 期待と実測の乖離

#### 設計起因の記録（路線完走時集約）
- LightGBM 単体の構造的限界
- MFE/MAE 予測の捉え方
- 1432指標全投入の影響
- K窓4種固定の影響
- 5分足単軸の限界
- 強い combo がなぜ全体合計を救えなかったか

監査依頼:
- 上記が**次の ML 設計判断に必要な情報として網羅的か**を独立評価
- **抜けている項目**を最大限提示してほしい
- **不要な項目**があれば指摘してほしい
- 優先度（必須 / 推奨 / 任意）を独立に判定してほしい

### 問2: ML 学習内容記録項目の選定にバイアスがないか

**現状の ML が何を学習したかを記録する項目について、Web Claude が a〜g を列挙し a/b/c/f/g を推奨した。この選定に Web Claude のバイアスが入っていないかを独立評価する。**

Web Claude が列挙した a〜g:
- a. どの指標が判断に効いたか（特徴量重要度トップ20）
- b. どんなパターンの時にエントリーすると判定したか（決定木の主要分岐）
- c. 予測値の分布（ヒストグラム）
- d. 学習データでの予測精度の推移（train/valid スコア推移）
- e. 学習データ vs 仮テスト vs 本テストで予測の傾向がどう変わったか
- f. ML の予測 vs 実際の市場の結果（予測の的中度）
- g. 各 combo が学習した「強み」の特徴

Web Claude の推奨: a/b/c/f/g（d/e は内部 verify として残す程度）

監査依頼:
- a〜g の中から、または a〜g 外から、**次の ML 設計判断に最も有効な記録項目を独立判定**
- Web Claude の「a/b/c/f/g 推奨」に**監査されにくい曖昧な項目を選ぶバイアス**が入っていないか
- 「次の設計で本当に効く項目を抜かしていないか」（例: モデルが学んだ非線形相互作用・特定の市場局面での予測の崩れ方・予測信頼度の calibration 状況など）
- 機械学習・統計の標準的観点（permutation importance・SHAP・partial dependence・calibration plot・cumulative information gain 等）から見て、抜けている観点があるか

### 問3: 「やったふり」を許さない記録の形式

**監査が問1・問2 で「これは必須」と判定した記録項目を、CC が虚偽報告（false_positive_incident_policy §2 類型G）できない形に CC 指示書をどう書くべきか。**

参考: 今セッションで Web Claude が用いた防止策
- 機械的証跡（wc -l・位置指定の現物引用・grep 結果・sha256・実測値）
- 異常値スメルテスト無条件発動（関所A の4数値条件）
- 独立再集計（Web Claude が CSV を独立再集計して CC の数字と照合）

監査依頼:
- 各記録項目について、**機械的証跡として何を CC に出させれば「やったふり」を物理的に防げるか**を独立提案
- Web Claude の既存防止策に**抜けがあるか**
- 「数値は正しいが解釈で恣意的な切り出しをする」類のずるさ（例: 不利な combo を集計から落とす・期間を恣意的に切る）を防ぐ追加策

### 問4: 道B採用判断の妥当性

**まこさんの目標（月次NET ≥ $1,900 必達・期限なし・見込みのない路線で続けない）に対して、道B（Phase 6-b まで完走）と道A（今すぐ設計組み直し）のどちらが妥当か。**

Web Claude の現状路線評価（再掲）:
- 現状路線の月次$1,900達成見込み低（最高月でも$1,265・選別+配分でも2-3倍が上限）
- まこさんの「見込みのない路線で続けない」方針と Web Claude の見立てが整合的なら道A が選ばれるはず
- 実際にはまこさんが道Bを選択し、Web Claude が事後追認

監査依頼:
- まこさんの目標（特に「見込みのない路線で続けない」）と道B採用は**論理的に整合するか**
- 「失敗を完走して記録する価値」が、トークン代・時間コストを正当化するか
- Web Claude の「現状路線の達成見込みは低い」見立て自体が**過剰悲観 / 過剰楽観**でないか独立判定（cc_ml_design_spec §1.6 撤退ライン・現状の数字から見て）
- 道B採用が「Web Claude が判断責任を回避してまこさんに丸投げた結果の事後追認」になっていないか
- 道B/A 以外の選択肢（例: 並行で新設計検討・現状路線を縮小して保険として残す・Phase 5-b/c/d/e の一部だけ走らせて Phase 6-b は省く 等）が有効でないか

### 問4-補: 道B採用後の保険

仮に道B採用が妥当だとしても、**完走の途中で「明らかに無駄」と判明した時に止める基準**が必要。
- どの数字が出たら「Phase 6-b まで走らせずに止める」べきか
- 撤退ラインの事前明文化（cc_ml_design_spec §1.6 既存ライン以外で）

---

## 監査者への明示的依頼

1. **問1〜4 への独立判定**を、Web Claude の自己申告に同調せず提示
2. **Web Claude が自分で塞げていない穴の最大限の提示**
   - 推奨項目選定のバイアス
   - 道B採用の事後追認構造
   - 失敗データ記録の網羅性不足
3. **問1・問2 で「必須」と判定した記録項目それぞれについて、CC 指示書での書き方の具体例**（やったふりを防ぐ機械的証跡の最小限）
4. **道B採用が妥当だった場合の「途中撤退ライン」の数値条件**を独立提案
5. **見落とし最大限提示**
   - 監査も気づいていない観点があれば、観点そのものの欠落を提示
   - 「監査も Web Claude もこの観点で見ていない」を1つでも特定できれば最大の価値

## 監査者は実装提案を出さない

WORKFLOW.md 規定通り、監査エージェントはコードを書かない・実行しない。指摘・判定のみ。
`.claude/auditor_template.md` の出力フォーマットに厳密に従うこと。

## 監査後のフロー

1. 監査結果をまこさんが受領 → Web Claude に共有
2. Web Claude が監査指摘を1件ずつ受容/却下判断 → 道B計画を改訂
3. **まこさん最終確認**（記録項目・道B採用・撤退ライン の確定）
4. Phase 5-b 指示書の作成（記録項目を CC 指示書に組み込んで）

---

## 参照ファイル

- 本依頼書（審査対象 = Web Claude の判断構造）
- `WORKFLOW.md` §🔴現在のフェーズ（改訂11）/ §🛑 2大絶対規定
- `CLAUDE.md` §目標 / §⛔ 絶対禁止
- `cc_ml_design_spec.md` §1.6（撤退ライン）/ §3（Exit設計）/ §8（制約・禁止事項）
- `.claude/rules/false_positive_incident_policy.md` §0-1/§0-2/§2/§3
- `.claude/rules/web_claude_self_check.md` チェック A/B/C
- `.claude/instructions/handoff_to_web_claude_v6_session_20260515.md`
- `.claude/memory/lessons_active.md` L-179/L-181/L-182/L-183/L-189/L-190/L-191
- Phase 5 v3 成果物:
  - `results/priority_rebuild/ml_phase5/monthly_pnl_option5_v3.csv`
  - `results/priority_rebuild/ml_phase5/replay_entries_option5_v3.csv`
  - `results/priority_rebuild/ml_phase5/phase5_summary_v3.json`
  - `results/priority_rebuild/ml_phase4_b/cluster_best_exit_option5_v3.csv`
- 過去 audit 結果: audit#12（trailing leak）/ audit#14（ガバナンス文書）
- `.claude/auditor_template.md` 観点①〜⑦
