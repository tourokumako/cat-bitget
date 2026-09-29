#!/usr/bin/env python3
"""gen_acceptance.py — engine_tuner の設計書を、元データと正本から組み立てる。

なぜ作ったか
------------
まこさん指示（2026-09-09・逐語）＝「ヌケモレがおおいから、手で書かざるを得ない部分以外は
自動生成にしろよ。。。。なんで最低限守って。虚偽、ヌケモレ、不正予防のために自動生成にしろって
言ってだけど。なんでできない」「この自動生成の件、毎回言ってるんだけど。いい加減覚えろよ」
「手書きはするな」。

何が起きていたか（実測 2026-09-09）
  M2-E-2 の設計書 577行のうち、プログラムが作ったのは SPEC の囲みだけだった。
  残りは手書き。その結果、
    ①関数の行番号を手で写した（verify_design_contract.py --write が毎回
      「行番号を手で写さない・93番」と画面に出しているのに）
    ②法則の一覧を手で並べ、21件のうち2件（R11・C8）を落とした
    ③まこさんが決めた探す候補（§2.2）を12件 切り、「入りません」と書いた
  どれも、正本から作れば起きない。

何をするか
----------
  --write        元データ（acceptance_src.json）と正本から設計書を組み立て、囲みの中に書く
  --verify       囲みの中が、機械の書いたままかを検出する（手で書き換えたら ❌）
  --dry-run      書かずに、組み立てた本文を画面に出す
  --selftest     わざと壊して ❌ が出るかを試す（8件）

★手で書くのは元データの5つだけ＝何を作るか／なぜ作るか／組み方／やらないこと／決めてほしいこと。
★行番号・一覧・件数・格子と範囲・SPEC は、この道具が正本から出す（元データに書かない）。
★2026-09-29（まこさん指示「やることリストなどの設計のもとになるものから設計書作成を自動生成」）
  ＝設計のもと（元データの「設計のもと」＝やることの番号と逐語のファイル）を、この道具が設計書 §0-1 に写す。
    やることの行は m2_todo.json から、まこさんの文は gen_verbatim.py の逐語のファイルから読む（CC は写さない）。
  ＝写した1行ずつに「設計書のどの節・実装の指示の何番で満たすか」（元データの「対応の表」）が無ければ書かない。
  ＝元データに「まこさんの決定」の欄が在れば止める（CC が手で書く口は閉じた・OK をもらった提案の7行目）。
★節の形＝まこさん決定 2026-09-09（恒久の決まり70番）＝7つの節。

fail-closed（黙って通さない・4つ）
  1. 正本のファイルが読めない → 止まる
  2. 元データの「やらないこと」が空 → 止まる（私が候補を切って何も書かない、を防ぐ）
  3. 置き換えられない目印が本文に残った → 止まる
  4. 法則ファイルの件数と、書き出した件数が違う → 止まる（法則を落として並べる、を防ぐ）

限界（正直に）
  ・元データの文の中で範囲を狭めることは、この道具では止められない（まこさんの目と監査）。
  ・囲みの外（節の見出しなど）を手で書き換えても、--verify は止めない。
  ・この道具自身を書き換えれば無効にできる（git の差分には出る）。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
RATCHET = SDK / ".claude" / "ratchet"
STATE = ROOT / ".claude" / "state"
PRIORITY = SDK / "scripts" / "priority_rebuild"
TODO = RATCHET / "m2_todo.json"                     # ★2026-09-29＝設計のもと（やることリスト）

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_verbatim as gv                           # noqa: E402  ★2026-09-29＝まこさんの文の逐語のファイル


def touches_trading(d: dict) -> bool:
    """この工事が売買のロジック（scripts/priority_rebuild・engine_tuner）に触るか。TARGET と NEW_FILE で見る。

    ★2026-09-29（まこさん指摘「監査の依頼内容が変じゃないか？」・worklog 20260929 §40〜§42）
      ＝直す前は、道具の直しの設計書でも 2-2 探す材料・2-3 成績表・2-4 乱数・7-3b（engine_tuner の要件）を必ず出し、
        依頼書にも engine_tuner の前提と大目的を出していた。工事の相手を見て出し分ける。
    """
    ps = [str(p) for p in (d.get("TARGET") or []) + (d.get("NEW_FILE") or [])]
    return any("scripts/priority_rebuild" in p or "engine_tuner" in p for p in ps)


NONTRADE = ("**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い"
            "（プログラムが TARGET と NEW_FILE から決めました）。")


def forbidden_items():
    """要件の正本から「作ってはいけないもの」の一覧を取り出す（★手で写さない＝恒久の決まり69番）。

    戻り＝[(番号, 名前), ...]。出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。
    ★なぜ要るか（2026-09-10・96回目）＝恒久の決まり §1 が「着手の前に、作ろうとしているものが
      その一覧に当たらないかを1件ずつ照合して、結果をチャットに出します」と求めている。
      それまでの設計書には、この照合を書く場所が1つも無かった。
    ★一覧が増えたら、この表も自動で増える（照合を書かないと --write が止まる＝fail-closed）。
    """
    p = RATCHET / "engine_tuner_requirements.json"
    body = json.loads(p.read_text(encoding="utf-8"))
    tbl = []

    def walk(x):
        if isinstance(x, str):
            if "| # | 作ってはいけないもの |" in x:
                tbl.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(body)
    if not tbl:
        raise SystemExit("[gen_acceptance] 要件の正本に「作ってはいけないもの」の表が無い（fail-closed）")
    out = []
    for ln in tbl[0].split("\n"):
        m = re.match(r"^\|\s*(\d+)\s*\|\s*\*\*(.+?)\*\*\s*\|", ln.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    if not out:
        raise SystemExit("[gen_acceptance] 「作ってはいけないもの」を1件も取り出せなかった（fail-closed）")
    return out

SRC = RATCHET / "acceptance_src.json"
# ★2026-09-10＝§4（設計の中身）の項目の正本。
#   3つの出どころ（うちの正本・外の標準・まこさんが過去に指摘したこと）118件を
#   全部 引き受ける形に割り当てたもの（gen_design_sections.py --check で検算する）。
#   ★項目をここ以外に書かない（2か所に書くと片方だけ直って食い違う）。
MAP = RATCHET / "design_section_map.json"
DEST = STATE / "acceptance.md"

# ── 正本（この道具が読む相手・手で写さない）─────────────────────────
SWITCH = RATCHET / "indicator_switch.json"
LAWS = RATCHET / "regime_laws.json"
FAMILIES = RATCHET / "signal_families.json"
RANKING = RATCHET / "material_ranking.json"
LIMITS = PRIORITY / "recipes" / "search_limits.json"
GEN_PY = PRIORITY / "engine_tuner_gen.py"
EXEC_PY = PRIORITY / "engine_tuner_exec.py"

# ── 囲み（9つ）───────────────────────────────────────────────
BLOCKS = ("STAGES", "MATERIALS", "LAWS", "RANKING", "CODEREF", "RANDOM",
          "ACCEPT_TABLE", "SELFTEST", "SPEC", "CHECKLIST", "AUDITTODO",
          # ★2026-09-24（設計書 impl-instruction-apply-20260924）＝設計書の「4-20 実装の指示」の囲み
          #   （元データの `実装の指示` が空なら出ない＝AUDITTODO と同じ形）
          "IMPL",
          # ★2026-09-29＝設計書 §0-1 の設計のもと（やることの行・逐語の行・対応の表）の囲み（いつも出る）
          "SOURCE")


def _begin(kind: str, h: str) -> str:
    if kind == "ACCEPT_TABLE":                       # ★承認ゲートが読む目印（形を変えない）
        return "<!-- ACCEPT_TABLE_START -->"
    return f"<!-- ACC_{kind}_START hash={h} gen_acceptance.py が自動生成＝手で書き換えない -->"


def _begin_re(kind: str) -> re.Pattern:
    if kind == "ACCEPT_TABLE":
        return re.compile(r"<!-- ACCEPT_TABLE_START -->")
    return re.compile(rf"<!-- ACC_{kind}_START hash=([0-9a-f]{{16}}).*?-->")


def _end(kind: str) -> str:
    if kind == "ACCEPT_TABLE":
        return "<!-- ACCEPT_TABLE_END -->"
    return f"<!-- ACC_{kind}_END -->"


def _h(body: str) -> str:
    """本文のハッシュ値（先頭16文字）。

    ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §4-1 の1）
      ＝数える前に、必ず末尾の改行を落とす。
      直す前＝書くときは本文の後ろに改行が付き、読むときは verify が rstrip("\\n") で
      落としていた。同じ中身でもハッシュ値が食い違い、T1 が落ちていた。
      ★数える場所を1か所（この関数）にまとめるのが直しの本体。
    """
    return hashlib.sha256(body.rstrip("\n").encode("utf-8")).hexdigest()[:16]


def _esc(s) -> str:
    """表のセルに入れるとき、| を壊さないようにする。"""
    return str(s).replace("|", "／").replace("\n", " ")


def _load(path: Path) -> dict:
    """正本を読む。読めなければ止まる（fail-closed の1つ目）。"""
    if not path.exists():
        raise SystemExit(f"[gen_acceptance] 正本が無い: {path}（fail-closed）")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] 正本が読めない: {path}（{e}）")


def src() -> dict:
    """元データを読む。「やらないこと」が空なら止まる（fail-closed の2つ目）。"""
    d = _load(SRC)
    if not d.get("やらないこと"):
        raise SystemExit(
            "[gen_acceptance] 元データの「やらないこと」が空です（fail-closed）。\n"
            "  ★探す候補を切ったのに理由を書かない、を防ぐための検査です。\n"
            "  切るものが無いなら、その旨を1行 書いてください。")
    return d


# ══ 囲みの中身を作る（正本から）══════════════════════════════════════

def build_materials(d: dict) -> str:
    """探す材料の一覧＝印がオンの指標・役割ごとの系統・時間足・範囲・格子。"""
    if not touches_trading(d):
        return NONTRADE
    sw = _load(SWITCH)
    fam = _load(FAMILIES)
    lim = _load(LIMITS)
    on = sw.get("on") or []
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        f"出どころ＝`{SWITCH.name}`・`{FAMILIES.name}`・`{LIMITS.name}`。")
    add("")
    add(f"**探す指標＝印がオンの {len(on)}種**（印を切り替えると、この一覧も設計も変わります）。")
    add("")
    add("```")
    add("・".join(str(x) for x in on))
    add("```")
    add("")
    add("**別枠の材料**")
    add("")
    add("| 別枠 | 印がオンのもの |")
    add("|---|---|")
    for key, name in (("geo_on", "レンジ幾何"), ("demand_on", "需給"), ("time_on", "時間帯")):
        add(f"| {name} | {_esc('・'.join(str(x) for x in (sw.get(key) or [])))} |")
    add("")
    roles = ((fam.get("role_lineage") or {}).get("roles") or {})
    add("**役割ごとに使える系統と時間足（型の表）**")
    add("")
    add("| 役割 | 系統 | 時間足 | レンジ幾何 |")
    add("|---|---|---|---|")
    for r, v in roles.items():
        tfs = v.get("tfs")
        tfs_s = "全部" if tfs == "all" else _esc("・".join(tfs or []))
        add(f"| {r} | {_esc('・'.join(v.get('lineages') or []))} | {tfs_s} "
            f"| {'使う' if v.get('geo') else '—'} |")
    add("")
    add("**値の範囲と格子（承認済み・この工事で数字を1つも作らない）**")
    add("")
    add("| 鍵 | 中身 |")
    add("|---|---|")
    for k in ("quantile_grid", "quantile_range", "int_grid", "int_range",
              "state_hold_bars_range", "nest_offset_range", "ref_mult_range",
              "hour_range", "material_param_ranges"):
        if k in lim:
            v = lim[k]
            s = "（空＝材料カタログの最小〜最大を使う）" if v == {} else _esc(json.dumps(v, ensure_ascii=False))
            add(f"| `{k}` | {s} |")
    add("")
    return "\n".join(L)


def build_laws(d: dict) -> str:
    """場面の法則の一覧＝全件（1件も落とさない・fail-closed の4つ目で数を照らす）。"""
    law = _load(LAWS)
    rows = [x for x in (law.get("法則") or []) if isinstance(x, dict)]
    L = []
    add = L.append
    add(f"**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`{LAWS.name}`。")
    add("")
    add(f"**相場の法則は全部で {len(rows)}件**です（場面ごと）。"
        "この表は1件も落としません（落とすと `--write` が止まります）。")
    add("")
    add("| 番号 | 場面 | 一文 | 機械が読む判定 | 掛かる場面 | 根拠 |")
    add("|---|---|---|---|---|---|")
    for r in rows:
        j = r.get("機械が読む判定")
        if isinstance(j, dict):
            typ = j.get("型", "")
            sel = j.get("数える部品")
            detail = ""
            if isinstance(sel, dict):
                parts = []
                for k in ("系統", "family", "geo", "性質", "時間足", "かつ", "側", "向きを持つ"):
                    if k in sel:
                        v = sel[k]
                        parts.append(f"{k}＝{_esc(json.dumps(v, ensure_ascii=False)) if isinstance(v, (dict, list)) else _esc(v)}")
                detail = "／".join(parts) + f"／本数 {j.get('本数', '')}"
            elif typ == "形を持つ":
                detail = f"形＝{j.get('形', '')}"
            elif typ == "系統を重ねない":
                detail = f"除く系統＝{_esc('・'.join(j.get('除く系統') or []))}／上限 {j.get('上限', '')}"
            jt = f"**{typ}**（{detail}）"
            scenes = _esc("・".join(j.get("掛かる場面") or []))
        elif r.get("判定の置き場"):
            jt = f"—（判定の置き場＝{_esc(r['判定の置き場'])}）"
            scenes = "—"
        else:
            jt = "—"
            scenes = "—"
        kyo = f"{len(r['根拠'])}件" if isinstance(r.get("根拠"), list) else "—"
        add(f"| **{_esc(r.get('番号'))}** | {_esc(r.get('場面'))} | {_esc(r.get('一文'))} "
            f"| {jt} | {scenes} | {kyo} |")
    add("")
    with_j = [x for x in rows if isinstance(x.get("機械が読む判定"), dict)]
    add(f"**内訳（プログラムが数えました）**＝機械が読む判定を持つもの **{len(with_j)}件** ／ "
        f"持たないもの **{len(rows) - len(with_j)}件**。")
    add("")
    return "\n".join(L)


def build_ranking(d: dict) -> str:
    """成績表に載っている本数＝役割 × 上位足（印の絞りを通した後）。"""
    if not touches_trading(d):
        return NONTRADE
    rk = _load(RANKING)
    order = (rk.get("順位") or {})
    up = ("10m", "15m", "30m", "1h", "2h", "4h", "6h", "1d")
    L = []
    add = L.append
    add(f"**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`{RANKING.name}`。")
    add("")
    add("**成績表に載っている列の本数**（札＝強さ・先読み24・執行足より上の時間足だけ）")
    add("")
    add("| 役割 | 上位足の列の本数 | 分離力の高い順に3本 |")
    add("|---|---|---|")
    for role in sorted(order):
        rows = ((order.get(role) or {}).get("強さ") or {}).get("24") or []
        hit = [(c, a) for c, a in rows if isinstance(c, str) and c.rsplit("__", 1)[-1] in up]
        top = sorted(hit, key=lambda x: -abs(float(x[1]) - 0.5))[:3]
        add(f"| {role} | {len(hit)} | {_esc('／'.join(f'{c}（{a}）' for c, a in top))} |")
    add("")
    add("**★この本数は、印がオンの指標だけを数えたものではありません。**"
        "組む側は `ranked_materials` を通して引き、その関数が印オフの指標を落とします。")
    add("")
    return "\n".join(L)


def build_coderef(d: dict) -> str:
    """触る関数の名前と定義の行（★手で写さない・93番）。"""
    sys.path.insert(0, str(PRIORITY))
    try:
        from verify_design_contract import spec_from_impl
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] 照合の道具を読み込めない: {e}（fail-closed）")
    impl = str(((d.get("DESIGN_CONTRACT") or {}).get("impl_file")) or "")
    path = SDK / impl if impl else GEN_PY
    if not path.exists():
        raise SystemExit(f"[gen_acceptance] 直す相手が無い: {path}（fail-closed）")
    spec = spec_from_impl(str(path))
    names = [str(x) for x in ((d.get("DESIGN_CONTRACT") or {}).get("self_check_calls") or [])]
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`"
        "（★行番号を手で写さない・93番）。")
    add("")
    add(f"**直す相手**＝`{impl or GEN_PY.name}`")
    add("")
    add("| 触る関数 | 定義の行 |")
    add("|---|---|")
    dl = spec.get("def_lines") or {}
    for n in names:
        add(f"| `{n}` | {dl.get(n, '（この関数は実物に無い）')} |")
    add("")
    add(f"**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で {len(dl)}件の関数が在ります）。")
    add("")
    return "\n".join(L)


def build_random(d: dict) -> str:
    """乱数を使っている場所（構文の木で数える・文字を探さない）。"""
    if not touches_trading(d):
        return NONTRADE
    if not GEN_PY.exists():
        raise SystemExit(f"[gen_acceptance] 実物が無い: {GEN_PY}（fail-closed）")
    text = GEN_PY.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(text)
    hits: dict[str, int] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        n = 0
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "rng":
                n += 1
            elif isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in ("draw_param", "draw_q", "draw_int", "draw_num"):
                n += 1
        if n:
            hits[node.name] = n
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        f"出どころ＝`{GEN_PY.name}` を構文の木で読んだ結果（コメントの中の文字は数えません）。")
    add("")
    add(f"**乱数を使っている関数＝{len(hits)}個 ／ 使っている回数の合計＝{sum(hits.values())}**")
    add("")
    add("| 関数 | 回数 |")
    add("|---|---|")
    for n, c in sorted(hits.items(), key=lambda x: (-x[1], x[0])):
        add(f"| `{n}` | {c} |")
    add("")
    # ★2026-09-29＝「この工事で0にするのは、場面の判定の束を組む所だけです」の固定の文を消した
    #   （どの工事でも同じ文が出て、工事と食い違った＝worklog 20260929 §40 の2）。何を0にするかは設計の中身に書く。
    add("**★乱数を外すのは、入口は M3、出口は M4 です（まこさんが決めた順番）。**"
        "この工事で外すかどうかは、設計の中身（4-0・4-20）に書きます。")
    add("")
    return "\n".join(L)


def build_accept_table(d: dict) -> str:
    """完成の条件の表（承認ゲートが読む欄で作る）。"""
    rows = d.get("完成の条件") or []
    if not rows:
        raise SystemExit("[gen_acceptance] 元データに「完成の条件」がありません（fail-closed）")
    L = []
    add = L.append
    add("")
    add("| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |")
    add("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        add(f"| {i} | {_esc(r.get('条件'))} | `{_esc(r.get('コマンド'))}` | {_esc(r.get('経路'))} "
            f"| {_esc(r.get('壊し方'))} | `{_esc(r.get('壊すプログラム'))}` | {_esc(r.get('監査確認'))} "
            f"| **{_esc(r.get('いまの状態'))}** |")
    add("")
    return "\n".join(L)


def build_selftest(d: dict) -> str:
    """わざと壊して止まるか試すテストの一覧（壊すプログラムと守る行の対応）。"""
    rows = d.get("完成の条件") or []
    # ★2026-09-29＝壊すプログラムと壊し方の組で まとめる（直す前は壊すプログラムだけで まとめ、「—」の行の
    #   壊し方を1つ目の行の文で代表させた＝#4・#5 に #3 の壊し方が付いた・worklog 20260929 §49 の5）
    by: dict[tuple, list[int]] = {}
    for i, r in enumerate(rows, 1):
        by.setdefault((str(r.get("壊すプログラム") or ""), str(r.get("壊し方") or "")), []).append(i)
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝元データの「完成の条件」。")
    add("")
    add("| 壊すプログラム | 守る行 | 壊し方 |")
    add("|---|---|---|")
    for (prog, brk), idx in sorted(by.items(), key=lambda x: x[1][0]):
        add(f"| `{_esc(prog)}` | {_esc('・'.join('#' + str(i) for i in idx))} | {_esc(brk)} |")
    add("")
    add("**★終了コードは、承認のプログラムが実際に走らせて記録します。**"
        "0 以外だったときだけ、その行を「済」にできます。")
    add("")
    return "\n".join(L)


def build_spec(d: dict) -> str:
    """SPEC と DESIGN_CONTRACT（実物から書き出す）。"""
    dc = d.get("DESIGN_CONTRACT") or {}
    sys.path.insert(0, str(PRIORITY))
    try:
        from verify_design_contract import spec_from_impl
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] 照合の道具を読み込めない: {e}（fail-closed）")
    impl = str(dc.get("impl_file") or "")
    path = SDK / impl
    if not path.exists():
        raise SystemExit(f"[gen_acceptance] impl_file の実物が無い: {path}（fail-closed）")
    spec = spec_from_impl(str(path))
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**")
    add("")
    add("DESIGN_CONTRACT")
    add("")
    add("```json")
    add(json.dumps(dc, ensure_ascii=False, indent=2))
    add("```")
    add("")
    add("SPEC")
    add("")
    add("```json")
    add(json.dumps({"impl_file": impl,
                    "public_functions": spec["public_functions"],
                    "constants": spec["constants"],
                    "cli_flags": spec["cli_flags"]}, ensure_ascii=False, indent=1))
    add("```")
    add("")
    return "\n".join(L)


def build_checklist(d: dict) -> str:
    """付録の照合の項目（hook の実体から抽出する道具を呼ぶ）。"""
    sys.path.insert(0, str(ROOT / ".claude" / "tools"))
    try:
        from list_banned_words import checklist_items, needs_group2
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] 項目を抽出する道具を読み込めない: {e}（fail-closed）")
    items = checklist_items()
    tgt = (d.get("TARGET") or [""])[0]
    g2 = needs_group2(tgt)
    g1 = [b for g, b in items if g == "群1"]
    g2list = [b for g, b in items if g == "群2"]
    L = []
    add = L.append
    add("**★この節はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。")
    add("")
    # ★2026-09-29＝項目を並べるだけで、照らした結果が1つも無かった（worklog 20260929 §49 の6）。
    #   元データの「ハード制約の照合」（群1 の項目と同じ数・同じ順の答え）を、項目の横に並べる。無い・数が違えば止める。
    ans = d.get("ハード制約の照合")
    if not isinstance(ans, list) or len(ans) != len(g1):
        raise SystemExit(f"[gen_acceptance] 元データの「ハード制約の照合」が、群1 の項目 {len(g1)} 件と同じ数の答えの一覧になっていない"
                         f"（いま {len(ans) if isinstance(ans, list) else '無し'}・fail-closed）。1件ずつ、この工事でどう守るかを書く")
    add("| # | 項目（hook の実体から抽出） | この工事での答え（元データ） |")
    add("|---|---|---|")
    for i, (b, a) in enumerate(zip(g1, ans), 1):
        add(f"| {i} | 【群1】{_esc(b[:110])} | {_esc(a)} |")
    add("")
    if g2:
        for b in g2list:
            add(f"- 【群2】{_esc(b[:110])}")
    else:
        add(f"- 【群2・{len(g2list)}件】まとめて非該当"
            "（売買のロジックにも審判にも触れないため）")
    add("")
    return "\n".join(L)


def build_stages(d: dict) -> str:
    """段ごとの表を、§2.2 の逐語から作る（★手で書かない・恒久69番）。

    ★なぜ在るか（2026-09-10）
      まこさんの問い＝「2-2の段ごと指標、閾値、パラメータ、時間足の組み方、使う法則」が
      設計書に1つも入っていなかった。§2.2 にはその全部が書いてあるのに、私は
      「§2.2 の段を、束の枡としてそのまま持つ」の1行しか書かなかった。
      だから、§2.2 の逐語を段ごとに割って、そのまま表にする。

    ★出どころを2か所に書かない＝`gen_s22_map.py` の抽出関数を呼ぶ。
    """
    sys.path.insert(0, str(ROOT / ".claude" / "tools"))
    try:
        from gen_s22_map import read_section, extract
    except Exception as e:
        raise SystemExit(f"[gen_acceptance] §2.2 を抜く道具を読み込めない: {e}（fail-closed）")
    items = [x for x in extract(read_section()) if x[1] == "段"]
    if not items:
        raise SystemExit("[gen_acceptance] §2.2 の段が0件（fail-closed）")

    L: list[str] = []
    add = L.append
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`engine_tuner_milestones2.md` の §2.2（レンジ判定の検索方法）を、"
        "`gen_s22_map.py` の抽出関数で読んだもの。**私は1文字も足していません。**")
    add("")
    add("| 段 | 何を選ぶ枠か | 使う法則 | 材料（指標の系統）と時間足 | 値の範囲 |")
    add("|---|---|---|---|---|")
    for sid, _kind, text in items:
        parts = [p.strip() for p in text.split("｜")]
        head = parts[0] if parts else ""
        mid = parts[1] if len(parts) > 1 else ""
        val = parts[2].replace("値＝", "") if len(parts) > 2 else ""
        m = re.match(r"^(\S+)\s*(.*?)（(.+?)）\s*$", head)
        if m:
            waku, laws = m.group(2).strip() or m.group(1), m.group(3)
        else:
            waku, laws = head, "—"
        add(f"| **{sid}** | {_esc(waku)} | {_esc(laws)} | {_esc(mid)} | {_esc(val)} |")
    add("")
    add(f"**段の件数＝{len(items)}件**（§2.2 に在るものを1つも落としていません）。")
    add("")
    return "\n".join(L)


BUILDER = {
    "STAGES": build_stages,
    "MATERIALS": build_materials,
    "LAWS": build_laws,
    "RANKING": build_ranking,
    "CODEREF": build_coderef,
    "RANDOM": build_random,
    "ACCEPT_TABLE": build_accept_table,
    "SELFTEST": build_selftest,
    "SPEC": build_spec,
    "CHECKLIST": build_checklist,
    # ★2026-09-11＝監査の指摘の表（`build_audit` は下で定義するので、名前で後から入れる）
}

_MARK_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def build_audit(d: dict) -> str:
    """この設計書に効いている監査レポートから、指摘を機械で抜き出す（2026-09-11 新設）。

    なぜ在るか（まこさん指示 2026-09-11・逐語）＝「ヌケモレ発生しそうなので、自動生成で対応できない？」

    ★何が起きていたか（実測 2026-09-11）＝私（CC）は監査の指摘を手で読んで報告し、
      **別枠4件（S-1〜S-4）を1行も出さなかった**。Critical 3件と Major 4件だけを出した。
    ★抜き出しは `gen_audit_todo.py` に任せる＝同じ判定を2か所に書き写さない。
      その道具は「表の行をそのまま写す」作りで、件数を丸めない・言い換えない・要約しない。
    ★元データの `audit_report` が空なら、この節は出さない（監査を受けていない設計書のため）。
    ★読めない・抜き出せないときは止まる（fail-closed）＝黙って0件にしない。
    """
    rel = (d.get("audit_report") or "").strip()
    if not rel:
        return ""
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"[gen_acceptance] 監査レポートが無い: {path}（fail-closed）")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import gen_audit_todo as _gat
    except Exception as e:                         # noqa: BLE001
        raise SystemExit(f"[gen_acceptance] 監査の抜き出しの道具を読めない: {e}（fail-closed）")
    items, missing = _gat.collect(str(path))
    if missing:
        raise SystemExit(f"[gen_acceptance] 監査レポートから節を切り出せない: {missing}"
                         "（見出しの書き方が変わった疑い・fail-closed）")
    if not items:
        raise SystemExit(f"[gen_acceptance] 監査レポートから指摘が0件（fail-closed）: {path}")
    L = [f"**出どころ**＝`{rel}` ／ **抜き出し**＝`.claude/tools/gen_audit_todo.py`"
         "（表の行をそのまま写す＝件数を丸めない・言い換えない・要約しない）",
         "",
         "**★この表は機械が作ります。**手で書き換えると `--verify` が止めます。"
         "**私（CC）が監査の件数を数え直しません**（恒久の決まり63番）。",
         "",
         "| 監査の節 | 番号 | 監査に書いてあること（逐語） |",
         "|---|---|---|"]
    for sec, no, body in items:
        L.append(f"| {_esc(sec)} | {_esc(no)} | {_esc(body)} |")
    L.append("")
    L.append(f"**合計 {len(items)} 行。**")
    L.append("")
    L.append("**★直したかどうかは、この表には出ません。**紐づけは監査レポートに書かれていないので、"
             "機械では出せません（私の解釈になります）。**直した記録は `next_step.md` の §6 と "
             "worklog に、1件ずつ書きます。**")
    return "\n".join(L)


BUILDER["AUDITTODO"] = build_audit      # ★定義の後に入れる（BUILDER は上で作っている）


def build_impl(d: dict) -> str:
    """元データの「実装の指示」から、監査結果の修正の指示と同じ6つの欄の節を組み立てる（2026-09-24 新設）。

    ★設計書 impl-instruction-apply-20260924（まこさん承認）。指示が無ければ空の文字列（節ごと出ない）。
    ★欄の並びと見出しは監査結果のテンプレ（`_template.md`）と同じ＝当てる道具が `gen_audit_docs.item_fields` で
      そのまま読める。読み取りは道具の側に1か所（ここには書かない）。
    """
    items = d.get("実装の指示") or []
    if not items:
        return ""
    L = ["**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝元データの `実装の指示`。"
         "当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`"
         "（承認の印と設計書のハッシュ値が合うときだけ当たる）。",
         ""]
    for it in items:
        L.append(f"#### 実装 {it.get('番号')}")
        L.append(f"対象のファイル: {it.get('対象のファイル', '')}")
        L.append(f"直す箇所: {it.get('直す箇所', 'なし')}")
        L.append("直す前の文字:")
        L.append("~~~")
        L.append(str(it.get("直す前の文字") if it.get("直す前の文字") is not None else "なし"))
        L.append("~~~")
        head = (f"案{it['案']} " if it.get("案") else "") + str(it.get("種類", "直した後の文字"))
        L.append(f"{head}:")
        L.append("~~~")
        L.append(str(it.get("中身", "")))
        L.append("~~~")
        L.append(f"根拠の抜き書き: {it.get('根拠の抜き書き', '')}")
        L.append(f"状態: {it.get('状態', '確定')}")
        L.append("")
    return "\n".join(L)


BUILDER["IMPL"] = build_impl            # ★定義の後に入れる（AUDITTODO と同じ）


# ══ 設計のもと（やることの行・まこさんが OK した文）と対応の表（2026-09-29）════════════════════
#   まこさん指示（2026-09-29・逐語）「やることリストなどの設計のもとになるものから設計書作成を自動生成」
#   ★CC は文を写さない。やることの行は m2_todo.json から、まこさんの文は gen_verbatim.py の逐語のファイルから、
#     この道具が写す。
#   ★対応の表＝写した1行ずつに「設計書のどの節・実装の指示の何番で満たすか」。1行でも無ければ書かない（fail-closed）。
#     抜けと誤りは全部 集めて一度に出す（1件ずつ止めない）。

TODO_FIELDS = ("一文", "中身", "触るファイル", "出るもの", "確かめ方", "注意")   # やることの行のうち、写して対応を求める欄
FIXED_SECTIONS = {"1", "2-1", "3-1", "3-2", "5", "6-1", "6-2", "6-3", "7-1", "7-2", "7-3", "7-3b",
                  "7-4", "7-5", "7-6", "7-7", "7-8"}                            # page が必ず出す節の番号
NO_MATCH = "対応なし"                                                           # 理由を必ず書く


def todo_item(no: str) -> dict:
    """やることリスト（m2_todo.json）から、番号の行（「一文」の欄を持つもの）を1つ探す。0件・2件以上は止まる。"""
    hits: list = []

    def walk(x):
        if isinstance(x, dict):
            if str(x.get("番号", "")) == no and "一文" in x:
                hits.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(_load(TODO))
    if len(hits) != 1:
        raise SystemExit(f"[gen_acceptance] やることリストに番号 {no} の行が {len(hits)} 件（1件であること・fail-closed）")
    return hits[0]


def source_rows(d: dict) -> list:
    """写す行＝[(出どころの番号, 文), …]。やることの行は欄ごと（一覧の欄は1つずつ）、逐語は1行ずつ（gen_verbatim.lines）。"""
    src = d.get("設計のもと") or {}
    rows: list = []
    for no in src.get("やることの番号") or []:
        it = todo_item(str(no))
        for k in TODO_FIELDS:
            v = it.get(k)
            if v in (None, "", []):
                continue
            vals = v if isinstance(v, list) else [v]
            for i, x in enumerate(vals, 1):
                rid = f"todo:{no}:{k}" + (f":{i}" if isinstance(v, list) else "")
                rows.append((rid, str(x)))
    for name in src.get("逐語のファイル") or []:
        try:
            rows += gv.lines(str(name))
        except gv.VerbatimError as e:
            raise SystemExit(f"[gen_acceptance] 逐語のファイルが照らしを通らない（{e}・fail-closed）")
    if not rows:
        raise SystemExit("[gen_acceptance] 元データの「設計のもと」が空です（やることの番号か逐語のファイルを1つ以上・fail-closed）")
    return rows


def section_ids() -> set:
    """対応の表に書いてよい節の番号＝page が必ず出す節と、§4 の項目の正本（design_section_map.json）の番号。"""
    m = _load(MAP)
    return FIXED_SECTIONS | {str(x.get("番号")) for x in (m.get("項目") or []) if x.get("節") == "§4"}


def match_problems(d: dict, rows: list) -> list:
    """対応の表の抜けと誤りを全部 集める。戻り＝文の一覧（空なら通る）。"""
    secs = section_ids()
    impl = {str(it.get("番号")) for it in (d.get("実装の指示") or [])}
    by: dict = {}
    bad = []
    for i, r in enumerate(d.get("対応の表") or [], 1):
        rid = str(r.get("出どころ", ""))
        by.setdefault(rid, []).append(r)
        ss = r.get("設計書の節")
        ss = [str(s) for s in (ss if isinstance(ss, list) else [ss]) if s not in (None, "")]
        if ss == [NO_MATCH]:
            if not str(r.get("理由", "")).strip():
                bad.append(f"対応の表の {i} 行目（{rid}）＝「{NO_MATCH}」なのに理由が無い")
        elif not ss:
            bad.append(f"対応の表の {i} 行目（{rid}）＝設計書の節が空")
        else:
            miss = [s for s in ss if s not in secs]
            if miss:
                bad.append(f"対応の表の {i} 行目（{rid}）＝設計書に無い節: {'・'.join(miss)}")
        miss_i = [str(x) for x in (r.get("実装の指示") or []) if str(x) not in impl]
        if miss_i:
            bad.append(f"対応の表の {i} 行目（{rid}）＝実装の指示に無い番号: {'・'.join(miss_i)}")
    ids = [rid for rid, _t in rows]
    for rid in ids:
        if rid not in by:
            bad.append(f"写した行 {rid} に、対応の表の行が無い")
    for rid in by:
        if rid not in ids:
            bad.append(f"対応の表の出どころ {rid} は、写した行に無い（打ち間違い・古い番号）")
    return bad


def build_source(d: dict) -> str:
    """設計書 §0-1＝設計のもと（やることの行・逐語の行）と対応の表。対応が1行でも欠ければ止まる。"""
    rows = source_rows(d)
    bad = match_problems(d, rows)
    if bad:
        raise SystemExit("[gen_acceptance] 設計のもとの対応が足りません（fail-closed・全部で "
                         f"{len(bad)} 件）:\n  " + "\n  ".join(bad))
    by: dict = {}
    for r in d.get("対応の表") or []:
        by.setdefault(str(r.get("出どころ")), []).append(r)
    src = d.get("設計のもと") or {}
    # ★2026-09-29＝逐語のファイルごとに、誰の文かを控えの「who」から書く（直す前は全部「まこさんの文」と読める書き方だった
    #   ＝OK をもらった CC の提案も並んでいた・worklog 20260929 §49 の2）。やることの番号が無ければ m2_todo.json を出どころに書かない。
    def _who(n):
        try:
            _t, m = gv.paths(n)
            w = set(json.load(open(m, encoding="utf-8")).get("who") or [])
        except Exception:                                    # noqa: BLE001
            w = set()
        return "まこさんの発言" if w == {"まこさん"} else ("まこさんが OK した CC の文" if w == {"CC"} else "まこさんの発言と CC の文")
    files = "・".join(f"`.claude/state/verbatim/{n}.txt`（{_who(n)}）" for n in (src.get("逐語のファイル") or [])) or "（無し）"
    origin = ("やることリスト `m2_todo.json` の行（欄ごと）と、" if src.get("やることの番号") else "")
    L = [f"**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝{origin}"
         "`gen_verbatim.py` がやり取りの記録から抜き出した逐語のファイル。**CC は1文字も写していません。**",
         "",
         f"**やることの番号**＝{'・'.join(str(x) for x in (src.get('やることの番号') or [])) or '（無し）'} ／ "
         f"**逐語のファイル**＝{files}",
         ""]
    # ★2026-09-29（まこさん指示「設計の元となるデータは明確にして」・worklog 20260929 §60）
    #   ＝逐語のファイルごとに、どの記録の、どの発言から抜き出したかを、控え（.meta.json）から表にする。
    #   直す前はファイル名と話し手だけで、元の発言を記録の中で探せなかった。
    L += ["**設計の元となるデータ（どこから抜き出したか）**",
          "",
          "| 逐語のファイル | 話し手 | 記録のファイル（やり取りの記録） | 発言の uuid | 時刻（UTC） | 本文の sha256 の先頭 | 行数 |",
          "|---|---|---|---|---|---|---|"]
    for n in src.get("逐語のファイル") or []:
        _t, m = gv.paths(str(n))
        meta = json.load(open(m, encoding="utf-8"))
        nrow = sum(1 for rid, _x in rows if rid.startswith(f"{n}:"))
        L.append(f"| `.claude/state/verbatim/{n}.txt` | {_who(n)} | `{Path(str(meta.get('session', ''))).name}` "
                 f"| {'・'.join(meta.get('uuids') or []) or '—'} | {'・'.join(meta.get('time') or []) or '—'} "
                 f"| {str(meta.get('sha256', ''))[:16] or '—'} | {nrow} |")
    for no in src.get("やることの番号") or []:
        nrow = sum(1 for rid, _x in rows if rid.startswith(f"todo:{no}:"))
        L.append(f"| `m2_todo.json` の {no} | やることリスト | — | — | — | — | {nrow} |")
    L += ["",
          "**照らし方**＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`（記録の発言と逐語のファイルが1文字も違わないか）。"
          "記録のファイルの置き場＝`~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/`。",
          "",
          f"**写した行＝{len(rows)} 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。",
          "",
          "| 出どころ | 文（逐語） | 設計書の節 | 実装の指示 | 理由 |",
          "|---|---|---|---|---|"]
    for rid, text in rows:
        for r in by[rid]:
            ss = r.get("設計書の節")
            ss = ss if isinstance(ss, list) else [ss]
            ii = "・".join(str(x) for x in (r.get("実装の指示") or [])) or "—"
            # ★「（逐語）」の印＝写した文の行と分かるようにする（承認ゲートの B-6 は「逐語」を含む行を結果の報告と見ない）
            L.append(f"| `{rid}`（逐語） | {_esc(text)} | {_esc('・'.join(str(s) for s in ss))} | {ii} "
                     f"| {_esc(r.get('理由', ''))} |")
    L.append("")
    return "\n".join(L)


BUILDER["SOURCE"] = build_source        # ★定義の後に入れる（AUDITTODO・IMPL と同じ）


def _repo(p) -> Path:
    """実装の指示の「対象のファイル」を実物の場所に直す（当てる道具 apply_audit_fix.repo_path と同じ決め方）。"""
    p = str(p or "").strip().strip("`")
    if p.startswith("SDK/"):
        return SDK / p[4:]
    for base in (ROOT, SDK):
        if (base / p).exists():
            return base / p
    return (ROOT / p) if (ROOT / p).parent.is_dir() else (SDK / p)


def impl_before_problems(d: dict) -> list:
    """実装の指示の「直す前の文字」が、実物にちょうど1か所在るか（2026-09-29）。

    ★なぜ要るか＝直す前の文字は CC が実物を見て書く（Bash で道具のファイルを別の所へ写す道は土台ゲートが止める）。
      写し間違いは、当てる道具が承認の後に初めて見つけていた。設計書を作る時点で機械が照らす。
    ★通すもの＝①ちょうど1か所 ②0か所で、直した後の文字（足す文字なら 直す前＋足す文字）がもう在る＝当て終わっている
      ③直す前の文字が「なし」の新しいファイルで、まだ無い（または中身がもう在る）。状態が「確定」でない件は見ない。
    """
    bad = []
    for it in d.get("実装の指示") or []:
        if str(it.get("状態", "確定")) != "確定":
            continue
        no = it.get("番号")
        before = it.get("直す前の文字")
        body = str(it.get("中身") or "")
        path = _repo(it.get("対象のファイル"))
        if before is None:
            bad.append(f"実装 {no}: 直す前の文字が無い")
            continue
        if str(before).strip() == "なし":
            if path.exists() and body not in path.read_text(encoding="utf-8"):
                bad.append(f"実装 {no}: 新しいファイルのはずが、別の中身でもう在る（{path}）")
            continue
        if not path.exists():
            bad.append(f"実装 {no}: 対象のファイルが無い（{path}）")
            continue
        cur = path.read_text(encoding="utf-8")
        n = cur.count(str(before))
        done = (str(before) + body) if it.get("種類") == "足す文字" else body
        if n == 1 or (n == 0 and body and done in cur):
            continue
        bad.append(f"実装 {no}: 直す前の文字が {path.name} に {n} か所（ちょうど1か所であること）")
    return bad


def build(kind: str, d: dict) -> str:
    """囲みの中身を作る。置き換えない目印が残ったら止める（fail-closed の3つ目）。"""
    body = BUILDER[kind](d)
    left = sorted(set(_MARK_RE.findall(body)))
    if left:
        raise SystemExit(f"[gen_acceptance] 置き換えられない目印が残っている: {left}（fail-closed）")
    return body


def laws_count_ok() -> tuple[bool, str]:
    """法則ファイルの件数と、書き出した表の行数が同じか（fail-closed の4つ目）。"""
    law = _load(LAWS)
    n = len([x for x in (law.get("法則") or []) if isinstance(x, dict)])
    body = build_laws({})
    rows = [ln for ln in body.splitlines()
            if ln.startswith("| **") and "番号" not in ln]
    return (len(rows) == n, f"法則ファイル {n}件 ／ 表 {len(rows)}行")


# ══ 設計書を組み立てる（7つの節）═════════════════════════════════════

def section4(d: dict) -> str:
    """§4（設計の中身）を、項目の正本（design_section_map.json）の順に組み立てる。

    ★なぜ正本を別に持つか（2026-09-10）
      まこさん指摘＝「まるごと設計のコアの部分が無い状態だよね」「思考が支離滅裂で
      その場しのぎすぎるんだよ」。私が §4 の項目を思いつきで足し、4回とも まこさんの
      問いで「出どころに在るのに項目に入っていないもの」が出た。
      だから項目は map に固定し、この関数は**並べるだけ**にする。

    fail-closed（黙って通さない）
      6. 項目の正本が読めない → 止まる
      7. 段が「必ず」の項目が、元データに無い（または空） → 止まる
      8. 段が「条件」で「当たらない」と書いたのに、理由が無い → 止まる
      9. 段が「省ける」で非該当なのに、理由と出どころが無い → 止まる
    """
    m = _load(MAP)
    items = [x for x in (m.get("項目") or []) if x.get("節") == "§4"]
    if not items:
        raise SystemExit(f"[gen_acceptance] §4 の項目が正本に無い: {MAP}（fail-closed 6）")

    # ★2026-09-10（まこさん決定・逐語「上記の項目順に修正でよい」）＝読む順に並べ替える。
    #   まこさん指摘＝「設計書の項目の順番が支離滅裂。冒頭は、目的とか概要、要件などで固めて、
    #   その後、全体の設計内容構造とかで、4-A この節に何を書いたか（一覧）などは後半でよいのでは？」。
    #   ★並び順の正本は MAP の「_§4の並び順」＝項目を2か所に書かない。
    #   fail-closed 10＝並び順に載っていない項目が在れば止める（項目を減らして出さないため）。
    order = m.get("_§4の並び順") or []
    if order:
        known = {str(x.get("番号")) for x in items}
        missing = [x for x in known if x not in order]
        ghost = [x for x in order if x not in known]
        if missing:
            raise SystemExit(
                "[gen_acceptance] 並び順に載っていない項目が在ります（fail-closed 10）＝"
                + "・".join(sorted(missing))
                + "\n  ★項目を減らして出さないための検査です。")
        if ghost:
            raise SystemExit(
                "[gen_acceptance] 並び順に、実在しない項目が在ります（fail-closed 10）＝"
                + "・".join(ghost))
        items = sorted(items, key=lambda x: order.index(str(x.get("番号"))))
    body = d.get("設計の中身") or {}

    L: list[str] = []
    add = L.append
    add("**★この節の項目は、正本 `design_section_sources.json` の3つの出どころ"
        "（うちの正本・外の標準・まこさんが過去に指摘したこと）118件を、"
        "1件も余さず引き受ける形に決めたものです。**"
        "割り当て＝`design_section_map.json`。検算＝`gen_design_sections.py --check`。")
    add("")
    # ★2026-09-10（まこさん指摘「4-A この節に何を書いたか（一覧）などは後半でよいのでは？」）
    #   ＝一覧は管理のための表なので、節の最後に出す。ここでは中身だけ作って、後で足す。
    tbl: list[str] = []
    tadd = tbl.append
    tadd("### 4-A この節に何を書いたか（一覧）")
    tadd("")
    tadd("**★この表は管理のためのものです。**設計の中身は上の 4-0 から順に読んでください。")
    tadd("")
    tadd("| 番号 | 段 | 項目 | 書いたか |")
    tadd("|---|---|---|---|")
    add = tadd  # ← 以降の行は一覧の表へ入れる（下で元に戻す）
    miss_must: list[str] = []
    miss_why: list[str] = []
    for it in items:
        no = str(it.get("番号"))
        step = str(it.get("段", ""))
        name = _esc(it.get("名前"))
        got = body.get(no)
        if no == "4-20" and (d.get("実装の指示") or []):
            # ★2026-09-24（設計書 impl-instruction-apply-20260924）＝実装の指示は元データの一覧から機械で作る
            state = f"書いた（実装の指示 {len(d['実装の指示'])} 件・プログラムが作る）"
        elif isinstance(got, dict) and got.get("非該当"):
            state = f"非該当（{_esc(got['非該当'])}）"
            if step == "必ず":
                miss_must.append(no)
            if not str(got["非該当"]).strip():
                miss_why.append(no)
        elif got:
            state = "書いた"
        else:
            state = "**未記入**"
            if step == "必ず":
                miss_must.append(no)
            else:
                miss_why.append(no)
        add(f"| {no} | {step} | {name} | {state} |")
    add("")
    add = L.append  # ★ここから先は本文へ戻す（一覧の表は最後に足す）

    if miss_must:
        raise SystemExit(
            "[gen_acceptance] 段が「必ず」の項目が埋まっていません（fail-closed 7）＝"
            + "・".join(miss_must)
            + "\n  ★「必ず」は非該当を認めません。どの工事でも書ける項目だからです。")
    if miss_why:
        raise SystemExit(
            "[gen_acceptance] 書いていない項目に、理由が在りません（fail-closed 8・9）＝"
            + "・".join(miss_why)
            + '\n  ★形＝{"非該当": "理由（出どころ）"} を元データの「設計の中身」に書いてください。')

    for it in items:
        no = str(it.get("番号"))
        add(f"### {no} {it.get('名前')}")
        add("")
        if it.get("中身"):
            add(f"**この項目に書くこと**＝{it['中身']}")
            add("")
        got = body.get(no)
        if no == "4-20" and (d.get("実装の指示") or []):
            # ★2026-09-24（設計書 impl-instruction-apply-20260924）＝4-20 は囲み IMPL（プログラムが作る）
            add(_begin("IMPL", _h(build("IMPL", d))))
            add(build("IMPL", d))
            add(_end("IMPL"))
            add("")
            continue
        if isinstance(got, dict) and got.get("非該当"):
            add(f"**非該当。**{got['非該当']}")
            add("")
            continue
        if isinstance(got, dict):
            for line in got.get("本文") or []:
                add(line)
            add("")
            blk = got.get("囲み")
            if blk:
                add(_begin(blk, _h(build(blk, d))))
                add(build(blk, d))
                add(_end(blk))
                add("")
        elif isinstance(got, list):
            # ★本文は行の一覧で持つ（1行ずつ出す。まとめて str() にすると
            #   Python の一覧の形（角括弧と引用符）がそのまま設計書に出る）。
            for line in got:
                add(str(line))
            add("")
        else:
            add(str(got))
            add("")
    # ★一覧は節の最後（まこさん指摘 2026-09-10「4-A この節に何を書いたか（一覧）などは後半でよいのでは？」）
    L.extend(tbl)
    return "\n".join(L)


def page(d: dict) -> str:
    """7つの節の設計書を組み立てる（囲みの外＝元データの文をそのまま置く）。"""
    L: list[str] = []
    add = L.append
    # ★2026-09-24（設計書 impl-instruction-apply-20260924）＝「実装の指示」は一覧（[]）でしか受けない（fail-closed）。
    #   散文で書いた指示をプログラムが解析する形にしない（設計書 3-1 の3）。
    if "実装の指示" in d and not isinstance(d.get("実装の指示"), list):
        raise SystemExit("[gen_acceptance] 元データの「実装の指示」が一覧（[]）の形ではありません（fail-closed）。")
    if any(not isinstance(it, dict) for it in (d.get("実装の指示") or [])):
        raise SystemExit("[gen_acceptance] 元データの「実装の指示」の中に、1件ずつの形（{…}）でないものが在ります（fail-closed）。")
    _ib = impl_before_problems(d)
    if _ib:
        raise SystemExit("[gen_acceptance] 実装の指示の直す前の文字が、実物と合いません（fail-closed・全部で "
                         f"{len(_ib)} 件）:\n  " + "\n  ".join(_ib))
    add(f'<!-- ARC iter="{d["iter"]}" -->')
    add("")
    add(f"# 設計書｜{d['設計書の題']}")
    add("")
    add("TARGET: " + ", ".join(d.get("TARGET") or []))
    if d.get("NEW_FILE"):
        add("NEW_FILE: " + ", ".join(d["NEW_FILE"]))
    if d.get("MODEL"):
        add("MODEL: " + ", ".join(d["MODEL"]))
    add("")
    # ★2026-09-29＝直す前は「engine_tuner_milestones2.md の §2.2」の固定の文で、どの工事でも出た（worklog 20260929 §42）。
    #   設計のもと（やることの番号・逐語のファイル）から作る。
    _src = d.get("設計のもと") or {}
    _req = []
    if _src.get("やることの番号"):
        _req.append("やることリスト `m2_todo.json` の " + "・".join(str(x) for x in _src["やることの番号"]) + " 番")
    if _src.get("逐語のファイル"):
        _req.append("逐語のファイル " + "・".join(f"`{n}`" for n in _src["逐語のファイル"]))
    add("REQUIREMENTS: 設計のもと（下の §0-1）＝" + ("／".join(_req) or "（無し）") + "。")
    add("")
    # ★2026-09-13（98回目・監査 cp36 の M-7＝next_step §6 の179番①）＝直す前は「未承認・実装はまだ1行も
    #   入れていません」と固定で書いていた。承認②（実装の後の作り直し）でも同じ文が出るので嘘になっていた。
    #   承認の状態は印（acceptance.approved・design_approved.json）が、実装の状態は 7-6 の表が正本＝そこを指す。
    add("**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。**"
        "**実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。")
    add("")
    # ★2026-09-29＝直す前は「手で書いたのは5つだけです」の固定の文で、嘘だった（4-0〜4-19・完成の条件ほかも手書き・§49 の1）。
    #   元データに在る欄の名前を、そのまま並べる（道具が作る囲みは <!-- ACC_… --> の中だけ）。
    _hand = [k for k in d if not str(k).startswith("_") and k not in ("iter", "audit_report")]
    add("**★この設計書は、元データ `.claude/ratchet/acceptance_src.json` からプログラムが組み立てます。**"
        f"CC が手で書いたのは、元データの次の {len(_hand)} 欄です＝{'・'.join(_hand)}。"
        "囲み（`<!-- ACC_… -->` の中）は、プログラムが正本から作りました。"
        "作り直し＝`python3 .claude/tools/gen_acceptance.py --write`。手で書き換えられていないかの検出＝`--verify`。")
    add("")

    add("## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）")
    add("")
    # ★2026-09-29（まこさんが OK した提案の7行目「「まこさんの決定」を私が手で書く口は閉じます。」）
    #   ＝元データに「まこさんの決定」の欄が在れば止める。まこさんの文は、下の 0-1 に道具が逐語のファイルから写す。
    if d.get("まこさんの決定"):
        raise SystemExit("[gen_acceptance] 元データに「まこさんの決定」の欄が在ります（fail-closed）＝CC が手で書く口は閉じました。"
                         "まこさんの文は gen_verbatim.py で逐語のファイルにし、元データの「設計のもと」の「逐語のファイル」に名前を書く。")
    add("**下の 0-1 は、やり取りの記録から抜き出した逐語のファイルを、道具が写したものです（CC は写していません）。**"
        "誰の文か（まこさんの発言か、まこさんが OK した CC の文か）は、ファイルごとに書いてあります。")
    add("")
    # ★2026-09-29（worklog §58）＝見出しは元データの「設計のもと」から決める（やることの番号が無いのに「やることの行」と書かない）
    _todo = bool((d.get("設計のもと") or {}).get("やることの番号"))
    add("### 0-1 設計のもと（" + ("やることの行と、" if _todo else "") + "まこさんの発言と、まこさんが OK した文・プログラムが写しました）")
    add("")
    add(_begin("SOURCE", _h(build("SOURCE", d))))
    add(build("SOURCE", d))
    add(_end("SOURCE"))
    add("")

    add("## 1｜概要")
    add("")
    add(d["何を作るか"])
    add("")

    add("## 2｜背景と範囲")
    add("")
    add("### 2-1 いまの状態（走らせて測ったもの）")
    add("")
    add("| 何を測ったか | コマンド | 結果 |")
    add("|---|---|---|")
    # ★2026-09-17（設計書 acceptance-results-from-commands-20260917・まこさん「手書きはするな」）
    #   ＝結果の欄は、道具がコマンドを走らせて入れる。直す前は元データの「結果」を私が手で写し、
    #     そのまま載せていた（コマンドと結果が合わない行を書いた＝worklog 20260917 §25 の前）。
    #   ★走らせるのは読むだけのコマンドだけ＝元データに書いたコマンドを道具が走らせると、
    #     Bash の土台ゲートを通らずに書き込む道になるため。
    #   ★区切りは「 | 」（前後に空白）＝grep の `a\|b` の縦棒は区切りにしない。
    def _measure(cmd: str) -> str:
        import shlex as _shlex
        read_heads = {"grep", "wc", "sed", "awk", "find", "sort", "head", "tail", "cut", "uniq", "tr", "cat"}
        git_subs = {"diff", "log", "show", "status", "ls-files", "grep"}
        py_tools = {"run_breaks.py", "tidy_next_step.py", "gen_hook_list.py", "verify_design_contract.py"}
        py_flags = {"--verify", "--count-targets", "--selftest", "--parse-only", "--lint-expect",
                    "--check", "--diff", "--design"}
        for bad in (">", "<", ";", "&", "`", "$(", "\n"):
            if bad in cmd:
                raise SystemExit(f"[gen_acceptance] 「なぜ作るか」のコマンドに「{bad}」が在ります"
                                 f"（読むだけのコマンドに限る・fail-closed）: {cmd}")
        for seg in cmd.split(" | "):
            try:
                toks = _shlex.split(seg)
            except ValueError as e:
                raise SystemExit(f"[gen_acceptance] コマンドを読めない（{e}・fail-closed）: {seg}")
            if not toks:
                raise SystemExit(f"[gen_acceptance] 空のコマンドの区切りが在る（fail-closed）: {cmd}")
            head = toks[0]
            why = ""
            if head in read_heads:
                if head == "sed" and any(t.startswith("-i") or t.startswith("--in-place") for t in toks[1:]):
                    why = "sed の -i（書き込み）"
                elif head == "find" and any(t in ("-exec", "-execdir", "-delete", "-ok", "-okdir",
                                                  "-fprint", "-fprintf", "-fls") for t in toks[1:]):
                    why = "find の書き込み・実行の旗"
                elif head == "awk" and "system(" in seg:
                    why = "awk の system("
            elif head == "git":
                if len(toks) < 2 or toks[1] not in git_subs:
                    why = "git の読むだけでない使い方"
            elif head == "python3":
                args = toks[1:]
                if not args or args[0].rsplit("/", 1)[-1] not in py_tools:
                    why = "決まった道具でない python3"
                elif any(t.startswith("-") and t not in py_flags for t in args[1:]):
                    why = "決まった読むだけの旗でない"
                elif not any(t in py_flags for t in args[1:]):
                    why = "読むだけの旗が無い python3"
            else:
                why = f"読むだけのコマンドの一覧に無い先頭の語「{head}」"
            if why:
                raise SystemExit(f"[gen_acceptance] 「なぜ作るか」のコマンドを走らせません＝{why}"
                                 f"（読むだけのコマンドに限る・fail-closed）: {cmd}")
        try:
            r = subprocess.run(["bash", "-c", cmd], cwd=str(ROOT), capture_output=True,
                               text=True, timeout=120)
        except subprocess.TimeoutExpired:
            raise SystemExit(f"[gen_acceptance] 「なぜ作るか」のコマンドが120秒で終わらない（fail-closed）: {cmd}")
        out = (r.stdout or "").strip() or (r.stderr or "").strip()
        lines = out.splitlines()
        text = " ⏎ ".join(lines)
        if len(text) > 500:
            text = text[:500] + f"…（出力 {len(lines)} 行のうち先頭 500 文字）"
        return f"{text}（終了コード {r.returncode}）"

    for r in d.get("なぜ作るか") or []:
        if "結果" in r:
            raise SystemExit("[gen_acceptance] 元データの「なぜ作るか」に「結果」の欄が在ります（fail-closed）。"
                             "結果は道具がコマンドを走らせて入れます（まこさん「手書きはするな」）。"
                             f"「読み方」（数字なし）に書き替えてください: {r.get('何を測ったか')}")
        yomi = str(r.get("読み方") or "")
        if re.search(r"[0-9０-９]", yomi):
            raise SystemExit("[gen_acceptance] 「なぜ作るか」の「読み方」に数字が在ります（fail-closed）。"
                             f"数字はコマンドの出力にだけ出します: {yomi}")
        cell = _esc(_measure(str(r["コマンド"]))) + (f"／読み方＝{_esc(yomi)}" if yomi else "")
        add(f"| {_esc(r['何を測ったか'])} | `{_esc(r['コマンド'])}` | {cell} |")
    add("")
    add("### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）")
    add("")
    add(_begin("MATERIALS", _h(build("MATERIALS", d))))
    add(build("MATERIALS", d))
    add(_end("MATERIALS"))
    add("")
    add("### 2-3 成績表に載っている本数")
    add("")
    add(_begin("RANKING", _h(build("RANKING", d))))
    add(build("RANKING", d))
    add(_end("RANKING"))
    add("")
    add("### 2-4 いま乱数を使っている場所")
    add("")
    add(_begin("RANDOM", _h(build("RANDOM", d))))
    add(build("RANDOM", d))
    add(_end("RANDOM"))
    add("")

    add("## 3｜目標と、やらないこと")
    add("")
    add("### 3-1 やらないこと（1件ずつ・理由と出どころ）")
    add("")
    add("| # | やらないこと | 理由 | 出どころ |")
    add("|---|---|---|---|")
    for i, r in enumerate(d["やらないこと"], 1):
        add(f"| {i} | {_esc(r['中身'])} | {_esc(r['理由'])} | {_esc(r['出どころ'])} |")
    add("")
    add("### 3-2 決めてほしいこと")
    add("")
    add("| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |")
    add("|---|---|---|---|")
    for i, r in enumerate(d.get("決めてほしいこと") or [], 1):
        add(f"| {i} | {_esc(r['中身'])} | {_esc(r['私の案'])} | {_esc(r.get('出どころ', ''))} |")
    if not d.get("決めてほしいこと"):
        add("| — | 無し（元データの「決めてほしいこと」が空） | — | — |")
    add("")

    add("## 4｜設計の中身")
    add("")
    add(section4(d))
    add("")

    add("## 5｜決めたことと理由・捨てた案")
    add("")
    add("| # | 決めたこと | 理由 | 捨てた案 |")
    add("|---|---|---|---|")
    for i, r in enumerate(d.get("決めたことと理由") or [], 1):
        add(f"| {i} | {_esc(r['決めたこと'])} | {_esc(r['理由'])} | {_esc(r['捨てた案'])} |")
    add("")

    add("## 6｜テストとリスクと見積もり")
    add("")
    add("### 6-1 わざと壊して止まるか試すテスト")
    add("")
    add(_begin("SELFTEST", _h(build("SELFTEST", d))))
    add(build("SELFTEST", d))
    add(_end("SELFTEST"))
    add("")
    add("### 6-2 リスク")
    add("")
    add("| # | リスク | どうするか |")
    add("|---|---|---|")
    for i, r in enumerate(d.get("リスク") or [], 1):
        add(f"| {i} | {_esc(r['中身'])} | {_esc(r['どうするか'])} |")
    add("")
    add("### 6-3 見積もり")
    add("")
    add("| 何 | 見込み | 根拠 |")
    add("|---|---|---|")
    for r in d.get("見積もり") or []:
        add(f"| {_esc(r['何'])} | {_esc(r['見込み'])} | {_esc(r['根拠'])} |")
    add("")
    add("**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**")
    add("")
    _audit = build_audit(d)
    if _audit:
        add("### 6-4 この設計書に効いている監査の指摘（★機械が抜き出します）")
        add("")
        add(_begin("AUDITTODO", _h(_audit)))
        add(_audit)
        add(_end("AUDITTODO"))
        add("")

    add("## 7｜付録（hook が求める項目）")
    add("")
    add("### 7-1 深掘り4点")
    add("")
    add("**① 真因（root cause）**＝" + d["真因"])
    add("")
    add("**② 期待値分解**＝" + d["期待値分解"])
    add("")
    add("**③ root か symptom か**＝" + d["root か symptom か"])
    add("")
    add("**④ ベースアップ**＝" + d["ベースアップ"])
    add("")
    add("### 7-2 ★疑似シミュ由来の固定値ゼロ宣言")
    add("")
    add(d["固定値ゼロ宣言"])
    add("")
    add("### 7-3 変更の単位（H16）")
    add("")
    add(d["変更の単位"])
    add("")
    add("### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）")
    add("")
    add("**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**"
        "出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。"
        "**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。")
    add("")
    # ★2026-09-29＝恒久の決まり §1 は engine_tuner の要件の照合。売買のロジックに触らない工事では非該当（worklog §42）
    if not touches_trading(d):
        add(NONTRADE)
    else:
        add("| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |")
        add("|---|---|---|---|")
        _hantei = d.get("作ってはいけないものとの照合") or {}
        for _no, _name in forbidden_items():
            _r = _hantei.get(_no)
            if not _r:
                raise SystemExit(f"[gen_acceptance] 「作ってはいけないもの」の {_no} 番との照合が"
                                 "元データに無い（fail-closed・恒久の決まり §1）")
            add(f"| {_no} | {_esc(_name)} | **{_esc(_r['当たるか'])}** | {_esc(_r['理由'])} |")
    add("")
    add("### 7-4 塞げないもの")
    add("")
    add("| 問い | 塞げないこと |")
    add("|---|---|")
    for r in d.get("塞げないもの") or []:
        add(f"| **{_esc(r['問い'])}** | {_esc(r['塞げないこと'])} |")
    add("")
    add("### 7-5 §4.6 ハード制約の照合")
    add("")
    add(_begin("CHECKLIST", _h(build("CHECKLIST", d))))
    add(build("CHECKLIST", d))
    add(_end("CHECKLIST"))
    add("")
    add("### 7-6 完成の条件")
    add("")
    add("**★状態は全部「未着手」です。「済」にするのはプログラムです**"
        "（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。"
        "**自分で「直った」と判定しません**（恒久の決まり64番）。"
        "**★触る関数の一覧は、実装の後に確定させます**"
        "＝`verify_design_contract.py --write` の出力で置き替えます。")
    add("")
    add(_begin("ACCEPT_TABLE", ""))
    add(build("ACCEPT_TABLE", d))
    add(_end("ACCEPT_TABLE"))
    add("")
    # ★2026-09-09（設計書 gen-acceptance-tool-20260909）＝見出しに SPEC の語を入れない。
    #   なぜ＝突き合わせの道具（verify_design_contract.extract_block）は、見出しに語が在れば
    #   それを目印として数え、その後ろの最初の囲みを読む。見出しに SPEC と書くと、
    #   すぐ後ろの DESIGN_CONTRACT の囲みを SPEC として読み、齟齬 66件の誤報が出た（実測）。
    #   ★目印は、下の単独の行（DESIGN_CONTRACT／SPEC）だけに置く。
    # ★2026-09-10＝§4 から §7 へ移した（別の AI の点検・逐語「恒久の決まり69番は、
    #   行番号を手で打つなと求めています。（略）手で書く §4 に置くと、69番と正面から
    #   ぶつかります」）。実測＝同じ4件の関数が §4-3・§7-7 の DESIGN_CONTRACT・
    #   §7-7 の SPEC の3か所に出ていた。
    add("### 7-7 触る関数と、その定義の行")
    add("")
    add(_begin("CODEREF", _h(build("CODEREF", d))))
    add(build("CODEREF", d))
    add(_end("CODEREF"))
    add("")

    add("### 7-8 プログラムが読む設定（2つ）")
    add("")
    add(_begin("SPEC", _h(build("SPEC", d))))
    add(build("SPEC", d))
    add(_end("SPEC"))
    add("")
    return "\n".join(L).rstrip() + "\n"


# ══ 書く・検出する ═══════════════════════════════════════════════════

def write(dry: bool = False, dest: Path = None) -> int:
    """設計書を作る。

    ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §3-2 の3）
      ＝書き出し先を差し替えられるようにした（`dest`）。
      なぜ＝自己テストが `write()` を呼ぶので、差し替えられないと、
      テストを走らせるたびに本物の設計書（`.claude/state/acceptance.md`）が
      上書きされ、承認が外れてこの道具を直せなくなる（2026-09-09 に実際に起きた）。
      ★`dest` を省くと、いままでどおり本物の設計書に書く（動きは変えていない）。
    """
    d = src()
    ok, why = laws_count_ok()
    if not ok:
        raise SystemExit(f"[gen_acceptance] 法則の件数が合わない（{why}）＝1件も落とせません（fail-closed）")
    body = page(d)
    if dry:
        print(body)
        return 0
    out = Path(dest) if dest else DEST
    out.write_text(body, encoding="utf-8")
    print(f"✅ --write 完了: {out}（{len(body.splitlines())}行・囲み {len(BLOCKS)}個）")
    print(f"   法則の件数の照合＝{why}")
    return 0


def _section4_blocks() -> set:
    """§4 の節が名指ししたときだけ出る囲み。

    ★2026-09-16＝この2つだけ。ほかの囲みは `page` が必ず出す＝いつも照らす。
      実物で確かめた＝`page` が MATERIALS・RANKING・RANDOM・CODEREF・SELFTEST・SPEC・
      CHECKLIST を直に書き、STAGES と LAWS は §4 の節の「囲み」の指定から出る。
      ★最初は5つと書いて、MATERIALS・RANKING・RANDOM を照らさなくする間違いをした。
    """
    return {"STAGES", "LAWS"}


def _blocks_in_src(d: dict) -> set:
    """元データの §4 の節が、実際に名指ししている囲みの名前。"""
    out = set()
    for got in (d.get("設計の中身") or {}).values():
        if isinstance(got, dict) and got.get("囲み"):
            out.add(got["囲み"])
    return out


def verify(dest: Path = None) -> int:
    """囲みの中が、機械の書いたままかを検出する。

    ★2026-09-09＝読む相手を差し替えられるようにした（`write` と対）。
    """
    target = Path(dest) if dest else DEST
    if not target.exists():
        print(f"❌ 設計書が無い: {target}")
        return 1
    d = src()
    cur = target.read_text(encoding="utf-8")
    rc = 0
    for kind in BLOCKS:
        if kind == "ACCEPT_TABLE":
            continue                                  # 承認ゲートが読む目印＝hash を持たない
        # ★2026-09-13（98回目）＝監査レポートの欄が空の設計書は、作る側（page）が AUDITTODO の囲みを出さない。
        #   直す前は検出の側だけが囲みを求め、必ず「❌ 囲みが無い」になっていた（作る側と検出の側の食い違い）。
        if kind == "AUDITTODO" and not (d.get("audit_report") or "").strip():
            print("— --verify: AUDITTODO は監査レポートの欄が空なので出ない設計書（照らさない）")
            continue
        # ★2026-09-24（設計書 impl-instruction-apply-20260924・監査 CP41 の B1）＝作る側が出さない囲みは照らさない。
        #   足さないと、指示が無い設計書で必ず ❌ になり、--selftest の T1 が落ちて b72・b73 が空になる。
        if kind == "IMPL" and not (d.get("実装の指示") or []):
            print("— --verify: IMPL は元データの「実装の指示」が空なので出ない設計書（照らさない）")
            continue
        # ★2026-09-16（設計書 audit-autofix-apply-20260916 の完成の条件 AUDIT-7・まこさん承認）
        #   ＝§4 の節に置く囲み（STAGES・LAWS など）は、作る側（page）が
        #     「元データのその節に『囲み』の指定が在るときだけ」出す。
        #   直す前＝検出の側だけが必ず求めたので、engine_tuner の設計書でない工事では
        #     必ず ❌ が2件 出た（98回目に AUDITTODO で入れたのと同じ型の食い違い）。
        if kind in _section4_blocks() and kind not in _blocks_in_src(d):
            print(f"— --verify: {kind} は元データのどの節も求めていないので出ない設計書（照らさない）")
            continue
        m = _begin_re(kind).search(cur)
        e = cur.find(_end(kind))
        if not m or e < 0:
            print(f"❌ --verify: {kind} の囲みが無い")
            rc = 1
            continue
        got = cur[cur.find("\n", m.start()) + 1: e].rstrip("\n")
        want = build(kind, d)
        if _h(got) != m.group(1):
            print(f"❌ --verify: {kind} は手で書き換えられています（本文 {_h(got)} ／ 目印 {m.group(1)}）")
            rc = 1
        elif got.rstrip() != want.rstrip():
            print(f"❌ --verify: {kind} は正本と食い違っています（--write で作り直してください）")
            rc = 1
        else:
            print(f"✅ --verify: {kind} は機械が書いたままです（hash={m.group(1)}）")
    ok, why = laws_count_ok()
    print(f"{'✅' if ok else '❌'} 法則の件数の照合＝{why}")
    rc |= 0 if ok else 1
    return rc


def diff_ok_before_impl(out: str) -> tuple:
    """実物との突き合わせの結果を、実装の前の状態として見てよいかを判定する。

    ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §4-1 の2）
      通すのは2通りだけ＝①齟齬が0件 ②齟齬が「設計にあるが実物に無い関数」だけ。
      ②を通す理由＝実装の前は、設計書に書いた関数がまだ実物に無いのが正しい。
      ★ほかの齟齬（実物にあるが設計に無い・呼ぶはずの名前が無い・定数の値が違う 等）
        は1件でも在れば落とす＝設計書と実物の食い違いを見る検査は消していない。
    戻り＝(通すか, 理由の文)
    """
    ALLOW = "設計にあるが実物に無い関数"
    if "齟齬: 0件" in out:
        return True, "齟齬 0件"
    rows = [ln.strip() for ln in out.splitlines() if ln.startswith("    ") and ln.strip()]
    if not rows:
        return False, f"齟齬の行が読めない（{out.strip()[:100]}）"
    other = [r for r in rows if not r.startswith(ALLOW)]
    if other:
        return False, f"実装の前でも通せない齟齬が {len(other)}件（{other[0][:70]}）"
    return True, f"齟齬は「{ALLOW}」{len(rows)}件だけ＝実装の前の正しい状態"


def selftest() -> int:
    """わざと壊して ❌ が出るかを試す（8件）。

    ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §3-2 の3）
      ＝本物の設計書（`.claude/state/acceptance.md`）には1文字も書かない。
      控え（一時のファイル）を相手にする。
      直す前＝T1 が `write()` を呼び、本物の設計書を上書きしていた。
      テストを走らせるだけで承認が外れ、この道具を直せなくなる作りだった。
    """
    ok = 0
    total = 0
    orig_src = SRC.read_text(encoding="utf-8")
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix="_acceptance_selftest.md", delete=False, encoding="utf-8")
    tmp.close()
    copy = Path(tmp.name)
    try:
        # T1 いまの状態で --verify が通る
        total += 1
        write(dest=copy)
        if verify(dest=copy) == 0:
            ok += 1
            print(f"   T{total} いまの状態で --verify → pass")
        else:
            print(f"   T{total} いまの状態で --verify が ❌ → fail")

        # T2 囲みに1行 足すと --verify が落ちる
        total += 1
        base = copy.read_text(encoding="utf-8")
        # ★2026-09-17（設計書 acceptance-results-from-commands-20260917）＝LAWS から MATERIALS へ。
        #   直す前＝LAWS の囲みは §4 の節が名指ししたときだけ出るので、engine_tuner の設計書でない工事では
        #     m が None になり、T2 で落ちていた（b72・b73 は壊さなくても rc=1 になり、守りを測れていなかった）。
        #   MATERIALS は page が必ず出す囲み（_section4_blocks の注記）。
        m = _begin_re("MATERIALS").search(base)
        copy.write_text(base[:m.end()] + "\nわざと足した1行\n" + base[m.end():], encoding="utf-8")
        if verify(dest=copy) == 1:
            ok += 1
            print(f"   T{total} 囲みに1行 足すと ❌ → pass")
        else:
            print(f"   T{total} 1行 足しても ✅ のまま → fail")
        copy.write_text(base, encoding="utf-8")

        # T3 「やらないこと」が空だと --write が止まる
        total += 1
        d = json.loads(orig_src)
        d["やらないこと"] = []
        SRC.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            src()
            print(f"   T{total} やらないことが空でも通る → fail")
        except SystemExit:
            ok += 1
            print(f"   T{total} やらないことが空だと止まる → pass")
        SRC.write_text(orig_src, encoding="utf-8")

        # T4 法則を1件 減らすと件数の照合が落ちる（ファイルは書かない）
        total += 1
        law = _load(LAWS)
        n = len([x for x in law["法則"] if isinstance(x, dict)])
        rows = [ln for ln in build_laws({}).splitlines() if ln.startswith("| **")]
        if len(rows) == n and n > 1:
            ok += 1
            print(f"   T{total} 法則の件数の照合が効く（{n}件を全部 並べた） → pass")
        else:
            print(f"   T{total} 法則の件数が合わない（法則 {n}件／表 {len(rows)}行） → fail")

        # T5 正本が読めないと止まる
        total += 1
        try:
            _load(RATCHET / "存在しない正本.json")
            print(f"   T{total} 無い正本でも通る → fail")
        except SystemExit:
            ok += 1
            print(f"   T{total} 無い正本で止まる → pass")

        # T6 置き換えない目印が残ると止まる
        total += 1
        try:
            body = "見本 {{" + "UNKNOWN}}"
            left = sorted(set(_MARK_RE.findall(body)))
            if left:
                raise SystemExit("目印が残っている")
            print(f"   T{total} 目印が残っても通る → fail")
        except SystemExit:
            ok += 1
            print(f"   T{total} 目印が残ると止まる → pass")

        # T7 作った設計書が、実物との突き合わせで齟齬0件
        #   ★2026-09-09（設計書 gen-acceptance-tool-20260909 の §4-1 の2）
        #     ＝実装の前は「設計にあるが実物に無い関数」が出るのが正しい状態。
        #     その1種類だけの齟齬なら通す。ほかの齟齬が1件でも在れば落とす。
        #     直す前＝齟齬が1件でも在れば落としていたので、実装の前は必ず落ちた。
        total += 1
        r = subprocess.run(
            [sys.executable, str(PRIORITY / "verify_design_contract.py"), "--diff", str(copy)],
            capture_output=True, text=True, cwd=str(SDK))
        ok7, why7 = diff_ok_before_impl(r.stdout)
        if ok7:
            ok += 1
            print(f"   T{total} 実物との突き合わせ（{why7}） → pass")
        else:
            print(f"   T{total} 実物との突き合わせ → fail（{why7}）")

        # T8 作った設計書が、食い違いゲートを通る
        total += 1
        r = subprocess.run(
            [sys.executable, str(ROOT / ".claude/hooks/enforce_design_consistency.py"),
             "--check", str(copy)], capture_output=True, text=True)
        if r.returncode == 0:
            ok += 1
            print(f"   T{total} 食い違いゲート 終了コード 0 → pass")
        else:
            print(f"   T{total} 食い違いゲート → fail（{r.stdout.strip()[:120]}）")

        # T9（2026-09-17・設計書 acceptance-results-from-commands-20260917）＝2-1 の表の結果は道具が入れる
        #   ①書き込みのコマンドで止まる ②読むだけのコマンドの出力と終了コードが表に入る
        #   ③元データに「結果」の欄が在ると止まる（本物のファイルには書かない＝page を直に呼ぶ）
        total += 1
        bad9 = ""
        d9 = json.loads(orig_src)
        d9["なぜ作るか"] = [{"何を測ったか": "見本", "コマンド": "rm -f /tmp/gen_acceptance_t9"}]
        try:
            page(d9)
            bad9 = "書き込みのコマンドで止まらない"
        except SystemExit:
            pass
        d9["なぜ作るか"] = [{"何を測ったか": "見本", "コマンド": "grep -c '^def page' .claude/tools/gen_acceptance.py",
                            "読み方": "定義の数"}]
        try:
            if "| 1（終了コード 0）／読み方＝定義の数 |" not in page(d9):
                bad9 = bad9 or "出力と終了コードが表に入らない"
        except SystemExit as e:
            bad9 = bad9 or f"読むだけのコマンドで止まった（{e}）"
        d9["なぜ作るか"] = [{"何を測ったか": "見本", "コマンド": "grep -c x .claude/tools/gen_acceptance.py",
                            "結果": "手で写した"}]
        try:
            page(d9)
            bad9 = bad9 or "「結果」の欄で止まらない"
        except SystemExit:
            pass
        if not bad9:
            ok += 1
            print(f"   T{total} 2-1 の結果を道具が入れる（書き込みで止まる・出力が入る・手の結果で止まる） → pass")
        else:
            print(f"   T{total} 2-1 の結果 → fail（{bad9}）")

        # T10（2026-09-29）＝対応の表から1行 消すと、設計書を書かない（設計のもとの抜けを通さない）
        total += 1
        d10 = json.loads(orig_src)
        tab = list(d10.get("対応の表") or [])
        if not tab:
            print(f"   T{total} 元データに対応の表が無い → fail")
        else:
            d10["対応の表"] = tab[1:]
            try:
                page(d10)
                print(f"   T{total} 対応の表の1行を消しても書ける → fail")
            except SystemExit as e:
                if "写した行" in str(e):
                    ok += 1
                    print(f"   T{total} 対応の表の1行を消すと止まる（写した行に対応が無い） → pass")
                else:
                    print(f"   T{total} 別の理由で止まった → fail（{str(e)[:120]}）")

        # T11（2026-09-29）＝元データに「まこさんの決定」の欄（CC が手で書く口）を足すと止まる
        total += 1
        d11 = json.loads(orig_src)
        d11["まこさんの決定"] = ["CC が手で書いた行（T11）"]
        try:
            page(d11)
            print(f"   T{total} まこさんの決定の欄を足しても書ける → fail")
        except SystemExit as e:
            if "手で書く口は閉じました" in str(e):
                ok += 1
                print(f"   T{total} まこさんの決定の欄を足すと止まる → pass")
            else:
                print(f"   T{total} 別の理由で止まった → fail（{str(e)[:120]}）")

        # T12（2026-09-29・まこさん指示「設計の元となるデータは明確にして」）＝0-1 に、逐語のファイルごとの
        #   記録のファイル・発言の uuid・時刻・行数の表が出て、行数の合計が写した行の数と合う
        total += 1
        d12 = json.loads(orig_src)
        try:
            s12 = build_source(d12)
            names12 = [str(n) for n in ((d12.get("設計のもと") or {}).get("逐語のファイル") or [])]
            rows12 = [ln for ln in s12.splitlines() if ln.startswith("| `.claude/state/verbatim/")]
            sum12 = sum(int(ln.rstrip(" |").rsplit("|", 1)[-1]) for ln in rows12)
            uu12 = all(len(ln.split("|")[4].strip()) >= 36 for ln in rows12)
            if (names12 and len(rows12) == len(names12) and sum12 == len(source_rows(d12))
                    and uu12 and "設計の元となるデータ" in s12):
                ok += 1
                print(f"   T{total} 0-1 に設計の元となるデータの表が出る（{len(rows12)} 本・{sum12} 行＝写した行と一致） → pass")
            else:
                print(f"   T{total} 設計の元となるデータの表 → fail（本={len(rows12)}/{len(names12)} 行={sum12} uuid={uu12}）")
        except SystemExit as e:
            print(f"   T{total} 設計の元となるデータの表 → fail（{str(e)[:120]}）")
    finally:
        SRC.write_text(orig_src, encoding="utf-8")
        copy.unlink(missing_ok=True)
    print(f"\n{'✅' if ok == total else '❌'} selftest {ok}/{total} pass")
    return 0 if ok == total else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="元データと正本から設計書を作る")
    p.add_argument("--verify", action="store_true", help="囲みの中が機械の書いたままかを検出する")
    p.add_argument("--dry-run", action="store_true", help="書かずに画面に出す")
    p.add_argument("--selftest", action="store_true", help="わざと壊して ❌ が出るかを試す（8件）")
    # ★2026-09-29＝控えの元データ（.claude/state の acceptance_src_*.json）で、書かずに作ってみる口。
    #   なぜ＝ratchet の元データへの書き込みは hook 12 が止めることがあり、まこさんに cp をお願いしてから
    #   止まり所に当たると、cp を何度もお願いすることになった（132回目に5回）。cp の前に控えで全部 確かめる。
    #   ★--dry-run と一緒のときだけ受ける（--write は ratchet の元データからだけ）。
    p.add_argument("--src", default="", help="--dry-run で読む元データ（控え）")
    # ★2026-09-29＝--src で作った設計書を、本物の設計書（acceptance.md）ではない置き場に書く口
    #   （承認の前の検査 pre_audit_check.py --check-design <置き場> に掛けるため）。
    p.add_argument("--out", default="", help="--dry-run --src の結果を書く置き場（本物の設計書には書かない）")
    a = p.parse_args()
    if a.src:
        # ★2026-09-29＝--selftest も控えの元データで走らせられるようにした（ratchet の元データを cp する前に確かめる）
        if not (a.dry_run or a.selftest):
            print("❌ --src は --dry-run か --selftest と一緒のときだけ使えます（--write は ratchet の元データからだけ）")
            return 2
        global SRC
        SRC = Path(a.src).resolve()
    if a.out:
        out = Path(a.out).resolve()
        if not a.src or out == DEST.resolve() or out.suffix != ".md":
            print("❌ --out は --dry-run --src と一緒のときだけ・本物の設計書以外の .md にだけ書けます")
            return 2
        return write(dest=out)
    if a.selftest:
        return selftest()
    if a.write:
        return write()
    if a.dry_run:
        return write(dry=True)
    if a.verify:
        return verify()
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
