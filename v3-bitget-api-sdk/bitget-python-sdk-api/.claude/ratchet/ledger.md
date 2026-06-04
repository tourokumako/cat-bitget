# ratchet ledger — PDCA 全記録（結果 / 原因究明 / 改善 / 修正 をすべて残す）

> **まこさんとの取り決め（2026-06-01 確定）**:
> - **審判（味見の機械）** = `scripts/priority_rebuild/score.py`（固定・`eval_engine` コスト・既知答えテスト pass 済）。全戦略はこれを通す以外に net を出せない。
> - **採点期間** = 2025-04〜2025-12（学習禁止）／**封印** = 2026-01〜03（過剰適合検出用・iteration 中は触れない・物理分離）。
> - **超える地面** = 手動 cat_v9（採点期間 月平均 **$172** ／ 12ヶ月通し **$354**）。
> - **A（戦略の値・特徴量・モデル選択）** = 実装前に詳細設計をまこさんに報告 → 結果で判断。
> - **B（未来漏れ / コスト甘 / 過剰適合 / 指標ズル ＝ 重大インシデント）** = コードの assert で物理的に止める（違反→スクリプト停止＝偽の数字を出さない・まこさんはチェックしない）。
> - 1周 ≤ 約5分・**数字を上げた変更＋そのコードだけ残す**（理解・設計・長文は蓄積に数えない）。
>
> **各実験に必ず書く**: 変更(A) / 結果(月平均・最悪月・$1900達成月数) / 原因究明 / 改善(次の一手) / 修正 / 採用 or 破棄

---

## E0: 地面測定（手動 cat_v9・ベースライン）
- **変更**: なし（基準を測るだけ）
- **方法**: 既存 365日 replay の売買記録を score.py に通す（`replay_csv.py` は実行せず＝保護ファイル）
- **結果**: 12ヶ月通し 月平均 **$354**（合計 $4,254）／ 採点期間 2025-04〜12 月平均 **$172** ／ 封印 2026-01〜03 月平均 $901。月次は −$144〜+$1,896 でバラつき・利益99%が下落5ヶ月・全月≥$1,900 は **0/12**。
- **原因究明**: 手動の稼ぎは下落 regime 集中（SHORT 継続）。LONG(P1/P4) は下げ期で負け（−$453/−$30）＝ regime 依存。
- **⚠️ P23単独 と 地面$172 の関係（最重要前提・2026-06-04 確定）**: ライブ Bot（`cat_v9_decider`+固定params）は `ENABLE_P23_SHORT` のみ有効（手動時代に Priority を1つずつ調整し P23 まで仕上げた段階）。**ただし地面 $172/$354 は別物＝「全Priorityをオンにした状態」（replay `--regime --regime-safe`＝regime切り替えの全部入り）で測った数字**。2026-06-04 にV9全部入りを再実行→既存地面と **sha256 一致＋score.py $172.68** で確定。**「P23単独の数字」ではなく V9 全設計の実力**（全Priority動かしてもこれ・利益は下落集中・全月$1,900は **0/9**・上げ/レンジPriorityは寄与ほぼなし）。詳細 auto-memory [[manual_v9_p23_only_reason]]。
- **採用/破棄**: 採用（ベースライン確定＝超える対象）
- **再現**: `python3 scripts/priority_rebuild/score.py results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv --start 2025-04-01 --end 2025-12-31`

## E1: 配管確認（捨て戦略 coinflip）
- **変更**: 方向を seed 固定乱数で決めるダミー戦略（`strat_coinflip.py`）
- **結果**: 採点期間 月平均 **−$268**（9ヶ月中8ヶ月マイナス）
- **原因究明**: 方向デタラメ → gross ≒ 0、コストだけ残る。予測通り明確マイナス。
- **採用/破棄**: 破棄（役目＝配管確認のみ）。判定 = **配管 OK**（戦略→CSV→審判→数字 が動き、審判がエッジ無しを正しくマイナス判定）。
- **再現**: `python3 scripts/priority_rebuild/strat_coinflip.py` → `python3 scripts/priority_rebuild/score.py results/priority_rebuild/ratchet/trades_coinflip.csv`

