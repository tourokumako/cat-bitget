#!/usr/bin/env python3
"""gen_folder_map.py — 2つの .claude フォルダの地図（.claude/rules/README_folder_map.md）を、実物を数えて作る（2026-10-02・146回目）。

なぜ＝まこさん「.claud配下と bitget-python-sdk-api>.claude配下の違いもよくわからない。ディレクトリマップもぐちゃぐちゃだよね」
  → 私の案 A（地図を道具が実物から作る・ゴミを片づける）→ まこさん「Aをやる。Bはあとでやるので書いておいて」。
  前の地図は 2026-08-02 に手で書いたまま（「hook 59本・rules 3本」＝実物は hook 193個・rules 6本）で、作った日から古くなり続けていた。
何をするか
  --write  ＝実物を数えて地図を書き直す。古い設定の控え（settings*.json.bak*・作って1日 過ぎ）を消す
  --verify ＝①地図に載っているフォルダと文書の並びが実物と同じ ②役割の書いていないフォルダや文書が無い ③古い設定の控えが無い。
             どれか外れていれば exit 2（引き継ぎの Stop hook enforce_next_step_tidy.sh が呼ぶ＝外れたままターンを終われない）
★数（ファイルの数・大きさ）は毎ターン変わるので、--verify では照らさない（並びと役割だけ）。
★役割の文（ROLES）は手で書く所。新しいフォルダを作ったら、ここに1行 足す（足さないと --verify が止める）。
使い方: python3 .claude/tools/gen_folder_map.py --write | --verify
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import re
import time
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOP = ROOT / ".claude"
SDK = ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api" / ".claude"
BOT = SDK.parent                        # ★2026-11-03（ToDo の250番）＝sdk 直下と scripts も地図に載せる
MAP =TOP / "rules" / "README_folder_map.md"
HEAD_RE = re.compile(r"^<!-- FOLDER_MAP_GENERATED names=([0-9a-f]{16}) ")
BAK_MIN_AGE = 86400                     # 作って1日 以内の設定の控えは消さない（直している最中の物を壊さない）

ROLES = {
    "top": {
        "breaks/": "壊すプログラム（わざと壊して、検査が止まるかを試す）",
        "hooks/": "hook（ファイルを書く・コマンドを打つ・ターンを終える直前に自動で走り、通すか止めるかを決めるプログラム）",
        "rules/": "CC の動き方の決まり（毎セッション自動で読み込まれる）",
        "state/": "いまの状態（next_step・worklog・ToDo・設計書・承認の記録・調べの道具）",
        "tools/": "道具（文書を作る・検査する・片づける）",
        "settings.json": "Claude Code の設定（hook の登録）。git に入っている",
        "settings.local.json": "この PC だけの許可の設定",
        "archive_rules/": "使わなくなったルールの控え",
        "context/": "V9 の頃の資料（構造の地図・ファイル構成・リリース手順・テストの一覧）",
        "instructions/": "指示書",
        "templates/": "指示書のひな形",
        "ml_axis_catalog.md": "ML の決める値（23軸）の一覧（2026-05）",
        "pm_review_template.md": "PM の見直しのサブエージェントへの説明のひな形",
        "review_lens.md": "Web 版 Claude の見直しの視点（凍結・参照のみ）",
    },
    "sdk": {
        "audits/": "監査の依頼書・結果・作業のフォルダ",
        "memory/": "教訓（lessons_active・lessons_archive）・知識の文書（KB）",
        "ratchet/": "マイルストーン・やることリスト（m2_todo.json）・設計書の控え・決定（decisions.md）",
        "rules/": "BOT の中身の決まり（要件定義書 cat_requirements.md ほか）",
        "state": "直下の .claude/state への近道（シンボリックリンク）＝同じフォルダ",
        "auditor_template.md": "監査のサブエージェントへの説明のひな形",
    },
    # ★2026-11-03（ToDo の250番）＝中を開いて確かめて書いた。「消す候補」は、まこさんの OK の後に消す
    "bot": {
        "archive/": "古い資料の控え（regime_research・workflow）",
        "bitget/": "Bitget の公式 SDK。消す候補（246番）",
        "cat/": "V9 の指標の計算と定数（indicators.py・const.py）。変更禁止（core_rules.md）。engine_tuner の指標はここでなく scripts/priority_rebuild/indicators/",
        "config/": "V9 のパラメータと取引所の鍵。鍵の中身は出さない",
        "configs/": "ML の頃の設定（recipes.yaml ほか）",
        "dashboard/": "ブラウザで見る画面と、そのデータ（index.html・data）。大半は git に入っていない",
        "data/": "相場データ（5分足・1分足の CSV ほか）。大半は git に入っていない",
        "drafts/": "2026-04 の引き継ぎのメモ",
        "logs/": "V9 の頃の走行ログ。git に入っていない",
        "models/": "HMM の学習済みモデル（.pkl）。git に入っていない",
        "results/": "実験の結果（採点の CSV ほか）。大半は git に入っていない",
        "runner/": "V9 の本番の実行（run_once_v9.py）と検証のプログラム、Bitget の発注（bitget_adapter.py）。Bitget の部分は消す候補（246番）",
        "scripts/": "プログラム。中身は下の表",
        "state/": "V9 の本番の状態ファイル。run_once_v9.py 経由以外で変更しない（core_rules.md）",
        "strategies/": "V9 の入口の判断（cat_v9_decider.py）",
        "tools/": "V9 の頃の調べのプログラムと、足の取得のプログラム",
        "README.md": "Bitget SDK の説明。消す候補（246番）",
        "README_EN.md": "Bitget SDK の説明の英語版。消す候補（246番）",
        "WORKFLOW.md": "作業の決まりと監査の一覧。現在地は書かない（現在地は next_step.md）",
        "cc_ml_design_spec.md": "ML の頃の実装指示書（2026-05-13）",
        "engine_tuner_e38_S2.log": "engine_tuner の走行ログ（2026-08-19）。消す候補（tuner_writeback.py が名前を持つので確かめてから）",
        "example.py": "Bitget SDK の例（2025-12）。消す候補（246番）",
        "example_ws_contract.py": "Bitget SDK の例（2025-12）。消す候補（246番）",
        "requirements.txt": "Python の依存の一覧",
    },
    "scripts": {
        "dashboard/": "画面のデータを作るプログラム",
        "data/": "相場データを取得するプログラム",
        "grid_search/": "格子探索のプログラム1本（recipe_grid_search.py）",
        "hmm/": "HMM の研究のプログラム",
        "labels/": "日足の場面の正解ラベルを作るプログラム",
        "priority_rebuild/": "engine_tuner・E38・採点の本体。レベル1・3・4 のデータも、この下のフォルダに置く",
        "regime/": "場面の判定の研究のプログラム",
        "signal_research/": "シグナルの研究のプログラム",
    },
}


def entries(base: pathlib.Path) -> list[str]:
    out = []
    for p in sorted(base.iterdir()):
        # ★2026-10-17＝Claude Code 自身が作るファイル（scheduled_tasks.lock）も数えない。
        #   10月7日に「役割の書いていないもの」と数えて止め、CC がそのファイルを消して通した。
        if p.name.startswith(".") or p.name in ("__pycache__", "scheduled_tasks.lock"):
            continue
        if p.is_symlink():
            out.append(p.name)
        elif p.is_dir():
            out.append(p.name + "/")
        else:
            out.append(p.name)
    return out


def baks() -> list[pathlib.Path]:
    return sorted(TOP.glob("settings*.json.bak*"))


def names_hash(top: list[str], sdk: list[str], bot: list[str], scripts: list[str]) -> str:
    keep = [n for n in top if not re.search(r"\.bak", n)]
    return hashlib.sha256("\n--\n".join("\n".join(x) for x in (keep, sdk, bot, scripts)).encode()).hexdigest()[:16]


def count(p: pathlib.Path) -> tuple[int, int]:
    if p.is_symlink():
        return 0, 0
    if p.is_file():
        return 1, p.stat().st_size
    n = size = 0
    for dp, dns, fns in os.walk(p):
        dns[:] = [d for d in dns if d != "__pycache__"]
        for f in fns:
            fp = pathlib.Path(dp) / f
            if fp.is_symlink():
                continue
            n += 1
            size += fp.stat().st_size
    return n, size


def human(b: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024 or u == "GB":
            return f"{b:.0f}{u}" if u == "B" else f"{b:.1f}{u}"
        b /= 1024
    return f"{b:.1f}GB"


def table(base: pathlib.Path, names: list[str], roles: dict) -> list[str]:
    rows = ["| 名前 | 何が入っているか | ファイルの数 | 大きさ |", "|---|---|---|---|"]
    for nm in names:
        if re.search(r"\.bak", nm):
            continue
        n, s = count(base / nm.rstrip("/"))
        role = roles.get(nm, "★役割が書かれていない（gen_folder_map.py の ROLES に足す）")
        rows.append(f"| `{nm}` | {role} | {n:,} | {human(s) if n else '—'} |")
    return rows


def sdk_hooks() -> int:
    n = 0
    for p in sorted((TOP / "hooks").iterdir()):
        if p.suffix in (".sh", ".py") and "bitget-python-sdk-api/.claude" in p.read_text(encoding="utf-8", errors="replace"):
            n += 1
    return n


def render() -> str:
    top, sdk, bot, scripts = entries(TOP), entries(SDK), entries(BOT), entries(BOT / "scripts")
    today = date.today().isoformat()
    lines = [
        f"<!-- FOLDER_MAP_GENERATED names={names_hash(top, sdk, bot, scripts)} gen_folder_map.py が実物を数えて作った＝手で書き換えない -->",
        "# ディレクトリマップと置き場のルール（ファイルを探す前・作る前にここを見る）",
        "",
        "作成: 2026-08-02（まこさん「なんで似たようなフォルダが複数あるの？ 整理できない？」）。"
        f"**2026-10-02 から、この文書は `.claude/tools/gen_folder_map.py` が実物を数えて作る**（まこさん「Aをやる」）。数えた日＝{today}。",
        "",
        "## 結論：2つあり、役割が違います",
        "",
        "| 場所 | ひとことで |",
        "|---|---|",
        "| **直下の `.claude/`** | **Claude Code を動かす仕組み**（hook・道具・設定・いまの状態） |",
        "| **`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/`（sdk の方）** | **BOT プロジェクトの文書**（要件定義書・マイルストーン・監査・教訓） |",
        "",
        "## トレードBOT の情報のレベルごとの置き場（2026-11-03・まこさん「３，OK」）",
        "",
        "根のフォルダは `v3-bitget-api-sdk/bitget-python-sdk-api/` です。レベルの定義の正本は `.claude/rules/cat_requirements.md` の §1.2.2 です。",
        "",
        "| レベル | データと読むプログラム | 人が読む文書 |",
        "|---|---|---|",
        "| 1 BOT の運用ルール | `scripts/priority_rebuild/bot_rules/`（244番と242番で作る）。期間は `periods.py` のまま | `.claude/rules/cat_requirements.md`。取引所は `exchange_spec.md`（244番で GMOコインへ直す） |",
        "| 2 トレード戦略 | `.claude/ratchet/adopted_strategies.md`（台帳のまま） | 同じ台帳 |",
        "| 3 トレードロジックの組み方（法則） | `scripts/priority_rebuild/laws/`（209番で作り、195番で regime_laws.json を移す） | `.claude/rules/法則一覧.md`（209番で laws.json から作る）。出どころの資料は `.claude/memory/` の KB のまま |",
        "| 4 トレードロジックの材料（要素） | `scripts/priority_rebuild/indicators/` | `.claude/rules/要件定義書_レベル4_指標の構造.md`（正本）と `要件定義書_レベル4_指標の集約工事.md` |",
        "",
        "## 置き場のルール（恒久の決まり78番・79番が元。本文はそちらが正本）",
        "",
        "1. ファイルを作る前に、情報のレベルを決め、上の表で置き場を決めます。",
        "2. データと読むプログラムは、レベルごとのフォルダに置きます。人が読む文書は、sdk の `.claude/rules/` に置きます。",
        "3. 調べの途中の出力は、Claude Code の作業場に書きます。リポジトリの中に書きません。",
        "4. 同じ中身の写しと控えを作りません。控えが要るなら、git のコミットで残します。",
        "5. 新しいファイルやフォルダは、作る前に まこさんに伺います。作ったら、下の表の役割を `gen_folder_map.py` の ROLES に1行足します。足さないと `--verify` が止まります。",
        "6. 消す物と動かす物は、読む所と git を調べ、まこさんの OK を取ってから消します。下の表の「消す候補」も同じです。",
        "",
        "## sdk 直下（`v3-bitget-api-sdk/bitget-python-sdk-api/`）の中身",
        "",
        *table(BOT, bot, ROLES["bot"]),
        "",
        "## `scripts/` の中身",
        "",
        *table(BOT / "scripts", scripts, ROLES["scripts"]),
        "",
        "指標の工事に関わるファイルの詳しい一覧は、`.claude/rules/要件定義書_レベル4_指標の構造.md` の第3章の3 の「8 ディレクトリマップ」に在ります。",
        "",
        "## なぜ `.claude` が2つあるか",
        "",
        "Claude Code は、起動した場所の直下の `.claude/` しか設定として読みません。だから hook の登録と実体は、リポジトリ直下にしか置けません。"
        "sdk の方は、それより前からあるプロジェクトの資料置き場です。",
        "",
        "## 直下の `.claude/` の中身",
        "",
        *table(TOP, top, ROLES["top"]),
        "",
        "## sdk の `.claude/` の中身",
        "",
        *table(SDK, sdk, ROLES["sdk"]),
        "",
        "## 同じ名前のフォルダ（迷いやすい所）",
        "",
        "- **rules**＝直下は CC の動き方の決まり（毎回 自動で読まれる）／sdk は BOT の中身の決まり（要件定義書ほか）。",
        "- **state**＝1つだけ。sdk の `state` は直下の `.claude/state` を指す近道なので、どちらから開いても同じファイル。",
        "- **audits**＝sdk の方だけを使う（直下の `.claude/audits` は 2026-10-02 に sdk の `audits/cp29_work/` へ移した）。",
        "",
        "## 動かさない理由（★まとめる工事は「B」として next_step の「5 プロジェクトのやることの表」に在る）",
        "",
        f"sdk の方を名指ししている hook が **{sdk_hooks()}個** あります（数えた日 {today}）。"
        "文書を作る道具も、パスを埋め込んで作り、ハッシュ値で改変を見ています。動かすと hook が黙って効かなくなる危険があります。"
        "だから場所は変えず、この地図で迷わないようにしました（まこさん確定 2026-08-02・案B）。"
        "2つを1つにまとめる工事は、まこさん 2026-10-02「Bはあとでやるので書いておいて」で後に回した。",
        "",
        "## 開始時の「❌ 欠落」について",
        "",
        "`verify_handoff_paths.sh` が引き継ぎのパスを確認します。2026-08-02 に、両方の場所を探す形へ直しました。"
        "見つかった場所を［直下］［sdk］で表示します。",
        "",
    ]
    return "\n".join(lines)


def verify() -> list[str]:
    ng = []
    top, sdk, bot, scripts = entries(TOP), entries(SDK), entries(BOT), entries(BOT / "scripts")
    text = MAP.read_text(encoding="utf-8") if MAP.exists() else ""
    m = HEAD_RE.match(text)
    if not m:
        ng.append("地図に目印が無い（手で書いた古い地図のまま）→ `gen_folder_map.py --write`")
    elif m.group(1) != names_hash(top, sdk, bot, scripts):
        ng.append("地図のフォルダと文書の並びが実物と違う（足した・消した・名前を変えた）→ `gen_folder_map.py --write`")
    miss = [f"直下の {n}" for n in top if n not in ROLES["top"] and not re.search(r"\.bak", n)]
    miss += [f"sdk の {n}" for n in sdk if n not in ROLES["sdk"]]
    miss += [f"sdk 直下の {n}" for n in bot if n not in ROLES["bot"]]
    miss += [f"scripts の {n}" for n in scripts if n not in ROLES["scripts"]]
    if miss:
        ng.append(f"役割の書いていないものが {len(miss)} 個（{'・'.join(miss[:5])}）→ gen_folder_map.py の ROLES に1行 足す")
    old = [p for p in baks() if time.time() - p.stat().st_mtime >= BAK_MIN_AGE]
    if old:
        ng.append(f"古い設定の控えが {len(old)} 本（{old[0].name} ほか）→ `gen_folder_map.py --write` で消す（settings.json は git に入っている）")
    return ng


def main() -> int:
    ap = argparse.ArgumentParser(description="2つの .claude フォルダの地図を実物から作る")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.write:
        gone = [p for p in baks() if time.time() - p.stat().st_mtime >= BAK_MIN_AGE]
        for p in gone:
            p.unlink()
        MAP.write_text(render(), encoding="utf-8")
        print(f"[gen_folder_map --write] 地図を書いた（{MAP.relative_to(ROOT)}）／古い設定の控えを消した {len(gone)} 本")
    ng = verify()
    if ng:
        print(f"❌ [gen_folder_map --verify] {len(ng)} 件:")
        for x in ng:
            print(f"   ・{x}")
        return 2
    if a.verify or a.write:
        print("✅ [gen_folder_map --verify] 地図の並び・役割・古い控え の3つとも通った")
        return 0
    ap.error("--write か --verify を指定してください")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
