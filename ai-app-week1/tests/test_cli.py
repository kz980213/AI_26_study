from app.cli import build_parser, run, main


def test_run_should_return_message():
    result = run("kk")
    assert result == "Hello, kk!"


def test_parser_should_use_default_name():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.name == "AI App"


def test_parser_should_accept_custom_name():
    parser = build_parser()
    args = parser.parse_args(["--name", "kk"])
    assert args.name == "kk"


def test_main_should_return_zero_on_success():
    exit_code = main(["--name", "kk"])
    assert exit_code == 0


def test_main_should_return_one_on_invalid_name():
    exit_code = main(["--name", "   "])
    assert exit_code == 1