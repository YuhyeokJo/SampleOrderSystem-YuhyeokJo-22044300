from model.production_job import ProductionJob
from view.production_view import ProductionView


def test_show_current_job_reports_empty_message_when_no_job(capsys):
    view = ProductionView()

    view.show_current_job(None)

    assert capsys.readouterr().out == "진행 중인 생산 항목이 없습니다.\n"


def test_show_current_job_prints_progress_bar(capsys):
    view = ProductionView()
    job = ProductionJob.create("ORD-1", "S-003", 170, 206, 165.0, sequence=1)
    job.add_produced_quantity(124)

    view.show_current_job(job)

    output = capsys.readouterr().out
    assert "현재 생산 중" in output
    assert " 주문번호    : ORD-1" in output
    assert " 시료 ID     : S-003" in output
    assert " 부족분      : 170" in output
    assert "실 생산량   : 206" in output
    assert "총 생산 시간 : 165.0" in output
    assert "[████████████░░░░░░░░] 60% (124/206)" in output


def test_show_waiting_jobs_reports_empty_message_when_no_jobs(capsys):
    view = ProductionView()

    view.show_waiting_jobs([])

    assert capsys.readouterr().out == "대기 중인 생산 항목이 없습니다.\n"


def test_show_waiting_jobs_prints_count_and_numbered_table(capsys):
    view = ProductionView()
    job = ProductionJob.create("ORD-1", "S-1", 10, 15, 12.0, sequence=1)

    view.show_waiting_jobs([job])

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "대기 중인 생산 항목 (총 1건, FIFO)"
    assert lines[1].startswith("순번")
    assert lines[2].startswith("1")
    assert "ORD-1" in lines[2]


def test_show_registration_success_prints_actual_quantity_and_time(capsys):
    view = ProductionView()
    job = ProductionJob.create("ORD-1", "S-1", 10, 15, 12.0, sequence=1)

    view.show_registration_success(job)

    output = capsys.readouterr().out
    assert output == "생산 큐 등록 완료. 실 생산량: 15, 총 생산 시간: 12.0\n"


def test_show_progress_result_when_completed(capsys):
    view = ProductionView()
    job = ProductionJob.create("ORD-1", "S-1", 10, 15, 12.0, sequence=1)

    view.show_progress_result(job, True)

    output = capsys.readouterr().out
    assert output == "생산 완료: 주문번호 ORD-1, 상태 변경: PRODUCING → [CONFIRMED]\n"


def test_show_progress_result_when_not_completed(capsys):
    view = ProductionView()
    job = ProductionJob.create("ORD-1", "S-1", 10, 15, 12.0, sequence=1)
    job.add_produced_quantity(4)

    view.show_progress_result(job, False)

    output = capsys.readouterr().out
    assert "진행 기록 완료: " in output
    assert "(4/15)" in output
