# Responses API context compaction demo

A single Python script showing this lifecycle:

```text
Initial facts -> four conversation turns -> growing context
    -> explicit compaction -> follow-up request -> early facts recalled
```

A run makes five Responses requests and one compaction request; normal API charges apply.

## Run locally

```bash
python -m pip install --upgrade -r requirements.txt
cp .env.example .env
python demo.py
```

## What to observe

The first turn introduces **Mira**, **Lantern**, and **Kowhai Hall**. Three more
turns develop the event plan. The script prints each reply, accumulated item
count, and request input-token usage so you can watch context grow.

It then calls `client.responses.compact(...)` explicitly, prints the returned
item types, and replaces the history with the complete `compacted.output`.
The final question asks for the original facts without supplying their values.
Look for those facts in the answer and this local check:

```text
Recall check PASSED: all three early facts appear in the answer.
```

This is an expected outcome, not a recorded API result. The check is a simple
case-insensitive text match, not a semantic evaluation. Missing text or an
incomplete response exits with an error, rather than claiming success.

## How it works

The script manages conversation state explicitly in a list. Each turn appends
the user message and **all** response output items. `store=False` is used;
encrypted reasoning content is requested so reasoning items can be carried
forward. There is no `previous_response_id` or server-managed conversation.

The key transition is:

```python
compacted = client.responses.compact(model=model, input=history)
history = list(compacted.output)
history.append({"role": "user", "content": question})
response = client.responses.create(model=model, input=history, store=False)
```

Compaction produces an opaque encrypted item and may retain other messages.
Keep the entire returned window intact. The recall demonstrates that facts
remain usable through that window; it does not prove each fact was encoded
in the encrypted item. The script resends its brief instructions each time.

This deliberately short example exercises the lifecycle without filling a
large context window or enabling automatic compaction. Item counts and encrypted
payload lengths do not measure token savings. A tiny conversation may not get
smaller, and compaction is not a guarantee of perfect recall.

## Official documentation

- [Compaction guide](https://developers.openai.com/api/docs/guides/compaction)
- [Python compact endpoint reference](https://developers.openai.com/api/reference/python/resources/responses/methods/compact)
- [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
