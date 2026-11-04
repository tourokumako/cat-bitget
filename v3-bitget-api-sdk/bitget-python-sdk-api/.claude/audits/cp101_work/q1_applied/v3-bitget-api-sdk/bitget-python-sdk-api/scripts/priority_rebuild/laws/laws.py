#!/usr/bin/env python3
"""laws.py — 法則のデータの読む口（工事 m2c15-laws-rows-20261103・ToDo の209番）。

まこさん（2026-11-03）「絶対に修正は発生するはずなので、とにかく今後、修正、増減、停止を容易にできる構造にしてほしい」。
laws.json を開くのは、このプログラムだけ。指標の情報は indicators.py を通して読む（集約の要件定義書 R5）。
engine_tuner はまだ読まない（196番・M3-1・M4）。

読む口が守る決まりは、laws.json の「読む口が守る決まり」の10個に、番号の重なり（⑪）・数の形（⑫）・動く条件の指す物と側（⑬）を足した13個。

使い方（ライブラリ）
  import laws
  r = laws.load()
  r.rows("決済の枝")          # その区分のオンの行（オフの法則を返さない）
  r.row("枝S1-TP2")           # 1行（無い・オフなら止まる）
  r.element("枝S1-TP2", "決済の割合")   # 1つの欄。行に無ければ「無いときの扱い」のとおり
  r.number("S1_直近の安値の本数")     # 法則の中の数の1行
  r.solve("枝S1-TP2")         # 数の名前を値に解き、動く条件が指す使い方の行を添える
使い方（コマンド）
  python3 laws.py --selftest       # 決まりを、自分の中の見本で試す（本物は読まない）
  python3 laws.py --write          # 法則一覧.md を作る
  python3 laws.py --verify         # 法則一覧.md が作り直した物と同じかを見る
  python3 laws.py --check-sources  # 写す元と laws.json のずれを見る
"""
import ast
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PR = HERE.parent
JSON_PATH = HERE / "laws.json"
DOC_PATH = PR.parents[1] / ".claude" / "rules" / "法則一覧.md"
TABLE_KEY = "要素の定義表"
PREFIX = "[法則の読む口]"
UNDECIDED = "まだ決めていない"
USE_THRESHOLD = "使い方の行の閾値を使う"
STYLE = "スキャル"
# 読む口が使う要素は、番号から名前を引く（コードに要素の名前を書かない）
NO = {"番号": "⑤-1", "場面": "⑤-3", "文": "⑤-4", "級": "⑤-5", "判定": "⑤-7", "オン/オフ": "⑤-10", "区分": "⑤-11", "売買の方向": "⑤-12",
      "どの売り方用か": "⑤-29", "何をするか": "⑤-31"}
FORM_FIELDS = (("nest", "入れ子か"), ("pair", "材料の本数"), ("band", "帯か"), ("needs_side", "側が要るか"), ("slope_n", "本数が要るか"),
               ("pre_ok", "前処理を持てるか"), ("state_free", "状態を持たないか"), ("exit_ok", "出口で使えるか"),
               ("trigger_ok", "入る合図で使えるか"), ("inner_tree_ok", "中に束を持てるか"))


class LawsError(SystemExit):
    """読む口が止まるときの例外（終わりのコードは 1）。"""


def _stop(msg: str):
    raise LawsError(f"{PREFIX} {msg}")


def _load_indicators():
    if str(PR / "indicators") not in sys.path:
        sys.path.insert(0, str(PR / "indicators"))
    import indicators as ind
    return ind.load()


