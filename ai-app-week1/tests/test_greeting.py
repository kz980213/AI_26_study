import pytest
from app.services.greeting import normalize_name, build_greeting
from app.exceptions import InvalidNameError


def test_normalize_name_should_strip_spaces():
    assert normalize_name("  kk  ") == "kk"


def test_normalize_name_should_raise_for_empty_input():
    with pytest.raises(InvalidNameError):
        normalize_name("   ")


def test_build_greeting_should_return_message():
    assert build_greeting("kk") == "Hello, kk!"


def test_build_greeting_should_strip_input():
    assert build_greeting("  kk  ") == "Hello, kk!"