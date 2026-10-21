#!/usr/bin/env python3
"""pre_audit_check.py — 監査に出す前のチェックを、決まった順番で走らせて1枚に書く
（2026-09-06・まこさん指示「監査前チェックの物理化（部品1＝順番を守る道具／部品2＝依頼書を書く瞬間に止める hook）→これはやって」）

なぜ在るか:
  2026-09-05〜06 に監査を3回 出して3回とも NO-GO。cp23 の Critical は「作り直しの順番が逆」だった。
  部品が 573 → 555 に減る前に gen_materials.py --write を打ち、減った後に打ち直さずに監査へ出した。
  ★順番は CC の記憶の中にしか無く、依頼書も手で書けたので、機械が何も見ていなかった。
  だから ①順番をこのファイルに書き ②結果を1枚（json）に残し
  ③その1枚が無い・古い・rc が0でないなら監査依頼書を書けなくする（hook 側＝部品2）。

使い方:
  python3 .claude/tools/pre_audit_check.py --run       # 決まった順番で走らせ、結果を json に書く
  python3 .claude/tools/pre_audit_check.py --verify    # その json が在る・新しい・全部 rc=0 かを確かめる（違えば exit 1）
  python3 .claude/tools/pre_audit_check.py --selftest  # 番人 P1〜P8

決まり:
  ・順番は下の ORDER が正本。CC が走らせる順番を思い出す必要は無い。
  ・`--approve` が要るもの（型の表・出口の表）は、この道具が打たない。
    まこさんの承認が要るので、画面に出して止める（CC が承認を代行しない＝恒久の決まり57番）。
  ・json には「そのとき見ていたコードの指紋」を書く。チェックの後にコードを触ったら --verify が落ちる。

正直な限界:
  ・json は土台ゲートの対象外＝CC が手で書けば通る。ただし指紋も偽造する必要がある。
  ・この道具と hook を書き換えれば無効にできる（git diff には必ず出る）。
  ・依頼書を `.claude/audits/inputs/` の外に書けば通る（ただし監査の一覧に出ない）。
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PR = SDK / "scripts/priority_rebuild"
OUT = ROOT / ".claude/state/pre_audit_check.json"

# ── 作り直しの順番（この一覧が正本・設計書 §1 の表と1件も違わない）──────────────
#   kind="approve" ＝ まこさんの承認が要る＝この道具は打たない（画面に出して止める）
#   kind="run"     ＝ この道具が打つ
ORDER = [
    ("gen_signal_families.py --write", "approve",
     "部品の件数が確定する＝全部の出発点。--write のあと まこさんの --approve が要る"),
    ("gen_exit_families.py --write", "approve",
     "出口の表が型の表を読む。--write のあと まこさんの --approve が要る"),
    ("gen_indicator_switch.py --write", "run", "印が型の表を読む"),
    ("gen_materials.py --write", "run", "文書が 1〜3 を全部 読む"),
    ("gen_signal_families.py --verify", "run", "G2 の印（コードと表が固まってから）"),
    ("leak_causality_diag.py", "run", "H2 の印（最後）"),
]

# ── 最後に走らせる検査（全部 rc=0 でなければ監査に出せない）────────────────────
INDICATOR_SOURCES_CHECK = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/check_indicator_sources.py"
CHECKS = [
    "gen_materials.py --verify",
    "gen_materials.py --selftest",
    "gen_indicator_switch.py --verify",
    "gen_exit_families.py --verify",
    "engine_tuner_exec.py --selftest",
    "observe_diag.py --selftest",
    # ★2026-09-07（next_step §6 の145番・141番・設計書 iter="approval-audit-plumbing-20260907"）
    #   ＝赤のまま放置されていた2本を、監査の前に必ず走らせる。
    #   141番＝監査の依頼書を作るプログラムの自己テストが -4/11 のまま、cp24・cp25・cp26 と
    #     3回の監査をまたいでいた。この一覧に無いので、赤が画面に出なかった。
    #   145番＝2026-09-07 に足した別枠3種の審査のテスト（T33-g）を、毎回 走らせる所が無かった。
    #     （全体の --selftest は約6分半かかるので、その枝だけを数秒で走らせる口を使う）
    # ★2026-10-18（192回目・ToDo の52番・まこさん決定「１は外しても問題ないなら、外す」）＝gen_audit_request.py --selftest を外した。
    #   古い依頼書の道具（RG-v5 の監査専用・2026-09-29 から不使用）は退役。依頼書は gen_audit_docs.py だけが作る。
    #   外しても問題ない根拠＝凍結ファイルを読む物がほかに無い・P8 は _MUST_IN_CHECKS の各行が CHECKS に在るかだけを見る（記録 20261018 §26）。
    #   ★壊すプログラム b42 は、この行を探していた。b42 の探す行を ②（engine_tuner_gen）に替える直しは まこさんの手（breaks は承認の相手）。
    "engine_tuner_gen.py --selftest-extra-gate",
    # ★2026-09-27（監査 CP47 の Process）＝設計書の SPEC と実物の突き合わせ。実装の後に設計書の SPEC を作り直していないと、本走が設計↔実装ゲートで止まる（M2-E-4e で齟齬 6件のまま監査に出た）。
    "verify_design_contract.py --diff /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md",
    # ★2026-10-07（158回目・まこさん「とにかくすべて完璧に修正して。毎回チェックでミスがあり、やりなおしで膨大な時間がかかるのを改善してほしい」）
    #   ＝①「使う」の指標が資料の表3つに全部 在るか ②設定ファイルの資料から写した部分が、いまの資料から写し直したものと同じか。
    #   直す前は、どちらを見る検査も無く、RCI と前期間pivot の3種が資料に無いまま3日 気づかなかった。
    INDICATOR_SOURCES_CHECK,
    # ★2026-10-10（164回目・監査 CP70 の所見・next_step §6 の254番）＝組み立ての表（composition_rules.json）の照らし。
    #   直す前は、この一覧に無かったので、設定か型の表を変えた後に組み立ての表を作り直していなくても、
    #   チェックは全部 rc=0 になった（162回目に gen_composition_rules.py --write を飛ばした件が、監査 CP70 まで出なかった）。
    "gen_composition_rules.py --verify",
]
# ★この3行が消されたら番人 P8 が落ちる（一覧から黙って外せなくする・145番・2026-10-07 の照らし・254番）
#   ★2026-10-18＝141番の gen_audit_request.py --selftest は、古い道具の退役で外した（上の CHECKS の注記）。
_MUST_IN_CHECKS = ("engine_tuner_gen.py --selftest-extra-gate",
                   INDICATOR_SOURCES_CHECK,
                   "gen_composition_rules.py --verify")

# ── 指紋の対象（このどれかが変わったら、チェックはやり直し）────────────────────
FINGERPRINT_FILES = [
    "observe_diag.py", "indicator_reference_diag.py", "observe_config.json",
    "gen_signal_families.py", "gen_indicator_switch.py", "gen_materials.py",
    "gen_exit_families.py", "engine_tuner_gen.py", "engine_tuner_exec.py",
    # ★照らしの道具（check_indicator_sources.py）が読む相手も指紋に入れる＝--run の後に設定・資料・写し方が変われば --verify が止める
    "recipes/search_limits.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_params_review.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_params_by_strategy.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_roles_thresholds.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indicator_switch.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_review/r3_draft_build.py",
]


def code_fingerprint() -> str:
    """いま見ているコードの指紋（H2 の印と同じ考え方＝中身から作る）。"""
    h = hashlib.sha256()
    for name in FINGERPRINT_FILES:
        p = PR / name
        h.update(name.encode())
        h.update(p.read_bytes() if p.exists() else b"<no file>")
    return h.hexdigest()


def _run(cmd: str) -> int:
    """scripts/priority_rebuild の .py を1本 走らせて終了コードを返す。
    ★2026-10-07＝名前が / で始まるものは、その絶対パスの道具を走らせる（.claude/tools の照らしの道具を CHECKS に置くため）。"""
    parts = cmd.split()
    r = subprocess.run([sys.executable, parts[0] if parts[0].startswith("/") else str(PR / parts[0])] + parts[1:],
                       cwd=str(SDK), capture_output=True, text=True)
    return int(r.returncode)


# ★2026-10-20（196回目・まこさん「OK」）＝照らす設計書を選べる旗 --design。
#   なぜ＝一覧の「設計書と実物の照合」が acceptance.md に決め打ちで、前の工事（承認の控え）の監査の依頼書を作るとき、
#   その工事と関係の無い いまの設計書を照らして落ちた（K-4 の実装の監査・記録 20261020 §12）。
#   旗が無いときは今までどおり acceptance.md。照らした設計書は記録に書き、--verify で問われた設計書と同じかを見る。
DESIGN_DIFF = "verify_design_contract.py --diff "
DEFAULT_DESIGN = str(ROOT / ".claude/state/acceptance.md")


def checks_for(design: str | None = None) -> list:
    """CHECKS のうち、設計書と実物の照合の行だけを、渡された設計書に替えた一覧。"""
    d = os.path.abspath(design) if design else DEFAULT_DESIGN
    return [DESIGN_DIFF + d if c.startswith(DESIGN_DIFF) else c for c in CHECKS]


# ★2026-10-20（196回目・まこさん決定「B」）＝分かっている食い違い。rc≠0 で、出力（標準出力＋標準エラー）のハッシュ値が
#   ここと1文字も同じときだけ、記録の行に known の印を付け、--verify は止めない。出力が違えば（新しい食い違い）今までどおり止める。
#   直して rc=0 になれば、この行は使われなくなる（そのときは消してよい）。
KNOWN_NG = {
    INDICATOR_SOURCES_CHECK: dict(
        # ★2026-10-21（工事 m2c15-band-s1-20261020 の実装の後・まこさん「OK」）＝出力が設計書 4-12 の見込みどおりに変わったので取り直した。
        #   直す前＝sha 13c462ef…（material_params の42行だけ・まこさん「B」2026-10-20・K-4 の実装の監査の依頼書を作るため・記録 20261020 §13）
        sha="222dadd4f4ee492802b52183bea5c0efb34c549d870e056f23a89f7303c813c5",
        why="②observe_config.json の material_params が、いまの資料の表から写し直した物と44行違う（10-18 の22番で資料の表の代表の値を"
            "1つにした後、material を作り直していない42行と、工事 m2c15-band-s1-20261020 で足した LeeMykland・LeeMykland_E36版 の2行）。"
            "search_limits.json の material_param_ranges が10行違う（同じ工事の新しい10種の範囲＝設計書の 4-9 で、範囲の表には書かないと"
            "決めた分）。next_step の あとで直すこと①・P-6・P-7 で直す",
        ok="まこさん「OK」（2026-10-21・B-1＋S-1 の実装の監査の依頼書を作るため・記録 20261021）"),
}


def _run_out(cmd: str) -> tuple:
    """_run と同じ走らせ方で、(終了コード, 標準出力＋標準エラー) を返す（分かっている食い違いの照らし用）。"""
    parts = cmd.split()
    r = subprocess.run([sys.executable, parts[0] if parts[0].startswith("/") else str(PR / parts[0])] + parts[1:],
                       cwd=str(SDK), capture_output=True, text=True)
    return int(r.returncode), (r.stdout or "") + (r.stderr or "")


def known_ng(cmd: str, rc: int, out: str) -> bool:
    """rc≠0 で、出力のハッシュ値が KNOWN_NG と同じか。"""
    k = KNOWN_NG.get(cmd)
    return bool(k) and rc != 0 and hashlib.sha256(out.encode("utf-8")).hexdigest() == k["sha"]


def run(design: str | None = None) -> int:
    """決まった順番で走らせ、結果を json に書く。"""
    rows = []
    print("=" * 70)
    print("監査に出す前のチェック（決まった順番で走らせます）")
    print("=" * 70)
    for cmd, kind, why in ORDER:
        if kind == "approve":
            print(f"  ⏸ {cmd}")
            print(f"     {why}")
            print("     ★この道具は打ちません。まこさんが次を打ってください:")
            print(f"       cd {SDK}")
            print(f"       python3 scripts/priority_rebuild/{cmd}")
            print(f"       python3 scripts/priority_rebuild/{cmd.split()[0]} --approve")
            rows.append(dict(cmd=cmd, kind=kind, rc=None, note="まこさんの承認が要る"))
            continue
        t0 = time.time()
        rc = _run(cmd)
        print(f"  {'OK' if rc == 0 else 'NG'} {cmd}  rc={rc}（{time.time() - t0:.1f}秒）")
        rows.append(dict(cmd=cmd, kind=kind, rc=rc, note=why))
    print("-" * 70)
    for cmd in checks_for(design):
        t0 = time.time()
        if cmd in KNOWN_NG:
            rc, out = _run_out(cmd)
            if known_ng(cmd, rc, out):
                print(f"  既知 {cmd}  rc={rc}（{time.time() - t0:.1f}秒）＝分かっている食い違い（出力が同じ）: {KNOWN_NG[cmd]['why']}")
                rows.append(dict(cmd=cmd, kind="check", rc=rc, known=True,
                                 note=f"分かっている食い違い（{KNOWN_NG[cmd]['why']}・{KNOWN_NG[cmd]['ok']}）"))
                continue
        else:
            rc = _run(cmd)
        print(f"  {'OK' if rc == 0 else 'NG'} {cmd}  rc={rc}（{time.time() - t0:.1f}秒）")
        rows.append(dict(cmd=cmd, kind="check", rc=rc, note="監査に出す前の検査"))
    data = dict(_これは何か="監査に出す前のチェックの結果（pre_audit_check.py が書く＝手で書き換えない）",
                at=time.strftime("%Y-%m-%d %H:%M:%S"), fingerprint=code_fingerprint(),
                design=os.path.abspath(design) if design else DEFAULT_DESIGN, rows=rows)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[作成] {OUT}（指紋 {data['fingerprint'][:16]}…）")
    ng = [r for r in rows if r.get("rc") not in (0, None) and not r.get("known")]
    waiting = [r for r in rows if r.get("rc") is None]
    if ng:
        print(f"NG rc が0でないもの {len(ng)} 件＝このままでは監査に出せません")
        return 1
    if waiting:
        print(f"⏸ まこさんの承認を待つもの {len(waiting)} 件")
    print("全部 rc=0")
    return 0


# ★2026-09-06（設計書 iter="pac-approve-detect-20260906"）＝まこさんが --approve を打ったかを、
#   承認の印のファイルで確かめる。
#   直す前＝「rc が None かつ種類が approve なら、承認が済んでいない」だけを見ていた。
#   rc が None になるのは **CC がその2本を打たないから**で、まこさんが打っても None のまま
#   ＝`--verify` が毎回「監査に出せません」を返した（2026-09-06 に実測）。
#   形＝{その道具のコマンド: (承認の印のファイル名, 対応する照合のコマンド)}
_APPROVE_MARK = {
    "gen_signal_families.py --write": ("signal_families_approved.txt",
                                       "gen_signal_families.py --verify"),
    "gen_exit_families.py --write": ("exit_families_approved.txt",
                                     "gen_exit_families.py --verify"),
}


def approve_problem(cmd: str, rows: list) -> str | None:
    """まこさんの承認が済んでいるか。戻り＝問題の説明（済んでいれば None）。

    ★見るのは2つだけ＝①承認の印のファイルが在るか ②対応する照合が rc=0 か。
    ★限界（正直に）＝印そのものを手で作る道は残る／誰が打ったかは区別できない。
    """
    mark, vcmd = _APPROVE_MARK.get(cmd, (None, None))
    if mark is None:
        return f"承認の印の在りかを知らない道具です: {cmd}（_APPROVE_MARK に足す）"
    p = SDK / ".claude" / "ratchet" / mark
    if not p.exists():
        return (f"まこさんの承認の印がありません: {mark}"
                f"（{cmd} のあと --approve を打つ）")
    rc = next((r.get("rc") for r in rows if r.get("cmd") == vcmd), None)
    if rc != 0:
        return f"承認の印は在りますが、照合が通っていません: {vcmd}（rc={rc}）"
    return None


def verify_problems(design: str | None = None, before_impl: bool = False) -> list[str]:
    """監査に出せる状態かを確かめる。1件でも返れば出せない。design＝問われた設計書（無ければ acceptance.md）。"""
    if not OUT.exists():
        return [f"チェックの1枚が無い（{OUT.name}）＝ python3 .claude/tools/pre_audit_check.py --run を打つ"]
    try:
        d = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception as e:                                    # noqa: BLE001
        return [f"チェックの1枚が読めない: {str(e)[:60]}"]
    ng = []
    if d.get("fingerprint") != code_fingerprint():
        ng.append("チェックの後にコードが変わっている（指紋の不一致）＝ --run をもう一度 打つ")
    # ★2026-10-20＝チェックが照らした設計書が、問われた設計書と同じか（記録に名前が無い前の記録は acceptance.md と読む）
    want = os.path.abspath(design) if design else DEFAULT_DESIGN
    got = d.get("design") or DEFAULT_DESIGN
    if got != want:
        ng.append(f"チェックが照らした設計書が違う（照らした {got} ／ 問われた {want}）＝ --run --design {want} を打つ")
    for r in (d.get("rows") or []):
        # ★2026-10-20（199回目・まこさん「OK」）＝設計書の監査（実装の前）は、設計書と実物の照合の行だけを見ない
        #   （設計書に書いた新しい関数が、実装の前なので まだ実物に無く、必ず落ちるため）。実装の監査では今までどおり見る。
        if before_impl and str(r.get("cmd") or "").startswith(DESIGN_DIFF):
            continue
        # ★2026-10-20＝分かっている食い違い（run が出力のハッシュ値で照らして印を付けた行）は止めない。一覧に無い道具の印は認めない
        if r.get("rc") not in (0, None) and not (r.get("known") and r.get("cmd") in KNOWN_NG):
            ng.append(f"rc が0でない: {r.get('cmd')}（rc={r.get('rc')}）")
        if r.get("rc") is None and r.get("kind") == "approve":
            # ★2026-09-06＝承認の印を見る（直す前は、打っても打たなくても止めていた）
            x = approve_problem(str(r.get("cmd")), d.get("rows") or [])
            if x:
                ng.append(x)
    return ng


def verify(design: str | None = None, before_impl: bool = False) -> int:
    ng = verify_problems(design, before_impl)
    if ng:
        print("監査に出せません:")
        for x in ng:
            print(f"   ・{x}")
        return 1
    print("監査に出せます（チェックの1枚が新しく、全部 rc=0）")
    return 0


def selftest() -> int:
    """番人 P1〜P8（設計書 §4。P8 は 2026-09-07・145番・141番で足した）。"""
    ng = []
    keep = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    fp = code_fingerprint()
    ok_json = json.dumps(dict(fingerprint=fp, rows=[
        dict(cmd="gen_materials.py --verify", kind="check", rc=0)]), ensure_ascii=False)
    try:
        # P1 1枚が無い
        if OUT.exists():
            OUT.unlink()
        if not any("1枚が無い" in x for x in verify_problems()):
            ng.append("P1: チェックの1枚が無いのに通る")
        # P2 rc が0でない行が在る＝落ちた検査の名前が出る
        OUT.write_text(json.dumps(dict(fingerprint=fp, rows=[
            dict(cmd="gen_materials.py --verify", kind="check", rc=1)]), ensure_ascii=False),
            encoding="utf-8")
        if not any("gen_materials.py --verify" in x for x in verify_problems()):
            ng.append("P2: rc が0でないのに通る／落ちた検査の名前が出ない")
        # P3 指紋が違う
        OUT.write_text(json.dumps(dict(fingerprint="0" * 64, rows=[
            dict(cmd="gen_materials.py --verify", kind="check", rc=0)]), ensure_ascii=False),
            encoding="utf-8")
        if not any("コードが変わっている" in x for x in verify_problems()):
            ng.append("P3: 指紋が違うのに通る")
        # P4 全部そろっている
        OUT.write_text(ok_json, encoding="utf-8")
        if verify_problems():
            ng.append(f"P4: 全部そろっているのに落ちる: {verify_problems()}")
        # P5 順番の一覧が設計書の表と一致する
        want = ["gen_signal_families.py --write", "gen_exit_families.py --write",
                "gen_indicator_switch.py --write", "gen_materials.py --write",
                "gen_signal_families.py --verify", "leak_causality_diag.py"]
        if [c for c, _k, _w in ORDER] != want:
            ng.append(f"P5: 順番の一覧が設計書の表と違う: {[c for c, _k, _w in ORDER]}")
        # ★P8（2026-09-07・next_step §6 の145番・141番）
        #   ＝監査の前に必ず走らせる2本が、一覧（CHECKS）から消されていないか。
        #   なぜ要るか＝この2本は「赤が画面に出ない」ことが問題だった。
        #     一覧から黙って外せば、また出なくなる。だから外したら番人が落ちる形にする。
        for _m in _MUST_IN_CHECKS:
            if _m not in CHECKS:
                ng.append(f"P8: 監査の前に走らせる一覧から外されている: {_m}")
        # ★P9（2026-10-20）＝照らした設計書が問われた設計書と違えば止まり、同じなら通る。一覧の照合の行だけが替わる
        _other = str(ROOT / ".claude/state/_selftest_other_design.md")
        OUT.write_text(ok_json, encoding="utf-8")            # 記録に設計書の名前が無い＝acceptance.md を照らした記録
        if not any("照らした設計書が違う" in x for x in verify_problems(_other)):
            ng.append("P9-1: 照らした設計書が問われた設計書と違うのに通る")
        OUT.write_text(json.dumps(dict(fingerprint=fp, design=_other, rows=[
            dict(cmd="gen_materials.py --verify", kind="check", rc=0)]), ensure_ascii=False), encoding="utf-8")
        if verify_problems(_other):
            ng.append(f"P9-2: 同じ設計書を照らした記録なのに落ちる: {verify_problems(_other)}")
        if not any("照らした設計書が違う" in x for x in verify_problems()):
            ng.append("P9-3: 別の設計書を照らした記録で、acceptance.md を問うと通る")
        _cf = checks_for(_other)
        if (len(_cf) != len(CHECKS) or DESIGN_DIFF + _other not in _cf
                or [c for c in _cf if not c.startswith(DESIGN_DIFF)] != [c for c in CHECKS if not c.startswith(DESIGN_DIFF)]):
            ng.append("P9-4: 一覧の照合の行のほかが替わった／照合の行が替わらない")
        # ★P10（2026-10-20・まこさん「B」）＝分かっている食い違いは、出力のハッシュ値が同じときだけ印が付き、--verify は止めない。
        #   出力が違えば印は付かない。一覧に無い道具の行に印が在っても、--verify は止める。
        _kc = INDICATOR_SOURCES_CHECK
        _ko = "見本の出力"
        _saved_k = dict(KNOWN_NG[_kc])
        KNOWN_NG[_kc]["sha"] = hashlib.sha256(_ko.encode("utf-8")).hexdigest()
        try:
            if not known_ng(_kc, 1, _ko):
                ng.append("P10-1: 出力のハッシュ値が同じなのに、分かっている食い違いと見ない")
            if known_ng(_kc, 1, _ko + "（1行 違う）"):
                ng.append("P10-2: 出力が違うのに、分かっている食い違いと見る")
            if known_ng(_kc, 0, _ko) or known_ng("gen_materials.py --verify", 1, _ko):
                ng.append("P10-3: rc=0 か一覧に無い道具なのに、分かっている食い違いと見る")
        finally:
            KNOWN_NG[_kc] = _saved_k
        OUT.write_text(json.dumps(dict(fingerprint=fp, rows=[dict(cmd=_kc, kind="check", rc=1, known=True)]),
                                  ensure_ascii=False), encoding="utf-8")
        if verify_problems():
            ng.append(f"P10-4: 印の付いた分かっている食い違いの行で止まる: {verify_problems()}")
        OUT.write_text(json.dumps(dict(fingerprint=fp, rows=[dict(cmd="gen_materials.py --verify", kind="check", rc=1, known=True)]),
                                  ensure_ascii=False), encoding="utf-8")
        if not any("gen_materials.py --verify" in x for x in verify_problems()):
            ng.append("P10-5: 一覧に無い道具の行に印が在ると通る")
        # P6（実経路）hook を呼ぶ＝依頼書の Write が止まるか／この判定で止まらないか
        hook = ROOT / ".claude/hooks/require_acceptance_before_impl.sh"
        inp = json.dumps(dict(tool_name="Write", tool_input=dict(
            # ★名前の頭に下線を付けない（2026-09-07・141番）。
            #   依頼書ゲートは `.claude/audits/inputs/_*.md`（凍結ファイル・テンプレ）を
            #   相手にしない形に直したので、下線で始めると番人が素通りする。
            file_path=str(ROOT / ".claude/audits/inputs/selftest_dummy.md"), content="x")))
        OUT.write_text(json.dumps(dict(fingerprint="0" * 64, rows=[]), ensure_ascii=False),
                       encoding="utf-8")
        r_bad = subprocess.run(["bash", str(hook)], input=inp, capture_output=True, text=True)
        if r_bad.returncode != 2 or "監査に出す前のチェック" not in (r_bad.stderr or ""):
            ng.append(f"P6-1: チェックが落ちているのに止まらない（rc={r_bad.returncode}）")
        OUT.write_text(ok_json, encoding="utf-8")
        r_ok = subprocess.run(["bash", str(hook)], input=inp, capture_output=True, text=True)
        if "監査に出す前のチェック" in (r_ok.stderr or ""):
            ng.append("P6-2: チェックが通っているのに、この判定で止められる")
        # ── P7（実経路）設計書ゲートを「2群とも」呼んでいるか ──
        #   まこさん指摘 2026-09-06「残り２本って何？なんでさっきの修正で全部やってない？」。
        #   ★なぜ群を分けるか＝呼び方が違う。群1 は「実装ファイルを書く瞬間」に走るので
        #     file_path に TARGET を入れる。群2 は「設計書そのものを書く瞬間」に走るので
        #     file_path の名前が acceptance.md でないと発火しない（中身は content から読む）。
        #   直す前は群2 に TARGET の file_path を渡していた＝一度も動いていなかった
        #     （壊した設計書を渡しても「不足0件」で通ることを実測した）。
        import contextlib
        import io
        import tempfile
        _t = pathlib.Path(tempfile.mkdtemp())
        # P7-1 群1＝設計書の形（DESIGN_CONTRACT に no_impl_functions_reason が無い見本）
        _b1 = _t / "a1.md"
        _b1.write_text(
            "TARGET: .claude/tools/pre_audit_check.py\n\n## 完成の条件\n\n## DESIGN_CONTRACT\n\n"
            '```json\n{"impl_file": ".claude/tools/pre_audit_check.py", "impl_functions": {},\n'
            ' "self_check_calls": [], "must_use": {}, "spec_lists": {}}\n```\n', encoding="utf-8")
        _o1 = io.StringIO()
        with contextlib.redirect_stdout(_o1):
            _rc1 = check_design(str(_b1))
        if _rc1 == 0 or "require_acceptance_before_impl.sh" not in _o1.getvalue():
            ng.append("P7-1: 設計書の形の判定（DESIGN_CONTRACT ほか）を呼んでいない")
        # P7-2 群2＝正本を Read tool で開いたか（手本を開いていない見本）
        _b2 = _t / "a2.md"
        _b2.write_text(
            "TARGET: scripts/priority_rebuild/番人の見本.py\n\n"
            "NEW_FILE: scripts/priority_rebuild/番人の見本.py\n\n"
            "MODEL: scripts/priority_rebuild/この手本は開いていません.py\n", encoding="utf-8")
        _o2 = io.StringIO()
        with contextlib.redirect_stdout(_o2):
            _rc2 = check_design(str(_b2))
        if _rc2 == 0 or "require_source_read_before_acceptance.sh" not in _o2.getvalue():
            ng.append("P7-2: 必読ゲート（正本を開いたか）を呼んでいない")
    finally:
        if keep is not None:
            OUT.write_text(keep, encoding="utf-8")
        elif OUT.exists():
            OUT.unlink()
    print("=" * 70)
    print("pre_audit_check 自己検査（番人 P1〜P10）")
    print("=" * 70)
    for x in ng:
        print(f"  NG {x}")
    print(f"  NG {len(ng)} 件" if ng else "  全部 pass")
    return 1 if ng else 0


def design_hooks() -> list:
    """設計書を書く瞬間に走る hook を settings.json から機械で集める（2026-09-06）。

    ★なぜ手で並べないか＝まこさん指摘「ほかにもヌケモレないのか調べろ」。
      直す前は CC が「今日 自分を止めた3本」を手で書いていた＝思い出せた範囲しか覆えない。
      実測＝設計書（acceptance.md）を名指しする hook は 25本 在り、3本では足りなかった。
    ★集め方＝settings.json の PreToolUse のうち、matcher が Write か Edit のものに登録された .sh 全部。
      関係のない hook は自分で「対象外」と判断して通すので、呼んでも害はない。
    """
    import re
    s = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
    out = []
    for grp in s.get("hooks", {}).get("PreToolUse", []):
        if not re.search(r"Write|Edit", grp.get("matcher", "") or ""):
            continue
        for h in grp.get("hooks", []):
            for tok in re.findall(r"[\w./-]+\.sh", h.get("command", "") or ""):
                p = ROOT / ".claude/hooks" / pathlib.Path(tok).name
                if p.exists() and str(p) not in out:
                    out.append(str(p))
    return out


_SHAPE_WHY = ("Claude Code だけが持つ情報（セッションの id）が、この呼び方では渡せないため。"
              "設計書の中身の問題ではない＝本物の Write のときは、この hook が普通に効く")


def _input_shape_miss(out: str) -> bool:
    """hook が「入力の形が足りない」で落ちたか（2026-09-06）。

    ★なぜ要るか＝ここは本物の Write ではないので、Claude Code だけが持つ情報
      （session_id・transcript_path）を渡せない。それで落ちた分を「設計書の不足」と数えると、
      設計書を直しても消えない ❌ が毎回 出て、まこさんが直せない指摘になる。
    ★★選り分けではない＝落ちた事実は画面に出す（見送りとして必ず1行 出す）。
      数に入れないだけで、隠さない。
    """
    return ("セッションの id が hook の入力に無い" in out
            or "session_id も transcript_path も無い" in out)


def check_design(md: str | None = None) -> int:
    """設計書ゲートの全判定を、いまの設計書に当てて不足を全部 出す（2026-09-06）。

    ★なぜこの道具から呼ぶか＝土台ゲートが `bash <hook>` を止めるので、CC は hook を直に打てない。
      python は「通してよい道具」の一覧（_TOOL_OK_J）に在るので、ここから呼べば打てる。
    ★判定は hook 本体の --check を呼ぶ＝同じ判定を2か所に書き写さない。
    """
    md = md or str(ROOT / ".claude/state/acceptance.md")
    p = pathlib.Path(md)
    if not p.exists():
        print(f"設計書が見つかりません: {md}")
        return 1
    # ★TARGET を全部 試す。理由＝hook の判定は「何を書こうとしているか」で分かれる。
    #   TARGET の1本目だけを試すと、それが .sh のときは DESIGN_CONTRACT の検査に入らず、
    #   何も見ないまま「通った」と出る（2026-09-06 に実測して気づいた）。
    tline = ""
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.startswith("TARGET:"):
            tline = ln[len("TARGET:"):]
            break
    targets = [t.strip() for t in tline.split(",") if t.strip()]
    if not targets:
        print("設計書に TARGET: の行がありません")
        return 1
    # ★設計書を書く瞬間に止める hook を「全部」呼ぶ（2026-09-06・まこさん指摘「なんでさっきの
    #   修正で全部やってない？」）。直す前は1本目だけを呼び、私が「全判定」と言った範囲が
    #   自分の思いつきの範囲になっていた（今日 止まった3本のうち1本しか覆えていなかった）。
    #   ★この一覧は「今日 実際に私を止めた hook」から作った＝思いつきで選んでいない。
    #
    # ★hook は2群に分かれる。呼び方が違うので、まとめて呼ぶと片方が発火しない
    #   （2026-09-06 に実測＝壊した見本を渡したのに「不足0件」で通った）。
    #   群1＝「実装ファイルを書く瞬間」に走る＝file_path に TARGET を入れる。
    #   群2＝「設計書そのものを書く瞬間」に走る＝file_path の名前が acceptance.md でないと発火しない。
    #        中身は tool_input の content から読む（実物のファイルは読まない）＝見本をそこに入れる。
    ng, seen, notes = 0, [], []
    body = p.read_text(encoding="utf-8")

    # ── 群1＝実装ファイルを書く瞬間の判定（TARGET を全部 試す）──
    #   ★群1 も手で並べない（2026-09-06・群2 と同じ直し）。実装ファイルを書く瞬間に走る hook は
    #     require_acceptance_before_impl だけではない（固定値スイープ・計器の必読・目的ゲート ほか）。
    hooks = design_hooks()
    if not hooks:
        # fail-closed＝一覧が空のまま「不足0件」と出すと、何も見ずに通ったのと同じになる
        print("設計書ゲートの一覧が空です（settings.json を読めていません）＝判定できません")
        return 1
    g1_abs = str(ROOT / ".claude/hooks/require_acceptance_before_impl.sh")
    for t in targets:
        abs_t = t if t.startswith("/") else str(ROOT / t)
        inp = json.dumps(dict(tool_name="Write", tool_input=dict(file_path=abs_t, content="")))
        for hp_s in hooks:
            hp = pathlib.Path(hp_s)
            why = hp.name
            if not hp.exists():
                seen.append(f"── {hp_s} が見つかりません（{why}）")
                ng += 1
                continue
            # ★--check-md で「どの設計書を見るか」を渡す（渡さないと hook は本物の acceptance.md を
            #   見る＝壊した見本を渡しても通ってしまう。2026-09-06 に実測して気づいた）。
            #   この口を持つのは require_acceptance_before_impl だけ＝ほかは付けずに呼ぶ。
            r = subprocess.run(["bash", hp_s] + (["--check-md", md] if hp_s == g1_abs else []),
                               input=inp, capture_output=True, text=True)
            out = (r.stderr or "") + (r.stdout or "")
            # 承認そのものの2件は対象外（これから承認をお願いする前に打つ道具だから）
            if "未承認です" in out or "承認後に変更されています" in out:
                continue
            if _input_shape_miss(out):
                notes.append(f"（見送り）{why}＝{_SHAPE_WHY}")
                continue
            if r.returncode != 0:
                ng += 1
                seen.append(f"── {t} を書こうとしたとき ／ {why} ──\n{out.strip()}")

    # ── 群2＝設計書そのものを書く瞬間の判定（1回だけ・中身を content で渡す）──
    #   ★一覧は settings.json から機械で集める＝CC が手で選ばない（design_hooks の説明を参照）。
    g2 = [(h, pathlib.Path(h).name) for h in hooks if h != g1_abs]
    inp2 = json.dumps(dict(tool_name="Write", tool_input=dict(
        file_path=str(ROOT / ".claude/state/acceptance.md"), content=body)))
    for hrel, why in g2:
        hp = pathlib.Path(hrel)
        if not hp.exists():
            seen.append(f"── {hrel} が見つかりません（{why}）")
            ng += 1
            continue
        r = subprocess.run(["bash", str(hp)], input=inp2, capture_output=True, text=True)
        out = (r.stderr or "") + (r.stdout or "")
        if "未承認です" in out or "承認後に変更されています" in out:
            continue
        if _input_shape_miss(out):
            notes.append(f"（見送り）{why}＝{_SHAPE_WHY}")
            continue
        if r.returncode != 0:
            ng += 1
            seen.append(f"── 設計書を書こうとしたとき ／ {why} ──\n{out.strip()}")
    tail = f"（TARGET {len(targets)} 本 × 群1 {len(hooks)} 本 ／ 群2 {len(g2)} 本を全部 試しました）"
    if ng:
        print(f"設計書に不足が {ng} 件あります{tail}:")
        for s in seen:
            print(s)
    else:
        print(f"設計書の中身は通ります（不足0件）{tail}。")
        print(f"   見た設計書: {md}")
    for n in dict.fromkeys(notes):
        print(f"   {n}")
    return 1 if ng else 0


def main() -> int:
    a = sys.argv[1:]
    if "--check-design" in a:
        i = a.index("--check-design")
        return check_design(a[i + 1] if len(a) > i + 1 else None)
    _dz = a[a.index("--design") + 1] if "--design" in a and len(a) > a.index("--design") + 1 else None
    if _dz and not os.path.isfile(_dz):
        print(f"❌ --design の設計書が無い: {_dz}")
        return 2
    if "--run" in a:
        return run(_dz)
    if "--verify" in a:
        return verify(_dz, "--before-impl" in a)
    if "--check-indicator-sources" in a:
        # ★2026-10-07＝照らしの道具だけを走らせる口（工事の始め・資料を足した直後に、9分の全部を待たずに確かめる）。
        #   この道具は土台ゲートの「走らせてよい道具」の一覧に在るので、ここから呼べば Bash から打てる。
        #   --only-1（①だけ）と --selftest（照らしの道具の自己テスト）は、そのまま渡す＝この道具の --selftest より先に見る。
        return subprocess.run([sys.executable, INDICATOR_SOURCES_CHECK] + [x for x in a if x in ("--only-1", "--selftest")]).returncode
    if "--known-hash" in a:
        # ★2026-10-20＝分かっている食い違いの道具を、--run と同じ走らせ方で1回 走らせ、出力のハッシュ値と、一覧の値と同じかを出す（書かない）
        for cmd in KNOWN_NG:
            rc, out = _run_out(cmd)
            print(f"{cmd}  rc={rc}  sha={hashlib.sha256(out.encode('utf-8')).hexdigest()}  一覧と同じ={known_ng(cmd, rc, out)}")
        return 0
    if "--selftest" in a:
        return selftest()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
