"""A small, explicit Responses API compaction walkthrough (Python 3.12+)."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


INSTRUCTIONS = "You help plan a community event. Keep replies under 100 words."
TURNS = [
    "Remember these event facts: the organizer is Mira, the project is called "
    "Lantern, and the venue is Kowhai Hall. Briefly acknowledge them.",
    "Suggest three activities for our community event.",
    "Suggest a simple afternoon schedule using those activities.",
    "Suggest a short volunteer checklist for setting up and cleaning up.",
]


def main():
    if sys.version_info < (3, 12):
        raise SystemExit("Please run this demo with Python 3.12 or newer.")
    load_dotenv(Path(__file__).with_name(".env"))
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your environment or local .env file.")

    client = OpenAI()  # Reads OPENAI_API_KEY from the environment.
    model = os.environ.get("OPENAI_MODEL", "gpt-6-astra")
    history = []
    print(f"Model: {model}", flush=True)

    # Keep every output item, including any reasoning items, across turns.
    for number, message in enumerate(TURNS, start=1):
        print(f"\n--- Turn {number}: {'initial context' if number == 1 else 'context grows'} ---")
        print(f"User: {message}", flush=True)
        history.append({"role": "user", "content": message})
        response = client.responses.create(
            model=model,
            instructions=INSTRUCTIONS,
            input=history,
            store=False,
            include=["reasoning.encrypted_content"],
        )
        if response.status != "completed":
            raise SystemExit(f"Turn did not complete: {response.status}")
        history.extend(response.output)
        print(f"Assistant: {response.output_text}")
        print(f"Context now contains {len(history)} items.")
        if response.usage:
            print(f"This request used {response.usage.input_tokens} input tokens.")

    print("\n--- Explicit compaction: POST /responses/compact ---", flush=True)
    before = len(history)
    compacted = client.responses.compact(
        model=model,
        instructions=INSTRUCTIONS,
        input=history,
    )

    # REPLACE the old history. Do not filter or decode the returned window.
    history = list(compacted.output)
    print(f"Context items: {before} before -> {len(history)} after")
    print("Returned item types:", [item.type for item in history])
    print("Item counts are not token counts; small examples may not shrink.")
    if not any(item.type == "compaction" for item in history):
        raise SystemExit("No compaction item returned; cannot demonstrate compaction.")

    # The question contains none of the answers. Only the returned window
    # supplies earlier conversation state; no previous_response_id is used.
    question = (
        "What were the organizer's name, project name, and venue from the start "
        "of our conversation? Use their exact original spellings."
    )
    print("\n--- Recall using the compacted context ---")
    print(f"User: {question}", flush=True)
    history.append({"role": "user", "content": question})
    response = client.responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=history,
        store=False,
    )
    if response.status != "completed":
        raise SystemExit(f"Recall did not complete: {response.status}")
    print(f"Assistant: {response.output_text}")

    # These expected values are local checks, never added to the recall request.
    missing = [
        fact for fact in ("Mira", "Lantern", "Kowhai Hall")
        if fact.casefold() not in response.output_text.casefold()
    ]
    if missing:
        raise SystemExit(f"Recall check FAILED. Missing exact text: {missing}")
    print("Recall check PASSED: all three early facts appear in the answer.")


if __name__ == "__main__":
    main()
