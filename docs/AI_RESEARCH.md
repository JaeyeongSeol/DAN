# AI Research

Owner: Mateus

For the AI part of DAN, the best starting point is Ollama with a local Gemma model.

## Recommendation

Use Ollama first, then run Gemma through Ollama.

Best model to start with:

```bash
ollama run gemma3:1b
```

If the laptops can handle it, we can try:

```bash
ollama run gemma3:4b
```

I think `gemma3:1b` is the better MVP choice because it should be easier for more people to run. The goal is not to have the smartest model possible. The goal is to have a working local AI feature that is reliable enough for our demo.

## Why Ollama

- It is easier than setting up a full Hugging Face pipeline.
- It runs locally, so we are not just calling an API.
- FastAPI can call Ollama through a local HTTP request.
- It is simple to swap models later if we need to.

## AI features for MVP

The AI part should stay focused on two features:

1. Summarize a note.
2. Extract action items from a note.

The app should not automatically create tasks from AI output. It should show the suggested tasks first, then the user chooses what to save.

## Expected helper functions

```python
summarize_note(text: str) -> str
extract_action_items(text: str) -> list[dict]
```

For action items, the output should be simple enough for the backend and frontend to use:

```python
[
    {
        "title": "Finish database schema",
        "due_date": "unknown",
        "priority": "medium"
    }
]
```

## Fallback plan

If Ollama or Gemma causes problems during setup, we should use mock AI functions for the demo.

That still lets us show the full app flow:

note -> AI suggestion -> user confirms -> task gets saved

The real local model can be connected after the rest of the app is stable.

## Next step

Install Ollama on one laptop and test:

```bash
ollama run gemma3:1b
```

Then test a short note and see if it can return a summary and action items in a clean format.

