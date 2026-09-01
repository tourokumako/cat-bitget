# 【監査結果・CP11】M2-B-3＝レンジの相場の法則10件（R1〜R10）の抜け・誤り・重複

- 監査日: 2026-09-01
- 依頼書: `.claude/audits/inputs/2026-09-01_m2b3_range_laws_cp11_audit_request.md`（wc -l 218行・全文 Read 済）
- 実施: auditor セッションの CC が Plan サブエージェント（cold start・本会話の文脈は渡さない）を起動して実施。外部検索は WebSearch / WebFetch で実施済み
- **Verdict: GO**（10件はこのまま M2-B-4 以降へ進んでよい）／ **Critical 指摘: 0件**

---

## 1. Step -1 監査対象の型宣言

- **文書型**＝相場の法則10件（R1〜R10）の「文としての中身」（一文・説明・出どころ）。正本＝`ratchet/regime_laws.json`、md＝`memory/regime_detection_kb.md` §11-2（機械生成）。
- 問いは3つだけ（Q1 抜け／Q2 誤り／Q3 重複）。「機械が読む判定」の実装の良し悪し・RG-v5/v6 の再現可否・1件ずつの net 効果は対象外（依頼書の禁止を遵守）。

## 2. Step 0 指摘前提確認（機械的証跡）

| 項目 | 実測 |
|---|---|
| 依頼書 wc -l | 218 行（全文 Read 済） |
| regime_detection_kb.md wc -l | 1345 行。§11-2＝L798-L869 ✓実在／§11-0〜11-1＝L676-L797 ✓／§11-7〜11-8＝L1096-L1119 ✓（依頼書の「L1118」は実際は L1119 が `KB_LAWS_END` マーカー＝実害なし） |
| regime_laws.json wc -l | 1241 行。`法則` 配下の R 番号＝**10件**。R1〜R10 の一文・級・説明が md L800-L811／L813-L869 と**完全一致**（機械抽出で照合） |
| 依頼書の表（L84-L95） | KB L800-L811 の表と一文・見ているもの・級が**一致**（「engine_tuner で書けるか」列のみ依頼書側で省略＝宣言どおり） |
| cp10a 依頼書 | 318 行。L12-L27 の注記（単品 net 判定の取り下げ）を読了＝本監査では同型の問いを立てていない ✓ |
| 出どころ実物照合 | R9 の「測るもの3つ」＝`indicator_combination_kb.md`:241-247 に逐語一致 ✓／R7 の `SCALP_FLOOR`＝`e38_logic_parts.py:23` ✓／`V11_ZONE_MIN_W=0.004`＝`e37_scalp.py:124` ✓／`e37_scalp.py:479`＝内側隙間 res_lo−sup_hi ✓。**不一致2件は Q2 に記載** |

## 3. 観点①〜⑦の所見 ＋ Q1／Q2／Q3

### 観点判定

| 観点 | 判定 | 根拠（1行） |
|---|---|---|
| ① 統計学的妥当性 | **PASS** | 数値は範囲で探す（C9）・単品判定をしない構え・穴9件の正直な自己申告。R6×R10 の順位相関も内部で既に実測済＝C3 と整合 |
| ② リスク管理 | **PASS** | R7（コスト床）・R9（実はトレンドだった割合＝誤判定の実測）・R8（否定条件）で「レンジと誤認して踏まれる」型の損を法則側で塞いでいる。穴9（C9×R7 の衝突）も既知として明記済 |
| ③ 認知バイアス | **PASS**（注記あり） | 出どころの印5つで確証バイアスを構造的に抑制。注記＝R1 の「最低3回」だけ ★数字は目安（C9）の注が無い（R5・R7 には在る）＝1つの数字への係留 |
| ④ ソフトウェア工学 | **FAIL**（限定） | 出どころの `file:line` 引用が機械検証されておらず、**2件が実物とずれている**（Q2 E1・E2）。gen_regime_kb.py --verify は md 改変検出のみで、コード行番号の実在は見ていない |
| ⑤ 再現性 | **PASS** | JSON 正本→md 機械生成の一方向。R1〜R10 の JSON↔md 一致を機械抽出で確認済 |
| ⑥ 実行プロセス | **PASS** | 取り下げ済みの2つの問い方（#23 コピー機／cp10a 単品 net）を依頼書自身が明示的に封じており、本監査もそれに従って実施できた |
| ⑦ 主エージェントバイアス | **PASS**（注記あり） | 依頼書の表は KB の忠実な複写＝誘導なし。注記＝R8 の級【実装】は自プロジェクトのコードが出どころ＝自己参照だが、印【実装】として宣言済みなので欺きではない |

