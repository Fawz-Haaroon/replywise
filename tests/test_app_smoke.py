from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_offline_app_generates_review_surface_with_disclosure(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "offline")
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=10).run()

    assert not app.exception
    app.text_area[0].set_value(
        "Hi team,\n\nPlease send the report to me. My SSN is 123-45-6789."
    ).run()
    app.button[0].click().run()

    assert not app.exception
    rendered_markdown = "\n".join(element.value for element in app.markdown)
    assert "AI-assisted draft" in rendered_markdown
    assert "ReplyWise never sends mail." in rendered_markdown
    assert "does not guarantee correctness, privacy, or fairness" in rendered_markdown
    assert "Responsible AI review" in rendered_markdown


def test_edit_requires_explicit_save_and_rechecks_the_saved_draft(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "offline")
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=10).run()
    app.button[0].click().run()
    app.button[1].click().run()

    assert [button.label for button in app.button] == ["Generate draft", "Save & review", "Discard changes"]
    app.text_area[1].set_value("Please review this. SSN 123-45-6789.").run()
    assert app.session_state.draft_result.draft_text != "Please review this. SSN 123-45-6789."

    app.button[1].click().run()

    assert app.session_state.editing is False
    assert app.session_state.draft_result.draft_text == "Please review this. SSN 123-45-6789."
    rendered_markdown = "\n".join(element.value for element in app.markdown)
    assert "Sensitive information" in rendered_markdown