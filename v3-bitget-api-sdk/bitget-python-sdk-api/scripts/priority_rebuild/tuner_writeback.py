#!/usr/bin/env python3
"""tuner_writeback.py — engine_tuner が見つけた値を設定ファイルへ書き戻す（要件 R9・まこさん OK 2026-08-02）

なぜ要るか
--------------------------------------------------------------------------
engine_tuner は、ツマミの数字の組み合わせを何百通りも試します。
試し終わると、一番良かった組み合わせを画面と試行ログに出します。
いまは、その数字を人が手で設定ファイルへ打ち込みます。打ち間違いが起きます。
要件 R9 の完了の線は3つです。
  1 採択した値を設定ファイルへ書き戻せること
  2 書き戻す前に差分が出ること
  3 上書きの前に元の値が残ること

この道具がやること
--------------------------------------------------------------------------
  1 この道具は、engine_tuner が見つけた一番良い値を受け取ります。
  2 この道具は、その値を設定ファイルのどこに入れるかを機械で探します。
  3 この道具は、何を何に変えるかを画面に出します。あわせてファイルにも残します。
  4 この道具は、--apply が付いたときだけ書きます。付いていなければ1バイトも書きません。
  5 この道具は、書く前に元のファイルを日付と時刻を付けた名前でコピーします。

止める場合
--------------------------------------------------------------------------
  ・値の名前が設定ファイルのどこにも見つからないときに、止まります。黙って捨てません。
  ・同じ名前が設定ファイルの2箇所以上にあるときに、止まります。どちらへ入れるか決められないためです。
  ・戦略が設定ファイルを持っていないときに、止まります。
  ・書いたあとに設定ファイルが読めなくなったときに、止まります。元のファイルへ戻します。

正直に言う限界
--------------------------------------------------------------------------
E37 は設定ファイルを持っていません。値は e37_scalp.py の中に定数として書いてあります。
ですから、この道具は E37 に書き戻せません。書き戻せるのは E38 だけです。
この限界は、歩6 で E37 を設定ファイルの形へ移すまで残ります。

使い方
--------------------------------------------------------------------------
  差分を見るだけ
    python3 scripts/priority_rebuild/tuner_writeback.py --strategy e38 --logic S2 \
        --values '{"tp1_frac": 0.5, "sl_zone_k": 1.2}'
  試行ログから拾う
    python3 scripts/priority_rebuild/tuner_writeback.py --strategy e38 --logic S2 \
        --from-log scripts/priority_rebuild/engine_tuner_e38_S2.log --trial 137
  実際に書く
    上のどちらかに --apply を足します。
  番人
    python3 scripts/priority_rebuild/tuner_writeback.py --selftest
"""
from __future__ import annotations

import argparse
import ast
import datetime
import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[2]
REC_DIR = ROOT / "results" / "priority_rebuild" / "ratchet" / "writeback"


class WritebackError(SystemExit):
    """書き戻せない理由が見つかったので止めます。黙って進めません。"""


# ══ 設定ファイルの場所を接続ファイルから引く ═══════════════════════════════════════
def translate(strategy: str, logic_id: str, values: dict) -> tuple[dict, list[tuple[str, str]]]:
    """試行の値を、設定ファイルの欄の名前へ言い換えます。

    言い換えの規則は接続ファイルが持ちます。設定ファイルの形を知っているのは接続ファイルだけ、
    といういまの作りに合わせています。規則を持たない戦略では、名前をそのまま使います。
    """
    from tuner_adapters import load_adapter
    fn = getattr(load_adapter(strategy), "writeback_map", None)
    if fn is None:
        return dict(values), []
    return fn(logic_id, values)


