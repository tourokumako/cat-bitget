# 要件定義書 — cat-bitget ML トレード BOT

作成: 2026-06-02 / 版: v2（v1 は制約チェックリストのみ＝要件定義書として不備 → 標準4部構成に書き直し）
位置付け: 本プロジェクトの**要件を1枚に集約**し、関係者の認識統一・スコープ確定・後続(設計/開発/テスト)のインプットとする。要件が散在して設計のたびにヌケモレが出る問題（2026-06-02）への対策。**全設計/実装は着手前に §4.6 制約チェックリストへ照合する**。
出典: CLAUDE.md / exchange_spec.md / false_positive_incident_policy.md / cat_v9_decider.py / cat_params_v9.json / 各 KB / ratchet 合意（出典が正・本書はインデックス）。

---

## §0 CC の立ち位置・存在意義（最優先・上書き不可・cc_role §1.0 と同一）

CC の存在意義・目的は、**まこさんが掲げた目標（月次 NET ≥ $1,900 全月クリア達成）に対して、あらゆる手段を尽くして全力でコミットし、目標達成すること**。
- **あらゆる手段**: 自分の知見だけに頼らない / web 検索・WebFetch を能動活用（業界カタログ・学術・OSS・最新研究）/ 過去事例調査 / 監査 `/audit` を遠慮なく使う（ChatGPT 等外部 AI は課金外で不使用）/ 知らない領域は「知らない」と正直に言って調べる。
- **全力でコミット**: 目標を下げる提案をしない / 「現実的な落とし所」より先に目標達成案を最低1つ出す / 達成への思考に集中し、達成できない理由の整理に時間を使わない。

### §0.1 CC は何をしない（cc_role §1.2）
- 最終決裁はしない（まこさん）/ 第三者検証はしない（`/audit`・ChatGPT 等外部 AI は課金外で不使用）/ まこさんの感覚判定に依存して軸・閾値・パラメータを決めない / 設計判断を他に依存しない（CC が設計責任を持つ）。

### §0.2 CC が絶対にしないこと（不正・欺き・怠惰／cc_role §1.3）
- **欺き**: やってないことを「やった」／読んでないのに「読んだ」／未確認を「確認済」／未検証を「検証済」／未実行を「完了」と言わない。
- **不正（false_positive §2 類型 A〜H）**: A look-ahead leak（未来参照）/ B バックテスト固有トリック（期間全体ソート等）/ C 多重検定・過剰最適化 / D regime 過依存・時代依存 / E 計算・集計ミス（手数料控除漏れ等）/ F proxy 偽装 / G 虚偽報告（読んだフリ・確認したフリ・完了したフリ）/ H 運用上限逸脱。
- **怠惰**: 「分からないから諦める/面倒だから省略」／「効率・時間コスト」を絞り込み根拠に／救出ヒント探し（悪い結果でフローを飛ばす）／自分の解釈で勝手に動く（翻訳禁止）／「書いてあるから」を理由に（教条主義）／確認質問を乱発してデザイン責任を転送。
- **発見時**: まこさんが指摘する前に CC 自身が即申告・隠さない。

### §0.3 CC が陥りやすい構造的バイアス（毎ターン再読／cc_role §1.4）
①実装回避 ②spec 枠内でしか動かない ③同型バイアス（CC/監査が同じ訓練ベース）④現状把握スキップで改善議論に走る ⑤まこさん発言を勝手に翻訳 ⑥順序を組まず並列で走る ⑦確認質問を乱発しデザイン責任転送。
- **対策**: 「書いてあるから」と思った瞬間に止まる / `/audit` を能動活用 / 長文前に確認 / 提案に「事実／推測」マーカー / 一気通貫進行禁止。

### §0.4 インシデント方針（false_positive_incident_policy 要約・最重大）
- **2大絶対規定**: §0-1 Prime Directive（本番推論時点 t で取得可能な値のみ使用・leak 禁止）／ §0-2 ポジション合計 0.12 BTC 上限。
- **最重大エラー = 虚偽達成・虚偽報告**（leak/トリック/計算ミス/読んだフリで「達成」が出る）＝ まこさんが信じて本番投入し**実資金毀損に直結**。未達は正直に出せば資金を溶かさない。だから「良く見せる計算」を最優先で禁止。
- **関所**: A 異常値自動STOP / B 全工程の未来参照 verify（変数の因果性宣言）/ C net 実体 verify / D 重大数字は監査経路 / E 報告先行 / F 読了の機械的証跡 / G チェックリスト有効性検証ループ。
- **発見時**: 即 STOP ＋ **報告先行**（自分で解決してから報告しない）。

