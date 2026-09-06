# 【監査レポート・再監査】M2-C-4＝cp21 の指摘19件を、実際に直せているか（CP22）

- 監査日: 2026-09-05
- 監査区分: CP22（再監査＝cp21 の指摘19件が直っているか）
- 監査対象タスク: M2-C-4（決まった部品と形を実装する）
- 依頼書: `.claude/audits/inputs/2026-09-05_m2c4_cp22_reaudit_request.md`（★リポジトリ直下に在ります。ほかの依頼書は sdk 側に在るので置き場が割れています＝下の §9）
- 前回の監査: `.claude/audits/2026-09-05_m2c4_add_parts_cp21_audit_report.md`（NO-GO・Critical 3・Major 5・Minor 5・プロセス 6）
- 監査の実施: auditor セッションの CC が Plan サブエージェントを cold start で起動（依頼書 §auditor 宣言のとおり・メインセッションの文脈は渡していない）。所要 27分49秒・ツール実行 123回。

---

# 1. Verdict

# **NO-GO**

**理由（1行）＝cp21 の M2 を「張り付きの割合を測る節が観察の道具に無い」として測らなかったが、その節（検査12）は既に在り、実際に走らせたら 完成の条件4「帯の許容幅が ATR に連動する」が実データで成立していないことが出た。**

- 実測＝`observe_diag.py --inspect … --only 12`（**347秒・rc=0**）。
- 5分足で `S-Rタッチ数(288,0.0015)`（**固定 0.15%** の既存部品）と `S-RタッチATR(288,0.5,21)`（**ATR 連動** の新部品）が **実質 同じもの**（値の相関 **+0.9999978**）。
- cp21 の **P3**（駆動側の都合を「検査そのものが走れない」に一般化する）が、同じ回の中で再演されている。

---

# 2. 監査の制約（先に正直に書きます）

| # | 依頼書が求めたこと | 実施 | 理由 |
|---|---|---|---|
| 1 | C1「わざと数字を書き換えて `gen_materials.py --verify` が落ちるか」 | **未実施** | 監査の実行環境が read-only（ファイルの作成・変更・削除が禁止）。代わりに ①`--verify` の実測（rc=0）②検出の仕組みのコード読解による静的な証明 を出した。**この1件は、まこさんか依頼元 CC が手で1回 打って確かめてください。** |
| 2 | 走らせた副作用 | `results/priority_rebuild/ratchet/observe/*.txt` が書かれた（`--inspect`・`--selftest`）。**`.gitignore:15` で除外＝リポジトリの差分はゼロ。**ほかに `/tmp/x_only12.log`（リポジトリの外）。 |

**監査の前後で作業ツリーは同一**（`git diff --stat` の最終行＝`31 files changed, 2138 insertions(+), 959 deletions(-)`）。

**走らせた実測の秒数**

| コマンド | 秒数 |
|---|---|
| `gen_materials.py --verify` | 6.9秒 |
| `observe_diag.py --inspect --only 3` | 82秒 |
| `observe_diag.py --inspect --only 12` | **347秒** |
| `observe_diag.py --selftest` | 115秒 |
| `engine_tuner_exec.py --identity` | 7秒 |
| `engine_tuner_exec.py --selftest` | 5秒 |
| `verify_design_contract.py` | 5秒 |
| `gen_materials.py --selftest` | 34秒 |

---

# 3. cp21 の19件 対応表

★見出しは cp21 レポートの §6・§7 をそのまま数えた＝**Critical 3・Major 5・Minor 5・プロセス 6 ＝ 19件**（依頼元 CC の申告と一致）。

