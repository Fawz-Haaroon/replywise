from pathlib import Path

import streamlit as st

from config import AppConfig, ConfigurationError, load_config
from domain.drafting import create_draft_result, review_existing_draft
from domain.intake import create_email_context
from llm.providers.gemini_provider import GeminiProvider
from llm.providers.groq_provider import GroqProvider
from llm.providers.ollama_provider import OllamaProvider
from llm.providers.offline_provider import OfflinePreviewProvider
from domain_types import DraftResult, EmailContext, Tone
from ui.components import (
    inject_construct_styles,
    render_draft_panel,
    render_disclosure,
    render_footer,
    render_header,
    render_sidebar_status,
    render_transparency_panel,
    render_warning_panel,
)


DEMO_EMAIL = """Hi Alex,

Can we move tomorrow's project review to Friday at 3 PM? Also, please send me the updated report before the meeting.

Thanks,
Rahul"""


def main() -> None:
    st.set_page_config(
        page_title="ReplyWise",
        page_icon="R",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_construct_styles()
    render_header()

    try:
        config = load_config(Path(__file__).resolve().parent / ".env")
        provider = create_provider(config)
    except (ConfigurationError, ValueError) as error:
        st.error(str(error))
        st.stop()

    draft_result = _render_input_and_generate(config, provider)
    render_sidebar_status(provider.provider_name, draft_result)

    if draft_result is None:
        st.markdown(
            '<div class="empty-panel"><div class="eyebrow">Human review first</div>'
            "<strong>Your generated draft will appear with its warnings and source reading here.</strong>"
            "</div>",
            unsafe_allow_html=True,
        )
        render_footer()
        return

    render_disclosure()
    _render_review_surface(draft_result, provider)
    render_footer()


def create_provider(config: AppConfig):
    provider_factories = {
        "offline": OfflinePreviewProvider,
        "ollama": lambda: OllamaProvider(config),
        "groq": lambda: GroqProvider(config),
        "gemini": lambda: GeminiProvider(config),
    }
    return provider_factories[config.llm_provider]()


def _render_input_and_generate(config: AppConfig, provider) -> DraftResult | None:
    if "original_email" not in st.session_state:
        st.session_state.original_email = DEMO_EMAIL
    if "instruction" not in st.session_state:
        st.session_state.instruction = "Keep it concise and confirm Friday at 3 PM works."
    if "tone" not in st.session_state:
        st.session_state.tone = Tone.PROFESSIONAL.value
    if "draft_result" not in st.session_state:
        st.session_state.draft_result = None
    if "editing" not in st.session_state:
        st.session_state.editing = False

    st.markdown('<div class="eyebrow">01 / Provide context</div>', unsafe_allow_html=True)
    original_email = st.text_area(
        "Original email",
        key="original_email",
        height=190,
        placeholder="Paste the email you received here…",
    )
    input_columns = st.columns([1, 2])
    with input_columns[0]:
        tone = st.selectbox(
            "Tone",
            options=[tone.value for tone in Tone],
            key="tone",
        )
    with input_columns[1]:
        instruction = st.text_input(
            "Additional instruction, optional",
            key="instruction",
            placeholder="Keep it short and confirm Friday works",
        )

    action_columns = st.columns([1, 3])
    with action_columns[0]:
        st.markdown('<div class="primary-action">', unsafe_allow_html=True)
        should_generate = st.button("Generate draft", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    if should_generate:
        try:
            email_context = create_email_context(
                original_email=original_email,
                tone=Tone(tone),
                instruction=instruction,
            )
            with st.spinner("Drafting and running the review checks…"):
                st.session_state.draft_result = create_draft_result(email_context, provider)
            st.session_state.editing = False
        except (RuntimeError, ValueError) as error:
            st.error(str(error))
            st.session_state.draft_result = None
    return st.session_state.draft_result


def _render_review_surface(draft_result: DraftResult, provider) -> None:
    st.markdown('<div class="eyebrow">02 / Review before use</div>', unsafe_allow_html=True)
    if st.session_state.editing:
        edited_draft = st.text_area(
            "Edit draft",
            value=draft_result.draft_text,
            key="draft_editor",
            height=240,
        )
        st.caption("Unsaved changes are not used until you apply them.")
        edit_columns = st.columns(2)
        with edit_columns[0]:
            if st.button("Save & review", use_container_width=True):
                email_context = _current_email_context()
                if email_context is None:
                    st.error("The current email context is unavailable. Generate a new draft.")
                else:
                    try:
                        st.session_state.draft_result = review_existing_draft(
                            draft_text=edited_draft,
                            email_context=email_context,
                            analysis=draft_result.analysis,
                            provider=provider,
                        )
                        st.session_state.editing = False
                        st.rerun()
                    except (RuntimeError, ValueError) as error:
                        st.error(str(error))
        with edit_columns[1]:
            if st.button("Discard changes", use_container_width=True):
                st.session_state.editing = False
                st.rerun()
        review_columns = st.columns([1.08, 0.92])
        with review_columns[0]:
            render_draft_panel(draft_result, edited_draft, True)
        with review_columns[1]:
            render_warning_panel(draft_result.warnings)
            render_transparency_panel(draft_result.analysis)
        return

    review_columns = st.columns([1.08, 0.92])
    with review_columns[0]:
        render_draft_panel(draft_result, draft_result.draft_text, False)
        _render_draft_actions(draft_result, provider)
    with review_columns[1]:
        render_warning_panel(draft_result.warnings)
        render_transparency_panel(draft_result.analysis)


def _render_draft_actions(draft_result: DraftResult, provider) -> None:
    action_columns = st.columns(3)
    with action_columns[0]:
        if st.button("Edit draft", use_container_width=True):
            st.session_state.editing = True
            st.rerun()
    with action_columns[1]:
        if st.button("Regenerate", use_container_width=True):
            email_context = _current_email_context()
            if email_context is None:
                st.error("Regeneration failed: the current email context is unavailable. Generate again.")
                return
            with st.spinner("Regenerating and repeating all review checks…"):
                st.session_state.draft_result = create_draft_result(email_context, provider)
            st.session_state.editing = False
            st.rerun()


def _current_email_context() -> EmailContext | None:
    try:
        return create_email_context(
            original_email=st.session_state.original_email,
            tone=Tone(st.session_state.tone),
            instruction=st.session_state.instruction,
        )
    except ValueError:
        return None


if __name__ == "__main__":
    main()