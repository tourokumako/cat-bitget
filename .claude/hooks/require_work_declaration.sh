#!/bin/bash
# require_work_declaration.sh — ToDo の1件を始める前に、宣言（作業内容・目的・経緯・ゴール）と まこさんの返事を求める（本体は require_work_declaration.py）
# まこさん指示（逐語 2026-10-12）「読んだのかを確認するためにも、作業を始める前に、作業内容、目的、経緯、ゴールを宣言するように強制する」
exec python3 "$(dirname "$0")/require_work_declaration.py"
