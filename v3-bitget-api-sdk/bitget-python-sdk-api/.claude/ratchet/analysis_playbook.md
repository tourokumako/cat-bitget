# analysis_playbook.md — PDCA 分析プレイブック（原因分析の唯一の正本）

作成: 2026-06-05
位置付け: ratchet PDCA の **Check(分析)工程を業界標準で完全化**し、毎セッション同じ手順で原因分析できるようにする唯一の正本。思いつき分析を排除し、**結果データの保管場所も本書に集約**（散らばり防止）。
出典(WebSearch 2026-06-05): ドローダウン3分類 [tradealgo](https://www.tradealgo.com/trading-guides/stocks/how-to-recover-from-a-trading-drawdown-a-step-by-step-framework) / ML診断・データスライス [FutureAGI](https://futureagi.com/glossary/ml-diagnostics/)・[error analysis](https://www.analyticsvidhya.com/blog/2021/08/a-quick-guide-to-error-analysis-for-machine-learning-classification-models/) / 成績指標 [backtest metrics](https://stoic.ai/blog/backtesting-trading-strategies/) / 実験ログ=ラボノート [W&B quant lifecycle](https://wandb.ai/site/articles/architecting-alpha-the-modern-quant-lifecycle/) / 最小regime成績MRP [arxiv 2604.08356](https://arxiv.org/pdf/2604.08356)

---

## §0 3行サマリ
- 1周ごとに **score.py で採点 → report.py で分析 → ledger に記録**。
- 負けたら **「戦略/執行/regime」のどれか必ず分類**してから直す（誤診=逆効果・§2.4）。
- 結果データは `results/priority_rebuild/ratchet/` に集約。本書 §3 がカタログ。

## §1 PDCA 工程（ツール対応）

| 段階 | 何をする | ツール / 成果物 |
|---|---|---|
| **Plan(設計)** | **目標逆算ブロック＋3行ゲート（WORKFLOW Step 0 ④）通過後**、変更を**1つ**、`cat_requirements §4.6 H1-H14` 照合で設計 | `ledger.md` E エントリ / `strat_v9ml_design.md` |
| **Do(実装)** | V9不変・新規ファイル・**自己検査(assert)つき** | `gen_*` / `train_*` / `strat_*` |
| **Check(採点)** | 固定審判で月次 net（地面 $172 と比較） | `score.py` |
| **Check(分析)** | 本書 §2 バッテリーを実行・原因を §2.4 で分類 | `report.py` / `*_learned_params.json` |
| **Act(判定)** | 数字が上がれば残す／原因+分類+改善を記録 | `ledger.md`（採用 or 破棄） |

原則: **1ターン1変更** / 封印期間(2026Q1)は触らない / judge(score.py・eval_engine)は改造しない。

## §2 分析バッテリー（完全版・毎周これを全部見る）

### §2.0 多角チェックリスト v1（毎回・MUST→場面の2段・2026-06-14 まこさん＋Web Claude）

> 経緯（恥・固定）: 2026-06-14 E34 iteration-0 で「264件の損の質」だけ見て「件数1.7件/日＝レンジ戦略に対し過少」を見落とした（E8a-2 と同型の再演＝trade_analysis_methods_kb §0#1 を読まず）。**1つの発見で止めず、下の角度を順に全部くぐらせる**。MUST は省略不可、場面は該当時。**0→1→2 を最初に通す**（量・設計意図＝今回飛ばした角度）。

**【MUST：毎回・省略不可】**
- ☐ 0. 設計意図照合: 狙い（レンジ=高頻度／スキャル=小利多数／トレンド=少数大利）と実挙動が一致するか。**ズレ自体が最大の発見**。〔自分で・analyze N0〕
- ☐ 1. 量・頻度: 件数/日は妥当か。**前回比で件数 激減/急増＝最大の発見**（KB §0#1）。〔report F4／analyze N0／--vs〕
- ☐ 5. gross/net 分離: 方向で負け か 手数料負け か。〔report J〕
- ☐ 16. **leak 点検**: 好結果ほど先に shift(1)/asof 漏れを疑う。「効いた」が出たら最初にここ（CC 最致命）。〔自分で・grep〕
- ☐ 17. **計器純正**: 判定数字は改造禁止の eval_engine/score.py が出したものか（CC のその場集計を混ぜない）。〔§8.4-2.9〕
- ☐ 18. **n不足ガード**: n<30 の帯・月・regime で「効く/効かない」を断定しない。〔analyze N0 が自動フラグ〕
- ☐ 19. **結論1行宣言（主張）**: チェック全体の主張を根拠数字つき1行で（ledger【主張】・件数/日 と net を含む）。〔pdca_gate 強制〕
- （※ 11. 前後比較 --vs は pdca_gate で物理 MUST 化済み）

**【場面に応じて】**
- ☐ 2. 発火ファネル: 候補→各フィルタ→実約定で、どの条件が何件に削ったか（過しぼり）。〔戦略スクリプト出力〕
- ☐ 3. 期待値/件（勝率×平均利益−敗率×平均損失）。〔report K〕／ ☐ 4. 必要勝率 vs 実際の差。〔analyze N7〕
- ☐ 6. 分布: 少数大勝ち依存か（上位除いて残るか・件数×avg 両方）。〔report D／KB §2〕
- ☐ 7. 時間/regime: 継続不調か特定月か（最弱月=下限）。〔report F・F2〕／ ☐ 8. 入口帯別＋学習vs採点ドリフト。〔report G／analyze N4〕
- ☐ 9. 出口: 理由別net＋MAE/MFE捕捉率（業界0.6-0.75）。〔report C・I／analyze N9〕／ ☐ 10. コスト: breakeven 倍率（<1=手数料負け）。〔precheck／report J〕
- ☐ 11. 前後比較: 件数・net・avg・勝率を並べる＋限界分解。〔report K・L〕／ ☐ 12. ロバスト性: bootstrap が0をまたがない／独立simは連続×年別／IS≫OOS。〔analyze N5／KB §6〕
- ☐ 13. 原因3分類（直す前に1つ）: 戦略欠陥／執行／regime依存。〔§2.4〕
- ☐ 14. 個別読み: 大勝ち・大負け・典型負けを前後24h値動きと突き合わせ。〔analyze N6／§2.9〕
- ☐ 15. 源泉検証（勝った時こそ）: 対照実験（予測逆転）／玉単位分解。〔§2.8〕

物理化（B・2026-06-14 まこさん）: #0/#1/#18 は analyze.py N0 が自動表示＋n<30 フラグ／#19 主張1行は pdca_gate が ledger【主張】未記入で終了ブロック。中身の質はまこさんの30秒チェックが最後の砦。

### 2.1 成績指標（report.py A）
net(審判) / 月平均 / NET日次 / 勝率 / 最大DD / 最大連敗 / 日次最悪 / **Sharpe / Sortino / Profit Factor / Recovery**。
最終合格は別途 **全月 net ≥ $1,900 + DSR>0.95 + PBO<0.5**（`cat_requirements §1.2`）。

### 2.2 スライス分析（report.py B–G, F2–F4）= 高/低成績の「塊」を探す
優先度別(B) / 出口理由別(C) / **サイズ・add別(D)** / ベスト・ワースト(E) / 月別(F) / **月別×出口・サイズ(F2/F3)** / 1日あたり(F4) / **指標帯別 ADX・ATR%・stoch・bb傾き(G)**。
→ 「どの帯・どの条件で勝ち/負けが集中するか」を特定（ML診断のデータスライス）。

### 2.3 較正（report.py H）= AI確率 × 実net の対応
高確率帯ほど net が高いか。**逆較正（一番儲かる帯にAIが低確率）は致命**（E6 で bb傾き<−30 が実証）。

### 2.4 ★ ドローダウン3分類（原因分析の幹・直す前に必ず1つに分類）

| 種別 | report での兆候 | 直し方（ここを間違えると逆効果） |
|---|---|---|
| **① 戦略欠陥** | 全 regime/月で負け・誤ラベル・逆較正(2.3)・IS≫OOS | ラベル定義・特徴量・モデル設計を直す |
| **② 執行** | gross 黒字なのに net 赤・手数料率高・slippage・発注過多 | コスト/約定モデル/発注頻度を直す |
| **③ regime依存** | 特定 regime(月)だけ負け・他月は黒（F で確認） | regime 条件付け / regime 別モデル / regime フィルタ |

出典 tradealgo: 「3種は別の対処が必要・誤診すると wrong fix」。

### 2.5 regime 頑健性（MRP）
**最悪月 = 最小 regime 成績**を robust 下限として見る（F の最小月）。最終目標は**全月** ≥ $1,900（単月判定）。「通算だけ黒字」で安心しない。

### 2.6 原因チェックリスト（ML 根因・該当を ledger に明記）
☐ 誤ラベル ☐ train/test 分布シフト ☐ leak(未来参照) ☐ **fat-tail(勝率と金額の乖離=大勝ちを切る)** ☐ 逆較正 ☐ 過学習(IS≫OOS・best_iter 過大)

### 2.7 学習の中身（train_* の出力）
重要特徴 top / 学習した分岐閾値 / AIが高評価する値域 / **使用した値一覧 JSON（cat_params風・`p23_ml_learned_params.json`）** で V9手書きと対比。

### 2.8 ★ 正の結果の源泉検証（勝った時こそ必須・報告前に実行・2026-06-11 追加）
プラスの数字は源泉を検証するまで「ML が効いた」と報告しない（E13/E15 の2連続実証）。
- **玉単位分解**: 設計効果 vs 副作用/幸運 を玉ごとに分ける（E13: +$98.9 の 2/3 が USD ゲート副作用＝ほぼ1玉の幸運と判明）。
- **対照実験＝予測逆転テスト**: ML に情報があるなら予測を逆にすると悪化するはず。悪化しない/良くなるなら ML 寄与ゼロ（E15: prob 逆の下位20%降りが +$85.0 ＞ 本命 +$52.6・1ループ数分で確定・採点を浪費しない）。
- **独立 sim のプラスは連続モード×年別（特に直近年）で確認するまで信じない**（E16事前分析: ADX 50-60 が独立 sim 4年プラス → 連続モードで 2024 が −$340 に反転）。

### 2.9 ★ 個別トレード読み（集計の前に・仕組みの理解・2026-06-11 追加）
- 大勝ち・大負け・典型負けの代表数本を、**前後24hの値動き（OHLC）と突き合わせ**、「市場が何をして・V9 がどう動き・なぜこの net か・人間ならどこで違う判断をしたか」を1本ずつ言語化する。
- 集計スライス（§2.2）だけでは文脈の欠落が見えない（2026-06-11 P23 読みの実証: 負け3本の共通点＝24h 地合いの方向・走り切り度が入力に無い／暴落日 12/19-20 を収益化できていない、は集計が2週間見抜けなかった）。
- 設計・提案はこの読み（仕組みを3〜5行で説明できる状態）を済ませてから（実データ→仮説→裏取り→設計の順）。

## §3 結果データ 保管場所カタログ（散らばり防止・ここを見れば全部ある）

> **文書の役割分担（どこに何を書くか）は [cat_requirements §8.2 文書マップ](../rules/cat_requirements.md) が正本**（2026-06-07 一本化）。本 §3 は「結果データ（CSV・JSON・report）のありか」カタログに限定。

| 種別 | パス | 中身 |
|---|---|---|
| PDCA 記録（正本） | `.claude/ratchet/ledger.md` | 各 E：変更/結果/原因(3分類)/改善/採用 or 破棄 |
| 設計（正本） | `.claude/ratchet/strat_v9ml_design.md` | 現方針 |
| **分析手法（正本=本書）** | `.claude/ratchet/analysis_playbook.md` | 分析バッテリー・PDCA・保管場所 |
| セッション経緯 | `.claude/ratchet/session_log_YYYYMMDD.md` | その日の学び |
| 候補・トレード記録 | `results/priority_rebuild/ratchet/*.csv` | 候補/AI選択/full/scored（score.py・report.py の入力） |
| 学習した値一覧 | `results/priority_rebuild/ratchet/p23_ml_learned_params.json` | AI が使用/学習した値 |
| 審判（固定） | `scripts/priority_rebuild/score.py` | 売買記録→月次 net |
| 分析ツール | `scripts/priority_rebuild/report.py` | A–I/F2–F4 一括 |
| **結果一覧（書類・人が確認）** | `results/priority_rebuild/ratchet/report_<名前>.txt` | report.py が実行ごとに保存する結果全文（A–I）。まこさんが開いて確認するのはこれ |
| 実装（候補生成/学習） | `scripts/priority_rebuild/gen_p23_candidates.py` / `train_p23_entry.py` | V9不変・自己検査つき |

### §3.1 保管運用ルール（2026-06-05 まこさん確定・ratchet直下を散らかさない）

- **ratchet 直下 = 現役のみ**（現役入力 ＋ 最新実験の出力だけ）。過去実験の出力は `results/priority_rebuild/ratchet/archive/` へ退避する。
- **生CSV（`trades_*`・売買記録）= 上書き / 最新のみ直下**。重い・再現は ledger のコマンドで再生成できる中間生成物。各実験後、前実験の生CSVは archive へ move。
- **記録（`report_*.txt` / `*_learned_params.json`）= E番号付きで残す**（履歴を消さない）。例: `report_trades_E08_*.txt` / `p23_learned_params_E08.json`。report.py は入力CSV名から自動命名するので、**戦略スクリプトの出力CSV名に E番号(E08等)を入れれば report も自動でE番号付き**になる（ledger の実験番号と1対1で対応＝後から探せる）。
- **現役入力（消さない・直下常駐）**: 現ベースの売買記録一式（現在＝採用 SHORT 柱候補 E36 の freq-iter1 base `trades_e36_short_oscillation_5m_shortset1*`・次イテレーションの --vs 比較相手）。⚠️ **E35 は E36 が import する共有エンジン（＋レンジ柱候補・作業中）であって採用 base ではない＝採用は E36**（adopted_strategies.md 台帳の「役割」列が正本・記憶や語感（「採用ベース不変」等）で「採用 base」を決めつけない＝memory feedback_adopted_base_from_ledger_not_wording）。旧 P23 系（`trades_p23_full_test.csv` / `p23_candidates_*.csv`）や旧地面 CSV は archive へ退避済（P23 作業は閉じ・採用地面は P21/P23/E32b の newwin＝archive・2026-06-20）。現役入力は「今のベース戦略の出力」に随時更新する（古い戦略の入力を直下に残さない）。
- **手順**: 新実験を回す前に、前実験の `trades_*`・記録を `archive/` へ move → 新実験を直下に出力 → 採点 → 分析。
- **★出力の命名/archive/上書き防止は共通の書き出し処理が物理化（2026-06-22 まこさん確定・全戦略が踏襲）**: 命名（タグ連番）・新実験前の旧実験 archive・書き出し前の上書き防止は `ratchet_io.py`（共有モジュール）に集約し、戦略は共通の書き出し処理 `_output_and_report`（いま e35 内・将来は中立モジュール）を呼ぶだけで自動で踏襲する。report/analyze/png（report.py / analyze.py / plot_trades.py）も `ratchet_io.archive_if_exists` で上書きせず archive へ逃がす。**新しい戦略（e37/38/39…）は必ずこの共通の書き出し処理を使う**＝個別に命名/archive を書かない。実験出力は `--tag <名前>` で `_<tag>_<NNN>` 連番（ユニーク・上書きしない）／タグ無＝安定名 base（--vs 固定）。
- **★全戦略共通の土台 `strat_base.py`（2026-06-23 新設・中立）**: 上の bullet の「将来は中立モジュール」がこれ＝① load_5m ／ ⑤ _verify_cap・_funding_cost ／ ⑥ _output_and_report（`ratchet_io` へ委譲）／ ⑦ 取引所・予算定数。全戦略（E35/E36/今後 e37…）が import するだけで始められる・戦略固有ロジック（箱・売買エンジン・hold-ML 判別）は各戦略が自前（E35/E36 が手本）。
- **★スクリプト(.py)も同じ思想で整理（2026-06-20 まこさん確定・155本でぐちゃぐちゃ事案）**: `scripts/priority_rebuild/` 直下 = **採用戦略 ＋ 判定器/共通基盤 ＋ それらが import で依存するモジュールのみ**。破棄/旧実験の .py は `scripts/priority_rebuild/archive/` へ `git mv`（履歴保持）。
  - **残す基準＝import closure**: 採用戦略（adopted_strategies.md 参照）と判定器（score/eval_engine/precheck/report/analyze/periods/params_sidecar/verify_design_contract/ratchet_guards/test_*/build_labels_pct/preload_cache）を根に、import を辿って到達する .py だけ直下。到達しない .py は archive へ。
  - **移動後は必ず機械確認**: 残した採用戦略＋判定器が `py_compile` ＋ `import` で壊れないこと（依存欠落＝ModuleNotFoundError が出ないこと）。
  - 採用が増減したら adopted_strategies.md を更新し、直下の .py も同基準で見直す。

## §4 毎セッション実行チェックリスト（この順で回す）

### §4.0 ⛔ 物理強制（hook・CC の意思に依存しない・2026-06-05 まこさん矯正指示）

**score.py で採点したら、report.py（結果表示）と ledger.md（記録）を書くまでターンを終われない**（Stop hook `pdca_gate.sh` が exit 2 でブロック）。CC 自主ルール（本 §4）では素通りした実証（2026-06-05・E8a-2 で score.py だけ回して report/ledger を飛ばした）を受けた物理化。

**更新頻度（何を毎回・何を随時か）**:
| 書類 | いつ | 方法 |
|---|---|---|
| `report_*.txt`（結果一覧A〜I） | **毎実験・必須**（hook強制） | score.py 後に report.py で自動生成 |
| `ledger.md`（全記録） | **毎実験・必須**（hook強制） | 結果+原因3分類+改善を手で1エントリ |
| `*_learned_params_*.json`（AIの値） | 学習した実験のみ | train が自動出力 |
| `strat_v9ml_design.md`（設計書） | 方針・段取りが変わった時だけ | 手で更新 |
| `analysis_playbook.md`（本書・分析手法） | 分析手順を足した時だけ | 手で更新 |

- 仕組み: `cat-bitget/.claude/hooks/pdca_mark.sh`（旗管理・PostToolUse）+ `pdca_gate.sh`（Stop ブロック）・登録は `cat-bitget/.claude/settings.local.json`。
- 旗を下ろす操作: report.py 実行 / ledger.md 編集。**回避（設定無効化・口実 bypass）禁止**（cc_role §1.4.6.2）。

**2026-06-12 拡張（まこさん合意・「最低ライン分析≠分析のゴール」の物理化）**:
- **precheck.py も審判の門**: FAIL で閉じる場合も report/analyze/ledger/5つの問い を飛ばせない（旗が立つ）。
- **report.py は --vs 必須**（KB §0 前後比較）。--vs なし実行は旗が残る。真の初回のみ、まこさん GO を得て `state/no_baseline_approved` を作成（1回で消費・GO なし作成は類型G）。
- **analyze.py N7〜N9 追加**: N7 必要勝率と不足量（損益分岐勝率 vs 実際・pt差）／ N8 負け玉の解剖（entry特徴の勝負中央値比較・月別集中・SL玉の正体）／ N9 出口効率（勝ち玉 MFE 捕捉率 vs 業界基準 0.6-0.75＝入口/出口どちらが問題かの自動切り分け）。
- **5つの問いゲート**: ledger の E エントリに【問1 レバー】【問2 不足量】【問3 負け集中】【問4 過去接続】【問5 次仮説】の5見出し全部を含む編集があるまでターン終了不可。N1〜N9 は数字の抽出（最低ライン）であり、5つの問いに答えるまでが分析。中身の質はまこさんの30秒チェックが担保（浅ければ「浅い」で差し戻し）。

```
1. 新しい売買記録 CSV を score.py で採点（月次 net・地面 $172 と比較）
   python3 scripts/priority_rebuild/score.py <trades.csv> --start 2025-04-01 --end 2025-12-31
2. report.py を通す（比較対象があれば --vs）→ §2.1–2.3,2.5 が一括で出る
   python3 scripts/priority_rebuild/report.py <trades.csv> --start ... --end ... [--vs <baseline.csv>]
3. §2.4 で勝ち/負けの原因を「戦略/執行/regime」に1つ分類 + §2.6 チェックリスト
4. ledger.md に「結果 + 原因(分類) + 改善1つ」を記録 → 次周 Plan へ
```

report.py 1コマンドで §2.1–2.3・2.5 が出る。**§2.4 の3分類と §2.6 チェックは CC が判断して ledger に明記**（report は材料、分類は人/CC の判断）。

## §5 関連
- `cat_requirements.md §4.6`（ハード制約 H1-H14・Plan で照合）/ §8.4（PDCA フロー・本書を参照）
- `ledger.md`（記録）/ `strat_v9ml_design.md`（設計）
- 出典 URL は本書冒頭。