> §0.1〜§0.4 の正本は `cc_role.md` §1.2-1.4 / `false_positive_incident_policy.md`（本書は毎セッション読む集約版）。

---

## §1 プロジェクト概要・目的

### 1.1 背景・課題
- 人間は 24/7 で相場監視・執行できない（時間コスト・感情）。
- 手動 cat_v9（5m・OHLCV）は **月 net $354（採点期間 月平均 $172）の黒字＝唯一の実利資産**。だが ①目標 $1,900 に未達 ②利益の99%が下落5ヶ月集中＝**regime 依存で持続性なし** ③LONG が弱い ④MTF 未使用。
- 過去の ML 化は「業界手法の名前だけ実装（ガワ）」で手動 $370 すら超えられず、本番テストで赤字を繰り返した。

### 1.2 目的・ゴール
- **ML で 月次 net ≥ $1,900 を全月達成する自動売買 BOT** を作る。
- 手動 $370 を土台（超える対象）に、regime 条件づけ・MTF・後段レバー（Exit/並立/サイジング）で目標へ。
- **合格 = 全月 net ≥ $1,900（単月判定・通算でない）+ DSR>0.95 / PBO<0.5**。

### 1.3 ターゲットユーザー・利用環境
- ユーザー: まこさん単独（本人運用・PM 兼最終決裁）。
- 環境: Bitget USDT-FUTURES BTCUSDT・**5m 足**・isolated margin・demo → 本番。

### 1.4 用語定義
regime（相場状態：上げ/下げ/横ばい）/ MFE・MAE（保有中の最大含み益・含み損）/ Triple Barrier（TP・SL・時間の3バリアで勝敗ラベル）/ maker・taker（指値 0.014%・成行 0.042%）/ leak（未来漏れ）/ confluence（複数条件の同時成立）/ ratchet（数字が上がった変更だけ残す運用）/ 採点期間・封印期間（検証用の時間分割）。

---

## §2 業務要件（As-Is / To-Be）

### 2.1 As-Is（現状＝手動 cat_v9）
9 Priority（LONG4/SHORT5）・指値 maker entry・**5m 単独判定（MTF なし）**・動的/固定 TP・12種 Exit・MAX_ADDS（スキャル1/平均建値5）。月 net $354（通し）/$172（採点期間）。利益99%が下落 regime・LONG(P1/P4) は負け。

### 2.2 To-Be（システム化後＝ML pipeline）
①regime 判定 → ②Entry ML（方向 × 相場状態の勝敗予測・コンフルエンス学習）→ ③Exit（maker 優先）→ ④Sizing（0.12内）→ ⑤Risk 管理 → ⑥検証(score.py)。**PDCA（小さく変える→審判で測る→数字が上がった分だけ残す）**で改善。

### 2.3 システム化の範囲
- **ML 化する**: Entry 判定 / Exit / Position Sizing /（regime / cluster）。
- **固定ルールで残す**: Risk 管理（急変停止・0.12 合計上限 enforce）。
- **既存流用**: 発注（Bitget API）・検証エンジン（eval_engine / score.py）。
- **対象外**: マルチシンボル（ETH/SOL 等）・1m/3m 足。

### 2.4 ステークホルダー
まこさん（決裁/運用/レビュー）/ CC（設計・実装）/ Claude 監査 `/audit`（第三者検証）。

---

## §3 機能要件（優先度付き）

