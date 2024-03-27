from openai import OpenAI

import os
import time
import json
import venv
import subprocess

from typing_extensions import override
from openai import AssistantEventHandler

# For Debugging reasons
DEBUG = True


# Functions
def write_file(file_name, file_contents):
    # Write the script to file_name
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    f = open(file_name, "w")
    f.write(file_contents)
    f.close()
    print(f"Wrote contents to {file_name} successfully!")
    return json.dumps({"file_name": file_name})


def write_python_file(args):
    # Decode arguments
    file_name = args.get("file_name")
    file_contents = args.get("file_contents")
    return write_file(file_name, file_contents)


def write_javascript_file(args):
    # Decode arguments
    file_name = args.get("file_name")
    file_contents = args.get("file_contents")
    return write_file(file_name, file_contents)


def run_python_script(args):
    # Decode arguments
    file_name = args.get("file_name")
    directory = args.get("directory")
    arguments = args.get("arguments", [])
    # Run the python script
    output = subprocess.run([f"{directory}/venv/bin/python", file_name] + arguments)
    return json.dumps({"output": output})


def create_virtual_env(args):
    # Decode arguments
    directory = args.get("directory")
    requirements_content = args.get("requirements_content")
    # Create the directory
    if not os.path.isdir(directory):
        subprocess.run(["mkdir", directory])
    # Write the requirements
    f = open(f"{directory}/requirements.txt", "w")
    f.write(requirements_content)
    f.close()
    # Create the environment and install relevant requirements
    venv_location = os.path.join(directory, "venv")
    venv.create(venv_location, with_pip=True)
    subprocess.run(
        [f"{directory}/venv/bin/pip", "install", "-r", f"{directory}/requirements.txt"]
    )
    return json.dumps({"directory": directory})


# All available functions
available_functions = {
    # For writing
    "write_python_file": write_python_file,
    "write_javascript_file": write_javascript_file,
    # For running
    "run_python_script": run_python_script,
    # Virtual environments
    "create_virtual_env": create_virtual_env,
}

