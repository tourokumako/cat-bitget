#!/usr/bin/env python3
"""gen_decisions.py — まこさんが決めたことの一覧を機械生成する（手書き禁止・2026-07-26 まこさん OK）

なぜ作るか
--------------------------------------------------------------------------
2026-07-26、CC が「保有の上限4時間」を判断材料として持ち出した。これはまこさんが以前に
「スキャルと不整合」と決着させ、設定ファイルからも撤去済みの話だった。CC はその決定を探しに
行かなかった。記録が無かったのではない。**決定が正本のあちこちに散らばっていて、作業を
始めるときに目に入る1枚が無かった**。

同じ日、理解確認テスト（質問形式の hook）はこの失敗を防げないことが実測で分かった
（CC はセッション冒頭でテストに回答したうえで蒸し返した）。そこで hook を無効化し、
代わりに「決定の一覧を機械で集めて、始めるときに目に入れる」形にした。

何を材料にするか（すべて実体から取る・CC が自由記述する箇所を作らない）
--------------------------------------------------------------------------
正本ファイルの中に、まこさんの決定はすでに印つきで書かれている（「まこさん確定 2026-07-25」等）。
その印と日付を機械で拾うだけ＝CC が一覧を手で書かない（手で書くと書き漏らしと古さが必ず出る）。

  ・.claude/ratchet/e38_flow.md          フローの正本（段の確定事項）
  ・.claude/ratchet/adopted_strategies.md 台帳（採用・役割・目標）
  ・.claude/state/next_step.md            次セッションの起点
  ・scripts/priority_rebuild/e38_logics.json    ロジック定義（値の確定）
  ・scripts/priority_rebuild/observe_config.json 観察の設定（刻みの確定）
  ・.claude/state/session_worklog_*.md    直近 WORKLOG_KEEP 本（その日の決定）

使い方
--------------------------------------------------------------------------
  python3 gen_decisions.py --write     # 生成して .claude/ratchet/decisions.md に書く
  python3 gen_decisions.py --verify    # 手書き改変の検出（ハッシュ照合）
  python3 gen_decisions.py --selftest  # 自己検査（材料が実体から取れているかの番人）

限界（正直に）
--------------------------------------------------------------------------
  ・**印が書かれていない決定は載らない**。機械は印を探しているだけ。印を書き忘れたら漏れる。
  ・**チャットでの発言は止められない**。hook はファイルとコマンドしか見られない。
    この一覧ができることは「始めるときに目に入れる」ところまで。
  ・1行を機械で切り出すので、長い決定は前後が切れることがある。出どころの行番号から原文を開く。
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent                      # bitget-python-sdk-api
OUT = ROOT / ".claude" / "ratchet" / "decisions.md"

WORKLOG_KEEP = 5                               # worklog は直近5本（まこさん確定 2026-07-26）
MARK = re.compile(r"まこさん\s?(確定|決定|承認|指示|採用|OK)")
DATE = re.compile(r"(20\d\d)[-/](\d\d)[-/](\d\d)")
MAXLEN = 180                                   # 1行の切り出しの上限（長い決定は原文を開く）

# 決定が書き込まれる正本（worklog は別途 直近 WORKLOG_KEEP 本を足す）
SOURCES = [
    ROOT / ".claude" / "ratchet" / "e38_flow.md",
    ROOT / ".claude" / "ratchet" / "adopted_strategies.md",
    ROOT / ".claude" / "state" / "next_step.md",
    HERE / "e38_logics.json",
    HERE / "observe_config.json",
]


def _worklogs() -> list[pathlib.Path]:
    """worklog は直近 WORKLOG_KEEP 本だけ（全部だと 142 件で読めない・まこさん確定 2026-07-26）。"""
    got = sorted((ROOT / ".claude" / "state").glob("session_worklog_*.md"), reverse=True)
    return got[:WORKLOG_KEEP]


def _clean(s: str, at: int = 0) -> str:
    """行から飾りを落として1文にする（表・箇条書き・JSON の記号を外す）。

    at＝印（まこさん確定 等）が行のどこに出たか。長い行は**印の少し手前から**切り出す。
    行頭から切ると、前置きの説明で 180 字を使い切って肝心の決定が落ちる（2026-07-26 実測＝
    observe_config.json の場面定義の注記で「全部60分に揃える」が切れた）。"""
    if at > 60:                                 # 前置きが長い行だけ、印の手前から取る
        s = "…" + s[at - 40:]
    s = s.strip()
    s = re.sub(r"^[\s>#*\-|]+", "", s)          # 見出し・箇条書き・表の頭
    s = re.sub(r'^"[^"]*"\s*:\s*"?', "", s)     # JSON のキー
    s = s.replace("**", "").replace("`", "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.rstrip('",')
    return s[:MAXLEN] + ("…" if len(s) > MAXLEN else "")


def _day_of(path: pathlib.Path, line: str) -> str:
    """決定の日付。行の中の日付を優先し、無ければ worklog のファイル名の日付を使う。"""
    m = DATE.search(line)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"session_worklog_(20\d\d)(\d\d)(\d\d)", path.name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return "日付なし"


def collect() -> list[dict]:
    """印のある行を集めて、日付の新しい順に並べる（重複は落とす）。"""
    rows, seen = [], set()
    for p in SOURCES + _worklogs():
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m0 = MARK.search(line)
            if not m0:
                continue
            txt = _clean(line, m0.start())
            if len(txt) < 8:                    # 印だけで中身の無い行は落とす
                continue
            key = re.sub(r"[\s・。、]", "", txt)[:90]
            if key in seen:
                continue
            seen.add(key)
            rows.append({"day": _day_of(p, line), "text": txt,
                         "src": f"{p.name}:{i}", "kind": m0.group(1)})
    # 新しい順。日付が拾えなかった行は最後へ（先頭は必ず直近の決定にする）
    rows.sort(key=lambda r: (r["day"] != "日付なし", r["day"], r["src"]), reverse=True)
    return rows


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def build() -> str:
    rows = collect()
    L = []
    L.append("# まこさんが決めたこと（gen_decisions.py が自動生成＝手書き禁止）")
    L.append("")
    L.append("⚠️ このファイルを手で書き換えないでください。中身は正本ファイルから機械で集めています。")
    L.append("   決定を足すには、正本の側に「まこさん確定 2026-MM-DD ...」のように印つきで書いてから")
    L.append("   下のコマンドで作り直します。改変の検出も同じコマンドです。")
    L.append("")
    L.append("```")
    L.append("python3 scripts/priority_rebuild/gen_decisions.py --write")
    L.append("python3 scripts/priority_rebuild/gen_decisions.py --verify")
    L.append("```")
    L.append("")
    L.append("## この一覧は何のためにあるか")
    L.append("")
    L.append("**過去にまこさんが決めたことを、CC が確認せずに蒸し返すのを防ぐため**です。")
    L.append("2026-07-26、CC が「保有の上限4時間」を持ち出しました。まこさんが以前に決着させ、")
    L.append("設定からも撤去済みの話でした。記録は在ったのに、始めるときに目に入る1枚が無かったのが原因です。")
    L.append("")
    L.append("**使い方＝提案を出す前に、この一覧と突き合わせる。**")
    L.append("")
    L.append("## 限界（正直に）")
    L.append("")
    L.append("- **印が書かれていない決定は載りません。** 機械は印を探しているだけです。")
    L.append("- **チャットでの発言は止められません。** できるのは目に入れるところまでです。")
    L.append("- 1行を機械で切り出すので、長い決定は前後が切れます。出どころから原文を開いてください。")
    L.append("")
    L.append(f"## 集めた先（{len(SOURCES)} 本の正本 ＋ 直近 {WORKLOG_KEEP} 本の worklog）")
    L.append("")
    for p in SOURCES + _worklogs():
        L.append(f"- {p.name}{'' if p.exists() else '（無い）'}")
    L.append("")
    L.append(f"## 決定の一覧（{len(rows)} 件・新しい順）")
    L.append("")
    L.append("| 日付 | 印 | 決めたこと | 出どころ |")
    L.append("|---|---|---|---|")
    for r in rows:
        txt = r["text"].replace("|", "／")
        L.append(f"| {r['day']} | {r['kind']} | {txt} | {r['src']} |")
    L.append("")
    body = "\n".join(L) + "\n"
    return f"<!-- DECISIONS_HASH={_sha(body)} -->\n{body}"


def verify() -> int:
    if not OUT.exists():
        print(f"❌ 決定の一覧が無い: {OUT}"); return 1
    txt = OUT.read_text(encoding="utf-8")
    head, _, body = txt.partition("\n")
    want = head.replace("<!-- DECISIONS_HASH=", "").replace(" -->", "").strip()
    got = _sha(body)
    if want != got:
        print(f"❌ 手書きで書き換えられている（ハッシュ不一致 期待 {want} / 実際 {got}）"); return 1
    print(f"✅ 改変なし（ハッシュ {got}）"); return 0


def selftest() -> int:
    ng = []
    rows = collect()
    if not rows:
        ng.append("決定を1件も拾えていない（印の探し方が壊れている）")
    # ① 材料を実体から取っている＝正本を足したら一覧も変わる（番人＝一時ファイルで確かめる）
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        probe = pathlib.Path(td) / "probe_source.md"
        probe.write_text("まこさん確定 2026-01-02 これは番人用のダミーの決定です。\n", encoding="utf-8")
        SOURCES.append(probe)
        try:
            if "番人用のダミーの決定" not in build():
                ng.append("正本を足しても一覧が変わらない（実体から取っていない）")
        finally:
            SOURCES.remove(probe)
    # ② worklog は直近 WORKLOG_KEEP 本だけ（全部読むと 142 件で読めない）
    if len(_worklogs()) > WORKLOG_KEEP:
        ng.append(f"worklog を {len(_worklogs())} 本読んでいる（上限 {WORKLOG_KEEP} 本）")
    # ③ 出どころ（ファイル名と行番号）が全行に付いている＝原文に戻れる
    for r in rows:
        if not re.match(r"^[\w.\-]+:\d+$", r["src"]):
            ng.append(f"出どころの形が壊れている: {r['src']}"); break
    # ④ 日付の形が揃っている
    for r in rows:
        if r["day"] != "日付なし" and not re.match(r"^20\d\d-\d\d-\d\d$", r["day"]):
            ng.append(f"日付の形が壊れている: {r['day']}"); break
    # ⑤ ハッシュが本文と一致する（--verify が意味を持つ）
    txt = build()
    head, _, body = txt.partition("\n")
    if head.replace("<!-- DECISIONS_HASH=", "").replace(" -->", "").strip() != _sha(body):
        ng.append("ハッシュが本文と一致しない（改変検出が効かない）")
    print("=" * 80)
    print("gen_decisions 自己検査")
    print("=" * 80)
    print(f"  集めた先 {len(SOURCES)} 本の正本 ＋ worklog {len(_worklogs())} 本")
    print(f"  拾った決定 {len(rows)} 件 / 出力先 {OUT}")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="まこさんが決めたことの一覧を機械生成する")
    ap.add_argument("--write", action="store_true", help="生成して書き出す")
    ap.add_argument("--verify", action="store_true", help="手書き改変の検出")
    ap.add_argument("--selftest", action="store_true", help="自己検査")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.verify:
        sys.exit(verify())
    txt = build()
    if a.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(txt, encoding="utf-8")
        print(f"✅ 書き出した: {OUT}（{len(txt.splitlines())}行）")
    else:
        print(txt)


if __name__ == "__main__":
    main()
