import json
import sqlite3
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored

GPT_MODEL = "gpt-4-0125-preview"
client = OpenAI()

# Initialize database
conn = sqlite3.connect("data/chinook.db")
print("Opened database successfully")

# Database functions
def get_table_names(conn):
	table_names = []
	tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
	for table in tables.fetchall():
		table_names.append(table[0])
	return table_names

def get_column_names(conn, table_name):
	column_names = []
	columns = conn.execute(f"PRAGMA table_info('{table_name}');").fetchall()
	for col in columns:
		column_names.append(col[1])
	return column_names

def get_database_info(conn):
	table_dicts = []
	for table_name in get_table_names(conn):
		column_names = get_column_names(conn, table_name)
		table_dicts.append({"table_name": table_name, "column_names": column_names})
	return table_dicts

database_schema_dict = get_database_info(conn)
database_schema_string = "\n".join(
	[
		f"Table: {table['table_name']}\nColumns: {', '.join(table['column_names'])}"
		for table in database_schema_dict
	]
)

# Wrapper around chat completion
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
	try:
		response = client.chat.completions.create(
			model=model,
			messages=messages,
			tools=tools,
			tool_choice=tool_choice
		)
		return response
	except Exception as e:
		print("Unable to generate ChatCompletion response")
		print(f"Exception: {e}")
		return e