## E0.1: 計器修正（SL を maker に・2026-06-02）
- **変更（B 計器の修正）**: `eval_engine` / `score.py` で SL を taker → **maker** に修正。根拠: run_once_v9.py L320-348 で TP も SL も `place-tpsl-order`（executePrice=triggerPrice）＝指値 maker。手動は手数料負け回避で entry/exit とも maker 優先（まこさん指摘・2026-06-02）。成行 taker は TIME/TRAIL_EXIT/MFE_STALE 等の能動クローズのみ。
- **再検証**: 既知答えテスト **9/9 pass**（計器壊れず）。
- **地面への影響**: 12ヶ月 $354.54→**$354.99** ／ 採点期間 $172.22→**$172.68**（ほぼ不変・手動の SL_FILLED は 1,157中3件のみ）。ただし v1 では SL の taker 過大計上を防ぐ意味で重要。
- **発見**: 手動の出口は約8割が taker（TRAIL 598 / TIME 152 / MFE_STALE 114 の能動成行）。v1 の固定出口（TP/SL 指値＋時間切れ）は時間切れ以外 maker ＝手動より maker 寄り。

## E2: v1（最初の本物の戦略）← 次
- **状態**: **設計確定（A・実装前・2026-06-04 まこさん確認済）**。詳細設計 = [`strat_v1_design.md`](strat_v1_design.md)（§4.6 H1-H14 照合つき・全9節）。
- **変更(A) 設計サマリ**:
  - モデル: LONG/SHORT 別 LightGBM 2値分類（ラベル = 固定出口で simulate して net>0 なら勝ち）
  - 特徴量: 手動10指標（複数期間）+ ローソク足の形 + バンドタッチ + 時間軸（ラグ/ローリング/変化/遷移）+ regime + MTF(5m〜4h)。**閾値は木が学習 / パラメータ（期間）は短中長の複数候補を用意し木が選ぶ**。1432全投入はしない
  - 出口: 固定maker（LONG TP0.6%/SL2%/96bar・SHORT TP0.8%/SL2%/96bar）将来ML化
  - エントリー閾値 θ（ツマミ）/ サイズ 0.024固定（0.12内）/ 期間 学習〜2025-03・採点2025-04〜12・封印2026Q1 / entry・出口とも maker・不約定モデル(eval_engine)
- **判定**: 採用 = 戦略 net（score.py 採点期間で手動 $172 超えるか）/ 診断 = ブロック単位 ablation（substitution 対策で束ねて引く・de Prado CFI）
- **V9照合**: cat_v9_decider/params 精読で Entry 要素を全数照合 → 材料に網羅（ローソク足の形・バンドタッチ・複数期間を追補）。Entry外（MAX_ADDS/Exit/サイズ/動的TP）は v1 スコープ外と切り分け
- **§4.6 照合**: H1-H14 照合済。H2(leak: train末<採点始+embargo) / H6(価格非依存) / H8(期間分割) / H9(最小注文) / H12(異常値STOP) は実装時に assert 追加（⬜→実装で✅化）
- **実装**: `scripts/priority_rebuild/strat_v1.py`（B 関所 H6/H8/H9/H1 assert 稼働・全 pass）。学習 LONG best_iter=33(勝率ラベル0.642)/SHORT=25(0.581)。
- **結果（2026-06-04 初回採点・2025-04〜12）**: 月平均 **−$897.61**（合計 −$8,078）/ 最悪月 2025-11 **−$2,581** / 全月≥$1,900 **0/9**。trades=6,669（月741・手動 replay 月96 の約7.7倍）/ side LONG4843:SHORT1826 / exit TP52%・TIME38%・SL10%。
- **判定**: **破棄**（地面 手動 +$172 を大きく下回り、coinflip −$268 すら下回る）。
- **原因究明（ML設計の不具合・データ/枠組みのせいにしない）**: ①**LONG偏重(4843:1826)で下落相場 2025-10/11/12 に大損(−$5,700)** = 手動の勝ち筋(下落SHORT)を捉えず・regime を木が方向選択に活かせていない ②大量entry(θ0.5緩い→月741・手動7.7倍)でコスト負け ③TP0.6%/SL2%非対称で勝率inflated(0.64)も net 期待値負け ④TIME決済38%=方向外し多い。
- **改善（次の一手・1変更ずつ）**: 候補 = θ厳選(entry数↓) / LONG-SHORT 方向是正(regime を効かせる) / TP-SL リスクリワード是正 / ラベル定義厳格化。最致命は①方向 → 次周で1つ試して採点。
- **再現**: `python3 scripts/priority_rebuild/strat_v1.py` → `python3 scripts/priority_rebuild/score.py results/priority_rebuild/ratchet/trades_v1.csv --start 2025-04-01 --end 2025-12-31`

