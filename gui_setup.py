#!/usr/bin/env python3
"""
LLM Council - Simple GUI Setup Tool
No command line needed - just click buttons!
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import sys
import subprocess
import threading
from pathlib import Path

class LLMCouncilGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Council Setup - Easy Mode")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Set window icon color
        self.root.configure(bg='#f0f0f0')

        self.project_dir = Path(__file__).parent
        self.env_file = self.project_dir / ".env"

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab 1: Setup
        self.setup_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.setup_tab, text="1️⃣ Setup API Key")
        self.create_setup_tab()

        # Tab 2: Run
        self.run_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.run_tab, text="2️⃣ Run Council")
        self.create_run_tab()

        # Tab 3: Deploy
        self.deploy_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.deploy_tab, text="3️⃣ Deploy to Cloud")
        self.create_deploy_tab()

        # Tab 4: Help
        self.help_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.help_tab, text="❓ Help")
        self.create_help_tab()

    def create_setup_tab(self):
        """Setup tab - Configure API key"""
        frame = ttk.Frame(self.setup_tab, padding="20")
        frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(frame, text="Step 1: Add Your OpenRouter API Key",
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Instructions
        instructions = ttk.Label(frame, text=
            "1. Go to: https://openrouter.ai/keys\n"
            "2. Copy your API key\n"
            "3. Paste it below\n"
            "4. Click 'Save API Key'",
            justify='left', font=('Arial', 10))
        instructions.pack(pady=10)

        # API Key input
        ttk.Label(frame, text="Your API Key:").pack(anchor='w', pady=(10, 0))
        self.api_key_input = ttk.Entry(frame, width=60, show="*")
        self.api_key_input.pack(fill='x', pady=5)

        # Show/Hide button
        self.show_key = tk.BooleanVar(value=False)
        show_btn = ttk.Checkbutton(frame, text="Show API Key",
                                   variable=self.show_key,
                                   command=self.toggle_api_key_visibility)
        show_btn.pack(anchor='w', pady=5)

        # Save button
        save_btn = ttk.Button(frame, text="💾 Save API Key",
                             command=self.save_api_key)
        save_btn.pack(pady=20, fill='x')

        # Status label
        self.setup_status = ttk.Label(frame, text="", foreground='green')
        self.setup_status.pack(pady=10)

        # Check if already configured
        self.check_api_key_status()

    def toggle_api_key_visibility(self):
        """Show or hide API key"""
        if self.show_key.get():
            self.api_key_input.config(show="")
        else:
            self.api_key_input.config(show="*")

    def check_api_key_status(self):
        """Check if API key is already configured"""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                content = f.read()
                if 'OPENROUTER_API_KEY=' in content:
                    # Extract the key to show it was set
                    self.setup_status.config(text="✅ API Key already saved!", foreground='green')

    def save_api_key(self):
        """Save API key to .env file"""
        api_key = self.api_key_input.get().strip()

        if not api_key:
            messagebox.showerror("Error", "Please enter your API key!")
            return

        if not api_key.startswith("sk-or-v1-"):
            messagebox.showwarning("Warning",
                "This doesn't look like a valid OpenRouter API key.\n"
                "Make sure you copied it correctly from https://openrouter.ai/keys")
            return

        try:
            # Create or update .env file
            env_content = f"""# OpenRouter API Key
OPENROUTER_API_KEY={api_key}