# Print messages in a human-readable format
def pretty_print_conversation(messages):
	role_to_color = {
		"system": "red",
		"user": "green",
		"assistant": "blue",
		"function": "magenta",
	}

	for message in messages:
		if message["role"] == "system":
			print(colored(f"System: {message['content']}\n", role_to_color[message["role"]]))
		elif message["role"] == "user":
			print(colored(f"User: {message['content']}\n", role_to_color[message["role"]]))
		elif message["role"] == "assistant" and message.get("function_call"):
			print(colored(f"Assistant: {message['function_call']}\n", role_to_color[message["role"]])),
		elif message["role"] == "assistant" and not message.get("function_call"):
			print(colored(f"Assistant: {message['content']}\n", role_to_color[message["role"]]))
		elif message["role"] == "function":
			print(colored(f"Function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

# Example dummy function
def get_current_weather(location, unit="fahrenheit"):
	"""Get the current weather in a given location"""
	if "tokyo" in location.lower():
		return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
	elif "san francisco" in location.lower():
		return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
	elif "paris" in location.lower():
		return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
	else:
		return json.dumps({"location": location, "temperature": "unknown"})

# Database helper functions
def ask_database(conn, query):
	try:
		results = str(conn.execute(query).fetchall())
	except Exception as e:
		results = f"Query failed with error: {e}"
	return results

def execute_function_call(message):
	if message.tool_calls[0].function.name == "ask_database":
		query = json.loads(message.tool_calls[0].function.arguments)["query"]
		results = ask_database(conn, query)
	else:
		results = f"Error: function {message.tool_calls[0].function.name} does not exist"
	return results

# Define tools for OpenAI API calls
tools = [
	{
		"type": "function",
		"function": {
			"name": "get_current_weather",
			"description": "Get the current weather in a given location",
			"parameters": {
				"type": "object",
				"properties": {
					"location": {
						"type": "string",
						"description": "The city and state, e.g. San Francisco, CA",
					},
					"format": {
						"type": "string",
						"enum": ["celsius", "fahrenheit"],
						"description": "The temperature unit to use. Infer this from the user's location",
					},
				},
				"required": ["location", "format"],
			},
		},
	},
	{
		"type": "function",
		"function": {
			"name": "get_n_day_weather_forecast",
			"description": "Get an N-day weather forecast",
			"parameters": {
				"type": "object",
				"properties": {
					"location": {
						"type": "string",
						"description": "The city and state, e.g. San Francisco, CA",
					},
					"format": {
						"type": "string",
						"enum": ["celsius", "fahrenheit"],
						"description": "The temperature unit to use. Infer this from the user's location",
					},
					"num_days": {
						"type": "integer",
						"description": "The number of days to forecast",
					},
				},
				"required": ["location", "format", "num_days"],
			}
		}
	},
	{
		"type": "function",
		"function": {
			"name": "ask_database",
			"description": "Use this function to answer user questions about music. Input should be a fully formed SQL query.",
			"parameters": {
				"type": "object",
				"properties": {
					"query": {
						"type": "string",
						"description": f"""
							SQL query extracting info to answer the user's question.
							SQL should be written using this database schema:
							{database_schema_string}
							The query should be returned in plain text, not in JSON.
							""",
					}
				},
				"required": ["query"],
			},
		}
	}
]

# Initialize database messages
messages = []
messages.append({"role": "system", "content": "Answer user questions by generating SQL queries against the Chinook Music Database."})
messages.append({"role": "user", "content": "Hi, who are the top 5 artists by number of tracks?"})
chat_response = chat_completion_request(messages, tools)
assistant_message = chat_response.choices[0].message
assistant_message.content = str(assistant_message.tool_calls[0].function)
messages.append({"role": assistant_message.role, "content": assistant_message.content})
if assistant_message.tool_calls:
	results = execute_function_call(assistant_message)
	messages.append({"role": "function", "tool_call_id": assistant_message.tool_calls[0].id, "name": assistant_message.tool_calls[0].function.name, "content": results})
pretty_print_conversation(messages)

# Initialize messages
print("Initializing messages")
messages = []
messages.append({"role": "system", "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."})
messages.append({"role": "user", "content": "What's the weather like today?"})
pretty_print_conversation(messages)

# Get assistant response
print("Getting first response")
chat_response = chat_completion_request(messages, tools=tools)
assistant_message = chat_response.choices[0].message
messages.append(assistant_message)
print(assistant_message)
print(messages)

# Supply additional information
print("Supplying additional information")
messages.append({"role": "user", "content": "I'm in Glasgow, Scotland."})
pretty_print_conversation(messages)

# Get assistant response
print("Getting second response")
chat_response = chat_completion_request(messages, tools=tools)
assistent_message = chat_response.choices[0].message
messages.append(assistant_message)
print(assistant_message)
pretty_print_conversation(messages)

def run_conversation():
	# Step 1: send the conversation and available functions to the model
	messages = [
		{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"},
	]
	tools = [
		{
			"type": "function",
			"function": {
				"name": "get_current_weather",
				"description": "Get the current weather in a given location",
				"parameters": {
					"type": "object",
					"properties": {
						"location": {
							"type": "string",
							"description": "The city and state, e.g. San Francisco, CA",
						},
						"format": {
							"type": "string",
							"enum": ["celsius", "fahrenheit"],
							"description": "The temperature unit to use. Infer this from the user's location",
						},
					},
					"required": ["location", "format"],
				},
			},
		},
		{
			"type": "function",
			"function": {
				"name": "get_n_day_weather_forecast",
				"description": "Get an N-day weather forecast",
				"parameters": {
					"type": "object",
					"properties": {
						"location": {
							"type": "string",
							"description": "The city and state, e.g. San Francisco, CA",
						},
						"format": {
							"type": "string",
							"enum": ["celsius", "fahrenheit"],
							"description": "The temperature unit to use. Infer this from the user's location",
						},
						"num_days": {
							"type": "integer",
							"description": "The number of days to forecast",
						},
					},
					"required": ["location", "format", "num_days"],
				}
			}
		}
	]
	response = client.chat.completions.create(
		model=GPT_MODEL,
		messages=messages,
		tools=tools,
		tool_choice="auto"
	)
	response_message = response.choices[0].message
	print(f"First response message: {response_message}")
	tool_calls = response_message.tool_calls
	# Step 2: check if the model wanted to call a function
	if tool_calls:
		# Step 3: call the function
		# Note the JSON response may not always be valid; be sure to handle errors
		available_functions = {
			"get_current_weather": get_current_weather,
		} # only one function in this example, but you can have multiple
		messages.append(response_message) # extend conversation with assistant's reply
		# Step 4: send the info for each function call and function response to the model
		for tool_call in tool_calls:
			function_name = tool_call.function.name
			function_to_call = available_functions[function_name]
			function_args = json.loads(tool_call.function.arguments)
			function_response = function_to_call(
				location=function_args.get("location"),
				unit=function_args.get("unit"),
			)
			messages.append(
				{
					"tool_call_id": tool_call.id,
					"role": "tool",
					"name": function_name,
					"content": function_response,
				}
			)
		second_response = client.chat.completions.create(
			model=GPT_MODEL,
			messages=messages,
		)
		return second_response
print(run_conversation())
