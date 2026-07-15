from model.sample import Sample
from view.sample_view import SampleView


def test_show_samples_reports_empty_message_when_no_samples(capsys):
    view = SampleView()

    view.show_samples([])

    assert capsys.readouterr().out == "등록된 시료가 없습니다.\n"


def test_show_samples_prints_count_and_table(capsys):
    view = SampleView()
    samples = [Sample.create("S-1", "Wafer-A", 10.0, 0.9, 100)]

    view.show_samples(samples)

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "등록 시료 목록 (총 1종)"
    assert "시료 ID" in lines[1]
    assert lines[1].startswith("시료 ID")
    assert "S-1" in lines[2]
    assert lines[2].startswith("S-1")


def test_prompt_choice_uses_selection_prompt(monkeypatch):
    view = SampleView()
    monkeypatch.setattr("builtins.input", lambda prompt: "1")

    assert view.prompt_choice() == "1"
