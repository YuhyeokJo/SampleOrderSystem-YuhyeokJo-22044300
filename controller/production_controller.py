from model.production_job import ProductionValidationError
from model.production_model import ProductionModel
from view.production_view import ProductionView


class ProductionController:
    """생산라인 관리 메뉴의 흐름을 제어한다."""

    def __init__(self, model=None, view=None):
        self.model = model or ProductionModel()
        self.view = view or ProductionView()

    def run(self):
        actions = {
            "1": self._register_job,
            "2": self._record_progress,
            "3": self._show_current_job,
            "4": self._show_waiting_jobs,
        }
        while True:
            self.view.show_menu()
            choice = self.view.prompt_choice()
            if choice == "5":
                self.view.show_message("종료합니다.")
                break
            action = actions.get(choice)
            if action is None:
                self.view.show_message("올바르지 않은 선택입니다.")
                continue
            action()

    def _register_job(self):
        order_id = self.view.prompt_order_id()
        sample_id = self.view.prompt_sample_id()
        raw_shortage_quantity = self.view.prompt_shortage_quantity()

        try:
            shortage_quantity = int(raw_shortage_quantity)
        except ValueError:
            self.view.show_message("등록 실패: 부족분은 정수여야 합니다.")
            return

        try:
            job = self.model.register(order_id, sample_id, shortage_quantity)
        except ProductionValidationError as error:
            self.view.show_message(f"등록 실패: {error}")
            return
        self.view.show_message(
            f"등록 완료: 실 생산량 {job.actual_production_quantity}, "
            f"총 생산 시간 {job.total_production_time}"
        )

    def _record_progress(self):
        raw_quantity = self.view.prompt_produced_quantity()

        try:
            quantity = int(raw_quantity)
        except ValueError:
            self.view.show_message("기록 실패: 생산 수량은 정수여야 합니다.")
            return

        try:
            job, completed = self.model.record_progress(quantity)
        except ProductionValidationError as error:
            self.view.show_message(f"기록 실패: {error}")
            return

        if completed:
            self.view.show_message(f"생산 완료: 주문번호 {job.order_id}, 상태 CONFIRMED로 전환")
        else:
            self.view.show_message(
                f"진행 기록 완료: 누적 생산량 {job.produced_quantity}/{job.actual_production_quantity}"
            )

    def _show_current_job(self):
        job = self.model.current_job()
        self.view.show_current_job(job)

    def _show_waiting_jobs(self):
        jobs = self.model.waiting_jobs()
        self.view.show_waiting_jobs(jobs)
