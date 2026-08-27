# 監査報告 — M2 場面の判定（レンジ）の物差し 第4要素「スイング数≥2のゾーン対・幅≥0.4%」

- 監査実施日: 2026-08-27
- 監査区分: CP9 場面の判定（レンジ）・要素ごとの分割監査（13要素中の第4要素）
- 依頼書: `.claude/audits/inputs/2026-08-27_regime_element04_audit_request.md`（auditor セッションの CC が Read tool で全文 読了・815行）
- 実施の形: 依頼書の auditor 宣言どおり、別セッションの CC が Plan サブエージェントを cold start で起動した（依頼書パス＋着手前必読6件＋Q1〜Q3＋外部検索要請だけを渡した・起案セッションの文脈は渡していない）
- 着手前必読6件: Plan サブエージェントが全件 読了（milestones2 1,072行／regime_detection_kb 792行／materials 1,038行／signal_families 557行／composition_rules 145行／exchange_spec 289行・各 wc -l 実測）
- 言葉の注記: 本文の「生成器」＝案を作るプログラム（engine_tuner_gen.py）。「実行器」＝売買を回すプログラム（engine_tuner_exec.py）。

---

## 1. Step -1 監査対象の型宣言

**混合型**（3つ全部を含む）:
- **コード型**: `engine_tuner_gen.py`（sample_regime_build ほか）・`engine_tuner_exec.py`（build_regime_columns・G7）・`e37_scalp.py`（ゾーンビルダー）・`scripts/dashboard/build_regime_gate_rg.py`（RG-v5 正本）
- **文書型**: 凍結13要素表（milestones2 §3.4）・やることリスト M2（同 §4）・法則50件（regime_detection_kb §11）
- **数値型**: 実測 0/96・36/120・順位表（material_ranking.json）・ゾーン定数4つ（168h／0.003／2／0.004）

## 2. Step 0 指摘前提確認（依頼書の表・実測値 vs 実物）

| # | 依頼書の記載 | 実物との照合結果 |
|---|---|---|
| 1 | 対象8ファイルの sha256 | **6/6 一致を実測**（e37_scalp `039dd543b21b26b7`・build_regime_gate_rg `bbdbe1133de22c59`・engine_tuner_gen `ba71ae590754c8c4`・engine_tuner_exec `1263d57b36cee9d7`・milestones2 `775d35a8886a1bc0`・regime_detection_kb `34275a365feb9722`）。残り2件（_frozen_question／_template）は照合していない |
| 2 | 原因1（`_num_src` 印を外さず検査を呼ぶ） | **実物一致**。印を外す包みは `engine_tuner_gen.py:801-812`（`_cc`/`_vr`）・`strip_marks` は同 `:814-822`。外部呼び出し `regime_r9_diag.py:250` は `ex.validate_recipe(r, limits=lim)` を素通しで呼んでいる |
| 3 | 原因2（範囲内に使える数字が無い組を飛ばさない） | **実物一致**。`engine_tuner_gen.py:2029-2036`＝10回引いて全滅なら `SampleError`・「★次の組へ飛ばさない」と明記。禁止3の1d組の n_eff<30 は `signal_families.md` 禁止3表（stdev%50×1d＝11.0・kurtosis50×1d＝11.0 等）と整合 |
| 4 | 第4要素の行「`S-Rタッチ数(288,0.003)` の1件だけ」 | **★実物と食い違い（凍結表が古い）**。現在は **6通り**＝`observe_config.json` の `sr_windows: [144,288]`・`sr_tol: [0.0015,0.003,0.006]`（M2-2-6・2026-08-21）。`materials.md` 場所1・`signal_families.md` 禁止1にも6件が実在 |
| 5 | 同「窓288本と幅0.3%が名前に焼かれていて可変にできない」 | **★材料レベルでは既に解消済み＝食い違い**。`material_ranges`（`engine_tuner_gen.py:226-299`）がカタログの最小〜最大を範囲にし、`draw_param`（同 `:317-330`）・`_mat_drawn`（同 `:391-408`）が窓144〜288の任意整数・幅0.0015〜0.006の小数を引ける |
| 6 | ❌の判定そのもの | **維持（正しい）**。理由は下の Q1＝ゾーン対の組み立ては engine_tuner の外に在る |

