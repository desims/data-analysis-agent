from unittest.mock import MagicMock, patch

from agent.data_agent import build_agent, run_agent_analysis


def test_build_agent_uses_supplied_model_and_backend():
    backend = object()
    with patch("agent.data_agent.create_deep_agent") as mock_create:
        mock_create.return_value = MagicMock()
        agent = build_agent(model_name="openai:gpt-4o-mini", backend=backend)
        assert agent is not None
        assert mock_create.call_count == 1
        assert mock_create.call_args.kwargs["model"] == "openai:gpt-4o-mini"
        assert mock_create.call_args.kwargs["backend"] is backend


def test_run_agent_analysis_handles_missing_backend():
    result = run_agent_analysis(question="What is the trend?", dataset_path="/tmp/data.csv", backend=None)
    assert result["success"] is False
    assert "backend" in result["error"].lower()
