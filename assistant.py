from openai import OpenAI

from typing_extensions import override
from openai import AssistantEventHandler


# First create an EventHandler class to define how we want to handle the events in the response stream
class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nAssistant > ", end="\n", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call):
        print(f"\nAssistant > {tool_call.type}\n", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\nOutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)


MY_ASSISTANTS = {
    "default": "You are a helpful assistant.",
    "planner": """You are a high level planner for a group of other GPTs that code.
    You will be given a task, or updates about the progress on tasks, and be expected to
    plan or replan, outputting a list of single bullet points, each of which look something like
    'Write the code for a starting app' or 'Write the backend'. Always use React for front-end,
    AWS for cloud, and Flask for back-end. Make similar types of design and implementation
    decisions yourself.""",
    "driver": """You are an engineering manager, who takes a single task, and turns it into
    bite-sized tasks that an engineer can perform with no ambiguity.""",
    "prompter": """You are an expert at system prompting AI Assistants. Your goal is to take a
    task from the user, and return a system prompt for another AI Assistant that would make it
    as helpful as possible for the user. For example, if the user task is 'Detect and fix bugs
    in Python code', you can respond with something like 'Your task is to analyze the provided
    Python code snippet, identify any bugs or errors present, and provide a corrected version of
    the code that resolves these issues. The corrected code should be functional, efficient, and
    adhere to best practices in Python programming'. Your system prompt should be no more than
    three sentences long.""",
}

assistant_type = input(
    "> Select the assistant you would like to use: "
    + ", ".join(MY_ASSISTANTS.keys())
    + "\n> "
)

client = OpenAI()
assistant = client.beta.assistants.create(
    instructions=MY_ASSISTANTS[assistant_type],
    # tools=[{"type": "code_interpreter"}],
    model="gpt-4-turbo-preview",
)

thread = client.beta.threads.create()

while True:
    x = input("> ")
    client.beta.threads.messages.create(
        thread.id,
        role="user",
        content=x,
    )
    with client.beta.threads.runs.create_and_stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

    thread_messages = client.beta.threads.messages.list(thread.id)
    print("\n")
