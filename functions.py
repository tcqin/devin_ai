import os
import time
import venv
import json
import subprocess
from bs4 import BeautifulSoup
from requests import get
from selenium import webdriver


def copy_file(args):
    # Decode arguments
    file_name = args.get("file_name")
    directory = args.get("directory")
    if not os.path.isdir(directory):
        subprocess.run(["mkdir", directory])
    subprocess.run(["cp", file_name, directory])
    status_message = f"Successfully copied {file_name} to {directory}"
    print(status_message)
    return json.dumps({"status": status_message})
    return write_file(file_name, file_contents)


def write_file(args):
    # Decode arguments
    file_name = args.get("file_name")
    file_contents = args.get("file_contents")
    # Write the script to file_name
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    f = open(file_name, "w")
    f.write(file_contents)
    f.close()
    status_message = f"Wrote contents to {file_name} successfully!"
    print(status_message)
    return json.dumps({"status": status_message})


def run_python_script(args):
    # Decode arguments
    file_name = args.get("file_name")
    directory = args.get("directory")
    arguments = args.get("arguments", [])
    # Run the python script
    p = subprocess.Popen(
        [f"{directory}/venv/bin/python", file_name] + arguments,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = p.communicate()
    return json.dumps({"output": str(output), "error": str(error)})


def open_png_file(args):
    # Decode arguments
    file_name = args.get("file_name")
    # Run the python script
    p = subprocess.Popen(
        ["open", file_name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = p.communicate()
    return json.dumps({"output": str(output), "error": str(error)})


def create_project_directory(args):
    # Creates a project directory
    directory = args.get("directory")
    if not os.path.isdir(directory):
        subprocess.run(["mkdir", directory])
    status_message = f"Successfully created {directory}"
    print(status_message)
    return json.dumps({"status": status_message})


def initialize_react_app(args):
    # Creates a project directory
    directory = args.get("directory")
    if not os.path.isdir(directory):
        subprocess.run(["mkdir", directory])
    # Initialize React app with Chakra UI and netlify
    subprocess.run(["npx", "create-react-app", "my-app"], cwd=directory)
    subprocess.run(["npm", "install", "@chakra-ui/react"], cwd=f"{directory}/my-app")
    subprocess.run(["npm", "install", "netlify-cli"], cwd=f"{directory}/my-app")
    status_message = f"Successfully initialized React app in {directory}"
    print(status_message)
    return json.dumps({"status": status_message})


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
        stderr=subprocess.PIPE,
    )

    # Wait for the prompt to come up
    time.sleep(5)

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
    return json.dumps({"output": str(output), "error": str(error)})


def redeploy_app_to_netlify(args):
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
        stderr=subprocess.PIPE,
    )
    output, error = p.communicate()
    return json.dumps({"output": str(output), "error": str(error)})


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
    p = subprocess.Popen(
        [f"{directory}/venv/bin/pip", "install", "-r", f"{directory}/requirements.txt"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = p.communicate()
    print(f"Successfully created a virtual environment in {directory}")
    return json.dumps({"output": str(output), "error": str(error)})


################### HELPER FUNCTIONS FOR WEBSITES ###################
def remove_tags(html):
    soup = BeautifulSoup(html, "html.parser")
    for data in soup(["style", "script"]):
        data.decompose()
    return " ".join(soup.stripped_strings)


def search_google(args):
    # Decode arguments
    query = args.get("query")
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    browser = webdriver.Chrome()
    browser.get(url)
    # Get raw text from the page
    extracted_data = remove_tags(browser.page_source)
    # Get links on the page
    link_elements = browser.find_elements("xpath", "//a[@href]")
    links = [link.get_attribute("href") for link in link_elements]
    return json.dumps({"text_on_page": extracted_data, "url_links": links})


def search_website(args):
    # Decode arguments
    url = args.get("url")
    browser = webdriver.Chrome()
    browser.get(url)
    # Get raw text from the page
    extracted_data = remove_tags(browser.page_source)
    return json.dumps({"text_on_page": extracted_data})


# All available functions
available_functions = {
    # For working with files
    "copy_file": copy_file,
    "write_file": write_file,
    # For running
    "run_python_script": run_python_script,
    # For opening files
    "open_png_file": open_png_file,
    # Virtual environments
    "create_virtual_env": create_virtual_env,
    # Create project directory
    "create_project_directory": create_project_directory,
    "initialize_react_app": initialize_react_app,
    "deploy_app_to_netlify": deploy_app_to_netlify,
    "redeploy_app_to_netlify": redeploy_app_to_netlify,
    "search_google": search_google,
    "search_website": search_website,
}
