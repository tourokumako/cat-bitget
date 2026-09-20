<!-- ARC iter="m2c-width-and-stage-candidates-20260918" -->

# 設計書｜場面の判定の候補を、指標のオン・オフの印に連動させる（名前の一覧の絞りを消す ＋ 帯の幅の枠が法則 R7 の指標も読む ＋ 法則 R2 が帯の幅の枠を系統の数から外す）

TARGET: scripts/priority_rebuild/engine_tuner_gen.py, scripts/priority_rebuild/engine_tuner_exec.py, scripts/priority_rebuild/regime_r9_diag.py, .claude/tools/gen_regime_kb.py, .claude/breaks/b86_stage_count.sh
NEW_FILE: .claude/breaks/b87_width_family.sh, .claude/breaks/b88_r2_exempt.sh
MODEL: .claude/breaks/b86_stage_count.sh

REQUIREMENTS: まこさんの決定（下の §0）と、`engine_tuner_milestones2.md` の §2.2（レンジ判定の検索方法）。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書はプログラムが作ります。**手で書いたのは、元データ `.claude/ratchet/acceptance_src.json` の5つ（何を作るか・なぜ作るか・組み方・やらないこと・決めてほしいこと）だけです。残りは正本から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --write`。手で書き換えられていないかの検出＝`--verify`。

## 0｜まこさんの決定（逐語）

> ★この工事への決定（逐語）
> これ間違ってると思う。帯の幅を見る指標はBB等、もっといっぱいある。以前もこの指摘があり修正しているはずだが、また先祖返りしている（2026-09-18）
> それでいいので、やることリストを書き直して（2026-09-18）
> R5であればその法則に則った指標のみを読み込むのは正しいが、なにを直そうとしている？ 法則が対象とする指標以外もすべて読み込ませようとしてるのか？（2026-09-18＝法則が指標を名指しすること自体は正しい。直すのは R7 だけ）
> そのやることリストを実行したら、レンジロジックを検索する際に、印（indicator_switch.json）でオンにした指標だけを、候補の母集団として読み込むことができるのであればOK（2026-09-18）
> その方法でBB幅・Donchian幅・HWC幅%を読み込めるようになるなら、いいよ。（2026-09-19＝読むもの宣言と、この設計の形への OK）
> 案BでOK（2026-09-19＝法則 R2 の数から、帯の幅の枠を外す道を選ぶ）
> ★前から引き継ぐ決定（逐語）
> 使う指標はオンオフで切り替えているので、入っていないということ自体がおかしいのでは？（2026-09-17）
> だから、オンオフで連動して指標を読み込ませる状態にしろよ。（2026-09-17）
> 法則と役割により除外するものは、除外でよい。（2026-09-17）
> 手で書くな。すべて自動生成しろ。オンオフ切り替えてる大元から自動で読み込ませろ（2026-09-17）
> 一律でtaの指標のみを使うという切り替えをする（2026-09-01・M2-C）
> ヌケモレがおおいから、手で書かざるを得ない部分以外は自動生成にしろよ。（2026-09-09・恒久69番）
> お前が法則を決めるな（2026-09-09＝法則の中身は まこさんが決める）
> コードを直したら、その行を探している壊すプログラムが在るかを、必ず grep（2026-09-16・L-605）

## 1｜概要

engine_tuner が場面の判定の束を組むときに、印（`indicator_switch.json`）でオンにした指標だけが候補の母集団になる状態を作ります。直すところは3つです。1つ目は、段の候補（段1 帯・段2a 強さの否定・段2c 3枠目）から、印とは別の2つ目の絞りを消すことです。いまは §2.2 の文に出てくる名前を私が一覧（`m2_stage_candidates.json` の語）にし、その名前に完全一致しない指標を落としています。そのため、印がオンで法則も許す指標（構造・位置の系統の多く・MMI・SQZ_ON）が候補に出ません。2つ目は、束の帯の幅の枠（A）が、法則 R7 が名指しした指標も読むようにすることです。いまはレンジ幾何だけを読み、その1件目（W%）を固定で使っています。2026-09-18 に法則 R7 へ戻した BB幅・Donchian幅・HWC幅% は、この道では1本も読まれません。3つ目は、法則 R2（構造・位置 を除く系統は束の中で1本まで）が、帯の幅の枠の部品を数から外すようにすることです。この3つ目が無いと、2つ目は動きません。帯の幅の指標は3件とも系統が ボラで、ボラの1本は法則 R6（低ボラ＝幅が狭い側）が既に使っているため、帯の幅を足すと2本になって審査 G7 が束を落とすからです。直した後は、候補は ①印 ②法則 ③役割（型の表）④時間足 ⑤標本不足 ⑥設定の欄 `stage_limits` だけで決まり、帯の幅の枠にも印がオンの指標が並びます。あわせて、§2.2 の段の表を engine_tuner が実際に出す候補から自動で書き、自己テストと壊すプログラムで、絞りが戻されたときに落ちる形にします。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

| 何を測ったか | コマンド | 結果 |
|---|---|---|
| 印とは別の、名前の一覧で候補を落とす行 | `grep -n -A1 'if not (_ok_name or _ok_lin)' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | （終了コード 1）／読み方＝この行が、名前の一覧に無い指標を候補から落としている |
| 印で指標を外している行（候補の元の成績表を読む所） | `grep -n 'if not ex.indicator_enabled(nm)' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 1388:                if not ex.indicator_enabled(nm):（終了コード 0）／読み方＝印の判定はここで既に効いている＝名前の一覧は二重の絞り |
| 印で「使う」にした指標の数 | `grep -o '"使う": [0-9]*' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indicator_switch.json` | "使う": 140（終了コード 0）／読み方＝候補は、この中から法則と役割で決まるはず |
| §2.2 の元データの語に MMI と SQZ_ON が在る数 | `grep -c '"探す": "MMI"\／"探す": "SQZ_ON"' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_stage_candidates.json` | 0（終了コード 1）／読み方＝語に無いので、名前の一覧の絞りで候補から落ちる |
| 成績表に MMI と SQZ_ON の列が在るか | `grep -o '"\(MMI[0-9]*\／SQZ_ON\)__[0-9a-z]*"' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/material_ranking.json ／ sort ／ uniq -c ／ wc -l` | 55（終了コード 0）／読み方＝列は成績表に在る＝名前の絞りを外せば候補に出る |
| ★②束を組む側の帯の幅の枠が、法則 R7 から geo だけを読んでいる行 | `grep -n 'geo_names, geo_side = _law_geo' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 2955:    geo_names, geo_side = _law_geo(laws, no)（終了コード 0）／読み方＝この行が、帯の幅の枠でレンジ幾何だけを読み、その先頭を固定で使っている＝帯の幅の法則に戻した指標は、この道では読まれない |
| ★②法則 R7 に HWC幅% が在る行（R6 からは 2026-09-09 に外れている） | `grep -n 'HWC幅%' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/regime_laws.json` | 712:        "★2026-09-09（まこさん決定「それで書いてよいが、証拠として、引用も書いておいて」）＝数える指標を6つにした（BB幅・SQZ_ON・Donchian幅・ATR%・realized_vol・stdev%）。外した2つ（HWC幅%・SQZPRO_ON_NARROW）は、2026-09-09 の Web 検索で出どころを取れなかった（出どころが取れたら まこさんに出して決めてもらう）。★BB幅は stdev の別の書き方（BB幅＝4σ÷中心線）＝同じ系統を2本 数えない決まり（R2）に当たる。" ⏎ 752:      "書けるか": "○ 幅の列は在る（レンジ幾何の全幅 W% と、帯の幅を割合で測る指標3件＝BB幅・Donchian幅・HWC幅%）", ⏎ 764:        {"指標": "HWC幅%", "出どころ": "同じ正本の HWC幅% の定義と、系統の欄（2026-09-18 に開いた）", "逐語": "ホルト・ウィンターズの水路の幅（上の帯 − 下の帯）を、終値で割って%化／水路の幅＝値動きの大きさの計測（BB幅 と同じ作り）", "…（出力 6 行のうち先頭 500 文字）（終了コード 0）／読み方＝帯の幅の法則の数える部品と側に在る＝法則の側では、候補として読める状態になっている |
| ★③戻した3件の系統 | `grep -n '"HWC幅%": dict(k=' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py` | 4391:    "HWC幅%": dict(k="ボラ", note="水路の幅＝値動きの大きさの計測（BB幅 と同じ作り）"),（終了コード 0）／読み方＝系統は ボラ（BB幅・Donchian幅 も同じ）＝役割 location では引けない |
| ★③役割 location が使える系統 | `sed -n '/"location": {/,/"tfs"/p' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families.json ／ grep -A2 '"lineages"'` | "lineages": [ ⏎      "構造・位置" ⏎     ],（終了コード 0）／読み方＝構造・位置 だけ＝ボラの指標は、その系統を使える役割から引く必要がある |
| ★③法則 R2 の上限と、除く系統 | `sed -n '/"番号": "R2"/,/"上限"/p' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/regime_laws.json ／ tail -5` | ], ⏎         "除く部品": { ⏎           "法則": "R7" ⏎         }, ⏎         "上限": 1（終了コード 0）／読み方＝構造・位置 を除く系統には上限が在り、ボラの枠は低ボラの法則が既に使っている。だから帯の幅を足すと上限を超えて、審査が束を落とす |
| ★②③印がオンか（BB幅・Donchian幅・HWC幅%） | `sed -n '/^ "on": \[/,/^ \]/p' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indicator_switch.json ／ grep -c '"BB幅"\／"Donchian幅"\／"HWC幅%"'` | 3（終了コード 0）／読み方＝どれも印がオン＝候補の母集団に入るべきもの |
| ★②帯の幅の指標の列が、成績表に在るか（HWC幅%） | `grep -o 'HWC幅%' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/material_ranking.json ／ wc -l` | 132（終了コード 0）／読み方＝成績表に列が在る＝ボラを使える役割から引ける（役割ごとの内訳は記録に書いた）。役割 location には無いので、帯の幅の枠は役割を型の表から引く必要がある |
| ★②型の表が役割から系統を引く形になっている所の数 | `grep -c 'table\["roles"\]\[role\]' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 10（終了コード 0）／読み方＝どれも「役割 → 系統」の向き＝逆（系統 → 役割）を引く処理は無い。この工事で新しく書く |
| 消す行を探している壊すプログラム（L-605） | `grep -rn '_ok_name\／_ok_lin' .claude/breaks` | （終了コード 1）／読み方＝ここに出る壊すプログラムを、この工事で直す |
| 直すファイルに commit されていない差の塊の数 | `git diff HEAD -- v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py .claude/tools/gen_regime_kb.py .claude/breaks/b86_stage_count.sh ／ grep -c '^@@'` | 10（終了コード 0）／読み方＝承認の前は差が無い＝照合が数える触った関数は、この工事で直すものだけになる |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

<!-- ACC_MATERIALS_START hash=c55cc4bff2fb96cb gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**探す指標＝印がオンの 140種**（印を切り替えると、この一覧も設計も変わります）。

```
ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・OBV傾き・転換線・基準線・EMA傾き・ATR%・BB%b・BB幅・realized_vol・Donchian幅・volume_ratio・swing高値距離・swing安値距離・高値からの経過バー・安値からの経過バー・形スコア・W字・fractal高値距離%・fractal安値距離%・高値切り上げ幅%・安値切り上げ幅%・構造破断距離%・close vs EMA・close vs SMA・close vs VWAP・Keltner上・Keltner下・n本高値・n本安値・pivotPP・pivotR1・pivotS1・fib位置・POC・VAH・VAL・MMI・S-Rタッチ数・AO%・CCI・ER・KST・KSTシグナル・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・SMC_SWEEP・SQZ_ON・STC・STCstoch・StochRSI%K・StochRSI%D・TRIX・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト・UO・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HILO%・close vs HMA%・close vs HT_TRENDLINE%・close vs HWMA%・close vs JMA%・close vs KAMA%・KAMA傾き%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs FAMA%・close vs MCGD%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA%・close vs SINWMA%・close vs SSF%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TSF%・close vs VIDYA%・close vs VWMA%・close vs WMA%・WMA傾き%・close vs ZLMA%・AROONU・AROOND・AROONOSC・CHOP・close vs CKSPl%・close vs CKSPs%・DPO%・close vs PMAX%・close vs PSAR%・PSAR加速・PSAR反転・close vs SAREXT%・VHF・VTXP・VTXM・EFI比・EOM比・NVI傾き・PVT傾き・MAD比・stdev%・close vs MEDIAN%・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・HWC幅%・MASSI・THERMO%・TR%・UI・HT_DCPHASE
```

**別枠の材料**

| 別枠 | 印がオンのもの |
|---|---|
| レンジ幾何 | W%・帯内位置% |
| 需給 | CVD・L-S比・taker_ls |
| 時間帯 | 時刻・曜日 |

**役割ごとに使える系統と時間足（型の表）**

| 役割 | 系統 | 時間足 | レンジ幾何 |
|---|---|---|---|
| env | トレンド・ボラ・時間帯 | 全部 | — |
| location | 構造・位置 | 全部 | 使う |
| sufficiency | ボラ・出来高・需給・オシレーター | 全部 | — |
| trigger | オシレーター・ローソク | 5m・10m・15m | — |

**値の範囲と格子（承認済み・この工事で数字を1つも作らない）**

| 鍵 | 中身 |
|---|---|
| `quantile_grid` | ["q10", "q20", "q30", "q40", "q50", "q60", "q70", "q80", "q90"] |
| `quantile_range` | {"lo": 10, "hi": 90, "kind": "int"} |
| `int_grid` | [3, 6, 12, 24] |
| `int_range` | {"lo": 3, "hi": 24} |
| `state_hold_bars_range` | {"lo": 24, "hi": 288, "kind": "int"} |
| `nest_offset_range` | {"lo": 0, "hi": 1, "kind": "int"} |
| `ref_mult_range` | {"lo": 0.5, "hi": 1.5, "kind": "float", "dec": 2} |
| `hour_range` | {"lo": 6, "hi": 18, "kind": "int"} |
| `material_param_ranges` | （空＝材料カタログの最小〜最大を使う） |

<!-- ACC_MATERIALS_END -->

### 2-3 成績表に載っている本数

<!-- ACC_RANKING_START hash=aa91c5a6fb1e7086 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`material_ranking.json`。

**成績表に載っている列の本数**（札＝強さ・先読み24・執行足より上の時間足だけ）

| 役割 | 上位足の列の本数 | 分離力の高い順に3本 |
|---|---|---|
| env | 1918 | MMI500__1d（0.639）／PWMA20傾き%__1d（0.595）／kurtosis50__1d（0.405） |
| location | 1270 | close vs TSF%20__1d（0.429）／close vs TEMA%20__1d（0.434）／close vs LINREG%20__1d（0.435） |
| sufficiency | 1528 | MMI500__1d（0.639）／kurtosis50__1d（0.405）／MAD比50__1d（0.592） |
| trigger | 250 | TD_SEQ_DN__10m（0.473）／TD_SEQ_DN__15m（0.484）／HT_LEADSINE__10m（0.514） |

**★この本数は、印がオンの指標だけを数えたものではありません。**組む側は `ranked_materials` を通して引き、その関数が印オフの指標を落とします。

<!-- ACC_RANKING_END -->

### 2-4 いま乱数を使っている場所

<!-- ACC_RANDOM_START hash=b77eb360eebdb373 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`engine_tuner_gen.py` を構文の木で読んだ結果（コメントの中の文字は数えません）。

**乱数を使っている関数＝21個 ／ 使っている回数の合計＝64**

| 関数 | 回数 |
|---|---|
| `_make_exits` | 17 |
| `sample_structure` | 7 |
| `synth_df` | 6 |
| `_exit_indicator_cond` | 4 |
| `_make_cond` | 4 |
| `_pair_materials` | 4 |
| `_pick_material` | 3 |
| `_loose_q` | 2 |
| `_pick_exit_material` | 2 |
| `_thr_band_drawn` | 2 |
| `draw_num` | 2 |
| `draw_param` | 2 |
| `_dc1_side` | 1 |
| `_iv` | 1 |
| `_iv_from` | 1 |
| `_mat_drawn` | 1 |
| `_nv` | 1 |
| `_thr_drawn` | 1 |
| `draw_int` | 1 |
| `draw_q` | 1 |
| `write_kakikudashi` | 1 |

**★この工事で0にするのは、場面の判定の束を組む所だけです。**入口は M3、出口は M4 で外します（まこさんが決めた順番）。

<!-- ACC_RANDOM_END -->

## 3｜目標と、やらないこと

### 3-1 やらないこと（1件ずつ・理由と出どころ）

| # | やらないこと | 理由 | 出どころ |
|---|---|---|---|
| 1 | 法則 R2 の上限を 1 から 2 にすること（案A） | 帯の幅だけでなく、束のすべての枠で同じ系統を2本 使えるようになる＝補助の重なりを防ぐという R2 の狙いまで緩む。まこさんが案B を選ばれた | まこさん 2026-09-19「案BでOK」 |
| 2 | 帯の幅をレンジ幾何だけのままにすること（案C） | 2026-09-18 のご指摘（帯の幅を見る指標はもっといっぱいある）が実装に届かない | まこさん 2026-09-18・2026-09-19「案BでOK」 |
| 3 | 法則 R6 に HWC幅% を足すこと | R6 から外れているのは、2026-09-09 に出どころ（外の文献）を取れなかったため。出どころが取れたら まこさんに出して決めていただく話で、この工事の相手ではない | regime_detection_kb.md の R6 の注記 |
| 4 | §2.2 の段2c に「なし」の候補を足すこと | §2.2 の文に在る決まりだが、この工事の1変更に混ぜない。帯の幅は案B（R2 の除く部品）で通るので、3枠目を外す必要がなくなった | cat_requirements §4.6 の H16 |
| 5 | `m2_stage_candidates.json` の語の欄を消すこと | §2.2 の文の写しとして表に残す（前処理・役割・法則の番号は同じ元データから読む）。候補の絞りに使わなくなるだけ | 4-8 |
| 6 | `gen_stage0_match.py` を直すこと | 名前で成績表を探す突き合わせの道具で、候補の決まり方には効かない。この工事の1変更に混ぜない | cat_requirements §4.6 の H16 |
| 7 | 数字（期間・閾値）の出どころを付ける工事 | 候補の絞りの直しとは別の1変更。この工事の後に行う | cat_requirements §4.6 の H16・worklog 20260917 §33 |
| 8 | 印の作り方（gen_indicator_switch.py）・成績表・そのほかの法則を変えること | この工事は、それらを読む側の絞りを直すだけ | まこさん 2026-09-17「オンオフ切り替えてる大元から自動で読み込ませろ」 |

### 3-2 決めてほしいこと

| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|

## 4｜設計の中身

**★この節の項目は、正本 `design_section_sources.json` の3つの出どころ（うちの正本・外の標準・まこさんが過去に指摘したこと）118件を、1件も余さず引き受ける形に決めたものです。**割り当て＝`design_section_map.json`。検算＝`gen_design_sections.py --check`。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

**この項目に書くこと**＝何を作るのか／どういう流れで動くのか／何ができるようになるのか／完成したとき何が出るのか。★項目に分けない。ここだけ読めば全体が分かる状態にする。★★必ず「なぜこの形にするのか」を、ほかの形と比べた実測の数字で書く（この形を取らなかったら何通り・何時間 掛かるか）。★なぜ必須か＝まこさん指摘 2026-09-10「2-2の設計思想は、総当りで組合わせロジックを出すと数百年かかるので、段ごとに絞り込んでいくという方法ということを、このセッション内で何度も言ってるのに、毎回抜けるから、いい加減にしてほしい」。私は「段＝枠を埋める順番」と読み、「段＝候補を絞る段階」という思想を毎回 落とした。

**この仕組みは、場面の判定の候補を、指標のオン・オフの印に連動させるものです。**

**いま何が起きているか。**どの指標を使うかは、M2-C で作った印（`indicator_switch.json`）で決めています。ところが、印より狭い絞りが2か所 残っています。1か所目は、私が M2-E-3 で足した名前の一覧です（§2.2 の文に出てくる名前に完全一致しない指標を落とす）。2か所目は、束の帯の幅の枠です（法則 R7 からレンジ幾何だけを読み、その1件目を固定で使う）。そのため、印がオンで法則も許す指標が候補に出ていません（2-1）。

**どう変えるか。**1つ目の絞りを消します。2つ目は、帯の幅の候補の一覧を作る処理を足し、法則 R7 が名指しした レンジ幾何 と 指標 の両方から候補を作って、成績表の順位で並べます。束はその一覧から、案の番号で決まる順位の1本を取ります。

**なぜ3つ目（法則 R2 の直し）が要るか。**帯の幅を測る指標は3件とも系統が ボラです。法則 R2 は「構造・位置 を除く系統は束の中で1本まで」と決めており、ボラの1本は法則 R6（低ボラ＝幅が狭い側）が既に使っています。だから帯の幅（幅が広い側）を足すと ボラが2本になり、審査 G7 が束を落とします。3枠目を外す道も試しましたが、それでは法則 R6 が0本になって、やはり落ちます。**＝法則 R2 が帯の幅の枠を数から外さない限り、2つ目は1本も束に入りません。**まこさんの決定（2026-09-19・逐語「案BでOK」）で、R2 の数から帯の幅の枠を外す道に決まりました。

**ほかの形と比べて、なぜこの形か。**候補を総当たりで組むのは成り立ちません。まとめて回したときの通り数は `grep -n '通り' .claude/ratchet/s22_combi.md` で、束を1本 測る時間は `grep -n '合計' .claude/ratchet/s22_breakdown.md` で見られます（どちらもプログラムが作った表）。だから §2.2 は段ごとに絞る形にしてあり、この工事はその段の候補の母集団を、印に合わせるものです。母集団を手の一覧で狭めると、印を切り替えても候補が変わらず、絞り込みの出発点が固定されます。

**完成したときに出るもの。**`regime_r9_diag.py --candidates stage2a` に MMI、`--candidates stage2c` に SQZ_ON、`--candidates width` に BB幅・Donchian幅・HWC幅% が出ます。帯の幅に指標を選んだ束が、審査 G7 を通ります。§2.2 の段の表に、実際の候補と、出ない指標の理由が出ます。売買は1件も回さないので、net は動きません。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

**この項目に書くこと**＝このプログラムを呼ぶ相手（人か、別のプログラムか）と、出た結果を次に使う相手。やること／やらないことの線。

**誰が動かすか。**engine_tuner の生成器が、場面の判定の束を組むたびに `build_stage_candidates` と `build_width_candidates` を呼びます。私が `gen_regime_kb.py --write stage` を走らせて、§2.2 の段の表を作ります。

**誰が結果を使うか。**束を組む `sample_regime_build`・束を審査する `_check_scene_rules`（G7）・R9 の診断・まこさん（§2.2 の段の表と、候補を見る口）。

**線。**候補を決める絞りと、帯の幅の枠と、法則 R2 の数え方だけを直します。印の作り方・成績表・そのほかの法則・束のほかの枠は触りません。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

**この項目に書くこと**＝関数やコマンドの取り決め（引数・戻り値・その意味・呼んでよい相手）。

**受け取るもの。**いまと同じ（段の名前・法則・型の表・時間足・設定の欄）。★`m2_stage_candidates.json` の語（名前の一覧）は、候補の絞りには使わなくなります。前処理（pre）・役割（role）・法則の番号（law・law_width）・幾何の列（geo_cols）・真偽の列（bool_col）は、いまどおり読みます。

**出すもの。**候補の一覧（鍵11個・形は変えない）。帯の幅の候補の一覧も同じ形で出します。§2.2 の段の表に、段ごとの「実際の候補」と「出ない指標と理由」の2つの表が足されます。

**法則ファイルに足す欄。**法則 R2 の「機械が読む判定」に `除く部品` を足します。中身は `{"法則": "R7"}` の形で、「この法則が数える部品は、系統の数から外す」という意味です。★法則の一文は1文字も変えません。

### 4-6 制約（従う決まりの全件と、その出どころ）

**この項目に書くこと**＝決まりを1件も落とさずに並べ、どれをどの工程で使うかを書く。動かせないもの（承認済みの設定・取引所の仕様）も。

| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 使う指標は印で一律に切り替える | M2-C（まこさん 2026-09-01「一律でtaの指標のみを使うという切り替えをする」） | 印より狭い絞りを2か所とも消す（名前の一覧・帯の幅の固定） |
| 法則の中身は まこさんが決める | まこさん 2026-09-09「お前が法則を決めるな」 | 法則 R2 に足す欄の中身（除く部品＝R7）は まこさんの決定（2026-09-19「案BでOK」）。法則の一文は1文字も変えない |
| 手で書かざるを得ない部分以外は自動生成 | 恒久69番・まこさん 2026-09-17「手で書くな。すべて自動生成しろ」 | §2.2 の段の表を実際の候補から作る。名前の一覧で候補を決めない |
| 同じ判定を2か所に書かない | 恒久69番 | 帯の幅の候補も、絞りは既にある関数（`ranked_groups`・`_group_usable_col`・型の表）を呼ぶ。役割の名前をコードに書かない |
| 法則と役割で外すものは外す | まこさん 2026-09-17「法則と役割により除外するものは、除外でよい」 | 法則・役割の絞りは残す |
| 乱数を使わない | 恒久67番 | 帯の幅の候補は成績表の順位で並べ、案の番号で順位を選ぶ。乱数を1つも足さない |
| コードを直したら、その行を探す壊すプログラムを grep | L-605 | b86 を直し、b87・b88 を足す（2-1） |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

**この項目に書くこと**＝主要な部品を挙げ、それぞれが何に責任を持つかを書く。部品どうしの協調も。

| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| `engine_tuner_gen.build_stage_candidates` | 名前の一覧で落とす行を消す（印・法則・役割・時間足・標本不足・設定の欄は残す） | 直す |
| `engine_tuner_gen.build_width_candidates` | 帯の幅の候補の一覧を作る。法則 R7 の geo と family の両方から候補を作り、成績表の順位で並べる。絞り（印・時間足・標本・範囲）は既にある関数を呼ぶ。★**指標の系統から役割を引く処理は、この工事で新しく書く**（型の表は「役割 → 系統」を引く形しか持たないため。中身＝型の表の役割を走査し、`lineages` にその系統を含むものを返す数行）。返す形は `build_stage_candidates` と同じ鍵にする（束が取る処理 `_stage_pick` が読むため） | **新設** |
| `engine_tuner_gen.sample_regime_build` | 帯の幅の枠（A）を、その一覧から案の番号で決まる順位で取る（`_stage_pick` と同じ形） | 直す |
| `engine_tuner_exec._check_scene_rules` | 法則 R2 の「除く部品」を読み、そこに書かれた法則が数える部品を、系統の数から外す | 直す |
| `engine_tuner_exec._validate_law` | 「除く部品」の形を検査する（知らない欄・法則ファイルに無い番号なら止まる＝fail-closed） | 直す |
| `engine_tuner_gen.selftest` の T40③-1 | 段1・段2a・段2c で、印と法則と役割と時間足と標本で許される指標の集まりが、候補の指標の集まりと一致すること | 直す |
| `engine_tuner_gen.selftest` の T45 | 帯の幅の候補に R7 の指標3件が出ること。帯の幅に指標を選んだ束が、R2 でも R6 でも審査 G7 を通ること | **新設** |
| `regime_r9_diag.print_stage_candidates` | 段の鍵に `width` を受け、帯の幅の候補を画面に出す | 直す |
| `gen_regime_kb.build_stage` | 段ごとに `build_stage_candidates` を呼び、候補の指標と本数、印がオンで法則が名指しするのに候補に出ない指標と理由を書く | 直す |
| `b86_stage_count.sh` | 消した名前の絞りを戻すと、T40③-1 が落ちることを測る | 直す |
| `b87_width_family.sh` | 帯の幅の枠が法則 R7 の family を読む処理を壊すと、T45 が落ちることを測る | **新設** |
| `b88_r2_exempt.sh` | 法則 R2 の「除く部品」の欄を消すと、T45 が落ちることを測る | **新設** |

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

**この項目に書くこと**＝工程の順番と、工程の間で何を渡すか。組み方の根拠（何の法則で決めるか）も。

1. `build_stage_candidates` が、成績表の順位の組を上から見ます（印がオフの指標は `ranked_materials` が既に外しています）。
2. 参照表・範囲・型の表の系統・時間足・標本不足で落とします（いまどおり）。
3. 法則が名指しした family か系統でないものを落とします（いまどおり）。
4. ★名前の一覧では落としません（この工事で消す）。
5. 設定の欄 `stage_limits` で落とします（いまどおり・いまは空）。
6. ★`build_width_candidates` が、法則 R7 の「数える部品」を読みます。geo（レンジ幾何の列）はそのまま候補にします。family（指標）は、その指標の系統を使える役割を型の表から引き、その役割の成績表の順位から候補を作ります。側は法則 R7 が持つ側（above）です。並びは、レンジ幾何を先頭に置き、その後ろに指標を成績表の順位で並べます。
7. ★`sample_regime_build` が、帯の幅の枠（A）を、6の一覧から案の番号で決まる順位で取ります（`_stage_pick` と同じ形＝上位を何本まで使うかは設定の欄）。
8. ★束の審査（G7）で、法則 R2 が系統を数えるとき、「除く部品」に書かれた法則（R7）が数える部品を先に外します。だから帯の幅が ボラの指標でも、3枠目の低ボラ（ボラ）と両立します。
9. `gen_regime_kb.build_stage` が、段ごとに1〜5の結果を呼んで表にします。出ない指標は、法則が名指しし印がオンの指標のうち、候補に無いものを数え、成績表のその役割に列が在るかで理由を分けます。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

**この項目に書くこと**＝実際の1件が、入口から出口までどう通るか。★読み手が設計を確かめられる唯一の欄。

**通しの例（帯の幅に BB幅 が入る1本）。**

1. **直す前。**BB幅 は印がオンで、法則 R7 が名指ししています。でも束の帯の幅の枠はレンジ幾何の1件目（W%）を固定で使うので、BB幅 は1本も入りません。
2. **直した後（候補）。**帯の幅の候補の一覧に、W%（レンジ幾何）に続いて BB幅・Donchian幅・HWC幅% が、成績表の順位で並びます。役割は、BB幅 の系統（ボラ）を使える役割を型の表から引いたものです。
3. **直した後（束）。**案の番号が BB幅 の順位を指したとき、帯の幅の条件が「BB幅 が閾値より上（幅が広い）」になります。
4. **審査（G7）。**法則 R2 が系統を数えるとき、「除く部品」に書かれた R7 の部品（BB幅）を外します。だから3枠目の低ボラ（例＝stdev% が閾値より下）と両立し、束は通ります。
5. **誰かが「除く部品」の欄を消したら。**T45 が、帯の幅に指標を選んだ束が R2 で落ちることを見つけて失敗します（壊すプログラム b88 が、これを毎回 確かめます）。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

**この項目に書くこと**＝工程ごとに、使う材料（指標）・時間足・閾値の格子・パラメータの範囲・候補の本数。

**非該当。**この工事は探す値の範囲と刻みを変えません（候補の絞りと、束の枠が読む相手を直す工事）。出どころ＝恒久70番の §4 の項目の説明

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

**この項目に書くこと**＝指定できる項目・その置き場・既定値・指定しなかったときの動き。

**変えません。**帯の幅の候補を上位から何本 使うかは、いまある設定の欄（`stage_keep_range`）をそのまま使います。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

**この項目に書くこと**＝できあがったときに出てくるものの形。★4-17（走っている途中の表示）とは別。数字は機械の出力から出す（私が書かない）。

**完成したときに画面に出るもの。**`engine_tuner_gen.py --selftest` の T40 と T45 の行。`regime_r9_diag.py --candidates stage2a` の出力に MMI の行、`--candidates width` の出力に BB幅・Donchian幅・HWC幅% の行。`gen_regime_kb.py --verify` が rc=0。★数は走らせた出力から書きます。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

**この項目に書くこと**＝入力の検証／起こりうる誤りの状態／中途半端な出力が残ったとき／やり直せるか。★正常の道だけを書かない。

| 起きたこと | どうなるか |
|---|---|
| 段の候補が0本 | いまどおり止まる（SampleError） |
| 帯の幅の候補が0本 | 止まる（SampleError＝法則 R7 が geo も family も名指ししていない状態） |
| 法則 R2 の「除く部品」に、法則ファイルに無い番号が書かれている | 法則の読み込みで止まる（fail-closed） |
| 法則 R2 の「除く部品」の形が違う（辞書でない・知らない鍵） | 同じく止まる（fail-closed） |
| 帯の幅に選んだ指標の系統が、どの役割でも使えない | その指標は候補に出ない（型の表が正本＝役割を作らない） |
| 法則が名指しし印がオンなのに候補に出ない指標 | §2.2 の段の表に理由つきで出す（止めない） |
| 名前の絞りが戻された | 自己テスト T40③-1 が落ちる |
| 帯の幅の family を読む処理が壊された | 自己テスト T45 が落ちる |
| 印のファイルが古い | いまどおり `gen_indicator_switch.py --verify` が止める（この工事は触らない） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

**この項目に書くこと**＝途中で作る表の列の意味・鍵の意味・既にあるデータの形をどう変えるか。

**元データの形は変えません。**`m2_stage_candidates.json` はそのまま残します（前処理・役割・法則の番号・幾何の列・真偽の列を読むため）。語の欄は、§2.2 の文の写しとして表に残り、候補の絞りには使いません。

**法則ファイルに欄を1つ足します。**法則 R2 の「機械が読む判定」に `除く部品` を足します（形＝`{"法則": "R7"}`）。ほかの法則には足しません。法則の一文・説明・根拠は1文字も変えません。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

**この項目に書くこと**＝置き場・上書きか追記か・作り直せるか・古いものをどうするか。

**書く先は変えません**（`engine_tuner_milestones2.md` の M2_STAGE の囲み）。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

**この項目に書くこと**＝タイムゾーン／境目の時刻を含むか含まないか／足の締まる時刻の定義。★静かに結果を変えるので、非該当にしない。

**時刻を使いません。**

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

**この項目に書くこと**＝時間と容量。★設計の形を決める材料でもあるので、§6-3 の見積もりとは別に書く。

| 何 | 見込み | 根拠 |
|---|---|---|
| `engine_tuner_gen.py --selftest` の1回 | 約5分30秒 | 2026-09-18 の実測（5分24秒） |
| `engine_tuner_exec.py --selftest` の1回 | 約10秒 | 2026-09-18 の実測（9.6秒） |
| `regime_r9_diag.py --candidates <段>` の1回 | 数秒 | 2026-09-17 の実測（段1 で約4秒） |
| G2・H2 の取り直し | 約6分半 | G2 約30秒・H2 約6分（98回目の実測 333.1秒） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

**この項目に書くこと**＝同じファイル・同じ記録を2つの走行が触らないか。

**奪い合いません。**成績表と印と法則は読むだけです。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

**この項目に書くこと**＝取引所の鍵／本番で実際に発注するかの切り替え／検査済みの記録。

**書き換えられては困る記録。**印・成績表は読むだけです。法則ファイルは R2 に欄を1つ足すだけで、一文は変えません。G2・H2 の印は、決まった道具で取り直します。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

**この項目に書くこと**＝途中経過が見えるか（恒久60番が求める）。後から何が起きたかを追えるか。

**画面に出すもの。**`gen_regime_kb.py --write stage` の完了の行（いまと同じ形）と、`--candidates width` の候補の一覧。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

**この項目に書くこと**＝いま在るもののうち、何がこの部分に依存しているか。★hook 64本と承認・ハッシュ値が絡むので、この repo では特に重い。

1. **場面の判定の束。**候補が増えるので、同じ案の番号でも違う指標が選ばれることが在ります（成績表の順位が上の指標が入るため）。帯の幅も、案の番号によってはレンジ幾何でなく指標になります。
2. **自己テスト T40・T42・T24・T35・T43。**候補の本数が変わります。本数を合格の条件にしている所は無い（T40 の注記）ので落ちない見込みです。★実装の後に全部 走らせて確かめます。
3. **法則の審査（G7）。**R2 の数え方が変わります。**帯の幅の枠の部品だけが数から外れ、ほかの数え方は変わりません。**わざと壊すテスト（既存の G7 破り14通り）が、直す前と同じ結果になることを確かめます。
4. **直す前と後で結果が同じか確かめる3本の走行（S1・S2・L1）。**固定のレシピなので変わらない見込みです。
5. **G2・H2 の印。**engine_tuner_gen.py と engine_tuner_exec.py を触るので失効します。実装の後に G2 → H2 の順で取り直します。
6. **壊すプログラム b86。**探す行を消すので、壊し方を作り直します（4-3）。
7. **`gen_stage0_match.py`。**名前で成績表を探す突き合わせの道具で、候補の決まり方には効きません。触りません（やらないこと）。
8. **売買のロジック・審判・印の作り方・成績表・そのほかの法則。**触りません。

### 4-18 再利用（手本にした、既にあるものの形）

**この項目に書くこと**＝同じ形が既にどこかに在るか。手本にしたファイル（`MODEL:` の行と同じ相手）。

| 手本 | 何を写すか |
|---|---|
| `engine_tuner_gen.build_stage_candidates` | 帯の幅の候補を作るときの絞りの呼び方（`ranked_groups`・`_group_usable_col`・型の表の系統・時間足）と、返す形（鍵11個） |
| `engine_tuner_gen._stage_pick` | 一覧から案の番号で1本 取る形（上位を何本まで使うか・記録の鍵） |
| `engine_tuner_exec._validate_law` の「系統を重ねない」の検査 | 「除く部品」の形の検査（知らない鍵・法則ファイルに無い番号で止める） |
| `.claude/breaks/b86_stage_count.sh` | 壊すプログラム2本（b87・b88）の書き方（EXPECT_RC・MEANS・EXPECT_MSG・guard・measure・finish） |

### 4-A この節に何を書いたか（一覧）

**★この表は管理のためのものです。**設計の中身は上の 4-0 から順に読んでください。

| 番号 | 段 | 項目 | 書いたか |
|---|---|---|---|
| 4-0 | 必ず | この仕組みは何か（全体・一続きの文章で書く） | 書いた |
| 4-1 | 必ず | システムの境界（誰が動かし、誰が結果を使うか） | 書いた |
| 4-2 | 必ず | 入力と出力（受け取るもの・出すもの・その形） | 書いた |
| 4-6 | 条件 | 制約（従う決まりの全件と、その出どころ） | 書いた |
| 4-3 | 必ず | 部品と責任の割り当て（どの部品が何をやるか） | 書いた |
| 4-4 | 必ず | 処理の流れ（うまくいったとき、何がどの順に起きるか） | 書いた |
| 4-19 | 必ず | 通しの例（最初から最後まで、1件を追いかけた例） | 書いた |
| 4-7 | 条件 | 探索の範囲（決める値と、その探し方＝範囲・並び・本数） | 非該当（この工事は探す値の範囲と刻みを変えません（候補の絞りと、束の枠が読む相手を直す工事）。出どころ＝恒久70番の §4 の項目の説明） |
| 4-9 | 条件 | 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗） | 書いた |
| 4-12 | 必ず | 出る結果の姿（完成したとき、何がどう表示されるか） | 書いた |
| 4-5 | 必ず | 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか） | 書いた |
| 4-8 | 条件 | データ構造（表や JSON の列と中身を、新しく作るか・変えるか） | 書いた |
| 4-10 | 条件 | 保存先（出したものをどこに置くか・上書きか、書き足すか） | 書いた |
| 4-11 | 条件 | 時刻の扱い（時間帯・足の区切りをどこで切るか） | 書いた |
| 4-14 | 条件 | 性能（どれくらい時間が掛かり、どれくらい容量を使うか） | 書いた |
| 4-15 | 条件 | 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか） | 書いた |
| 4-16 | 条件 | セキュリティ（人に見せてはいけない値と、書き換えられては困る記録） | 書いた |
| 4-17 | 省ける | ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか） | 書いた |
| 4-13 | 必ず | 影響範囲（この直しで、ほかのどれが壊れるか） | 書いた |
| 4-18 | 省ける | 再利用（手本にした、既にあるものの形） | 書いた |


## 5｜決めたことと理由・捨てた案

| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 法則 R2 の数から、帯の幅の枠（法則 R7 が数える部品）を外す | R2 の一文は「補助（トレンドの強さ・値動きの幅・出来高）は、違う系統から選ぶ」＝補助の重なりを防ぐもの。帯の幅（R7）は補助ではなく、レンジが成立する条件（往復の手数料を超える幅が在るか）。まこさんが案B を選ばれた（2026-09-19「案BでOK」） | 案A＝R2 の上限を 2 にする。捨てた理由＝束のすべての枠が緩む／案C＝いまのまま。捨てた理由＝ご指摘が実装に届かない |
| 2 | 帯の幅の候補を作る関数を新しく足す（段の候補の枠組みに入れない） | 段の候補は「1つの段＝1つの役割」を前提にしている。帯の幅は、レンジ幾何（役割 location）と 指標（系統がボラ＝別の役割）の2つにまたがるので、その枠組みに乗らない | §2.2 の候補の元データに段を1つ足す。捨てた理由＝段は §2.2 の表と1対1で、まこさんの文に無い段が表に増える |
| 3 | 帯の幅に使う指標の役割は、型の表から機械で引く | BB幅 の系統はボラで、役割 location では引けない。役割の名前をコードに書くと、型の表を変えたときに食い違う | 役割の名前（sufficiency）をコードに書く。捨てた理由＝恒久69番（同じ判定を2か所に書かない） |
| 4 | 名前の絞りを消すだけにし、段の候補の関数は増やさない | 上の段の関数を足すと、設計書の SPEC と実物が合わなくなる | 候補と除外の理由を返す新しい関数を作る。捨てた理由＝承認が2回になる |
| 5 | §2.2 の段の表は `build_stage_candidates` を呼んで作る | 候補の絞りを表の道具に写すと、2か所で食い違う（今回の名前の絞りと同じ型） | 表の道具に絞りを書き写す。捨てた理由＝恒久69番 |
| 6 | 出ない指標の理由は2つに分ける（成績表のこの役割に列が無い／時間足と標本不足で0本） | `build_stage_candidates` は落とした組を返さないので、表の道具は候補に無い指標しか分からない。成績表に列が在るかは表の道具が確かめられる | 落とした段（時間足・標本不足・範囲）を1つずつ出す。捨てた理由＝新しい関数か戻り値の変更が要る |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

<!-- ACC_SELFTEST_START hash=2d7e93cfde62d79d gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝元データの「完成の条件」。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b86_stage_count.sh` | #1 | 名前の一覧で候補を落とす行を戻すと、T40③-1 が『❌ T40③-1』で落ちる |
| `b87_width_family.sh` | #3 | 帯の幅の枠が法則 R7 の family を読む処理を壊すと、T45 が『❌ T45』で落ちる |
| `b88_r2_exempt.sh` | #4 | 法則 R2 の「除く部品」の欄を消すと、T45 が『❌ T45』で落ちる |
| `—` | #2・#5・#6・#7 | 壊すプログラムは付けない（1行目の b86 が同じ絞りを測る） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

