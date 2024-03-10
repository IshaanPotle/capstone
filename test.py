import cohere
from cohere.responses.chat import StreamEvent

co = cohere.Client('WrwwKEMSMjFySzaPxE9NmECZ6gjs4cINUtioGtNF')

for event in co.chat("What is an LLM?", stream=True):
    if event.event_type == StreamEvent.TEXT_GENERATION:
      print(event.text)
    elif event.event_type == StreamEvent.STREAM_END:
      print(event.finish_reason)