def config_path(strategy: str) -> pathlib.Path:
    """その戦略の設定ファイルの場所を返します。持っていなければ止めます。"""
    from tuner_adapters import load_adapter
    ad = load_adapter(strategy)
    cfg = getattr(ad, "CONFIG", None)
    if cfg is None:
        raise WritebackError(
            f"[書き戻しエラー] {strategy} は設定ファイルを持っていません。\n"
            f"  値は実装のファイルの中に定数として書いてあります。この道具では書き戻せません。\n"
            f"  E37 がこれに当たります。歩6 で設定ファイルの形へ移すまで、この限界は残ります。")
    p = pathlib.Path(cfg)
    if not p.exists():
        raise WritebackError(f"[書き戻しエラー] 設定ファイルが見つかりません: {p}")
    return p


# ══ 値をどこへ入れるかを機械で探す ═══════════════════════════════════════════════
def find_slots(logic: dict, name: str) -> list[list]:
    """設定の中から、その名前の入れ先を全部探します。入れ先は鍵の並びで返します。"""
    found: list[list] = []

    def walk(node, path: list) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k == name and not isinstance(v, (dict, list)):
                    found.append(path + [k])
                walk(v, path + [k])
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + [i])

    walk(logic, [])
    return found


def get_at(node, path: list):
    for k in path:
        node = node[k]
    return node


def set_at(node, path: list, value) -> None:
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value


def find_logic(cfg: dict, logic_id: str) -> dict:
    """設定の中から、そのロジックの定義を1つ取り出します。"""
    for x in cfg.get("logics") or []:
        if isinstance(x, dict) and x.get("id") == logic_id:
            return x
    ids = [x.get("id") for x in (cfg.get("logics") or []) if isinstance(x, dict)]
    raise WritebackError(
        f"[書き戻しエラー] ロジック {logic_id} が設定ファイルにありません。\n"
        f"  設定にあるロジック: {ids}")


def plan(cfg: dict, logic_id: str, values: dict) -> list[tuple[str, list, object, object]]:
    """何を何に変えるかの一覧を作ります。1つでも入れ先が決まらなければ止めます。"""
    logic = find_logic(cfg, logic_id)
    rows: list[tuple[str, list, object, object]] = []
    missing: list[str] = []
    ambiguous: list[str] = []
    for name, new in values.items():
        slots = find_slots(logic, name)
        if not slots:
            missing.append(name)
            continue
        if len(slots) > 1:
            ambiguous.append(f"{name} は {len(slots)} 箇所")
            continue
        path = slots[0]
        rows.append((name, path, get_at(logic, path), new))
    if missing:
        raise WritebackError(
            f"[書き戻しエラー] 次の値の名前が設定ファイルに見つかりません: {', '.join(missing)}\n"
            f"  黙って捨てません。設定ファイルに入れ先を作るか、値の名前を直してください。")
    if ambiguous:
        raise WritebackError(
            f"[書き戻しエラー] 次の値の名前が設定ファイルの2箇所以上にあります: {', '.join(ambiguous)}\n"
            f"  どちらへ入れるか決められないので止めます。")
    return rows


# ══ 値の受け取り方 ═════════════════════════════════════════════════════════════
def values_from_log(log_path: pathlib.Path, trial: int) -> dict:
    """engine_tuner の試行ログの1行から、その試行の値を取り出します。"""
    if not log_path.exists():
        raise WritebackError(f"[書き戻しエラー] 試行ログが見つかりません: {log_path}")
    want = f"T{trial}"
    for ln in log_path.read_text(encoding="utf-8").splitlines():
        cols = ln.split("\t")
        if not cols or cols[0] != want:
            continue
        for c in reversed(cols):
            c = c.strip()
            if c.startswith("{"):
                try:
                    d = ast.literal_eval(c)
                except Exception as e:                          # noqa: BLE001
                    raise WritebackError(f"[書き戻しエラー] 試行 {trial} の値を読めません: {e}")
                if isinstance(d, dict):
                    return d
        raise WritebackError(f"[書き戻しエラー] 試行 {trial} の行に値の組が入っていません")
    raise WritebackError(f"[書き戻しエラー] 試行 {trial} が試行ログにありません: {log_path.name}")


