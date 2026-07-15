from view.console_format import render_divider
from view.main_menu_view import MainMenuView


def test_show_menu_prints_divider_banner_and_items(capsys):
    view = MainMenuView()

    view.show_menu()

    output = capsys.readouterr().out
    assert output.count(render_divider()) == 2
    assert " S-Semi 반도체 시료 생산주문관리 시스템" in output
    assert " [1] 시료 관리          [2] 시료 주문" in output
    assert " [7] 프로그램 종료" in output


def test_show_summary_reports_no_samples_message(capsys):
    view = MainMenuView()

    view.show_summary(0, 0)

    assert capsys.readouterr().out == "등록된 시료가 없습니다.\n"


def test_show_summary_reports_sample_count_and_total_stock(capsys):
    view = MainMenuView()

    view.show_summary(2, 128)

    output = capsys.readouterr().out
    assert "등록된 시료: 2종" in output
    assert "총 재고 수량: 128" in output


def test_prompt_choice_uses_selection_prompt(monkeypatch):
    view = MainMenuView()
    captured_prompt = {}

    def fake_input(prompt):
        captured_prompt["value"] = prompt
        return "1"

    monkeypatch.setattr("builtins.input", fake_input)

    result = view.prompt_choice()

    assert result == "1"
    assert captured_prompt["value"] == "선택 > "
