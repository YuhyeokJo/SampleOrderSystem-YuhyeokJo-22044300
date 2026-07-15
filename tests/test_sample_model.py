import pytest

from model.sample_model import SampleModel
from model.sample import SampleValidationError
from model.sample_repository import SampleRepository


@pytest.fixture
def sample_model(tmp_path):
    repository = SampleRepository(str(tmp_path / "samples.json"))
    return SampleModel(repository=repository)


def test_register_success_returns_sample_with_given_values(sample_model):
    sample = sample_model.register("S-1", "Wafer-A", 10.0, 0.95, 100)

    assert sample.sample_id == "S-1"
    assert sample.name == "Wafer-A"
    assert sample.avg_production_time == 10.0
    assert sample.yield_rate == 0.95
    assert sample.stock_quantity == 100
    assert sample_model.find_by_id("S-1") is sample


def test_register_duplicate_id_is_rejected(sample_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.95, 100)

    with pytest.raises(SampleValidationError):
        sample_model.register("S-1", "Wafer-B", 5.0, 0.5, 10)


def test_register_duplicate_id_uses_exact_string_comparison(sample_model):
    sample_model.register("1", "Wafer-A", 10.0, 0.95, 100)

    registered = sample_model.register("01", "Wafer-B", 5.0, 0.5, 10)

    assert registered.sample_id == "01"


@pytest.mark.parametrize("invalid_time", [0, -1, -0.5])
def test_register_rejects_non_positive_avg_production_time(sample_model, invalid_time):
    with pytest.raises(SampleValidationError):
        sample_model.register("S-1", "Wafer-A", invalid_time, 0.9, 10)


@pytest.mark.parametrize("invalid_yield_rate", [-0.01, 1.01, -1, 2])
def test_register_rejects_yield_rate_out_of_range(sample_model, invalid_yield_rate):
    with pytest.raises(SampleValidationError):
        sample_model.register("S-1", "Wafer-A", 10.0, invalid_yield_rate, 10)


@pytest.mark.parametrize("boundary_yield_rate", [0.0, 1.0])
def test_register_allows_yield_rate_boundary_values(sample_model, boundary_yield_rate):
    sample = sample_model.register("S-1", "Wafer-A", 10.0, boundary_yield_rate, 10)

    assert sample.yield_rate == boundary_yield_rate


@pytest.mark.parametrize("invalid_stock", [-1, 3.5, "10"])
def test_register_rejects_invalid_stock_quantity(sample_model, invalid_stock):
    with pytest.raises(SampleValidationError):
        sample_model.register("S-1", "Wafer-A", 10.0, 0.9, invalid_stock)


def test_register_allows_zero_stock_quantity(sample_model):
    sample = sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 0)

    assert sample.stock_quantity == 0


def test_register_rejects_empty_name(sample_model):
    with pytest.raises(SampleValidationError):
        sample_model.register("S-1", "  ", 10.0, 0.9, 10)


def test_list_when_no_samples_registered_returns_empty(sample_model):
    assert sample_model.all() == []


def test_search_when_no_samples_registered_returns_empty(sample_model):
    assert sample_model.search_by_name("Wafer") == []


def test_search_by_name_returns_matching_samples(sample_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 10)
    sample_model.register("S-2", "Wafer-B", 5.0, 0.8, 5)
    sample_model.register("S-3", "Die-C", 3.0, 0.7, 1)

    results = sample_model.search_by_name("Wafer")

    assert {sample.sample_id for sample in results} == {"S-1", "S-2"}


def test_search_with_no_matching_keyword_returns_empty(sample_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 10)

    assert sample_model.search_by_name("NoSuchName") == []


def test_decrease_stock_reduces_quantity_and_persists(sample_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)

    updated_sample = sample_model.decrease_stock("S-1", 30)

    assert updated_sample.stock_quantity == 70
    assert sample_model.find_by_id("S-1").stock_quantity == 70


def test_decrease_stock_allows_exact_boundary_reducing_to_zero(sample_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 30)

    updated_sample = sample_model.decrease_stock("S-1", 30)

    assert updated_sample.stock_quantity == 0


def test_decrease_stock_rejects_amount_greater_than_current_stock(sample_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 30)

    with pytest.raises(SampleValidationError):
        sample_model.decrease_stock("S-1", 31)

    assert sample_model.find_by_id("S-1").stock_quantity == 30


def test_decrease_stock_rejects_unregistered_sample_id(sample_model):
    with pytest.raises(SampleValidationError):
        sample_model.decrease_stock("UNKNOWN", 1)


@pytest.mark.parametrize("invalid_amount", [-1, 1.5, "10"])
def test_decrease_stock_rejects_invalid_amount(sample_model, invalid_amount):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 30)

    with pytest.raises(SampleValidationError):
        sample_model.decrease_stock("S-1", invalid_amount)
