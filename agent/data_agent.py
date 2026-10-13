from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from agent.prompts import SYSTEM_PROMPT


def create_backend() -> Any:
    backend_mode = os.getenv("DEEPAGENT_BACKEND", "local-shell").strip().lower()

    if backend_mode == "local-shell":
        from deepagents.backends import LocalShellBackend

        root_dir = os.getenv("DEEPAGENT_ROOT_DIR", tempfile.mkdtemp(prefix="data-agent-"))
        return LocalShellBackend(root_dir=root_dir, virtual_mode=True, env={"PATH": os.environ.get("PATH", "")})

    if backend_mode == "langsmith":
        try:
            from deepagents.backends.langsmith import LangSmithSandbox
            from langsmith.sandbox import SandboxClient
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("LangSmith sandbox backend requested but unavailable.") from exc

        client = SandboxClient()
        sandbox = client.create_sandbox()
        return LangSmithSandbox(sandbox=sandbox)

    raise RuntimeError(
        "No supported Deep Agents backend is configured. Set DEEPAGENT_BACKEND=local-shell or LANGSmith sandbox settings."
    )


def build_agent(model_name: str | None = None, backend: Any | None = None, *, system_prompt: str | None = None) -> Any:
    if backend is None:
        raise ValueError("A Deep Agents backend is required to build the analysis agent.")

    resolved_model = model_name or os.getenv("DEEP_AGENT_MODEL", "google_genai:gemini-2.5-flash")
    agent = create_deep_agent(
        model=resolved_model,
        tools=[],
        backend=backend,
        checkpointer=InMemorySaver(),
        middleware=[TodoListMiddleware()],
        system_prompt=system_prompt or SYSTEM_PROMPT,
    )
    return agent


def run_agent_analysis(question: str, dataset_path: str | Path, backend: Any | None, model_name: str | None = None) -> dict[str, Any]:
    if backend is None:
        return {
            "success": False,
            "error": "A Deep Agents backend is required. Configure LANGSMITH_API_KEY or DEEPAGENT_BACKEND=local-shell before running the analysis.",
            "answer": "",
        }

    try:
        agent = build_agent(model_name=model_name, backend=backend)
        user_message = {
            "role": "user",
            "content": (
                f"Analyze the dataset at {dataset_path}. "
                f"Answer this question using the uploaded CSV file: {question}"
            ),
        }
        stream = agent.stream_events({"messages": [user_message]}, {"configurable": {"thread_id": "analysis-session"}}, version="v3")

        output_chunks: list[str] = []
        for snapshot in stream:
            if hasattr(snapshot, "values"):
                for value in snapshot.values:
                    if isinstance(value, dict):
                        if "messages" in value:
                            for message in value["messages"]:
                                if hasattr(message, "content"):
                                    if isinstance(message.content, str):
                                        output_chunks.append(message.content)
                                elif isinstance(message, dict) and "content" in message and isinstance(message["content"], str):
                                    output_chunks.append(message["content"])

        answer = "\n".join(output_chunks).strip() or "The agent returned no textual answer."
        return {"success": True, "answer": answer, "error": ""}
    except Exception as exc:  # pragma: no cover - environment dependent runtime path
        return {"success": False, "answer": "", "error": f"Analysis failed: {exc}"}