## 3. 観点①〜⑦（PASS/FAIL）＋ Q1〜Q3 の所見

### Q1 — この1要素を、いまの engine_tuner は組み立てられるか

**組み立てられない。凍結表の ❌ は結論として正しい。ただし「足りないもの」は依頼書の表の記載（古い実測）とは別物である。**足りないものは4つ:

**(1) ゾーン対の組み立てが engine_tuner の外の固定コードに在り、要素の2つの数字がレシピから可変にできない。**
「スイング数≥2のゾーン対・幅≥0.4%」を実際に組んでいるのは RG-v5 のゾーンビルダー `build_regime_gate_rg.py:95-147`（`_zones_1h_rg`）で、定数は v17 のモジュール定数＝`build_range_gate_dashboard.py:50-53`（`ZONE_LOOKBACK=168`・`ZONE_TOL=0.003`・**`ZONE_TOUCH=2`**・**`ZONE_MIN_W=0.004`**）。同型定数が `e37_scalp.py:121-124`。engine_tuner に渡るのはビルダーの**結果の列だけ**（`engine_tuner_exec.py:2239-2249`＝`df["v11_res_lo"]` 等から geo を組む／出どころは `e37_scalp.py:517-547` `_rg5_frames`・`adaptive_k=None` 固定）。**レシピからゾーンビルダーの4定数へ渡る経路は0本**（`recipes/search_limits.json` に zone のキー0件・実測）。＝「スイング数≥2」「幅≥0.4%」は探す値になっておらず、engine_tuner はこの要素を**読める**が**組めない**。

**(2) 幅の定義が食い違っている。**要素の「幅≥0.4%」は**内側の隙間** `rz[0]−sz[1]`＝res_lo−sup_hi（`build_regime_gate_rg.py:147`・`e37_scalp.py:479`）。engine_tuner が条件に使える幅は **W%＝(res_hi−sup_lo)/close＝全幅**（`engine_tuner_exec.py:2247`・`indicator_reference_diag.py:4140-4141` RANGE_GEO_REF）。内側の隙間は ratio 列として存在しない（出口の `zone_sl w="inner"` にだけ在る＝`engine_tuner_exec.py:1491-1493`）。K-6 の幅条件（`engine_tuner_exec.py:1110-1111`）は要素と**別の量**を測る。

**(3) 代理部品 S-Rタッチ数は意味が別物。**`_sr_touch`（`observe_diag.py:363-372`）は `lvl = ca[i]`＝**いまの終値の価格帯**への窓内タッチ数。要素の「ゾーンごとのスイング数≥2・close の上下に対で揃う」ではない（レンジ中央に居るバーでは現値のタッチ数が少なくても帯対は存在する）。さらに「タッチ」（バーのレンジ重なり）と「スイング」（確定 fractal の本数・`sf._detect_fractals`）は数え方が別。なお生成器の閾値は `_thr_drawn`（`engine_tuner_gen.py:477-480`）＝分位（threshold_q）のみで、「≥2本」という整数の絶対値は生成束に書かれない。

**(4) 生成経路がいま壊れている（依頼書の実測を実物で裏づけた）。**原因1＝`regime_r9_diag.py:250` が印を外さない（0/96）。原因2＝`engine_tuner_gen.py:2029-2036` が使えない組を飛ばさない（外して36/120）。**Q1 の答えは「組めない」で、依頼書の2原因を直しても (1)(2)(3) は残る。**

**補足（断言できるプラス材料）**: location 役割の成績表を監査側で再計算した結果（`material_ranking.json`・location 10,482列・ranked_groups 相当の種類×時間足の中央値集計）、**組の1位・2位は S-Rタッチ数×15m／×10m**（列単位でも上位5件が全部 S-Rタッチ数・分離力 0.699〜0.743）。＝`sample_regime_build` の cond_b（r_b=1）はタッチ実績の部品を実際に選ぶ。R1 の「タッチ実績を条件に入れる」だけは生成束に入る——ただしこれは**データの性質による偶然の担保**で、設計（K-4）は系統しか見ていない（下の Q2）。

