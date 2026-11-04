<!-- FOLDER_MAP_GENERATED names=c54536c0c170249a gen_folder_map.py が実物を数えて作った＝手で書き換えない -->
# ディレクトリマップと置き場のルール（ファイルを探す前・作る前にここを見る）

作成: 2026-08-02（まこさん「なんで似たようなフォルダが複数あるの？ 整理できない？」）。**2026-10-02 から、この文書は `.claude/tools/gen_folder_map.py` が実物を数えて作る**（まこさん「Aをやる」）。数えた日＝2026-11-04。

## 結論：2つあり、役割が違います

| 場所 | ひとことで |
|---|---|
| **直下の `.claude/`** | **Claude Code を動かす仕組み**（hook・道具・設定・いまの状態） |
| **`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/`（sdk の方）** | **BOT プロジェクトの文書**（要件定義書・マイルストーン・監査・教訓） |

## トレードBOT の情報のレベルごとの置き場（2026-11-03・まこさん「３，OK」）

根のフォルダは `v3-bitget-api-sdk/bitget-python-sdk-api/` です。レベルの定義の正本は `.claude/rules/cat_requirements.md` の §1.2.2 です。

| レベル | データと読むプログラム | 人が読む文書 |
|---|---|---|
| 1 BOT の運用ルール | `scripts/priority_rebuild/bot_rules/`（244番と242番で作る）。期間は `periods.py` のまま | `.claude/rules/cat_requirements.md`。取引所は `exchange_spec.md`（244番で GMOコインへ直す） |
| 2 トレード戦略 | `.claude/ratchet/adopted_strategies.md`（台帳のまま） | 同じ台帳 |
| 3 トレードロジックの組み方（法則） | `scripts/priority_rebuild/laws/`（209番で作り、195番で regime_laws.json を移す） | `.claude/rules/法則一覧.md`（209番で laws.json から作る）。出どころの資料は `.claude/memory/` の KB のまま |
| 4 トレードロジックの材料（要素） | `scripts/priority_rebuild/indicators/` | `.claude/rules/要件定義書_レベル4_指標の構造.md`（正本）と `要件定義書_レベル4_指標の集約工事.md` |

## 置き場のルール（恒久の決まり78番・79番が元。本文はそちらが正本）

1. ファイルを作る前に、情報のレベルを決め、上の表で置き場を決めます。
2. データと読むプログラムは、レベルごとのフォルダに置きます。人が読む文書は、sdk の `.claude/rules/` に置きます。
3. 調べの途中の出力は、Claude Code の作業場に書きます。リポジトリの中に書きません。
4. 同じ中身の写しと控えを作りません。控えが要るなら、git のコミットで残します。
5. 新しいファイルやフォルダは、作る前に まこさんに伺います。作ったら、下の表の役割を `gen_folder_map.py` の ROLES に1行足します。足さないと `--verify` が止まります。
6. 消す物と動かす物は、読む所と git を調べ、まこさんの OK を取ってから消します。下の表の「消す候補」も同じです。
7. `.claude/state` の直下に在ってよい物は、下の「`.claude/state` の直下の中身」の表だけです。表に無い物が増えると、`--verify` が止め、ターンを終われません（まこさん 2026-11-04）。`audits` の直下は決まった名前の形だけ、`scripts/priority_rebuild` と `ratchet` の直下は git に在る物と、いまの設計書に名前が在る物だけです。

## sdk 直下（`v3-bitget-api-sdk/bitget-python-sdk-api/`）の中身

