from optimus_backend.infrastructure.source_connectors.in_memory_connector import InMemorySourceConnector
from optimus_backend.infrastructure.tools.code_search_tool import CodeSearchTool
from optimus_backend.infrastructure.tools.config_inspection_tool import ConfigInspectionTool
from optimus_backend.infrastructure.tools.diff_analysis_tool import DiffAnalysisTool
from optimus_backend.infrastructure.tools.log_analysis_tool import LogAnalysisTool


def test_code_search_tool_matches_paths_and_lines() -> None:
    tool = CodeSearchTool()
    output, truncated = tool.run(
        {
            "query": "handler",
            "files": [
                {"path": "src/service.py", "content": "def handler():\n    return 1"},
                {"path": "src/other.py", "content": "print('x')"},
            ],
        }
    )
    assert "src/service.py:1:def handler()" in output
    assert truncated is False


def test_diff_analysis_tool_requires_diff() -> None:
    tool = DiffAnalysisTool()
    output, truncated = tool.run({"diff_text": "--- a/x.py\n+++ b/x.py\n@@\n-a\n+b"})
    assert "touched_files=" in output
    assert truncated is False


def test_log_and_config_analysis_tools() -> None:
    log_tool = LogAnalysisTool()
    log_output, _ = log_tool.run({"log_text": "INFO ok\nERROR failure"})
    assert "errors=1" in log_output

    config_tool = ConfigInspectionTool()
    cfg_output, _ = config_tool.run({"config_text": '{"service":"optimus","debug":false}'})
    assert "json_valid=true" in cfg_output


def test_in_memory_source_connector_minimum_contract() -> None:
    connector = InMemorySourceConnector({"src/app.py": "print('hi')", "README.md": "Optimus"})
    assert connector.fetch_file("src/app.py") == "print('hi')"
    assert "src/app.py" in connector.list_files("src/*.py")
    result = connector.search("optimus")
    assert result[0]["path"] == "README.md"
    assert result[0]["line_number"] == 1
