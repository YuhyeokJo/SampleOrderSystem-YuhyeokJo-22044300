class MainMenuView:
    """메인 메뉴의 콘솔 입출력을 담당한다."""

    MENU = """
==== S-Semi 시료 생산주문 관리 시스템 ====
1. 시료 관리
2. 시료 주문
3. 주문 승인/거절
4. 모니터링
5. 생산라인
6. 출고 처리
7. 프로그램 종료
"""

    def show_summary(self, sample_count, total_stock_quantity):
        if sample_count == 0:
            print("등록된 시료가 없습니다.")
            return
        print(f"등록된 시료: {sample_count}종")
        print(f"총 재고 수량: {total_stock_quantity}")

    def show_menu(self):
        print(self.MENU)

    def prompt_choice(self):
        return input("메뉴를 선택하세요: ").strip()

    def show_message(self, message):
        print(message)