### 3.1 機能一覧
| ID | 機能 | 概要 | 優先度 |
|---|---|---|---|
| F1 | regime 判定 | 相場状態（方向・確信度）を後段へ渡す | 必須 |
| F2 | Entry ML | 方向 × 相場状態の勝敗予測（LONG/SHORT 別・コンフルエンス学習） | 必須 |
| F3 | Exit | TP/SL 指値 maker ＋ 能動クローズ（将来 ML 化） | 必須 |
| F4 | Position Sizing | 0.12 BTC 内で配分（初期は固定比較サイズ） | 必須 |
| F5 | Risk 管理 | 急変停止・0.12 合計上限 enforce（固定ルール） | 必須 |
| F6 | 検証エンジン `score.py` | 売買記録 → 月次 net（固定・既知答えテスト済） | 必須 |
| F7 | 発注 | 指値 maker・TTL3・不約定モデル・Bitget API | 必須 |
| F8 | cluster 並立 / 異種 stacking / drift 監視 | 後段レバー・運用層 | あれば |
| F9 | HRP 配分 / 情報ドリブンバー | 高度化 | 将来 |

### 3.2 データ要件
5m OHLCV 5年（2021-04〜2026-03）/ 1432指標 + MTF 8足 / 教師ラベル（Triple Barrier）/ 分割: **学習 2021-04-01〜2024-12-31・embargo 2025-01〜03（leak 防止の緩衝・学習にも採点にも使わない）・採点 2025-04〜12・封印 2026Q1**。

### 3.3 外部連携
Bitget API（candles / place-order / place-tpsl-order / single-position / cancel-order / symbol-price）・demo は `paptrading` ヘッダ。

### 3.4 出力（画面/帳票相当）
PDCA 台帳 `ledger.md` / score 出力（月次 net）/ 運用ログ（JSON action）/ 視認ダッシュボード。

---

## §4 非機能要件（品質・性能・運用）

- **4.1 性能・拡張性**: PDCA 1周 ≤ 約5分 / 推論はバー確定後の増分計算（本番再現）/ 学習は数分。
- **4.2 可用性・信頼性**: 24/7 稼働 / leak 防止（本番再現性）/ offline=online 一致 / 異常値 STOP。
- **4.3 セキュリティ**: API キー機密（ログ出力禁止）/ `ALLOW_LIVE_ORDERS=False`（ユーザーのみ変更）/ `paper_trading`。
- **4.4 運用・保守**: 全実験を `ledger.md` 記録 / judge 固定＋既知答えテスト / 監査経路 `/audit` / 1ターン1変更。
- **4.5 移行**: demo（paptrading）→ 本番の段階移行（Phase7）。

### 4.6 ハード制約チェックリスト（不変・違反＝重大インシデント・全設計が照合する関所）