# Optional settings
USE_FIRESTORE=true
"""
            with open(self.env_file, 'w') as f:
                f.write(env_content)

            self.setup_status.config(text="✅ API Key saved successfully!", foreground='green')
            messagebox.showinfo("Success",
                "✅ API Key saved!\n\n"
                "Go to Tab 2 to run the Council locally,\n"
                "or Tab 3 to deploy to Google Cloud.")

            self.api_key_input.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API key:\n{str(e)}")

    def create_run_tab(self):
        """Run tab - Start the council locally"""
        frame = ttk.Frame(self.run_tab, padding="20")
        frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(frame, text="Step 2: Run Council Locally",
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Instructions
        instructions = ttk.Label(frame, text=
            "This will start the LLM Council on your computer.\n"
            "It will run in the background.\n"
            "You can access it at: http://localhost:8001",
            justify='center', font=('Arial', 10))
        instructions.pack(pady=10)

        # Run button
        run_btn = ttk.Button(frame, text="▶️ Start Council (Local)",
                            command=self.start_local)
        run_btn.pack(pady=20, fill='x')

        # Status
        self.run_status = ttk.Label(frame, text="", foreground='blue')
        self.run_status.pack(pady=10)

        # Output box
        ttk.Label(frame, text="Console Output:").pack(anchor='w', pady=(20, 0))
        self.run_output = scrolledtext.ScrolledText(frame, height=15, width=70)
        self.run_output.pack(fill='both', expand=True, pady=5)

        # Info
        info = ttk.Label(frame, text=
            "⏱️ First run may take 30 seconds to load models\n"
            "📱 Open browser to: http://localhost:8001\n"
            "⚠️ Keep this window open while using the Council",
            justify='center', font=('Arial', 9), foreground='#666')
        info.pack(pady=10)

    def start_local(self):
        """Start council locally"""
        if not self.env_file.exists():
            messagebox.showerror("Error",
                "❌ API Key not configured!\n\n"
                "Go to Tab 1 and save your API key first.")
            return

        self.run_status.config(text="⏳ Starting Council... (check console below)",
                              foreground='blue')
        self.run_output.delete(1.0, tk.END)

        def run_in_thread():
            try:
                env = os.environ.copy()
                # Load env file
                with open(self.env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env[key] = value

                process = subprocess.Popen(
                    [sys.executable, '-m', 'backend.main'],
                    cwd=str(self.project_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    env=env
                )

                for line in process.stdout:
                    self.run_output.insert(tk.END, line)
                    self.run_output.see(tk.END)
                    self.root.update()

            except Exception as e:
                self.run_output.insert(tk.END, f"Error: {str(e)}\n")

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

        self.run_status.config(text="✅ Council is running! Visit http://localhost:8001",
                              foreground='green')

    def create_deploy_tab(self):
        """Deploy tab - Deploy to Google Cloud"""
        frame = ttk.Frame(self.deploy_tab, padding="20")
        frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(frame, text="Step 3: Deploy to Google Cloud",
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Instructions
        instructions = ttk.Label(frame, text=
            "Deploys your Council to Google Cloud Firebase\n"
            "Your Council will be live on the internet!\n\n"
            "Requirements:\n"
            "• Firebase project configured\n"
            "• Firebase CLI installed",
            justify='left', font=('Arial', 10))
        instructions.pack(pady=10)

        # Deploy button
        deploy_btn = ttk.Button(frame, text="🚀 Deploy to Cloud",
                               command=self.start_deploy)
        deploy_btn.pack(pady=20, fill='x')

        # Status
        self.deploy_status = ttk.Label(frame, text="", foreground='blue')
        self.deploy_status.pack(pady=10)

        # Output box
        ttk.Label(frame, text="Deployment Log:").pack(anchor='w', pady=(20, 0))
        self.deploy_output = scrolledtext.ScrolledText(frame, height=15, width=70)
        self.deploy_output.pack(fill='both', expand=True, pady=5)

        # Info
        info = ttk.Label(frame, text=
            "⏱️ Deployment may take 5-10 minutes\n"
            "📚 See 'Help' tab for detailed instructions",
            justify='center', font=('Arial', 9), foreground='#666')
        info.pack(pady=10)

    def start_deploy(self):
        """Start deployment"""
        if not self.env_file.exists():
            messagebox.showerror("Error",
                "❌ API Key not configured!\n\n"
                "Go to Tab 1 and save your API key first.")
            return

        self.deploy_status.config(text="⏳ Deploying... (this may take several minutes)",
                                 foreground='blue')
        self.deploy_output.delete(1.0, tk.END)

        def run_in_thread():
            try:
                env = os.environ.copy()
                # Load env file
                with open(self.env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env[key] = value

                process = subprocess.Popen(
                    ['bash', 'deploy.sh'],
                    cwd=str(self.project_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    env=env
                )

                for line in process.stdout:
                    self.deploy_output.insert(tk.END, line)
                    self.deploy_output.see(tk.END)
                    self.root.update()

                process.wait()
                if process.returncode == 0:
                    self.deploy_status.config(
                        text="✅ Deployment successful! Check the log above for your URL",
                        foreground='green')
                else:
                    self.deploy_status.config(
                        text="❌ Deployment failed. See log above for details.",
                        foreground='red')

            except Exception as e:
                self.deploy_output.insert(tk.END, f"Error: {str(e)}\n")
                self.deploy_status.config(text=f"❌ Error: {str(e)}", foreground='red')

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    def create_help_tab(self):
        """Help tab - Instructions and FAQs"""
        frame = ttk.Frame(self.help_tab, padding="20")
        frame.pack(fill='both', expand=True)

        help_text = scrolledtext.ScrolledText(frame, height=30, width=70,
                                             wrap='word', state='normal')
        help_text.pack(fill='both', expand=True)

        help_content = """
LLM COUNCIL - HELP & INSTRUCTIONS
═══════════════════════════════════════════════════════════════

WHAT IS THIS?
─────────────
The LLM Council is an AI system with 4 specialist personas:
  🔵 Orchestrator - Clarifies confusing requests
  🟢 Architect - Designs systems with trade-offs
  🔴 Mentor - Gives ruthless, honest feedback
  🟣 Visionary - Focuses on innovation & future tech

They work together to give you the best answer to any question!

QUICK START (3 STEPS)
────────────────────
1. TAB 1: Add your OpenRouter API key
2. TAB 2: Click "Start Council (Local)"
3. Open http://localhost:8001 in your browser

GETTING YOUR API KEY
────────────────────
1. Visit: https://openrouter.ai/keys
2. Sign up (free)
3. Click "Create New Key"
4. Copy the key
5. Paste it in Tab 1

DEPLOYING TO CLOUD
──────────────────
To deploy to Google Cloud (make it live on internet):
1. Create Firebase project: https://console.firebase.google.com
2. Install Firebase CLI (if you have Node.js)
3. Run: firebase init
4. Go to Tab 3 and click "Deploy to Cloud"

TROUBLESHOOTING
───────────────
Q: "API Key not found"
A: Go to Tab 1 and save your API key first

Q: "Connection error"
A: Make sure you're running the Council (Tab 2)

Q: "Can't deploy"
A: Make sure you have Firebase CLI installed and configured

WHAT'S HAPPENING BEHIND THE SCENES?
────────────────────────────────────
• Tab 2 runs the Council on your computer
• Your questions are sent to OpenRouter's API
• 4 AI models respond independently
• They evaluate each other's answers
• A Chairman AI synthesizes the best answer
• Everything is encrypted and secure

NEED MORE HELP?
───────────────
Check the project README at:
/home/user/llm-council/README.md

Or ask for help in the GitHub issues:
https://github.com/mapachekurt/llm-council
"""

        help_text.insert(1.0, help_content)
        help_text.config(state='disabled')


def main():
    root = tk.Tk()
    app = LLMCouncilGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