## E3: v1 出口 TP/SL 対称化（先生を厳しく・2026-06-04）
- **変更(A)**: ラベル/実出口の TP/SL を 0.6-0.8%/2% → **対称 1.0%/1.0%**（小さいTPの"まぐれ勝ち"を○にしない＋1回の負けを半減）。`strat_v1.py` SIDE_PARAMS のみ変更。
- **結果（2025-04〜12）**: 月平均 **−$429.95**（合計 −$3,870）/ 最悪月 2025-11 −$2,805 / 全月≥$1,900 0/9 / **黒字月 6/9**。trades 6,669→**2,937**（半減）/ exit TIME35%・SL33%・TP32%。
- **E2比較**: −$897.61 → **−$429.95**（マイナス約半減）。
- **原因究明（新たに露呈）**: ①**SHORT が完全死亡（全2,937件 LONG・SHORT 0件）**。対称1:1で SHORT ラベル勝率 0.472<0.5（best_iter=1）→ 木が SHORT を出さない。②下落月(06/08/11)で LONG 大損(−$1,474/−$1,798/−$2,805)残存＝方向を場面で切替できてない（regime 未活用）。
- **判定**: **採用**（数字が上がった: −$897→−$430。TP/SL 1:1 を残す）。手動 +$172 には未達。
- **次の一手（E4）**: 方向問題。SHORT を生かす／regime で下落時に SHORT を選ばせる。
- **再現**: `python3 scripts/priority_rebuild/strat_v1.py`（SIDE_PARAMS tp/sl=0.010）→ score.py（上に同じ）

## E4: V9ベース ML メタフィルタ（勝率で採用/見送り）+ MTF（2026-06-05）— 破棄
- **方針転換**: v1（ゼロからML）を破棄 → **V9を踏襲（候補＝V9 / Exit＝V9）しハードコード部分だけML化**（[[policy_v9_base_ml_unlock]]・GO 2026-06-04）。
- **前提訂正（重要）**: 地面 $172/$354 は「P23単独」でなく**V9全部入り（regime切替・全Priority）の数字**と確定（sha256一致＋score.py $172.68）。5年暖機データで採点期間は **$149.50/月**（365d版$172.68との差は2025-04のregime暖機差・他月一致）。比較は同源5年の $149.50。詳細 [[manual_v9_p23_only_reason]] / [[v9_priority_styles]]。
- **変更(A)**: V9全部入りの各候補に LightGBM で「勝つか(net>0)」を予測し prob≥θ で採用。特徴量＝5m指標(atr/bb_slopeはpct化=H6)+MTF(15m/30m/1h/4h・leak-safe)+regime+side+priority。`scripts/priority_rebuild/strat_v9_ml.py`新規（V9本体不変）。学習<2025-04/採点2025-04〜12/封印除外・embargo・leak assert。
- **結果(採点2025-04〜12)**: AUC **0.673**（選別力あり・MTFも top15 で効く）。だが net は θ↑で**悪化**：取る全部 **$149.50** / θ0.65 **$83.5** / θ0.70 $12.3。地面を超えず。
- **原因究明（data確定）**: corr(ml_prob, net_usd)=**−0.027**（無相関）。低prob群(勝率0.43)が net+$620、avg_net は prob下位50%$3.61 vs 上位50%$0.54（低probが7倍）。**勝率最大化は大勝ちを切る＝edge逆行**。根本＝①ラベルが勝率(net金額でない) ②**スタイル違いPriorityを1モデルに混ぜた**（P21スキャル小勝ち＋P23ポジション大勝ち）。
- **判定**: **破棄**（数字が上がらない・θ↑で下がる）。安価に「勝率メタ・スタイル混在は間違い」を確定＝ラチェット機能。
- **改善（次の一手・合意方向）**: **Priority（スタイル）別にML化・Entry/Exitをセットでnet最適化・予測対象は勝率でなくnet金額**（出口を同サイズに揃えれば勝率≈net）。MTF入力。詳細 `.claude/ratchet/session_log_20260605.md`。
- **再現**: replay全5年(`--regime --regime-safe`)→`strat_v9_ml.py`→`score.py results/priority_rebuild/ratchet/trades_v9_score_unfiltered.csv --start 2025-04-01 --end 2025-12-31`（θ掃引は ml_prob 列）。
