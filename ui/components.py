from html import escape

import streamlit as st

from responsible_ai.disclosure import build_ai_disclosure_notice
from domain_types import ContextAnalysis, DraftResult, RiskLevel, Warning, WarningCategory


def inject_construct_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --paper: #FAFAF7;
          --ink: #14151A;
          --surface: #FFFFFF;
          --muted: #E7E5DE;
          --blue: #1E4FA3;
          --red: #C1392B;
          --yellow: #E0A937;
        }
        .stApp { background: var(--paper); color: var(--ink); }
        [data-testid="stHeader"] { background: var(--paper); }
        [data-testid="stSidebar"] {
          background: var(--muted);
          border-right: 2px solid var(--ink);
        }
        .block-container { max-width: 1180px; padding-top: 2.5rem; }
        h1, h2, h3 { color: var(--ink); letter-spacing: -0.03em; }
        h1 { font-size: clamp(2.25rem, 6vw, 4.8rem); line-height: 0.95; }
        h2 { font-size: clamp(1.5rem, 3vw, 2.3rem); }
        p, label, [data-testid="stCaptionContainer"] { color: var(--ink); }
        [data-testid="stTextArea"] textarea,
        [data-baseweb="select"] > div {
          background: var(--surface);
          color: var(--ink);
          border: 2px solid var(--ink);
          border-radius: 0;
        }
        [data-testid="stTextArea"] textarea:focus,
        [data-baseweb="select"] > div:focus-within {
          border-color: var(--blue);
          box-shadow: 0 0 0 2px var(--paper), 0 0 0 4px var(--blue);
        }
        .stButton > button, .stDownloadButton > button {
          min-height: 44px;
          border: 2px solid var(--ink);
          border-radius: 0;
          background: transparent;
          color: var(--ink);
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          box-shadow: 3px 3px 0 var(--ink);
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
          border-color: var(--ink);
          color: var(--ink);
          transform: translate(-1px, -1px);
          box-shadow: 5px 5px 0 var(--ink);
        }
        .stButton > button:active { transform: translate(2px, 2px); box-shadow: none; }
        .primary-action button {
          background: var(--blue) !important;
          color: var(--surface) !important;
        }
        .construct-rule { border-top: 3px solid var(--ink); margin: 1rem 0 1.5rem; }
        .eyebrow {
          color: var(--blue);
          font-size: 0.72rem;
          font-weight: 800;
          letter-spacing: 0.18em;
          text-transform: uppercase;
        }
        .brand-mark {
          display: inline-block;
          width: 16px;
          height: 16px;
          border: 2px solid var(--ink);
          position: relative;
          margin-right: 8px;
          vertical-align: -2px;
        }
        .brand-mark:after {
          content: "";
          position: absolute;
          width: 6px;
          height: 6px;
          background: var(--blue);
          right: -5px;
          bottom: -5px;
          border: 2px solid var(--ink);
        }
        .review-panel, .analysis-panel, .disclosure-panel, .empty-panel {
          background: var(--surface);
          border: 2px solid var(--ink);
          padding: 1.25rem;
          margin-bottom: 1rem;
        }
        .review-panel { border-left: 6px solid var(--blue); }
        .disclosure-panel { border-color: var(--blue); }
        .draft-text {
          white-space: pre-wrap;
          font-family: "Space Mono", "Courier New", monospace;
          line-height: 1.65;
          font-size: 0.96rem;
        }
        .warning-item {
          border: 2px solid var(--ink);
          border-left: 6px solid var(--red);
          padding: 0.9rem;
          margin: 0.75rem 0;
          background: var(--surface);
        }
        .warning-item.medium { border-left-color: var(--yellow); }
        .warning-category {
          font-size: 0.72rem;
          font-weight: 800;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }
        .triggering-phrase {
          display: block;
          font-family: "Space Mono", "Courier New", monospace;
          margin: 0.45rem 0;
        }
        .status-row {
          display: flex;
          justify-content: space-between;
          gap: 1rem;
          border-bottom: 1px solid var(--ink);
          padding: 0.7rem 0;
          font-size: 0.85rem;
        }
        .status-value { font-weight: 800; text-align: right; }
        .risk-high { color: var(--red); }
        .risk-medium { color: #8A5B00; }
        .risk-low { color: #2A6B35; }
        .entity {
          display: inline-block;
          border: 2px solid var(--blue);
          color: var(--blue);
          padding: 0.25rem 0.45rem;
          margin: 0.2rem 0.3rem 0.2rem 0;
          font-size: 0.76rem;
          font-weight: 700;
        }
        .footer-note {
          border-top: 2px solid var(--ink);
          margin-top: 2rem;
          padding-top: 1rem;
          font-size: 0.78rem;
        }
        @media (max-width: 700px) {
          .block-container { padding: 1.25rem 1rem 2rem; }
          .review-panel, .analysis-panel, .disclosure-panel { padding: 1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        '<div class="eyebrow"><span class="brand-mark"></span>Responsible AI / Human review</div>',
        unsafe_allow_html=True,
    )
    st.title("ReplyWise")
    st.markdown(
        "Draft a reply while keeping the model’s assumptions, commitments, and sensitive details visible.",
    )
    st.markdown('<div class="construct-rule"></div>', unsafe_allow_html=True)


def render_disclosure() -> None:
    st.markdown(
        f'<div class="disclosure-panel"><strong>AI-assisted draft</strong><br>'
        f'{escape(build_ai_disclosure_notice())}</div>',
        unsafe_allow_html=True,
    )


def render_draft_panel(draft_result: DraftResult, draft_text: str, is_editing: bool) -> None:
    st.markdown(
        '<div class="review-panel"><div class="eyebrow">AI-assisted draft</div>'
        f'<div class="draft-text">{escape(draft_text)}</div></div>',
        unsafe_allow_html=True,
    )
    if not is_editing:
        st.code(draft_text, language=None)


def render_warning_panel(warnings: tuple[Warning, ...]) -> None:
    if not warnings:
        st.markdown(
            '<div class="analysis-panel"><div class="eyebrow">Responsible AI review</div>'
            "<strong>No potential issues detected by the prototype checks.</strong><br>"
            "Human review is still required.</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div class="analysis-panel"><div class="eyebrow">{len(warnings)} issue(s) flagged</div>',
        unsafe_allow_html=True,
    )
    for warning in warnings:
        severity_class = "medium" if warning.category == WarningCategory.INVENTED_DETAIL else ""
        st.markdown(
            f'<div class="warning-item {severity_class}">'
            f'<span class="warning-category">{escape(_warning_title(warning.category))}</span>'
            f'<span class="triggering-phrase">“{escape(warning.triggering_phrase)}”</span>'
            f'<span>{escape(warning.explanation)}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_transparency_panel(analysis: ContextAnalysis) -> None:
    st.markdown(
        '<div class="analysis-panel"><div class="eyebrow">Transparency</div>'
        f"<h3>{escape(analysis.intent)}</h3>"
        "<strong>Key entities</strong><br>"
        f"{_render_entities(analysis.key_entities)}"
        "<br><strong>Detected requests</strong>",
        unsafe_allow_html=True,
    )
    if analysis.detected_requests:
        for request in analysis.detected_requests:
            st.markdown(f"- {request}")
    else:
        st.caption("No explicit request phrase detected.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar_status(
    provider_name: str,
    draft_result: DraftResult | None,
) -> None:
    st.sidebar.markdown("## Review controls")
    st.sidebar.markdown(
        "ReplyWise never sends mail. It stops at a reviewed draft you can copy."
    )
    st.sidebar.markdown('<div class="construct-rule"></div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<div class="status-row"><span>Provider</span><span class="status-value">'
        f"{escape(provider_name)}</span></div>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<div class="status-row"><span>AI disclosure</span>'
        '<span class="status-value">ALWAYS ON</span></div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<div class="status-row"><span>Human review</span>'
        '<span class="status-value">REQUIRED</span></div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<div class="status-row"><span>Autonomous sending</span>'
        '<span class="status-value">NOT AVAILABLE</span></div>',
        unsafe_allow_html=True,
    )
    if draft_result is not None:
        risk_class = f"risk-{draft_result.risk_level.value}"
        st.sidebar.markdown(
            f'<div class="status-row"><span>Prototype heuristic</span>'
            f'<span class="status-value {risk_class}">'
            f"{escape(draft_result.risk_level.value.upper())}</span></div>",
            unsafe_allow_html=True,
        )


def render_footer() -> None:
    st.markdown(
        '<div class="footer-note"><strong>Prototype boundary:</strong> '
        "ReplyWise attempts to identify common unsupported claims and sensitive details. "
        "It does not guarantee correctness, privacy, or fairness. "
        '<span id="privacy">Privacy: input stays in this process unless the selected '
        "provider sends it to its configured endpoint.</span> "
        '<span id="terms">Terms: review every draft before using it.</span></div>',
        unsafe_allow_html=True,
    )


def _warning_title(category: WarningCategory) -> str:
    titles = {
        WarningCategory.SENSITIVE_INFO: "Sensitive information",
        WarningCategory.UNSUPPORTED_COMMITMENT: "Unsupported commitment",
        WarningCategory.UNVERIFIABLE_CLAIM: "Unverifiable claim",
        WarningCategory.INVENTED_DETAIL: "Invented detail",
    }
    return titles[category]


def _render_entities(entities: tuple[str, ...]) -> str:
    if not entities:
        return '<span class="entity">None detected</span>'
    return "".join(f'<span class="entity">{escape(entity)}</span>' for entity in entities)