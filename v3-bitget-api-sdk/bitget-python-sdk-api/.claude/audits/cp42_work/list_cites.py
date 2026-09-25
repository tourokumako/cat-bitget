#!/usr/bin/env python3
"""list_cites.py — 結果の中の「ファイル名:行番号」を、確かめてから直すゲート（enforce_checked_edit）と同じ形で拾い、
ファイルごとに行番号を並べて出す（読むだけ）。取りまとめ側が、その行を自分で開いて確かめるため。
"""
import re
import sys
from collections import defaultdict

CITE_RE = re.compile(r"(?<![\w.])([A-Za-z0-9_][\w\-.]*\.[A-Za-z][A-Za-z0-9]{0,9}):(\d+)(?:〜(\d+))?")
ALIAS_RE = re.compile(r"(?<![\w/.:\-])(gen|exec|r9|kb):(\d+)(?:〜(\d+))?")

text = open(sys.argv[1], encoding="utf-8").read()
by = defaultdict(set)
for m in CITE_RE.finditer(text):
    by[m.group(1)].add(int(m.group(2)))
for m in ALIAS_RE.finditer(text):
    by["ALIAS:" + m.group(1)].add(int(m.group(2)))
for base in sorted(by):
    print(base, " ".join(str(x) for x in sorted(by[base])))