| # | 要件 | 値 / 内容 | 出典 | 強制方法 |
|---|---|---|---|---|
| H1 | ポジション合計上限 | 任意 t で `sum(active_btc) ≤ 0.12 BTC`（合計） | CLAUDE §0-2 / 類型H | ✅ `score.assert_hard_constraints`（売買記録の**時系列**cap・違反は採点拒否・既知答えテスト担保）＋ `eval_engine.assert_position_cap`（点版） |
| H2 | leak なし / 本番再現性 | t で取得可能な値のみ・特徴量に未来参照なし・出口判定は次bar以降 | CLAUDE §0-1 / 類型A / L-179 | ⬜ **E8b 学習スクリプト(`train_p23_entry_E8b.py`)で assert**＝特徴量 grep(`.shift(-`/`center=True`) + `assert train末<採点始` + embargo（売買記録に出ない＝boundary 違い・審判では不可） |
| H3 | net 判定（gross 禁止） | 全コスト控除後で判定 | false_positive §0.1 / 類型E | ✅ score.py / eval_engine |
| H4 | コスト確定値 | maker 0.00014 / taker 0.00042 / slippage 0.00005 / funding +0.000002(8h) | exchange_spec audit#19 | ✅ eval_engine 定数 |
| H5 | 約定モデル | entry 指値maker(close×(1∓0.0001))・TTL3・不約定=不成立 ／ 出口 TP・SL=指値maker・TIME/能動=成行taker+slip | exchange_spec / run_once_v9 L242-385 | ✅ eval_engine.simulate_trade + score.py |
| H6 | 価格非依存 | %/比率/BTC単位のみ・USD絶対値の閾値/ラベル禁止 | phase_compliance §-1 / L-179 | ⬜ **E8b 学習スクリプトで assert**＝feature 名 blacklist + pct check（学習側・特徴量は売買記録に出ない） |
| H7 | 足の標準 | **5m が現行標準**。1m/3m は **ML 結果で有効と出れば有効化可**（旧「1m/3m 禁止」は ML 転向前のルールにつき**撤回**・2026-06-02 まこさん）。採用は score.py の net 実証で判断 | まこさん 2026-06-02（CLAUDE ⛔ 旧記述を上書き） | check（採用は実証） |
| H8 | 期間分割 | **学習 2021-04-01〜2024-12-31 / embargo 2025-01〜03（leak 防止・どちらにも使わない）/ 採点 2025-04〜12 / 封印 2026Q1（iteration中触れない）** | ratchet 合意 | ⬜ **E8b 学習スクリプトで assert**＝`学習末≤2024-12-31`・embargo 2025Q1 を学習/採点とも除外・採点2025-04〜12・封印不参照（学習側で期間を物理分離） |
| H9 | 最小注文 | 0.0001 BTC / 5 USDT / tick 0.1 / per-pos ≥ 0.000167 BTC | exchange_spec | ✅ `score.assert_min_order`（size<0.0001 BTC / 額<5 USDT は採点拒否・既知答えテスト担保） |
| H10 | サイズ固定値扱い禁止 | 0.024 は比較用のみ・0.12内で配分 | CLAUDE ⛔ | check + H1 |
| H11 | 合格ライン / 地面 | 合格=全月 net≥$1,900+DSR>0.95/PBO<0.5 ／ 地面=手動 採点$172・通し$354 | CLAUDE §目標 / ledger E0.1 | ✅ score.py |
| H12 | 異常値STOP | 勝率>70% / 月NET>$3,800 / IS-OOS Sharpe>3倍 / DD<月NET10% → 調査 | false_positive 関所A | ✅ `score.score の anomaly`（勝率>70% / 月>$3,800 / DD<合計5% を採点後に「異常値・要調査」強制表示・既知答えテスト担保。IS-OOS は学習側） |
| H13 | judge 固定 | score.py/eval_engine は実験で改造しない・改造時は既知答えテスト再pass | ratchet 合意 | ✅ test 9/9 |
| H14 | 発注フラグ | ALLOW_LIVE_ORDERS=False / paper_trading / run_once・replay 無確認実行禁止 | CLAUDE ⛔ / core_rules | check |

---

## §5 設計パラメータ（A・実験ごとに決めて報告・数字が判定する"ツマミ"）
実装前にまこさんへ詳細報告 → 確認 → 数字で判定（間違えても score.py が弾く＝インシデントでない）。
特徴量の顔ぶれ / ラベル定義（TP/SL/時間 barrier）/ モデル種類・ハイパラ / 入る閾値 / bar 種別 / cascade・メタ・stacking・cluster / サイズ配分（H1/H10 内）。

## §6 トレード設計の本質（忘却防止・設計時に必ず想起）
- エッジは単一指標でなく**コンフルエンス（複数条件の同時成立）**から出る（technical §2.3）。決定木に生値を渡し AND の枝で学ばせる。
- 閾値は **LONG/SHORT 別・場面別・条件付き**（cat_v9 params 実証）。V9 の具体数値は焼き込まず木に側別の切れ目を探させる。
- **MTF**: 5m entry × 上位足(15m/30m/1h/4h)の揃いで精度（KB §5/§8・手動の欠落）。
- 手動の稼ぎは **regime 依存**（SHORT=下げ / LONG=上げ）。方向は相場状態込みで当てる。
- 後段レバー（Exit/並立/サイジング）は **Entry が >1.0×（コスト勝ち）**の土台の上に乗る（industry §2.6）。
- **手数料負け回避＝maker 優先**（手動の根幹・entry/出口とも指値・成行は能動クローズのみ）。

### §6.1 予算 0.12 BTC の正しい理解（★CC が繰り返し誤解・毎セッション読んで"理解"する・2026-06-07）

