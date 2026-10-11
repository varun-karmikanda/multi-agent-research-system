import re
import time

import streamlit as st

from src.agents.agents import (
    build_search_agent,
    build_reader_agent,
    writer_chain,
    critic_chain,
)

st.set_page_config(
    page_title="Multi-Agent Research Lab",
    page_icon="🔬",
    layout="wide",
)

# ───────────────────────── Theme (zinc-950) ─────────────────────────
ZINC_950 = "#09090b"
ZINC_900 = "#18181b"
ZINC_800 = "#27272a"
ZINC_700 = "#3f3f46"
ZINC_400 = "#a1a1aa"
ZINC_100 = "#f4f4f5"
ACCENT = "#34d399"  # emerald-400

st.markdown(
    f"""
    <style>
    .stApp {{ background: {ZINC_950}; color: {ZINC_100}; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    section[data-testid="stSidebar"] {{
        background: {ZINC_900};
        border-right: 1px solid {ZINC_800};
    }}
    h1, h2, h3, h4, p, label, span, li {{ color: {ZINC_100}; }}
    .muted {{ color: {ZINC_400} !important; }}

    /* inputs */
    .stTextInput input, .stTextArea textarea {{
        background: {ZINC_900} !important;
        color: {ZINC_100} !important;
        border: 1px solid {ZINC_700} !important;
        border-radius: 10px !important;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: {ACCENT} !important;
        box-shadow: 0 0 0 1px {ACCENT} !important;
    }}

    /* buttons */
    .stButton > button, .stDownloadButton > button {{
        background: {ACCENT};
        color: {ZINC_950};
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.55rem 1.2rem;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background: #6ee7b7;
        color: {ZINC_950};
    }}
    .stDownloadButton > button {{
        background: {ZINC_800};
        color: {ZINC_100};
        border: 1px solid {ZINC_700};
    }}
    .stDownloadButton > button:hover {{
        background: {ZINC_700};
        color: {ZINC_100};
    }}

    /* status + expander cards */
    div[data-testid="stStatusWidget"], details {{
        background: {ZINC_900} !important;
        border: 1px solid {ZINC_800} !important;
        border-radius: 12px !important;
    }}

    /* tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid {ZINC_800}; }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: {ZINC_400};
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
    }}
    .stTabs [aria-selected="true"] {{ color: {ACCENT} !important; }}
    .stTabs [data-baseweb="tab-highlight"] {{ background-color: {ACCENT}; }}

    /* cards */
    .card {{
        background: {ZINC_900};
        border: 1px solid {ZINC_800};
        border-radius: 14px;
        padding: 18px 20px;
    }}
    .hero-title {{
        font-size: 2.3rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0;
    }}
    .hero-title span {{ color: {ACCENT}; }}
    .pill {{
        display: inline-block; padding: 3px 12px; border-radius: 999px;
        font-size: 0.8rem; font-weight: 600; border: 1px solid {ZINC_700};
        background: {ZINC_800}; color: {ZINC_100};
    }}
    .pill-good {{ border-color: #059669; color: {ACCENT}; background: #022c22; }}
    .pill-mid  {{ border-color: #b45309; color: #fbbf24; background: #2a1a02; }}
    .pill-bad  {{ border-color: #b91c1c; color: #f87171; background: #2a0a0a; }}
    .score {{ font-size: 3rem; font-weight: 700; color: {ACCENT}; line-height: 1; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ───────────────────────── Helpers ─────────────────────────
STAGES = ["Search", "Read", "Write", "Review"]


def parse_critic(feedback: str):
    score_m = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback or "")
    verdict_m = re.search(r"verdict:\s*\[?([A-Za-z ]+?)\]?\s*$", feedback or "", re.I | re.M)
    score = score_m.group(1) if score_m else None
    verdict = verdict_m.group(1).strip() if verdict_m else None
    return score, verdict


def verdict_class(verdict: str | None) -> str:
    v = (verdict or "").lower()
    if v.startswith("acceptable"):
        return "pill-good"
    if v.startswith("needs"):
        return "pill-mid"
    if v.startswith("unacceptable"):
        return "pill-bad"
    return ""


def pause(seconds: int, label: str):
    """Gentle delay between stages to stay under free-tier TPM limits."""
    if seconds > 0:
        with st.spinner(f"{label} (waiting {seconds}s for rate limit window)…"):
            time.sleep(seconds)


def run_pipeline(topic: str, wait: int) -> dict:
    state: dict = {}

    # 1. Search
    with st.status("🔎 Search agent: gathering sources…", expanded=False) as s:
        agent = build_search_agent()
        res = agent.invoke(
            {
                "messages": [
                    (
                        "user",
                        f"Search for information on the topic: {topic}. "
                        "Provide titles, URLs, and short snippets of relevant content.",
                    )
                ]
            }
        )
        state["search_results"] = res["messages"][-1].content
        s.update(label="🔎 Search agent: done", state="complete")

    pause(wait, "Cooling down before reader")

    # 2. Read
    with st.status("📖 Reader agent: scraping pages…", expanded=False) as s:
        agent = build_reader_agent()
        res = agent.invoke(
            {
                "messages": [
                    (
                        "user",
                        f"Based on the following search result about topic '{topic}', "
                        "pick the most relevant URLs and scrape their content. "
                        "For every scrape call, pass the complete URL as the tool's 'url' argument. "
                        "Do not pass search parameters. Summarize the scraped content concisely."
                        f"\n\nSearch Results:\n{state['search_results']}",
                    )
                ]
            }
        )
        state["scraped_content"] = res["messages"][-1].content
        s.update(label="📖 Reader agent: done", state="complete")

    pause(wait, "Cooling down before writer")

    # 3. Write
    with st.status("✍️ Writer: drafting report…", expanded=False) as s:
        research = (
            f"Search Results:\n{state['search_results']}\n\n"
            f"Detailed Scraped Content:\n{state['scraped_content']}\n\n"
        )
        state["report"] = writer_chain.invoke({"topic": topic, "research": research})
        s.update(label="✍️ Writer: done", state="complete")

    pause(wait, "Cooling down before critic")

    # 4. Review
    with st.status("🧐 Critic: reviewing report…", expanded=False) as s:
        state["feedback"] = critic_chain.invoke(
            {"topic": topic, "report": state["report"]}
        )
        s.update(label="🧐 Critic: done", state="complete")

    state["topic"] = topic
    return state


# ───────────────────────── Sidebar ─────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    wait = st.slider(
        "Pause between stages (s)",
        0,
        60,
        15,
        help="Helps avoid Groq free-tier rate limits (8K tokens/min).",
    )
    st.markdown("---")
    st.markdown("### 🧩 Pipeline")
    for i, name in enumerate(STAGES, 1):
        st.markdown(f"<span class='muted'>{i}.</span> {name}", unsafe_allow_html=True)
    st.markdown("---")
    st.caption("Search → Read → Write → Review")

# ───────────────────────── Main ─────────────────────────
st.markdown(
    "<p class='hero-title'>Multi-Agent <span>Research Lab</span></p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='muted'>Four agents search the web, read sources, write a report, and critique it.</p>",
    unsafe_allow_html=True,
)

col_input, col_btn = st.columns([5, 1], vertical_alignment="bottom")
with col_input:
    topic = st.text_input(
        "Research topic",
        placeholder="e.g. LLM based multi-agent systems",
        label_visibility="collapsed",
    )
with col_btn:
    run = st.button("Run research", use_container_width=True)

if run:
    if not topic.strip():
        st.warning("Enter a topic first.")
    else:
        try:
            st.session_state["result"] = run_pipeline(topic.strip(), wait)
        except Exception as e:
            st.session_state.pop("result", None)
            st.error(f"Pipeline failed: {e}")

# ───────────────────────── Results ─────────────────────────
result = st.session_state.get("result")
if result:
    score, verdict = parse_critic(result["feedback"])

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        st.markdown(
            f"<div class='card'><div class='muted'>Critic score</div>"
            f"<div class='score'>{score or '–'}<span class='muted' style='font-size:1.1rem'>/10</span></div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='card'><div class='muted'>Verdict</div><br>"
            f"<span class='pill {verdict_class(verdict)}'>{verdict or 'n/a'}</span></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div class='card'><div class='muted'>Topic</div>"
            f"<div style='font-size:1.15rem;font-weight:600;margin-top:6px'>{result['topic']}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    tab_report, tab_review, tab_sources, tab_scraped = st.tabs(
        ["📄 Report", "🧐 Critic", "🔗 Sources", "📖 Scraped summary"]
    )

    with tab_report:
        st.markdown(result["report"])
        st.download_button(
            "Download report (.md)",
            data=result["report"],
            file_name="research_report.md",
            mime="text/markdown",
        )

    with tab_review:
        st.markdown(result["feedback"])

    with tab_sources:
        st.markdown(result["search_results"])

    with tab_scraped:
        st.markdown(result["scraped_content"])
else:
    st.markdown(
        "<div class='card muted' style='margin-top:24px'>"
        "Enter a topic above and hit <b>Run research</b>. Results appear here.</div>",
        unsafe_allow_html=True,
    )