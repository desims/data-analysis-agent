from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

from agent.data_agent import create_backend, run_agent_analysis
from utils.data_loader import DatasetValidationError, load_csv_from_bytes, upload_csv_to_temp
from utils.profiling import summarize_dataset
from utils.report_export import build_markdown_report
from utils.visualization import choose_chart, make_chart_figure

MAX_UPLOAD_SIZE_MB = 20

st.set_page_config(page_title="AI Data Analysis Agent", page_icon="📊", layout="wide")
st.title("AI Data Analysis Agent")
st.caption("Upload a CSV, inspect it, and ask natural-language questions with a Deep Agents analysis workflow.")


def reset_session() -> None:
    for key in list(st.session_state.keys()):
        st.session_state.pop(key)


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "dataset_df" not in st.session_state:
    st.session_state.dataset_df = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "dataset_path" not in st.session_state:
    st.session_state.dataset_path = None
if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = "uploaded_dataset.csv"

with st.sidebar:
    st.header("Controls")
    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=["csv"],
        help="CSV files up to 20 MB are supported.",
    )
    st.caption("Accepted formats: UTF-8 CSV, semicolon/comma/tab delimited files.")
    if st.button("Reset session", use_container_width=True):
        reset_session()
        st.rerun()

    st.subheader("Deep Agents backend")
    backend_hint = "Not configured"
    try:
        create_backend()
        backend_hint = "Configured"
    except Exception:
        backend_hint = "Requires LangSmith or a local shell backend"
    st.info(backend_hint)

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        df = load_csv_from_bytes(file_bytes, max_bytes=MAX_UPLOAD_SIZE_MB * 1024 * 1024)
        profile = summarize_dataset(df)
        temp_dir = Path(tempfile.mkdtemp(prefix="ai_data_agent_"))
        dataset_path = upload_csv_to_temp(file_bytes, temp_dir)

        st.session_state.dataset_df = df
        st.session_state.profile = profile
        st.session_state.dataset_path = str(dataset_path)
        st.session_state.dataset_name = uploaded_file.name
        st.session_state.chat_history = []
        st.session_state.dataset_id = str(uuid.uuid4())

        st.success(f"Dataset loaded: {uploaded_file.name}")
    except DatasetValidationError as exc:
        st.error(str(exc))
        st.session_state.dataset_df = None
        st.session_state.profile = None
        st.session_state.dataset_path = None
        st.session_state.chat_history = []

if st.session_state.dataset_df is not None:
    df: pd.DataFrame = st.session_state.dataset_df
    profile = st.session_state.profile

    st.subheader("Dataset overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", profile["row_count"])
    col2.metric("Columns", profile["column_count"])
    col3.metric("Missing cells", sum(profile["missing_values"].values()))

    with st.expander("Column and data type summary"):
        st.dataframe(
            pd.DataFrame(
                {
                    "column": list(profile["columns"]),
                    "dtype": [profile["dtypes"][col] for col in profile["columns"]],
                    "missing_values": [profile["missing_values"].get(col, 0) for col in profile["columns"]],
                }
            ),
            use_container_width=True,
        )

    with st.expander("Dataset preview"):
        st.dataframe(df.head(10), use_container_width=True)

    st.subheader("Natural-language analysis")
    question = st.text_area(
        "Ask a question about the uploaded file",
        placeholder="Example: Which products generated the highest revenue, and how did revenue change over time?",
        height=120,
    )

    if st.button("Run analysis"):
        if not question.strip():
            st.warning("Enter a question before running the analysis.")
        else:
            backend = None
            try:
                backend = create_backend()
            except Exception as exc:  # pragma: no cover - environment-dependent runtime path
                st.error(
                    "The live Deep Agents backend is not configured for this environment. "
                    "Set LANGSMITH_API_KEY for a LangSmith sandbox or use DEEPAGENT_BACKEND=local-shell."
                )
                st.code(str(exc))
            else:
                result = run_agent_analysis(question, st.session_state.dataset_path, backend)
                if result["success"]:
                    st.session_state.chat_history.append({"role": "user", "content": question})
                    st.session_state.chat_history.append({"role": "assistant", "content": result["answer"]})
                else:
                    st.error(result["error"])

    if st.session_state.chat_history:
        st.subheader("Conversation")
        for entry in st.session_state.chat_history:
            with st.chat_message(entry["role"]):
                st.markdown(entry["content"])

    if profile["numeric_columns"]:
        st.subheader("Recommended visualizations")
        numeric_cols = profile["numeric_columns"]
        x_col = profile["datetime_columns"][0] if profile["datetime_columns"] else numeric_cols[0]
        y_col = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
        chart_type = choose_chart(df, x_col=x_col, y_col=y_col)
        if chart_type != "invalid":
            fig = make_chart_figure(df, chart_type, x_col=x_col, y_col=y_col, title=f"{y_col} vs {x_col}")
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

    st.subheader("Download report")
    answer_text = "\n".join(
        entry["content"]
        for entry in st.session_state.chat_history
        if entry["role"] == "assistant"
    )
    report = build_markdown_report(
        question="Latest analysis question",
        profile=profile,
        answer=answer_text or "No analysis performed yet.",
        dataset_name=st.session_state.dataset_name,
    )
    st.download_button(
        label="Download analysis report (.md)",
        data=report,
        file_name="data_analysis_report.md",
        mime="text/markdown",
    )

else:
    st.info("Upload a CSV file to begin dataset profiling and analysis.")
