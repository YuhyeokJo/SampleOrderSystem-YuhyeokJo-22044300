from datetime import date
from unittest.mock import patch

from controller.main_controller import MainController
from view.console_format import render_divider

ORDER_1_ID = "ORD-20260715-0001"
ORDER_2_ID = "ORD-20260715-0002"
ORDER_3_ID = "ORD-20260715-0003"


def _build_input_queue():
    return iter(
        [
            # 시료 3종 등록 (각 재고 1, 주문 수량 5 -> 모두 재고 부족 유발)
            "1",
            "1",
            "S-101",
            "웨이퍼A",
            "1",
            "0.9",
            "1",
            "1",
            "S-102",
            "웨이퍼B",
            "1",
            "0.9",
            "1",
            "1",
            "S-103",
            "웨이퍼C",
            "1",
            "0.9",
            "1",
            "4",
            # 주문 3건 접수
            "2",
            "1",
            "S-101",
            "고객A",
            "5",
            "1",
            "S-102",
            "고객B",
            "5",
            "1",
            "S-103",
            "고객C",
            "5",
            "2",
            # 3건 모두 승인 -> 재고 부족으로 순서대로 생산 큐에 등록
            "3",
            "2",
            ORDER_1_ID,
            "2",
            ORDER_2_ID,
            "2",
            ORDER_3_ID,
            "4",
            # 생산라인: 대기열이 FIFO 순서를 지키는지 확인 후 하나씩 완료 처리
            "5",
            "4",  # 대기 주문 확인: 2건(주문2, 주문3) FIFO 순서
            "3",  # 생산 현황 조회: 주문1이 진행 중, 누적 생산량 0
            "2",
            "2",  # 부분 진행 기록(2/5) -> 진행률 바가 중간 단계로 채워지는지 확인
            "3",  # 생산 현황 조회: 누적 생산량 2/5(40%)
            "2",
            "999999",  # 주문1 완료 -> 주문2가 진행 중으로 승격
            "4",  # 대기 주문 확인: 1건(주문3)만 남음
            "3",  # 생산 현황 조회: 주문2가 진행 중
            "2",
            "999999",  # 주문2 완료 -> 주문3이 진행 중으로 승격
            "4",  # 대기 주문 확인: 없음
            "3",  # 생산 현황 조회: 주문3이 진행 중
            "2",
            "999999",  # 주문3 완료 -> 큐 전체 비워짐
            "4",  # 대기 주문 확인: 없음
            "3",  # 생산 현황 조회: 진행 중인 항목 없음
            "5",
            # 모니터링으로 전부 CONFIRMED 전환 확인
            "4",
            "1",
            "3",
            "7",
        ]
    )


def test_production_queue_processes_multiple_jobs_in_fifo_order(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    inputs = _build_input_queue()
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("model.order_model.date") as mock_date:
        mock_date.today.return_value = date(2026, 7, 15)
        controller = MainController()
        controller.run()

    output = capsys.readouterr().out

    assert "Traceback" not in output

    # 승인 시 3건 모두 재고 부족으로 생산라인에 등록됨
    assert output.count("(생산라인에 등록되었습니다)") == 3

    # 첫 확인 시점: 대기열 표에 주문2, 주문3이 FIFO 순서(등록 순서)로 존재
    first_waiting_index = output.index("대기 중인 생산 항목")
    block_end = output.index(render_divider(), first_waiting_index)
    first_waiting_block = output[first_waiting_index:block_end]
    assert first_waiting_block.index(ORDER_2_ID) < first_waiting_block.index(ORDER_3_ID)
    assert ORDER_1_ID not in first_waiting_block  # 진행 중인 항목은 대기 목록에서 제외

    # 부분 진행 기록(2/5) 시 진행률 바가 0%가 아닌 중간 단계(40%)로 채워짐을 확인
    assert "진행 기록 완료: [████████░░░░░░░░░░░░] 40% (2/5)" in output
    assert "진행률      : [████████░░░░░░░░░░░░] 40% (2/5)" in output

    # 완료 처리마다 다음 항목이 진행 중으로 승격되며 순서대로 CONFIRMED 전환
    assert f"생산 완료: 주문번호 {ORDER_1_ID}, 상태 변경: PRODUCING → [CONFIRMED]" in output
    assert f"생산 완료: 주문번호 {ORDER_2_ID}, 상태 변경: PRODUCING → [CONFIRMED]" in output
    assert f"생산 완료: 주문번호 {ORDER_3_ID}, 상태 변경: PRODUCING → [CONFIRMED]" in output

    # 마지막 대기 주문 확인/생산 현황 조회 시점에는 큐가 완전히 비어 있음
    assert output.count("대기 중인 생산 항목이 없습니다.") == 2
    assert "진행 중인 생산 항목이 없습니다." in output

    # 최종 모니터링: 3건 모두 CONFIRMED
    assert "[CONFIRMED]: 3건" in output
