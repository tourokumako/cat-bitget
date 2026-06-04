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