| # | cp21 の指摘（見出し） | 判定 | 根拠＝実際に打ったコマンドと出力 |
|---|---|---|---|
| **C1** | KB の件数を実測に直し、機械生成にする | **直った（ただし破壊テスト未実施）** | `jq '.bans.direction_stateful.parts\|length'`＝**142** ／ `.bans.direction_note.parts\|length`＝**6** ／ 重なり **0** ／ 和集合 **148**。`regime_detection_kb.md`:705 の機械生成ブロックの本文＝「向きを持たない部品 **148件**…**142件** ＋ **6件**、重なり **0件**」＝**完全一致**。`gen_materials.py --verify` → `✅ 一致（手で書き換えられていない）`・**rc=0** |
| **C2** | `_mmi` を原典の向きに直す／既知答えを差し替える | **直った** | 原典を WebFetch＝`// mind Data order: Data[0] is newest!` を確認。実装 `observe_diag.py:434-435` は原典と1行ずつ一致。awk で独立計算＝9点の並びで **原典 37.5000 ／ 直す前 62.5000**。実装は原典側の 37.5 を出す。`--inspect --only 3`＝**MMI200/300/400/500 とも「既知3/3」** |
| **C3** | 恒等の非退行を非退行テストで測る | **部分的** | `engine_tuner_exec.py --identity`（7秒）→ `レシピ実行器: 165 行 md5 7b01f51b5a9b29b3c05a7b340c203ba1 → ✅ 完全一致`。`--identity-l1-quick` を実際に打つと **hook が即ブロック**＝L1・S1 は本当に走らせられない。**★しかし文書が直っていない**（下の N-2） |
| **M1** | 需給の3層の配線を geo と同じにする | **部分的（①②のみ）** | ①`engine_tuner_exec.py:198 demand_enabled`・`:615` で G6 拒否＝geo と同型 ✅ ②`engine_tuner_gen.py:712-716` で `demand_ok` と照合 ✅ ③`grep -n "demand" engine_tuner_gen.py`＝**生成の行は0件**。`grep -rln '"demand"' recipes/`＝**0本**。geo は `:1339 m = {"geo": str(rng.choice(table["geo_ok"]))}` が在る |
| **M2** | `_sr_touch_atr` の上下限を足に合わせるか足を絞る | **直っていない ＋ 理由が事実と違う** | 下の Q2・N-1。`--only 12`（347秒・rc=0）で張り付きを実測できた |
| **M3** | 既知答えに荒れた区間・静かな区間の2水準 | **直った** | `indicator_reference_diag.py:1231-1240`＝見本①ATR%=0.5%／見本②ATR%=1.0%。期待値は `min(max(k*0.005,…))` と `min(max(k*0.01,…))` を別々に再導出＝定数の焼き込みを捕まえる。実測＝**S-RタッチATR 18件とも「既知2/2」** |
| **M4** | T-e を、いま在る道で測る／記録を訂正する | **直った** | `observe_diag.py:6469-6489`＝`load_demand(_bars_te.index)` を直接呼び、3種とも値を持つかを `ng` に足す。`observe_diag.py --selftest` → **✅ 全部 pass**（115秒・rc=0）。`next_step.md:134` に訂正文あり |
| **M5** | 禁止事項2 の白黒を まこさんに出す | **部分的（結論は正しいが、根拠2つでは支えられず、白黒も出していない）** | 下の Q2。`decisions.md:62` に「まこさん確定＝禁止事項2 には当たらない」が**残ったまま** |
| **m1** | 出典を実際の記事に直す | **直った（外部で裏取り済）** | `observe_config.json:268`＝「Boosting Strategies with MMI」＋URL。WebFetch で両記事を開いて確認（下の §5） |
| **m2** | `_sr_atr_k` に「この用途の範囲は未承認」を足す | **直った** | `observe_config.json:261` に逐語「**この用途での 0.5〜1.5 は未承認です**」 |
| **m3** | worklog の「6ファイル」を7ファイルに | **直った** | `session_worklog_20260904.md:636`＝「**7ファイル**（★…cp21 の m3 で直した）」 |
| **m4** | G2 と差分の大きさを実物から機械で埋める | **部分的** | `g2_pass.json`＝`d5cdb24a23ac06bb…`・**38件**・22:28:10 ✅ 申告と一致。**しかし差分の大きさは手写しのまま**＝申告 2049 に対し実測 **2138**（下の §7） |
| **m5** | 選べる列・種類の前後を記録に残す | **直った** | `materials.md:53-55`＝3520列(55.8%)／140種類。`git show HEAD:…materials.md`＝6061列(100.0%)／249種類 |
| **P1** | 文書の数字を機械生成にする | **部分的（同じファイルに手書きが3件 残り、この回で古くなった）** | 下の Q5-P1・N-3 |
| **P2** | 完成の条件の各行に「その数字を出したコマンド」の欄 | **部分的（欄は16行とも在るが、5行で宣言と実際が違う）** | 下の Q5-P2 |
| **P3** | 「測れない」と書くときは grep の出力で示す | **部分的（134番は直ったが、135番と M2 で同型を再演）** | 下の Q5-P3・N-1／N-2 |
| **P4** | 「まこさん決定」の行に逐語と日付 | **部分的（4か所のうち1か所の逐語が独立の記録に無い）** | 下の Q5-P4 |
| **P5** | 監査前ゲートを機械にする | **直していない（範囲外と宣言・妥当）** | まこさんの決定待ち＝121番の棚。この回の工事の外なのは事実 |
| **P6** | 壊すテストの終了コードを機械の控えに残す | **直していない（範囲外と宣言・妥当）** | `.claude/breaks/` は承認が2回 要る仕組み＝設計書 §6 に正直に明記されている |

**集計**

| 判定 | 件数 | 内訳 |
|---|---|---|
| 直った | **8件** | C1・C2・M3・M4・m1・m2・m3・m5 |
| 部分的 | **8件** | C3・M1・M5・m4・P1・P2・P3・P4 |
| 直していない | **3件** | M2・P5・P6 |

---

# 4. Q1〜Q5 の答え

## Q1｜Critical 3件は本当に直っているか

### C1 ＝ 直っている（数字は一致・機械生成は成立）。破壊テストだけ未実施。

数え直した実測:

```
$ jq '.bans.direction_stateful.parts|length' .claude/ratchet/signal_families.json   → 142
$ jq '.bans.direction_note.parts|length'      .claude/ratchet/signal_families.json   → 6
$ jq '[(.bans.direction_stateful.parts + .bans.direction_note.parts)|unique|length]' → [148]
$ awk '/BANS_COUNT_START/,/BANS_COUNT_END/' .claude/memory/regime_detection_kb.md
向きを持たない部品**148件** … `direction_stateful` **142件** ＋ `direction_note` **6件**、重なり **0件**。
$ python3 scripts/priority_rebuild/gen_materials.py --verify   → ✅ 一致  rc=0 （6.9秒）
```

**わざと壊す検査の代わりに、検出の仕組みをコードで確かめた**（`gen_materials.py:2244-2247`）。

```python
_cur = _bt[_s:_bt.index(_BANS_END, _s) + len(_BANS_END)]
if _cur != bans_count_block():
    ng.append(f"{_BANS_TARGET.name}: 向きを持たない部品の件数が型の表と食い違う…")
```