| # | リスク | どうするか |
|---|---|---|
| 1 | 候補が増えて、束を組む自己テスト（T42 など）の時間が延びる | 実装の後に全部 走らせて時間を記録する。延びすぎたら まこさんに出す |
| 2 | 法則 R2 の数え方を変えたことで、いままで落ちていた束が通るようになる（帯の幅の枠 以外でも） | 「除く部品」は法則 R7 が数える部品だけを外す。既存の G7 破りのテスト（14通り）が直す前と同じ結果になることを確かめる。T45 でも、帯の幅 以外の重なりは今までどおり落ちることを見る |
| 3 | 帯の幅に指標が入ると、レンジ幾何 W% を使う束が減る | 候補の並びはレンジ幾何を先頭に置く（案の番号が小さいうちは W% が選ばれる）。どちらが良いかは判定の成績（M2-F〜H）で測る |
| 4 | T40③-1 の「許される指標の集まり」を作る処理が、`build_stage_candidates` の絞りと食い違う | 同じ関数を呼んで作る（4-18）。食い違ったら T40③-1 が落ちるので、実装の後に分かる |
| 5 | `gen_regime_kb.py --write stage` が engine_tuner_gen を呼ぶので、G2・H2 の印が合わないと止まる | 実装の後に G2 → H2 を取り直してから --write する |

