from app.cli import build_parse, run


def test_run_should_return_message():
    result = run("kk")
    assert result == "Hello, kk!"


def test_parser_should_use_default_name():
    parser = build_parse()
    args = parser.parse_args([])
    assert args.name == "AI App"


def test_parser_should_accept_custom_name():
    parser = build_parse()
    args = parser.parse_args(["--name", "kk"])
    assert args.name == "kk"