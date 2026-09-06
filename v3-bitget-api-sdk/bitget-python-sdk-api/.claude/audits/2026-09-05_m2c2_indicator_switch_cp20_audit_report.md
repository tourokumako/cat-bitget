# 【監査報告】M2-C-2（指標のオン・オフの切り替え）の検収と、承認の凍結が空だった件（cp20）

- 監査実施日: 2026-09-05
- 監査人: 独立 auditor（Plan サブエージェントを cold start で起動＝メインセッション CC の分析・結論は一切 渡していない・cc_role §1.4.5 改善9）
- 依頼書: `.claude/audits/inputs/2026-09-05_m2c2_indicator_switch_cp20_audit_request.md`（`wc -l` = 377。最終行に改行が無く、表示上は 378行）
- 依頼書の sha256: `33fb77d207efc44d784c595a3d082673eacd7540cd039f96d548f09759479cc6`
- worklog の sha256: `f88585bd5e1ef9450af7dc974096e53fe8edca23361dc7989ac7ec1211210a40`
- **リポジトリのファイルは1つも変更していません**（`git status` は監査前と同一）
- 着手前必読9件は全部 開いた。依頼書の数字は実物で1件ずつ照合した。外部検索は WebSearch で7クエリ実施した。

---

## 1. Step -1 監査対象の型宣言

```
対象の型: 混合型（コード型 ＋ 数値型 ＋ 文書型）
判定根拠: 判断材料が ①シェル/Python の分岐ロジック（approve_impl.sh・verify_design_contract.py・
          gen_indicator_switch.py）②件数とハッシュ（140/116/89/21/6/367B/44136fa3…）
          ③承認・監査ガバナンス文書（設計書・worklog・next_step）の3種にまたがるため。
使用観点: ①統計学的妥当性 ②リスク管理 ③認知バイアス ④ソフトウェア工学
          ⑤CC 設計判断の品質 ⑥実行プロセスの妥当性 ⑦主エージェント作業バイアス（全7観点を使用）
証跡要求: sha256（要）／grep・行番号（要）／逐語引用（要）／git diff --stat（要）
対象外の明示: 本件は道具・承認機構の監査で、売買記録0本・net $0。
          月次 NET ≥ $1,900 の達成可能性の判定は本監査の対象外。
          目標を下げる方向の提案は1件も含まない。
```

---

## 2. Step 0 指摘前提確認（依頼書の数字を実物で1件ずつ照合）

| # | 依頼書の記載 | 実測 | 判定 |
|---|---|---|---|
| 1 | `44136fa3…` ＝ 空の辞書 `{}` の sha256 | `printf '{}' \| shasum -a 256` → `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` | **一致** |
| 2 | t25 の凍結＝367 バイト・説明の鍵3つだけ | 367 B・`_これは何か`／`_作り方`／`_出どころ` のみ | **一致** |
| 3 | 空の凍結は3本（cp19・indicator-switch・t25） | 3本とも sha256 `d5d63cc2d16306e5a…` ＝**バイト完全同一**（`diff` 差分ゼロ） | **一致**（＋バイト同一を追加立証） |
| 4 | cp19 の空は「正しい空」 | `impl-lock-fix-cp19-20260904.md` の DESIGN_CONTRACT に `"impl_functions": {}` を実見 | **一致** |
| 5 | cp17 の凍結＝run_breaks.py 9件・gen_audit_request.py 20件 | 実測 9件・20件 | **一致** |
| 6 | 凍結ファイルが在る承認＝**6本** | **実測 7本**（`identity-l1s1-…frozen.json` 2,406 B・非空が 23:24 に追加済み） | **不一致（実測7本）** |
| 7 | SPEC の目印が在る＝24本 | 実測 24本 | 一致（ただし §18 執筆時点は22本＝スナップショット混在） |
| 8 | SPEC が DC より**後ろ**＝**21本** | **実測 19本**（依頼書自身の §18.1 の表も**19行**しかない） | **不一致（実測19本）** |
| 9 | SPEC が DC より**前**＝3本 | **実測 5本**（＋identity ×2） | **不一致（実測5本）** |
| 10 | `acceptance_archive/*.md`（`.actual.md` を除く）**121本** | 総 `.md` 121本・`.actual.md` 1本 → **除くと120本** | **不一致（実測120本）** |
| 11 | 使う 140 種 | `on` 配列 140 件・`counts.使う` = 140 | **一致** |
| 12 | 使わない 116 種 | `off` 116 件（140+116 = 256 で整合） | **一致** |
| 13 | 定義表の種類 256 | `counts.定義表の種類` = 256 | **一致** |
| 14 | 源1 ta 64 ／ 源2 法則 89 ／ 源3 恒等 8 | `sources.ta` 64・`sources.law` 89・`sources.identity` 8 | **一致** |
| 15 | 直す前＝71 ／ 185 ／ 源2 9 | `git show 4ac4405:./indicator_switch.json` で 71・185・9 を実見 | **一致** |
| 16 | 「系統と性質で 80 種ほど」 | 89 − 9 = **ちょうど80** | **一致** |
| 17 | 印の指紋 `dec5519430b997b0` | `fingerprint` フィールド一致 | **一致** |
| 18 | 対応が決まらない ta 5件 | `ta_unresolved` 5件・名前5つとも一致 | **一致** |
| 19 | 25行 追加・3行 削除 | `git show --stat b282902` → `25 insertions(+), 3 deletions(-)` | **一致** |
| 20 | `approve_impl.sh`:62-73 が `break` 無し＝最後が勝つ | 実物確認・`break` 無し | **一致** |
| 21 | 実装の門は「最初の囲み」 | `require_acceptance_before_impl.sh`:601-608 に `break` **有り** | **一致** |
| 22 | `--diff` の入口 :1622 が SPEC の impl_file を読む | 実物 `_impl = _resolve_impl(_md, str(_d.get("impl_file","")))` | **一致** |
| 23 | 設計書の impl_functions ＝**65件**（`9bdb794b…`） | **実測 129件**（`t25-fixture-off-20260904.md`:278-406）。**65 は SPEC の `public_functions` の件数**（実測 65件＋定数5件・worklog:241 が出どころ） | **不一致（実測129件）** |
| 24 | identity の凍結＝関数100件（含めて101件） | 一覧の要素は **100件**（うち1つが `<モジュール直下>`＝関数名は99）。101 は「ファイル名の鍵の行」を足した数で、`<モジュール直下>` ではない。worklog §19 冒頭の「101件（`<モジュール直下>` を含む）」は +1 の誤り（道具自身の出力も「全関数（100件）」） | **数え方の説明が不正確** |
| 25 | 逐語の写し（§8・§14・§15・§18・§19.1） | `diff` で §8・§14・§15・§18 は**完全一致**。§19.1 は worklog 446-473 が完全一致だが、**依頼書 312行目に worklog 483行目（＝§20 の行）が無告知で追加**されている | **1件 不一致** |