### 6-3 見積もり

| 何 | 見込み | 根拠 |
|---|---|---|
| コードの直し（5ファイル＋壊すプログラム2本） | 2時間 | ★実測ではない（前の版の見込みは3ファイルで1時間） |
| 走らせて確かめる（自己テスト3回・候補の口4回・G2・H2・--write と --verify） | 約40分 | 4-14 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

**① 真因（root cause）**＝印より狭い絞りを、私が2か所 作ったことです。1か所目は M2-E-3 で足した名前の一覧（§2.2 の文から私が作った）で、M2-C で作った印と照らしませんでした。2か所目は、2026-09-09 に法則 R7 から帯の幅の指標3件を外したことです（外した根拠は私の判断で、まこさんの承認ではありませんでした）。その結果、束の帯の幅の枠はレンジ幾何の1件目しか読まない状態になりました。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。動くのは、場面の判定の束を組む候補の数（名前の一覧と帯の幅の固定だけを理由に落ちていた指標が入る）です。

**③ root か symptom か**＝root です。symptom の直し方は、名前の一覧に MMI と SQZ_ON を書き足し、帯の幅にも指標の名前を1件ずつ書き足すことで、印を変えるたびに一覧も直す必要が残ります。この設計は、印より狭い絞りそのものを2か所とも無くします。

