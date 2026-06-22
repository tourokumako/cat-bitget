"""
ratchet_io.py — 全戦略・全ツール共有の「出力の保管インフラ」（read 専用の命名/移動のみ・net 不関与）。

まこさん指示（2026-06-22）: e36 限定でなく e37/e38/e39… どの戦略でも同じく
  ① タグ＋自動連番でユニーク命名（実験出力が衝突しない）
  ② 出力先が既存なら絶対に上書きせず archive へ逃がしてから書く（過去を保全）
  ③ 新実験を書く前に同 stem の旧実験出力（trades/report/analysis/params）を archive へ（直下＝現役のみ）
を効かせる。analysis_playbook §3.1（直下=現役のみ・過去は archive・記録は履歴保全）の物理化。

⚠️ 本モジュールは「ファイル名と置き場所」だけを扱う＝売買記録の net 列・判定器（score.py/eval_engine）に
   一切触れない（H13）。pdca_mark の実験/審判検知には乗らない（戦略でも審判でもない共通基盤）。

既知答えテスト: `python3 ratchet_io.py` で _known_answer() が走る（連番／archive_if_exists／
  archive_prior_experiments／番人メタ確認＝わざと既存を作って上書きされないことを確認）。
"""
from __future__ import annotations

import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]               # bitget-python-sdk-api/
RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"      # 売買記録・記録の置き場（e35.RATCHET と同一）

# 出力ファミリの接頭辞（trades=売買記録 / report_/analysis_=記録 / それらの params サイドカーも含む）
_OUT_PREFIXES = ("trades_", "report_trades_", "analysis_trades_")
# タグ連番トークン `_NNN`（後ろが . か _ か末尾）= タグ付き実験ファイルの目印。安定名(base)には現れない。
_SEQ_RE = re.compile(r"_\d{3}(?=[._]|$)")


def tagged_suffix(stem: str, default_suffix: str, tag: str | None, ratchet_dir: pathlib.Path | None = None) -> str:
    """出力CSVの suffix を決める（命名のみ・net 不変）。
    - tag が falsy → default_suffix（戦略の安定名・--vs 固定の現役 base・完全互換）。
    - tag 指定     → `_<tag>_<NNN>`（NNN=ratchet_dir 直下の既存 `trades_{stem}_<tag>_NNN.csv` を走査し max+1・
                     3桁ゼロ埋め・毎走で新番号＝既存を物理的に上書きしない）。
    report/analyze/png は入力CSV名から自動命名なので、CSV名がユニークになれば自動で追従する。"""
    if not tag:
        return default_suffix
    rd = ratchet_dir or RATCHET
    base = f"_{tag}"
    pat = re.compile(rf"^trades_{re.escape(stem)}{re.escape(base)}_(\d{{3}})(?:_train|_score)?\.csv$")
    mx = 0
    for p in rd.glob(f"trades_{stem}{base}_*.csv"):
        m = pat.match(p.name)
        if m:
            mx = max(mx, int(m.group(1)))
    return f"{base}_{mx + 1:03d}"


def _split_name(name: str) -> tuple[str, str]:
    """ファイル名を (幹, 拡張子) に割る。複合拡張（_params.json）も素直に suffix で割る。"""
    p = pathlib.Path(name)
    return p.stem, p.suffix


def archive_if_exists(path) -> pathlib.Path:
    """書き出し直前に呼ぶ。`path` が既に在れば「同じ階層の archive/ へ move」してから返す
    ＝絶対に上書きしない（過去ファイルは必ず archive に保全）。archive 内でも同名が在れば `_prevNNN` を付ける。
    戻り値＝書き込み先 path（呼び出し側はこの後そこへ書く）。generic＝RATCHET でも VIZ_DIR でも効く。"""
    path = pathlib.Path(path)
    if path.exists():
        arch = path.parent / "archive"
        arch.mkdir(parents=True, exist_ok=True)
        dest = arch / path.name
        if dest.exists():
            stem, suf = _split_name(path.name)
            i = 1
            while (arch / f"{stem}_prev{i:03d}{suf}").exists():
                i += 1
            dest = arch / f"{stem}_prev{i:03d}{suf}"
        shutil.move(str(path), str(dest))
    return path