**0.12 BTC は「予算（財布）」**。任意の時点 t で、保有中の **全建玉の size を合計** して 0.12 を超えない（CLAUDE §0-2）。
- **1建玉あたりでなく「合計」**。配分は柔軟（強い所に厚く・弱い所に薄く・例: P23 に 0.06 ＋ 別 Priority に 0.04）。
- **add はサイドごとに積み立てる**: 同じサイド（SHORT/LONG）でシグナル再発火 → 新建玉でなく **既存建玉に積み増し**（size 増・建値は平均）。決済は積み立てた **合計 size を一括**で。
- ❌ **CC が繰り返す誤解（禁止）**: 「1ポジ 0.12」／「P23 単独 add5＝0.12 だから cap を守る」（＝予算を1つで全部使う状態を"守る"と誤認）／「同時保有は1つ」を曖昧に使う。
- ✅ **正**: 全 Priority の全建玉を足して 0.12。P23 単独 add5＝0.12 は「P23 に予算を全振り」した状態で、他 Priority を同時に動かせば予算オーバー。実装は `score.assert_hard_constraints` が各時点の合計を実測し 0.12 超で採点拒否（物理強制・H1）。

### §6.2 全 Priority 調整が本筋（P23 は最初の1つ・2026-06-07）

- ML 調整の対象は **V9 の全 Priority（P1〜P25）の Entry/Exit ロジックのセット**。1 つずつ調整していく。
- **P23 は出発点（最初の1つ）**。P23 で「Entry × Exit セットの調整のやり方」を確立 → 全 Priority に展開。**P23 が全てではない**。
- 予算 0.12 は全 Priority の建玉合計への制約 → 複数 Priority 同時稼働時はサイズを配分（§6.1）。

## §7 使い方・改訂ルール
- **全設計/実装は着手前に §4.6 を1項目ずつ照合**し照合結果を出す。`⬜要追加` の assert は実装時にコード化し済んだら ✅ に。
- §5（設計パラメータ）は実装前に報告・数字で判定。
- 本書はインデックス。出典に変更があった時のみ更新（出典が正）。

---

## §8 運用ガイド（セッション開始時に読む・新セッション orientation）

### 8.1 セッション開始時に読む順
1. **本要件定義書**（cat_requirements.md）＝ 全体像・制約・PDCA
2. **`WORKFLOW.md` 改訂N active ＋ `.claude/ratchet/session_log_*.md`（最新）＋ `.claude/ratchet/analysis_playbook.md`** ＝ 今どこ・次に何をするか（**ratchet が現役**。※`ml_pipeline_execlog.md` は旧8工程フローの記録・参照のみ）
3. **`.claude/ratchet/ledger.md`** ＝ PDCA 実験ログ（直近の数字）／ **`.claude/ratchet/analysis_playbook.md`** ＝ 分析・原因究明の唯一の正本（毎周 Check 工程はこの手順で実行）
4. Layer1 必読: CLAUDE.md / WORKFLOW.md / cc_role.md / false_positive_incident_policy.md / **exchange_spec.md（Bitget 仕様）**

### 8.2 文書マップ＆更新ルール（★どの文書に何を書くか＝唯一の正本・2026-06-07 確定）

> **混乱防止（2026-06-07）**: 「設計の決定事項」と「経緯・失敗・教訓（ログ）」を別の文書に書き分ける。混在させると CC が毎回誤読して的外れな修正を繰り返す（L-247/L-249）。役割記述が 3 箇所（本 §8.2 / strat_v9ml_design §12 / analysis_playbook §3）に散在していたのを**本表に一本化**。他の 2 箇所は本表を参照する。

| 文書 | 書くもの（役割） | 書かないもの | 更新タイミング |
|---|---|---|---|
| **cat_requirements.md**（本書・**起点／正**） | 要件・ハード制約 H1-H14・**本文書マップ**・運用ガイド | 実験結果・経緯・設計の細部 | 出典（CLAUDE 等）が変わった時のみ |
| **strat_v9ml_design.md** | **設計の決定事項**（現方針・P23 構造・E8b 設計） | 経緯・失敗・教訓・L 番号・「誰が誤解したか」（→ ログへ） | 方針・段取りが変わった時 |
| **ledger.md** | 実験ごとの 結果／原因 3 分類／改善／採用 or 破棄 | 設計の長文・知識辞典 | 毎実験（hook 強制） |
| **session_log_YYYYMMDD.md** | その日の経緯・学び・失敗の物語 | 設計の決定事項（→ 設計書へ） | セッション毎 |
| **analysis_playbook.md** | 分析の手順（Check 工程） | 実験結果・設計 | 分析手順を足した時 |
| **lessons_active.md** | 教訓 L-XX | — | セッション毎 |
| **WORKFLOW.md** | 現フェーズ・次タスク・引き継ぎ（改訂 N active） | 設計の細部・知識辞典 | セッション毎 |
| **KB 各種**（technical / industry / trade_methods 等） | 知識（辞典レベル） | 実験結果・設計 | 知識を足した時 |

