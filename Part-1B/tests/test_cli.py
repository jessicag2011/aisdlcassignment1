import io
import json

from reminder import cli


def test_cli_returns_typed_input_error_without_api_configuration(
    monkeypatch,
) -> None:
    monkeypatch.setattr(cli.sys, "stdin", io.StringIO('{"wrong":"shape"}'))
    output = io.StringIO()
    monkeypatch.setattr(cli.sys, "stdout", output)

    exit_code = cli.main()

    assert exit_code == 2
    assert json.loads(output.getvalue()) == {
        "error": {"category": "input_error", "code": "invalid_request"}
    }