def archive_prior_experiments(stem: str, keep_suffix: str, ratchet_dir: pathlib.Path | None = None) -> list[str]:
    """新実験を書く前に呼ぶ。ratchet_dir 直下の「同 stem のタグ付き実験出力（trades/report/analysis/params）」のうち、
    今回の keep_suffix を含むもの と 安定名 base（タグ連番 `_NNN` を持たない現役）以外を archive へ move する。
    ＝直下を「現役 base ＋ 今回」だけに保つ（§3.1）。move したファイル名一覧を返す（ログ用）。他 stem は触らない。"""
    rd = ratchet_dir or RATCHET
    moved: list[str] = []
    if not rd.exists():
        return moved
    for p in sorted(rd.glob(f"*{stem}*")):
        if not p.is_file():
            continue
        name = p.name
        if not name.startswith(_OUT_PREFIXES):       # 出力ファミリ以外は触らない
            continue
        if keep_suffix and keep_suffix in name:       # 今回の出力 → 残す
            continue
        if not _SEQ_RE.search(name):                  # タグ連番 `_NNN` を持たない = 安定名 base（現役）→ 残す
            continue
        archive_if_exists(p)
        moved.append(name)
    return moved


def _known_answer() -> None:
    """既知答えテスト（tmp ディレクトリ・net 不参照）。`python3 ratchet_io.py` で走る。"""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        stem = "e36_short_oscillation"

        # (1) tagged_suffix: tag 無 → default 安定名。tag 有 → 001, 002 と連番が進む。
        assert tagged_suffix(stem, "_5m_shortset1", None, d) == "_5m_shortset1", "tag無は安定名"
        s1 = tagged_suffix(stem, "_5m_shortset1", "freqiter3", d)
        assert s1 == "_freqiter3_001", f"初回は 001: {s1}"
        (d / f"trades_{stem}_freqiter3_001.csv").write_text("x")
        (d / f"trades_{stem}_freqiter3_001_score.csv").write_text("x")
        s2 = tagged_suffix(stem, "_5m_shortset1", "freqiter3", d)
        assert s2 == "_freqiter3_002", f"既存001があれば次は 002: {s2}"

        # (2) archive_if_exists: 既存は archive/ へ逃げ、元 path が空く（＝上書きされない）。
        f = d / "report_trades_x.txt"
        f.write_text("old")
        ret = archive_if_exists(f)
        assert ret == f and not f.exists(), "既存は move されて元pathは空く"
        assert (d / "archive" / "report_trades_x.txt").read_text() == "old", "中身は archive に保全"
        # 番人メタ確認: もう一度同名を作って archive 済みと衝突 → _prev で保全（上書きしない）。
        f.write_text("old2")
        archive_if_exists(f)
        assert (d / "archive" / "report_trades_x_prev001.txt").read_text() == "old2", "archive内衝突は_prevで保全"

        # (3) archive_prior_experiments: 安定名 base と今回(keep)は残し、旧タグ実験だけ archive へ。
        for n in (f"trades_{stem}_5m_shortset1.csv",          # 安定名 base（_NNN無し）→ 残す
                  f"trades_{stem}_freqiter3_001.csv",          # 旧実験 → 退避
                  f"trades_{stem}_freqiter3_002.csv",          # 今回(keep) → 残す
                  f"report_trades_{stem}_freqiter3_001.txt"):  # 旧実験の記録 → 退避
            (d / n).write_text("x")
        moved = archive_prior_experiments(stem, "_freqiter3_002", d)
        assert (d / f"trades_{stem}_5m_shortset1.csv").exists(), "安定名 base は残す"
        assert (d / f"trades_{stem}_freqiter3_002.csv").exists(), "今回(keep)は残す"
        assert not (d / f"trades_{stem}_freqiter3_001.csv").exists(), "旧実験 trades は退避"
        assert not (d / f"report_trades_{stem}_freqiter3_001.txt").exists(), "旧実験 record は退避"
        # step(1) で作った _001_score.csv も「旧実験(keep以外)」として一緒に退避される（正しい挙動）。
        assert set(moved) == {f"trades_{stem}_freqiter3_001.csv",
                              f"trades_{stem}_freqiter3_001_score.csv",
                              f"report_trades_{stem}_freqiter3_001.txt"}, moved
        # keep(_002) と base は moved に含まれない。
        assert all("_freqiter3_002" not in m and "_5m_shortset1" not in m for m in moved), moved

    print("ratchet_io 既知答えテスト: 全 PASS（連番／archive_if_exists／archive_prior_experiments／番人メタ確認）")


if __name__ == "__main__":
    _known_answer()
