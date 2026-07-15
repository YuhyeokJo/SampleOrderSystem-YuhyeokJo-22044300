from datetime import date
from unittest.mock import patch

from controller.main_controller import MainController

ORDER_1_ID = "ORD-20260715-0001"  # S-201 5개, 승인(충분) -> CONFIRMED -> 출고 -> RELEASE
ORDER_2_ID = "ORD-20260715-0002"  # S-201 5개, 미승인 -> RESERVED로 남음 (여유 판단용 수요)
ORDER_3_ID = "ORD-20260715-0003"  # S-202 3개, 승인(충분) -> CONFIRMED (출고하지 않고 남김)
ORDER_4_ID = "ORD-20260715-0004"  # S-202 10개, 미승인 -> RESERVED로 남음 (부족 판단용 수요)
ORDER_5_ID = "ORD-20260715-0005"  # S-203 3개, 승인(정확히 소진) -> CONFIRMED (출고하지 않고 남김)
ORDER_6_ID = "ORD-20260715-0006"  # S-204 8개, 승인(부족) -> PRODUCING, 생산 절반만 진행 후 미완료로 남김
ORDER_7_ID = "ORD-20260715-0007"  # S-201 2개, 거절 -> REJECTED (모니터링에서 제외되어야 함)


def _build_input_queue():
    return iter(
        [
            # 1. 시료 4종 등록 + 목록 조회 + 이름 검색
            "1",
            "1",
            "S-201",
            "실리콘 웨이퍼",
            "1",
            "0.9",
            "20",
            "1",
            "S-202",
            "GaN 에피",
            "1",
            "0.9",
            "10",
            "1",
            "S-203",
            "실리콘 웨이퍼 특수",
            "1",
            "0.9",
            "3",
            "1",
            "S-204",
            "테스트 칩",
            "1",
            "0.9",
            "2",
            "2",  # 목록 조회: 4종 모두 표시
            "3",
            "웨이퍼",  # 이름 검색: S-201, S-203 두 건만 일치
            "4",
            # 2. 주문 7건 접수
            "2",
            "1",
            "S-201",
            "고객1",
            "5",
            "1",
            "S-201",
            "고객2",
            "5",
            "1",
            "S-202",
            "고객3",
            "3",
            "1",
            "S-202",
            "고객4",
            "10",
            "1",
            "S-203",
            "고객5",
            "3",
            "1",
            "S-204",
            "고객6",
            "8",
            "1",
            "S-201",
            "고객7",
            "2",
            "2",
            # 3. 승인/거절: 주문1/3/5 승인(충분), 주문6 승인(부족->생산 등록), 주문7 거절
            #    주문2/4는 RESERVED로 남겨 재고 상태 판단용 수요를 만든다
            "3",
            "1",  # 접수된 주문 목록: 7건 모두 RESERVED
            "2",
            ORDER_1_ID,
            "2",
            ORDER_3_ID,
            "2",
            ORDER_5_ID,
            "2",
            ORDER_6_ID,
            "3",
            ORDER_7_ID,
            "4",
            # 4. 생산라인: 주문6의 생산 항목을 절반만 진행하고 완료하지 않은 채로 둔다
            "5",
            "3",  # 생산 현황 조회: 부족분 6, 실 생산량 8, 누적 0/8
            "2",
            "3",  # 3개만 진행 기록 -> 3/8 (미완료)
            "3",  # 생산 현황 조회: 누적 3/8로 갱신되었는지 확인
            "5",
            # 5. 출고 처리: 주문1만 출고하고, 주문3/5는 CONFIRMED 상태로 남긴다
            "6",
            "1",  # CONFIRMED 목록 조회: 주문1/3/5 3건
            "2",
            ORDER_1_ID,
            "3",
            # 6. 최종 모니터링: 5가지 주문 상태와 3가지 재고 상태가 동시에 나타나는지 확인
            "4",
            "1",
            "2",
            "3",
            "7",
        ]
    )


def test_mixed_status_scenario_shows_every_order_and_stock_state_together(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    inputs = _build_input_queue()
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    with patch("model.order_model.date") as mock_date:
        mock_date.today.return_value = date(2026, 7, 15)
        controller = MainController()
        controller.run()

    output = capsys.readouterr().out

    assert "Traceback" not in output

    # 1. 이름 검색: "웨이퍼"로 검색 시 S-201, S-203 두 건만 결과에 포함
    #    (input()을 모의하면서 프롬프트 문자열은 출력되지 않으므로, 검색 결과 표 헤더의
    #    건수("총 2종")로 목록 조회 결과(총 4종)와 구분한다)
    search_index = output.index("등록 시료 목록 (총 2종)")
    approval_index = output.index("주문 승인/거절", search_index)
    search_block = output[search_index:approval_index]
    assert search_block.count("S-201") >= 1
    assert search_block.count("S-203") >= 1
    assert "S-204" not in search_block  # "테스트 칩"은 검색어와 무관하므로 결과에서 제외

    # 2. 접수 7건 모두 성공
    assert output.count("예약 접수 완료.") == 7

    # 3. 승인 결과: 충분/정확히 소진/부족 세 갈래가 모두 나타남
    assert f"상태 변경  : RESERVED → [CONFIRMED]" in output
    assert "부족분     : 6 (생산라인에 등록되었습니다)" in output
    assert "거절 완료." in output

    # 4. 생산 진행: 3/8까지만 기록되고 완료되지 않음("생산 완료" 메시지가 없어야 함)
    assert "진행 기록 완료: [████████░░░░░░░░░░░░] 38% (3/8)" in output
    assert f"생산 완료: 주문번호 {ORDER_6_ID}" not in output

    # 5. 출고: 주문1만 출고 처리됨
    assert output.count("출고 처리 완료.") == 1

    # 6. 최종 모니터링: 5가지 상태(REJECTED 제외)가 동시에 나타남
    assert "[RESERVED]: 2건" in output  # 주문2, 주문4
    assert "[CONFIRMED]: 2건" in output  # 주문3, 주문5 (주문1은 출고됨)
    assert "[PRODUCING]: 1건" in output  # 주문6 (미완료로 남음)
    assert "[RELEASE]: 1건" in output  # 주문1

    # 7. 최종 재고 상태: 여유/부족/고갈이 동시에 나타남
    #    S-201: 재고 15(20-5), 수요(주문2) 5 -> 여유
    #    S-202: 재고 7(10-3), 수요(주문4) 10 -> 부족
    #    S-203: 재고 0(3-3 정확히 소진) -> 고갈
    #    S-204: 재고 0(2 전량 소진, 부족분은 생산라인 몫) -> 고갈
    stock_status_index = output.rindex("재고수량")
    stock_status_block = output[stock_status_index:]
    assert "[여유]" in stock_status_block
    assert "[부족]" in stock_status_block
    assert stock_status_block.count("[고갈]") == 2