### Q1 抜け＝**新しい抜け 2件**＋既知の穴への根拠づけ 2件＋要裏取り 1件

**N1（新・最重要）｜時間帯・曜日の周期性**
- ① 法則の一文（案）＝「レンジ判定の頻度と閾値は、時間帯（欧米株式市場の取引時間）と曜日（平日/週末）で水準が変わる前提で扱う」
- ② 出どころ＝Wang, Jying-Nan / Liu, Hung-Chun / Hsu, Yuan-Teng (2020) *Finance Research Letters* 34「Time-of-day periodicities of trading volume and volatility in Bitcoin exchange」。**要旨を本文で開いた・逐語**＝"the trading activity resembles a reverse V-shaped pattern throughout the day. The Bitcoin market exhibits noticeably higher trading volume and volatility during hours that coincide with the daytime trading hours of European and US stock exchanges... Both variables are substantially higher on weekdays than weekends."（https://ideas.repec.org/a/eee/finlet/v34y2020ics1544612319301904.html）
- ③ 測る部品＝UTC の時刻（hour-of-day）・曜日の列＋ボラ/出来高の時間帯別分位。materials に時刻由来の列を足すだけで書ける。
- 位置づけ＝R1〜R10・C1〜C10・穴9件のどれにも無い（穴5＝funding・清算とは別物）。BTC は 24/7 だが値動きの密度は一様でない＝5分足レンジ判定に直接効く軸が丸ごと欠落。

**N2（新・Minor）｜だまし抜けの頻発（レンジ終了の判定は1本の抜けで下さない）**
- ① 一文（案）＝「レンジ中は帯の外へのヒゲ抜け（だまし）が頻発する。帯の外の1タッチでレンジ終了と判定せず、終値と確認本数で判定する」
- ② 出どころ＝LuxAlgo「Neutral Trading: Profit in Sideways Markets」**本文を開いた・逐語**＝"False breakouts are common in sideways markets."（https://www.luxalgo.com/blog/neutral-trading-profit-in-sideways-markets/）
- ③ 測る部品＝帯（res/sup）と close・streak（既存材料で書ける）。
- 注＝C6②（入る線と出る線を別に）・R4（本数）が機構としては近い。ただし「だましはレンジで頻発する＝ヒゲでなく終値で境界を見る」という相場側の事実は未収載。

**既知の穴への根拠づけ（歓迎枠）**
- 穴1（出来高0件）への**逆向きの警告**＝StockCharts ChartSchool・Rectangle（本文・逐語）＝"Unlike symmetrical triangles, **rectangles don't exhibit standard volume patterns**. Sometimes, volume will decline as the pattern develops. Other times, volume will be choppy."（https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/rectangle.md）→ 出来高の材料を足すとき「低出来高＝レンジ」を法則として焼かないこと。パターンの権威自身が「標準の型は無い」と断言している。
- 穴8（帯の対の選び方）＝同 Rectangle 本文＝"At least **two** equivalent reaction highs are required to form the upper resistance line and two equivalent reaction lows to form the lower support line."＝外部の一次資料でも片側2点が最低線＝穴7・穴8 の裏取りが1件進んだ。

**要裏取り（開けなかった・挙げない扱い）**
- 「レンジの成熟度（長いスクイーズほど大きな抜けが近い）」＝検索要約には出るが、開いた本文（netpicks・StockCharts Squeeze）に逐語なし。**採用しない**（データ不足・理由: 本文逐語が取れなかった）。funding・清算連鎖（穴5）も同様に本文逐語まで届かず＝穴5 は「調べていない」のまま正しい。

