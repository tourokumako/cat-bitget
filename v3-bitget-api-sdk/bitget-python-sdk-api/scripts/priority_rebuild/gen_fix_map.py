#!/usr/bin/env python3
"""gen_fix_map.py — 監査FBの修正対応表（fix_map）を機械生成する（まこさん承認 2026-07-30）。

なぜこの形か:
  CC が監査FBの修正リストを手書きすると、矮小化（項目を落とす・言い換えて弱める）と
  捏造（出典に無い定義を作る）が混ざる（2026-07-30 実例＝「決済のしかた4種」の縮め・
  閾値/パラメータの対応落ち＝まこさんが2件とも発見）。だから:
  ① 指摘の側（番号・見出し・核心の逐語）は本スクリプトが監査レポートから機械で抽出する
     ＝一覧が CC の手を経由しない＝落とす・弱めるが物理的にできない。
  ② CC が書くのは対応の json（engine_tuner_fix_map.json）だけ。生成時に
     (a) 監査の全指摘番号に対応が揃っているか（欠け・余りの両方向）
     (b) json が引く出典の逐語が、引いた先のファイルに実在するか
     を照合し、1件でも不一致なら md を生成せず止まる。
  ③ 出力 md はハッシュつき＝手で書き換えると --verify が検出する
     （gen_windows / gen_v9_exits / gen_engine_tuner_manual と同じ守り方・hook は増やさない）。

使い方:
  python3 gen_fix_map.py --write    # 照合して md を生成
  python3 gen_fix_map.py --verify   # md の改変検出（ハッシュ照合）
  python3 gen_fix_map.py --selftest # 番人＝わざと壊した入力で止まるか

限界（正直に）: 「対応」の中身が指摘の趣旨とずれていないかの意味判定は機械にはできない。
  ただし指摘の逐語が必ず対応の真横に並ぶので、ずれはまこさんが1行単位で見比べられる。
  出典 path="chat"（まこさんの発言）はファイル照合ができない＝「機械照合外」と明示する。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SUB = ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
AUDIT = SUB / ".claude/audits/2026-07-27_engine_tuner_r3r13r14_design_cp2_audit_report.md"
JSON_IN = SUB / ".claude/ratchet/engine_tuner_fix_map.json"
# ★GENERATES＝この道具が作る文書の名乗り（2026-08-16 新設・まこさん決定 A）。
#   なぜ要るか＝名前で数えると必ず漏れる（出力先の変数名が道具ごとにバラバラで、
#   読むファイルと作るファイルが同じ形で並んでいる＝外から見分けられない）。
#   だから道具の側に名乗らせる。集める道具＝gen_docmap.py。
#   形＝(リポジトリの根からのパス, "まるごと" か "一部の節")。
GENERATES = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_fix_map.md", "まるごと"),
]

MD_OUT = SUB / ".claude/ratchet/engine_tuner_fix_map.md"

HEAD_RE = re.compile(r"^#{3,4}\s+(?:不具合)?(\d+-\d+)\s*(.*)$")
GONKYO_RE = re.compile(r"^###\s+根拠(\d)\s*(.*)$")
SOKUTEI_RE = re.compile(r"^###\s+測定(\d)\s*(.*)$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def extract_findings(text: str) -> list[dict]:
    """監査レポートから指摘（ID・見出し・核心の逐語）を機械抽出する。CC の手を経由しない。"""
    lines = text.splitlines()
    found: list[dict] = []
    if any(l.startswith("## 1. 初版の撤回") for l in lines):
        found.append({"id": "撤回", "head": "初版の撤回", "at": next(
            i for i, l in enumerate(lines) if l.startswith("## 1. 初版の撤回"))})
    for i, l in enumerate(lines):
        m = HEAD_RE.match(l) or GONKYO_RE.match(l) or SOKUTEI_RE.match(l)
        if not m:
            continue
        if GONKYO_RE.match(l):
            fid, head = f"根拠{m.group(1)}", m.group(2)
        elif SOKUTEI_RE.match(l):
            fid, head = f"測定{m.group(1)}", m.group(2)
        else:
            fid, head = m.group(1), m.group(2)
        found.append({"id": fid, "head": head.strip(" —-"), "at": i})
    # 各指摘の核心の逐語＝見出しから次の見出しまでの間で、表・引用行を除く最初の太字（10字以上）
    for k, f in enumerate(found):
        end = found[k + 1]["at"] if k + 1 < len(found) else len(lines)
        quote = ""
        for l in lines[f["at"] + 1: end]:
            s = l.strip()
            if s.startswith("|") or s.startswith(">") or s.startswith("#"):
                continue
            for b in BOLD_RE.findall(s):
                if len(b) >= 10:
                    quote = b
                    break
            if quote:
                break
        f["quote"] = quote
    return found


def load_json() -> dict:
    return json.loads(JSON_IN.read_text(encoding="utf-8"))


def verify_sources(entries: list[dict]) -> list[str]:
    """json が引く出典の逐語が実在するかを照合。不一致の一覧を返す（空なら合格）。"""
    errs = []
    for e in entries:
        for s in e.get("出典", []):
            if s["path"] == "chat":
                continue
            p = ROOT / s["path"]
            if not p.exists():
                errs.append(f"{e['id']}: 出典ファイルが無い {s['path']}")
                continue
            if s["逐語"] not in p.read_text(encoding="utf-8", errors="replace"):
                errs.append(f"{e['id']}: 逐語が {s['path']} に実在しない: 「{s['逐語']}」")
    return errs


def build_md(findings: list[dict], data: dict) -> str:
    by_id = {e["id"]: e for e in data["entries"]}
    audit_ids = [f["id"] for f in findings]
    # 網羅の照合（欠け・余りの両方向）
    missing = [i for i in audit_ids if i not in by_id]
    extra = [i for i in by_id if i not in audit_ids]
    if missing:
        raise SystemExit(f"[網羅エラー] 監査の指摘に対応が無い: {missing}＝md を生成しない")
    if extra:
        raise SystemExit(f"[網羅エラー] 監査に無い番号が entries にある: {extra}（監査外は extra 節へ）")
    errs = verify_sources(data["entries"]) + verify_sources(data.get("extra", []))
    if errs:
        raise SystemExit("[出典エラー] 逐語の照合に失敗＝md を生成しない:\n  " + "\n  ".join(errs))
    # ★「行き先」が未定義の歩を指していないかの照合（2026-07-30 まこさん指摘
    #   「歩1とかの内容が生成されてないよね？」＝歩の定義がチャットにしか無かった穴を塞ぐ）
    step_ids = {s["id"] for s in data.get("steps", [])}
    used = set()
    for e in data["entries"] + data.get("extra", []):
        used.update(re.findall(r"歩\d", e.get("行き先", "")))
    undef = sorted(used - step_ids)
    if undef:
        raise SystemExit(f"[歩の定義エラー] 行き先が未定義の歩を指している: {undef}"
                         "＝json の steps に定義を足すこと（チャットの説明は定義にならない）")

    def _src_lines(e):
        out = []
        for s in e.get("出典", []):
            name = s["path"].split("/")[-1] if s["path"] != "chat" else "まこさんの発言（機械照合外）"
            out.append(f"  - {name}: 「{s['逐語']}」")
        return out

    L = []
    L.append("# engine_tuner 修正対応表（gen_fix_map.py が機械生成＝手書き禁止）")
    L.append("")
    L.append("このファイルは手で書き換えません。直すときは engine_tuner_fix_map.json を直して再生成します。")
    L.append("指摘の側は監査レポートから機械で抽出しています。私（CC）の手を経由していません。")
    L.append(f"監査の指摘 {len(audit_ids)} 件すべてに対応が付いています。欠けや余りがあると生成が止まります。")
    L.append("出典の逐語は、引用先のファイルに実在することを生成のたびに機械照合しています。")
    L.append("")
    L.append("```")
    L.append("python3 scripts/priority_rebuild/gen_fix_map.py --write   # 作り直す")
    L.append("python3 scripts/priority_rebuild/gen_fix_map.py --verify  # 改変の検出")
    L.append("```")
    L.append("")
    if data.get("premise"):
        L.append("## 前提（毎セッション有効・消さない・まこさん指示 2026-07-30）")
        L.append("")
        for p in data["premise"]:
            L.append(f"- {p}")
        L.append("")
    L.append("## まず全体を見る表（詳細は下の節にあります）")
    L.append("")
    L.append("| ID | 指摘（見出しだけ） | 行き先 | 状態 |")
    L.append("|---|---|---|---|")
    for f in findings:
        e = by_id[f["id"]]
        L.append(f"| {f['id']} | {f['head']} | {e.get('行き先', '—')} | {e.get('状態', '未着手')} |")
    for e in data.get("extra", []):
        L.append(f"| {e['id']} | {e.get('内容', '')} | {e.get('行き先', '—')} | {e.get('状態', '未着手')} |")
    L.append("")
    L.append("## 作り直しの歩（「行き先」の定義）")
    L.append("")
    L.append("下の表と節に出てくる「歩N」の定義です。順番は依存関係だけで決めています。")
    L.append("")
    L.append("| 歩 | 名前 | 何をするか | 検収のしかた | 状態 |")
    L.append("|---|---|---|---|---|")
    for s in data.get("steps", []):
        L.append(f"| {s['id']} | {s['title']} | {s['中身']} | {s.get('検収', '—')} | {s.get('状態', '未着手')} |")
    L.append("")
    L.append("## 監査の指摘と対応（1件ずつ）")
    for f in findings:
        e = by_id[f["id"]]
        L.append("")
        L.append(f"### {f['id']} — {f['head']}")
        L.append("")
        if f["quote"]:
            L.append(f"監査の言葉（機械抽出）: 「{f['quote']}」")
            L.append("")
        L.append(f"対応: {e['対応']}")
        srcs = _src_lines(e)
        if srcs:
            L.append("")
            L.append("出典:")
            L.extend(srcs)
        L.append("")
        L.append(f"行き先: {e.get('行き先', '—')} ／ 状態: {e.get('状態', '未着手')}")
    L.append("")
    L.append("## 監査外（まこさんの決定・照合で見つけた欠け）")
    for e in data.get("extra", []):
        L.append("")
        L.append(f"### {e['id']} — {e.get('内容', '')}")
        L.append("")
        L.append(f"対応: {e['対応']}")
        srcs = _src_lines(e)
        if srcs:
            L.append("")
            L.append("出典:")
            L.extend(srcs)
        L.append("")
        L.append(f"行き先: {e.get('行き先', '—')} ／ 状態: {e.get('状態', '未着手')}")
    L.append("")
    body = "\n".join(L) + "\n"
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return f"<!-- FIXMAP_HASH={h} -->\n" + body


def selftest() -> None:
    """番人＝わざと壊した入力で止まるか。"""
    findings = extract_findings(AUDIT.read_text(encoding="utf-8"))
    ids = {f["id"] for f in findings}
    need = {"撤回", "根拠1", "根拠2", "根拠3", "根拠4", "1-1", "1-2", "1-3", "1-4",
            "4-1", "4-7", "4-14", "4-20", "4-22", "4-23", "測定1", "測定2"}
    assert need <= ids, f"抽出漏れ: {need - ids}"
    data = load_json()
    # 番人1: 対応を1件抜く → 網羅エラーで止まるか
    broken = {"entries": data["entries"][1:], "extra": []}
    try:
        build_md(findings, broken)
        raise AssertionError("番人1 失敗: 対応の欠けで止まらなかった")
    except SystemExit as e:
        assert "網羅エラー" in str(e)
    # 番人2: 出典の逐語を捏造 → 出典エラーで止まるか
    import copy
    broken2 = copy.deepcopy(data)
    broken2["entries"][0].setdefault("出典", []).append(
        {"path": "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/entry_exit_matrix.md",
         "逐語": "この文字列は捏造であり実在しない9x7z"})
    try:
        build_md(findings, broken2)
        raise AssertionError("番人2 失敗: 捏造逐語で止まらなかった")
    except SystemExit as e:
        assert "出典エラー" in str(e)
    print(f"selftest OK（抽出 {len(findings)} 件・番人2/2 pass）")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--write"
    if mode == "--selftest":
        selftest()
        return
    if mode == "--verify":
        t = MD_OUT.read_text(encoding="utf-8")
        m = re.match(r"<!-- FIXMAP_HASH=([0-9a-f]+) -->\n", t)
        body = t[m.end():]
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        ok = m and m.group(1) == h
        print("verify OK（改変なし）" if ok else "⚠️ verify FAIL（手書きの改変あり＝再生成する）")
        sys.exit(0 if ok else 2)
    findings = extract_findings(AUDIT.read_text(encoding="utf-8"))
    md = build_md(findings, load_json())
    MD_OUT.write_text(md, encoding="utf-8")
    print(f"生成した: {MD_OUT}（監査の指摘 {len(findings)} 件・全件対応・逐語照合済み）")


if __name__ == "__main__":
    main()