**④ ベースアップ**＝この工事で外の検索はしていません。実物は、読むもの宣言（`design_read_plan.md`・まこさんの OK 2026-09-19「OK」）に書いた20件を Read tool で開きました。数は 2-1 の表のコマンドで数えました。法則の審査の数え方（R2 が系統を数える所・R6 が側で数える所）は、`engine_tuner_exec.py` の実物を開いて確かめました。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

この工事に、疑似シミュから取った値は1つもありません。

### 7-3 変更の単位（H16）

変更の単位は「印でオンにした指標が、候補の母集団になる（帯の幅を含む）」の1つです（まこさん 2026-09-18「印でオンにした指標だけを、候補の母集団として読み込むことができるのであればOK」）。3つの直し（名前の一覧を消す・帯の幅の枠が指標を読む・法則 R2 が帯の幅の枠を数から外す）は、その1つを成立させる部品です。★3つ目が無いと2つ目は1本も束に入りません（4-0）。T40③-1・T45・b86・b87・b88・§2.2 の段の表の直しは、同じ絞りを測る・見せるための部品です。H1〜H16 と審判整合（群2）は非該当です（売買のロジックにも審判にも触れないため）。過去に取りやめた失敗の再演か＝当たりません。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | この工事は乱数を1つも足しません。候補は成績表の順位で並び、束はその順位から案の番号で取ります。 |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | この工事は数字も指標の名前も書きません。候補は印・法則・成績表・型の表から機械で決まります。 |