＝**ブロック全体の文字列の完全一致**なので、148 を1文字でも書き換えれば必ず不一致になり rc=1 になる。設計として穴は無い。**ただし実際に走らせて確かめてはいない。**

**★C1 に残る穴（N-4）**＝この新しい仕組みには **番人（わざと壊して落ちるか）が1つも無い**。`gen_materials.py --selftest` の S1〜S8・R1〜R9 に BANS の項目は0件。

### C2 ＝ 直っている。

原典（WebFetch した本文）:

```c
double m = Median(Data,Length);
int i, nh=0, nl=0;
for(i=1; i<Length; i++) {
  if(Data[i] > m && Data[i] > Data[i-1]) // mind Data order: Data[0] is newest!
    nl++;
  else if(Data[i] < m && Data[i] < Data[i-1])
    nh++;
}
return 100.*(nl+nh)/(Length-1);
```

実装（`observe_diag.py:425-445`）との1行ずつの突き合わせ:

| 原典 | 実装 | 一致 |
|---|---|---|
| `Median(Data,Length)`＝最新 Length 本の中央値 | `c.rolling(n).median()` | ✅ |
| `i=1..Length-1`＝Data[0]（最新）を除く n−1本 | `s = slice(i - n + 1, i)` | ✅ |
| `Data[i] > Data[i-1]`＝時系列では「その値 > 次の値」 | `gt[:-1] = a[:-1] > a[1:]` | ✅ |
| `Data[i] < Data[i-1]` | `lt[:-1] = a[:-1] < a[1:]` | ✅ |
| `100.*(nl+nh)/(Length-1)` | `100.0 * cnt / (n - 1)` | ✅ |

**cp21 が挙げた9点の並びを awk で独立に計算した結果:**

```
median=1
ORIGINAL(Data[0]=newest) = 37.5000
OLD(naive time order)    = 62.5000
```

実装は原典の向きを使うので **37.5** を出す。既知答えも差し替わっている（`indicator_reference_diag.py:1258-1263`）＝3件目は向きが逆だと 0.0 になる**割れる見本**。実測＝MMI4件とも「既知3/3」。

**★C2 に残る小さな穴（N-6）**＝`_mmi` の docstring は原典を「逐語」と書いているが、`// mind Data order: Data[0] is newest!` と `int i, nh=0, nl=0;` が落ちている（実装コメント :428-431 に説明が在るので実害は無い）。

### C3 ＝ 部分的。S2 は本当に一致。L1・S1 は本当に走らせられない。ただし文書が直っていない。

```
$ python3 scripts/priority_rebuild/engine_tuner_exec.py --identity        （7秒・rc=0）
[恒等1 separate] レシピ実行器: 165 行 md5 7b01f51b5a9b29b3c05a7b340c203ba1 → ✅ 完全一致
[恒等2 R14] … → ✅ 3者一致
[恒等検収まとめ] ✅ 全部一致
```

**L1・S1 を測っていないことが許されるか＝許される（構造上できない）。**実際に打って確かめた:

```
$ python3 scripts/priority_rebuild/engine_tuner_exec.py --identity-l1-quick
🔒 [設計↔実装ゲート] engine_tuner を指す DESIGN_CONTRACT が1本もありません（fail-closed）
```

理由もコードで裏が取れる＝hook の `CHECK` は `--identity` の完全一致でしか免除しない（`require_design_contract_before_run.sh:58-59` ＋ `hit = CHECK & set(flags)`）。`--identity-l1` は集合に無く、この設計書の `impl_file` は `observe_diag.py` なので fail-closed。**＝CC の「まこさんの決定待ち」は事実。**

**★ただし直っていない点（N-2・Major）**＝設計書 §6 の6行目は**いまも**「`leak_causality_diag.py` の恒等3本の一致（★**md5 そのものは出せません**＝`engine_tuner_gen.py` を走らせるには それを指す設計書が要り hook が止めるため）」と書いている。①`md5 は出せない` は誤り（今日 7秒で出た）②理由も誤り（入口は `engine_tuner_exec.py`）③指している `leak_causality_diag.py` は cp21 が「性質の違うテスト」と名指しした当のもの。**同じ誤りが `next_step.md` の135番にもそのまま在る。**

---

## Q2｜Major のうち直していない2件は妥当か

### M2（帯の許容幅の上下限）＝**逃げです。理由が事実と違い、実際に安く測れました。**

CC の理由（worklog §36-3・next_step 136番の逐語）＝「**張り付き割合を出す節が観察の道具に1つも無い**」。

**これは事実と違う。**`observe_diag.py` には **検査12（材料どうしの重複の総当たり）**が 2026-08-11 から在り、`--inspect … --only 12` で走らせられる（新しいコードも承認も不要）。実測（**347秒・rc=0**・出力そのまま）:

```
■ 検査12 材料どうしの重複を総当たりで出す
  値決め窓の 20000 本 × 571 列（5m）を総当たり＝162,735 通り
  ★実質 同じもの（|相関| ≥ 0.99999）= 5 組 ／ 近い組（≥ 0.999）= 28 組
     [実質 同じもの] S-RタッチATR(288,0.5,14) ↔ S-RタッチATR(288,0.5,21)（値の相関 +0.9999979）
     [実質 同じもの] S-Rタッチ数(288,0.0015) ↔ S-RタッチATR(288,0.5,21)（値の相関 +0.9999978）
     [実質 同じもの] S-RタッチATR(144,0.5,14) ↔ S-RタッチATR(144,0.5,21)（値の相関 +0.9999961）
     [実質 同じもの] S-Rタッチ数(144,0.0015) ↔ S-RタッチATR(144,0.5,21)（値の相関 +0.9999960）
     [実質 同じもの] S-Rタッチ数(288,0.0015) ↔ S-RタッチATR(288,0.5,14)（値の相関 +0.9999927）
  ・残す S-RタッチATR(288,0.5,14) ／ 省く S-RタッチATR(288,0.5,21)・S-Rタッチ数(288,0.0015)
```