| 名前 | 何が入っているか | ファイルの数 | 大きさ |
|---|---|---|---|
| `README.md` | Bitget SDK の説明。消す候補（246番） | 1 | 4.5KB |
| `README_EN.md` | Bitget SDK の説明の英語版。消す候補（246番） | 1 | 4.2KB |
| `WORKFLOW.md` | 作業の決まりと監査の一覧。現在地は書かない（現在地は next_step.md） | 1 | 90.9KB |
| `archive/` | 古い資料の控え（regime_research・workflow） | 15 | 912.0KB |
| `bitget/` | Bitget の公式 SDK。消す候補（246番） | 31 | 53.9KB |
| `cat/` | V9 の指標の計算と定数（indicators.py・const.py）。変更禁止（core_rules.md）。engine_tuner の指標はここでなく scripts/priority_rebuild/indicators/ | 9 | 31.2KB |
| `cc_ml_design_spec.md` | ML の頃の実装指示書（2026-05-13） | 1 | 24.7KB |
| `config/` | V9 のパラメータと取引所の鍵。鍵の中身は出さない | 4 | 7.8KB |
| `configs/` | ML の頃の設定（recipes.yaml ほか） | 4 | 16.5KB |
| `dashboard/` | ブラウザで見る画面と、そのデータ（index.html・data）。大半は git に入っていない | 497 | 208.4MB |
| `data/` | 相場データ（5分足・1分足の CSV ほか）。大半は git に入っていない | 108 | 465.7MB |
| `drafts/` | 2026-04 の引き継ぎのメモ | 3 | 13.4KB |
| `engine_tuner_e38_S2.log` | engine_tuner の走行ログ（2026-08-19）。消す候補（tuner_writeback.py が名前を持つので確かめてから） | 1 | 12.7KB |
| `example.py` | Bitget SDK の例（2025-12）。消す候補（246番） | 1 | 2.1KB |
| `example_ws_contract.py` | Bitget SDK の例（2025-12）。消す候補（246番） | 1 | 890B |
| `logs/` | V9 の頃の走行ログ。git に入っていない | 50 | 40.4MB |
| `models/` | HMM の学習済みモデル（.pkl）。git に入っていない | 4 | 14.9KB |
| `requirements.txt` | Python の依存の一覧 | 1 | 3.2KB |
| `results/` | 実験の結果（採点の CSV ほか）。大半は git に入っていない | 1,142 | 300.9MB |
| `runner/` | V9 の本番の実行（run_once_v9.py）と検証のプログラム、Bitget の発注（bitget_adapter.py）。Bitget の部分は消す候補（246番） | 20 | 269.8KB |
| `scripts/` | プログラム。中身は下の表 | 337 | 11.3MB |
| `state/` | V9 の本番の状態ファイル。run_once_v9.py 経由以外で変更しない（core_rules.md） | 77 | 663.4KB |
| `strategies/` | V9 の入口の判断（cat_v9_decider.py） | 2 | 37.5KB |
| `tools/` | V9 の頃の調べのプログラムと、足の取得のプログラム | 13 | 114.0KB |

## `scripts/` の中身

| 名前 | 何が入っているか | ファイルの数 | 大きさ |
|---|---|---|---|
| `dashboard/` | 画面のデータを作るプログラム | 17 | 167.5KB |
| `data/` | 相場データを取得するプログラム | 11 | 50.7KB |
| `grid_search/` | 格子探索のプログラム1本（recipe_grid_search.py） | 1 | 4.5KB |
| `hmm/` | HMM の研究のプログラム | 16 | 124.3KB |
| `labels/` | 日足の場面の正解ラベルを作るプログラム | 4 | 20.4KB |
| `priority_rebuild/` | engine_tuner・E38・採点の本体。レベル1・3・4 のデータも、この下のフォルダに置く | 237 | 10.3MB |
| `regime/` | 場面の判定の研究のプログラム | 33 | 533.7KB |
| `signal_research/` | シグナルの研究のプログラム | 17 | 64.6KB |

指標の工事に関わるファイルの詳しい一覧は、`.claude/rules/要件定義書_レベル4_指標の構造.md` の第3章の3 の「8 ディレクトリマップ」に在ります。

## なぜ `.claude` が2つあるか

Claude Code は、起動した場所の直下の `.claude/` しか設定として読みません。だから hook の登録と実体は、リポジトリ直下にしか置けません。sdk の方は、それより前からあるプロジェクトの資料置き場です。

## 直下の `.claude/` の中身

