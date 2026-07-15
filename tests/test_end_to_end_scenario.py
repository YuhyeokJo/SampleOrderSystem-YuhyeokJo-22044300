from datetime import date
from unittest.mock import patch

from controller.main_controller import MainController

ORDER_1_ID = "ORD-20260715-0001"
ORDER_2_ID = "ORD-20260715-0002"
ORDER_3_ID = "ORD-20260715-0003"


def _build_input_queue():
    return iter(
        [
            # 1. 초기 상태 모니터링 (빈 데이터, 버그 회귀 확인)
            "4",
            "1",
            "2",
            "3",
            # 2. 더미 시료 등록
            "1",
            "1",
            "S-001",
            "실리콘 웨이퍼",
            "1",
            "0.9",
            "100",
            "1",
            "S-002",
            "GaN 웨이퍼",
            "1",
            "0.9",
            "5",
            "2",
            "4",
            # 3. 시료 주문 접수
            "2",
            "1",
            "S-001",
            "테스트고객A",
            "50",
            "1",
            "S-002",
            "테스트고객B",
            "20",
            "1",
            "S-001",
            "테스트고객C",
            "10",
            "2",
            # 4. 주문 승인/거절
            "3",
            "1",
            "2",
            ORDER_1_ID,
            "2",
            ORDER_2_ID,
            "3",
            ORDER_3_ID,
            "4",
            # 5. 생산라인
            "5",
            "3",
            "2",
            "999999",
            "4",
            "5",
            # 6. 출고 처리
            "6",
            "1",
            "2",
            ORDER_1_ID,
            "2",
            ORDER_2_ID,
            "3",
            # 7. 최종 모니터링
            "4",
            "1",
            "2",
            "3",
            # 8. 프로그램 종료
            "7",
        ]
    )


def test_full_console_scenario_runs_end_to_end_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    inputs = _build_input_queue()
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("model.order_model.date") as mock_date:
        mock_date.today.return_value = date(2026, 7, 15)
        controller = MainController()
        controller.run()

    output = capsys.readouterr().out

    assert "Traceback" not in output

    # 1. 초기 상태 모니터링
    assert "[RESERVED]: 0건" in output
    assert "[CONFIRMED]: 0건" in output
    assert "[PRODUCING]: 0건" in output
    assert "[RELEASE]: 0건" in output
    assert "등록된 시료가 없습니다." in output

    # 2. 더미 시료 등록
    assert "등록 완료: S-001 (실리콘 웨이퍼)" in output
    assert "등록 완료: S-002 (GaN 웨이퍼)" in output
    assert "S-001" in output and "S-002" in output

    # 3. 시료 주문 접수
    assert output.count("예약 접수 완료.") == 3
    assert ORDER_1_ID in output
    assert ORDER_2_ID in output
    assert ORDER_3_ID in output
    assert "등록되어 있지 않습니다" not in output

    # 4. 주문 승인/거절
    assert "부족분     : 15 (생산라인에 등록되었습니다)" in output
    assert "거절 완료." in output

    # 5. 생산라인 - 999999 입력 1회로 즉시 완료 처리
    assert f"생산 완료: 주문번호 {ORDER_2_ID}, 상태 변경: PRODUCING → [CONFIRMED]" in output
    assert "대기 중인 생산 항목이 없습니다." in output

    # 6. 출고 처리
    assert output.count("출고 처리 완료.") == 2

    # 7. 최종 모니터링 - RELEASE 2건, REJECTED 제외
    assert "[RELEASE]: 2건" in output
    assert "[고갈]" in output

    # 8. 프로그램 종료
    assert "프로그램을 종료합니다." in output
