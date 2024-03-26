from openai import OpenAI

import time
import json
from typing_extensions import override
from openai import AssistantEventHandler


# Functions
def write_python_script(args):
    # Decode arguments
    file_name = args.get("file_name", "blank.txt")
    script = args.get("script", "")
    # Write the script to file_name under the 'auto' directory
    f = open(f"auto/{file_name}.txt", "w")
    f.write(script)
    f.close()
    print(f"Wrote script to auto/{file_name} successfully!")
    return json.dumps({})


# All available functions
available_functions = {
    "write_python_script": write_python_script,
}

# Tools
tools = [
    {
        "type": "code_interpreter",
    },
    {
        "type": "function",
        "function": {
            "name": "write_python_script",
            # I had to enforce it to only write Python because it tried writing web applications to files called ui_design.py
            "description": "Create and write a Python script for the user. Only use for Python scripts. Do not use for any other language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The file name of the script",
                    },
                    "script": {
                        "type": "string",
                        "description": "The contents of the Python script",
                    },
                },
                "required": ["file_name", "script"],
            },
        },
    },
]


# First create an EventHandler class to define how we want to handle the events in the response stream
class EventHandler(AssistantEventHandler):

    @override
    def on_text_created(self, text) -> None:
        print(f"\nAssistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call):
        print(f"\nAssistant > {tool_call.type}\n", flush=True)
        if tool_call.type == "function":
            print(f"Building function call args for {tool_call.function.name}")

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "function":
            # print(delta)
            string = delta.function.arguments
            print(string, end="", flush=True)
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\nOutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

    def on_tool_call_done(self, tool_call) -> None:
        # For debugging
        current_run = self.current_run
        run_id, thread_id = current_run.id, current_run.thread_id
        print(f"\nrun_id: {run_id}")
        print(f"thread_id: {thread_id}")
        print(f"tool_call: {tool_call}")
        if tool_call.type == "function":
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_arguments = json.loads(tool_call.function.arguments)
            function_response = function_to_call(function_arguments)
            tool_output = {"tool_call_id": tool_call.id, "output": "Finished!"}
            if current_run.status == "requires_action":
                with client.beta.threads.runs.submit_tool_outputs_stream(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=[tool_output],
                    event_handler=EventHandler(),
                ) as stream:
                    stream.until_done()
            else:
                pass
        else:
            pass


# Assistants
MY_ASSISTANTS = {
    "default": "You are a helpful assistant.",
    "planner": """You are a high level planner for a group of other GPTs that code.
    You will be given a task, or updates about the progress on tasks, and be expected to
    plan or replan, outputting a list of single bullet points, each of which look something like
    'Write the code for a starting app' or 'Write the backend'. Always use React for front-end, AWS for cloud,
    and Flask for back-end. Make similar types of design and implementation decisions yourself.""",
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

# Initialize client
client = OpenAI()

assistant_type = input(
    "> Select the assistant you would like to use: "
    + ", ".join(MY_ASSISTANTS.keys())
    + "\n> "
)

assistant = client.beta.assistants.create(
    instructions=MY_ASSISTANTS[assistant_type],
    tools=tools,
    model="gpt-4-turbo-preview",
)

thread = client.beta.threads.create()

# Loop on user input
while True:
    x = input("\n\nUser > ")
    if x.lower() == "exit":
        break

    # Create a message
    message = client.beta.threads.messages.create(
        thread.id,
        role="user",
        content=x,
    )

    # Run assistant
    with client.beta.threads.runs.create_and_stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

    # messages = client.beta.threads.messages.list(thread_id=thread.id)
    # print(messages)
