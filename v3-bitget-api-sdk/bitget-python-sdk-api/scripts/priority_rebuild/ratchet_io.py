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
ADOPTED_LEDGER = ROOT / ".claude" / "ratchet" / "adopted_strategies.md"   # 採用台帳（ADOPTED_BASE_FILES マーカーの正本）

# 出力ファミリの接頭辞（trades=売買記録 / report_/analysis_=記録 / それらの params サイドカーも含む）
_OUT_PREFIXES = ("trades_", "report_trades_", "analysis_trades_")
# タグ連番トークン `_NNN`（後ろが . か _ か末尾）= タグ付き実験ファイルの目印。安定名(base)には現れない。
_SEQ_RE = re.compile(r"_\d{3}(?=[._]|$)")


def _adopted_base_stems(ledger_path: pathlib.Path | None = None) -> tuple:
    """採用 base のファイル幹（台帳 adopted_strategies.md の機械可読マーカー ADOPTED_BASE_FILES に追従・
    コードに戦略名を焼かない＝PORTFOLIO_CHECK/ROLE_CHECK と同型・2026-07-03 まこさん承認）。
    背景: 採用 base はタグ連番名のまま（再走禁止＝タグ無し安定名を再発行できない）なので、同 stem の新実験の
    たびに archive_prior_experiments が採用 base ごと archive へ押し出していた（直下=現役のみ の逆転事案）。
    台帳マーカーに載る幹を含むファイルは押し出さない。マーカーが無い/読めない場合は空＝従来挙動（安全側）。"""
    try:
        txt = (ledger_path or ADOPTED_LEDGER).read_text(encoding="utf-8")
    except Exception:
        return ()
    m = re.search(r"ADOPTED_BASE_FILES:\s*([^>]+?)\s*-->", txt)
    if not m:
        return ()
    return tuple(s for s in re.split(r"[;,\s]+", m.group(1)) if s)


def tagged_suffix(stem: str, default_suffix: str, tag: str | None, ratchet_dir: pathlib.Path | None = None) -> str:
    """出力CSVの suffix を決める（命名のみ・net 不変）。
    - tag が falsy → default_suffix（戦略の安定名・--vs 固定の現役 base・完全互換）。
    - tag 指定     → `_<tag>_<NNN>`。NNN は【全タグ通し・直下＋archive 込み】の既存連番の max+1
                     ＝**同じ番号を二度出さない**（2026-06-24 まこさん指示・タグごとに 001 が乱立し番号重複した事案の是正）。
                     タグ名は保持し番号だけ全体ユニーク・3桁ゼロ埋め・毎走で新番号＝既存を物理的に上書きしない。
    report/analyze/png は入力CSV名から自動命名なので、CSV名がユニークになれば自動で追従する。"""
    if not tag:
        return default_suffix
    rd = ratchet_dir or RATCHET
    base = f"_{tag}"
    # 全タグ通しで NNN の最大を探す（タグ問わず・直下＋archive 両方）＝番号を再利用しない（タグ別カウントだと新タグが必ず001になり重複）
    seq_pat = re.compile(rf"^trades_{re.escape(stem)}_.+_(\d{{3}})(?:_train|_score)?\.csv$")
    mx = 0
    for dd in (rd, rd / "archive"):
        if not dd.exists():
            continue
        for p in dd.glob(f"trades_{stem}_*.csv"):
            m = seq_pat.match(p.name)
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


def archive_prior_experiments(stem: str, keep_suffix: str, ratchet_dir: pathlib.Path | None = None,
                              adopted_stems: tuple | None = None) -> list[str]:
    """新実験を書く前に呼ぶ。ratchet_dir 直下の「同 stem のタグ付き実験出力（trades/report/analysis/params）」のうち、
    今回の keep_suffix を含むもの と 安定名 base（タグ連番 `_NNN` を持たない現役）と
    採用 base（台帳マーカー ADOPTED_BASE_FILES の幹を含む・2026-07-03 押し出し防止）以外を archive へ move する。
    ＝直下を「現役 base ＋ 今回」だけに保つ（§3.1）。move したファイル名一覧を返す（ログ用）。他 stem は触らない。
    adopted_stems はテスト注入用（None なら台帳から読む）。"""
    rd = ratchet_dir or RATCHET
    adopted = _adopted_base_stems() if adopted_stems is None else adopted_stems
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
        if any(ab and ab in name for ab in adopted):  # 採用 base（台帳 ADOPTED_BASE_FILES）→ 残す（押し出し防止）
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
        # 全タグ通しでユニーク（別タグでも番号を再利用しない・2026-06-24 まこさん指示）
        (d / f"trades_{stem}_freqiter3_002.csv").write_text("x")          # 002 も実在させる
        s3 = tagged_suffix(stem, "_5m_shortset1", "rvX", d)
        assert s3 == "_rvX_003", f"別タグでも全体max+1（freqiter3_001/002 があるので 003）: {s3}"
        # archive 内の番号も見る（archive の連番も再利用しない）
        (d / "archive").mkdir(exist_ok=True)
        (d / "archive" / f"trades_{stem}_oldtag_009.csv").write_text("x")
        s4 = tagged_suffix(stem, "_5m_shortset1", "rvX", d)
        assert s4 == "_rvX_010", f"archive の 009 を見て次は 010: {s4}"

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
        moved = archive_prior_experiments(stem, "_freqiter3_002", d, adopted_stems=())
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

        # (4) 採用 base 押し出し防止（台帳 ADOPTED_BASE_FILES マーカー追従・2026-07-03 まこさん承認）:
        #     タグ連番 `_NNN` を持つ採用 base（例 scenecap_012）は新実験の archive 掃除で押し出されない。
        for n in (f"trades_{stem}_scenecap_012.csv", f"trades_{stem}_scenecap_012_score.csv",
                  f"report_trades_{stem}_scenecap_012_score.txt"):
            (d / n).write_text("x")
        moved4 = archive_prior_experiments(stem, "_newexp_099", d,
                                           adopted_stems=(f"trades_{stem}_scenecap_012",))
        assert (d / f"trades_{stem}_scenecap_012.csv").exists(), "採用 base trades は押し出さない"
        assert (d / f"trades_{stem}_scenecap_012_score.csv").exists(), "採用 base score も押し出さない"
        assert (d / f"report_trades_{stem}_scenecap_012_score.txt").exists(), "採用 base の記録も押し出さない"
        assert all("scenecap_012" not in m for m in moved4), moved4
        # 番人メタ確認: マーカーから幹を外すと従来どおり退避される（弱体化なし）。
        moved5 = archive_prior_experiments(stem, "_newexp_099", d, adopted_stems=())
        assert not (d / f"trades_{stem}_scenecap_012.csv").exists(), "番人: マーカー無しなら従来どおり退避"
        assert any("scenecap_012" in m for m in moved5), moved5
        # マーカー読取り: 一時台帳ファイルからのパース確認。
        lg = d / "adopted.md"
        lg.write_text("x\n<!-- ADOPTED_BASE_FILES: trades_a_001 ; trades_b_002 -->\ny")
        assert _adopted_base_stems(lg) == ("trades_a_001", "trades_b_002"), _adopted_base_stems(lg)

    print("ratchet_io 既知答えテスト: 全 PASS（連番／archive_if_exists／archive_prior_experiments／採用base押し出し防止／番人メタ確認）")


if __name__ == "__main__":
    _known_answer()