### Q2 誤り＝**2件**（＋表現の食い違い1件・誤りでないもの1件）

**E1（Major）｜R8 の出どころの行番号が実物とずれている**
- どの行＝KB L858「**出どころ**＝【実装】RG-v5 `range_ok_rg5`（`e37_range_scalp.py:1615`）」（JSON 同文）。
- 何と食い違うか＝**実物の e37_range_scalp.py:1615 は `tp_ge_sl_check_v11`（R:R 検査）の中**であり、rg5 判定ではない。RG-v5 の実体は 2026-08-20 の一本化（同ファイル L1584-1588 のコメント＝「RG-v5 の2関数（_rg5_frames・_apply_rg5_to_5m）」）で **`e37_scalp.py`**（L518〜）へ移り、e37_range_scalp.py:1588 で import している。
- 法則の中身自体（帯あり ∩ 帯内 ∩ 非 uptrend）は e37_range_scalp.py:4336 の表示文「（帯対拡張 ∩ 5分帯内 ∩ 非uptrend）」と一致＝**一文は正しい。誤りは出どころの行参照のみ**。

**E2（Minor）｜R7 の注意の行番号が実物とずれている**
- どの行＝KB L852「engine_tuner の条件＝全幅 (res_hi−sup_lo)/close＝W%・`engine_tuner_exec.py:2247`」。
- 何と食い違うか＝実物の 2247 行目は `ok, _up = _regime_series(df, recipe)`。W% の式 `(res_hi - sup_lo) / c * 100.0` は **engine_tuner_exec.py:2464**。同型の行番号ドリフト。

**E3（Minor・表現）｜R5 の CHOP の説明が、引いている出典の式と読み違えを誘う**
- どの行＝KB L838「CHOP＝…1本ずつの値動きの合計 ÷ **全体で進んだ幅**」。
- 出典の逐語（KB 自身の §3-A A-2・L100 に写してある TradingView の式）＝"100 * LOG10( SUM(ATR(1), n) / ( **MaxHi(n) - MinLo(n)** ) ) / LOG10(n)"＝分母は「n本の最高値−最安値（動いた幅）」であって「進んだ幅（正味の変位）」ではない。「進んだ幅」は ER の分子の言い方（L120「まっすぐ進んだ距離」）で、同じ KB の A-2（L106「n本ぜんぶで**動いた**幅」）・L309（「n本の最高値 − 最安値」）とも食い違う。
- 書き換え案（元の一文は不変・説明のみ）＝
  - 元（1文字も変えず並記）：「②CHOP が 61.8 超（CHOP＝値動きのゴチャゴチャ度。1本ずつの値動きの合計 ÷ 全体で進んだ幅。高いほど行ったり来たり＝横ばい）」
  - 案：「②CHOP が 61.8 超（CHOP＝値動きのゴチャゴチャ度。1本ずつの値動きの合計 ÷ n本ぜんぶで動いた幅（最高値−最安値）。高いほど行ったり来たり＝横ばい）」