# Tools
tools = [
    {
        "type": "code_interpreter",
    },
    {
        "type": "function",
        "function": {
            "name": "write_python_file",
            "description": """Create and write a Python file for the user. Only use for Python files.
            Do not use for any other language.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": """The file name. This should be prefaced by the same directory
                        that the rest of the project is being built in. If there is no current project
                        being worked on, then default to beginning the file name with 'auto/'.""",
                    },
                    "file_contents": {
                        "type": "string",
                        "description": "The contents of the Python file.",
                    },
                },
                "required": ["file_name", "file_contents"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_javascript_file",
            "description": """Create and write a Javascript file for the user. Only use for Javascript files.
            Do not use for any other language such as bash scripts.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": """The file name. This should be prefaced by the same directory
                        that the rest of the project is being built in. If there is no current project
                        being worked on, then default to beginning the file name with 'auto/'.""",
                    },
                    "file_contents": {
                        "type": "string",
                        "description": "The contents of the Javascript file.",
                    },
                },
                "required": ["file_name", "file_contents"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_script",
            "description": """Runs a Python script using the virtual environment directory supplied.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": """The Python file to be run.""",
                    },
                    "directory": {
                        "type": "string",
                        "description": """The directory that you can find the virtual environment in.""",
                    },
                    "arguments": {
                        "type": "array",
                        "description": """A list of arguments to pass into the Python script.""",
                        "items": {
                            "type": "string",
                        },
                    },
                },
                "required": ["file_name", "directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_virtual_env",
            "description": """Create a Python virtual environment for future code development.
            Please include contents for any requirements file that will be installed using pip.
            Only create one virtual environment per user input, which can store all the necessary
            requirements. Make sure the virtual environment is created before any additional work
            is done on any code project.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": """The directory in which the code development will take place. Please preface
                        this directory with 'auto/' and end with a suffix that briefly describes the coding project.""",
                    },
                    "requirements_content": {
                        "type": "string",
                        "description": """The contents of the requirements.txt file that will be called
                        during a pip install command.""",
                    },
                },
                "required": ["directory", "requirements_content"],
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
            if DEBUG:
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
        # Get run and thread information
        current_run = self.current_run
        run_id, thread_id = current_run.id, current_run.thread_id
        if DEBUG:
            print(f"\nrun_id: {run_id}")
            print(f"thread_id: {thread_id}")
            print(f"tool_call: {tool_call}")
            print(f"run_status: {current_run.status}")
        if current_run.status == "requires_action":
            tool_outputs = []
            if DEBUG:
                print(
                    f"Tool calls: {current_run.required_action.submit_tool_outputs.tool_calls}"
                )
            for tool_call in current_run.required_action.submit_tool_outputs.tool_calls:
                if tool_call.type == "function":
                    function_name = tool_call.function.name
                    function_to_call = available_functions[function_name]
                    function_arguments = json.loads(tool_call.function.arguments)
                    function_response = function_to_call(function_arguments)
                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(function_response),
                        }
                    )
            if current_run.required_action.type == "submit_tool_outputs":
                with client.beta.threads.runs.submit_tool_outputs_stream(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs,
                    event_handler=EventHandler(),
                ) as stream:
                    stream.until_done()
        else:
            pass


# Assistants
MY_ASSISTANTS = {
    "default": {
        "system_prompt": "You are a helpful assistant.",
        "description": "The default assistant.",
    },
    "planner": {
        "system_prompt": """You are a high level planner for a group of other GPTs that code.
        You will be given a task, or updates about the progress on tasks, and be expected to
        plan or replan. Output a list of single bullet points, each of which look something like
        'Set up the project directory and initialize the web app with React' or 'Write the backend'.
        Always use React for front-end, AWS for cloud, Flask for back-end, and Netlify for deployment.
        Make similar types of design and implementation decisions yourself.
        
        If possible, give a clear directory structure of any code project that you are given.
        
        If prompted to create a virtual environment, build the environment in the parent directory
        of the suggested project directory structure. Do not build more than one virtual environment.
        Create the virtual environment before writing any code.
        
        Always assume that the user wants you to proceed with any code development without asking for
        additional affirmation.""",
        "description": "The high-level planner of a project",
    },
    "driver": {
        "system_prompt": """You are an engineering manager, who takes a single task, and turns it into
        bite-sized tasks that an engineer can perform with no ambiguity.""",
        "description": "The engineering manager",
    },
    "prompter": {
        "system_prompt": """You are an expert at system prompting AI Assistants. Your goal is to take a
        task from the user, and return a system prompt for another AI Assistant that would make it
        as helpful as possible for the user. For example, if the user task is 'Detect and fix bugs
        in Python code', you can respond with something like 'Your task is to analyze the provided
        Python code snippet, identify any bugs or errors present, and provide a corrected version of
        the code that resolves these issues. The corrected code should be functional, efficient, and
        adhere to best practices in Python programming'. Your system prompt should be no more than
        three sentences long.""",
        "description": "The assistant prompter",
    },
    "venv_builder": {
        "system_prompt": """You are an expert software engineer. Your task is to follow instructions from
        the user to build one virtual environment and install all the necessary package dependencies
        required. Do not build more than one virtual environment.""",
        "description": "The virtual environment builder",
    },
}

# Initialize client
client = OpenAI()

assistant = client.beta.assistants.create(
    instructions=MY_ASSISTANTS["planner"]["system_prompt"],
    tools=tools,
    model="gpt-4-turbo-preview",
)

thread = client.beta.threads.create()

# Loop on user input
iteration = 0
while True:
    # Formatting reasons
    x = input("\nUser > " if iteration == 0 else "\n\nUser > ")

    # Allow user to exit
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

    # Increase counter
    iteration += 1
