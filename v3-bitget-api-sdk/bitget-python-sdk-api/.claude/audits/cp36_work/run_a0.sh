#!/bin/bash
# run_a0.sh — 監査 cp36 の走らせる側を、写しで順に走らせて記録に残す（本物は触らない）
#   T0 土台 → T1 壊すプログラム15本 → T2 追加の壊し方3つ → T3 法則9件の書き替え → T4 種の比較 → T5 0e1f1be との比較
set -u
W="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work"
R="bash $W/run.sh"
LOG="$W/logs"; mkdir -p "$LOG"
SUM="$LOG/summary.txt"; : > "$SUM"
note () { echo "$(date '+%H:%M:%S') $*" | tee -a "$SUM"; }
run () {  # run <名前> <コマンド...>  → 出力を logs/<名前>.out に、rc と秒を summary に
    local name="$1"; shift
    local t0=$(date +%s)
    "$@" > "$LOG/$name.out" 2>&1
    local rc=$?
    local t1=$(date +%s)
    note "$name rc=$rc sec=$((t1-t0))"
    return $rc
}
hashk () { $R hash "$1" | tr '\n' ' ' ; echo; }

note "== T0 土台 =="
$R restore-all > "$LOG/restore0.out" 2>&1; note "restore-all rc=$?"
run T0_gen_selftest $R gen --selftest
tail -3 "$LOG/T0_gen_selftest.out" >> "$SUM"
run T0_count $R count
run T0_kb_verify $R kb --verify
run T0_acc_verify $R acc --verify
run T0_rb_selftest $R rb --selftest

note "== T1 壊すプログラム15本 =="
for b in b76_laws_not_read:laws b77_no_streak:gen b78_law_literal:gen b79_param_drawn:gen \
         b80_quantile_one_by_one:gen b81_drop_tf_ignored:gen b82_abs_missing:exec b83_bool_col_extra_key:exec \
         b84_qtable_per_bundle:r9 b85_band_ignores_laws:gen b86_stage_count:gen b87_stages_record:gen \
         b88_stage_fam_unknown:cands b89_audit_todo_row_removed:acc b90_expect_msg_mismatch:rb; do
    name="${b%%:*}"; key="${b##*:}"
    msg=$(grep -m1 "^# EXPECT_MSG:" "$W/mirror/breaks/$name.sh" | sed 's/^# EXPECT_MSG: *//')
    run "T1_$name" $R break "$name"
    if grep -qF -- "$msg" "$LOG/T1_$name.out"; then note "  $name EXPECT_MSG「$msg」＝出力に在る"; else note "  $name EXPECT_MSG「$msg」＝出力に無い"; fi
    grep -n "❌\|^  T[0-9]\|落ち\|NG\|止まった" "$LOG/T1_$name.out" | head -12 >> "$SUM"
    note "  $name 戻り: $(hashk "$key")"
    [ "$key" = "cands" ] && note "  $name 戻り(mile): $(hashk mile)"
done

note "== T2 追加の壊し方（2本目） =="
$R restore-all > /dev/null 2>&1
# (i) 2本目の上位足を 10m だけにする
$R patch gen '    upper = [t for t in tfs_all if tfs_all.index(t) > tfs_all.index("5m")]      # 執行足より上（C4・R3）' '    upper = ["10m"]  # A0c-i（10分足だけを許す）' >> "$SUM" 2>&1
run T2_i_10m_only $R gen --selftest
grep -n "❌\|^  T24\|^  T39\|^  T40\|^  T41\|落ち\|NG" "$LOG/T2_i_10m_only.out" | head -12 >> "$SUM"
$R restore gen >> "$SUM"
# (ii) 2本目の family の絞りを外す（_material_for_law）
$R patch gen '        if want and fam not in want:                     # ★法則が名指しした family だけを数える' '        if False:  # A0c-ii（法則の family で絞らない）' >> "$SUM" 2>&1
run T2_ii_no_family_filter $R gen --selftest
grep -n "❌\|^  T24\|^  T39\|^  T40\|落ち\|NG" "$LOG/T2_ii_no_family_filter.out" | head -12 >> "$SUM"
$R restore gen >> "$SUM"
# (iii) 2本目の帯の向きを常に above にする
$R patch gen '    r_b, r_c, r_g, side_b = regime_draw_order(order_n)' '    r_b, r_c, r_g, side_b = regime_draw_order(order_n); side_b = "above"  # A0c-iii' >> "$SUM" 2>&1
run T2_iii_side_fixed $R gen --selftest
grep -n "❌\|^  T24\|^  T39\|落ち\|NG" "$LOG/T2_iii_side_fixed.out" | head -12 >> "$SUM"
$R restore gen >> "$SUM"
# (iv) 2本目の系統の絞りを外す（_material_for_lineage）
$R patch gen '        if iref.FAMILY_LINEAGE[fam]["k"] not in want:      # ★法則が名指しした系統だけを数える' '        if False:  # A0c-iv（法則の系統で絞らない）' >> "$SUM" 2>&1
run T2_iv_no_lineage_filter $R gen --selftest
grep -n "❌\|^  T24\|^  T39\|^  T40\|落ち\|NG" "$LOG/T2_iv_no_lineage_filter.out" | head -12 >> "$SUM"
$R restore gen >> "$SUM"

