from openai import OpenAI

from functions import *

import os
import time
import json
import venv
import subprocess

from typing_extensions import override
from openai import AssistantEventHandler

# For Debugging reasons
DEBUG = True

# Tools
tools = [
    {
        "type": "code_interpreter",
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": """Copy a file from any location to another directory.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": """The file name. This should contain the full path of the file.""",
                    },
                    "directory": {
                        "type": "string",
                        "description": "The directory to copy the file into.",
                    },
                },
                "required": ["file_name", "directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": """Create and write a file for the user in the language specified as an argument.
            The extension of the file name must match the language that you are writing in.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": """The language of the file. This could be any one of, but not limited to,
                        Python, CSS, Javascript, C++, or text.""",
                    },
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
                "required": ["language", "file_name", "file_contents"],
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
                        "description": """The full path of the Python file to be run.""",
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
            "name": "open_png_file",
            "description": """Opens a png file.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": """The full path of the png file to be opened.""",
                    },
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_project_directory",
            "description": """Create a project directory for a web application. The directory should always start with
            'auto/' and end with a suffix that briefly describes the coding project in CamelCase.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": """The directory in which the code development will take place. Please preface
                        this directory with 'auto/' and end with a suffix that briefly describes the coding project in
                        CamelCase.""",
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "initialize_react_app",
            "description": """Initializes a vanilla React app with Chakra UI for frontend components in the project
            directory specified.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": """The directory in which the code development will take place.""",
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deploy_app_to_netlify",
            "description": """Deploys the React app to netlify. On a successful function call, please display the
            Website URL for the user to access the application online.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": """The project directory. This should never have '/my-app' as a suffix.""",
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "redeploy_app_to_netlify",
            "description": """Re-deploy the React app to netlify. Only call if the web app has already been deployed
            to netlify on a previous call. On a successful function call, please display the website URL for the user
            to access the web app online.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": """The project directory. This should never have '/my-app' as a suffix.""",
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_virtual_env",
            "description": """Create a Python virtual environment for future code development.
            Please include contents for any requirements file that will be installed using pip.""",
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
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": """Make a google search.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": """The query to search.""",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_website",
            "description": """Search a website to get relevant information.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": """The URL of the website to search.""",
                    },
                },
                "required": ["url"],
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
    ### The very default assistant
    "default": {
        "system_prompt": "You are a helpful assistant.",
        "description": "The default assistant.",
    },
    ### The main assistant
    "planner": {
        "system_prompt": """You are a high level planner. You will be given a task, or updates about the
        progress on tasks, and be expected to plan or replan. First output a list of single bullet points,
        each of which look something like 'Set up the project directory and initialize the web app with React'.
        Always use React for front-end and Netlify for deployment. Make similar types of design and
        implementation decisions yourself. You are very resourceful and you can proceed with the user's requests
        without additional prompting from the user unless you are stuck.
        
        After laying out your project plan, begin by initializing a project directory and building a relevant
        Python virtual environment that contains all the necessary modules that you might need to tackle the project.
        For miscellaneous Python scripts, always include a '__main__' clause at the end in case the user wants
        to call the script from the command line. If the user wants to run the program, be sure to create the
        virtual environment first. If you get an error after running a script, give the user a brief description of
        what the error was and try to fix the error.
                
        For any web app coding project you are given, proceed by creating a vanilla React app with Chakra UI
        for frontend components in the project. Create and write the necessary Python, Javascript, and CSS files
        needed for the web application. For now, write everything in the frontend code. Development should always
        happen in the 'my-app' subdirectory of your project directory. For example, you should be writing the main
        frontend code in the 'my-app/src/' directory, though feel free to create other files as needed. Proceed down
        the action items in your bullet point list as much as you can, which includes writing code for the project.
        
        Always assume the user wants you to proceed with any code development without asking for additional affirmation.
        Avoid using deprecated functions in code development. When you are finished coding, deploy the app to Netlify
        and give the user a link to the website. Ask if the user has any additional requests regarding the coding
        project. If the user has a request, make the relevant changes and re-deploy the website to Netlify. Re-link
        the user to the website. On errors, give the user a brief description of what the error was and try to fix
        the error yourself.
        
        If there is a question you can't answer, start by making a Google search. If that's not sufficient, read the
        url_links from the Google search and search relevant websites for useful information without additional
        prompting from the user.""",
        "description": "The high-level planner of a project",
    },
    ### Placeholder code for additional assistants to manage particular subtasks ###
    "driver": {
        "system_prompt": """You are an engineering manager, who takes a single task, and turns it into
        bite-sized tasks that an engineer can perform with no ambiguity.""",
        "description": "The engineering manager",
    },
    ### Maybe we can have an assistant dynamically write system prompts for other assistants
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
    if DEBUG:
        print(
            "Debug mode is currently on. To turn it off, toggle the DEBUG boolean at the top of assistant.py"
        )
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