class Laws:
    def __init__(self, data: dict, reader=None):
        if not isinstance(data, dict) or TABLE_KEY not in data:
            _stop("要素の定義表が無い")
        self.data = data
        self.table = data[TABLE_KEY]
        self.ind = reader if reader is not None else _load_indicators()
        self.E = {e["番号"]: e["要素の名前"] for e in self.table["要素"]}
        self.defs = {e["要素の名前"]: e for e in self.table["要素"]}
        self.key = {k: self.E[v] for k, v in NO.items()}
        self.lines = data["法則の行"]
        names = [n["名前"] for n in data["法則の中の数"]]
        for nm in names:
            if names.count(nm) > 1:
                _stop(f"数の名前が重なる: {nm}")
        self.numbers = {n["名前"]: n for n in data["法則の中の数"]}
        self._referrer_on = True
        self.forms = {n["名前"]: n for n in data["条件の書き方"]}
        self.states = {n["名前"]: n for n in data["玉の状態"]}
        self._check_all()

    # ── 選べる値 ─────────────────────────────────────────────────────────
    def choices(self, name: str):
        cv = self.table["選べる値"]
        if name not in cv:
            _stop(f"選べる値に「{name}」が無い")
        v = cv[name]
        if isinstance(v, dict) and "表" in v:
            t = v["表"]
            if t.startswith("indicators.json の選べる値の"):
                out = list(self.ind.choices(t[len("indicators.json の選べる値の"):]))
            elif t.startswith("observe_config.json"):
                out = list(self.ind.choices("時間足"))
            else:
                _stop(f"選べる値「{name}」が名前で指す表「{t}」が読めない")
            return out + list(cv.get("法則だけが使う場面") or []) if name == self.key["場面"] else out
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return [x["種類"] for x in v]
        return v

    def _kind_row(self, cname: str, kind: str) -> dict:
        for x in self.table["選べる値"].get(cname) or []:
            if isinstance(x, dict) and x.get("種類") == kind:
                return x
        _stop(f"種類の表に無い種類: {cname} の {kind!r}")

    # ── 読み込みの照らし ─────────────────────────────────────────────────
    def _used_in(self, row_def: dict, kubun: str) -> bool:
        u = row_def.get("使う区分")
        return u is None or u == "全部" or kubun in u

    def _check_all(self) -> None:
        cv = self.table["選べる値"]
        seen = set()
        for row in self.lines:
            no = row.get(self.key["番号"])
            if no is None:
                _stop("番号の無い行が在る")
            if no in seen:
                _stop(f"番号が重なる: {no}")
            seen.add(no)
        self.by_no = {r[self.key["番号"]]: r for r in self.lines}
        for row in self.lines:
            self._referrer_on = self._on(row)      # オフの行が指す相手は、オフでも止めない（一緒に止められるようにする）
            self._check_row(row)
        self._referrer_on = True
        for n in self.numbers.values():
            self._check_number(n)
        del cv

    def _check_number(self, n: dict) -> None:
        unit = n.get("単位")
        allowed = set(self.ind.choices("値の単位")) | set(self.table["選べる値"].get("数だけの単位") or [])
        if unit is not None and unit not in allowed:
            _stop(f"選べる値に無い値: 法則の中の数「{n['名前']}」の単位 {unit!r}")
        if unit in (self.table["選べる値"].get("使えない単位") or []):
            _stop(f"使えない単位: 法則の中の数「{n['名前']}」の単位 {unit!r}（H6）")
        rng = n.get("範囲")
        is_num = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)
        if rng is not None and not (isinstance(rng, dict) and is_num(rng.get("lo")) and is_num(rng.get("hi")) and rng["lo"] <= rng["hi"]):
            _stop(f"範囲の形でない値: 法則の中の数「{n['名前']}」の範囲 {rng!r}")
        rep = n.get("代表の値")
        for k, v in (rep.items() if isinstance(rep, dict) else ()):
            if k not in self.ind.choices("売買スタイル"):
                _stop(f"選べる値に無い値: 法則の中の数「{n['名前']}」の代表の値の鍵 {k!r}")
            if not is_num(v):
                _stop(f"代表の値が数でない: 法則の中の数「{n['名前']}」の {k} の {v!r}")
            if rng is not None and not rng["lo"] <= v <= rng["hi"]:
                _stop(f"代表の値が範囲の外: 法則の中の数「{n['名前']}」の {k} の {v!r}（範囲 {rng['lo']}〜{rng['hi']}）")

    def _check_row(self, row: dict) -> None:
        no = row[self.key["番号"]]
        kubun = row.get(self.key["区分"])
        if kubun not in self.choices("区分"):
            _stop(f"選べる値に無い値: 行「{no}」の区分 {kubun!r}")
        for k, v in row.items():
            d = self.defs.get(k)
            if d is None:
                _stop(f"定義表に無い欄: 行「{no}」の「{k}」")
            if not self._used_in(d, kubun):
                _stop(f"その区分で使わない欄: 行「{no}」（{kubun}）の「{k}」")
            self._check_value(no, d, v)
        for d in self.table["要素"]:
            if self._used_in(d, kubun) and d["要素の名前"] not in row and self._required(d, row, kubun):
                _stop(f"必ず要る欄が無い: 行「{no}」の「{d['要素の名前']}」")

    def _required(self, d: dict, row: dict, kubun: str) -> bool:
        how = str(d.get("無いときの扱い") or "")
        if not how.startswith("必ず要る"):
            return False
        if how == "必ず要る" or how.startswith("必ず要る（一文"):
            return True
        if how.startswith("必ず要る（判定を持つ法則"):
            return self.key["判定"] in row
        if how.startswith("必ず要る（決済の枝と"):
            return kubun == "決済の枝" or row.get(self.key["何をするか"]) == "すぐ決済"
        _stop(f"「無いときの扱い」が読めない: {how!r}")

    def _check_value(self, no: str, d: dict, v) -> None:
        form = d.get("形の決まり") or {}
        kind, cname = form.get("値の種類") or "", form.get("選べる値の名前")
        where = f"行「{no}」の「{d['要素の名前']}」"
        if kind == "条件の束":
            return self._check_tree(no, v)
        if kind == "条件の種類ごとの値":
            return self._check_kinds(no, where, cname, v)
        if kind == "種類ごとの欄の値":
            return self._check_level(no, where, v)
        if kind == "値段の決め方と法則の中の数の組":
            self._check_level(no, where, v.get("値段の決め方"))
            return self._need_number(where, v.get("待つ本数"))
        if kind == "法則の中の数の名前":
            return self._need_number(where, v)
        if kind in ("枝の名前", "枝の名前の並び", "法則の番号の並び"):
            for x in (v if isinstance(v, list) else [v]):
                self._need_row(where, x, allow_off=(kind == "法則の番号の並び"))
            return None
        if kind == "玉の状態の名前":
            return self._need_state(where, v)
        if kind == "選べる値の組":
            groups = self.choices(cname)
            for k, x in v.items():
                if k not in groups:
                    _stop(f"選べる値に無い値: {where} の鍵 {k!r}")
                if x not in groups[k]:
                    _stop(f"選べる値に無い値: {where} の {k} の {x!r}")
            return None
        if cname:
            allowed = self.choices(cname)
            for x in (v if isinstance(v, list) else [v]):
                if x not in allowed:
                    _stop(f"選べる値に無い値: {where} の {x!r}")
        return None

    def _need_number(self, where: str, name) -> None:
        if name not in self.numbers:
            _stop(f"指している名前が無い: {where} の法則の中の数 {name!r}")

    def _need_state(self, where: str, name) -> None:
        if name not in self.states:
            _stop(f"指している名前が無い: {where} の玉の状態 {name!r}")

    def _need_row(self, where: str, name, allow_off: bool = False) -> None:
        if name in (self.table["選べる値"].get("枝の名前で指せる語") or []):
            return
        r = self.by_no.get(name)
        if r is None:
            _stop(f"指されている法則が無い: {where} の {name!r}")
        if self._referrer_on and not allow_off and not self._on(r):
            _stop(f"指されている法則が無い（オフ）: {where} の {name!r}")

    def _on(self, row: dict) -> bool:
        """欄が無ければオン。在るときは、状態が「オン」のときだけオン（indicators.py の _state_on と同じ・打ち間違いをオンにしない）。"""
        nm = self.key["オン/オフ"]
        if nm not in row:
            return True
        st = row[nm]
        return (isinstance(st, dict) and st.get("状態") == "オン") or st == "オン"

    def _check_kinds(self, no: str, where: str, cname: str, v) -> None:
        items = v if isinstance(v, list) else [{"種類": k, "値": x} for k, x in v.items()]
        for it in items:
            kr = self._kind_row(cname, it.get("種類"))
            val = it.get("値")
            if kr.get("形") == "法則の中の数の名前":
                self._need_number(where, val)
            if kr.get("形") == "範囲" and isinstance(val, list):
                for x in val:
                    if x is not None:
                        self._need_number(where, x)

    def _check_level(self, no: str, where: str, lv) -> None:
        if isinstance(lv, str):
            return self._need_row(where, lv)
        if not isinstance(lv, dict):
            _stop(f"値段の決め方の形でない値: {where} の {lv!r}")
        kr = self._kind_row("値段の決め方の種類", lv.get("種類"))
        fields = {f["名前"]: f["形"] for f in kr["欄"]}
        for k, x in lv.items():
            if k == "種類":
                continue
            if k not in fields:
                _stop(f"種類の欄に無い欄: {where} の {lv['種類']} の「{k}」")
            shape = fields[k]
            if shape == "法則の中の数の名前":
                self._need_number(where, x)
            elif shape == "枝の名前":
                self._need_row(where, x)
            elif "値段の決め方" in shape:
                self._check_level(no, where, x)
        return None

    def _check_tree(self, no: str, tree: dict) -> None:
        where = f"行「{no}」の動く条件"
        joins = self.table["表の形"]["条件の1本"]["つなぎ方"]
        for j, conds in tree.items():
            if j not in joins:
                _stop(f"選べる値に無い値: {where} のつなぎ方 {j!r}")
            for c in conds:
                self._check_cond(where, c)

    def _check_cond(self, where: str, c: dict) -> None:
        cols = {f["名前"]: f for f in self.table["表の形"]["条件の1本"]["欄"]}
        for k in c:
            if k not in cols:
                _stop(f"定義表に無い欄: {where} の「{k}」")
        allowed = self.choices("動く条件が指せる物")
        for k, x in (c.get("指す物") or {}).items():
            if k not in allowed:
                _stop(f"選べる値に無い値: {where} の指す物 {k!r}")
            if k == "玉の状態":
                self._need_state(where, x)
            if k == "値の読み方":
                _stop(f"読む口が読まない欄: {where} の指す物 {k!r}（solve が読むようになるまで書かない）")
            if k == "時間足" and x not in self.ind.choices("時間足"):
                _stop(f"選べる値に無い値: {where} の時間足 {x!r}")
            if k == self.key["場面"] and x not in self.choices(self.key["場面"]):
                _stop(f"選べる値に無い値: {where} の場面 {x!r}")
            if k == "部品の名前" and x not in self.ind.names("部品の記録") and x not in (self.table["選べる値"].get("未作の部品") or []):
                _stop(f"指している名前が無い: {where} の部品 {x!r}")
        m = re.search(r"（(.+)）", str((cols.get("側") or {}).get("形") or ""))
        if "側" in c and m and c["側"] not in m.group(1).split("・"):
            _stop(f"選べる値に無い値: {where} の側 {c['側']!r}")
        for f in (c.get("条件の書き方") if isinstance(c.get("条件の書き方"), list) else [c.get("条件の書き方")]):
            if f is not None and f not in self.forms:
                _stop(f"指している名前が無い: {where} の条件の書き方 {f!r}")
        val = c.get("値")
        if val is not None and val != USE_THRESHOLD:
            self._need_number(where, val)

    # ── 読む口 ───────────────────────────────────────────────────────────
    def rows(self, kubun: str = None) -> list:
        return [self._public(r) for r in self.lines if self._on(r) and (kubun is None or r[self.key["区分"]] == kubun)]

    def _public(self, row: dict) -> dict:
        return {k: v for k, v in row.items() if self.defs[k].get("オン/オフ") == "オン"}

    def row(self, no: str) -> dict:
        r = self.by_no.get(no)
        if r is None:
            _stop(f"無い法則: {no}")
        if not self._on(r):
            _stop(f"オフの法則は返さない: {no}")
        return self._public(r)

    def element(self, no: str, elem: str):
        r = self.row(no)
        d = self.defs.get(elem)
        if d is None:
            _stop(f"定義表に無い欄: {elem}")
        if d.get("オン/オフ") != "オン":
            _stop(f"オフの要素は返さない: {elem}")
        if elem in r:
            return r[elem]
        how = str(d.get("無いときの扱い") or "")
        if how.startswith("未設定"):
            return UNDECIDED
        if how.startswith("既定＝"):
            return re.split(r"[（(]", how[len("既定＝"):])[0].strip()
        if how.startswith("必ず要る"):
            _stop(f"必ず要る欄が無い: {no} の {elem}")
        _stop(f"「無いときの扱い」が読めない: {how!r}")

    def number(self, name: str) -> dict:
        if name not in self.numbers:
            _stop(f"指している名前が無い: 法則の中の数 {name!r}")
        return self.numbers[name]

    def _value(self, name: str, style: str):
        rep = self.number(name).get("代表の値")
        return rep.get(style, UNDECIDED) if isinstance(rep, dict) else UNDECIDED

    def _resolve(self, v, style: str):
        if isinstance(v, str) and v in self.numbers:
            return self._value(v, style)
        if isinstance(v, dict):
            return {k: self._resolve(x, style) for k, x in v.items()}
        if isinstance(v, list):
            return [self._resolve(x, style) for x in v]
        return v

    def _role_of(self, rec: dict) -> tuple:
        """指標の役割。区分が空なら札から引き、未確認として返す（役割は変えない）。"""
        role = rec.get("教科書の役割") or {}
        if role.get("区分"):
            return list(role["区分"]), False
        tbl = self.ind.table["選べる値"].get("役割の区分の表") or {}
        return [k for k, x in tbl.items() if x.get("札") == role.get("札")], True

    def _sides_of(self, row: dict) -> set:
        """その行の売買の方向（どの売り方用か → 売り方の行の売買の方向）。売り方を指さない行は空＝方向で絞らない。オフの売り方も読む。"""
        out = set()
        for x in row.get(self.key["どの売り方用か"]) or []:
            side = (self.by_no.get(x) or {}).get(self.key["売買の方向"])
            if side:
                out.add(side)
        return out

    def _usages_of(self, cond: dict, sides: set, unconfirmed: list) -> list:
        """指す物に書いてある欄だけで使い方の行を絞る。使い方の行の 玉の向き（無いときは両方）を、行の売買の方向で絞る。指標の記録も部品の記録も読む。"""
        want = cond.get("指す物") or {}
        need = want.get("教科書の役割")
        need = need if isinstance(need, list) else [need]
        out = []
        for u in self.ind.usages():
            if "使い方の種類" in want and want["使い方の種類"] != u.get("使い方の種類"):
                continue
            st = u.get("場面と型") or {}
            if (self.key["場面"] in want and want[self.key["場面"]] != st.get("場面")) or ("型" in want and want["型"] != st.get("型")):
                continue
            if "時間足" in want and want["時間足"] not in (u.get("時間足") or []):
                continue
            if sides and u.get("玉の向き", "両方") not in sides | {"両方"}:
                continue
            ptr = u.get("指す物") or {}
            nm = ptr.get("指標の記録") or ptr.get("部品の記録")
            roles, weak = self._role_of(self.ind.record(nm))
            if not set(need) & set(roles):
                continue
            if weak and nm not in unconfirmed:
                unconfirmed.append(nm)
            out.append(u)
        return out

    def solve(self, no: str, style: str = STYLE) -> dict:
        """数の名前を値に解き、動く条件が指す使い方の行を添える。

        1本に決まれば「使い方の行」、0本なら「使える物が無い」、2本以上なら「候補が複数」に入れて返す。止めない（指標を足す・止めるだけで全体を止めないため）。
        """
        row = self.row(no)
        out = {"行": self._resolve(copy.deepcopy(row), style), "使い方の行": [], "使える物が無い": [], "候補が複数": [], "役割が未確認": []}
        sides = self._sides_of(row)
        for elem, tree in row.items():
            if (self.defs[elem].get("形の決まり") or {}).get("値の種類") != "条件の束":
                continue
            for conds in tree.values():
                for c in conds:
                    want = c.get("指す物") or {}
                    if "使い方の種類" not in want and "教科書の役割" not in want:
                        continue
                    hit = self._usages_of(c, sides, out["役割が未確認"])
                    if len(hit) == 1:
                        out["使い方の行"].append(hit[0])
                    elif not hit:
                        out["使える物が無い"].append(want)
                    else:
                        out["候補が複数"].append({"指す物": want, "候補": hit})
        return out

    # ── 文書 ─────────────────────────────────────────────────────────────
    def doc(self) -> str:
        k = self.key
        lines = ["# 法則一覧（レベル3 の法則のデータ）", "",
                 "★この文書は `scripts/priority_rebuild/laws/laws.py --write` が laws.json から作った（手で書き替えない・`--verify` で見る）。",
                 "★engine_tuner はまだ laws.json を読まない（196番・M3-1・M4）。相場の法則と組み合わせの法則は195番で入る。", ""]
        for kubun in self.choices("区分"):
            rows = [r for r in self.lines if r[k["区分"]] == kubun]
            lines.append(f"## {kubun}（{len(rows)}件）")
            lines.append("")
            if rows:
                lines += ["| 番号 | 文 | 級と出どころ | オン/オフ |", "|---|---|---|---|"]
                for r in rows:
                    g = r.get(k["級"]) or {}
                    txt = str(r.get(k["文"])).replace("|", "／")
                    lines.append(f"| {r[k['番号']]} | {txt} | {g.get('級', '')}・{g.get('出どころ', '')} | {'オン' if self._on(r) else 'オフ'} |")
                lines.append("")
        lines += [f"## 法則の中の数（{len(self.numbers)}件）", "", "| 名前 | 単位 | 範囲 | 代表の値 | 出どころ |", "|---|---|---|---|---|"]
        for n in self.numbers.values():
            rng = n.get("範囲")
            r_txt = f"{rng['lo']}〜{rng['hi']}" if rng else "未設定"
            lines.append(f"| {n['名前']} | {n.get('単位') or '未設定'} | {r_txt} | {n.get('代表の値') or '未設定'} | {n.get('出どころ')} |")
        return "\n".join(lines) + "\n"

    # ── 写す元との照らし ─────────────────────────────────────────────────
    def check_sources(self, pr: Path = PR) -> list:
        """写す元と比べる。写す元を見つけられない・読めないときも違いとして出す（黙って「違い0件」と言わない）。"""
        ng = []

        def text(path: Path):
            try:
                return path.read_text(encoding="utf-8")
            except OSError:
                ng.append(f"写す元を読めない: {path.name}")
                return None

        def assign_of(path: Path, name: str):
            src = text(path)
            for node in (ast.parse(src).body if src is not None else []):
                if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == name:
                    return node
            if src is not None:
                ng.append(f"写す元を読めない: {path.name} に {name} が無い")
            return None

        def load(path: Path):
            src = text(path)
            return json.loads(src) if src is not None else None

        node = assign_of(pr / "engine_tuner_exec.py", "FORM_SPEC")
        if node is not None:
            src = {}
            for key, val in zip(node.value.keys, node.value.values):
                d = {kw.arg: ast.literal_eval(kw.value) for kw in val.keywords}
                src[ast.literal_eval(key)] = {jp: d[en] for en, jp in FORM_FIELDS}
            mine = {n: {a: b for a, b in r.items() if a != "名前"} for n, r in self.forms.items()}
            if src != mine:
                ng.append("写す元と違う: 条件の書き方（engine_tuner_exec.py の FORM_SPEC）")
        node = assign_of(pr / "indicator_reference_diag.py", "STATE_COLS")
        if node is not None and set(ast.literal_eval(node.value)) != set(self.states):
            ng.append("写す元と違う: 玉の状態（indicator_reference_diag.py の STATE_COLS）")
        lim = load(pr / "recipes" / "search_limits.json")
        iref = text(pr / "indicator_reference_diag.py")
        rules = load(pr.parents[1] / ".claude" / "ratchet" / "exit_families_rules.json")
        for n in self.numbers.values():
            where = str(n.get("出どころ"))
            m = re.fullmatch(r"recipes/search_limits\.json の ([\w.]+)", where)
            if m:
                v = lim
                for part in m.group(1).split("."):
                    v = v.get(part) if isinstance(v, dict) else None
                if v is None:
                    ng.append(f"写す元と違う: {n['名前']}（{m.group(1)} が無い）")
                    continue
                lo, hi = v.get("lo", v.get("lo_bars")), v.get("hi", v.get("hi_bars"))
                if (lo, hi) != (n["範囲"]["lo"], n["範囲"]["hi"]):
                    ng.append(f"写す元と違う: {n['名前']}（元 {lo}〜{hi}・laws.json {n['範囲']['lo']}〜{n['範囲']['hi']}）")
                continue
            if re.fullmatch(r"recipes/identity_s1_legacy\.json:\d+", where):
                continue                                  # S1 の値は T44 が比べる
            m = re.fullmatch(r"indicator_reference_diag\.py の CONST_REGISTRY の (\w+)", where)
            if m:
                g = re.search(rf'"{m.group(1)}": dict\(value=([0-9.]+)', iref or "")
                if not g or float(g.group(1)) != (n.get("代表の値") or {}).get(STYLE):
                    ng.append(f"写す元と違う: {n['名前']}（CONST_REGISTRY の {m.group(1)}）")
                continue
            if re.fullmatch(r"exit_families_rules\.json:\d+", where):
                got = {b["confirm_max"] for b in ((rules or {}).get("branch_types") or {}).values() if "confirm_max" in b}
                if got != {(n.get("代表の値") or {}).get(STYLE)}:
                    ng.append(f"写す元と違う: {n['名前']}（confirm_max {sorted(got)}）")
                continue
            ng.append(f"出どころの文の形を読めない: {n['名前']} の {where!r}")
        ng += self._check_types(rules) + self._check_sellers(load(pr / "e38_logics.json"), load(pr / "recipes" / "identity_s1_legacy.json"))
        return ng

    def _check_types(self, rules) -> list:
        """枝の型を exit_families_rules.json と比べる。"""
        ng = []
        types = (rules or {}).get("branch_types")
        if not types:
            return ["写す元を読めない: exit_families_rules.json の branch_types"]
        mine = {r[self.key["番号"]][len("枝型-"):]: r for r in self.lines if str(r[self.key["番号"]]).startswith("枝型-")}
        for nm in sorted(set(types) ^ set(mine)):
            ng.append(f"写す元と違う: 枝の型 {nm} が片方にしか無い")
        for nm in set(types) & set(mine):
            b, r = types[nm], mine[nm]
            pl, how = b["placement"], r.get("決済のしかた") or {}
            fire, conds = b.get("fire") or [], (r.get("動く条件") or {}).get("全部満たす") or []
            want = {"文": b["jp"] == r.get(self.key["文"]), "決済の理由": b["reason"] == r.get("決済の理由"),
                    "置き方": {"resting": "足の途中に置く", "on_close": "足の終わり"}[pl["kind"]] == how.get("置き方"),
                    "fill": {"profit": "利の側", "adverse": "損の側", None: None}[pl.get("fill")] == how.get("側"),
                    "pessimistic": bool(pl.get("pessimistic")) == ("値段が飛んだときの約定" in how),
                    "動く条件の本数": len(fire) == len(conds),
                    "negative": [bool(f.get("negative")) for f in fire] == [bool(c.get("値を負にするか")) for c in conds]}
            ng += [f"写す元と違う: 枝型-{nm} の {k}" for k, ok in want.items() if not ok]
        return ng

    def _check_sellers(self, logics, s1) -> list:
        """売り方の行を e38_logics.json と比べる。S1 の計算の関数はレシピの entry.type と比べる。"""
        if not logics or not s1:
            return ["写す元を読めない: 売り方の文と方向"]
        ng = []
        by_id = {x["id"]: x for x in logics.get("logics") or []}
        for r in self.lines:
            if r[self.key["区分"]] != "売り方":
                continue
            lid = str(r[self.key["番号"]])[len("売り方"):]
            lg = by_id.get(lid)
            if lg is None:
                ng.append(f"写す元と違う: {r[self.key['番号']]} が e38_logics.json に無い")
                continue
            func = s1["entry"]["type"] if lid == "S1" else (lg.get("entry") or {}).get("type")
            want = {"文": lg["label"] == r.get(self.key["文"]), "方向": lg["side"].upper() == r.get(self.key["売買の方向"]), "計算の関数": func == r.get("計算の関数")}
            ng += [f"写す元と違う: {r[self.key['番号']]} の {k}" for k, ok in want.items() if not ok]
        return ng