### Q2 — やることリスト（M2）のどの行が担保しているか

担保していると読める行は3つあり、**3つとも実物との食い違いがある**:

| 行 | 主張 | 食い違い |
|---|---|---|
| **M2-2-6**（✅済・milestones2:729） | 「決まった数字を範囲へ4件＝帯の窓 288→144〜288・帯の幅 0.003→0.0015〜0.006・**山と谷の本数 2〜2→2〜5**」 | 窓・幅の範囲化は**実在**（observe_config.json 実測）。だが範囲化されたのは**代理の S-Rタッチ数**のパラメータであり、ゾーンビルダーの `ZONE_LOOKBACK`・`ZONE_TOL` は 168・0.003 のまま固定。さらに「**山と谷の本数**」の実物は `fractal_k`＝**確定を待つ本数**（observe_config.json:222-226 の注記逐語「山と谷を確定させるまでに待つ本数」）であって、**要素4の「スイング数≥2」（ZONE_TOUCH）ではない**。ZONE_TOUCH を範囲化した行は M2 のどこにも無い |
| **M2-2-9**（✅済・milestones2:732） | 「書けない9件→0件・13要素が全部書ける」 | 検証は「**手書きの1束（条件14件）**が検査を通り真のバーが出た」＝**書ける**の確認。**生成器が組める**の担保ではない。実測（2026-08-27）＝生成経路は 0/96。さらに第4要素について「書けた」のは分位閾値の代理条件であり、ゾーン対そのもの（(1)(2)(3)）は書けていない |
| **M2-5-1**（✅済・milestones2:779） | 「100本 組んで92本が G5・G6・G7 を通る」 | ✅の後（59回目・2026-08-25 の78番の直し＝`_num_src` 印の導入）に**外部呼び出し経路が全滅する回帰**が起きた（原因1）。✅済の状態が黙って壊れており、それを検出するテストが外部経路に無かった（89番と同型・依頼書自身が認定） |

**「ゾーン対の組み立てを engine_tuner の中に持つ（またはビルダーの4定数を探す値にする）」行は、M2-1〜M2-11 のどこにも無い。**要素5の△（「RG-v5 が作った帯を読む列＝engine_tuner が帯を作っているのではない」）が第4要素にそのまま掛かるのに、これを解消する行が無い。M2-4 の K-4 は「構造・位置の系統1本以上」だけ（`engine_tuner_exec.py:1106-1108`）で、`close vs EMA9%` でも通る＝R1 の「タッチの実績」の特定性を強制していない。

### Q3 — 法則の一覧（50件）に穴があるか

**ある。4件**（＋軽微1件）:

