from openai import OpenAI

# from functions import *

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
]

# Assistants
MY_ASSISTANTS = {
    "default": {
        "system_prompt": """You are a high level planner for a group of other GPTs that code.
        You will be given a task, or updates about the progress on tasks, and be expected to
        plan or replan. First output a list of single bullet points, each of which look something like
        'Set up the project directory and initialize the web app with React'. Always use React for front-end
        and Netlify for deployment. Make similar types of design and implementation decisions yourself. Always
        assume the user wants you to proceed with implementation.""",
        # After laying out your project plan, begin by initializing a project directory and building a relevant
        # Python virtual environment that contains all the necessary modules that you might need to tackle the project.
        # For miscellaneous Python scripts, always include a '__main__' clause at the end in case the user wants
        # to call the script from the command line. If the user wants to run the program, be sure to create the
        # virtual environment first.
        # For any web app coding project you are given, proceed by creating a vanilla React app with Chakra UI
        # for frontend components in the project. Create and write the necessary Python and Javascript files
        # needed for the web application. Code development should always happen in the 'my-app'
        # subdirectory of your project directory. For example, you should be writing the main frontend code in
        # 'my-app/src/App.js', though feel free to create other files as needed. Proceed down the action items
        # in your bullet point list as much as you can, which includes writing code for the project.
        # Always assume the user wants you to proceed with any code development without asking for additional affirmation.
        # Avoid using deprecated functions in code development.
        # When you are finished coding, deploy the app to Netlify and give the user a link to the website.
        # Ask if the user has any additional requests regarding the coding project. If the user has a request, make
        # the relevant changes and re-deploy the website to Netlify. Re-link the user to the website.
    },
    "software_engineer": {
        "system_prompt": """You are an expert software engineer with experience in a variety of engineering tasks
        ranging from writing simple scripts to developing entire web applications. Your task is to follow the provided
        directions and write code that is concise, functional, and efficient. Your code should adhere to the best
        practices of programming in a variety of different coding languages. Always start by initializing a project
        directory and building a Python virtual environment that contains all the necessary modules that you might
        need to tackle the project. For miscellaneous Python scripts, include a '__main__' clause at the end so that
        the program is runnable from the command line.
        
        For any web application project you are given, proceed by creating a vanilla React app with Chakra UI for
        frontend components in the project directory. Complete all the action items in the provided instructions.
        Always assume the user wants you to proceed with any code development without asking for additional affirmation.
        Avoid using deprecated functions. When you are finished coding, deploy the app to Netlify and give the user a
        link to the website. Ask if the user has any additional requests regarding the coding project. If the user has
        a request, make the relevant changes and re-deploy the website to Netlify.
        """,
    },
}

# Tools to call
tools_v2 = {
    "default": [
        {
            "type": "function",
            "function": {
                "name": "invoke_software_engineer",
                "description": """Build the project by developing software.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instructions": {
                            "type": "string",
                            "description": """The step-by-step instructions for the coding project.""",
                        },
                    },
                    "required": ["instructions"],
                },
            },
        },
    ],
    "software_engineer": [
        {
            "type": "code_interpreter",
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
                "name": "create_and_write_file",
                "description": """Create a file and write code for the user.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_name": {
                            "type": "string",
                            "description": """The full path for the file.""",
                        },
                        "file_contents": {
                            "type": "string",
                            "description": "The contents of the file.",
                        },
                    },
                    "required": ["file_name", "file_contents"],
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
    ],
}

# Initialize client and assistants
client = OpenAI()

assistants = {
    asst_type: client.beta.assistants.create(
        instructions=MY_ASSISTANTS[asst_type]["system_prompt"],
        tools=tools_v2[asst_type],
        model="gpt-4-turbo-preview",
    )
    for asst_type in MY_ASSISTANTS
}


# Functions
def invoke_software_engineer(args):
    # Decode arguments
    instructions = args.get("instructions")
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread.id,
        role="user",
        content=instructions,
    )
    # Invoking software engineer
    print("########### Invoking software engineer ###########")
    with client.beta.threads.runs.create_and_stream(
        thread_id=thread.id,
        assistant_id=assistants["software_engineer"].id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()
    print("\n########### Complete software engineer ###########")
    thread_messages = client.beta.threads.messages.list(thread.id)
    return json.dumps({})


def create_project_directory(args):
    # Creates a project directory
    directory = args.get("directory")
    if not os.path.isdir(directory):
        subprocess.run(["mkdir", directory])
    return json.dumps({"directory": directory})


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


def initialize_react_app(args):
    # Creates a project directory
    directory = args.get("directory")
    if not os.path.isdir(directory):
        subprocess.run(["mkdir", directory])
    # Initialize React app with Chakra UI and netlify
    subprocess.run(["npx", "create-react-app", "my-app"], cwd=directory)
    subprocess.run(["npm", "install", "@chakra-ui/react"], cwd=f"{directory}/my-app")
    subprocess.run(["npm", "install", "netlify-cli"], cwd=f"{directory}/my-app")
    return json.dumps({"directory": directory})


def create_and_write_file(args):
    # Decode arguments
    file_name = args.get("file_name")
    file_contents = args.get("file_contents")
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    f = open(file_name, "w")
    f.write(file_contents)
    f.close()
    print(f"Wrote contents to {file_name} successfully!")
    return json.dumps({"file_name": file_name})


def deploy_app_to_netlify(args):
    # Decode arguments
    directory = args.get("directory")
    # Build the React app
    p = subprocess.Popen(["npm", "run", "build"], cwd=f"{directory}/my-app")
    p.wait()
    # Deploy to netlify
    p = subprocess.Popen(
        ["netlify", "deploy", "--dir", "./build", "--prod"],
        cwd=f"{directory}/my-app",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    # Wait for the prompt to come up
    time.sleep(2)

    # Helper function for interacting with the terminal
    def send_input(process, bytes):
        process.stdin.write(bytes)
        process.stdin.flush()
        time.sleep(1)

    # What would you like to do? [Create & configure a new site]
    send_input(p, b"\x1b[B\n")

    # Team [DevinTC]
    send_input(p, b"\n")

    # Site name (leave blank for a random name; you can change it later) []
    send_input(p, b"\n")

    output, error = p.communicate()
    return json.dumps({"output": str(output)})


available_functions = {
    "invoke_software_engineer": invoke_software_engineer,
    "create_project_directory": create_project_directory,
    "create_virtual_env": create_virtual_env,
    "initialize_react_app": initialize_react_app,
    "create_and_write_file": create_and_write_file,
    "deploy_app_to_netlify": deploy_app_to_netlify,
}


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


# Initialize the main thread
thread = client.beta.threads.create()

# Loop on user input
iteration = 0
while True:
    # Formatting reasons
    user_input = input("\nUser > " if iteration == 0 else "\n\nUser > ")

    # Allow user to exit
    if user_input.lower() == "exit":
        break

    # Create a message
    message = client.beta.threads.messages.create(
        thread.id,
        role="user",
        content=user_input,
    )

    # Run assistant
    with client.beta.threads.runs.create_and_stream(
        thread_id=thread.id,
        assistant_id=assistants["default"].id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

    # Increase counter
    iteration += 1
