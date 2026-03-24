import pytest
from app.cli import run, normalize_name


def test_run_default_name():
    result = run("AI App")
    assert result == "Hello, AI App!"


def test_run_custom_name():
    result = run("kk")
    assert result == "Hello, kk!"

def test_normalize_name_should_strip_spaces():
    result = normalize_name("  kk  ")
    assert result == "kk"


def test_normalize_name_should_raise_for_empty_input():
    with pytest.raises(ValueError):
        normalize_name("   ")