**読み方（3つ）**

1. **ATR の期間（7/14/21）が効いていない**＝k=0.5 では許容幅が下端 0.15% に張り付き、ATR の期間を変えても同じ列になる。
2. **決定的**＝`S-Rタッチ数(288,0.0015)`（**固定 0.15% の既存部品**）と `S-RタッチATR(288,0.5,*)`（**新しい ATR 連動の部品**）が **実質 同じもの**。＝**やること4 の狙い「固定の割合でなく値動きの幅に連動」が、k=0.5 では 5分足で成立していない。**
3. **この工事は、カタログ唯一の「実質 同じもの」5組を作った**（工事の前は 0組）。18件のうち **6件（k=0.5 × 窓2 × ATR期間3）が固定幅の複製**。

＝**完成の条件4「帯の許容幅が ATR に連動して動く」は、既知答え（合成の見本2水準）では通るのに、実データでは k=0.5 で成立していない。**そして測る道具は既に在り、6分で答えが出た。**cp21 の P3 と同型。**

**限界も正直に**＝検査12 は5分足だけを回す。1分足・4時間足ごとの張り付き割合は出ない。それでも「節が1つも無い」は誤りで、執行足の5分足で既に成立していないことが分かる。

### M5（禁止事項2 の白黒）＝結論は正しい。ただし根拠2つだけでは支えられず、白黒も出していない。

**根拠2つは実物どおり在る:**

```
$ grep -n "material_param_ranges" scripts/priority_rebuild/recipes/search_limits.json
44:  "material_param_ranges": {},                     ← 空 ✅
$ sed -n '286,290p' scripts/priority_rebuild/engine_tuner_gen.py
  spec.append({"kind": "int" if is_int else "float",
               "lo": min(vals), "hi": max(vals), "dec": int(dec)})   ← ✅
```

**しかしこの2つは「範囲の表がどう作られるか」しか言っていない。**「engine_tuner が本当にその範囲から引くか」は別の行が担保している＝`engine_tuner_gen.py:405-411 _mat_drawn` の `param = draw_param(rng, family, ranges)`。ここを開いて初めて「点の一覧ではない」が成立する（`material_pool()` が作る `(family, param)` は**カタログの数字そのもの**で、そこから引いていたら「点の一覧」のままだった）。**CC が挙げた2つは、結論に届く途中まで。**

**白黒**＝cp21 の M5 は「**まこさんに出す**」だった。CC は自分で「当たりません」と決着させている。しかも文書が3つに割れている:

| 場所 | 書いてあること |
|---|---|
| `acceptance.md` §0-A M5 | 「**まこさんの決定待ち**」 |
| `acceptance.md` §8.1-2 | 「**白黒は まこさんが付けてください**」 |
| `worklog §36-4` | 「**実物で決着した。当たりません**」 |

さらに `decisions.md:62` に誤りが残ったまま＝「まこさん確定＝禁止事項2 には当たらない」（61行に訂正文を足しただけで、62行は消えていない）。

---

## Q3｜M1（需給の3層の配線）は geo と同じ形になったか

**①②は geo と同じ形になった。③が無いので、やること1 の目的は達せられていない。**

| 層 | geo | demand | 判定 |
|---|---|---|---|
| 印（indicator_switch） | `:175 d["_geo_set"]`／`:193 geo_enabled` | `:176 d["_demand_set"]`／`:198 demand_enabled`・`:615` で G6 拒否 | **同型 ✅** |
| 型の表（signal_families） | `:710-711 geo_ok` | `:715-716 demand_ok` | **同型 ✅** |
| 生成（抽選） | `:1338-1339 m = {"geo": str(rng.choice(table["geo_ok"]))}` | **0件** | **無い ❌** |

```
$ grep -n "demand" scripts/priority_rebuild/engine_tuner_gen.py
712/715/716（assert_provenance）・1196（表を読む）・2715/2730/2733/2741/2747/2749（既に在るときに列を載せる）
→ {"demand": …} を組み立てる行は0件
$ grep -rln '"demand"' scripts/priority_rebuild/recipes/     → 0本
```

**評価**＝**「材料になった」とは言えない。**満たされたのは「実行器が受け取れる」「不正な需給を弾ける」の2つで、**engine_tuner が案を作るとき需給の列が条件に選ばれる回数は、いまも構造上ゼロ回**（cp21 の Q1-補足と同じ結論が、直したあとも変わっていない）。

**乱数で引かない判断そのものは正しい**（違反の記録 #14・#24）。ただし geo が現に `rng.choice` で引かれている以上、「乱数だから作れない」は **geo との非対称**を説明していない。設計書の文言を「実行器が受けられるようにした（生成は M2-E）」に直したのは適切だが、`engine_tuner_milestones2.md` §6-8 の3つ目の源に需給を載せた以上、**印の上では「使う」なのに一生 選ばれない材料が3件 在る**状態。**「M2-E まで需給は使われない」と1行 添えるべき。**

---

## Q4｜測っていない3件は本当に「範囲の外」か

