from app.cli import run


def test_run_default_name():
    result = run("AI App")
    assert result == "Hello, AI App!"


def test_run_custom_name():
    result = run("kk")
    assert result == "Hello, kk!"