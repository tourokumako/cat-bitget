# acceptance — M2-B-3 監査（CP11）の指摘の反映（採用12件・iter="m2-b3-audit-fixes-20260901"）

<!-- ARC order=1 iter="m2-b3-audit-fixes-20260901" 前提="M2-B-3 の監査（CP11・2026-09-01）は Verdict GO・Critical 0件。指摘13件への採用12・不採用1の判定は 2026-09-01 にチャットで出し、まこさん「進めてよい」（worklog 20260901 §3）。審査に使う「機械が読む判定」は直しの前後で同じ中身" 採否="仕組みと文書の直し（売買なし・採否なし）" base_csv="" score_csv="" train_csv="" 狙い="レンジの相場の法則の出どころ・説明を実物と一致させ、行番号ドリフトを機械で止め、監査が見つけた抜け（時間帯・曜日）を法則に足す＝M2-B-4 以降を正しい土台の上に載せる" 内容="regime_laws.json＝誤り3件（E1・E2・E3）の直し・R11（時間帯・曜日）の追加・注意/相互参照/級の直し・穴1への警告。gen_regime_kb.py＝--verify に file:line 引用の実在検査（check_citations）を追加" 方法="前後突き合わせ（一文・機械が読む判定の差0件を機械で確認）＋check_citations の実測（直した後の引用全件 pass・わざと番号をずらすと ❌）＋gen_regime_kb --write→--verify ✅＋exec --selftest 回帰＋G2→H2" -->

