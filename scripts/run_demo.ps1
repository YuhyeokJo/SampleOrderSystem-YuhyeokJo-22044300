# 데모 시나리오 실행 스크립트 (PowerShell).
# 기존에 남아 있는 실행 결과 데이터(data/samples.json, data/orders.json,
# data/production_jobs.json)를 먼저 지우고 main.py에 지정한 데모 입력 파일을
# 표준입력으로 넣어 실행한다.
#
# 사용법: .\scripts\run_demo.ps1 [demo_scenario.txt|demo_production_fifo.txt]
# 인자를 생략하면 demo_scenario.txt(전체 기능 시나리오)를 실행한다.

param(
    [string]$DemoFile = "demo_scenario.txt"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Remove-Item -Path (Join-Path $ProjectRoot "data") -Recurse -Force -ErrorAction SilentlyContinue

Get-Content (Join-Path $ScriptDir $DemoFile) | python (Join-Path $ProjectRoot "main.py")
