#!/usr/bin/env bash
# 데모 시나리오 실행 스크립트.
# 기존에 남아 있는 실행 결과 데이터(data/samples.json, data/orders.json,
# data/production_jobs.json)를 먼저 지우고 main.py에 지정한 데모 입력 파일을
# 표준입력으로 넣어 실행한다.
#
# 사용법: scripts/run_demo.sh [demo_scenario.txt|demo_production_fifo.txt]
# 인자를 생략하면 demo_scenario.txt(전체 기능 시나리오)를 실행한다.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEMO_FILE="${1:-demo_scenario.txt}"

rm -rf "$PROJECT_ROOT/data"

python "$PROJECT_ROOT/main.py" < "$SCRIPT_DIR/$DEMO_FILE"