**Step 0 の結論**＝技術的中核（原因の同定・空の正体・コードの行）は**全部 実物で裏が取れた**。一方、**数え上げ系は4件が不一致**（21→19・6→7・3→5・121→120）で、**内容の数字も1件 不一致**（65→129）。写しの逐語も1行 混入している。

---

## 3. 観点①〜⑦ ＋ Q1〜Q4 の所見

### 観点① 統計学的妥当性 — **FAIL**

- 「140種が意図の範囲か」を判断する側の統計的性質が測られていない。140種のうち **45種（32.1%）が `close vs <移動平均の変種>%`** で、`off` 側の `close vs` は **0件**＝この族から1つも落ちていない。同じ移動平均群の「傾き%」は on 6件／off 26件で、**同じ原系列から「位置」だけ全採用・「傾き」はほぼ全除外**という非対称が生じている。
- 高相関な移動平均距離の特徴 45本の情報量は 45 ではない（業界標準は PCA 等での圧縮）。この重複度を測った数字（相関行列・VIF・実効次元）は本件のどの文書にも存在しない＝**データ不足（理由: 相関・冗長度の実測が未実施）**。
- 一方、DSR／PBO は**試行数**で合格の線を上げる（`tuner_stats.py`）。候補の種類を増やすことは、統計的には**合格を遠ざける方向**に働く。増やす判断には、増分の情報量の実測が要る。

### 観点② リスク管理 — **PASS（限定付き）**

- 本件は net $0・売買記録0本・`ALLOW_LIVE_ORDERS` 非関与。H1（合計 0.12 BTC）・H2（leak）・H4（コスト）に触れる変更は1つも無い。H2 の印（`leak_causality_diag` 全検査 pass・指紋 `4ee6ed6b…`）と G2（`a9dafad0…`）が取られている。
- 限定＝「本番に出す判断」に至る鎖のうち、**設計書と実装の同一性の証明が今回の iteration では成立していない**（観点⑥・Q1 参照）。金銭リスクは今ゼロだが、この鎖は将来 本番判断の根拠になる。

### 観点③ 認知バイアス — **FAIL**

- **アンカリング・視野固定**＝「原因＝最後の囲みから取る」に固定され、**「空でも通す」という向きの欠陥**（本当の Critical）に焦点が移っていない。`next_step.md` 131番の記述も「最後が勝つ」だけを見出しに置いている。
- **早期の一般化**＝対策が「SPEC を前に置く」＝**1回の成功事例からの規則化**。同じセッション内でその規則が2つ目の穴（L）を生んだにもかかわらず、規則の妥当性は再検討されていない。
- **確証バイアスの回避は成功している点**（公平に記す）＝走行B（`raise` を `pass` にした走行）で T33-f が**実際に落ちること**を確かめ、走行C で lint が**実際に不合格を出すこと**を確かめている。これは `cat_requirements` §2.9③「わざと壊して落ちるか」を満たす数少ない実例で、**評価できる**。

### 観点④ ソフトウェア工学 — **FAIL（本件の中核）**

同一の Markdown 文書に対し、**同じ正規表現から3通りの選択規則**が並存する。

| 仕組み | 選択規則 | 実物 |
|---|---|---|
| ① 実装の門 `require_acceptance_before_impl.sh` | **最初**の `impl_file` 囲み（`break` **有り**） | :601-608 |
| ② 照合 `verify_design_contract.py` | **目印の行**（見出しに語が在れば目印・:175）の後ろの囲み | `extract_block`:141-197 |
| ③ 承認 `approve_impl.sh` | **最後**の `impl_file` 囲み（`break` **無し**） | :65-73 |

①と③は**同じ regex・同じループで、`break` の有無だけが違う**。単一の文書に対する「契約はどれか」の解釈が3つある時点で、Single Source of Truth 違反。

さらに ③ は同じループの中で `spec_lists` は**全部の囲みから累積**（`lists.update`）、`impl_file` は**最後だけ**採用という**集約セマンティクスの不整合**を持つ（:70-73）。

### 観点⑤ CC 設計判断の品質 — **FAIL**

- 依頼書は「機械出力の逐語だけ」を掲げながら、**§19.1 に §20 の1行を無告知で足している**（依頼書312行目＝worklog483行目）。内容自体は Q2 の最重要材料なので**改竄ではない**が、「節ごとそのまま貼る・抜粋しない」「diff で確かめた（5節とも一致）」という宣言は §19.1 について**厳密には成立していない**。
- **数え上げの品質**が低い。21本（実測19本）・6本（実測7本）・3本（実測5本）・121本（実測120本）・65件（実測129件）。特に **65件 は SPEC の `public_functions` の件数**であり、**SPEC と DESIGN_CONTRACT の取り違えを、その取り違えを調査している文章の中で再演している**。
- 「21本」の誤りの機序を特定した。**24（今の SPEC 目印あり総数）− 3（古い時点の BEFORE 一覧）= 21**。今の BEFORE は5本なので正解は 24 − 5 = **19**。＝**新しいスナップショットと古い除外リストを混ぜた引き算**。

