import os
import tkinter as tk
from tkinter import scrolledtext
import threading
import configparser
import openai
import pty
import subprocess
import locale
from tkinter import font

# OpenAI API Key initialization
config = configparser.ConfigParser()
config_file = 'config.ini'

if not os.path.exists(config_file):
    print(f"Debug: Configuration file '{config_file}' not found.")
    raise FileNotFoundError(f"Configuration file '{config_file}' not found. Please create it and add your OpenAI API key.")

config.read(config_file)

if 'openai' not in config or 'api_key' not in config['openai']:
    print(f"Debug: Sections found in config: {config.sections()}")
    print(f"Debug: Configuration content: {dict(config._sections)}")
    print("API key not found in configuration file. Please add it to config.ini under [openai] section.")
    exit(1)

api_key = config['openai']['api_key']
if not api_key or not isinstance(api_key, str):
    print(f"Debug: API key returned from config: {api_key}")
    raise ValueError("Invalid OpenAI API key. Please check your configuration.")

# Set OpenAI API key
client = openai.OpenAI(api_key=api_key)

# Detect user's language
user_language, _ = locale.getdefaultlocale()

# Execute command in a real terminal
def execute_command(command, terminal_output):
    def read(fd):
        while True:
            output = os.read(fd, 1024).decode()
            if not output:
                break
            terminal_output.insert(tk.END, output)
            terminal_output.see(tk.END)

    master, slave = pty.openpty()
    process = subprocess.Popen(command, shell=True, stdin=slave, stdout=slave, stderr=slave, close_fds=True)
    os.close(slave)
    threading.Thread(target=read, args=(master,)).start()

# Get AI suggestion for next command
def ai_suggest(target, chat_log):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are an assistant helping to achieve the following target. Respond in {user_language}. Provide only the next command."},
                {"role": "user", "content": f"Target: {target}\nProvide only the next command to achieve this target step by step."}
            ],
            temperature=0.6,
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except AttributeError:
        # Handle issue with response structure
        return "Error: Unexpected response format from OpenAI API."

class AIAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Terminal Assistant")
        self.target = ""
        self.chat_log = ""

        # Set up the main layout with three parts
        self.setup_layout()

    def setup_layout(self):
        # Terminal Area (Left Side) - Larger area with interactive terminal
        self.terminal_output = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=90, height=30, font=font.Font(size=12))
        self.terminal_output.grid(row=0, column=0, rowspan=6, padx=10, pady=10, sticky='nsew')
        self.terminal_output.insert(tk.END, "Welcome to AI Terminal Assistant!\n")

        # Suggestion Area (Right Upper) - Adjusted size
        self.suggestion_label = tk.Label(self.root, text="AI Suggested Steps:")
        self.suggestion_label.grid(row=0, column=1, padx=10, pady=5)
        
        self.suggestion_text = tk.Text(self.root, wrap=tk.WORD, width=50, height=15, font=font.Font(size=12))
        self.suggestion_text.grid(row=1, column=1, padx=10, pady=5)

        # Command Area (Right Lower)
        self.command_label = tk.Label(self.root, text="AI Suggested Command:")
        self.command_label.grid(row=2, column=1, padx=10, pady=5)
        
        self.command_entry = tk.Entry(self.root, width=50, font=font.Font(size=12))
        self.command_entry.grid(row=3, column=1, padx=10, pady=5)
        
        # Buttons for Command Execution
        self.execute_button = tk.Button(self.root, text="Execute", command=self.execute_command)
        self.execute_button.grid(row=4, column=1, sticky='w', padx=10, pady=5)
        
        self.resuggest_button = tk.Button(self.root, text="Resuggest", command=self.resuggest_command)
        self.resuggest_button.grid(row=4, column=1, padx=10, pady=5)
        
        self.cancel_button = tk.Button(self.root, text="Cancel", command=self.cancel_command)
        self.cancel_button.grid(row=4, column=1, sticky='e', padx=10, pady=5)

        # Target Entry
        self.target_label = tk.Label(self.root, text="Enter your goal:")
        self.target_label.grid(row=5, column=1, padx=10, pady=5)

        self.target_entry = tk.Entry(self.root, width=50, font=font.Font(size=12))
        self.target_entry.grid(row=6, column=1, padx=10, pady=5)
        
        self.start_button = tk.Button(self.root, text="Start", command=self.start_goal)
        self.start_button.grid(row=6, column=1, sticky='e', padx=10, pady=5)

    def start_goal(self):
        self.target = self.target_entry.get()
        self.chat_log = ""
        self.terminal_output.insert(tk.END, f"\nUser Goal: {self.target}\n")
        self.suggest_next_step()

    def suggest_next_step(self):
        if self.target:
            self.terminal_output.insert(tk.END, "AI is thinking...\n")
            threading.Thread(target=self.get_ai_suggestion).start()

    def get_ai_suggestion(self):
        try:
            suggestion = ai_suggest(self.target, self.chat_log)
            self.chat_log += f"\n{suggestion}"
            self.suggestion_text.delete(1.0, tk.END)
            self.suggestion_text.insert(tk.END, suggestion)
            self.command_entry.delete(0, tk.END)
            command = suggestion.split('\n')[-1]
            self.command_entry.insert(0, command)
            self.terminal_output.insert(tk.END, f"AI Suggested Command: {command}\n")
        except Exception as e:
            self.terminal_output.insert(tk.END, f"Error: {e}\n")

    def execute_command(self):
        command = self.command_entry.get()
        if command:
            self.terminal_output.insert(tk.END, f"Executing: {command}\n")
            threading.Thread(target=execute_command, args=(command, self.terminal_output)).start()

    def resuggest_command(self):
        self.suggest_next_step()

    def cancel_command(self):
        self.command_entry.delete(0, tk.END)
        self.terminal_output.insert(tk.END, "Command input cancelled.\n")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1400x900")  # Adjust window size to be larger by default
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=3)
    root.columnconfigure(1, weight=1)
    app = AIAssistantApp(root)
    root.mainloop()