### 7-4 塞げないもの

| 問い | 塞げないこと |
|---|---|
| **候補が増えた後の束は良い判定か** | この工事では分かりません。判定の成績は M2-F〜H で測ります |
| **帯の幅は レンジ幾何 と 指標 のどちらが良いか** | この工事では決めません。候補として両方 並べるだけで、良し悪しは M2-F〜H の成績と M2-L の net で測ります |
| **法則 R2 の数から帯の幅を外す読み方が正しいか** | 私は決めません。まこさんの決定（2026-09-19「案BでOK」）に従います。この読み方が net に効くかは、この工事では分かりません |
| **出ない指標の理由を、時間足・標本不足・範囲のどれかまで分けられるか** | 分けません。成績表に列が在るかどうかの2つだけです |
| **印そのものが正しいか** | この工事では見ません（gen_indicator_switch.py の --verify と --selftest が見ます） |
| **この道具と壊すプログラムそのものを書き換えられたら** | 書き換えれば無効にできます。承認で凍結され、差分は git に出ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認済みで凍結されているため） |

### 7-5 §4.6 ハード制約の照合

<!-- ACC_CHECKLIST_START hash=cb5f35c3aee2bdd1 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

- 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記）
- 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine`
- 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ
- 【群1】① 真因（root cause・損/不足の構造的原因）
- 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか）
- 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由）
- 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止）
- 【群1】変更は 1レバーか（複数混ぜない）
- 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行）
- 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設
- 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc
- 【群1】H16 1変更・過去失敗の不再演
- 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③）
- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。**★触る関数の一覧は、実装の後に確定させます**＝`verify_design_contract.py --write` の出力で置き替えます。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 候補が印と法則と役割と時間足と標本だけで決まる。`engine_tuner_gen.py --selftest` の T40③-1 が pass（許される指標の集まりと候補の指標の集まりが一致） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 実経路 | 名前の一覧で候補を落とす行を戻すと、T40③-1 が『❌ T40③-1』で落ちる | `b86_stage_count.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝候補の絞りに名前の一覧を戻すと、T40③-1 が「許される指標が候補に出ていない」で落ちた|
| 2 | 段2a の候補に MMI が出る。`regime_r9_diag.py --candidates stage2a` の出力に MMI の行が在る | `python3 scripts/priority_rebuild/regime_r9_diag.py --candidates stage2a` | 実経路 | 壊すプログラムは付けない（1行目の b86 が同じ絞りを測る） | `—` | — | **未着手** |
| 3 | ★帯の幅の候補に、法則 R7 が名指しした指標3件（BB幅・Donchian幅・HWC幅%）が出る。`regime_r9_diag.py --candidates width` の出力に3件の行が在る | `python3 scripts/priority_rebuild/regime_r9_diag.py --candidates width` | 実経路 | 帯の幅の枠が法則 R7 の family を読む処理を壊すと、T45 が『❌ T45』で落ちる | `b87_width_family.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝帯の幅の枠が法則 R7 の指標を読む処理を壊すと、T45 が「帯の幅の候補に指標が出ない」で落ちた|
| 4 | ★帯の幅に指標を選んだ束が、法則 R2 でも R6 でも審査 G7 を通る。`engine_tuner_gen.py --selftest` の T45 が pass | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 実経路 | 法則 R2 の「除く部品」の欄を消すと、T45 が『❌ T45』で落ちる | `b88_r2_exempt.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝法則 R2 の「除く部品」を読まなくすると、帯の幅に指標を選んだ束が審査 G7 で拒否され、自己テストが落ちた |
| 5 | ★法則の読み込みが、「除く部品」の形と番号を検査して止まる（fail-closed）。`engine_tuner_exec.py --selftest` の B0 の枝が pass | `python3 scripts/priority_rebuild/engine_tuner_exec.py --selftest` | 実経路 | 壊すプログラムは付けない（既存の B0 fail-closed の枠組みが同じ形で測る） | `—` | — | **未着手** |
| 6 | §2.2 の段の表が実際の候補から作られている。`gen_regime_kb.py --verify stage` が rc=0 | `python3 ../../.claude/tools/gen_regime_kb.py --verify stage` | 実経路 | 壊すプログラムは付けない（読むための表・恒久71番） | `—` | — | **未着手** |
| 7 | 直す前と後で結果が同じか確かめる3本の走行（S1・S2・L1）が変わらない | `python3 scripts/priority_rebuild/engine_tuner_exec.py --identity` | 実経路 | 壊すプログラムは付けない（既存の恒等の仕組み） | `—` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