### 観点⑥ 実行プロセスの妥当性 — **FAIL**

- **M2-C-2 の検収走行は、凍結の照合を1度も通っていない。** `require_design_contract_before_run.sh`:60-62 の
  `CHECK = set(['--selftest','--self-test','--verify','--identity','--help','--scan-contracts','--diff','--write','--dry-run'])`
  により `--selftest` は「確認のための走行」として素通しされる。走行A（6分7秒）・B（6分9秒）・C（6分4秒）は全部 `--selftest`。
  ＝**「設計書どおりに実装したか」を機械で確かめる経路を通らずに、検収の数字が出ている。**
- 承認の瞬間、`approve_impl.sh`:114 は `🧊 impl_functions: 0 件を凍結しました` を**印字する**が、**exit しない**。さらに :178 の `_same = (bool(_fz_design) and …)` が偽になるため、:181／185／189 の3分岐が**どれも印字されない**＝空のときだけ出どころの注記が消える。**3回とも画面に「0件」が出ながら、誰も・何も止まらなかった。**
- 物理の証跡は良質（時刻・md5・指紋・`git diff --stat`・標準出力の貼り付け）。ここは PASS 相当だが、上2点で観点全体は FAIL。

### 観点⑦ 主エージェント作業バイアス — **FAIL**

- **B 後出し追加**＝承認が3回 要り、その2回は設計書の不足（§9 の節・Q5 の5件）。初版に織り込まれていなかった。
- **A 過剰適応**＝cp13〜cp19 の7回の工事で「凍結を作る」「凍結と比べる」という**個別パターン**を積み上げた結果、**「凍結が空である」という一般的な異常**が検査対象から漏れた。auditor_template ⑦A が名指しする「特定パターン検出への依存」そのもの。
- **D レビューサイクルの異常**＝同一 families（囲みの選択規則）の欠陥が、同一セッション内で**2回**（承認側・照合側）踏まれている。

---

### Q1 凍結が空だった件（原因＝approve_impl.sh が最後の囲みから取る作り）

**数値根拠のある断言。**

原因の同定は**正しい**（実物で確認済み・Step 0 の #20／#21）。ただし CC の原因記述は**不完全**で、Critical はそこではない。

1. **本当の Critical は「空を書いても止まらない」こと。** `approve_impl.sh`:108 の `_fz = obj.get("impl_functions") or {}` は、囲みが見つからない場合や impl_functions が無い場合を**黙って `{}` に潰す**。仮に「最初から取る」（＝`break` を1行 足す）に直しても、SPEC を先頭に置いた文書では**同じ空凍結が起きる**。方向の非対称性（fail-closed）が無い。
2. **照合側にも「両方が空なら PASS」の穴が残る。** `verify_design_contract.py`:951-953 は `json.dumps(design)` と `json.dumps(frozen)` の**文字列一致**だけを見る。design が `{}` かつ frozen が `{}` なら **一致して PASS**＝関数を1つも照合していないのに「設計通り」と出る。今回 FAIL が出たのは design 側が 129件（`9bdb794b…`）で偶々 非空だったからにすぎない。
3. **検出の遅延**＝空は 22:16 に作られ、承認は3回とも通り、実装の Edit も3回とも通り、6分×3の検収走行も全部 通った。単体の照合を手で打つまで誰も止まらなかった。