| 何 | CC の理由 | 判定 | 根拠 |
|---|---|---|---|
| **T-d**（前処理を付けた束の部品名を1文字 変える） | 「束を組む工程が M2-E だから」 | **範囲の外ではない＝cp21 の P3 と同型** | 検査の中身は「`_material_name` が pre 付きの材料でも未登録の名前を拒否するか」だけで、束を組む工程は要らない。`engine_tuner_exec.py:556-577` が pre を先に検証し、`:622-625` で `iref.find(name) is None → _fail("G6", …)`。**M2-E を待つ理由はどこにも無い。**（承認がもう1回 要るのは事実＝`selftest` は凍結一覧に無い。**ただし CC が挙げた理由はそれではない。**） |
| **T-f**（印から需給を1件 抜くと G6 が拒否する） | 「実行器の自己テストに需給の見本が無く、足すと承認がもう1回 要る」 | **理由は事実。ただし数が不正確** | `def selftest`（`engine_tuner_exec.py:3968`）以降に `demand` は **0件**。`_selftest_roundtrip`（:3788）にも 0件。凍結の一覧に `engine_tuner_exec.py` の `selftest` は無い＝足せば凍結ゲートに当たる。**＝「承認がもう1回」は妥当。**（CC の「需給の文字が出るのは実装側の4か所」は実測 10行＝軽微な誤り） |
| **M2 の列の実分布** | 「張り付き割合を出す節が観察の道具に無い」 | **範囲の外ではない＝cp21 の P3 と同型・しかも今回いちばん重い** | 上の Q2。検査12 を 347秒 走らせただけで答えが出た |

**＝3件のうち2件（T-d・M2）が、cp21 の P3 が名指しした型の再演。**しかも cp21 の P3 対策として設計書に入れた やること7-e（「測れない」と書くときは `grep` の出力で示す）は、**M2 と T-d の「測れない」には1度も適用されていない**（worklog §36-3 に grep の出力が1つも無い）。

---

## Q5｜プロセス対策 P1〜P4 は実際に効く形になったか

### P1（手で数字を書ける場所を消す）＝部分的。同じファイルの中に手書きが3件 残り、この工事でその3件が古くなった。

機械生成にしたのは KB の**1行だけ**（BANS_COUNT ブロック）。**同じ `regime_detection_kb.md` の 1283-1291行の表は全部 手書きで、今回の工事で古くなっている:**

| KB の行 | 手書きの数字 | いまの実測 | コマンド |
|---|---|---|---|
| :1287（5番） | 指標の種類 **256**（選べる **249**／選べない **7**） | 選べる **140**／選べない **118** | `sed -n '54,55p' .claude/ratchet/materials.md` |
| :1288（6番） | 材料の一覧 **261件** | **263件** | `sed -n '8p' .claude/ratchet/materials.md` |
| :1289（7番） | 部品 **551件**（＋別枠4件＝**555**） | **573件**（＋別枠 demand3・geo2・time2＝**580**） | `jq '.parts\|length'`＝573 |
| :1290（8番） | 「**555** に膨らむ理由」 | 555 は存在しない | 同上 |

**＝P1 が「これからも起きる」と診断した事故が、P1 を入れたのと同じファイルの、10行 下で、同じ工事によって現に起きている。**さらに、この新しい仕組みには番人（わざと壊す検査）が0件。

（P1 の良い点＝KB:709 の説明文にある 148/126/115 は「経緯の記録」なので古くなっても害は小さい。）

### P2（完成の条件に「その数字を出したコマンド」の欄）＝16行とも埋まっている。ただし5行で「宣言したコマンド」と「実際に使ったコマンド」と「その数字を出せるコマンド」が食い違っている＝cp21 の C3 と同じ型。

| 行 | 設計書 §6 の宣言 | worklog §36-2 で実際に使ったもの | 実測 |
|---|---|---|---|
| **6** | `leak_causality_diag.py` の恒等3本（★md5 は出せません） | `engine_tuner_exec.py --identity` | **食い違い**。しかも宣言側は cp21 が否定した「性質の違うテスト」のまま |
| **9** | `gen_materials.py --verify` の出力 | 「在る263／足す0／指紋 245d3e37e7850ef1」 | **`--verify` はその数字を出さない**。実行結果は `✅ 一致（手で書き換えられていない）` の1行だけ。その数字は `--write`／`--status`／`materials.json` から取ったもの |
| **11** | 承認の出力「🧊 N 件」＋ `impl_functions_frozen.json` | **7ファイル・22件** | **数が違う**（実測 **26件**・下の §7） |
| **12** | `grep -c` を `engine_tuner_requirements.md` の一覧に当てる | `git diff` で `observe_config.json` を見る | **3通り**。実際の 38件/89個 は `materials.md:90` の機械生成の値 |
| **16** | `engine_tuner_exec.py --selftest`（`demand_enabled` の往復）＋ T-f の rc | `verify_design_contract.py` の must_use（AST） | **食い違い**。`--selftest` に `demand` は0件＝宣言したコマンドではこの行を測れない |

**＝欄を足しただけでは「性質の違うものを後から当てはめる」を止められていない。**止めるには、その欄を機械が読んで、実際に打ったコマンドの出力と突き合わせる仕組みが要る（いまは全部 手書きの自由記述）。

### P3（「測れない」と書くときは grep の出力で示す）＝134番は直った。しかし同じ回で135番と M2 に同型が残り、再演している。