**誤りでないことの確認（突き合わせ済み・帰属違いゼロ）**
- CHOP の帰属＝Bill (E.W.) Dreiss・1990年代初頭・豪州の商品トレーダー＝外部で確認（https://www.netpicks.com/choppiness-index-by-bill-dreiss/ ・https://www.tradingview.com/support/solutions/43000501980-choppiness-index-chop/）。61.8/38.2 も出典どおり ✓
- ER の帰属（Kaufman）と式＝KB A-3 の StockCharts 逐語と一致 ✓／MMI の「高いほどレンジ寄り」＝Financial Hacker 逐語（"the more trending the market becomes, the more the MMI decreases"）と整合 ✓
- **R6 は誤りなし・むしろ級を上げられる**＝本監査で StockCharts Squeeze の本文を開いた。逐語＝"A Bollinger Band Squeeze is a condition that occurs when the Bollinger Bands narrow due to decreased volatility."／"Narrowing bands do not provide any directional clues."（https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze）＝R6 の一文・「抜けの向きは教えない」と一致＝【要約】→【本文】へ昇格可能。
- 参考観察（実装スコープ寄り・判定はしない）＝R5 の説明は ①ADX②CHOP③ER④**MMI** の4つを挙げるが、機械が読む判定の family は ADX/CHOP/ER/**VHF**（VHF は級【要約】・A-6）。散文と機械欄で4つ目が違う。

### Q3 重複＝**4対**（全対「残す」判定・1対のみ統合候補）

| 対 | 同じところ | 違うところ | 裁定 |
|---|---|---|---|
| **R4 × C6①** | 「何本 続いたら成立」＝文字どおり同じ機構 | C6 は一般の分類（①streak ②ヒステリシスの2つを別扱い）／R4 はレンジ場面への**要求**（必ず入れる） | **統合候補**。残すなら R4 に「＝C6① のレンジ適用」と相互参照を1行。C6② が R4 に吸収されないよう、統合するなら C6 側へ一本化が安全 |
| **R3 × C4** | 上位足が枠を、下位足が執行を決める（MTF） | C4 は「部品1本が上位足」という一般則／R3 は**構造・位置（ゾーン）が上位足**という限定 | **残す**。機械が読む判定が別物（R3 は構造系統×上位足を数える）＝レンジ固有の強い形。相互参照のみ推奨 |
| **R2 × C2・C3** | 同系統を重ねない | C2/C3 は一般（問いレベル・実データレベル）／R2 は「構造1本＋補助は別系統」というレンジの構成則（RG-1 とセット） | **残す**。R2 は RG-1 の相方として構成を規定＝一般則に畳むと「補助3系統」の情報が落ちる |
| **R6 × R10** | 同じ「ばらつきの水準」軸（内部実測の順位相関も既知＝worklog 20260830 §7(1)） | R6 は**レンジ検出の入力**（低ボラ＝レンジ寄り）／R10 は**レンジ内の下位分類**（検出後に静/荒を分けて出口・サイズに効かせる） | **残す**。ただし役割の1行（検出 vs 下位分類）を両方の説明に足すこと。指標レベルで動きがほぼ同じなら C3 が片方を落とす＝法則を消す必要はない |

## 4. 外部検索結果サマリー（クエリ＋主要発見）

| # | クエリ | 主要発見 | 出典 |
|---|---|---|---|
| 1 | range-bound market detection rules / sideways indicators | ADX<25・BB 幅縮小・RSI 30-70・平坦 MA・ROC≈0・低出来高＝業界の定番はほぼ R5/R6/R10 で被覆済み | https://blog.elearnmarkets.com/5-indicators-for-range-bound-markets/ ・https://tradingliteracy.com/best-indicators-for-sideways/ ・https://www.luxalgo.com/blog/neutral-trading-profit-in-sideways-markets/ |
| 2 | support resistance touch count | 業界の扱いは「最低2・3以上で強い・多いほど強い」の**幅**。「複数タッチで強くならない」という反対論も存在 | https://tradersagency.com/blog/support-and-resistance-levels-trading-strategy ・https://forexmentoronline.com/support-resistance-levels-dont-become-stronger-with-multiple-touches/ ・https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/rectangle.md（逐語＝片側 "At least two equivalent reaction highs"） |
| 3 | Choppiness Index 帰属・式・閾値 | Bill (E.W.) Dreiss・1990年代初頭・式と 61.8/38.2（フィボナッチ由来）を確認＝KB と一致 | https://www.tradingview.com/support/solutions/43000501980-choppiness-index-chop/ ・https://www.netpicks.com/choppiness-index-by-bill-dreiss/ ・https://www.motivewave.com/studies/choppiness_index.htm |
| 4 | BB Squeeze 本文 | 定義と「向きは教えない」の逐語を取得＝R6 を【本文】へ昇格可能。同時に「大きな動きの前触れ」＝レンジの終わりの接近も同じ現象 | https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze |
| 5 | BTC の時間帯周期性（学術） | 逆V字の日内型・欧米株式時間にボラ/出来高が集中・平日≫週末＝**新しい抜け N1** | Wang, Liu & Hsu 2020, Finance Research Letters＝https://ideas.repec.org/a/eee/finlet/v34y2020ics1544612319301904.html ・https://www.sciencedirect.com/science/article/abs/pii/S1544612319301904 |
| 6 | crypto 5m scalping regime / funding・清算 | funding はコストとして控除すべき・清算カスケードで60秒未満に1%動く＝穴5 の方向は正しいが本文逐語まで届かず＝要裏取りのまま | https://cryptopulsehq.com/crypto-scalping-strategy/ ・https://www.ebc.com/forex/how-experts-use-crypto-scalping-to-capture-fast-profit |
| 7 | Rectangle（レンジの原型パターン） | 出来高に標準の型は無い（逐語）＝穴1 への逆向きの警告／最低タッチ片側2 | https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/rectangle.md |

## 5. 総合判定

**Verdict: GO**（10件はこのまま M2-B-4 以降へ進んでよい）

- 10件の**一文には、出典と食い違う実質的な誤りは1件も無い**。見つかった誤りは出どころの行番号ドリフト2件（E1・E2）と説明の言い回し1件（E3）＝法則の中身は変えずに直せる。
- 重複4対はいずれも「一般則 × レンジ適用」または「検出 × 下位分類」の役割違い＝一文を消す統合は不要（R4×C6① のみ統合候補）。
- 抜けは N1（時間帯・曜日）が唯一の実質的な新軸。M2-B-4 を止める性質のものではなく、法則の追加1件として積めばよい。
- Critical 指摘＝**0件**。

## 6. 改善方向性（優先度つき・6件）

| # | 優先度 | 提案 |
|---|---|---|
| 1 | **Major** | E1・E2 の行参照を実物へ直す（R8＝`e37_scalp.py` の `_rg5_frames`/`_apply_rg5_to_5m`（e37_range_scalp.py:1588 で import）／R7注意＝`engine_tuner_exec.py:2464`）。あわせて **`file:line` 引用の実在検査を gen_regime_kb.py --verify に足す**（cited 行に cited 識別子が grep で在るか）＝行番号ドリフトの再発を機械で止める |
| 2 | **Major** | N1（時間帯・曜日の周期性）を法則1件として追加（Wang-Liu-Hsu 2020 の要旨逐語つき・【本文】級）。測る部品＝UTC 時刻・曜日の列。穴5（暗号資産特有）の隣に置くと整理がよい |
| 3 | **Minor** | E3 の説明の書き換え（上記の並記案どおり・一文は不変） |
| 4 | **Minor** | R6 の級を【要約】→【本文】へ昇格（本監査が開いた StockCharts の逐語2つを注意欄へ転記）。同時に「スクイーズは大きな動きの前触れでもある（"can foreshadow a significant advance or decline"）＝レンジの終わりの接近と同じ現象」の注意を1行 |
| 5 | **Minor** | R1 の「最低3回」に ★数字は目安（C9）の注を足す（R5・R7 と同じ形）。外部の幅＝StockCharts Rectangle 片側2・LuxAlgo ≥3・自前実装 V11_ZONE_TOUCH=2（穴7 の材料として記録） |
| 6 | **Minor** | N2（だまし抜けの頻発）を R4/C6 の注意または法則1件として追加（LuxAlgo 逐語つき）。穴1 には「出来高に標準の型は無い」（StockCharts Rectangle 逐語）の逆向き警告を追記＝将来「低出来高＝レンジ」を無検証で焼く事故の予防 |

## 7. CC プロセス欠陥対策

- **該当1件**＝出どころの `file:line` 引用が、コード編集による行ドリフトで黙って腐る構造（E1・E2 は 2026-08-20 の一本化と以後の編集で発生したと推定）。これは違反記録 #25（「設定に書いてある」と「実物が読んでいる」を確かめず同一視）と同じ型の「引用と実物の突き合わせ関所の不在」。対策は改善1の機械検査（引用行の識別子 grep）＝人の注意ではなく生成器の --verify に載せること。
- 依頼書のプロセス自体は健全＝取り下げ済みの2つの問い方（#23・cp10a）を依頼書が自ら封じており、本監査で同型の問いを立てる誘因は無かった。

---

監査結果 終わり。