note "== T3 束の直接の走査（新・旧）と法則の書き替え =="
run T3_scan_new python3 "$W/scan_bundles.py" mirror 200 "$LOG/scan_new.json"
run T3_scan_old python3 "$W/scan_bundles.py" mirror_old 200 "$LOG/scan_old.json"
lawedit () {  # lawedit <名前> <python の文>
    $R restore laws > /dev/null 2>&1
    $R pyedit laws "$2" >> "$SUM" 2>&1
    run "T3_law_$1" python3 "$W/scan_bundles.py" mirror 6 "$LOG/scan_law_$1.json"
    $R restore laws > /dev/null 2>&1
}
PRE='d=json.loads(s)
def L(no):
    return next(x for x in d["法則"] if x.get("番号")==no)
'
POST='
open(p,"w",encoding="utf-8").write(json.dumps(d,ensure_ascii=False,indent=2)+"\n")'
lawedit C4_no_range "${PRE}L(\"C4\")[\"機械が読む判定\"][\"掛かる場面\"]=[\"uptrend\",\"downtrend\"]${POST}"
lawedit C6_no_range "${PRE}L(\"C6\")[\"機械が読む判定\"][\"掛かる場面\"]=[\"uptrend\",\"downtrend\"]${POST}"
lawedit R1_lineage_vola "${PRE}L(\"R1\")[\"機械が読む判定\"][\"数える部品\"][\"系統\"]=[\"ボラ\"]${POST}"
lawedit R3_lineage_vola "${PRE}L(\"R3\")[\"機械が読む判定\"][\"数える部品\"][\"系統\"]=[\"ボラ\"]${POST}"
lawedit R4_no_range "${PRE}L(\"R4\")[\"機械が読む判定\"][\"掛かる場面\"]=[]${POST}"
lawedit R5_family_chop_only "${PRE}j=L(\"R5\")[\"機械が読む判定\"][\"数える部品\"]; j[\"family\"]=[\"CHOP\"]; j[\"側\"]={\"CHOP\":\"above\"}${POST}"
lawedit R6_family_atr_only "${PRE}j=L(\"R6\")[\"機械が読む判定\"][\"数える部品\"]; j[\"family\"]=[\"ATR%\"]; j[\"側\"]={\"ATR%\":\"below\"}${POST}"
lawedit R7_geo_pos "${PRE}j=L(\"R7\")[\"機械が読む判定\"][\"数える部品\"]; j[\"geo\"]=[\"帯内位置%\"]; j[\"側\"]={\"帯内位置%\":\"below\"}${POST}"
lawedit R8_no_range "${PRE}L(\"R8\")[\"機械が読む判定\"][\"掛かる場面\"]=[]${POST}"
lawedit R5_side_flip "${PRE}j=L(\"R5\")[\"機械が読む判定\"][\"数える部品\"]; j[\"側\"]={k:(\"above\" if v==\"below\" else \"below\") for k,v in j[\"側\"].items()}${POST}"
$R restore-all >> "$SUM" 2>&1

note "== T4 種の比較・A5-a・D1（regime_r9_diag） =="
run T4_r9_seed7 $R r9 --build 3 --no-trades --seed 7
run T4_r9_seed8 $R r9 --build 3 --no-trades --seed 8
run T4_r9_default $R r9 --build 3 --no-trades
for f in T4_r9_seed7 T4_r9_seed8 T4_r9_default; do grep -n "組めない\|束 .* 本\|止ま\|Error\|Traceback" "$LOG/$f.out" | head -8 >> "$SUM"; done

note "== T5 0e1f1be の版 =="
run T5_old_r9_seed7 $R old-r9 --build 3 --no-trades --seed 7
grep -n "組めない\|束 .* 本\|Traceback" "$LOG/T5_old_r9_seed7.out" | head -6 >> "$SUM"
run T5_old_gen_selftest $R old-gen --selftest
tail -3 "$LOG/T5_old_gen_selftest.out" >> "$SUM"

note "== T6 恒等（完成の条件 #17）・写しで =="
run T6_exec_identity timeout 2400 $R exec --identity
tail -5 "$LOG/T6_exec_identity.out" >> "$SUM"

$R restore-all >> "$SUM" 2>&1
note "== 終わり =="