TARGET: .claude/tools/gen_regime_kb.py
（データの直し＝`.claude/ratchet/regime_laws.json`。scripts/priority_rebuild/*.py は1本も触らない）

## DESIGN_CONTRACT

```json
{
  "impl_file": ".claude/tools/gen_regime_kb.py",
  "self_check_calls": ["check_citations", "coverage", "verify_one", "_kakeru"]
}
```

## 何を作るか（1まとまり＝M2-B-3 の監査の指摘の反映・採用12件）

### A. regime_laws.json の直し（10点・★法則の一文と「機械が読む判定」は1文字も触らない）

| # | 指摘 | 直す欄 | 直す中身 |
|---|---|---|---|
| 1 | E1（Major） | R8 の出どころ | 「RG-v5 `range_ok_rg5`（`e37_range_scalp.py:1615`）」→「RG-v5 `_rg5_frames`（`e37_scalp.py:517`）・`_apply_rg5_to_5m`（`e37_scalp.py:548`）＝正本。`_rg5_frames` は `e37_range_scalp.py:1588` で import（2026-08-20 の一本化）」。実物で確認済み（1615行は tp_ge_sl_check_v11 の中） |
| 2 | E2（Minor） | R7 の注意 | 「`engine_tuner_exec.py:2247`」→「`wpct_arr`（`engine_tuner_exec.py:2464`）」。判定側の引用も検査が対応づけられる形へ＝「帯の内側の隙間が `V11_ZONE_MIN_W` 以上（`e37_scalp.py:479`）」。実物で確認済み（2464行に W% の式・479行に V11_ZONE_MIN_W の比較） |
| 3 | E3（Minor） | R5 の説明 | 「1本ずつの値動きの合計 ÷ 全体で進んだ幅」→「1本ずつの値動きの合計 ÷ n本ぜんぶで動いた幅（最高値−最安値）」（監査の並記案どおり・KB L100 の式と L106 に一致させる） |
| 4 | 改善5 | R1 の注意 | 「★「最低3回」の数字は目安＝範囲で探す（C9）。外部の幅＝StockCharts Rectangle は片側2（逐語 "At least two equivalent reaction highs are required to form the upper resistance line and two equivalent reaction lows to form the lower support line."）／LuxAlgo ≥3／自前実装 `V11_ZONE_TOUCH`＝2（`e37_scalp.py:123`）＝穴7の材料」を足す |
| 5 | 改善4 | R6 の級・出どころ・注意 | 級【要約】→【本文】（2026-09-01 に本文を開いた）。出どころに URL。注意に逐語2つ（"A Bollinger Band Squeeze is a condition that occurs when the Bollinger Bands narrow due to decreased volatility."／"Note that narrowing bands do not provide any directional clues."）と「★スクイーズは大きな動きの前触れでもある（"can foreshadow a significant advance or decline"）＝レンジの終わりの接近と同じ現象」を足す |
| 6 | Q3（R6×R10） | R6・R10 の注意 | 役割の1行ずつ＝R6「★役割＝レンジ検出の入力。R10（検出の後の下位分類）とは役割が違う」／R10「★役割＝検出の後の下位分類（静か／荒いを出口・サイズに効かせる）。R6（検出の入力）とは役割が違う。動きがほぼ同じ2本を重ねる件は C3 が別に見る」 |
| 7 | N2＋Q3（R4×C6①） | R4 の注意 | 2行＝①「★レンジ中は帯の外へのヒゲ抜け（だまし）が頻発する＝帯の外の1タッチでレンジ終了と判定せず、終値と確認本数で見る（LuxAlgo 逐語 "False breakouts are common in sideways markets."）」②「★C6①（何本 続いたら成立）のレンジ適用＝同じ機構。統合はしない（C6 は共通の法則・R4 はレンジへの要求）＝相互参照だけ」 |
| 8 | Q3（R3×C4） | R3 の注意 | 「★C4（執行足より上の部品1本）とは別物＝C4 は部品C（強さ×上位足）で常に満たす。R3 は構造・位置の部品が上位足に在ることを求める。実測＝組む側の30案のうち12案は C4 を通るのに R3 を破る（worklog 20260830 §7（4））」 |
| 9 | N1（改善2） | 法則 R11 を追加（場面＝レンジ） | 一文＝「レンジ判定の頻度と閾値は、時間帯（欧米株式市場の取引時間）と曜日（平日/週末）で水準が変わる前提で扱う」。級【本文】。出どころ＝Wang, Jying-Nan／Liu, Hung-Chun／Hsu, Yuan-Teng（2020）Finance Research Letters 34＋URL＋逐語3つ（reverse V-shaped／欧米株式時間に高い／平日≫週末・2026-09-01 に要旨を開いた）。**「機械が読む判定」は持たせない＝「判定の置き場」だけ持つ**＝「M2-C で UTC の時刻・曜日の列を足した後に決める（閾値の探索を時間帯別に扱う＝探索の側・束1つの審査の形にならない）」。注意＝★数字は目安（C9）＋★測る部品は いま材料に0件＝足すのは M2-C |
| 10 | 改善6の後半 | 穴1 の中身 | 「★逆向きの警告＝出来高の材料を足すとき「低出来高＝レンジ」を法則として焼かない。StockCharts Rectangle の逐語＝"Unlike symmetrical triangles, rectangles don't exhibit standard volume patterns."（レンジの原型パターンの資料自身が、標準の型は無いと書いている）」を追記 |

### B. gen_regime_kb.py の直し（1点＝改善1の後半）

- **`check_citations(d)` を新設し、--verify（laws）と --selftest に足す。**中身＝50件の法則の 出どころ・注意・説明 から `名前.py:行` の引用を全部 取り出し、1件ずつ ①ファイルが実在する ②行番号がファイルの行数の中に在る ③引用の直前の backtick の識別子（空白と = より前を切る）が、その行の前後5行に在る、を確かめる。1件でも外れたら ❌（--verify が落ちる）。
- **なぜ**＝出どころの行番号は手書きで、コードを編集すると黙ってずれる（E1・E2 はこれ）。違反の記録 #25 と同じ「引用と実物を突き合わせる関所の不在」なので、人の注意でなく生成の道具の --verify に載せる。
- **実測済みの下調べ**＝いまの引用は全50件の中に6件。試作の検査で本当のずれは2件（E1・E2）、1件（R7 の `e37_scalp.py:124`）は識別子の対応づけの誤検知だった＝③の「直前の識別子・空白と = より前を切る」はこの誤検知を消すための決めごと。

## なぜ作るか

- 法則は engine_tuner の審査（G7）の材料。出どころが実物とずれたまま M2-B-4（部品を数える）へ進むと、誤った土台の上に工程が載る。
- 監査（CP11）の指摘13件のうち採用12件（まこさん「進めてよい」2026-09-01・判定の全文＝チャットと worklog 20260901 §3）。不採用1件＝R4×C6① の統合（相互参照だけにする）。

## 完成の条件（何ができたら完成か）

1. **前後突き合わせ（プログラム）**＝一文が変わった法則 **0件**・「機械が読む判定」が変わった法則 **0件**。変わってよいのは R1・R3〜R8・R10 の 説明／注意／級／出どころ と、R11 の追加・穴1 の追記だけ（変わった欄の一覧を機械で出す）。
2. **check_citations**＝直した後の引用 全件 pass。--selftest で わざと行番号をずらした見本が ❌ になる。
3. **gen_regime_kb --write → --verify** 全部 ✅。「判定を揃えた場面」の数え＝レンジ **11件＝機械が読む判定 9件＋判定の置き場 2件（R9・R11）＋どちらも無い 0件**。
4. **engine_tuner_exec.py --selftest 全部 pass**（コードは触らないが、regime_laws.json を読むので回帰を実測。R11 は判定を持たない＝審査の結果が直しの前後で同じことをここで確かめる）。
5. **gen_materials.py --verify ✅ 一致**（126番の回帰）。
6. **印の取り直し＝G2（約30秒）→ H2（約5分・regime_laws.json は対象22ファイルの中）**。
7. net はゼロのまま（実験・採点・売買記録なし）。

## 深掘り4点

- **① 真因**＝file:line の引用が手書きで、コード編集による行ドリフトを突き合わせる関所が無い（違反の記録 #25 と同じ型）。抜け（N1）の真因＝法則集めが社内実物と取引所の資料に寄り、学術の時間帯研究を照らしていなかった。
- **② 期待値分解**＝net の勝率・平均損益は動かさない（売買に触らない）。動かすのは「M2-B-4 以降が誤った出どころの上に載る危険」と「次の行ドリフトが黙って通る危険」の2つをゼロに近づけること。
- **③ root か symptom か**＝root。行番号を直すだけ（symptom）で終えず、検査を --verify に載せて再発を機械で止める。
- **④ ベースアップ**＝監査 CP11 本体＋出典4件の本文を自分で開いて逐語を取り直した（WebFetch・Wang-Liu-Hsu 2020／LuxAlgo／StockCharts Squeeze／StockCharts Rectangle＝4件とも監査の引用と一致・worklog 20260901 §3（2））。

## ★疑似シミュ由来の固定値ゼロ

- この直しは数字を1つも決めない。R11 は閾値を持たない（★数字は目安＝C9・範囲で探す）。probe は使っていない。採否の判定そのものが無い（売買なし）。

## H16（1変更・過去失敗の不再演）

- 変更は1まとまり＝「監査 CP11 の指摘の反映」。個々の直しは独立だが、全部 同じ監査結果から来ており、審査の結果を動かさない（完成の条件4で実測）。
- 不再演＝#23（既存判定の再現の目的化）＝RG-v5・RG-v6 の定数も判定も持ち込まない。#25（「設定に書いてある」と「実物が読んでいる」の同一視）＝逆にこの直しは「書いてある」と「実物」を突き合わせる検査を足す側。

## 群2 の照合

- **まとめて非該当**＝売買のロジック・審判（score.py／eval_engine.py）・engine_tuner の2本のコード・期間・cap・約定・exit_reason のどれにも触らない（TARGET は文書の生成の道具＋法則のデータ）。

## 自己検査（わざと壊して止まるか）

1. check_citations＝行番号を1つずらした json を渡す → ❌（--selftest に見本として組み込む）。
2. 既存の selftest（マーカーの中に1行 足す → ❌）が5節とも pass のまま。
3. coverage＝R11 の「判定の置き場」を消した json を渡す → ❌（どちらも無い 1件）。

## 読んだもの（Read tool・このセッション）

- `.claude/tools/gen_regime_kb.py`（全文）／`.claude/ratchet/regime_laws.json`／`regime_detection_kb.md`（§11-2）／`e37_scalp.py`（120-129・477-481・517-548）／`e37_range_scalp.py`（1584-1591）／`engine_tuner_exec.py`（2460-2467）／`cat_requirements.md`／`exchange_spec.md`

## SPEC

- 実装の後に `python3 scripts/priority_rebuild/verify_design_contract.py --write .claude/state/acceptance.md --dry-run` で機械から書き出す（M2-B0・M2-B-2b と同じ）。