_CACHE: dict = {}


def load(path=None) -> Laws:
    p = Path(path) if path else JSON_PATH
    key = str(p)
    if key not in _CACHE:
        if not p.is_file():
            _stop(f"laws.json が無い・読めない: {p}")
        _CACHE[key] = Laws(json.loads(p.read_text(encoding="utf-8")))
    return _CACHE[key]


# ── 自己テスト（自分の中の小さな見本・本物は読まない）──────────────────────
class _Ind:
    table = {"選べる値": {"役割の区分の表": {"向き": {"札": "トレンド"}, "行き過ぎ": {"札": "オシレーター"}}}}
    _c = {"場面": ["レンジ", "上げ"], "玉の向き": ["SHORT", "LONG"], "時間足": ["5m", "15m"], "値の単位": ["%"], "売買スタイル": ["スキャル", "デイトレ"]}

    extra: list = []
    drop: tuple = ()

    def choices(self, name):
        return self._c[name]

    def names(self, kind="指標の記録"):
        return ["部品P"] if kind == "部品の記録" else ["X", "Y", "Z"]

    def usages(self):
        base = [{"指す物": {"指標の記録": "X"}, "使い方の種類": "前提崩れの印", "場面と型": {"場面": "レンジ", "型": "t"}, "時間足": ["5m"], "閾値": [{"形": "値", "代表の値": {"スキャル": 1}}]},
                {"指す物": {"指標の記録": "Y"}, "使い方の種類": "前提崩れの印", "場面と型": {"場面": "レンジ", "型": "t"}, "時間足": ["5m"]}]
        return [u for u in base + self.extra if u["指す物"].get("指標の記録") not in self.drop]

    def record(self, nm):
        return {"X": {"教科書の役割": {"区分": None, "札": "トレンド"}}, "Y": {"教科書の役割": {"区分": ["行き過ぎ"]}},
                "Z": {"教科書の役割": {"区分": ["向き"]}}, "部品P": {"教科書の役割": {"区分": ["向き"]}}}[nm]