- ✅ **直った**＝`next_step.md` 134番に訂正文が入り、T-e が `--selftest` の中で実測されるようになった。`observe_diag.py --selftest` を走らせて **✅ 全部 pass（115秒・rc=0）**を確認。訂正の文は事実と合っている。
- ❌ **残っている**＝`next_step.md` **135番**（2026-09-05 付）が今も「恒等3本（S1・S2・L1）の md5 を出せない」「`engine_tuner_gen.py` を走らせるには…」「代わりに使えるもの＝`leak_causality_diag.py`」と書いている。**S2 は出せる（7秒で出た）。理由も誤り。代わりの手段は cp21 が否定した当のもの。**
- ❌ **新しく作った**＝M2 の「測る節が無い」（Q2）。**grep の出力は1つも添えられていない。**

### P4（「まこさん決定」の行に逐語と日付）＝4か所のうち、独立の記録で裏が取れたのは2か所。1か所は正直に取り下げ（良い）。1か所は逐語がどこにも記録されていない。

| # | 場所 | 逐語 | 独立の記録に在るか |
|---|---|---|---|
| 1 | やること1-f（案A） | 「案A にします。…§6 の8番に3つ目の源…そこに 需給3種と MMI の両方が入ります。…**手書きの一覧は作らないこと**」 | **❌ 在りません。**repo 全体を grep した結果、この逐語が出るのは `acceptance.md`（と その凍結コピー）・`milestones2.md:577`・cp21 の依頼書＝**全部 CC が書いた文書**。その日の記録 `session_worklog_20260904.md` §29 が残しているまこさんの逐語は「**1・2・4・5・6 を足す／3 は外す／需給は「使う」にする**」の1本だけ |
| 2 | §6 の8番との関係 | 「この、本来の目的が達成できるまでは、指標一覧はta 43種にする」 | **✅ 在ります**＝`session_worklog_20260827.md:1813` に逐語で一致 |
| 3 | §8 の E（J-6） | 逐語が無いので「まこさん決定」の書き方をやめた | **✅ 妥当（この処置は正しい）**。ただし**出どころの `next_step.md:43` は今も「（まこさん決定）」のまま**＝自分の設計書だけ直して、根の記録を直していない |
| 4 | §3.6（3 は外す） | 「3 は外す」 | **✅ 在ります**＝`session_worklog_20260904.md:596` |

**＝P4 の目的（逐語が本当に記録に在るか）は、1件目で満たされていない。**書いた逐語が独立の記録に在るかを照らす仕組みが無いので、**CC が自分で書いた文を自分で引用する**形が通る。

---

# 5. 外部検索の結果（MMI 原典）

**依頼元 CC の m1 の直しは正しい。**記事は2本 在り、CC の割り当ては原典と一致した。

## ① https://financial-hacker.com/the-market-meanness-index/ ＝「The Market Meanness Index」（計算の式）

```c
// Market Meanness Index
double MMI(double *Data,int Length)
{
  double m = Median(Data,Length);
  int i, nh=0, nl=0;
  for(i=1; i<Length; i++) {
    if(Data[i] > m && Data[i] > Data[i-1]) // mind Data order: Data[0] is newest!
      nl++;
    else if(Data[i] < m && Data[i] < Data[i-1])
      nh++;
  }
  return 100.*(nl+nh)/(Length-1);
}
```

本文の逐語＝`"If the MMI function is fed with perfectly random price changes from a perfectly efficient market, it will return a value of about 75%."`

**`MMIPeriod = optimize(` はこの記事の本文に無い**（読者コメント #56 に外部スクリプトの話として出るだけ）＝cp21 の指摘どおり。

## ② https://financial-hacker.com/boosting-systems-by-trade-filtering/ ＝タイトルは「Boosting Strategies with MMI」（期間の式）

```c
int MMIPeriod = optimize(0,200,500,100);
if(MMIPeriod) {
  MMIPeriod = checkLookBack(MMIPeriod);
  var *MMI_Raw = series(MMI(Price,MMIPeriod));
  var *MMI_Smooth = series(LowPass(MMI_Raw,MMIPeriod));
  DoTrade = falling(MMI_Smooth);
}
```

本文＝`"trades are opened and closed only when the smoothed MMI is falling, meaning that the market has entered trending mode within the last 200 to 500 bars."`／「1260 systems: 900 without MMI and 360 with MMI ranges of 200, 300, 400, and 500 bars」＝**200・300・400・500 で確定**。

**判定**＝`observe_config.json:268` の直し（式＝「The Market Meanness Index」／期間＝「Boosting Strategies with MMI」＋URL）は**原典と一致している。m1 は直っている。**

---

# 6. 新しく見つけた指摘

## Critical（1件）

### N-1｜完成の条件4「帯の許容幅が ATR に連動する」が、実データで成立していない。しかも測る道具は既に在り、6分で答えが出た。

- 実測＝`python3 scripts/priority_rebuild/observe_diag.py --inspect data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv --only 12`（**347秒・rc=0**）。
- 5分足で **`S-Rタッチ数(288,0.0015)`（固定 0.15%）と `S-RタッチATR(288,0.5,21)`（ATR 連動）が「実質 同じもの」（値の相関 +0.9999978）**。144窓でも同じ。
- **この工事は、カタログ唯一の「実質 同じもの」5組を作った**（工事の前は 0組）。18件のうち **6件（k=0.5）が固定幅の複製**、k=1.0 の ATR期間 14↔21 も「近い組」。
- **既知答え（合成の2水準）は通るのに実データでは通らない**＝合成の見本だけでは担保にならないことが実証された。
- **やること**＝(a) M2 の直しを M2-E に送る前に、この実測を まこさんに出す (b) 完成の条件4 の判定に「実データで k の3水準が別の列になるか」を足す (c) `next_step.md` 136番の「測る節が無い」を訂正する。