<!-- ACC_CODEREF_START hash=8985a2a13788406b gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/engine_tuner_gen.py`

| 触る関数 | 定義の行 |
|---|---|
| `build_stage_candidates` | 2775 |
| `build_width_candidates` | 2937 |
| `stage_tfs_of` | 2721 |
| `stage_lineages_of` | 2751 |
| `stage_limits_of` | 2650 |
| `ranked_groups` | 2290 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 157件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

<!-- ACC_SPEC_START hash=c5f075dcd08c6546 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
  "impl_functions": {
    "scripts/priority_rebuild/engine_tuner_gen.py": [
      "build_stage_candidates",
      "build_width_candidates",
      "sample_regime_build",
      "selftest"
    ],
    "scripts/priority_rebuild/engine_tuner_exec.py": [
      "_check_scene_rules",
      "_validate_law"
    ],
    "scripts/priority_rebuild/regime_r9_diag.py": [
      "print_stage_candidates"
    ],
    ".claude/tools/gen_regime_kb.py": [
      "build_stage"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数。`build_width_candidates` は新設。照合A は commit 済みの版（HEAD）との差で数える＝直すファイルの差は0（2-1）なので、この7つだけになる。",
  "self_check_calls": [
    "build_stage_candidates",
    "build_width_candidates",
    "stage_tfs_of",
    "stage_lineages_of",
    "stage_limits_of",
    "ranked_groups"
  ],
  "_self_check_calls の意味": "7-7 の表に出す engine_tuner_gen.py の関数の名前。`build_width_candidates` は この工事で新しく作るので、実装の後に在る。",
  "must_use": {
    "build_stage_candidates": [
      "stage_tfs_of",
      "stage_lineages_of",
      "stage_limits_of",
      "ranked_groups",
      "_group_usable_col"
    ],
    "build_width_candidates": [
      "_law_geo",
      "_law_families",
      "ranked_groups",
      "_group_usable_col"
    ],
    "sample_regime_build": [
      "build_width_candidates",
      "_stage_pick"
    ],
    "selftest": [
      "build_stage_candidates",
      "build_width_candidates",
      "ranked_groups"
    ],
    "build_stage": [
      "expand_stage",
      "build_stage_candidates"
    ]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "組む側が外から読む一覧（印・法則・成績表・範囲の鍵）は、この工事で増やさない。読む側の絞りを2か所 消し、法則 R2 に欄を1つ足すだけで、一覧を書き替えると候補と審査が変わることは自己テスト T40③-1 と T45 が振る舞いで測る。",
  "generated_from": {
    "impl_functions": "設計の段で、中身を直す関数と新しく作る関数を書いた（HEAD との差が0なのを git で確かめた）",
    "must_use": "いまの呼び出しと、直した後に呼ぶ名前（4-3・4-18）",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
 "public_functions": {
  "load_limits": [],
  "HoldRangeError": [],
  "resolve_hold_range": [
   "HoldRangeError"
  ],
  "hold_bars": [
   "HoldRangeError"
  ],
  "material_pool": [],
  "material_ranges": [
   "load_limits"
  ],
  "param_in_range": [
   "material_ranges"
  ],
  "draw_param": [
   "material_ranges"
  ],
  "assert_provenance": [
   "SampleError",
   "material_ranges",
   "param_in_range",
   "q_range_of"
  ],
  "assert_roles": [
   "SampleError"
  ],
  "assert_exit_roles": [
   "SampleError"
  ],
  "validate_drawn": [
   "strip_marks"
  ],
  "strip_marks": [],
  "int_range_of": [],
  "draw_int": [
   "int_range_of"
  ],
  "num_range_of": [],
  "draw_num": [
   "num_range_of"
  ],
  "ladder_min_frac": [],
  "max_ladder_steps": [
   "ladder_min_frac",
   "num_range_of"
  ],
  "q_range_of": [],
  "quantile_list": [
   "q_range_of"
  ],
  "draw_q": [
   "q_range_of"
  ],
  "q_in_range": [
   "q_range_of"
  ],
  "num_in_range": [
   "num_range_of"
  ],
  "SampleError": [],
  "load_signal_table": [],
  "load_material_ranking": [],
  "ranked_materials": [
   "load_material_ranking"
  ],
  "same_fn_family_pairs": [],
  "pair_allowed": [
   "same_fn_family_pairs"
  ],
  "load_exit_table": [],
  "ranked_groups": [
   "ranked_materials"
  ],
  "regime_draw_order": [
   "SampleError"
  ],
  "laws_for_scene": [
   "SampleError"
  ],
  "stage_candidates": [
   "SampleError"
  ],
  "drop_tfs_of": [
   "SampleError"
  ],
  "stage_limits_of": [
   "SampleError",
   "material_ranges",
   "q_range_of"
  ],
  "stage_tfs_of": [
   "SampleError",
   "drop_tfs_of",
   "stage_limits_of"
  ],
  "stage_lineages_of": [
   "SampleError"
  ],
  "build_stage_candidates": [
   "SampleError",
   "int_range_of",
   "material_ranges",
   "ranked_groups",
   "stage_candidates",
   "stage_limits_of",
   "stage_lineages_of",
   "stage_tfs_of"
  ],
  "build_width_candidates": [
   "SampleError",
   "material_ranges",
   "ranked_groups",
   "stage_candidates",
   "stage_tfs_of"
  ],
  "stage_keep_of": [
   "SampleError"
  ],
  "stage_counts": [
   "build_stage_candidates",
   "stage_keep_of"
  ],
  "sample_regime_build": [
   "SampleError",
   "build_stage_candidates",
   "build_width_candidates",
   "laws_for_scene",
   "regime_draw_order",
   "stage_candidates",
   "stage_counts",
   "stage_keep_of"
  ],
  "default_regime": [],
  "sample_structure": [
   "SampleError",
   "default_regime",
   "load_signal_table",
   "sample_regime_build"
  ],
  "recipe_hash": [
   "strip_marks"
  ],
  "write_kakikudashi": [],
  "structure_breakdown": [],
  "needed_qkeys": [],
  "build_qtable": [
   "needed_qkeys"
  ],
  "attach_materials": [],
  "pvalue_daily": [],
  "bh_select": [],
  "strat_gate": [],
  "Journal": [],
  "assert_known_exit_reason": [],
  "run_trial": [
   "strip_marks"
  ],
  "run_trial_guarded": [
   "run_trial"
  ],
  "reject_code": [],
  "zero_trade_gate": [],
  "per_day_gate": [
   "zero_trade_gate"
  ],
  "suggest_slot": [],
  "value_slots": [
   "hold_bars",
   "int_range_of",
   "num_range_of",
   "q_range_of"
  ],
  "apply_slots": [],
  "read_slots": [],
  "run_generation": [
   "Journal",
   "apply_slots",
   "bh_select",
   "build_qtable",
   "load_signal_table",
   "per_day_gate",
   "pvalue_daily",
   "quantile_list",
   "read_slots",
   "recipe_hash",
   "reject_code",
   "run_trial",
   "run_trial_guarded",
   "sample_structure",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "suggest_slot",
   "value_slots",
   "write_kakikudashi"
  ],
  "synth_df": [],
  "selftest_rank_demand": [
   "load_signal_table",
   "ranked_groups",
   "ranked_materials"
  ],
  "selftest": [
   "Journal",
   "apply_slots",
   "assert_known_exit_reason",
   "assert_provenance",
   "bh_select",
   "build_qtable",
   "build_stage_candidates",
   "build_width_candidates",
   "drop_tfs_of",
   "gate_matrix",
   "ladder_min_frac",
   "laws_for_scene",
   "lint_provenance",
   "load_exit_table",
   "load_limits",
   "load_material_ranking",
   "load_signal_table",
   "material_pool",
   "material_ranges",
   "max_ladder_steps",
   "needed_qkeys",
   "num_in_range",
   "pair_allowed",
   "param_in_range",
   "per_day_gate",
   "pre_run_gate",
   "pvalue_daily",
   "q_in_range",
   "q_range_of",
   "quantile_list",
   "ranked_groups",
   "ranked_materials",
   "read_slots",
   "regime_draw_order",
   "reject_code",
   "resolve_hold_range",
   "run_generation",
   "run_trial_guarded",
   "sample_regime_build",
   "sample_structure",
   "selftest_rank_demand",
   "stage_candidates",
   "stage_counts",
   "stage_keep_of",
   "stage_lineages_of",
   "stage_tfs_of",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "synth_df",
   "validate_drawn",
   "value_slots",
   "verify_provenance",
   "zero_trade_gate"
  ],
  "pre_run_gate": [],
  "run_main": [
   "assert_known_exit_reason",
   "hold_bars",
   "load_limits",
   "material_pool",
   "pre_run_gate",
   "resolve_hold_range",
   "run_generation"
  ],
  "main": [
   "gate_matrix",
   "lint_provenance",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "run_main",
   "sample_structure",
   "selftest",
   "selftest_rank_demand",
   "strip_marks",
   "structure_breakdown",
   "verify_provenance"
  ],
  "lint_provenance": [],
  "gate_matrix": [
   "apply_slots",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "material_ranges",
   "resolve_hold_range",
   "run_trial_guarded",
   "sample_structure",
   "value_slots"
  ],
  "verify_provenance": [
   "load_limits",
   "load_signal_table",
   "resolve_hold_range"
  ]
 },
 "constants": {
  "PARAM_SRC": "_param_src",
  "Q_SRC": "_q_src",
  "NUM_SRC": "_num_src",
  "LIN_SRC": "_lineage_src",
  "ATTACH_CALLS": 0
 },
 "cli_flags": []
}
```

<!-- ACC_SPEC_END -->
