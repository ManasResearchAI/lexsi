import json
import os
import subprocess
import sys


def test_module_cli_writes_schema(tmp_path):
    output = tmp_path / "schema.json"
    env = {**os.environ, "PYTHONPATH": "src"}
    subprocess.run(
        [sys.executable, "-m", "ticket_system.cli", "write-schema", "--output", str(output)],
        check=True, env=env,
    )
    assert json.loads(output.read_text())["title"] == "Ticket"
