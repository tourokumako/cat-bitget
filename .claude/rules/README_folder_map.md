# .claude フォルダの地図 — なぜ2つあるか（探す前にここを見る）

作成: 2026-08-02。まこさんの指摘「なんで似たようなフォルダが複数あるの？ 整理できない？」で作りました。

## 結論：2つあり、役割が違います。名前が似ているだけで中身は別物です。

| 場所 | 何が入っているか | ひとことで言うと |
|---|---|---|
| **`cat-bitget/.claude/`（リポジトリ直下）** | hooks（59本）・settings.json・settings.local.json・state・tools・rules 3本 | **Claude Code という道具の設定** |
| **`cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/`（深い方）** | rules 10本・memory・ratchet・audits・instructions・templates（280ファイル） | **BOT プロジェクトの資料** |

## なぜ分かれているか

Claude Code は、起動した場所の直下の `.claude/` しか設定として読みません。だから hook の登録も実体も、リポジトリ直下にしか置けません。深い方は、それより前からあるプロジェクトの資料置き場です。

## どっちに何があるか（迷ったとき）

- **リポジトリ直下の rules 3本**＝`chat_writing_rules.md`（チャットの文章）／`experiment_result_procedure.md`（実験後の手順）／`pdca_flow.md`（hook の一覧）。**CC の動き方の決まりです。**
- **深い方の rules 10本**＝`cat_requirements.md`（要件定義書）／`cc_role.md`／`exchange_spec.md`／`false_positive_incident_policy.md` ほか。**BOT の中身の決まりです。**
- **state（next_step.md・worklog）は1つです。** 深い方の `state` はリポジトリ直下へのシンボリックリンクなので、どちらの道から開いても同じファイルです。

## 動かさない理由

深い方を参照している hook が11本あります（enforce_e37_pdca・require_read_before_work・pdca_gate ほか）。機械生成の文書もパスを埋め込んで作られ、ハッシュで改変を検出します。動かすと hook が黙って効かなくなる危険があります。**だから場所は変えず、この地図で迷わないようにしました**（まこさん確定 2026-08-02・案B）。

## 開始時の「❌ 欠落」について

`verify_handoff_paths.sh` が引き継ぎのパスを確認します。**2026-08-02 に、両方の場所を探す形へ直しました。** 見つかった場所を［直下］［sdk］で表示します。それ以前は深い方しか見ておらず、直下のファイルを毎回「❌ 欠落」と誤報していました。この検査は毎回、自分自身を既知答え3件で自己検査します（番人が落ちたら大きく警告が出ます）。
