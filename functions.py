import os
import time
import venv
import json
import subprocess


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
    output = subprocess.run(
        [f"{directory}/venv/bin/python", file_name] + arguments, capture_output=True
    ).stdout
    print(f"Output: {output}")
    return json.dumps({"output": str(output)})


def create_project_directory(args):
    # Creates a project directory
    directory = args.get("directory")
    if not os.path.isdir(directory):
        subprocess.run(["mkdir", directory])
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
    # Create project directory
    "create_project_directory": create_project_directory,
    "initialize_react_app": initialize_react_app,
    "deploy_app_to_netlify": deploy_app_to_netlify,
}
