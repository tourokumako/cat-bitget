# セッション詳細ログ 2026-06-05 — V9構造の理解 / V9ベースMLラチェットの方法 / E4失敗と学び

記録目的（まこさん指示・2026-06-05）: **CC はスクリプトからトレード手法を読み取る力がない**。だから「V9の構造（Priorityごとにスタイルを変えている等）／MLラチェット調整の方法（Entry/Exitをセットにする等）／これまでの失敗／学び」を詳細に記録し、次セッションで再導出・再失敗しないようにする。

---

## 0. このセッションの結論（1段落）
「地面 $172 は P23単独」という思い込みが**誤り**と判明（実は V9全部入り＝regime切り替えで全Priority動かした数字・sha256+score.pyで確定）。V9ベースML（V9踏襲＋ハードコード部分だけML化）の最初の1手 E4（V9候補に「勝つか」二値メタ＋MTF）は **AUC 0.673 出たが net は超えず＝破棄**。原因＝①ラベルが勝率（net金額でない）②**スタイルの違うPriorityを1モデルに混ぜた**。まこさん指摘で「V9は Priorityごとにスタイルを変えて設計してある」「ML調整は Entry/Exit をセットで net 判定」「Priority別にML化」が確定。

---

## 1. 大前提の訂正 — 地面 $172 の正体（思い込み撤回）
- 誤: 「地面 $172/$354 は P23単独の数字／V9全設計は未測定」。
- 正: **地面 $172/$354 ＝ V9全部入り（regime切り替え・全Priority）の数字**。
  - 検証: `replay_csv.py --regime --regime-safe` を再実行 → 既存地面ファイルと **sha256 完全一致(abe8e42c…)** → score.py 採点期間 **$172.68**（ledger E0 と一致）。1,157トレード・全Priority発火。
  - 5年データ（暖機十分）で採点期間を測ると **$149.50/月**（365d版$172.68との差は2025-04のregime暖機差・他月一致）。MLは同源5年の $149.50 と apples-to-apples で比較。
- ライブBot（run_once_v9＋固定 `cat_params_v9.json`）は **P23 SHORT のみ有効**（手動時代に Priority を1つずつ手調整し P23 まで仕上げた段階）。
- 含意: **全Priority動かしても $172・全月$1,900は0/9・利益は下落集中**。「未調整Priorityを足せば届く」は誤り。$1,900の壁は Priorityの数でなく根本。
- 正本: `manual_v9_p23_only_reason.md`(auto-memory) / ledger E0。

---

## 2. V9の構造 ＝ Priorityごとにスタイルを変えている（最重要・CCが読めなかった核心）
V9 Entry = 9セットアップ（5m指標のAND・`cat_v9_decider.py`）。Exit = 12種（`run_once_v9._check_exits` / `replay_csv._check_exits_replay`）。
**各Priorityは狙うトレードスタイルが違う**（まこさんが意図的に設計）。判別の手がかり = `MAX_ADDS_BY_PRIORITY` ＋ 保有時間 ＋ TP_PCT ＋ decider のコメントラベル。

| P | 方向 | MAX_ADDS | スタイル | 狙う局面/型 | 根拠（params/observed） |
|---|---|---|---|---|---|
| P1 | LONG | **1** | スキャル | 上げMACDゴールデン短期 | decider「スキャルMACD」/ 保有~35min |
| P21 | SHORT | **1** | スキャル | 下げMACDデッド短期 | decider「スキャルMACD」/ 保有~6min（最短）|
| P25 | SHORT | **1** | 順張り初動 | 下げ加速(ADXスパイク) | P25_MAX_ADDS=1 |
| P3 | LONG | **1** | stoch単発 | 強い上げのstochゴールデン | P23のミラー |
| P2 | LONG | **5** | 平均建値/ポジション | 売られすぎ反発を買い増し | ADDS=5 / 保有~128min |
| P4 | LONG | **5** | 押し目買い | 上げトレンドの押し目 | ADDS=5 / 保有~65min |
| P22 | SHORT | **5** | 戻り売り | 上に行き過ぎを売る | ADDS=5 |
| P23 | SHORT | **5** | 下落継続（**大勝ち源**）| 下げの戻りが切れて再下落 | ADDS=5 / TP1.2% / avg net **$13.9**（最大）|
| P24 | SHORT | **5** | 買われすぎ反転 | 過熱天井 | ADDS=5 / 保有~235min |