## Major（4件）

### N-2｜C3 の文書が直っていない＝cp21 が否定した主張が、いまも2つの生きた文書に在る。

`acceptance.md` §6 の6行目と `next_step.md` 135番が、どちらも「md5 そのものは出せません」「理由＝`engine_tuner_gen.py` を走らせるには…」「代わりに `leak_causality_diag.py`」と書いている。**S2 の md5 は出せる**（`--identity` で7秒）。理由も誤り（入口は `engine_tuner_exec.py`）。＝cp21 の P2 と P3 の両方が、生きた文書に残っている。

### N-3｜P1 の対策と同じファイルの中で、同じ事故が同じ工事で起きている。

`regime_detection_kb.md` の 1287-1290行（手書き）＝指標の種類 256（選べる249）／材料 261件／部品 551（＋4＝555）。実測＝選べる **140**／**263件**／**573**（＋7＝**580**）。

### N-4｜C1 の新しい仕組みに番人（わざと壊して落ちるか）が0件。

`gen_materials.py --selftest` の S1〜S8・R1〜R9 に BANS の項目が無い。§2.9③（番人は わざと壊して落ちるかをメタ確認）が、この仕組みだけ抜けている。**ゆえに C1 の判定も「静的にしか確かめていない」止まり。**

### N-5｜設計書の TARGET の1本 `gen_materials.py` の自己検査が、いま落ちている。誰も測っていない。

```
$ python3 scripts/priority_rebuild/gen_materials.py --selftest    （34秒）
  ❌ R6: 要件の逐語を変えても差し込む表が変わらない（その場で引いていない）
  ❌ R9: 対応表から1件 消しても落ちない
  ❌ S5: 確かめる相手（state=完了 の要件に効く ✅済 の行）が見つからない
  ❌ 3 件
RC=1
```

`gen_materials.py` は TARGET で、この工事で7関数を凍結している。**worklog 20260904 と next_step.md を grep しても `gen_materials.py --selftest` の記録は0件**（走らせていない）。`git diff` を見るかぎり R6/R9/S5 の判定コードは今回 触っていないので**この回で壊した可能性は低い**が、**TARGET の自己検査が赤のまま監査に出ている**のは事実。

## Minor（4件）

| # | 中身 |
|---|---|
| **N-6** | `_mmi` の docstring が原典を「逐語」と書いているが、`// mind Data order: Data[0] is newest!` と `int i, nh=0, nl=0;` が落ちている（実害は無い） |
| **N-7** | `decisions.md:62` に「まこさん確定＝禁止事項2 には当たらない」が残ったまま（61行に訂正文を足しただけ）。決定台帳を読む人は、いまも誤った「まこさん確定」を見る |
| **N-8** | `next_step.md:43` の J-6 の行が「（まこさん決定）」のまま。CC 自身が「逐語が手元の記録に無い」と認めた文の**出どころ**が直っていない |
| **N-9** | M5 の位置づけが3つの文書で割れている（`acceptance.md` §0-A ／ §8.1-2 ／ `worklog §36-4`） |

## プロセス（3件）

| # | 中身 | 提案 |
|---|---|---|
| **N-10** | **P2 は形だけで効いていない**。欄を機械が読まないので、宣言と実際が食い違っても何も止まらない | `gen_audit_request.py` か `--verify` が「宣言したコマンドの名前が、報告した出力の中に在るか」を機械で照らす |
| **N-11** | **P3 が同じ回で再演している**（135番・M2・T-d）。やること7-e は 134番にしか適用されていない | 「測れない／節が無い」と書いた行は、同じ行に `grep`／`--only` の実行結果を必須にする。P3 の文言を「grep」から「探した道具の一覧と、その出力」に広げる |
| **N-12** | **P4 の逐語が、CC が書いた文書からの自己引用でも通る**（案A の1件） | 逐語の欄に「その逐語が在るファイル:行」を必須にし、指し先が `acceptance.md` 自身・その凍結・監査依頼書のときは受け付けない |

---

# 7. 依頼元 CC の自己申告と、実物が食い違ったもの（全部）

