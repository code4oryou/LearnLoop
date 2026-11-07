
import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

from engine import run_learnloop
from memory.store import init_db, recent_lessons

ROOT = Path(__file__).resolve().parent
LESSONS_DIR = ROOT / "artifacts" / "lessons"
LOGS_DIR = ROOT / "artifacts" / "evaluation_logs"

LESSONS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
init_db()

st.set_page_config(
    page_title="LearnLoop — Content Intelligence",
    page_icon="✳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- DESIGN SYSTEM --------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #090d18;
    --panel: #111827;
    --border: #253047;
    --muted: #929db2;
    --text: #edf1fa;
    --accent: #a78bfa;
}

/* 1. Global App Layout & Typography */
.stApp {
    background:
        radial-gradient(ellipse at 75% 0%, rgba(91, 70, 170, .15), transparent 40%),
        #090d18 !important;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

h1, h2, h3 {
    font-family: 'Manrope', sans-serif !important;
    letter-spacing: -0.7px;
    color: #f2f4fc !important;
}

p, label, li {
    color: #c0c9d9;
}

/* 2. Fix the "keyboard_d" Font / Icon Glitch in Sidebar */
[data-testid="stSidebarCollapseButton"] span:not([class*="material"]),
button[data-testid="baseButton-headerNoPadding"] span,
[data-testid="stSidebar"] [data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded" !important;
    font-weight: normal !important;
    font-style: normal !important;
    font-size: 1.1rem !important;
}

[data-testid="stSidebarCollapseButton"] span:contains("keyboard_d"),
[data-testid="stSidebar"] span:contains("keyboard_d") {
    display: none !important;
    font-size: 0px !important;
}

/* 3. Sidebar Styling */
[data-testid="stSidebar"] {
    background: #0c1220 !important;
    border-right: 1px solid #202a3d !important;
}

[data-testid="stSidebar"] * {
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stSidebar"] hr {
    border-color: #263249 !important;
    margin-top: 20px;
    margin-bottom: 20px;
}

.brand {
    font-family: 'Manrope', sans-serif;
    font-size: 27px;
    font-weight: 800;
    letter-spacing: -1.4px;
    color: #f5f3ff;
}

.brand span {
    color: #a78bfa;
}

.small-muted {
    color: #8492aa;
    font-size: 12px;
    line-height: 1.5;
}

/* 4. Hero Section */
.hero {
    padding: 28px 32px;
    border: 1px solid #303451;
    border-radius: 18px;
    background:
        radial-gradient(ellipse at 85% 10%, rgba(139, 92, 246, .22), transparent 45%),
        linear-gradient(120deg, #151b30, #101727);
    margin: 8px 0 24px 0;
}

.eyebrow {
    color: #a78bfa;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.hero-title {
    font-family: 'Manrope', sans-serif;
    font-size: clamp(26px, 4vw, 38px);
    font-weight: 800;
    line-height: 1.2;
    letter-spacing: -1.8px;
    color: #f6f5ff;
    margin: 10px 0;
}

.hero-copy {
    font-size: 14px;
    color: #aab5ca;
    max-width: 650px;
    line-height: 1.8;
}

.section-label {
    color: #a78bfa;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.6px;
    text-transform: uppercase;
    margin-bottom: 10px;
}

/* 5. Metrics Cards */
div[data-testid="stMetric"] {
    background: #111827 !important;
    border: 1px solid #263249 !important;
    padding: 16px !important;
    border-radius: 12px !important;
    transition: border-color .2s ease, transform .2s ease;
}

div[data-testid="stMetric"]:hover {
    border-color: #8066d3 !important;
    transform: translateY(-2px);
}

div[data-testid="stMetricLabel"] {
    color: #9ba9c0 !important;
}

div[data-testid="stMetricValue"] {
    color: #f5f3ff !important;
}

/* 6. Fix Expander Headers (Eliminates White Glare in Dark Mode) */
[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid #28344a !important;
    border-radius: 11px !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] details {
    background: #111827 !important;
    border: none !important;
}

[data-testid="stExpander"] summary {
    background: #111827 !important;
    color: #edf1fa !important;
    padding: 14px 18px !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
}

[data-testid="stExpander"] summary:hover {
    background: #182235 !important;
    color: #c4b5fd !important;
}

[data-testid="stExpander"] summary p {
    color: #edf1fa !important;
    font-weight: 600 !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: #0d1322 !important;
    padding: 18px !important;
    border-top: 1px solid #1f2a3d !important;
}

/* 7. Alerts, Success, and Info Boxes (Dark Theme Integration) */
[data-testid="stAlert"] {
    background: #131b2e !important;
    border: 1px solid #2e3d5b !important;
    border-radius: 10px !important;
}

[data-testid="stAlert"] p {
    color: #dbe4f0 !important;
}

/* 8. Buttons & Inputs */
.stButton > button {
    border-radius: 10px !important;
    min-height: 44px !important;
    font-weight: 700 !important;
    border: 1px solid #7255c7 !important;
    background: linear-gradient(110deg, #7857d5, #6245b8) !important;
    color: white !important;
    transition: all .2s ease !important;
}

.stButton > button:hover {
    border-color: #b9a3ff !important;
    background: linear-gradient(110deg, #8969e8, #7253d0) !important;
    transform: translateY(-1px) !important;
}

.stDownloadButton > button {
    border-radius: 9px !important;
    background: #151d2e !important;
    border: 1px solid #34425b !important;
    color: #e2e8f5 !important;
    transition: all .2s ease !important;
}

.stDownloadButton > button:hover {
    border-color: #a78bfa !important;
    color: #c4b5fd !important;
}

.stTextInput input {
    background: #111827 !important;
    border: 1px solid #34415a !important;
    border-radius: 9px !important;
    color: #f5f3ff !important;
}

.stTextInput input:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 1px #a78bfa !important;
}

/* 9. Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 14px;
    border-bottom: 1px solid #263249 !important;
}

.stTabs [data-baseweb="tab"] {
    color: #9ba9c0 !important;
    font-weight: 600 !important;
    padding: 12px 16px !important;
}

.stTabs [aria-selected="true"] {
    color: #c4b5fd !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background-color: #a78bfa !important;
}

/* 10. Status Badges */
.status-approved {
    color: #86efac;
    background: rgba(34, 197, 94, .1);
    border: 1px solid rgba(34, 197, 94, .35);
    border-radius: 11px;
    padding: 14px 18px;
    font-size: 14px;
    font-weight: 700;
    margin: 10px 0 20px 0;
}

.status-rejected {
    color: #fca5a5;
    background: rgba(239, 68, 68, .1);
    border: 1px solid rgba(239, 68, 68, .35);
    border-radius: 11px;
    padding: 14px 18px;
    font-size: 14px;
    font-weight: 700;
    margin: 10px 0 20px 0;
}

/* 11. Clean Lesson Reading Area */
[data-testid="stMarkdownContainer"] h1 {
    font-size: 2rem !important;
    letter-spacing: -1px !important;
    margin-bottom: 1.2rem !important;
}

[data-testid="stMarkdownContainer"] h2 {
    font-size: 1.4rem !important;
    margin-top: 1.8rem !important;
    padding-bottom: 6px;
    border-bottom: 1px solid #263249;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    line-height: 1.8 !important;
}

hr {
    border-color: #263249 !important;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown(
        '<div class="brand">Learn<span>Loop</span> ✳</div>',
        unsafe_allow_html=True
    )

    st.caption("CONTENT INTELLIGENCE SYSTEM")

    st.divider()

    st.markdown("### Workspace")
    st.markdown("✳  Lesson generator")
    st.markdown("◈  Quality evaluator")
    st.markdown("↻  Revision engine")
    st.markdown("▤  Evaluation history")

    st.divider()

    st.markdown("### System configuration")
    st.markdown("**Generation model**")
    st.caption("Gemini Flash-Lite")

    st.markdown("**Maximum attempts**")
    st.caption("3 total · 1 generation + 2 revisions")

    st.markdown("**Approval policy**")
    st.caption("All quality gates must pass")

    st.divider()

    st.markdown(
        '<div class="small-muted">LEARNLOOP · CONTENT SYSTEMS<br>'
        'Built with Python, Gemini & LangGraph</div>',
        unsafe_allow_html=True
    )


# -------------------- HEADER --------------------

st.markdown("""
<div class="hero">
    <div class="eyebrow">✳ &nbsp; INTELLIGENT CONTENT WORKSPACE</div>
    <div class="hero-title">
        Better lessons.<br>Proven by evaluation.
    </div>
    <div class="hero-copy">
        Generate educational content, challenge its quality,
        and refine it until it meets every teaching standard.
        No lesson gets approved just because it was generated.
    </div>
</div>
""", unsafe_allow_html=True)


# -------------------- GENERATION INPUT --------------------

st.markdown('<div class="section-label">01 / CREATE A LESSON</div>',
            unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### What should we teach today?")
    st.caption(
        "Choose a topic. LearnLoop will generate a lesson "
        "and evaluate it against its quality rubric."
    )

    topic = st.text_input(
        "Topic",
        value="Introduction to RAG",
        placeholder="e.g. Introduction to Machine Learning",
        label_visibility="collapsed"
    )

    st.markdown("")

    demo_mode = st.checkbox(
        "Enable evaluator stress test",
        help=(
            "Injects a deliberately incorrect factual statement "
            "to demonstrate whether the evaluator catches it."
        )
    )

    if demo_mode:
        st.warning(
            "Stress-test mode: a deliberate RAG misconception "
            "will be injected into the initial lesson."
        )

    generate = st.button(
        "✳  Generate and evaluate lesson",
        type="primary",
        use_container_width=True
    )


# -------------------- EXECUTION --------------------

if generate:
    if not topic.strip():
        st.error("Please enter a lesson topic.")
    else:
        try:
            with st.status(
                "LearnLoop is working through the generation pipeline...",
                expanded=True
            ) as status:

                st.write("01 · Generating the lesson")
                st.write("02 · Evaluating against quality gates")
                st.write("03 · Revising if any gate fails")
                st.write("04 · Saving the final evaluation")

                result = run_learnloop(
                    topic.strip(),
                    inject_failure=demo_mode
                )

                status.update(
                    label=(
                        "Lesson approved."
                        if result["approved"]
                        else "Evaluation completed — lesson rejected."
                    ),
                    state="complete"
                )

            timestamp = datetime.now().astimezone().strftime(
                "%Y%m%d_%H%M%S"
            )

            slug = re.sub(
                r"[^a-zA-Z0-9]+",
                "_",
                topic.strip().lower()
            ).strip("_")[:40]

            lesson_path = LESSONS_DIR / f"{slug}_{timestamp}.md"
            log_path = LOGS_DIR / f"{slug}_{timestamp}.json"

            log_data = {
                "topic": topic.strip(),
                "approved": result["approved"],
                "attempts": result["attempts"],
                "checks": result["checks"],
                "rejection_log": result["rejection_log"],
                "summary": result["summary"],
                "generated_at": timestamp
            }

            lesson_path.write_text(
                result["lesson"],
                encoding="utf-8"
            )

            log_path.write_text(
                json.dumps(log_data, indent=2),
                encoding="utf-8"
            )

            st.session_state["run_result"] = result
            st.session_state["run_log"] = log_data

            st.toast("Evaluation report saved successfully.")

        except Exception as exc:
            st.error(f"Something went wrong: {exc}")


# -------------------- RESULTS --------------------

if "run_result" in st.session_state:

    result = st.session_state["run_result"]
    log_data = st.session_state["run_log"]

    st.divider()

    st.markdown(
        '<div class="section-label">02 / EVALUATION RESULTS</div>',
        unsafe_allow_html=True
    )

    if result["approved"]:
        st.markdown(
            '<div class="status-approved">'
            '✓ &nbsp; APPROVED — All quality gates passed.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="status-rejected">'
            '✕ &nbsp; REJECTED — The lesson did not meet every quality requirement.'
            '</div>',
            unsafe_allow_html=True
        )

    checks = result["checks"]
    passed = sum(c["status"] == "PASS" for c in checks)
    failed = len(checks) - passed

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Attempts", f"{result['attempts']} / 3")
    c2.metric("Gates passed", passed)
    c3.metric("Gates failed", failed)
    c4.metric("Approval", "APPROVED" if result["approved"] else "REJECTED")

    lesson_tab, evaluation_tab, history_tab = st.tabs(
        ["◫  Final lesson", "◈  Evaluation report", "↻  Revision history"]
    )

    # -------------------- LESSON TAB --------------------

    with lesson_tab:
        st.markdown("### Generated learning material")
        st.caption(
            "The final lesson produced by the generation and revision pipeline."
        )

        st.markdown(result["lesson"])

        st.divider()

        d1, d2 = st.columns(2)

        with d1:
            st.download_button(
                "↓  Download lesson",
                data=result["lesson"],
                file_name="LearnLoop_Final_Lesson.md",
                mime="text/markdown",
                use_container_width=True
            )

        with d2:
            st.download_button(
                "↓  Download evaluation JSON",
                data=json.dumps(log_data, indent=2),
                file_name="LearnLoop_Evaluation_Log.json",
                mime="application/json",
                use_container_width=True
            )

    # -------------------- EVALUATION TAB --------------------

    with evaluation_tab:
        st.markdown("### Quality gate assessment")
        st.caption(
            "Every criterion is independently marked PASS or FAIL. "
            "A single failure prevents approval."
        )

        for check in checks:
            symbol = "✓" if check["status"] == "PASS" else "✕"

            with st.expander(
                f"{symbol}  {check['id']} · {check['name']} · {check['status']}"
            ):
                st.markdown(f"**Evidence**")
                st.write(check["evidence"] or "No evidence provided.")

                st.markdown("**Evaluator reasoning**")
                st.write(check["reason"])

        st.markdown("**Overall evaluator summary**")
        st.info(result["summary"])

    # -------------------- HISTORY TAB --------------------

    with history_tab:
        st.markdown("### Rejection and revision trail")

        if not result["rejection_log"]:
            st.success(
                "No rejected attempts. The initial lesson passed all checks."
            )

        for entry in result["rejection_log"]:
            with st.expander(
                f"Attempt {entry['attempt']} · Rejected"
            ):
                for failure in entry["failures"]:
                    st.write(f"✕ {failure}")

        if result["rejection_log"]:
            if result["approved"]:
                st.success(
                    f"Lesson approved after {result['attempts']} total attempts."
                )
            else:
                st.error(
                    "Maximum attempts reached. The lesson remains rejected."
                )


# -------------------- PREVIOUS RUNS --------------------

st.divider()

st.markdown('<div class="section-label">03 / WORKSPACE HISTORY</div>',
            unsafe_allow_html=True)

st.markdown("### Previous evaluations")

history = recent_lessons()

if not history:
    st.caption("No previous lessons yet. Generate your first lesson above.")
else:
    for name, approved, attempts, created in history:
        symbol = "✓" if approved else "✕"

        with st.container(border=True):
            left, right = st.columns([3, 1])

            with left:
                st.markdown(f"**{symbol}  {name}**")
                st.caption(f"Created: {created}")

            with right:
                st.caption(
                    f"{'Approved' if approved else 'Rejected'} · "
                    f"{attempts} attempts"
                )