1. **ゾーンの「対」の選び方の法則が無い。**R1 は「線が close の上下に揃っていたらレンジ」まで。実例の「**近い順・幅を満たす最初の対**」（`build_regime_gate_rg.py:97-99` の逐語・`e37_scalp.py:1976-1977`）という選択手続きは50件のどこにも無い。§11-7（穴の自己申告）にも無い（穴2は上げの2窓構成の話）。外部資料はゾーンの選抜・格付け（タッチ数・鮮度・フリップ）を明示的に法則化している（下の検索結果 2・6）。
2. **「タッチ」と「スイング」の数え分けの法則が無い。**R1 は「タッチ最低3回」、実例は「スイング数≥2」、実装は S-Rタッチ数（バー重なり）と fractal スイング束ね（`_zones_1h_rg`）の**2種類の別の測り方**が併存。どちらをどの場面で数えるかの法則が無いため、代理部品での置き換え（意味のずれ・Q1(3)）が検査に掛からない。
3. **幅の測り方（内側の隙間か全幅か）の定義が無い。**R7 は「コストを超える」だけ。実物は判定＝内側の隙間（`e37_scalp.py:479`）・条件材料＝全幅 W%（`engine_tuner_exec.py:2247`）と使い分けており、法則が定義しないため K-6 が別の量を測っても違反にならない。なお R7 の出どころ表記「SCALP_FLOOR（`e38_logic_parts.py:23`）＝実例の幅≥0.4%の根拠」は数字が合わない＝SCALP_FLOOR は **0.08%**（`e38_logic_parts.py:23`）、0.4% の実体は `V11_ZONE_MIN_W`（`e37_scalp.py:124`・a-priori v17）で **5倍**違う。
4. **絶対コスト床を分位閾値で書けない問題への法則が無い。**C9（範囲で探す）と R7（コスト超え）は衝突し得る＝値決め窓の W% 分布が丸ごとコスト未満の区間では、q10〜q90 のどの分位を選んでも「決まりを満たす」束が R7 違反になる。実行器には `const`（名前つき定数）の書き方が在る（`engine_tuner_exec.py:659`）のに、生成器の場面の束は分位しか引かない（`engine_tuner_gen.py:2086-2087`）。「コスト床は絶対値（named constant）で書く」という法則が50件に無い。外部資料はレンジ幅と往復コストを絶対比較で扱う（検索結果 7）。
5. （軽微）**ゾーン幅の上限（帯の膨張防止）の法則が無い。**外部資料は「ゾーンが際限なく広がるとタッチ数の意味が壊れる＝上限と再センタリングが要る」と明示（検索結果 1）。実物は束ね幅 tol で自然に制限しているが、法則には無い。

### 観点①〜⑦

| 観点 | 判定 | 根拠（1行） |
|---|---|---|
| ① 統計学的妥当性 | **FAIL** | 分位のみの閾値で絶対コスト床（R7）を書けない構造（Q3-4）＋2026-08-19 実測の凍結表を「事実データ」として監査入力にした（鮮度未管理・Step 0 #4/#5） |
| ② リスク管理 | **PASS** | 全経路 fail-closed（SampleError／RecipeError／G5-G7／H2・G2 印）・実弾への露出なし・H1/H5 不変。0.4% 床は現状ビルダー側で担保されている（`e37_scalp.py:479`） |
| ③ 認知バイアス | **FAIL** | 「書ける」（手書き1束）を「組める」（生成器）に読み替えた M2-2-9 の✅（確認したことと主張の範囲のずれ）＋「山と谷の本数」の語が2つの別物（確定遅延 k とスイング数）を指す混同（Q2） |
| ④ ソフトウェア工学 | **FAIL** | 同じ検証を2経路が別々に呼び片方だけ印を外す（`engine_tuner_gen.py:801-822` vs `regime_r9_diag.py:250`＝89番と同型の再発）＋✅済の後の回帰を検出するテストが外部経路に無い |
| ⑤ 再現性 | **PASS** | 順位・列挙とも決定論（`ranked_groups` の sort・`regime_draw_order`・seed 明示）。0/96・36/120 の機構を監査側で実物から再確認できた |
| ⑥ 実行プロセス | **PASS** | 「直す前に監査」「13分割・1要素」のまこさん決定どおり。スコープ逸脱なし。M2 停止判断も正当 |
| ⑦ 主エージェントバイアス | **FAIL（部分）** | 依頼書の原因1・原因2 は実物で正しい（共感ではなく検証済み）。ただし依頼書は第4要素の「実物」欄の陳腐化（6日前の作業で解消済みの記載）に触れず、「足りないもの」をゾーン対の組み立てでなく名前焼き込みの問題として提示している＝起案 CC の古い枠組みが凍結複写でそのまま監査対象化された |

## 4. 外部検索結果サマリー