def _sample() -> dict:
    def el(no, name, how, kind="文字", choice=None, used=None, on="オン"):
        r = {"番号": no, "要素の名前": name, "形の決まり": {"値の種類": kind, "選べる値の名前": choice}, "無いときの扱い": how, "オン/オフ": on}
        if used:
            r["使う区分"] = used
        return r
    tbl = {"要素": [el("⑤-1", "番号", "必ず要る"), el("⑤-3", "場面", "必ず要る", "選べる値から選ぶ", "場面"), el("⑤-4", "文", "必ず要る（一文）"),
                    el("⑤-5", "級と出どころ", "未設定"), el("⑤-7", "判定", "未設定"), el("⑤-10", "オン/オフと注意", "既定＝オン"),
                    el("⑤-11", "区分", "必ず要る", "選べる値から選ぶ", "区分", "全部"),
                    el("⑤-12", "売買の方向", "必ず要る", "選べる値から選ぶ", "売買の方向", ["売り方"]),
                    el("⑤-29", "どの売り方用か", "未設定", "法則の番号の並び", None, ["決済の枝", "玉全体の決済"]),
                    el("⑤-20", "決済のしかた", "必ず要る", "選べる値の組", "決済のしかた", ["決済の枝"]),
                    el("⑤-21", "値段の決め方", "未設定", "種類ごとの欄の値", "値段の決め方の種類", ["決済の枝"]),
                    el("⑤-22", "効く玉", "未設定", "条件の種類ごとの値", "効く玉の条件の種類", ["決済の枝"]),
                    el("⑤-23", "動く条件", "未設定", "条件の束", "動く条件が指せる物", ["決済の枝"]),
                    el("⑤-24", "決済の割合", "既定＝全部", "法則の中の数の名前", None, ["決済の枝"]),
                    el("⑤-30", "決済の理由", "必ず要る（決済の枝と、何をするかが「すぐ決済」の行）", "文字", None, ["決済の枝", "玉全体の決済"]),
                    el("⑤-31", "何をするか", "必ず要る", "選べる値から選ぶ", "玉全体の動き", ["玉全体の決済"]),
                    el("⑤-90", "試しのオフ", "未設定", on="オフ")],
           "選べる値": {"場面": {"表": "indicators.json の選べる値の場面"}, "法則だけが使う場面": ["共通"], "区分": ["売り方", "決済の枝", "玉全体の決済"], "売買の方向": ["SHORT", "LONG"],
                    "使えない単位": ["ドル", "値段"], "未作の部品": ["未作P"],
                    "決済のしかた": {"方法": ["指値", "成行"]},
                    "値段の決め方の種類": [{"種類": "建値から%", "欄": [{"名前": "幅", "形": "法則の中の数の名前"}]},
                                  {"種類": "直近", "欄": [{"名前": "代わり", "形": "値段の決め方（入れ子）か枝の名前"}]}],
                    "効く玉の条件の種類": [{"種類": "型", "形": "文字"}], "玉全体の動き": ["すぐ決済", "状態を付けて持ち続ける"],
                    "動く条件が指せる物": ["玉の状態", "教科書の役割", "値の読み方", "使い方の種類", "場面", "型", "時間足", "部品の名前"], "数だけの単位": ["本数", "ドル"], "枝の名前で指せる語": ["同じ案の利確の枝"]},
           "表の形": {"条件の1本": {"欄": [{"名前": x, "形": "文字（以上・以下・より上・より下）" if x == "側" else "文字"} for x in ("指す物", "条件の書き方", "側", "値", "入口の向きの逆か")], "つなぎ方": ["全部満たす"]}}}
    a = {"番号": "枝A", "区分": "決済の枝", "場面": "レンジ", "文": "見本A", "決済のしかた": {"方法": "指値"}, "値段の決め方": {"種類": "建値から%", "幅": "数1"},
         "効く玉": {"型": "t"}, "どの売り方用か": ["売り方A"], "決済の理由": "TP_FILLED",
         "動く条件": {"全部満たす": [{"指す物": {"玉の状態": "hold_min"}, "条件の書き方": "level", "側": "以上", "値": "数1"},
                                {"指す物": {"教科書の役割": "向き", "使い方の種類": "前提崩れの印", "場面": "レンジ", "型": "t", "時間足": "5m"}, "値": USE_THRESHOLD}]}}
    b = {"番号": "枝B", "区分": "決済の枝", "場面": "共通", "文": "見本B", "決済のしかた": {"方法": "成行"}, "値段の決め方": {"種類": "直近", "代わり": "枝A"}, "決済の理由": "TIME_EXIT"}
    c = {"番号": "全体C", "区分": "玉全体の決済", "場面": "レンジ", "文": "見本C", "何をするか": "状態を付けて持ち続ける"}
    s = {"番号": "売り方A", "区分": "売り方", "場面": "レンジ", "文": "見本S", "売買の方向": "SHORT"}
    return {TABLE_KEY: tbl, "法則の行": [a, b, c, s], "条件の書き方": [{"名前": "level"}], "玉の状態": [{"名前": "hold_min"}],
            "法則の中の数": [{"名前": "数1", "単位": "本数", "範囲": None, "代表の値": {"スキャル": 3}, "出どころ": "見本"}]}