| 名前 | 何が入っているか | ファイルの数 | 大きさ |
|---|---|---|---|
| `archive_rules/` | 使わなくなったルールの控え | 1 | 26.5KB |
| `breaks/` | 壊すプログラム（わざと壊して、検査が止まるかを試す） | 245 | 422.3KB |
| `context/` | V9 の頃の資料（構造の地図・ファイル構成・リリース手順・テストの一覧） | 4 | 47.5KB |
| `hooks/` | hook（ファイルを書く・コマンドを打つ・ターンを終える直前に自動で走り、通すか止めるかを決めるプログラム） | 164 | 1.4MB |
| `instructions/` | 指示書 | 125 | 1.4MB |
| `ml_axis_catalog.md` | ML の決める値（23軸）の一覧（2026-05） | 1 | 26.8KB |
| `pm_review_template.md` | PM の見直しのサブエージェントへの説明のひな形 | 1 | 17.2KB |
| `review_lens.md` | Web 版 Claude の見直しの視点（凍結・参照のみ） | 1 | 12.4KB |
| `rules/` | CC の動き方の決まり（毎セッション自動で読み込まれる） | 8 | 359.3KB |
| `settings.json` | Claude Code の設定（hook の登録）。git に入っている | 1 | 10.1KB |
| `settings.local.json` | この PC だけの許可の設定 | 1 | 9.6KB |
| `state/` | いまの状態（next_step・worklog・ToDo・設計書・承認の記録・調べの道具） | 1,128 | 39.9MB |
| `templates/` | 指示書のひな形 | 4 | 56.7KB |
| `tools/` | 道具（文書を作る・検査する・片づける） | 31 | 1.3MB |

## `.claude/state` の直下の中身

| 何が入っているか | ファイルの数 |
|---|---|
| 引き継ぎ（次にやること） | 10 |
| 日付ごとの作業の記録 | 96 |
| 設計書と承認 | 15 |
| 過去の決定の文（文書が指す） | 4 |
| 検査済みの記録 | 7 |
| 要件と試験の対応表 | 2 |
| 指標の資料（教科書の表ほか・消す時期は162番） | 14 |
| hook の一覧 | 5 |
| hook が書く印とログ | 17 |
| 文書が根拠に挙げる調べのプログラム | 3 |
| E37 の調べの結果（E37 は保留） | 9 |

| フォルダ | 何が入っているか |
|---|---|
| `verbatim/` | まこさんの言葉の逐語と、工事ごとの設計書の元 |
| `indicator_review/` | 指標の工事の調べと写すプログラム |
| `sessions/` | セッションごとの hook の記録（終わった物は tidy_next_step.py が消す） |
| `reviews/` | 設計書と依頼書の見直し表 |
| `hook_fix_proposals/` | hook の直しの案 |
| `precheck_pass_results/` | 採点の前の検査の結果 |

## sdk の `.claude/` の中身

| 名前 | 何が入っているか | ファイルの数 | 大きさ |
|---|---|---|---|
| `auditor_template.md` | 監査のサブエージェントへの説明のひな形 | 1 | 38.9KB |
| `audits/` | 監査の依頼書・結果・作業のフォルダ | 438 | 15.3MB |
| `memory/` | 教訓（lessons_active・lessons_archive）・知識の文書（KB） | 43 | 2.9MB |
| `ratchet/` | マイルストーン・やることリスト（m2_todo.json）・設計書の控え・決定（decisions.md） | 2,008 | 39.6MB |
| `rules/` | BOT の中身の決まり（要件定義書 cat_requirements.md ほか） | 14 | 778.0KB |
| `state` | 直下の .claude/state への近道（シンボリックリンク）＝同じフォルダ | 0 | — |

## 同じ名前のフォルダ（迷いやすい所）

- **rules**＝直下は CC の動き方の決まり（毎回 自動で読まれる）／sdk は BOT の中身の決まり（要件定義書ほか）。
- **state**＝1つだけ。sdk の `state` は直下の `.claude/state` を指す近道なので、どちらから開いても同じファイル。
- **audits**＝sdk の方だけを使う（直下の `.claude/audits` は 2026-10-02 に sdk の `audits/cp29_work/` へ移した）。

## 動かさない理由（★まとめる工事は「B」として next_step の「5 プロジェクトのやることの表」に在る）

sdk の方を名指ししている hook が **17個** あります（数えた日 2026-11-04）。文書を作る道具も、パスを埋め込んで作り、ハッシュ値で改変を見ています。動かすと hook が黙って効かなくなる危険があります。だから場所は変えず、この地図で迷わないようにしました（まこさん確定 2026-08-02・案B）。2つを1つにまとめる工事は、まこさん 2026-10-02「Bはあとでやるので書いておいて」で後に回した。

## 開始時の「❌ 欠落」について

`verify_handoff_paths.sh` が引き継ぎのパスを確認します。2026-08-02 に、両方の場所を探す形へ直しました。見つかった場所を［直下］［sdk］で表示します。