| # | クエリ | 主要発見 | 出どころ |
|---|---|---|---|
| 1 | support resistance zone touch count validation trading rule | 2〜3回の明確な反応で水準は有効・1回は暫定。**ゾーンの無限拡張を防ぐ上限と再センタリングが要る**（帯化するとタッチ数の意味が壊れる） | [proplynq](https://proplynq.com/blog/how-to-trade-support-and-resistance-zones-in-2026)・[finaur](https://finaur.com/blog/en/education/how-to-identify-support-and-resistance-levels/) |
| 2 | support resistance zone clustering swing highs lows algorithm | ピボットを束ねてゾーン化・**タッチ数で強度格付け**・ATR でゾーン幅をボラ連動・壊れた水準の自動除去 | [LuxAlgo S&R Zones Strength Classifier](https://www.luxalgo.com/library/indicator/support-resistance-zones-strength-classifier/)・[LuxAlgo S&R Pro Toolkit](https://www.luxalgo.com/library/indicator/support-resistance-pro-toolkit/) |
| 3 | range bound market detection support resistance touch count | **サポートから最低2回・レジスタンスから最低2回の反発でレンジ確定**（＝実例のスイング数≥2 と同水準の業界相場）。タッチ品質を重み40%で採点する実装も在る | [stockgro](https://www.stockgro.club/blogs/stock-market-101/how-to-identify-range-bound-market/)・[LuxAlgo range-bound](https://www.luxalgo.com/blog/support-and-resistance-basics-in-range-bound-markets/)・[QuantConnect touch detection](https://www.quantconnect.com/forum/discussion/16677/support-amp-resistance-quot-touch-detection-quot/) |
| 4 | automated trading rule generation genetic programming market regime | 遺伝的プログラミングによる売買ルール自動生成は確立分野。ルールは条件式の木として生成され、レジーム切替モデルと併用される＝「条件の束の自動生成」は業界到達点の範囲内 | [ScienceDirect (risk-adjusted GP rules)](https://www.sciencedirect.com/science/article/abs/pii/S0957417411000595)・[ScienceDirect (GP trading rules)](https://www.sciencedirect.com/science/article/abs/pii/S0305054803000637) |
| 5 | pivot point confirmation delay repainting zigzag lookforward bars | ピボットは N 本後にしか確定しない＝**確定遅延は隠さず明示するのが正**。非リペイント実装＝「N 本後に真の位置へ描き、以後動かさない」（うちの j+2 確定・`fractal_k` と同型） | [PatternSmart](https://patternsmart.com/wp/why-do-some-trading-indicators-repaint/)・[ValorAlgo](https://www.valoralgo.com/blog/pine-script-repaint-mistakes) |
| 6 | （2 の補強） | フリップゾーン（S⇄R 転換）はタッチ数と並ぶ強度指標＝ゾーン格付けの法則群はうちの50件に未収載 | [AlgoStorm](https://algostorm.com/support-and-resistance-zones/) |
| 7 | range trading minimum range width transaction costs scalping | **レンジ幅と往復コストは絶対値で比較する**のが業界の型（例＝往復0.2%・幅2%→中央線利食いで正味0.8%）。幅が細いレンジはコスト後の期待値が立たない | [Blofin](https://blofin.com/en/academy/education/range-trading-strategies)・[FundedFast](https://fundedfast.com/learn/trading-strategies/scalping-strategy) |

## 5. 総合判定

**Verdict: NO-GO** — 第4要素は、いまの engine_tuner では組み立てられない（凍結表の ❌ は維持）。ただし ❌ の理由の記載が古い。要素の2つの数字（スイング数≥2・幅0.4%）は `build_range_gate_dashboard.py:50-53`／`e37_scalp.py:121-124` のモジュール定数に焼かれたままで、レシピから可変にする経路が0本（search_limits.json に zone キー0件・実測）。M2 リストにこれを解消する行が無く、依頼書の直し方の案2件（原因1・原因2）を実施しても本要素は組めるようにならない。あわせて、幅の定義の食い違い（内側の隙間 vs W% 全幅・`e37_scalp.py:479` vs `engine_tuner_exec.py:2247`）が K-6 の実効性を損なっている。業界の裏づけ＝タッチ2〜3回・幅とコストの絶対比較・ゾーン選抜規則はいずれも標準（§4）で、要素自体の設計は業界整合。組めないのはうち側のコードのつながりである。

## 6. 改善方向性（優先度つき・net 目標を下げる提案なし）

| # | 優先度 | 提案 |
|---|---|---|
| 1 | **Critical** | **M2 に「帯を作る」行を新設する**＝ゾーンビルダーの4定数（窓・束ね幅・スイング数・幅の床）を recipe の `meta.regime.build` から範囲で渡せるようにする（`build_range_geometry`／`_zones_1h_rg` のパラメータ化）。第4・第5要素の ❌/△ の根本。M2-2-6 の窓・幅の範囲化は代理部品（S-Rタッチ数）止まりで、ゾーン対そのものは1つも可変になっていない |
| 2 | **Critical** | **幅の条件に絶対床（名前つき定数）を書ける道を生成器に足す**＝`sample_regime_build` の cond_a が `_thr_drawn`（分位のみ・`engine_tuner_gen.py:2086-2087`）しか引かない。実行器の `const`（`engine_tuner_exec.py:659`）を使い、W% ≥ max(分位, コスト床) の形を許す。R7 の実効化。あわせて「内側の隙間」の ratio 列（(res_lo−sup_hi)/close）を RANGE_GEO_REF に登録し、要素と同じ幅を条件で測れるようにする |
| 3 | **Major** | **外部呼び出し用の検証の包みを1本にする**（原因1の直し・依頼書の案1と同方向）＝strip_marks 込みの公開関数を作り `regime_r9_diag.py:250` ほかを揃える。あわせて「外から呼ぶ経路」の自己テストを追加（89番と同型の再発を機械で止める） |
| 4 | **Major** | **順位から「範囲内に使える数字が1つも無い組」を除外する**（原因2の直し・依頼書の案2と同方向）。乱数に依らせないため範囲の全走査で判定する、という案の設計は妥当＝「使える中の1位から順」となり決定論が保たれる |
| 5 | **Major** | **凍結13要素表に実測日を刻み、依頼書生成時に再実測する**＝`gen_audit_request.py` が §3.4 を当時のまま複写するため、2026-08-21 に半分解消済みの記載が「監査対象の事実データ」を名乗った（本監査の Step 0 #4/#5）。残り12要素の監査でも同じ陳腐化が起きる |
| 6 | **Minor** | **法則一覧に4件追記**＝対の選び方（近い順・幅を満たす最初の対）／タッチとスイングの数え分け／幅の定義（内側 vs 全幅）／コスト床は絶対値で書く。出典は本監査の外部検索（§4 の 1・2・3・7）と実物（`build_regime_gate_rg.py:95-147`） |
| 7 | **Minor** | **K-4 の特定性**＝「構造・位置の系統1本以上」（`engine_tuner_exec.py:1106-1108`）を「帯・タッチ実績の部品1本以上」に絞るか、現状が location 成績表の1位＝S-Rタッチ数というデータの性質に依存していることを composition_rules.md に明記する |

## 7. CC プロセス欠陥対策

**該当あり・2件**:
1. **✅済の担保が「その時点の自己テスト」だけで、後の変更による回帰を検出しない**（M2-5-1 の✅が78番の直しで黙って壊れ、6日間 誰も気づかなかった＝発見は依頼書起案時の実測）。対策＝✅済の行に「担保する自動テストの名前」を紐づけ、そのテストは内部経路（`_vr`）だけでなく**外部呼び出し経路**（regime_r9_diag 等の実際の呼び方）を必ず含める。cc_role §1.4.6 に「✅済の主張には、それを毎回検証する機械の名前を添える」を追加。
2. **監査入力の鮮度検査が無い**（凍結表の複写が最新の実物と食い違ったまま「事実データ」節に載った）。対策＝`gen_audit_request.py` に「複写する実測値の測定日を明記し、測定日から N 日超なら再実測してから依頼書を作る」検査を足す。残り12要素の依頼書すべてに効く。

---

（本報告は Plan サブエージェント（cold start・依頼書のみ）の所見を、auditor セッションの CC が結果ファイルの型（7節）で保存したもの。所見の中身は変えていない。）
