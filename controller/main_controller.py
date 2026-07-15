from model.sample_model import SampleModel
from view.main_menu_view import MainMenuView


def _default_controllers():
    from controller.approval_controller import ApprovalController
    from controller.monitoring_controller import MonitoringController
    from controller.order_controller import OrderController
    from controller.production_controller import ProductionController
    from controller.release_controller import ReleaseController
    from controller.sample_controller import SampleController
    from model.approval_model import ApprovalModel
    from model.monitoring_model import MonitoringModel
    from model.order_model import OrderModel
    from model.production_model import ProductionModel
    from model.release_model import ReleaseModel

    sample_model = SampleModel()
    order_model = OrderModel(sample_model=sample_model)
    production_model = ProductionModel(sample_model=sample_model, order_model=order_model)
    approval_model = ApprovalModel(
        order_model=order_model, sample_model=sample_model, production_model=production_model
    )
    release_model = ReleaseModel(order_model=order_model)
    monitoring_model = MonitoringModel(sample_model, order_model)

    return {
        "1": SampleController(model=sample_model),
        "2": OrderController(model=order_model),
        "3": ApprovalController(model=approval_model),
        "4": MonitoringController(model=monitoring_model),
        "5": ProductionController(model=production_model),
        "6": ReleaseController(model=release_model),
    }


class MainController:
    """메인 메뉴의 흐름을 제어하고 각 기능 컨트롤러를 실행한다."""

    EXIT_CHOICE = "7"

    def __init__(self, view=None, controllers=None):
        self.view = view or MainMenuView()
        self.controllers = controllers if controllers is not None else _default_controllers()

    def run(self):
        while True:
            self._show_summary()
            self.view.show_menu()
            choice = self.view.prompt_choice()

            if choice == self.EXIT_CHOICE:
                self.view.show_message("프로그램을 종료합니다.")
                break

            controller = self.controllers.get(choice)
            if controller is None:
                self.view.show_message("올바르지 않은 선택입니다.")
                continue

            controller.run()

    def _show_summary(self):
        samples = SampleModel().all()
        sample_count = len(samples)
        total_stock_quantity = sum(sample.stock_quantity for sample in samples)
        self.view.show_summary(sample_count, total_stock_quantity)
