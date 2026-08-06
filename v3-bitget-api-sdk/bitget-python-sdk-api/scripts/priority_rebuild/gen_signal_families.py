#!/usr/bin/env python3
"""gen_signal_families.py — 型の表（許可の一覧）の自動生成（CP4 監査フィードバック①・2026-08-06）

まこさん確定の作り（2026-08-06 逐語準拠）:
  表の本体＝カタログ105種×8時間足＋軸カタログから機械で広く展開する（V9 は使わない）。
  削る＝「方向」の欄から機械生成した禁止（向きの矛盾）などで、無意味な組み合わせだけ消す。
  試験＝できた表に V9 の実物の組み合わせが入っているかを機械で照合する（入っていなければ表が不合格）。

★すべて自動生成（まこさん指示「極力自動生成で作れ」「すべて自動生成でつくれ」）:
  - 表の本体・禁止の規則・出典は、全部このスクリプトが機械で作る。CC の作文の行はゼロ。
  - 機械で導けない決まりは、作らずに「空欄・まこさんの判断待ち」として表に明示する（根拠の無い行を書かない）。
  - 出力は決定論（同じ入力から2回作って md5 が一致）。--verify が手の改変を検出する。

このスクリプトがやらないこと: 売買しない・値を選ばない・採点しない・engine_tuner 系のコードに触れない。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path.insert(0, str(HERE))

import indicator_reference_diag as iref                     # noqa: E402（方向の欄・系統＝②で検査済み）

MATRIX_MD = SDK / ".claude/ratchet/entry_exit_matrix.md"    # 軸カタログの正本（E-a シグナル家族）
LIMITS_JSON = HERE / "recipes/search_limits.json"           # n_min=30（まこさん OK 2026-08-01「たたき台でOK」）
OUT_JSON = SDK / ".claude/ratchet/signal_families.json"     # 型の表（機械可読・G2 判定器が読む）
OUT_MD = SDK / ".claude/ratchet/signal_families.md"         # 型の表（人が読む・同じ中身）

# 値決め窓の日数（periods.py 正本から機械で取る＝手打ちしない）
from periods import SEARCH_START, SEARCH_END                # noqa: E402


def _catalog():
    """部品の一覧＝observe_diag のカタログ（②の材料検査で検証済み）から機械抽出。"""
    import importlib.util as iu
    spec = iu.spec_from_file_location("od", HERE / "observe_diag.py")
    od = iu.module_from_spec(spec)
    spec.loader.exec_module(od)
    cfg = od.load_config(None)
    names = [nm for nm, _f, _d in od.build_catalog(cfg)]
    tfs = list(cfg["timeframes"])
    return names, tfs


def _families_ea() -> list[dict]:
    """型の一覧＝軸カタログ（entry_exit_matrix.md の E-a 行）から機械抽出。"""
    text = MATRIX_MD.read_text(encoding="utf-8")
    m = re.search(r"\*\*E-a シグナル家族（何を取るか・[^*]*\*\*:\s*(.+)", text)
    if not m:
        raise SystemExit("[生成エラー] entry_exit_matrix.md に E-a シグナル家族の行が見つからない")
    line = m.group(1)
    fams = []
    for chunk in re.split(r"\s*/\s*(?=\(\d\))", line):       # 区切りは「 / (数字)」＝型名の中の / では切らない
        mm = re.match(r"\((\d)\)\s*(.+)", chunk.strip())
        if mm:
            fams.append(dict(id=f"E-a{mm.group(1)}", name=mm.group(2).strip()))
    if len(fams) != 8:
        raise SystemExit(f"[生成エラー] E-a の型が {len(fams)} 個しか取れない（8個のはず）＝正本の形が変わった")
    return fams


def _n_min() -> int:
    j = json.loads(LIMITS_JSON.read_text(encoding="utf-8"))
    v = j.get("n_min")
    if not isinstance(v, (int, float)) or v <= 0:
        raise SystemExit("[生成エラー] search_limits.json の n_min が読めない")
    return int(v)


_TF_MIN = {"5m": 5, "15m": 15, "30m": 30, "1h": 60, "2h": 120, "4h": 240, "6h": 360, "12h": 720, "1d": 1440}


def _window_days(name: str, tf: str) -> float | None:
    """部品×時間足の「値が独立に1つ決まるのに要する日数」＝カタログ名のパラメータから機械算出。
    出典＝CP2 監査 4-4 の算術（122日の窓に日足50本平均は独立区間が2つしか取れない）。"""
    ref, prm = iref.find(name)
    if ref is None or tf not in _TF_MIN:
        return None
    nums = [p for p in (prm or ()) if isinstance(p, (int, float)) and p >= 2]
    win_bars = max(nums) if nums else 1
    return win_bars * _TF_MIN[tf] / 1440.0


def build_table() -> dict:
    """表の本体＝広く展開。削る＝機械生成の禁止だけ。全行に根拠フィールドが付く。"""
    names, tfs = _catalog()
    fams = _families_ea()
    n_min = _n_min()
    period_days = (SEARCH_END - SEARCH_START).days

    # ── 禁止1: 向きを持たない部品を「向きの条件」に使わない（方向の欄＝②材料検査1 で全種検証済み）──
    ban_direction = []
    # ── 禁止2: カタログ注記「型の表で向きの材料に使わない」（②の実測＋まこさん OK 2026-08-06）──
    ban_note = []
    kubun = {}
    for nm in names:
        ref, _ = iref.find(nm)
        cat = ref["houkou"].split("＝")[0] if ref else "？"
        kubun[nm] = cat
        if "型の表で向きの材料に使わない" in (ref["houkou"] if ref else ""):
            ban_note.append(nm)
        elif cat in ("状態量", "ボラ量"):
            ban_direction.append(nm)

    # ── 禁止3: 有効標本数の不足（部品×時間足）。n_eff = 値決め窓の日数 ÷ 独立に1つ決まる日数 < n_min ──
    ban_samples = []
    for nm in names:
        for tf in tfs:
            wd = _window_days(nm, tf)
            if wd is None:
                continue
            n_eff = period_days / wd if wd > 0 else float("inf")
            if n_eff < n_min:
                ban_samples.append(dict(part=nm, tf=tf, n_eff=round(n_eff, 1)))

    table = dict(
        purpose="net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的（まこさん確定 2026-08-06 逐語）",
        built_by="gen_signal_families.py（全自動生成・CC の手書きの行ゼロ）",
        # 表の本体（広さ）＝機械抽出。ここから下の禁止に当たらない組み合わせは全部 許可。
        families=fams,
        parts=names,
        timeframes=tfs,
        kubun=kubun,
        # 削る（全部 機械生成・根拠つき）
        bans=dict(
            direction_stateful=dict(
                rule="区分が 状態量・ボラ量 の部品は、向き（上昇/下落の優劣）の条件に使えない。強さ・量の条件には使える",
                parts=sorted(ban_direction),
                basis="indicator_reference_diag の「方向」の欄（2026-08-06 材料検査1＝合成系列＋実データの2本柱で全種検証済み・❌0件）",
            ),
            direction_note=dict(
                rule="カタログ注記「型の表で向きの材料に使わない」を持つ部品は、向きの条件に使えない",
                parts=sorted(ban_note),
                basis="2026-08-06 材料検査1 の実測（普通の相場で向きの差が四分位幅の半分以下）＋まこさん OK",
            ),
            insufficient_samples=dict(
                rule=f"値決め窓 {period_days} 日で有効標本数 n_eff < {n_min} の（部品×時間足）は条件の候補にしない",
                pairs=ban_samples,
                basis="CP2 監査 4-4 の算術＋search_limits.json の n_min（まこさん OK 2026-08-01）。恒久の接続（検査5 の実測表）は D9 の直しで行う",
            ),
        ),
        # 機械で導けなかったもの＝作らない・空欄で明示（根拠の無い行を書かないため）
        pending=dict(
            direction_conflict=dict(
                rule="（空欄）型の狙う向きと条件の向きの矛盾の定義＝機械で導く根拠がまだ無い。CC は書かない。まこさんの判断待ち",
                basis="無し（2026-08-06 の不正の再発防止＝根拠の無い規則を書かない）",
            ),
            role_lineage=dict(
                rule="（空欄）役割（引き金・環境認識・十分性・位置）ごとに系統を絞る決まり＝機械で導く根拠がまだ無い。CC は書かない。まこさんの判断待ち",
                basis="無し（同上。2026-08-06 に CC が監査の例文から捏造して不正になった部分）",
            ),
        ),
        approval=dict(fingerprint=None, note="まこさんの承認の指紋が入るまで、この表は無効（G1 が生成器のコードの書き込みを止める）"),
    )
    return table


def _canon(table: dict) -> str:
    return json.dumps(table, ensure_ascii=False, sort_keys=True, indent=1)


def _md(table: dict, h: str) -> str:
    b = table["bans"]
    lines = [
        f"<!-- SIGNAL_FAMILIES hash={h} gen_signal_families.py が自動生成＝手で書き換えない -->",
        "# signal_families.md — 型の表（許可の一覧・全自動生成・CC の手書きの行ゼロ）",
        "",
        "作り（まこさん確定 2026-08-06）＝ 表の本体は広く展開 ／ 削るのは機械生成の禁止だけ ／ 検算は V9 の実物。",
        "",
        f"## 表の本体（広さ）＝型 {len(table['families'])} 種 × 部品 {len(table['parts'])} 種 × 時間足 {len(table['timeframes'])} 本",
        "",
        "| 型 | 中身（軸カタログ E-a の逐語） |",
        "|---|---|",
    ]
    for f in table["families"]:
        lines.append(f"| {f['id']} | {f['name']} |")
    lines += [
        "",
        "部品と時間足＝observe_diag のカタログ（2026-08-06 材料検査済み）の全部。**下の禁止に当たらない組み合わせは全部 許可。**",
        "",
        "## 削る（全部 機械生成・根拠つき）",
        "",
        f"### 禁止1 向きの条件に使えない部品（区分＝状態量・ボラ量）… {len(b['direction_stateful']['parts'])} 種",
        f"根拠: {b['direction_stateful']['basis']}",
        "、".join(b["direction_stateful"]["parts"]),
        "",
        f"### 禁止2 カタログ注記による向きの除外 … {len(b['direction_note']['parts'])} 種",
        f"根拠: {b['direction_note']['basis']}",
        "、".join(b["direction_note"]["parts"]),
        "",
        f"### 禁止3 有効標本数の不足（部品×時間足）… {len(b['insufficient_samples']['pairs'])} 組",
        f"規則: {b['insufficient_samples']['rule']}",
        f"根拠: {b['insufficient_samples']['basis']}",
        "",
        "| 部品 | 時間足 | n_eff |",
        "|---|---|---|",
    ]
    for p in b["insufficient_samples"]["pairs"]:
        lines.append(f"| {p['part']} | {p['tf']} | {p['n_eff']} |")
    lines += [
        "",
        "## ★機械で導けなかったもの（CC は書かない・まこさんの判断待ち）",
        "",
        f"- 向きの矛盾の定義: {table['pending']['direction_conflict']['rule']}",
        f"- 役割ごとの系統の絞り: {table['pending']['role_lineage']['rule']}",
        "",
        "## 承認",
        "",
        f"- 指紋: {table['approval']['fingerprint']}（{table['approval']['note']}）",
    ]
    return "\n".join(lines) + "\n"


def write() -> None:
    table = build_table()
    canon = _canon(table)
    h = hashlib.md5(canon.encode("utf-8")).hexdigest()[:16]
    OUT_JSON.write_text(canon, encoding="utf-8")
    OUT_MD.write_text(_md(table, h), encoding="utf-8")
    b = table["bans"]
    print(f"[生成] {OUT_JSON}")
    print(f"[生成] {OUT_MD}")
    print(f"[中身] 型 {len(table['families'])} 種 ／ 部品 {len(table['parts'])} 種 ／ 時間足 {len(table['timeframes'])} 本")
    print(f"[削る] 禁止1（状態量・ボラ量を向きに使わない）= {len(b['direction_stateful']['parts'])} 種"
          f" ／ 禁止2（注記）= {len(b['direction_note']['parts'])} 種"
          f" ／ 禁止3（標本不足の部品×時間足）= {len(b['insufficient_samples']['pairs'])} 組")
    print(f"[空欄] 機械で導けず作らなかった決まり = {len(table['pending'])} 件（向きの矛盾の定義・役割ごとの系統）＝まこさんの判断待ち")
    print(f"[指紋] md5 {h} ／ 承認の指紋 = {table['approval']['fingerprint']}（無し＝表は無効のまま）")


def verify() -> None:
    if not OUT_JSON.exists() or not OUT_MD.exists():
        raise SystemExit("[検証エラー] 表がまだ無い（--write が先）")
    now = _canon(build_table())
    disk = OUT_JSON.read_text(encoding="utf-8")
    # 承認の指紋だけは後から入るので、指紋欄を除いて比べる
    strip = lambda s: re.sub(r'"fingerprint": "[^"]*"', '"fingerprint": null', s)  # noqa: E731
    if strip(disk) != strip(now):
        raise SystemExit("[検証エラー] 表が入力と一致しない（手の改変か、入力の正本が変わった）＝ --write で作り直す")
    h_md = re.search(r"hash=([0-9a-f]{16})", OUT_MD.read_text(encoding="utf-8"))
    h_now = hashlib.md5(disk.encode("utf-8")).hexdigest()[:16]
    if not h_md or (h_md.group(1) != h_now and strip(disk) == disk):
        raise SystemExit("[検証エラー] md の指紋が json と食い違う")
    print("[検証] ✅ 表は入力の正本と一致（手の改変なし）")


APPROVED_FILE = SDK / ".claude/ratchet/signal_families_approved.txt"


def _table_status() -> tuple[bool, str]:
    """表が有効か＝①json が在る ②承認の指紋が在る ③指紋が今の json と一致する。"""
    if not OUT_JSON.exists():
        return False, "表（signal_families.json）が無い"
    h = hashlib.md5(OUT_JSON.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    if not APPROVED_FILE.exists():
        return False, f"承認の指紋が無い（まこさんが --approve を実行するまで表は無効）。今の表 md5 {h[:8]}…"
    rec = APPROVED_FILE.read_text(encoding="utf-8").split()[0]
    if rec != h:
        return False, f"承認の指紋（{rec[:8]}…）が今の表（{h[:8]}…）と一致しない＝表が変わった。再承認が要る"
    return True, f"承認済み（md5 {h[:8]}…）"


def approve() -> None:
    """★まこさんが実行する承認の操作（CC は実行しない＝実行した場合は worklog に残る不正）。"""
    verify()
    h = hashlib.md5(OUT_JSON.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    import datetime
    APPROVED_FILE.write_text(f"{h}  approved {datetime.date.today()}\n", encoding="utf-8")
    print(f"[承認] 指紋を記録した: {h}")
    print("[注意] この操作はまこさんが行う。CC が自分で実行するのは false_positive 類型 G の不正")


def _collect_parts(obj, parts: set, tfs: set, found: list) -> None:
    """構造（レシピ）の中から『部品__時間足』の形の文字列を全部拾う（形式に依存しない走査）。"""
    if isinstance(obj, dict):
        for v in obj.values():
            _collect_parts(v, parts, tfs, found)
    elif isinstance(obj, list):
        for v in obj:
            _collect_parts(v, parts, tfs, found)
    elif isinstance(obj, str) and "__" in obj:
        base, _, tf = obj.rpartition("__")
        if tf in tfs or base in parts:
            found.append((base, tf))


def check_structures(path: str) -> None:
    """G2 判定器＝生成された全構造を表と照合する。適合率 100% でなければ終了コード1。
    表が無効（承認の指紋なし）のときも終了コード1（本走に進めない）。"""
    table = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    parts = set(table["parts"])
    tfs = set(table["timeframes"])
    banned_pairs = {(p["part"], p["tf"]) for p in table["bans"]["insufficient_samples"]["pairs"]}
    ok_tbl, msg = _table_status()
    print(f"[表の状態] {msg}")
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    structures = data.get("structures", data) if isinstance(data, dict) else data
    if not isinstance(structures, list) or not structures:
        raise SystemExit("[G2エラー] 構造の一覧が読めない（json のリストか {structures:[...]} を渡す）")
    n_ok = 0
    for i, st in enumerate(structures):
        found: list = []
        _collect_parts(st, parts, tfs, found)
        ng = []
        for base, tf in found:
            if base not in parts:
                ng.append(f"部品 {base} がカタログに無い")
            elif tf not in tfs:
                ng.append(f"時間足 {tf} が表に無い（{base}）")
            elif (base, tf) in banned_pairs:
                ng.append(f"{base}__{tf} は標本不足の禁止（禁止3）")
        if not found:
            ng.append("部品が1つも見つからない（構造の形式が想定外）")
        if ng:
            print(f"  ❌ 構造#{i}: " + " ／ ".join(ng))
        else:
            n_ok += 1
            print(f"  ✅ 構造#{i}: 部品 {len(found)} 個 全部 表の中")
    rate = n_ok / len(structures)
    print(f"[G2] 適合率 {rate:.0%}（{n_ok}/{len(structures)}）"
          f" ／ 未検査＝空欄2件（向きの矛盾・役割の系統）は定義がまだ無いので照合できない（隠さず明示）")
    if not ok_tbl or rate < 1.0:
        raise SystemExit(1)


def g2_selftest() -> None:
    """G2 の番人＝既知答え。表の中の構造は ✅・表の外（偽の部品・禁止3 の組）は ❌ が出ること。"""
    table = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    parts = set(table["parts"])
    tfs = set(table["timeframes"])
    banned = {(p["part"], p["tf"]) for p in table["bans"]["insufficient_samples"]["pairs"]}
    if not banned:
        raise SystemExit("[番人エラー] 禁止3 が空＝既知答えが作れない")
    bp, btf = next(iter(sorted(banned)))
    cases = [
        (dict(entry={"all": [{"m": "RSI9__15m"}]}), True, "表の中の部品"),
        (dict(entry={"all": [{"m": f"{bp}__{btf}"}]}), False, f"禁止3 の組（{bp}__{btf}）"),
        (dict(entry={"all": [{"m": "ニセ指標__5m"}]}), False, "カタログに無い偽の部品"),
    ]
    ng = []
    for st, want_ok, label in cases:
        found: list = []
        _collect_parts(st, parts, tfs, found)
        bad = [1 for b, t in found if b not in parts or t not in tfs or (b, t) in banned]
        got_ok = bool(found) and not bad
        mark = "✅" if got_ok == want_ok else "🚨"
        print(f"  {mark} {label}: 期待={'通る' if want_ok else '❌'} ／ 実際={'通る' if got_ok else '❌'}")
        if got_ok != want_ok:
            ng.append(label)
    if ng:
        raise SystemExit(f"[番人] 🚨 G2 が既知答えに正しく反応しない: {ng}")
    print("[番人] ✅ G2 の既知答え 3件 全部 期待どおり")


V9_LOGIC_MD = SDK / ".claude/ratchet/v9_logic.md"
# V9 の指標名 → カタログの family 名の対応（★名前の翻訳表＝方針の決定ではない・全行が出力に印字される。
# 空リスト＝カタログに機械対応の family が無い＝検算の対象外と明示する（勝手に対応づけて誤魔化さない））
V9_FAMILY_MAP = {
    "RCI": ["RCI"],
    "ボリンジャーバンド": ["BB%b", "BB幅"],
    "ADX": ["ADX"],
    "ATR": ["ATR%"],
    "EMA": ["close vs EMA", "EMA傾き"],
    "RSI": ["RSI"],
    "MACD": ["MACD線%", "MACDシグナル線%", "MACDヒスト%"],
    "ストキャスティクス": ["Stoch%K", "Stoch%D"],
    "location_prev": [],
    "entry_risk_score": [],
}


def _v9_indicators() -> list[str]:
    """V9 の使用指標10種を v9_logic.md §1.2 の表から機械で抜く。
    前提＝材料検査3（②）で「V9 のコードは記録時点 2026-07-27 から不変」を機械確認済み＝文書はコードと一致。"""
    text = V9_LOGIC_MD.read_text(encoding="utf-8")
    m = re.search(r"## 1\.2 .*?\n(.*?)\n#", text, re.S)
    if not m:
        raise SystemExit("[V9検算エラー] v9_logic.md の §1.2（使用指標の表）が見つからない")
    names = []
    for row in m.group(1).splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] not in ("指標", "---") and not set(cells[0]) <= {"-"}:
            names.append(cells[0])
    if len(names) != 10:
        raise SystemExit(f"[V9検算エラー] §1.2 から {len(names)} 種しか取れない（10種のはず）: {names}")
    return names


def v9_test(exclude_family: str | None = None) -> None:
    """検算＝できた表に V9 の実物の組み合わせ（の部品）が入っているか。入っていなければ表が不合格。
    exclude_family はメタ確認専用＝わざとその family を表から消して、検算が落ちることを確かめる。
    ★範囲の正直な明示＝この検算が見るのは Entry の部品（指標×5分足）まで。Exit の枝は D2 の段。
    location_prev / entry_risk_score はカタログに機械対応が無く対象外（隠さず印字する）。"""
    table = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    parts = set(table["parts"])
    banned3 = {(p["part"], p["tf"]) for p in table["bans"]["insufficient_samples"]["pairs"]}
    fam_of = {}
    for p in parts:
        ref, _ = iref.find(p)
        fam_of.setdefault(ref["family"] if ref else "？", []).append(p)
    print("[前提] 材料検査3（②）で V9 のコードが記録時点から不変であることを確認済み＝v9_logic.md はコードと一致")
    print("[対応表] V9 の指標名 → カタログ family（名前の翻訳・方針の決定ではない）:")
    ng = []
    skipped = []
    for ind in _v9_indicators():
        fams = V9_FAMILY_MAP.get(ind)
        if fams is None:
            ng.append(f"{ind}: 対応表に無い（翻訳表の漏れ）")
            continue
        if not fams:
            skipped.append(ind)
            print(f"   ⚠️ {ind} → 機械対応なし＝検算の対象外（カタログに同じ意味の family 名が無い）")
            continue
        for f in fams:
            if exclude_family and f == exclude_family:
                have = []
            else:
                have = fam_of.get(f, [])
            ok5m = [p for p in have if (p, "5m") not in banned3]
            mark = "✅" if ok5m else "❌"
            print(f"   {mark} {ind} → {f}: 表の部品 {len(have)} 種 ／ うち5分足で使用可 {len(ok5m)} 種")
            if not ok5m:
                ng.append(f"{ind} → {f}: 表に無い か 5分足で全部 禁止＝実在する稼ぐ組み方を締め出している")
    print(f"[検算のまとめ] 対象外 {len(skipped)} 種（{'・'.join(skipped)}）＝機械対応が無いことを明示")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        print("[V9検算] ❌ 不合格＝表が V9 の実物を締め出している（表を直すまで承認に進めない）")
        raise SystemExit(1)
    print("[V9検算] ✅ 合格＝V9 が使う部品は全部 表に入っている（Entry の部品×5分足の範囲で）")


def v9_selftest() -> None:
    """V9検算の番人＝わざと Stoch%K を表から消すと、検算が実際に落ちること。"""
    print("== 番人: わざと Stoch%K を表から消す → 検算が落ちるはず ==")
    try:
        v9_test(exclude_family="Stoch%K")
    except SystemExit as e:
        if e.code == 1:
            print("[番人] ✅ 検算が正しく落ちた")
            return
        raise
    raise SystemExit("[番人] 🚨 偽の欠落が素通りした＝検算が機能していない")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="型の表の自動生成と G2 判定器（read-only・売買しない・値を選ばない）")
    ap.add_argument("--write", action="store_true", help="表を作る（json と md）")
    ap.add_argument("--verify", action="store_true", help="表が入力の正本と一致するか（手の改変の検出）")
    ap.add_argument("--approve", action="store_true", help="★まこさん専用＝表を承認して指紋を記録する（CC は実行しない）")
    ap.add_argument("--status", action="store_true", help="表が有効か（承認の指紋の状態）を表示する")
    ap.add_argument("--check-structures", default=None, metavar="FILE",
                    help="G2 判定器＝構造の一覧（json）を表と照合する。適合率100%%未満か表が無効なら終了コード1")
    ap.add_argument("--g2-selftest", action="store_true", help="G2 の番人（既知答え3件）")
    ap.add_argument("--v9-test", action="store_true", help="検算＝表に V9 の実物の部品が入っているか（入っていなければ不合格）")
    ap.add_argument("--v9-selftest", action="store_true", help="検算の番人＝わざと家族を消すと落ちるか")
    a = ap.parse_args()
    if a.write:
        write()
    elif a.verify:
        verify()
    elif a.approve:
        approve()
    elif a.status:
        ok, msg = _table_status()
        print(("✅ " if ok else "❌ ") + msg)
        raise SystemExit(0 if ok else 1)
    elif a.check_structures:
        check_structures(a.check_structures)
    elif a.g2_selftest:
        g2_selftest()
    elif a.v9_test:
        v9_test()
    elif a.v9_selftest:
        v9_selftest()
    else:
        ap.error("--write / --verify / --approve / --status / --check-structures / --g2-selftest を指定する")
