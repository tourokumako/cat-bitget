#!/usr/bin/env python3
"""indicators.py — 指標の情報の読む口（工事 m2c15-indicator-redirect-20261031・やることの表 F-1・ToDo の161番）。

まこさん（2026-10-23）「指標の情報を１つのデータに集約して、そこからしか指標の情報は取れない状態にするための修正」。
indicators.json を開くのは、このプログラムだけ（集約の要件定義書 R5）。計算の関数の本体は持たない（R8）＝記録は関数の名前で指す。
計算は、記録の「計算の関数」の登録の名前で、観察の道具の計算の登録（observe_diag.py の MATERIAL_FAMILIES）から取って返す
（やることの表 F-1・指標の構造の要件定義書 第2章の2「指標の値の計算も返します」）。オフの指標の計算は返さない（要件6）。
時間足の表だけは、設定ファイル observe_config.json の timeframes を名前で指す（要素の定義表の「選べる値」の「時間足」）。

読む口が守る決まり5つ（192番の設計書 4-13・indicators.json の「要素の定義表」の「読む口が守る決まり」）
  ① 要素の定義表を読む（欄の名前をコードに書かない）
  ② 記録に無い要素は、その要素の「無いときの扱い」で返す（未設定なら UNDECIDED＝「まだ決めていない」・黙って既定の値を作らない）
  ③ 「オン/オフ」がオフの要素は返さない
  ④ 選べる値から選ぶ要素の値が、その選べる値に無いときは止まる（fail-closed）
  ⑤ 指標の記録がオフなら、その指標の使い方の記録と、それを使う部品の記録も返さない
  ★読む口が使う要素（オン/オフ・計算の関数・列を作る組・パラメータの軸・指す物・使う物）は、要素の定義表の番号から名前を引く（決まり①・監査 CP94 の修正11）。
  ★column_sets（列を作る組）は、171番まで列を変えないため、決まり⑤の外とする（オフの指標と、オフの指標を使う部品の列の組も返す）。
    決まり③は守り、「列を作る組」の要素がオフなら止まる（監査 CP94 の修正12）。

使い方（ライブラリ）
  import indicators as ind
  r = ind.load()                              # 1回だけ読む（2回目からは同じ物を返す）
  r.names("指標の記録")                       # 記録の名前の並び（オン・オフを問わず）
  r.record("RSI")                             # 1件の記録（在る要素だけ・オフの要素は無い）
  r.element("RSI", "パラメータの軸")          # 1つの要素の値。無ければ「無いときの扱い」のとおり
  r.usages("RSI")                             # その指標の使い方の記録（指標がオフなら空）
  r.parts()                                   # 部品の記録（使う指標がオフなら外す）
  r.column_sets()                             # 列を作る組（指標と部品）をカタログの並びの順で（161-2 の build_catalog が使う）
  r.calc("RSI")                               # 計算の関数（登録の名前・名前の型・向きを持つ・関数）。観察の道具の登録から取る
  r.value("RSI", d, 14)                       # 指標の値（パラメータの値を渡して計算する）
使い方（コマンド）
  python3 indicators.py --selftest            # 決まり5つと計算の口を、自分の中の小さな見本のデータで試す（本物は読まない）
  python3 indicators.py --count               # 本物の記録の数・要素ごとの空でない数・計算の関数が登録に在るかを出す（読むだけ）
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
JSON_PATH = HERE / "indicators.json"
CONFIG_PATH = HERE.parent / "observe_config.json"            # 時間足の表（要素の定義表の「選べる値」の「時間足」が名前で指す）
TABLE_KEY = "要素の定義表"
RECORD_KINDS = ("指標の記録", "使い方の記録", "部品の記録")          # 法則の記録（⑤）は195番で作る
TIMEFRAMES_TABLE = "observe_config.json の timeframes"
UNDECIDED = "まだ決めていない"                                   # 決まり②＝未設定の要素は、この印を返す
ANY = "両方"                                                    # 玉の向きの「両方」（選べる値「玉の向き」）
PREFIX = "[読む口]"
# 読む口が使う要素は、要素の定義表の番号から名前を引く（コードに要素の名前を書かない＝決まり①・監査 CP94 の修正11）
NO = {"オン/オフ": {"指標の記録": "②-10", "部品の記録": "④-8", "使い方の記録": "③-11"},
      "計算の関数": {"指標の記録": "②-2", "部品の記録": "④-3"},
      "列を作る組": {"指標の記録": "②-12", "部品の記録": "④-9"},
      "パラメータの軸": {"指標の記録": "②-4", "部品の記録": "④-4"},
      "指す物": {"使い方の記録": "③-1"}, "使う物": {"部品の記録": "④-2"}}
# 「指標の記録の値を使う」要素が、指標の記録のどの要素を使うか（番号で持つ・③-6 パラメータの代表の値 → ②-4 パラメータの軸）
USE_FROM_NO = {"③-6": "②-4"}


# 選べる値から選ぶ要素のうち、値が辞書（か辞書の並び）の物は、どの欄が選べる値か（選べる値の名前 → 欄の名前）。
# ★要素の定義表の「形の決まり」の文からは決められない（②-7 教科書の役割の形の決まりは「選べる値から選ぶ」だけで、値は {区分・出どころ・札}
#   の辞書＝2026-11-01 に写しで確かめた）ので、この対応はコードに残す（監査 CP94 の Q13 の2つ目＝8つの対応の中身は合う）。
_CHOICE_FIELD = {"閾値の形": "形", "値の単位": "単位", "値の読み方の区分": "区分", "役割の区分": "区分", "場面": "場面",
                 "軸の意味": "意味", "時間足": "時間足", "判定の型": "型"}


class IndicatorsError(SystemExit):
    """読む口が止まるときの例外（終わりのコードは 1）。"""


def _stop(msg: str):
    raise IndicatorsError(f"{PREFIX} {msg}")


def _load_observe():
    """観察の道具（observe_diag.py）を読み込む。計算の関数の本体の置き場（R8）。読み込むのは calc を初めて呼んだときだけ。"""
    import contextlib
    import io
    import os
    if str(HERE.parent) not in sys.path:
        sys.path.insert(0, str(HERE.parent))
    cwd = os.getcwd()
    try:
        os.chdir(HERE.parent)
        with contextlib.redirect_stdout(io.StringIO()):
            import observe_diag as od  # noqa: E402
    finally:
        os.chdir(cwd)
    return od


class Indicators:
    def __init__(self, data: dict, timeframes=None, registry=None):
        if not isinstance(data, dict) or TABLE_KEY not in data:
            _stop("要素の定義表が無い")
        self.data = data
        self.table = data[TABLE_KEY]
        for k in ("要素", "選べる値", "読む口が守る決まり"):
            if k not in self.table:
                _stop(f"要素の定義表に「{k}」が無い")
        for k in RECORD_KINDS:
            if k not in data:
                _stop(f"一番外に「{k}」が無い（古い形の indicators.json＝写すプログラムで写し直す）")
        self._tf = timeframes
        self._registry = registry                                # 計算の登録（自己テストは見本を渡す。無ければ calc で観察の道具から読む）
        self._od = None
        self.rows = {}                                           # 置く記録 → {要素の名前: 行}（決まり①）
        self.rows_on = {}                                        # 置く記録 → {要素の名前: 行}（オンの要素だけ・決まり③）
        self.E = {e["番号"]: e["要素の名前"] for e in self.table["要素"]}   # 番号 → 要素の名前（決まり①・監査 CP94 の修正11）
        for e in self.table["要素"]:
            self.rows.setdefault(e["置く記録"], {})[e["要素の名前"]] = e
            if e.get("オン/オフ") == "オン":
                self.rows_on.setdefault(e["置く記録"], {})[e["要素の名前"]] = e
        self.records = {k: data[k] for k in RECORD_KINDS}
        self._check_all()

    # ── 決まり①④＝読み込んだときに全部 照らす ───────────────────────────────────────────────
    def choices(self, name: str) -> list:
        """選べる値の名前 → 選べる値の並び（名前で指す表＝その表の鍵）。無ければ止まる。"""
        cv = self.table["選べる値"]
        if name not in cv:
            _stop(f"選べる値に「{name}」が無い")
        v = cv[name]
        if isinstance(v, dict) and "表" in v:
            t = v["表"]
            if t == TIMEFRAMES_TABLE:
                if self._tf is None:
                    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                    self._tf = list(cfg["timeframes"])
                return list(self._tf)
            if t in cv and isinstance(cv[t], dict):
                return list(cv[t])
            _stop(f"選べる値「{name}」が名前で指す表「{t}」が無い")
        if isinstance(v, dict):
            return list(v)
        return list(v)

    def _check_value(self, kind: str, rec_name: str, row: dict, val) -> None:
        """決まり④＝選べる値から選ぶ要素の値が、選べる値に在るか。値の形は「形の決まり」のとおりに辿る。"""
        cname = (row.get("形の決まり") or {}).get("選べる値の名前")
        if not cname:
            return
        allowed = set(self.choices(cname))
        field = _CHOICE_FIELD.get(cname)
        where = f"{kind}「{rec_name}」の要素「{row['要素の名前']}」"
        got = []
        for x in (val if isinstance(val, list) else [val]):
            if x is None or (isinstance(x, str) and x == UNDECIDED):
                continue
            if isinstance(x, str):
                got.append(x)
            elif isinstance(x, dict) and field:
                v = x.get(field)                                 # 欄が無い辞書＝その欄はまだ決めていない（決まり②）
                for g in (v if isinstance(v, list) else [v]):
                    if g is not None and not isinstance(g, str):
                        _stop(f"選べる値の形でない値: {where} の欄「{field}」の値 {g!r}（選べる値「{cname}」）")
                    got.append(g)
            else:
                # ★文字・文字の並び・選べる値の欄を持つ辞書のどれでもない値（入れ子の並び・欄の決まらない辞書・数）は、黙って通さない（監査 CP94 の修正11）
                _stop(f"選べる値の形でない値: {where} の値 {x!r}（選べる値「{cname}」）")
        for g in got:
            if g is None:
                continue
            if g not in allowed:
                _stop(f"選べる値に無い値: {where} の値 {g!r}（選べる値「{cname}」）")

    def _check_record(self, kind: str, rec_name: str, rec: dict) -> None:
        rows = self.rows.get(kind) or {}
        for k, v in rec.items():
            if k not in rows:
                _stop(f"要素の定義表に無い要素: {kind}「{rec_name}」の鍵「{k}」")
            self._check_value(kind, rec_name, rows[k], v)

    def _check_all(self) -> None:
        for kind in ("指標の記録", "部品の記録"):
            if not isinstance(self.records[kind], dict):
                _stop(f"「{kind}」は名前を鍵にした辞書でない")
            for nm, rec in self.records[kind].items():
                self._check_record(kind, nm, rec)
        if not isinstance(self.records["使い方の記録"], list):
            _stop("「使い方の記録」は行の並びでない")
        for i, rec in enumerate(self.records["使い方の記録"]):
            self._check_record("使い方の記録", f"{i}", rec)
        self.column_sets()                                       # 並びの重なり・抜けも、読み込んだときに止める

    # ── 読む口 ─────────────────────────────────────────────────────────────────────────────
    def names(self, kind: str = "指標の記録") -> list:
        if kind not in ("指標の記録", "部品の記録"):
            _stop(f"名前の並びを持つ記録は 指標の記録・部品の記録（{kind}）")
        return list(self.records[kind])

    def _find(self, name: str) -> tuple:
        for kind in ("指標の記録", "部品の記録"):
            if name in self.records[kind]:
                return kind, self.records[kind][name]
        _stop(f"記録に無い名前: {name}")

    def _el(self, role: str, kind: str) -> str:
        """読む口が使う要素の名前を、要素の定義表の番号から引く（NO の番号が表に無ければ止まる）。"""
        no = NO[role][kind]
        if no not in self.E:
            _stop(f"要素の定義表に {no}（{role}・{kind}）が無い")
        return self.E[no]

    def _state_on(self, kind: str, rec: dict) -> bool:
        """その記録のオン/オフ。要素が記録に無いときは、その要素の「無いときの扱い」で決める（④-8＝既定＝オン・決まり②）。"""
        nm = self._el("オン/オフ", kind)
        st = rec.get(nm) if nm in rec else self._missing(self.rows[kind][nm], rec, kind)
        return (isinstance(st, dict) and st.get("状態") == "オン") or st == "オン"

    def is_on(self, name: str) -> bool:
        kind, rec = self._find(name)
        return self._state_on(kind, rec)

    def record(self, name: str) -> dict:
        """1件の記録。在る要素のうち、要素の定義表でオンの物だけ（決まり③）。無い要素は入れない（element で「無いときの扱い」を返す）。"""
        kind, rec = self._find(name)
        on = self.rows_on.get(kind) or {}                      # ★決まり③
        return {k: v for k, v in rec.items() if k in on}

    def element(self, name: str, elem: str, kind: str = None):
        """1つの要素の値。記録に無ければ「無いときの扱い」のとおり（決まり②）。オフの要素は止まる（決まり③）。"""
        if kind is None:
            kind, rec = self._find(name)
        else:
            rec = self.records[kind][name] if kind != "使い方の記録" else name
        rows = self.rows.get(kind) or {}
        if elem not in rows:
            _stop(f"要素の定義表に無い要素: {kind} の「{elem}」")
        row = rows[elem]
        if row.get("オン/オフ") != "オン":
            _stop(f"オフの要素は返さない: {kind} の「{elem}」")
        if elem in rec:
            return rec[elem]
        return self._missing(row, rec, kind)

    def _missing(self, row: dict, rec: dict, kind: str):
        how = str(row.get("無いときの扱い") or "")
        if how.startswith("必ず要る"):
            _stop(f"必ず要る要素「{row['要素の名前']}」が無い（{kind}）")
        if how.startswith("未設定"):
            return UNDECIDED
        if how.startswith("指標の記録の値を使う"):
            ptr = rec.get(self._el("指す物", "使い方の記録"))
            tgt = ptr.get("指標の記録") if isinstance(ptr, dict) else None
            if not tgt:
                _stop(f"要素「{row['要素の名前']}」は指標の記録の値を使うが、指す物が無い")
            # 指標の記録の側の要素＝同じ名前が在ればそれ。無ければ USE_FROM_NO の番号（③-6 パラメータの代表の値 → ②-4 パラメータの軸＝
            # 192番の要素 ③-6 の中身「軸ごとの代表の値…書いたときだけ、指標の記録の値の代わりに使う」）
            no = USE_FROM_NO.get(row.get("番号"))
            src = row["要素の名前"] if row["要素の名前"] in (self.rows.get("指標の記録") or {}) else (self.E.get(no) if no else None)
            if not src:
                _stop(f"要素「{row['要素の名前']}」は指標の記録の値を使うが、指標の記録のどの要素かが決まらない")
            v = self.element(tgt, src, "指標の記録")
            if no and isinstance(v, list):
                # ③-6 の形の決まり「軸の名前ごとの数の組」＝軸の並びを {軸の名前: 代表の値} にして返す（監査 CP94 の修正24）
                return {a.get("名前"): a.get("代表の値", UNDECIDED) for a in v if isinstance(a, dict)}
            return v
        if how.startswith("既定＝"):
            import re
            val = re.split(r"[（(]", how[len("既定＝"):])[0].strip()       # （ ）の前までを値にする（192番の形の決まり・監査 CP94 の修正24）
            if str((row.get("形の決まり") or {}).get("値の種類") or "").startswith("オン/オフ"):
                return {"状態": val}                                       # 書く値と同じ形で返す（③-11・④-8＝監査 CP94 の修正24）
            return val
        _stop(f"要素「{row['要素の名前']}」の「無いときの扱い」が読めない: {how!r}")

    def usages(self, name: str = None) -> list:
        """使い方の記録（決まり⑤＝指す物の指標がオフなら返さない）。"""
        out = []
        ptr_nm = self._el("指す物", "使い方の記録")
        for rec in self.records["使い方の記録"]:
            ptr = rec.get(ptr_nm) if isinstance(rec.get(ptr_nm), dict) else {}
            tgt = ptr.get("指標の記録") or ptr.get("部品の記録")
            if tgt is None or (name is not None and tgt != name):
                continue
            if not self.is_on(tgt):
                continue
            if not self._state_on("使い方の記録", rec):         # ★使い方の記録そのもの（③-11）がオフなら返さない（監査 CP94 の修正11）
                continue
            on = self.rows_on.get("使い方の記録") or {}
            out.append({k: v for k, v in rec.items() if k in on})
        return out

    def parts(self, name: str = None) -> dict:
        """部品の記録（決まり⑤＝使う物の指標がオフなら返さない・部品そのものがオフでも返さない）。"""
        out = {}
        on = self.rows_on.get("部品の記録") or {}
        for nm, rec in self.records["部品の記録"].items():
            if name is not None and nm != name:
                continue
            if not self.is_on(nm):
                continue
            uses = rec.get(self._el("使う物", "部品の記録")) or []
            if any(not self.is_on(u.get("指標の記録")) for u in uses if isinstance(u, dict) and u.get("指標の記録")):
                continue
            out[nm] = {k: v for k, v in rec.items() if k in on}
        return out

    def axes(self, name: str):
        kind, _rec = self._find(name)
        return self.element(name, self._el("パラメータの軸", kind))

    def registry(self) -> dict:
        """計算の登録（登録の名前 → (名前の型, 向きを持つ, 関数)）。渡されていなければ観察の道具から読む。"""
        if self._registry is None:
            self._od = _load_observe()
            self._registry = self._od.MATERIAL_FAMILIES
        return self._registry

    def calc(self, name: str) -> dict:
        """計算の関数（F-1・第2章の2）。記録の「計算の関数」の登録の名前で、計算の登録から取る（本体はコードのまま＝R8）。
        オフの指標の計算は返さない（要件6）。登録の名前が無い・登録に無いときは止まる。"""
        if not self.is_on(name):
            _stop(f"オフの指標の計算は返さない: {name}")
        kind, _rec = self._find(name)
        c = self.element(name, self._el("計算の関数", kind))
        reg = c.get("登録の名前") if isinstance(c, dict) else None
        if not reg:
            _stop(f"計算の関数の登録が無い: {name}（{(c or {}).get('注記') if isinstance(c, dict) else ''}）")
        mf = self.registry()
        if reg not in mf:
            _stop(f"計算の登録に無い名前: {name} の {reg}")
        tpl, directional, fn = mf[reg]
        return {"登録の名前": reg, "名前の型": tpl, "向きを持つ": directional, "関数": fn}

    def value(self, name: str, d, *params):
        """指標の値（第2章の2）。パラメータの値を渡して、計算の関数で計算する。数が名前の型と合わなければ止まる。"""
        c = self.calc(name)
        if c["名前の型"].count("{}") != len(params):
            _stop(f"パラメータの数が名前の型と合わない: {name}（型 {c['名前の型']}・渡した {list(params)}）")
        if self._od is not None and hasattr(self._od, "_load_pta"):
            self._od._load_pta()                                 # 観察の道具の make_material と同じ準備（外のライブラリの読み込み）
        return c["関数"](d, *params)

    def column_sets(self) -> list:
        """列を作る組（②-12・④-9）を、カタログの並びの順で。並びに重なりか抜けが在れば止まる（4-5）。
        ★171番まで列を変えないため、決まり⑤の外（オフの指標と、オフの指標を使う部品の列の組も返す）。決まり③は守る＝「列を作る組」の要素が
          オフなら止まる（監査 CP94 の修正12）。"""
        out = []
        for kind in ("指標の記録", "部品の記録"):
            el = self._el("列を作る組", kind)
            if (self.rows[kind][el].get("オン/オフ")) != "オン":
                _stop(f"オフの要素は返さない: {kind} の「{el}」")
            for nm, rec in self.records[kind].items():
                cs = rec.get(el)
                if not cs:
                    continue
                tpls, sets, order = cs.get("名前の型") or [], cs.get("組") or [], cs.get("並び") or []
                if len(sets) != len(order):
                    _stop(f"列を作る組の組と並びの数が合わない: {nm}")
                for p, i in zip(sets, order):
                    out.append({"記録": nm, "種類": kind, "名前の型": tpls[0] if tpls else None, "組": list(p), "並び": int(i)})
        out.sort(key=lambda x: x["並び"])
        seen = [x["並び"] for x in out]
        if len(set(seen)) != len(seen):
            _stop("列を作る組の並びが重なる: " + "・".join(str(s) for s in sorted({s for s in seen if seen.count(s) > 1})[:10]))
        if seen and seen != list(range(len(seen))):
            miss = sorted(set(range(max(seen) + 1)) - set(seen))
            _stop("列を作る組の並びが抜ける: " + "・".join(str(m) for m in miss[:10]))
        return out


_CACHE: dict = {}


def load(path=None, timeframes=None) -> Indicators:
    """indicators.json を読む（同じパスは1回だけ読む）。無い・読めない・要素の定義表が無いときは止まる。"""
    p = Path(path) if path else JSON_PATH
    key = str(p)
    if key not in _CACHE:
        if not p.is_file():
            _stop(f"indicators.json が無い・読めない: {p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:                                   # noqa: BLE001
            _stop(f"indicators.json が無い・読めない: {p}（{e}）")
        _CACHE[key] = Indicators(data, timeframes)
    return _CACHE[key]


# ── 自己テスト（自分の中の小さな見本のデータ・本物は読まない）────────────────────────────
def _sample() -> dict:
    def row(no, name, kind, how, on="オン", choice=None, form="文字"):
        return {"番号": no, "要素の名前": name, "置く記録": kind, "中身": "見本",
                "形の決まり": {"値の種類": form, "選べる値の名前": choice, "複数持てるか": False},
                "無いときの扱い": how, "オン/オフ": on, "読むプログラム": [], "写す元": "見本",
                "根拠": {"要件の行": [], "構造に要ること": [], "拡張の条件": []}, "出どころ": "見本"}
    table = {"_これは何か": "見本", "_出どころ": "見本",
             "要素": [row("②-1", "名前", "指標の記録", "必ず要る"),
                      row("②-2", "計算の関数", "指標の記録", "必ず要る"),
                      row("②-4", "パラメータの軸", "指標の記録", "未設定（軸の無い指標は空の並び）", choice="軸の意味", form="行の並び（名前・意味）"),
                      row("②-7", "教科書の役割", "指標の記録", "未設定", choice="役割の区分", form="選べる値から選ぶ（区分）と文字（出どころ・札）"),
                      row("②-8", "確定と期間", "指標の記録", "未設定"),
                      row("②-10", "オン/オフ", "指標の記録", "必ず要る"),
                      row("②-12", "列を作る組", "指標の記録", "未設定"),
                      row("②-99", "試しのオフの要素", "指標の記録", "未設定", on="オフ"),
                      row("③-1", "指す物", "使い方の記録", "必ず要る"),
                      row("③-2", "使い方の種類", "使い方の記録", "必ず要る", choice="使い方の種類", form="選べる値から選ぶ"),
                      row("③-5", "閾値", "使い方の記録", "未設定", choice="閾値の形", form="行の並び（形・単位・代表の値・出どころ）"),
                      row("③-6", "パラメータの代表の値", "使い方の記録", "指標の記録の値を使う"),
                      row("③-7", "時間足", "使い方の記録", "未設定", choice="時間足", form="文字の並び"),
                      row("③-10", "未来を使ってよいか", "使い方の記録", "既定＝いいえ（見本の補足）"),
                      row("③-11", "オン/オフと出どころ", "使い方の記録", "既定＝オン（見本の補足）", form="オン/オフと文字"),
                      row("③-12", "玉の向き", "使い方の記録", "既定＝両方", choice="玉の向き", form="選べる値から選ぶ"),
                      row("④-1", "名前", "部品の記録", "必ず要る"),
                      row("④-2", "使う物", "部品の記録", "必ず要る"),
                      row("④-3", "計算の関数", "部品の記録", "必ず要る"),
                      row("④-4", "パラメータの軸", "部品の記録", "未設定"),
                      row("④-8", "オン/オフと出どころ", "部品の記録", "既定＝オン", form="オン/オフと文字"),
                      row("④-9", "列を作る組", "部品の記録", "未設定")],
             "選べる値": {"使い方の種類": ["出口の反転", "前提崩れの印"], "閾値の形": ["値", "分位"],
                      "役割の区分": {"表": "役割の区分の表"}, "役割の区分の表": {"行き過ぎ": {"札": "オシレーター"}},
                      "軸の意味": ["窓"], "玉の向き": ["SHORT", "LONG", "両方"], "時間足": {"表": TIMEFRAMES_TABLE}},
             "この表で受けない要ること": {}, "読む口が守る決まり": ["見本"]}
    recs = {"RSI": {"名前": "RSI", "計算の関数": {"登録の名前": "RSI", "関数の名前": ["_rsi"], "式の文": "見本"},
                    "パラメータの軸": [{"名前": "n", "意味": "窓"}], "教科書の役割": {"区分": ["行き過ぎ"]},
                    "オン/オフ": {"状態": "オン"}, "試しのオフの要素": "返してはいけない",
                    "列を作る組": {"名前の型": ["RSI{}"], "組": [[7], [14]], "並び": [0, 2]}},
            "OFF指標": {"名前": "OFF指標", "計算の関数": {"登録の名前": "OFF", "関数の名前": [], "式の文": "見本"},
                      "オン/オフ": {"状態": "オフ"}, "列を作る組": {"名前の型": ["OFF{}"], "組": [[1]], "並び": [1]}}}
    uses = [{"指す物": {"指標の記録": "RSI"}, "使い方の種類": "出口の反転", "閾値": [{"形": "値"}], "時間足": ["5m"]},
            {"指す物": {"指標の記録": "OFF指標"}, "使い方の種類": "前提崩れの印"},
            {"指す物": {"指標の記録": "RSI"}, "使い方の種類": "前提崩れの印", "オン/オフと出どころ": {"状態": "オフ"}}]
    parts = {"帯見本": {"名前": "帯見本", "使う物": [{"指標の記録": "RSI"}], "オン/オフと出どころ": {"状態": "オン"},
                      "計算の関数": {"登録の名前": "帯見本", "関数の名前": [], "式の文": "見本"},
                      "列を作る組": {"名前の型": ["帯見本({})"], "組": [[0.1]], "並び": [3]}},
             "帯OFF": {"名前": "帯OFF", "使う物": [{"指標の記録": "OFF指標"}], "オン/オフと出どころ": {"状態": "オン"}},
             "帯既定": {"名前": "帯既定", "使う物": [{"指標の記録": "RSI"}],          # ④-8 が無い＝無いときの扱い（既定＝オン）で読む
                      "計算の関数": {"登録の名前": "帯既定", "関数の名前": [], "式の文": "見本"}}}
    return {"_作った道具": "見本", TABLE_KEY: table, "指標の記録": recs, "使い方の記録": uses, "部品の記録": parts}


def selftest() -> int:
    import copy
    ok = []

    def t(name, good):
        ok.append((name, bool(good)))

    def stops(data, text):
        try:
            Indicators(copy.deepcopy(data), timeframes=["5m", "15m"])
            return False
        except IndicatorsError as e:
            return text in str(e)

    base = _sample()
    r = Indicators(copy.deepcopy(base), timeframes=["5m", "15m"])
    # ①要素の定義表を読む＝要素の定義表に無い鍵は止まる
    bad = copy.deepcopy(base)
    bad["指標の記録"]["RSI"]["知らない鍵"] = 1
    t("決まり①: 要素の定義表に無い要素の鍵が在ると止まる", stops(bad, "要素の定義表に無い要素"))
    # ②無いときの扱い
    t("決まり②: 未設定の要素は「まだ決めていない」", r.element("RSI", "確定と期間") == UNDECIDED)
    t("決まり②: 既定＝の要素は既定の値", r.element(r.records["使い方の記録"][0], "未来を使ってよいか", "使い方の記録") == "いいえ"
      and r.element(r.records["使い方の記録"][0], "玉の向き", "使い方の記録") == ANY)
    t("決まり②: 指標の記録の値を使う要素は、指す物の指標の軸ごとの代表の値（③-6 → ②-4・{軸の名前: 代表の値}・監査 CP94 の修正24）",
      r.element(r.records["使い方の記録"][0], "パラメータの代表の値", "使い方の記録") == {"n": UNDECIDED})
    t("決まり②: 「既定＝」は（ ）の前までを値にする（監査 CP94 の修正24）", r.element(r.records["使い方の記録"][0], "未来を使ってよいか", "使い方の記録") == "いいえ")
    t("決まり②: オン/オフの既定は、書く値と同じ形（{状態: オン}）で返す（監査 CP94 の修正24）",
      r.element(r.records["使い方の記録"][0], "オン/オフと出どころ", "使い方の記録") == {"状態": "オン"})
    t("決まり②: 部品のオン/オフ（④-8）が無ければ、既定＝オンで読む（監査 CP94 の修正11）", r.is_on("帯既定") and "帯既定" in r.parts())
    # ①要素の名前を番号から引く＝要素の名前を変えても、番号が同じなら読める（監査 CP94 の修正11）
    ren = copy.deepcopy(base)
    for e in ren[TABLE_KEY]["要素"]:
        if e["番号"] == "②-10":
            e["要素の名前"] = "見本の状態の欄"
    for rr in ren["指標の記録"].values():
        rr["見本の状態の欄"] = rr.pop("オン/オフ")
    try:
        rn = Indicators(ren, timeframes=["5m", "15m"])
        t("決まり①: 要素の名前を番号から引く（②-10 の名前を変えても、オン/オフを読める）", rn.is_on("RSI") and not rn.is_on("OFF指標"))
    except IndicatorsError as e:
        t(f"決まり①: 要素の名前を番号から引く（{e}）", False)
    bad = copy.deepcopy(base)
    del bad["指標の記録"]["RSI"]["名前"]
    try:
        Indicators(bad, timeframes=["5m"]).element("RSI", "名前")
        t("決まり②: 必ず要る要素が無ければ止まる", False)
    except IndicatorsError as e:
        t("決まり②: 必ず要る要素が無ければ止まる", "必ず要る要素" in str(e))
    # ③オフの要素は返さない
    t("決まり③: record はオフの要素を返さない", "試しのオフの要素" not in r.record("RSI") and "名前" in r.record("RSI"))
    try:
        r.element("RSI", "試しのオフの要素")
        t("決まり③: element はオフの要素で止まる", False)
    except IndicatorsError as e:
        t("決まり③: element はオフの要素で止まる", "オフの要素は返さない" in str(e))
    # ④選べる値に無い値は止まる
    bad = copy.deepcopy(base)
    bad["指標の記録"]["RSI"]["教科書の役割"]["区分"] = ["知らない区分"]
    t("決まり④: 名前で指す表（役割の区分の表）に無い値で止まる", stops(bad, "選べる値に無い値"))
    bad = copy.deepcopy(base)
    bad["使い方の記録"][0]["閾値"][0]["形"] = "知らない形"
    t("決まり④: 行の並びの中の欄（閾値の形）でも止まる", stops(bad, "選べる値に無い値"))
    bad = copy.deepcopy(base)
    bad["使い方の記録"][0]["時間足"] = ["99m"]
    t("決まり④: 時間足の表（observe_config.json の timeframes）に無い値で止まる", stops(bad, "選べる値に無い値"))
    bad = copy.deepcopy(base)
    bad["指標の記録"]["RSI"]["パラメータの軸"][0]["意味"] = "知らない意味"
    t("決まり④: 軸の意味が選べる値に無いと止まる", stops(bad, "選べる値に無い値"))
    bad = copy.deepcopy(base)
    bad["使い方の記録"][0]["玉の向き"] = 5
    t("決まり④: 選べる値の要素の値が数なら止まる（監査 CP94 の修正11）", stops(bad, "選べる値の形でない値"))
    bad = copy.deepcopy(base)
    bad["使い方の記録"][0]["使い方の種類"] = {"見本": "出口の反転"}
    t("決まり④: 選べる値の欄が決まらない辞書なら止まる（監査 CP94 の修正11）", stops(bad, "選べる値の形でない値"))
    bad = copy.deepcopy(base)
    bad["使い方の記録"][0]["時間足"] = [["5m"]]
    t("決まり④: 入れ子の並びなら止まる（監査 CP94 の修正11）", stops(bad, "選べる値の形でない値"))
    # ⑤指標がオフなら使い方と部品も返さない
    t("決まり⑤: オフの指標の使い方の記録を返さない", [u["指す物"]["指標の記録"] for u in r.usages()] == ["RSI"])
    t("決まり⑤: 使い方の記録そのもの（③-11）がオフなら返さない（監査 CP94 の修正11）", len(r.usages("RSI")) == 1)
    t("決まり⑤: オフの指標を使う部品の記録を返さない", list(r.parts()) == ["帯見本", "帯既定"])
    # 記録に無い名前
    try:
        r.record("無い指標")
        t("記録に無い名前で止まる", False)
    except IndicatorsError as e:
        t("記録に無い名前で止まる", "記録に無い名前" in str(e))
    # 列を作る組の並び
    cs = r.column_sets()
    t("列を作る組を並びの順で返す（指標と部品）", [x["記録"] for x in cs] == ["RSI", "OFF指標", "RSI", "帯見本"] and [x["並び"] for x in cs] == [0, 1, 2, 3])
    bad = copy.deepcopy(base)
    bad["指標の記録"]["RSI"]["列を作る組"]["並び"] = [0, 1]
    t("列を作る組の並びが重なると止まる", stops(bad, "並びが重なる"))
    bad = copy.deepcopy(base)
    bad["指標の記録"]["RSI"]["列を作る組"]["並び"] = [0, 5]
    t("列を作る組の並びが抜けると止まる", stops(bad, "並びが抜ける"))
    t("列を作る組は決まり⑤の外＝オフの指標の組も返す（171番まで列を変えない・監査 CP94 の修正12）", "OFF指標" in [x["記録"] for x in cs])
    bad = copy.deepcopy(base)
    for e in bad[TABLE_KEY]["要素"]:
        if e["番号"] == "②-12":
            e["オン/オフ"] = "オフ"
    t("列を作る組の要素がオフなら止まる（決まり③・監査 CP94 の修正12）", stops(bad, "オフの要素は返さない"))
    bad = copy.deepcopy(base)
    del bad["部品の記録"]
    t("一番外に3つの記録が無い（古い形）と止まる", stops(bad, "古い形"))
    # 計算の口（F-1・第2章の2）＝見本の計算の登録を渡して試す（観察の道具は読まない）
    def _rsi_fn(d, n):
        return d * n
    reg = {"RSI": ("RSI{}", True, _rsi_fn), "帯見本": ("帯見本({})", False, lambda d, t_: d + t_)}
    rc = Indicators(copy.deepcopy(base), timeframes=["5m"], registry=reg)

    def safe(f):
        try:
            return f()
        except Exception:                                        # noqa: BLE001  壊れた口でも最後まで回し、❌ の行を出す
            return False
    t("計算: 記録の登録の名前で、計算の登録から関数を取る（F-1）",
      safe(lambda: rc.calc("RSI")["関数"] is _rsi_fn and rc.calc("RSI")["名前の型"] == "RSI{}" and rc.calc("RSI")["向きを持つ"] is True))
    t("計算: 値を計算して返す（第2章の2）", safe(lambda: rc.value("RSI", 3, 7) == 21 and rc.value("帯見本", 1, 0.5) == 1.5))

    def calc_stops(rd, name, text, params=None):
        try:
            rd.calc(name) if params is None else rd.value(name, 3, *params)
            return False
        except IndicatorsError as e:
            return text in str(e)
    t("計算: オフの指標の計算は返さない（要件6）", calc_stops(rc, "OFF指標", "オフの指標の計算は返さない"))
    bad = copy.deepcopy(base)
    bad["指標の記録"]["RSI"]["計算の関数"]["登録の名前"] = None
    t("計算: 登録の名前が無ければ止まる", calc_stops(Indicators(bad, timeframes=["5m"], registry=reg), "RSI", "計算の関数の登録が無い"))
    t("計算: 計算の登録に無い名前なら止まる", calc_stops(Indicators(copy.deepcopy(base), timeframes=["5m"], registry={}), "RSI", "計算の登録に無い名前"))
    t("計算: パラメータの数が名前の型と合わなければ止まる", calc_stops(rc, "RSI", "パラメータの数が名前の型と合わない", params=(7, 9)))
    for name, good in ok:
        print(f"  {'✅' if good else '❌'} {name}")
    n_ng = sum(1 for _n, g in ok if not g)
    print(f"読む口の自己テスト＝{len(ok) - n_ng}/{len(ok)}")
    return 0 if n_ng == 0 else 1


def count() -> int:
    r = load()
    for kind in ("指標の記録", "部品の記録"):
        recs = r.records[kind]
        on = sum(1 for nm in recs if r.is_on(nm))
        print(f"{kind}: {len(recs)} 件（オン {on}）")
        for e in self_rows(r, kind):
            n = sum(1 for rec in recs.values() if e in rec)
            print(f"    {e}: {n}")
    print(f"使い方の記録: {len(r.records['使い方の記録'])} 件・列を作る組: {len(r.column_sets())} 組")
    # 計算の口＝オンの記録のうち、計算の関数に登録の名前を持つ物が、観察の道具の計算の登録に全部 在るか（読むだけ）
    mf = r.registry()
    have, miss, none = 0, [], []
    for kind in ("指標の記録", "部品の記録"):
        for nm, rec in r.records[kind].items():
            if not r.is_on(nm):
                continue
            ce = rec.get(r._el("計算の関数", kind))
            reg = ce.get("登録の名前") if isinstance(ce, dict) else None
            if not reg:
                none.append(nm)
            elif reg in mf:
                have += 1
            else:
                miss.append(f"{nm}（{reg}）")
    print(f"計算の関数が計算の登録に在る: {have} 件・登録の名前が無い: {len(none)} 件（{'・'.join(none)}）・登録に無い: {len(miss)} 件")
    for m in miss:
        print("  ❌ 計算の登録に無い:", m)
    return 0 if not miss else 1


def self_rows(r: Indicators, kind: str) -> list:
    return [e["要素の名前"] for e in r.table["要素"] if e["置く記録"] == kind]


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--count" in sys.argv:
        return count()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
