import anthropic
client = anthropic.Anthropic()
msg = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=10,
    messages=[{"role": "user", "content": "hi"}]
)
print(msg.content)