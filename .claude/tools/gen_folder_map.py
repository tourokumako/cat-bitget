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
MAP = TOP / "rules" / "README_folder_map.md"
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
    },
    "sdk": {
        "archive_rules/": "使わなくなったルールの控え",
        "audits/": "監査の依頼書・結果・作業のフォルダ",
        "context/": "V9 の頃の資料（構造の地図・ファイル構成・リリース手順・テストの一覧）",
        "instructions/": "指示書",
        "memory/": "教訓（lessons_active・lessons_archive）・知識の文書（KB）",
        "ratchet/": "マイルストーン・やることリスト（m2_todo.json）・設計書の控え・決定（decisions.md）",
        "rules/": "BOT の中身の決まり（要件定義書 cat_requirements.md ほか）",
        "state": "直下の .claude/state への近道（シンボリックリンク）＝同じフォルダ",
        "templates/": "指示書のひな形",
        "auditor_template.md": "監査のサブエージェントへの説明のひな形",
        "ml_axis_catalog.md": "ML の決める値（23軸）の一覧（2026-05）",
        "pm_review_template.md": "PM の見直しのサブエージェントへの説明のひな形",
        "review_lens.md": "Web 版 Claude の見直しの視点（凍結・参照のみ）",
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


def names_hash(top: list[str], sdk: list[str]) -> str:
    keep = [n for n in top if not re.search(r"\.bak", n)]
    return hashlib.sha256(("\n".join(keep) + "\n--\n" + "\n".join(sdk)).encode()).hexdigest()[:16]


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
    top, sdk = entries(TOP), entries(SDK)
    today = date.today().isoformat()
    lines = [
        f"<!-- FOLDER_MAP_GENERATED names={names_hash(top, sdk)} gen_folder_map.py が実物を数えて作った＝手で書き換えない -->",
        "# .claude フォルダの地図 — なぜ2つあるか（探す前にここを見る）",
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
        "## なぜ分かれているか",
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
    top, sdk = entries(TOP), entries(SDK)
    text = MAP.read_text(encoding="utf-8") if MAP.exists() else ""
    m = HEAD_RE.match(text)
    if not m:
        ng.append("地図に目印が無い（手で書いた古い地図のまま）→ `gen_folder_map.py --write`")
    elif m.group(1) != names_hash(top, sdk):
        ng.append("地図のフォルダと文書の並びが実物と違う（足した・消した・名前を変えた）→ `gen_folder_map.py --write`")
    miss = [f"直下の {n}" for n in top if n not in ROLES["top"] and not re.search(r"\.bak", n)]
    miss += [f"sdk の {n}" for n in sdk if n not in ROLES["sdk"]]
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