def selftest() -> int:
    ok = []
    ind = _Ind()

    def t(name, good):
        ok.append((name, bool(good)))

    def stops(d, text):
        try:
            Laws(copy.deepcopy(d), reader=ind)
            return False
        except LawsError as e:
            return text in str(e)

    def bad(fn):
        d = _sample()
        fn(d)
        return d
    base = _sample()
    r = Laws(copy.deepcopy(base), reader=ind)
    t("決まり①: 定義表に無い欄で止まる", stops(bad(lambda d: d["法則の行"][0].update({"知らない欄": 1})), "定義表に無い欄"))
    t("決まり②: 無い欄は「無いときの扱い」で返す（未設定）", r.element("枝A", "級と出どころ") == UNDECIDED)
    t("決まり②: 無い欄は「無いときの扱い」で返す（既定）", r.element("枝A", "決済の割合") == "全部")
    try:
        r.element("枝A", "試しのオフ")
        t("決まり③: オフの要素で止まる", False)
    except LawsError as e:
        t("決まり③: オフの要素で止まる", "オフの要素は返さない" in str(e))
    t("決まり④: 選べる値に無い値で止まる", stops(bad(lambda d: d["法則の行"][0].update({"場面": "知らない"})), "選べる値に無い値"))
    t("決まり④: 組の中の値でも止まる", stops(bad(lambda d: d["法則の行"][0].update({"決済のしかた": {"方法": "知らない"}})), "選べる値に無い値"))
    off = bad(lambda d: d["法則の行"][2].update({"オン/オフと注意": {"状態": "オフ"}}))
    t("決まり⑤: オフの法則を返さない", [x["番号"] for x in Laws(off, reader=ind).rows()] == ["枝A", "枝B", "売り方A"])
    t("決まり⑥: 指されている法則を消すと止まる", stops(bad(lambda d: d["法則の行"].pop(0)), "指されている法則が無い"))
    t("決まり⑥: 指されている法則を止めると止まる", stops(bad(lambda d: d["法則の行"][0].update({"オン/オフと注意": {"状態": "オフ"}})), "指されている法則が無い"))
    t("決まり⑦: その区分で使わない欄で止まる", stops(bad(lambda d: d["法則の行"][2].update({"決済のしかた": {"方法": "指値"}})), "その区分で使わない欄"))
    t("決まり⑧: 必ず要るは、その区分の欄だけに掛かる", r.row("全体C")["番号"] == "全体C")
    t("決まり⑧: 必ず要る欄が無いと止まる", stops(bad(lambda d: d["法則の行"][0].pop("決済のしかた")), "必ず要る欄が無い"))
    t("決まり⑧: 決済の枝に決済の理由が無いと止まる", stops(bad(lambda d: d["法則の行"][0].pop("決済の理由")), "必ず要る欄が無い"))
    t("決まり⑨: 種類の表に無い種類で止まる", stops(bad(lambda d: d["法則の行"][0]["値段の決め方"].update({"種類": "知らない"})), "種類の表に無い種類"))
    t("決まり⑨: 種類の欄に無い欄で止まる", stops(bad(lambda d: d["法則の行"][0]["値段の決め方"].update({"知らない": 1})), "種類の欄に無い欄"))
    t("決まり⑩: 法則の中の数の名前が無いと止まる", stops(bad(lambda d: d["法則の行"][0]["値段の決め方"].update({"幅": "無い数"})), "指している名前が無い"))
    t("決まり⑩: 玉の状態の名前が無いと止まる", stops(bad(lambda d: d["法則の行"][0]["動く条件"]["全部満たす"][0]["指す物"].update({"玉の状態": "無い"})), "指している名前が無い"))
    t("決まり⑩: 条件の書き方の名前が無いと止まる", stops(bad(lambda d: d["法則の行"][0]["動く条件"]["全部満たす"][0].update({"条件の書き方": "無い"})), "指している名前が無い"))
    t("決まり⑪: 番号が重なると止まる", stops(bad(lambda d: d["法則の行"][1].update({"番号": "枝A"})), "番号が重なる"))
    s = r.solve("枝A")
    t("解く: 数の名前を値にする", s["行"]["値段の決め方"]["幅"] == 3)
    t("解く: 使い方の行を添え、役割の区分が空の指標を未確認に出す", [u["指す物"]["指標の記録"] for u in s["使い方の行"]] == ["X"] and s["役割が未確認"] == ["X"])
    more = bad(lambda d: d["法則の行"].append({"番号": "枝D", "区分": "決済の枝", "場面": "レンジ", "文": "見本D", "決済のしかた": {"方法": "指値"}, "決済の理由": "TP_FILLED"}))
    t("足す: 行を足すと返す", "枝D" in [x["番号"] for x in Laws(more, reader=ind).rows()])
    add = bad(lambda d: d[TABLE_KEY]["要素"].append({"番号": "⑤-99", "要素の名前": "足した欄", "形の決まり": {}, "無いときの扱い": "未設定", "オン/オフ": "オン"}))
    t("足す: 定義表に欄を足すと、行を直さずに読める", Laws(add, reader=ind).element("枝A", "足した欄") == UNDECIDED)
    t("文書: 行の番号が出る", "| 枝A | 見本A |" in r.doc())
    # 止める操作（監査 CP100 の修正1）
    both = bad(lambda d: [x.update({"オン/オフと注意": {"状態": "オフ"}}) for x in d["法則の行"] if x["番号"] in ("枝A", "枝B")])
    t("止める: 指す行も指される行も全部オフなら止まらない", [x["番号"] for x in Laws(both, reader=ind).rows()] == ["全体C", "売り方A"])
    seller_off = bad(lambda d: d["法則の行"][3].update({"オン/オフと注意": {"状態": "オフ"}}))
    t("止める: 法則の番号の並びが指す売り方をオフにしても止まらない", "枝A" in [x["番号"] for x in Laws(seller_off, reader=ind).rows()])

    # 足す操作（監査 CP100 の修正7）
    def ind_with(extra=(), drop=()):
        i = _Ind()
        i.extra, i.drop = list(extra), tuple(drop)
        return i

    def use(nm, side, kind="指標の記録"):
        return {"指す物": {kind: nm}, "使い方の種類": "前提崩れの印", "場面と型": {"場面": "レンジ", "型": "t"}, "時間足": ["5m"], "玉の向き": side}
    s2 = Laws(copy.deepcopy(base), reader=ind_with([use("X", "LONG")])).solve("枝A")
    t("足す: ロングの行を足しても、ショートの枝が解ける", len(s2["使い方の行"]) == 1 and s2["候補が複数"] == [])
    s3 = Laws(copy.deepcopy(base), reader=ind_with([use("Z", "SHORT")])).solve("枝A")
    t("足す: 同じ役割の別の指標を足すと、候補が複数と出る", s3["使い方の行"] == [] and len(s3["候補が複数"]) == 1)
    s4 = Laws(copy.deepcopy(base), reader=ind_with([use("部品P", "SHORT", "部品の記録")])).solve("枝A")
    t("足す: 部品の行で落ちない", len(s4["候補が複数"]) == 1)
    s5 = Laws(copy.deepcopy(base), reader=ind_with(drop=("X",))).solve("枝A")
    t("足す: 指標を止めると、使える物が無いと出て止まらない", len(s5["使える物が無い"]) == 1)
    # 足りなかった決まり（監査 CP100 の修正8）
    typo = bad(lambda d: d["法則の行"][2].update({"オン/オフと注意": {"状態": "おふ"}}))
    t("オン/オフ: 打ち間違いをオンにしない", "全体C" not in [x["番号"] for x in Laws(typo, reader=ind).rows()])

    def num(**kw):
        return bad(lambda d: d["法則の中の数"][0].update(kw))

    def ptr(**kw):
        return bad(lambda d: d["法則の行"][0]["動く条件"]["全部満たす"][1]["指す物"].update(kw))
    t("決まり⑫: 範囲の形でないと止まる", stops(num(範囲={"lo": "a", "hi": 3}), "範囲の形でない値"))
    t("決まり⑫: lo と hi が逆だと止まる", stops(num(範囲={"lo": 5, "hi": 3}), "範囲の形でない値"))
    t("決まり⑫: 代表の値が範囲の外だと止まる", stops(num(範囲={"lo": 5, "hi": 9}), "代表の値が範囲の外"))
    t("決まり⑫: 数の名前が重なると止まる", stops(bad(lambda d: d["法則の中の数"].append(dict(d["法則の中の数"][0]))), "数の名前が重なる"))
    t("決まり⑫: ドルの単位で止まる", stops(num(単位="ドル"), "使えない単位"))
    t("決まり⑬: 時間足が選べる値に無いと止まる", stops(ptr(時間足="9m"), "の時間足"))
    t("決まり⑬: 場面が選べる値に無いと止まる", stops(ptr(場面="無い"), "の場面"))
    t("決まり⑬: 部品が無いと止まる", stops(ptr(部品の名前="無い"), "の部品"))
    t("決まり⑬: 未作の部品の表に在れば通る", isinstance(Laws(ptr(部品の名前="未作P"), reader=ind), Laws))
    t("決まり⑬: 読まない値の読み方で止まる", stops(ptr(値の読み方="%"), "読む口が読まない欄"))
    t("決まり⑬: 側が表の形に無いと止まる", stops(bad(lambda d: d["法則の行"][0]["動く条件"]["全部満たす"][0].update({"側": "上"})), "の側"))
    # 写す元を読めないときは「違い0件」と言わない（監査 CP100 の修正11）
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        pr = Path(td) / "a" / "b"
        pr.mkdir(parents=True)
        ng = r.check_sources(pr)
    t("写す元: 読めないときは違いとして出す", any("写す元を読めない" in x for x in ng) and any("出どころの文の形を読めない" in x for x in ng))
    for name, good in ok:
        print(f"  {'✅' if good else '❌'} {name}")
    n_ng = sum(1 for _n, g in ok if not g)
    print(f"法則の読む口の自己テスト＝{len(ok) - n_ng}/{len(ok)}")
    return 0 if n_ng == 0 else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--write" in sys.argv:
        DOC_PATH.write_text(load().doc(), encoding="utf-8")
        print(f"書いた: {DOC_PATH}")
        return 0
    if "--verify" in sys.argv:
        if not DOC_PATH.is_file() or DOC_PATH.read_text(encoding="utf-8") != load().doc():
            print(f"{PREFIX} 文書が作り直した物と違う: {DOC_PATH}")
            return 1
        print("法則一覧.md は作り直した物と同じ")
        return 0
    if "--check-sources" in sys.argv:
        ng = load().check_sources()
        for x in ng:
            print(f"{PREFIX} {x}")
        if not ng:
            print("写す元との照らし＝違い0件")
        return 1 if ng else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
