from app.ai_helpers import extract_action_items, summarize_note


def test_summarize_note_returns_message_for_text():
    summary = summarize_note("Finish the proposal and review the Git workflow.")

    assert "Mock summary" in summary


def test_summarize_note_handles_empty_text():
    summary = summarize_note("   ")

    assert summary == "No note text was provided."


def test_extract_action_items_returns_list_for_text():
    items = extract_action_items("We need to finish the slides and test the backend.")

    assert isinstance(items, list)
    assert items[0]["title"]
    assert items[0]["priority"] == "medium"


def test_extract_action_items_handles_empty_text():
    items = extract_action_items("")

    assert items == []