**業界整合**＝これは業界の既知アンチパターンと同型。OPA／Gatekeeper の `failurePolicy: Ignore` は、ポリシーが空・評価が落ちたとき**通してしまう**（[open-policy-agent/opa#1529](https://github.com/open-policy-agent/opa/issues/1529)）。金融側では Knight Capital が「全サーバに正しい版が入ったかを検証する機構が無かった」ことで 45分・4億ドルを失っている（[PRMIA case study](https://prmia.org/common/Uploaded%20files/eAI/PRMIA%20Case%20study%20-%20Knight%20Trading.pdf)）。SEC Rule 15c3-5 は統制を **pre-trade で・機械で** 効かせることを求める（[SEC final rule 34-63241](https://www.sec.gov/files/rules/final/2010/34-63241.pdf)）。**「印字するが止めない」は統制ではない。**

**改善余地: 4件**（提案1・2・3・7）

---

### Q2 その対策が「SPEC を節の前に置く」という暗黙の並び順である件

**数値根拠のある断言。この対策は恒久策として不適格。** 根拠は4つ。

1. **依存する不変条件が2つあり、2つ目は同じセッションで踏んでいる。**
   - 不変条件A＝SPEC の節を DESIGN_CONTRACT より前に置く（③が拾う「最後」を DC にする）
   - 不変条件B＝**SPEC 側の見出しに「DESIGN_CONTRACT」の語を書かない**（`extract_block`:175 が `s.startswith("#") and mark in s` で見出しを目印と数えるため）
   - Bは 23:2x に実際に破れた。worklog:442 の逐語＝「§10 の見出しに『★この節を DESIGN_CONTRACT より前に置く理由』と書いたため、…SPEC の json（impl_functions 無し）を契約として読んだ」＝**A を守るための説明文を書いた行為が、そのまま B を破った。**
2. **2つのうち1つしか登録されていない。** `next_step.md` §6 の131番は A のみ。B は `grep` で `next_step.md` に **0件**（`extract_block`／`fe8c2702`／見出しの語 のいずれもヒットなし）。B は承認済み設計書の §9 の L 行にだけ残っている（`.claude/state/acceptance.md`:170）＝**「塞げないもの」の欄は ToDo ではない**。
3. **機械の検査がゼロ。** 並び順を検査する hook・lint・CI は存在しない（`.claude/hooks` を grep して0件）。守れているかは、次に設計書を書く人が覚えているかだけに依存する。
4. **破ったときの向きが両方向にある。** A を破ると③が空を凍結する（今回）。B を破ると②が設計書側を空と読む（L）。**そして A・B の両方が同時に破れて design も frozen も `{}` になった場合は、②が「一致」で PASS を返す**（Q1 の2）。＝並び順を守っているうちは偶々この最悪ケースに入らないだけで、規則が守っているのは「たまたま」。

**業界整合**＝文書内の並び順に依存する強制は、SLSA／in-toto の思想と正反対。in-toto は「何を検証するか」を**署名された構造化メタデータ**で1点に固定し、admission controller が enforcement point になる（[in-toto と SLSA の解説](https://mikael.barbero.tech/blog/post/2023-12-28-slsa-and-in-toto/)、[Legit Security: SLSA provenance](https://www.legitsecurity.com/blog/slsa-provenance-blog-series-part-2-deeper-dive-into-slsa-provenance)）。feature flag ガバナンスの現行推奨も「必須メタデータが欠けた flag は CI／API バリデーションが**reject する**」＝スキーマ強制であって規約ではない（[Swetrix: 12 feature flagging best practices 2026](https://swetrix.com/blog/feature-flagging-best-practices)）。SR 11-7 も version control と production controls を**仕組み**として求める（[SR 11-7 framework](https://umbrex.com/resources/frameworks/regulatory-frameworks/model-risk-management-sr-11-7-framework/)）。

**なお まこさんは「直そうとしないでください」と指示し、131番と121番を1本の設計書に束ねる判断を既にされている。**本監査は「いま直せ」ではなく「**M2-C-2 を『検収済』として閉じる前に、どこまで担保されているかを正確に記す**」ことを求める。

**改善余地: 3件**（提案2・4・6）

---

### Q3 過去の設計書のうち、同じ並びで空が凍結されたものが何本あるか

**自分で数え直した。「未調査」ではない。**

`acceptance_archive/*.md`（`.actual.md` を除く 120本）を、依頼書と同じ3通りの目印（その語だけの行／`#` 見出しに語／囲みの見出しに語）で `grep -n -m1` して比較した。

| 区分 | 依頼書の記載 | **実測** | 差の説明 |
|---|---|---|---|
| SPEC の目印が在る | 24本 | **24本** | 一致 |
| SPEC が DC より**後ろ** | **21本** | **19本** | 依頼書の §18.1 の表も **19行**。21 は `24 − 3` の計算だが、今の BEFORE は5本なので `24 − 5 = 19` が正 |
| SPEC が DC より**前** | 3本 | **5本** | identity-l1s1 の2本（回り道を使った当のもの）が加算されていない |
| 凍結ファイルが在る承認 | 6本 | **7本** | identity-l1s1（2,406 B・**非空**）が 23:24 に追加済み |
| 凍結が **空**（367 B） | 3本 | **3本** | 一致。3本とも sha256 `d5d63cc2…` で**バイト完全同一** |
| うち「**誤った空**」 | **2本** | **2本** | `indicator-switch-20260902` と `t25-fixture-off-20260904`。どちらも 2026-09-04 の同一 iteration |
| うち「正しい空」 | 1本（cp19） | **1本** | `impl-lock-fix-cp19-20260904.md` の DC が実際に `"impl_functions": {}`＝実物で確認 |

**確定的な答え**＝**誤った空が凍結されたのは 2本のみ。どちらも 2026-09-04 の t25 の系統である。**

**それ以前の17本については「未調査」ではなく「該当なし」。** 理由＝凍結の仕組みは 2026-09-03（cp14 B-1）に新設されたもので、それ以前の設計書には比較対象の凍結ファイルが物理的に存在しない（`ls` で確認）。「同じ並びだった設計書が19本ある」ことと「空が凍結された設計書が2本ある」ことは別の集合で、依頼書はこの2つを同じ節に並べているため**19本すべてが被害に遭ったかのように読める形**になっている。実際の被害は 2本。

**未測定の項目（正直に）**＝依頼書自身が §18 末尾で認めている限界と同じもの。目印は `grep` の1件目で見ており、照合の道具の `extract_block` と同じ判定ではない。監査人も同じ方法しか使えなかった（`python3 -c` は走らせる門が止めるため）。`extract_block` を実際に呼んで数え直すと、**19 は上下しうる**（特に「見出しの文中で語に触れただけ」の行を拾う分だけ**過大**に出る向き）。ただし「誤った空 2本」は**凍結ファイルの実物を直接 読んで判定**しており、この数字は方法に依存しない。

**業界整合**＝「影響範囲を発見時点の見た目より広く見積もる」（`false_positive_incident_policy` §4 Step 2）に対し、今回は**逆に狭く見積もる誤りは無く、むしろ広く（21本）見せる誤り**が出ている。これは資金毀損の向きではないが、まこさんの意思決定に「19本の設計書を作り直す必要があるか」という存在しない検討を発生させる。

**改善余地: 2件**（提案5・6）

---

### Q4 「使う」140種が意図の範囲かの確認

**これは まこさんが決めること。**外部監査が代行できる判断ではない（`cc_role` §1.5＝最終決裁はまこさん・§0.1）。判断材料を数字で出す。

**(1) 意図の出どころ（逐語・CC 自身が `gen_indicator_switch.py`:6-8 のドックストリングに写している）**

```
2026-08-27「本来の目的が達成できるまでは、指標一覧はta 43種にする」＋「レンジ判定で必要な指標は入れろ」
2026-09-01「一律でtaの指標のみを使うという切り替えをする」
```

**(2) いまの数字と、逐語との距離**

| 項目 | 実測 | まこさんの逐語との関係 |
|---|---|---|
| 使う | **140種**／256種中（54.7%） | 「43種」の **3.26倍** |
| 源1 ta | **64種** | 同じドックストリングが「源1 ta の**43種**」と書いている＝**文書と実物が食い違う**。43 は `ta_class` の件数（38確定＋5未解決）、64 はそこから引いた指標の種類。**単位が違うものを同じ数字として書いている** |
| 源2 法則 | **89種**（前は9種） | 「レンジ判定で必要な指標は入れろ」が根拠 |
| 源3 恒等 | 8種 | 恒等レシピが実際に使う材料（`volume_ratio` ほか）＝落とすと S2 が壊れる |

**(3) 増えた80種の正体（★ここが判断の核心）**

71 から 140 への増分は、**相場の法則ファイルの3つの句だけ**が駆動している。

- `regime_laws.json`:556（R1）と :604（R3）＝ `"系統": ["構造・位置"]`
- `regime_laws.json`:792（R10）＝ `"性質": "vol"`

そして展開の仕方が **クラス全体**である（`gen_indicator_switch.py`:204-208）。

```python
if lins:                                   # ③系統での名指し（R1・R3＝構造・位置）
    out |= {f for f in families()
            if iref.FAMILY_LINEAGE.get(f, {}).get("k") in lins}
if props:                                  # ④性質での名指し（R10＝vol）
    out |= {e["family"] for e in iref.REFS if e["prop"] in props}
```

＝**法則が「構造・位置」と1語 書くと、その系統に属する family が全部 オンになる**（`FAMILY_LINEAGE` 内で `k="構造・位置"` は **74件**）。**法則が名指しした指標だけ**ではない。

その結果、次のことが起きている。

- **140種のうち 45種（32.1%）が `close vs <移動平均の変種>%`**（ALMA・DEMA・FWMA・HILO・HMA・HT_TRENDLINE・HWMA・JMA・KAMA・LINREG・LRb・MAMA・FAMA・MCGD・MIDPOINT・MIDPRICE・MMAR・PWMA・RAINBOW・RMA・SINWMA・SSF・SWMA・T3・TEMA・TRIMA・TSF・VIDYA・VWMA・WMA・ZLMA・CKSPl・CKSPs・PMAX・PSAR・SAREXT・MEDIAN・ABER_ZG・ACCBL・ACCBU・CE_L・CE_S ほか）
- `off` 側の `close vs` は **0件**＝この族から**1つも落ちていない**
- 対照的に、同じ移動平均群の **「傾き%」は on 6件・off 26件**。＝**同じ原系列から「位置」だけ全採用、「傾き」はほぼ全除外**。系統の分類が展開の粒度を決めており、情報の重複度は一切 考慮されていない

**(4) fail-closed の向き（効いている所・効いていない所）**

| | 内容 | 実物 |
|---|---|---|
| ✅ **効いている** | 型の表に無い指標はオンにしても使えない（`on = [f for f in all_f if f in want]`） | `gen_indicator_switch.py`:248 |
| ✅ **効いている** | 機械で対応が決まらない ta クラス5件は「使わない」に倒す | :243・`ta_unresolved` 5件 |
| ✅ **効いている** | `off_ok` の抜け道を T33-f が機械で守る。**走行B（`raise` を `pass` にした走行）で実際に落ちることを実測**＝`cat_requirements` §2.9③ の「番人メタ確認」を満たす数少ない実例 | `engine_tuner_gen.py`:5338-5348 |
| ❌ **fail-OPEN** | **系統・性質の名指しはクラス全体をオンにする。法則を1本 足して系統を1語 書けば、レビューなしに数十種が増える** | :204-208 |
| ❌ **fail-OPEN** | **増えた指標の一覧を まこさんが承認する関所は存在しない。**承認スクリプトは指標の一覧を1度も見ない（`approve_impl.sh` に `indicator_switch` の文字列は0件） | — |

**(5) 業界整合**

- 高相関な移動平均距離の特徴を並べることは情報量を増やさない。学術・実務の標準は **PCA 等で圧縮してから使う**（[Reinforcement learning meets technical analysis (Cogent Economics & Finance, 2025)](https://www.tandfonline.com/doi/full/10.1080/23322039.2025.2490818) ＝「highly correlated な複数移動平均のシグナルを標準化し PCA で次元と情報冗長性を削減する」）。指標を増やすほど information redundancy と overfitting を招くのが定説。
- Bailey と López de Prado の Deflated Sharpe Ratio は **試行数**で合格の線を上げる（[SSRN 2460551](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)）。候補の種類が 71 から 140 に増えることは、統計的には**合格を遠ざける**方向に働く。本プロジェクトは既に `tuner_stats.py` で DSR を試行数から計算している＝**140 にする判断は、DSR の線を自分で上げる判断**である。

**(6) 監査人としての整理（判定ではなく材料）**

- 「140種は意図の範囲か」に**機械が答えられる材料は存在しない**（設計書 §9.2 の逐語「印の中身が正しい範囲かどうかは、機械には分かりません」は正しい）。
- ただし**まこさんが決めるための材料は不足していない**。上の (3) の1行——「**法則の3つの句が、系統と性質のクラス全体を展開して +80種にした。うち45種は close vs 移動平均の変種で、off 側にはこの族が1件も無い**」——が判断に必要な全部である。
- **順序について1点**＝engine_tuner の案の作り方は今も乱数（D14 未修正・`false_positive_incident_policy` §3 の #14／#24）。乱数で選ぶ機械に 140種 を与えても、140 の是非は測れない。**「140 が多いか」は、探索が法則で組むようになってから net で測るのが順序である。**いま決められるのは「クラス全体展開という**作り**を許すか」であって、「140 という**数**」ではない。

**改善余地: 3件**（提案4・6・7）

---

## 4. 外部検索結果サマリー

実施した検索クエリ（7件・WebSearch）

1. `trading system configuration change control fail-closed empty config silent default production incident`
2. `"fail open" vs "fail closed" security control empty allowlist misconfiguration detection`
3. `infrastructure as code drift detection signed artifact attestation supply chain in-toto SLSA provenance verify config`
4. `feature flag governance stale flags audit trail approval workflow best practices 2026`
5. `Lopez de Prado backtest overfitting number of trials deflated Sharpe ratio feature count multiple testing`
6. `SEC market access rule 15c3-5 risk management controls pre-trade parameter verification supervisory procedures algorithmic trading`
7. `technical indicators highly correlated redundant "moving average" variants information content trading feature engineering diminishing returns`

| # | 主要発見 | 本件への当て方 | URL |
|---|---|---|---|
| 1 | **Knight Capital**＝全サーバに正しい版が入ったかを**検証する機構が無く**、旧コードが本番に残存。リアルタイムの安全弁も無し。45分で 4億ドル | 「承認が入ったこと」と「承認された中身が入ったこと」は別。今回は後者が3回とも空だった | [PRMIA case study](https://prmia.org/common/Uploaded%20files/eAI/PRMIA%20Case%20study%20-%20Knight%20Trading.pdf) |
| 2 | **OPA／Gatekeeper は既定で `failurePolicy: Ignore`**＝ポリシー評価が落ちるときや未定義のとき**通す**。運用停止を避けるため意図的に fail-open だが、誤設定時に非準拠リソースが通る | `approve_impl.sh`:108 の `or {}` と :114 の「印字のみ」は、これと同型の fail-open | [open-policy-agent/opa#1529](https://github.com/open-policy-agent/opa/issues/1529) |
| 3 | **Fail-closed の原則**＝統制が不確実・誤設定・停止した瞬間を攻撃者は狙う。fail-open は統制のバイパスを許す | 「空の凍結」＝統制が不確実な瞬間。ここで通すか止めるかの選択が本件の本質 | [authzed.com/blog/fail-open](https://authzed.com/blog/fail-open) ／ [devsecopsschool.com/blog/fail-closed](https://devsecopsschool.com/blog/fail-closed/) |
| 4 | **SLSA と in-toto**＝SLSA が「provenance に何を含むか」、in-toto が「その署名形式」を定め、**admission controller が単一の enforcement point** になる | 本件は enforcement point が3つ（①②③）あり、しかも**選択規則が3通り**。attestation を1本に固定するのが業界の解 | [in-toto と SLSA](https://mikael.barbero.tech/blog/post/2023-12-28-slsa-and-in-toto/) ／ [SLSA provenance](https://www.legitsecurity.com/blog/slsa-provenance-blog-series-part-2-deeper-dive-into-slsa-provenance) |
| 5 | **feature flag ガバナンス 2026**＝「必須メタデータ（owner／lifecycle／expiry）が欠けた flag は **CI チェックや API バリデーションが reject する**」。承認ワークフローは**変更をブロック**する | 「SPEC を前に置く」規約ではなく、**スキーマ検査で reject** が業界の現行推奨 | [Swetrix](https://swetrix.com/blog/feature-flagging-best-practices) ／ [Unleash](https://www.getunleash.io/blog/devops-regulatory-compliance-how-feature-flags-can-streamline-auditing-and-governance) |
| 6 | **SEC Rule 15c3-5**＝統制は **pre-trade で**適用が必須。手動注文も自動生成注文も対象。年次で有効性をレビューし CEO が証明 | 「印字して人が気づく」は pre-trade 統制ではない。承認の瞬間に止める形が要る | [SEC 34-63241](https://www.sec.gov/files/rules/final/2010/34-63241.pdf) ／ [FINRA Market Access](https://www.finra.org/rules-guidance/key-topics/market-access) |
| 7 | **SR 11-7（Fed／OCC）**＝model inventory・version control・testing evidence・**production controls**・開発者と検証者の職務分離 | 承認スクリプトを CC が打てない設計（cp16 E-3）は職務分離として正しい。足りないのは production controls 側 | [SR 11-7 framework](https://umbrex.com/resources/frameworks/regulatory-frameworks/model-risk-management-sr-11-7-framework/) |
| 8 | **Bailey と López de Prado, Deflated Sharpe Ratio**＝試行数・歪度・尖度で有意水準を補正。「試行数を統制しないと過度に楽観的な期待値になる」。PBO は選定過程が過学習を助長したかを測る | 指標を 71 から 140 に増やす＝試行空間を広げる＝DSR の線を自分で上げる | [SSRN 2460551](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551) ／ [Stefan Jansen](https://stefan-jansen.github.io/machine-learning-for-trading/08_ml4t_workflow/01_multiple_testing/) |
| 9 | **相関した移動平均シグナルの扱い**＝「複数移動平均のように**高相関なシグナル**の矛盾をどう調停するかが投資家の課題」→ 標準化し **PCA で次元と情報冗長性を削減**して状態に使う | `close vs <MA変種>%` 45本を「45種類の指標」として数えることの是非 | [tandfonline.com](https://www.tandfonline.com/doi/full/10.1080/23322039.2025.2490818) |
| 10 | **指標の冗長性**＝「指標を使いすぎると情報冗長と過学習を招く。各指標の寄与を定期的に評価し、冗長なものを除いて戦略を簡潔に保つべき」 | 140種を維持するなら、寄与の定期評価が対で要る | [StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays) |

---

## 5. 総合判定

### **Verdict: PIVOT**

**GO ではない理由（＝M2-C-2 を「検収済」として閉じられない）**

M2-C-2 の検収の証跡は、**設計書と実装の同一性を機械で確かめる経路を1度も通らずに**取られている。

- 承認3回とも凍結は `{}`（`44136fa3…`）で、**設計書の 129件（`9bdb794b…`）は1度も凍結されていない**
- 検収の走行A・B・C（合計18分20秒）は全部 `--selftest`＝`require_design_contract_before_run` の CHECK 旗で素通し
- 実装の門（`require_acceptance_before_impl.sh`）は凍結ファイルを**1度も読まない**

＝「承認された設計書のとおりに実装されている」という主張を支える機械的根拠が、この iteration には**存在しない**。SEC 15c3-5 の pre-trade 統制原則・SR 11-7 の production controls・SLSA の attestation 検証のいずれの基準でも、この状態を「検証済」とは呼ばない。

**NO-GO でもない理由（＝成果物を捨てる必要はない）**

- 実装そのものは**独立に検証できる**。`git show --stat b282902` = 25 insertions／3 deletions（設計書の3か所と完全一致）、走行B で番人が実際に落ちること、走行C で lint が実際に不合格を出すこと、恒等3本が 2026-08-05 以来の基準値（`7b01f51b…`／`96a9102e…`／`18b3d31a…`）と完全一致すること、G2・H2 pass。**この負のテスト2本は `cat_requirements` §2.9③ を満たす良質な証跡である。**
- net $0・売買記録0本・`ALLOW_LIVE_ORDERS` 非関与・H1／H2／H4 に触れる変更ゼロ。**資金リスクは今ゼロ。**
- 承認をまこさんの端末に限定した設計（cp16 E-3）は SR 11-7 の職務分離として**正しい方向**。

**PIVOT の中身**＝成果物（印の作り直し・T25 の直し）は**そのまま残す**。閉じ方だけを変える。「M2-C-2 検収済」ではなく「**M2-C-2 の実装は完了。ただし検収の鎖は承認機構の欠陥により未接続。131番の直し（10行以下）の後に、`--selftest` 1回で鎖を接続して閉じる**」とする。追加コストは自己テスト1回（約6分）である。

---

## 6. 改善方向性（7件・優先度つき）

### 【Critical 1】承認の瞬間に「空の凍結」を fail-closed で止める

- **現状**＝`.claude/hooks/approve_impl.sh`:108 の `_fz = obj.get("impl_functions") or {}` → :114 で `0 件を凍結しました` と**印字するだけ**。3回とも画面に出ながら誰も止まらなかった。
- **方向性**＝`_fz` が空、**かつ** 設計書に `no_impl_functions_reason` が無いなら `sys.exit(3)`（既に :90-93 に同じ形の中止処理が在るので、その形をそのまま使える）。cp19 のような「正しい空」は `no_impl_functions_reason` を持つので通る。**追加は約4行。**
- **業界根拠**＝OPA の fail-open が誤設定時に非準拠を通す問題と同型。fail-closed が統制の原則。

### 【Critical 2】囲みの選択規則を3つから1つに統一する

- **現状**＝①`require_acceptance_before_impl.sh`:601-608（`break` 有り＝最初）／②`verify_design_contract.py`:141-197（目印の見出し）／③`approve_impl.sh`:65-73（`break` 無し＝最後）。**①と③は同じ regex・同じループで `break` の有無だけが違う。**
- **方向性**＝③を②の `extract_block(md, "DESIGN_CONTRACT")` に置き換える（②は既に `verify_design_contract` から import 可能な位置に在り、`approve_impl.sh`:58 で同モジュールから `resolve_spec_list` を import している実績がある）。①も同じ関数に寄せる。**これで「どの囲みが契約か」の解釈が1つになり、Q2 の不変条件A・Bの両方が不要になる。**
- **業界根拠**＝SLSA／in-toto の enforcement point 単一化。

### 【Critical 3】「両方が空なら PASS」の穴を塞ぐ

- **現状**＝`scripts/priority_rebuild/verify_design_contract.py`:951-953 は JSON 文字列の一致だけを見る。design が `{}` かつ frozen が `{}` なら**一致して PASS**＝1関数も照合していないのに「設計通り」と出る。
- **方向性**＝比較の**前**に「frozen が空なら NG（`no_impl_functions_reason` が在る控えを除く）」を1行 足す。現に `_arch.exists()` が無いときは止める処理（:941-944）が在るので、その隣に置ける。

### 【Major 4】法則の系統・性質の展開を「クラス全体」から「差分の承認つき」に変える

- **現状**＝`gen_indicator_switch.py`:204-208 が系統1語で 74 family、性質1語で vol 族をまとめてオンにする。増えた一覧を承認する関所はゼロ。
- **方向性**＝`--write` のとき **前回の `on` との差分（増えた種類・減った種類）を必ず印字し、差分が0でなければ `--write` を拒否して `--write --accept-delta` を要求する**。まこさんが目で見て通す瞬間を1つ作る。**140 を減らせという提案ではない**（減らす判断はまこさんのもの）。「増えたことに誰も気づかない経路」を塞ぐ提案である。

### 【Major 5】Q3 の件数を訂正する（21本 → 19本）

- **現状**＝依頼書 §18.1 の見出しが 21本、表は 19行、実測 19本。誤りの機序＝`24 −（古い時点の 3）`。
- **方向性**＝`next_step.md` §6 の131番と worklog §18 の見出しを **19本**に直し、併せて「そのうち実際に空が凍結されたのは **2本**（残り17本は凍結の仕組み以前＝比較対象なし）」を同じ行に置く。**19 と 2 を並べないと「19本 作り直しが要る」と読まれる。**

### 【Major 6】「65件」を「129件」に訂正し、SPEC と DESIGN_CONTRACT の取り違えを記録する

- **現状**＝worklog:354（→依頼書 209行目）の「私の設計書の impl_functions（65件・`9bdb794b…`）」は誤り。**実測 129件**。65 は SPEC の `public_functions` の件数（worklog:241 が出どころ・実測 65件＋定数5件）。
- **方向性**＝数字を直したうえで、**「SPEC と DESIGN_CONTRACT を取り違える事故を調査している文章の中で、同じ取り違えが起きた」**ことを1行 記録する。これは Q1／Q2 の欠陥が**人間側の認知にも同型に効いている**証拠で、規約（並び順）では消えないことの実証である。

### 【Minor 7】残る4点

- **7a**＝`_mat_fixture` の docstring（`engine_tuner_gen.py`:473）が「この道で範囲の検査を飛ばすことはできない」と書くが、実装は `off_ok=True` のとき `material_ranges()` と `param_in_range()` を**通らずに return する**（:476-482）。守られているのは「オンの指標に使えない」ことだけ。文言を実装に合わせる。
- **7b**＝控えの凍結2本（`indicator-switch-20260902.frozen.json`・`identity-l1s1-…frozen.json`）が **git 未追跡**（`git status` で `??`）。`verify_design_contract.py`:927 自身が「控えは git 未追跡なので、消しても跡が残らなかった」と警告している。監査の根拠になるファイルは追跡下に置く。
- **7c**＝依頼書 §19.1 に worklog §20 の1行が無告知で混入している。次回は「§19.1（446-473）＋ §20 から1行（483）」と範囲を明示する。
- **7d**＝「関数101件」（worklog §19 冒頭）は実測 100件（道具自身の出力も「全関数（100件）」）。+1 の出どころは `<モジュール直下>` ではなくファイル名の鍵の行。

---

## 7. CC プロセス欠陥対策（cc_role §1.4.6 改訂提案）

### 提案 §1.4.6.4（新設）＝「印字するだけの検査」を検査と呼ばない

**背景**＝`false_positive_incident_policy` §3 の内部検出は25件中1件（#18）のみ。今回もその型である。承認の瞬間に `🧊 impl_functions: 0 件を凍結しました` と**画面に出ていた**にもかかわらず、3回とも通った。

**改訂案（cc_role §1.4.6 に追加）**

> **§1.4.6.4 「止める」と「出す」を分けて宣言する義務**
> 強制の仕組み（hook・承認スクリプト・照合の道具）を新設・改訂するとき、CC は各検査について次の2つを1行ずつ書く義務を負う。
> 1. **止める検査か、出すだけの検査か**（exit する／しない）
> 2. **止まらないとき何が通ってしまうか**（fail-open の内容を1文で）
>
> 「出すだけ」の検査を「担保」「守っている」「fail-closed」と書くことは `false_positive_incident_policy` §2 類型 G（確認したフリ）として扱う。
>
> **本節の実証**（2026-09-04）＝`approve_impl.sh` は空の凍結について「0件を凍結しました」と出すが止めない。3回の承認・3回の実装 Edit・18分20秒の検収走行が全部 通った。内部検出はゼロ。

### 提案 §1.4.6.5（新設）＝規約による対策を「対策」と呼ばない

**改訂案**

> **§1.4.6.5 「暫定の決まり」を出すときの必須3項目**
> 道具の欠陥に対して「今後こう書く」という**人の規約**で回避する場合、CC は次の3つを同時に出す義務を負う。
> 1. **その規約が依存する不変条件を全部 数え上げる**（1つとは限らない）
> 2. **各不変条件を破ったとき、止まる向きか通る向きか**
> 3. **各不変条件を `next_step.md` §6 に個別の番号で登録する**（設計書の「塞げないもの」の欄は ToDo ではない）
>
> **本節の実証**（2026-09-04）＝「SPEC は DESIGN_CONTRACT より前に置く」は不変条件を**2つ**持つ（並び順／見出しに目印の語を書かない）。2つ目は同じセッションで破れたが、`next_step.md` §6 には1つ目しか登録されていない（131番）。しかも「A を守る理由を見出しに説明として書いた行為」が、そのまま B を破った。

### 提案 §1.4.6.6（新設）＝数え上げのスナップショットを固定する

**改訂案**

> **§1.4.6.6 件数を報告するときの義務**
> 過去の成果物を数えて件数を報告するとき、CC は次を守る。
> 1. **数えた時刻を明記する**（監査中にファイルが増える）
> 2. **合計 − 除外 の引き算で件数を出さない。**該当するものを1件ずつ列挙し、**列挙した行数を件数とする**
> 3. 表の行数と見出しの件数が一致することを、書いた直後に自分で数える
>
> **本節の実証**（2026-09-04）＝「21本」は `24（今の総数）− 3（古い時点の除外一覧）` の引き算で出ており、表の行数は 19。実測も 19。同じセッションで「6本」「3本」「121本」も同型にずれた（実測 7本・5本・120本）。

---

## 最終まとめ

### Critical の件数: **3件**

1. 承認の瞬間に空の凍結を止める機械が無い（`approve_impl.sh`:108／114・印字のみで exit しない・3回すり抜けた）
2. 囲みの選択規則が3通り並存する（①最初 ②目印の見出し ③最後。①と③は `break` の有無だけの差）
3. 照合が「設計書も凍結も空」なら PASS を返す（`verify_design_contract.py`:951-953・1関数も照合せず「設計通り」）

### Verdict 一行

> **PIVOT** — 実装（25行／3行・負のテスト2本・恒等3本 完全一致）は健全なので残すが、M2-C-2 の検収証跡は承認機構の fail-open により「設計書と実装の同一性」を機械で1度も確かめておらず（凍結3回とも `{}`・検収走行は `--selftest` で契約照合を素通し）、いま「検収済」として閉じると未検証の環を検証済と認証することになる。Critical 3件（合計 約15行の直し）を入れて `--selftest` を1回（約6分）走らせ、鎖を接続してから閉じることを勧める。

---

## 直すときに開くファイル（実装点）

- `.claude/hooks/approve_impl.sh`（62-73行＝`break` 無しの選択・105-115行＝`or {}` と印字のみの凍結。Critical 1・2 の実装点）
- `scripts/priority_rebuild/verify_design_contract.py`（141-197行 `extract_block`＝統一先の関数・882-960行 `check_impl_functions`＝Critical 3 の実装点・1622行 `--diff` の入口）
- `.claude/hooks/require_acceptance_before_impl.sh`（601-608行＝`break` 有りの「最初が勝つ」側。Critical 2 で統一する相手）
- `scripts/priority_rebuild/gen_indicator_switch.py`（204-208行＝系統・性質のクラス全体展開・6-8行のドックストリング「ta の43種」が実物 64種と食い違う。Major 4 の実装点）
- `.claude/state/next_step.md`（§6 の131番＝不変条件Aのみ登録・Bが未登録。Major 5・6 と §1.4.6.5 の反映先）