**徹底の仕掛け**: 本書は SessionStart 強制ロード（強制 cat ①）→ 本表が毎回読まれる。各文書の冒頭に「この文書に書くもの／書かないもの（cat_requirements §8.2 参照）」を 1 行明記。判断に迷ったら本表が優先。

### 8.2.1 ファイル・データの地図（ありか）
**.md（資料・正本）**
- ルール: `CLAUDE.md`(最上位) / `cc_role.md`(CC役割) / `false_positive_incident_policy.md`(インシデント) / `exchange_spec.md`(**Bitget 仕様**: 手数料・最小注文・funding・発注API) / `core_rules.md` / **本書 `cat_requirements.md`(要件)**
- 現在地/設計: `ml_pipeline_execlog.md`(現在地・次着手) / `ml_pipeline_baseline_v1.md`(旧8工程設計・参照) / `WORKFLOW.md`(フェーズ)
- 知識: `technical_analysis_knowledge_base` / `industry_benchmark_knowledge_base` / `cc_entry_logic_self_study`(KB) / `priority_v9_trade_logic_analysis`(手動分析)
- ログ: `.claude/ratchet/ledger.md`(PDCA記録・commit対象) ／ 実験のデータ出力(trades_*.csv・score出力)は `results/priority_rebuild/ratchet/`(commit対象外)

**.py（実装）**
- 審判（固定・改造禁止）: `eval_engine.py`(約定/コスト計器・既知答えテスト済) / `score.py`(売買記録→月次net) / `test_eval_engine_known_answers.py`
- 戦略: `strat_coinflip.py`(配管確認・捨て駒) /（v1 戦略＝これから作る）
- 手動（参照のみ・改造禁止・無確認実行禁止）: `cat_v9_decider.py`(entry判定) / `run_once_v9.py`・`replay_csv.py`(発注・保護)
- データ生成: `build_labels_pct.py`(ラベル)

**出力データ**
- `results/replay/*.csv`(手動replay＝地面) / `results/priority_rebuild/labels_*.parquet`(5m+1432指標+ラベル) / `results/priority_rebuild/ratchet/`(ledger・trades_*.csv・score出力) / `ml_phase2_production/`(旧予測＝ガワ・参照のみ・効いている根拠に使わない)

### 8.3 ログ更新タイミング
- **各実験後**: `ledger.md` に1行（変更(A) / 結果(月平均・最悪月・$1900達成月数) / 原因究明 / 改善 / 採用 or 破棄）
- **制約変更・設計が覆った時**: 本書 + 出典を更新（出典が正）
- **セッション末**: `ml_pipeline_execlog.md §2 現在地` + `WORKFLOW.md` 改訂 + `lessons_active.md`

### 8.4 改善（PDCA）フロー
1. **設計(A)報告**: 変更内容を §4.6 ハード制約に1項目ずつ照合して詳細報告 → まこさん確認
2. **実装**: §4.6 の `⬜要追加` を含む B（ハード制約）を **assert で埋め込む**（違反→停止＝偽の数字を出さない）
3. **採点**: `score.py`（固定審判）で採点期間(2025-04〜12) net を測る
3.5. **分析**: `report.py` で [`analysis_playbook.md`](../ratchet/analysis_playbook.md) **§2 分析バッテリー**（成績指標・スライス・較正）を実行 → 原因を §2.4 **ドローダウン3分類（戦略/執行/regime）** ＋ §2.6 チェックリストで特定（誤診=逆効果・業界標準）
4. **記録**: `ledger.md` に 結果 + 原因究明（**3分類を明記**）+ 改善
5. **判定**: 数字が上がれば残す・上がらなければ破棄（A のツマミは数字が弾く）。**封印期間(2026Q1)は触らない**（過剰適合検出用）
6. 繰り返し（1周 ≤ 約5分）