**読み方の核**:
- **MAX_ADDS=1 ＝ スキャル**（小勝ち・速い・単発）: P1 / P21 / P25 / P3
- **MAX_ADDS=5 ＝ 平均建値/ポジション**（買い増して大きく取る・長め）: P2 / P4 / P22 / P23 / P24
- 系統: 順張り(P4/P3/P23/P25) / 逆張り(P2/P22/P24) / スキャル(P1/P21)
- **大勝ち源＝P23**（ADDS=5・下落を持つ・TP1.2%・avg net最大）／**小勝ち源＝P21**（スキャル・avg $2.9・6min）。
- regime→Priority割当（`replay_csv._REGIME_PRIORITY_SETS`・手書き）: 下落→P2/P21/P23 ／ レンジ→P4 ／ 上昇→P1/P24。

---

## 3. V9ベース ML ラチェット調整の方法（合意した進め方）
- **方針**: V9を踏襲（候補＝V9のセットアップ / Exit＝V9の12種）し、**人が手で決めたハードコード部分だけML化**（`policy_v9_base_ml_unlock.md`・まこさんGO 2026-06-04）。コピーでなく、抜き出してML化。
- **ML化する部分（抜き出し）**: ①Entryの固定閾値 ②採用/見送り ③局面→Priority割当 ④Exitパラメータ
- **残す（構造）**: セットアップの形 / Exitの種類（12メニュー）
- **足す（V9に無い新入力）**: MTF（15m/30m/1h/4h・leak-safe）
- **Entry/Exit はセットで net 最適化**（まこさん指示 2026-06-05）。Entryだけ勝率で絞るのは禁止（E4の失敗）。出口の数値も候補に並べ、入口選別×出口設定の組合せを net で判定。
- **Priority（スタイル）ごとにML化**（混ぜない・E4の教訓）。各Priority内はスタイルが揃うので勝率/閾値/出口の学習が net と整合する。
- **判定 ＝ score.py の net**（固定審判）。数字が上がった変更だけ残す。1周は小さく。封印2026Q1は触らない。
- **fat-tail の扱い（まこさんの指摘）**: 「大勝ち偏り」は固定でなくスタイルの選択。**出口を同サイズに揃えれば勝率≈netになる**。スタイル（スキャル小勝ち/ポジション大勝ち）に合わせて label と出口を揃える。長め(swing/position)は手動で読める領域＝BOTの狙い。
- **業界裏取り（WebSearch 2026-06-05）**: 勝ち負け二値でなく **net/PnL を直接最適化**が標準（[QuantStrategy](https://quantstrategy.io/blog/machine-learning-for-exit-optimization-predicting-the-best/)）／Entry+Exit一括最適化＝**RL**（報酬 net/Sharpe・[QuantInsti](https://blog.quantinsti.com/reinforcement-learning-trading/)/[MDPI](https://www.mdpi.com/2227-7390/12/24/4020)）だが小データ過学習リスク／純net報酬は少数大勝ちに過剰適合→**Sharpe等リスク調整報酬**（[arXiv2506.04358](https://arxiv.org/pdf/2506.04358)）／メタは二値でなく net金額で重み付け（[Meta-Labeling](https://en.wikipedia.org/wiki/Meta-Labeling)）。

---

## 4. これまでの失敗と学び（時系列）
- **v1（`strat_v1.py`・2026-06-04）**: ゼロからML・全bar無差別の単段 → E2 −$897(破棄)/E3 −$430(SHORT死亡)。過去 Phase1 v6 全滅(8軸欠落)の再演。**学び**: CCにゼロ設計させるとガワになる → V9踏襲へ転換。
- **E4（`strat_v9_ml.py`・2026-06-05）**: V9候補（replayの実トレード）に LightGBM で「勝つか(net>0)」を予測し prob≥θ で採用＋MTF。
  - 結果: AUC **0.673**（勝率の選別力あり・MTFも top15 で効く）。だが net は θ↑で悪化（取る全部 $149.50 → θ0.65 $83.5 → θ0.70 $12.3）。地面を超えず → **破棄**。
  - 原因（data確定）: **corr(ml_prob, net_usd)=−0.027**（無相関）。低prob群(勝率0.43)が net+$620、avg_net は prob下位50%$3.61 vs 上位50%$0.54（低probが7倍）、net最大5件のprob=0.64-0.69（中位）。**勝率最大化は大勝ちを切る＝edge と逆行**。
  - 根本: ①ラベルが勝率（net金額でない）②**スタイルの違うPriorityを1モデルに混ぜた**（P21スキャル小勝ち＋P23ポジション大勝ちが同モデル）。
- **学びまとめ（次に効く）**:
  1. 地面 $172 ＝ V9全部入り（P23単独でない）。
  2. **V9はPriorityごとにスタイルを変えてる**（MAX_ADDS=1スキャル / 5ポジション）。
  3. **勝率 ≠ net**（fat-tail）。net金額を目的に。出口を同サイズに揃えれば勝率≈netになる。
  4. **スタイルが違うものを混ぜるな** → Priority別にML化。
  5. **Entry/Exit はセットで net 最適化**。
  6. **CCはスクリプトからトレード手法を読み取れない** → 記録で縛る（本ログ）。設計はまこさんのトレード判断起点、CCは翻訳+計測。

---

## 5. 次の一手（未着手・合意済方向）
- **Priority（スタイル）別に、Entry閾値＋採用＋ExitパラメータをセットでML化し、net で判定**。
- 予測対象＝net金額（勝率でない）。MTF入力。学習<2025-04/採点2025-04〜12/封印2026Q1。
- 進め方: §4.6 H1-H14 照合つきで設計(A)報告 → まこさん確認 → 実装 → score.py。

---

## 6. このセッションの生成物
| 種別 | パス | 状態 |
|---|---|---|
| MLコード | `scripts/priority_rebuild/strat_v9_ml.py` | E4（破棄）だが土台。per-priority化で改修 |
| 出力 | `results/priority_rebuild/ratchet/trades_v9_score_unfiltered.csv` | $149.50 baseline（ml_prob列付き） |
| 入力コピー | `data/BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv` / `results/replay_..._1826d_V9FULL_safe.csv` | 5年V9全部入りトレード（3,797件・学習用） |
| 記録 | 本ログ / ledger E4 / lessons L-247 / `v9_priority_styles.md`(auto-memory) | — |

V9本体（cat_v9_decider.py / cat_params_v9.json / run_once_v9.py / replay_csv.py）は一切変更していない。

---

## 7. このセッション続き（2026-06-05 PM）— E5 filter(負け) → E6 V9踏襲ML本実装 → 分析基盤1本化

> 記録目的: 経緯を抜け漏れなく残し、次セッションが誤解なく引き継ぐ（まこさん指示）。CCはトレード意図をコードから読めないので、設計確定経緯・実装・結果・診断・次の手を全部固定する。

### 7.1 設計確定（まこさんと多数往復で確定。CCは何度も外したので確定形を固定）
- **対象**: P23 SHORT（**ポジション型・買い増し(add)で大勝ち**。データ確定: add平均2.1/最大5・勝率46%だが大勝ちで稼ぐ・**スキャルではない**）。
- **ML化する所**: 「**最初に入るか**」だけ。**add（買い増し）と出口はV9のまま**（大勝ち構造を壊さない）。
- **ML化する閾値（抽出）**: P23コードの人が手で置いた数字＝gap0.3 / ADX30-50 / ATR≥150(→%化) / bb傾き<-10 / high_adx複合（出口TP1.2%等は次段）。**型(stochデッドクロス+陰線)は残す**。
- **学習方法**: 型だけで候補を広げ（閾値AND外す）→生指標を決定木に渡しnetで判定（=閾値ANDを木のsplitに置換・cat_requirements §6）。**金額回帰でなく○×(net>0)分類**（E5金額回帰が弱い+WebSearch裏取り 分類>回帰・fat-tail）。
- **⚠️ CCが繰り返し外した点（次セッション再演防止）**: ①「V9を間引く(後段フィルタ=E4/E5)」②「regimeゼロ設計で作り直す」——**両方違う**。正解は「**V9の固定閾値を抽出してML化・型/add/出口はV9のまま**」。まこさん10往復以上訂正。

### 7.2 E5（`strat_v9ml_p23.py`・破棄）
P23のみ・net金額**回帰**(Huber)でfilter。Spearman(予測,実net)=+0.115（E4の−0.027から反転=方向は正）だがfilterは削るだけで総net減・地面未達 → **破棄**。学び: filterのみ・金額回帰は弱い。

### 7.3 E6（`gen_p23_candidates.py` + `train_p23_entry.py`）= 本実装
- **gen（候補engine・V9不変importのみ）**: P23の型だけで候補50,328件（閾値外す＝V9が捨てた場面も）。各候補を**V9のadd/exitで独立前向きsim**（run()のloop移植・`_check_exits_replay`等import）。
  - **自己検査✅**: 連続モードが本物 `replay_csv.run()` と **1232件 net$2558.80 で1円一致**（移植の正しさを機械的に証明）。
  - 候補: full(V9閾値)2045件+$5747 / typeonly(型だけ)50,328件 −$32,819 勝率0.339（広げると大損＝V9が絞る理由＝ML余地）。
- **train（○×分類）**: 特徴量=入口指標(atr/bb_slope pct化)+MTF・結果列除外(leak)・過学習対策・θ*は学習側net最大。
  - **結果（採点2025-04〜12・score.py）**: AUC0.594 / **V9手書きfull $1943(481件) vs AI θ0.56 $1346(1223件)=AI負け(−$596)**。

### 7.4 精密診断（report.py・**負けの核心を特定**）
- **① 単発(add無)は赤字**: 0.024サイズ(add1) 1122件 **−$497**。**利益は全部 買い増しが育った取引**（add2-5で+$1991）。＝P23の利益は入口の瞬間でなく「下げが続いて買い増せるか」。
- **② bb傾き 逆較正（核心）**: 一番儲かる急な下げ **bb≤−30 が+$1982** なのに、AIの平均prob **0.448（最低）**。上げ(0+)に最高prob0.509。**AIが大勝ち(下げ継続)を捨てる正体**。
- **原因**: ○×(勝つか)は勝率最大化で**fat-tail(大勝ち)を切る**＝E4の罠がbb傾きで再現（急な下げは勝率36%だが1発が大きい→○×は「勝率低い=避ける」）。
- **AIが学習した値**（`p23_ml_learned_params.json`）: EDGE_ADX[25,50]（V9は30→25-30取りこぼし）/ EDGE_ATR%[0.3,0.7] / EDGE_BB≤−30。θ0.56・AUC0.594。

### 7.5 分析基盤の1本化（まこさん指摘＝結果が散らばる）
- `report.py`（新規・分析ツール）: A全体(Sharpe/Sortino/PF/Recovery含む)/B優先度/C出口/D サイズ・add/E ベスト悪/F月別(+AI vs V9)/F2-4 月別×出口・サイズ・1日あたり/G指標帯×prob×net/H確率較正/I MFE-MAE。**日本語表記・結果を `report_<名前>.txt` に自動保存**（まこさんが開いて確認する書類）。
- `analysis_playbook.md`（新規・**分析の唯一の正本**）: PDCA工程＋業界標準バッテリー（ドローダウン3分類/データスライス/較正/MRP/原因チェックリスト・WebSearch裏取り）＋**結果データ保管場所カタログ**＋毎セッションチェックリスト。`cat_requirements §8`組込み（毎セッション実行）。

### 7.6 次の一手（E7・合意方向）
- **下げの強さ(bb≤−30)を勝率でなく「金額の大きさ(payoff)」で効かせる**。○×confidence順のサイジングは**逆効果**（bb逆較正でAIが大勝ちを低prob化）→ net金額/payoffベース、または下げregimeを土台に固定しその中でML。
- 地面: 採点 全Priority$172 / P23単独≈$98(9mo) / V9手書きP23(test独立)$1943。判定=score.py + report.py(原因3分類)。

### 7.7 このセッションの生成物
| 種別 | パス | 状態 |
|---|---|---|
| 候補engine | `scripts/priority_rebuild/gen_p23_candidates.py` | 自己検査✅・V9不変 |
| 学習 | `scripts/priority_rebuild/train_p23_entry.py` | ○×分類+学習値JSON出力 |
| E5(破棄・土台) | `scripts/priority_rebuild/strat_v9ml_p23.py` | net回帰filter |
| 分析ツール | `scripts/priority_rebuild/report.py` | A-I・書類自動保存 |
| 分析正本 | `.claude/ratchet/analysis_playbook.md` | PDCA+バッテリー+カタログ |
| 記録 | ledger E5/E6 / lessons L-248 / 本ログ §7 | — |

V9本体（cat_v9_decider.py / cat_params_v9.json / run_once_v9.py / replay_csv.py / score.py / eval_engine.py）は一切変更していない（importのみ）。

---

## 8. このセッション続き（2026-06-05 夜）— E8a-2破棄 / θ足切り路線の終了 / E8bへ転換 / 矯正 / 4資料精読

> 記録目的: 設計書(strat_v9ml_design)には設計だけを書き、**経緯・失敗・教訓はここ(ログ)に書く**（まこさん指示 2026-06-05）。

### 8.1 E8a-2（破棄）— θ選定を「検証スライス＋プラトー中央値」に変更 → さらに悪化
- 狙い: E8a 僅差負け（θ0.66 $1,877）の原因＝θ選定が学習フィット部で高θ化、を直す。θを検証スライス(学習内hold-out 15%)で選定＋プラトー中央値で穏当化。
- 結果(score.py): **θ*=0.74 / $785（130件）vs V9 $1,943 ＝大負け −$1,157**（前回0.66 $1,914 より改悪）。
- 事後診断 採点θ掃引（trades_p23_E08_all_scored.csv）: **θ0.5 1036件$3,068 / θ0.55 754件$2,765 / θ0.6 523件$2,605 / θ0.66 318件$1,914 / θ0.74 130件$801** ＝**取るほど稼ぐ・削るほど減る**。
- 原因(3分類): ①戦略欠陥でない（AUC0.733・較正正常・テストθ0.5でV9超え$3,068）②真因＝**θ選定の train/test 分布シフト**（検証スライス＝学習最後15%が「高θ地合い」に偏る）。k-fold も学習窓は全部採点前で同型バイアス→無効。③副次＝θで絞っても伸びない玉が残り大勝ちを削る＝**θ足切りの構造的限界**。
- ledger E8a-2 に記録。**判定＝破棄**。

### 8.2 θ足切り路線の終了（まこさん叱責で判明した CC の誤り）
- まこさんの一貫指示＝「**Entry/Exit をセットで閾値調整**」。CC はこれを「**θ（確率の足切り線）**」に勝手に翻訳し（cc_role §3.3 翻訳禁止違反）、Exit を V9 固定のまま Entry 側 θ だけを E6/E8a/E8a-2 と3回いじった＝**Entry/Exit セットを一度も実行していなかった**。
- θ足切りは P23（fat-tail＝取るほど稼ぐ）と構造的に不適。**θ足切り路線は破棄**。
- データ分析の基本欠落も叱責: 前回レポートと比較せず「AI負け」と単体判定／トレード数激減(318→130)を見落とし（「データ分析ってわかる？」）。

### 8.3 4資料精読 + 業界整合（ベースアップ）
- trade_methods §6: Entry/Exit 連動・**期待値=勝率×平均利益−敗率×平均損失**・Triple Barrier（**Exit がラベルを決める**＝入口学習は Exit とセット）。
- industry §2.6: **Entry 単独 1.6× では $1,900 不可能・5レバー（Entry/Exit/並立/regime/sizing）必須**（ケースB 中央値で 5.57×）。
- cc_entry §14.1: ラベルは **MFEピーク（バックテスト固有・取れない）でなく Triple Barrier（実出口）** が業界標準。§18.2 cascade（段1で高recall絞り）。
- → 結論: **E8b（Entry×Exit セット閾値調整・木が split=閾値を net 最大に学習）** へ転換。設計は strat_v9ml_design §10.2-10.5。

### 8.4 矯正（まこさん指示で恒久化）
- **PDCA 物理強制 hook**（L-250）: `cat-bitget/.claude/hooks/pdca_mark.sh` + `pdca_gate.sh`。score.py 採点後に report.py + ledger 記録が済むまでターン終了不可。登録 settings.local.json。
- **トレード結果データ分析方法 KB 新規作成**: `.claude/memory/trade_analysis_methods_kb.md`（前後比較必須・MAE/MFE較正・Monte Carlo・ブートストラップ等・WebSearch 出典）。
- cc_role §1.4.6.2 の hook パス誤記（bitget-python-sdk-api 配下 → 実態 cat-bitget 直下）を訂正。

### 8.5 目標逆算（まこさん指示）
- 月$1,900 = 日$63.3 = 件数 × avg net。日2件なら avg$32 / 日5件なら avg$13。手数料下限 size0.024で$0.67。
- 現状 V9手書き P23＝月53件・avg$4.0（月$216）＝サイズ上限でも未達＝**P23単独では届かない・多レバー必須**。今は P23 で Entry×Exit セットの土台天井を測る段階。strat_v9ml_design §11。

### 8.6 次の一手（E8b・設計確定・実装前まこさん確認待ち）
- strat_v9ml_design §10.5 の通り: 入口閾値（ADX/ATR%/bb傾き/stoch gap）を木が net 最大の split で学習（V9固定値を置換・θ足切りしない）× 出口閾値（TP/TIME/MFE）を V9 近傍グリッド → セットで score.py net 最大を学習期間で選び採点で確認。判定＝地面$1,943超え＋§11逆算。