| # | CC の申告（依頼書 §2 ／ worklog §36-2） | **実測** | コマンド |
|---|---|---|---|
| **11** | 凍結された impl_functions ＝ **7ファイル・22件** | **7ファイル・26件**（`<モジュール直下>` 3 ＋ 関数名 23）。22件は1つ前の承認（`acceptance_archive/…05.md`）の値で、いま凍結されているのは `…06.md` の 26件 | `grep -c '^  "' .claude/ratchet/impl_functions_frozen.json`＝26 ／ `verify_design_contract.py` の出力＝6+2+1+2+7+4+4＝26 |
| **14** | 変更の大きさ ＝ **31 files, 2049 insertions(+), 959 deletions(-)** | **31 files changed, 2138 insertions(+), 959 deletions(-)** | `git diff --stat`（差の +89 は §36 を worklog に書いた分＝改ざんではないが、**cp21 の m4「手写しの数字が並存する」が直っていない**証拠） |
| **9** | 文書の食い違い0件 ＝「`gen_materials.py --verify`」で「在る263／足す0／指紋 `245d3e37e7850ef1`」 | **`--verify` はその数字を出さない**（出力は `✅ 一致（手で書き換えられていない）` の1行）。263／0／`245d3e37e7850ef1` は `materials.json`／`--write`・`--status` の値で、値そのものは正しい | `gen_materials.py --verify` の実行結果1行 |
| **16** | 「`engine_tuner_exec.py --selftest`（`demand_enabled` の往復）」 | **`--selftest` に `demand` は0件**＝そのコマンドではこの行を測れない。実際に使ったのは `verify_design_contract.py` の must_use | `L=$(grep -n "^def selftest" …); tail -n +$L … \| grep -c "demand"`＝**0** |
| **12** | 「`git diff` で `observe_config.json` の数字の並びを見る」 | 38件/89個の出どころは **`materials.md:90`（機械生成）**。設計書 §6 の宣言は「`grep -c` を `engine_tuner_requirements.md` に当てる」＝**3通り** | `sed -n '90p' .claude/ratchet/materials.md` |
| **§36-3** | T-f の理由「需給の文字が出るのは実装側の**4か所**」 | 実測 **10行**。**見本が0件という結論は正しい**が、数が違う | `grep -n "demand" scripts/priority_rebuild/engine_tuner_exec.py` |
| **§36-3 / next_step 136** | M2「張り付き割合を出す節が観察の道具に**1つも無い**」 | **在ります**＝検査12（`--only 12`）。走らせたら張り付きの直接の証拠が出た（N-1） | `observe_diag.py --inspect … --only 12`（347秒） |
| **§36-2 の「そのほか」** | `observe_diag.py --selftest` ＝1分49秒 | **115秒**（誤差の範囲・問題なし） | 実測 |

**一致を確認できたもの（食い違い無し）**

| # | 中身 |
|---|---|
| 1 | 別枠3枠・需給3件 |
| 2 | MMI 既知3/3 |
| 3 | MMI 0→4件 |
| 4 | S-RタッチATR 18件とも既知2/2 |
| 5 | `pre_b` の道は通り、唯一の呼び出し元 `:2386` は渡していない |
| 6 | S2 md5 `7b01f51b5a9b29b3c05a7b340c203ba1` |
| 7 | G2 `d5cdb24a23ac06bb…`（38ファイル・22:28:10）・H2 `14f11027997dd3a2…`（22:33:00）＋**印の対象ファイルに印より新しいものは0件**（mtime 全件照合） |
| 10 | 印の4件・`demand_on` 3件・源4＝4 |
| 13 | `verify_design_contract.py`＝`RESULT: PASS（設計通り）` |
| 15 | 6061列(100.0%)→3520列(55.8%)・種類249→140 |
| — | `engine_tuner_exec.py --selftest` ✅（5秒） |

---

# 8. 次に手を打つ順番（監査の提案・決めるのは まこさん）

| 順 | やること |
|---|---|
| 1 | **N-1**＝検査12 の実測を まこさんに出し、M2 の案(a)〜(c) を決めていただく。完成の条件4 の判定を実データ側に足す |
| 2 | **N-2**＝`acceptance.md` §6 の6行目と `next_step.md` 135番を、実測（`engine_tuner_exec.py --identity` で S2 は出る／L1・S1 だけが hook で止まる）に合わせて書き直す |
| 3 | **N-3**＝`regime_detection_kb.md` 1287-1290行の4つの数字も機械生成に入れる（P1 を1行で終わらせない） |
| 4 | **N-5**＝`gen_materials.py --selftest` の ❌3件を切り分ける |
| 5 | **C1 の破壊テスト**＝監査は read-only で実施できていない。まこさんか依頼元 CC が1回 打って、rc=1 になることを確かめる |

---

# 9. 置き場の注意（この監査で気づいたこと）

**cp22 の依頼書だけ、置き場が ほかと違います。**

| ファイル | 置き場 |
|---|---|
| cp21 の依頼書・報告書 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/`（と `inputs/`） |
| **cp22 の依頼書** | **リポジトリ直下の `.claude/audits/inputs/`** |
| cp22 の報告書（この文書） | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/`（ほかの報告書に合わせた） |

**理由**＝CP 監査一覧を作る道具 `.claude/tools/gen_audit_index.py` の26行目が `AUD = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits"` を見ているためです。この報告書を直下に置くと、一覧に出ません。
**★依頼書を移すかどうかは まこさんが決めてください。**移さないと、一覧の cp22 の行に依頼書が「—」と出ます。

---

# 10. この監査で参照した主要ファイル（絶対パス）

- `/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py`（`_mmi` :409-446／`_sr_touch_atr` :395-406／T-e :6469-6489／検査12 :4375-4470）
- `/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py`（`demand_enabled` :198／`_material_name` の需給分岐 :610-618／`selftest` :3968）
- `/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py`（`assert_provenance` :707-716／`material_pool` :191／`_mat_drawn` :400／`sample_regime_build` :2196-2247／geo の抽選 :1338）
- `/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py`（`bans_count_block` :2106／verify の BANS 判定 :2235-2247）
- `/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py`（S-RタッチATR :1204-1240／MMI :1241-1264）
- `/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/regime_detection_kb.md`（BANS ブロック :704-706／★手書きが古い表 :1283-1291）
- `/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md`（§0-A・§6 の16行・§9 DESIGN_CONTRACT）
- `/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/next_step.md`（134・135・136番／:43 の J-6）
- `/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_design_contract_before_run.sh`（CHECK :58-59／engine_tuner の fail-closed :277-284）