# ══ 書く ═══════════════════════════════════════════════════════════════════════
def backup(path: pathlib.Path) -> pathlib.Path:
    """上書きの前に、元のファイルを日付と時刻を付けた名前でコピーします。"""
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = path.with_name(f"{path.stem}.backup_{stamp}{path.suffix}")
    shutil.copy2(path, dst)
    return dst


def render(strategy: str, logic_id: str, path: pathlib.Path, rows: list,
           applied: bool, bak: pathlib.Path | None,
           unused: list[tuple[str, str]] | None = None) -> str:
    """差分を文字にします。画面とファイルで同じ文字を使います。"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state = "書きました" if applied else "まだ書いていません。--apply が付いていません"
    out = ["=" * 92,
           f"設定ファイルへの書き戻し ／ {strategy} の {logic_id}",
           "=" * 92,
           f"日時          : {now}",
           f"設定ファイル  : {path}",
           f"書いたかどうか: {state}"]
    if bak:
        out.append(f"元のファイル  : {bak.name}")
    out += ["", f"{'値の名前':<20} {'入れ先':<34} {'いまの値':>14}  →  新しい値", "-" * 92]
    for name, keys, old, new in rows:
        where = ".".join(str(k) for k in keys)
        out.append(f"{name:<20} {where:<34} {str(old):>14}  →  {new}")
    if unused:
        # ★使わなかった値も必ず出します。黙って捨てたと思われないためです。
        out += ["", f"[使わなかった値 {len(unused)} 件]"]
        for name, why in unused:
            out.append(f"  {name:<20} {why}")
    out += ["",
            "★この値は engine_tuner が値決め窓で選んだものです。採点窓では選んでいません。",
            "★採否は別です。採点窓で score.py に通して、まこさんが決めます。"]
    return "\n".join(out)


def record(text: str, strategy: str, logic_id: str) -> pathlib.Path | None:
    """差分をファイルに残します。画面だけだと流れて消えるためです。"""
    try:
        REC_DIR.mkdir(parents=True, exist_ok=True)
        day = datetime.datetime.now().strftime("%Y%m%d")
        stem = f"writeback_{strategy}_{logic_id}_{day}"
        n = len(list(REC_DIR.glob(f"{stem}_*.txt"))) + 1
        p = REC_DIR / f"{stem}_{n:03d}.txt"
        p.write_text(text + "\n", encoding="utf-8")
        return p
    except Exception as e:                                      # noqa: BLE001
        print(f"[記録の保存に失敗しました。差分そのものには影響しません] {e}")
        return None


def write_back(path: pathlib.Path, logic_id: str, rows: list) -> pathlib.Path:
    """元をコピーしてから書きます。書いたあとに読めなければ元へ戻します。"""
    bak = backup(path)
    cfg = json.loads(path.read_text(encoding="utf-8"))
    logic = find_logic(cfg, logic_id)
    for _name, keys, _old, new in rows:
        set_at(logic, keys, new)
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:                                      # noqa: BLE001
        shutil.copy2(bak, path)
        raise WritebackError(f"[書き戻しエラー] 書いたあとに設定ファイルが読めません: {e}\n"
                             f"  元のファイルへ戻しました。戻した元は {bak.name} です。")
    return bak


def run(strategy: str, logic_id: str, values: dict, apply: bool) -> int:
    path = config_path(strategy)
    mapped, unused = translate(strategy, logic_id, values)
    cfg = json.loads(path.read_text(encoding="utf-8"))
    rows = plan(cfg, logic_id, mapped)
    if not rows:
        raise WritebackError("[書き戻しエラー] 書き戻す値が1つもありません")
    bak = write_back(path, logic_id, rows) if apply else None
    text = render(strategy, logic_id, path, rows, apply, bak, unused)
    print(text)
    p = record(text, strategy, logic_id)
    if p:
        print(f"\n[記録] {p}")
    if not apply:
        print("\n※ まだ書いていません。この内容でよければ、同じコマンドの後ろに --apply を足してください。")
    return 0


# ══ 番人（合成データのみ・本物の設定ファイルを書き換えない）═════════════════════════
def selftest() -> int:
    import tempfile
    ng: list[str] = []
    sample = {
        "schema_version": 1,
        "logics": [
            {"id": "S2",
             "entry": {"params": {"pos_min": None, "confirm": None}},
             "exit": {"params": {"tp1_frac": None, "sl_zone_k": None}},
             "params": {"max_lots": 2}},
            {"id": "L1",
             "entry": {"params": {"pos_min": 0.3}},
             "exit": {"params": {"tp1_frac": 0.5}}},
        ],
    }
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "sample_logics.json"
        p.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
        before = p.read_text(encoding="utf-8")

        # ① 入れ先を1つだけ見つける
        rows = plan(json.loads(before), "S2", {"tp1_frac": 0.42, "pos_min": 0.11})
        got = {r[0]: ".".join(str(k) for k in r[1]) for r in rows}
        if got != {"tp1_frac": "exit.params.tp1_frac", "pos_min": "entry.params.pos_min"}:
            ng.append(f"① 入れ先の探し方が違います: {got}")

        # ② 見つからない名前で止まる
        try:
            plan(json.loads(before), "S2", {"no_such_key": 1})
            ng.append("② 見つからない名前で止まりません")
        except WritebackError:
            pass

        # ③ 無いロジックで止まる
        try:
            plan(json.loads(before), "S9", {"tp1_frac": 1})
            ng.append("③ 無いロジックで止まりません")
        except WritebackError:
            pass

        # ④ --apply が無ければ1バイトも書かない
        _ = render("e38", "S2", p, rows, False, None)
        if p.read_text(encoding="utf-8") != before:
            ng.append("④ --apply が無いのにファイルが変わりました")

        # ⑤ 書いたら元のコピーが残り、値が入り、読める
        bak = write_back(p, "S2", plan(json.loads(before), "S2",
                                       {"tp1_frac": 0.42, "pos_min": 0.11}))
        if not bak.exists():
            ng.append("⑤ 元のファイルのコピーが作られません")
        elif bak.read_text(encoding="utf-8") != before:
            ng.append("⑤ 元のファイルのコピーの中身が元と違います")
        after = json.loads(p.read_text(encoding="utf-8"))
        s2 = find_logic(after, "S2")
        if s2["exit"]["params"]["tp1_frac"] != 0.42 or s2["entry"]["params"]["pos_min"] != 0.11:
            ng.append(f"⑤ 値が入っていません: {s2}")
        if s2["exit"]["params"]["sl_zone_k"] is not None or s2["params"]["max_lots"] != 2:
            ng.append("⑤ 渡していない値まで変わりました")
        if find_logic(after, "L1")["exit"]["params"]["tp1_frac"] != 0.5:
            ng.append("⑤ 別のロジックの値まで変わりました")

        # ⑥ 同じ名前が2箇所にあれば止まる
        try:
            plan({"logics": [{"id": "S2", "a": {"x": 1}, "b": {"x": 2}}]}, "S2", {"x": 9})
            ng.append("⑥ 同じ名前が2箇所にあるのに止まりません")
        except WritebackError:
            pass

        # ⑦ 試行ログから拾える
        lg = pathlib.Path(d) / "t.log"
        lg.write_text("T0\t-1.0\t10\t0.5\t通過\t{'tp1_frac': 0.24, 'pos_min': 0.3}\n"
                      "T7\t+2.0\t20\t1.5\t通過\t{'tp1_frac': 0.77, 'pos_min': 0.9}\n",
                      encoding="utf-8")
        v = values_from_log(lg, 7)
        if v != {"tp1_frac": 0.77, "pos_min": 0.9}:
            ng.append(f"⑦ 試行ログから拾った値が違います: {v}")
        try:
            values_from_log(lg, 99)
            ng.append("⑦ 無い試行番号で止まりません")
        except WritebackError:
            pass

    # ⑧ 設定ファイルを持たない戦略で止まる
    try:
        config_path("e37")
        ng.append("⑧ 設定ファイルを持たない戦略で止まりません")
    except WritebackError:
        pass
    except Exception as e:                                      # noqa: BLE001
        ng.append(f"⑧ 別の理由で落ちました: {e}")

    # ⑨ 選ばれたしきい値だけが入り、選ばれなかったものは使わないと出る（本物の宣言で確かめる）
    vals = {"confirm_htf": "roc24_2h", "th_roc24_2h": 1.5, "th_macd_2h": 9.9,
            "confirm_vol": "none", "th_volr20_15m": 8.8, "tp1_frac": 0.4}
    mapped, unused = translate("e38", "S2", vals)
    if mapped.get("confirm_htf_th") != 1.5:
        ng.append(f"⑨ 選ばれたしきい値が入れ先へ入りません: {mapped}")
    if "th_macd_2h" in mapped or "th_volr20_15m" in mapped:
        ng.append("⑨ 選ばれなかったしきい値まで入れようとしています")
    if mapped.get("tp1_frac") != 0.4 or mapped.get("confirm_htf") != "roc24_2h":
        ng.append("⑨ しきい値でない値の名前が変わりました")
    names = {n for n, _w in unused}
    if names != {"th_macd_2h", "th_volr20_15m"}:
        ng.append(f"⑨ 使わない値の一覧が違います: {names}")

    # ⑩ 言い換えたあとの名前が、設定ファイルの入れ先と実際につながる
    try:
        real = json.loads(config_path("e38").read_text(encoding="utf-8"))
        rows = plan(real, "S2", mapped)
        where = {r[0]: ".".join(str(k) for k in r[1]) for r in rows}
        if where.get("confirm_htf_th") != "entry.params.confirm_htf_th":
            ng.append(f"⑩ 言い換えた名前が設定ファイルにつながりません: {where}")
    except WritebackError as e:
        ng.append(f"⑩ 本物の設定ファイルで入れ先が見つかりません: {e}")

    print("=" * 92)
    print("tuner_writeback 自己検査。合成データだけで試します。本物の設定ファイルは書き換えません。")
    print("=" * 92)
    print("  ① 入れ先を1つだけ見つける ② 見つからない名前で止まる ③ 無いロジックで止まる")
    print("  ④ --apply が無ければ1バイトも書かない ⑤ 元のコピーが残り値が入り読める")
    print("  ⑥ 同じ名前が2箇所にあれば止まる ⑦ 試行ログから拾える ⑧ 設定ファイルが無い戦略で止まる")
    print("  ⑨ 選ばれたしきい値だけが入る ⑩ 言い換えた名前が本物の設定ファイルとつながる")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="engine_tuner が見つけた値を設定ファイルへ書き戻します（要件 R9）")
    ap.add_argument("--strategy", default="e38",
                    help="接続ファイル名。設定ファイルを持つのは e38 だけです")
    ap.add_argument("--logic", help="設定ファイルの中のロジックの id。例 S2")
    ap.add_argument("--values", help="値の組を json の文字列で渡します")
    ap.add_argument("--from-log", help="engine_tuner の試行ログのパス")
    ap.add_argument("--trial", type=int, help="試行ログから拾う試行の番号")
    ap.add_argument("--apply", action="store_true",
                    help="これが付いたときだけ書きます。付いていなければ1バイトも書きません")
    ap.add_argument("--selftest", action="store_true", help="番人を走らせます")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.logic:
        raise WritebackError("[書き戻しエラー] --logic を指定してください")
    if a.values:
        values = json.loads(a.values)
    elif a.from_log and a.trial is not None:
        values = values_from_log(pathlib.Path(a.from_log), a.trial)
    else:
        raise WritebackError("[書き戻しエラー] --values か、--from-log と --trial の組を指定してください")
    return run(a.strategy, a.logic, values, a.apply)


if __name__ == "__main__":
    raise SystemExit(main())
