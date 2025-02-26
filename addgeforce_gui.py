import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import vdf

def list_to_dict(lst):
    """Convert a list to a dictionary with numeric keys."""
    return {str(i): item for i, item in enumerate(lst)}

def check_installed_browsers():
    """Return a dictionary of installed browsers with browser name as key and app_id as value."""
    try:
        result = subprocess.run(["flatpak", "list", "--app"], stdout=subprocess.PIPE, text=True)
        output = result.stdout
    except Exception as e:
        output = ""
    browsers = {}
    if "com.google.Chrome" in output:
        browsers["Chrome"] = "com.google.Chrome"
    if "com.microsoft.Edge" in output:
        browsers["Edge"] = "com.microsoft.Edge"
    return browsers

def install_browser(app_id, browser_name):
    # Install browser using flatpak
    messagebox.showinfo("Install Browser", f"{browser_name} is not installed. Installing {browser_name} now...")
    try:
        subprocess.run(["flatpak", "install", "--user", "-y", "flathub", app_id])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to install {browser_name}: {e}")

def check_permissions(app_id):
    """Check if the browser has the required permissions; if not, override them."""
    try:
        result = subprocess.run(["flatpak", "info", "--show-permissions", app_id],
                                stdout=subprocess.PIPE, text=True)
        if "/run/udev:ro" not in result.stdout:
            subprocess.run(["flatpak", "override", "--user", "--filesystem=/run/udev:ro", app_id])
    except Exception as e:
        messagebox.showerror("Error", f"Error checking permissions for {app_id}: {e}")

def load_shortcuts():
    userdata_path = "/home/deck/.local/share/Steam/userdata"
    user_ids = [d for d in os.listdir(userdata_path)
                if os.path.isdir(os.path.join(userdata_path, d))]
    if len(user_ids) == 1:
        user_id = user_ids[0]
    else:
        messagebox.showerror("Error", "Multiple user IDs found, please specify.")
        exit(1)
    global shortcuts_path
    shortcuts_path = os.path.join(userdata_path, user_id, "config", "shortcuts.vdf")
    if os.path.exists(shortcuts_path) and os.path.getsize(shortcuts_path) > 0:
        try:
            with open(shortcuts_path, "rb") as f:
                shortcuts = vdf.binary_load(f)
        except SyntaxError:
            messagebox.showwarning("Warning", f"{shortcuts_path} is corrupted. Starting with an empty shortcuts dictionary.")
            shortcuts = {"shortcuts": {}}
    else:
        messagebox.showinfo("Info", f"{shortcuts_path} is empty or doesn't exist. Starting with an empty shortcuts dictionary.")
        shortcuts = {"shortcuts": {}}
    return shortcuts

def find_browser_entry(shortcuts, browser_name):
    browser_entry = None
    for key, entry in shortcuts.get('shortcuts', {}).items():
        app_name = entry.get('appname', '').lower()
        if browser_name.lower() in app_name:
            browser_entry = entry
            break
    if browser_entry is None:
        messagebox.showerror("Error", f"No {browser_name} entry found. Please add {browser_name} manually as a non-Steam game first.")
        exit(1)
    return browser_entry

def save_shortcuts(shortcuts):
    with open(shortcuts_path, "wb") as f:
        vdf.binary_dump(shortcuts, f)

def restart_steam():
    os.system("steam -shutdown")
    time.sleep(5)  # Give Steam time to close
    subprocess.Popen(
        ["steam"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setpgrp
    )
    messagebox.showinfo("Info", "Steam restarted. Check your library for the new shortcuts!")

# --- Browser Detection & Setup ---
installed_browsers = check_installed_browsers()
if not installed_browsers:
    # If no browsers are installed, prompt to install Chrome by default.
    response = messagebox.askyesno("No Browser Found", "No compatible browser found. Would you like to install Chrome?")
    if response:
        install_browser("com.google.Chrome", "Chrome")
        installed_browsers = check_installed_browsers()
    else:
        messagebox.showerror("Error", "A compatible browser is required. Exiting.")
        exit(1)

# Load shortcuts
shortcuts = load_shortcuts()

# Global variables for selected browser information; default to the first available browser.
selected_browser_name = list(installed_browsers.keys())[0]
check_permissions(installed_browsers[selected_browser_name])
selected_browser_entry = find_browser_entry(shortcuts, selected_browser_name)
browser_exe = selected_browser_entry['exe']
browser_app_id = installed_browsers[selected_browser_name]
start_dir = selected_browser_entry['StartDir']

def update_browser_selection(new_browser):
    global selected_browser_name, selected_browser_entry, browser_exe, browser_app_id, start_dir
    selected_browser_name = new_browser
    check_permissions(installed_browsers[selected_browser_name])
    selected_browser_entry = find_browser_entry(shortcuts, selected_browser_name)
    browser_exe = selected_browser_entry['exe']
    browser_app_id = installed_browsers[selected_browser_name]
    start_dir = selected_browser_entry['StartDir']
    messagebox.showinfo("Browser Selected", f"Using {selected_browser_name} for shortcuts.")

def add_game(game_title, game_url):
    launch_options = (
        f'run --branch=stable --arch=x86_64 --command={browser_exe} --file-forwarding {browser_app_id} @@u @@ '
        f'--window-size=1024,640 --force-device-scale-factor=1.25 --device-scale-factor=1.25 --kiosk "{game_url}"'
    )
    existing_keys = [int(k) for k in shortcuts['shortcuts'].keys() if k.isdigit()]
    new_key = str(max(existing_keys) + 1) if existing_keys else "0"
    new_entry = {
        "appname": game_title,
        "exe": browser_exe,
        "StartDir": start_dir,
        "LaunchOptions": launch_options,
        "icon": "",
        "ShortcutPath": "",
        "IsHidden": 0,
        "AllowDesktopConfig": 1,
        "OpenVR": 0,
        "Devkit": 0,
        "DevkitGameID": "",
        "LastPlayTime": 0,
        "tags": list_to_dict(["GeForce Now"])
    }
    shortcuts['shortcuts'][new_key] = new_entry
    return new_entry

def process_batch():
    batch_file = "batchadd.txt"
    backup_file = "batchbackup.txt"
    if not os.path.exists(batch_file):
        messagebox.showerror("Error", f"{batch_file} not found in the current directory.")
        return
    with open(batch_file, "r") as f:
        lines = f.readlines()
    to_add = []
    to_skip = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ": " in line:
            game_title, game_url = line.split(": ", 1)
            game_title = game_title.strip()
            game_url = game_url.strip()
            if game_url:
                to_add.append((game_title, game_url, line))
            else:
                to_skip.append(game_title)
        else:
            to_skip.append(line)
    result_text = ""
    if to_add:
        result_text += "Games to be added:\n"
        for title, url, _ in to_add:
            result_text += f"  {title}: {url}\n"
        if messagebox.askyesno("Confirm", "Proceed with adding these games?"):
            added_count = 0
            for game_title, game_url, _ in to_add:
                add_game(game_title, game_url)
                result_text += f"Added {game_title} to Steam shortcuts.\n"
                added_count += 1
            # Update batchadd.txt: remove lines that were added
            remaining_lines = [line for line in lines if line.strip() not in [entry[2] for entry in to_add]]
            with open(batch_file, "w") as f:
                f.writelines(remaining_lines)
            # Append to batchbackup.txt
            with open(backup_file, "a") as f:
                for _, _, original_line in to_add:
                    f.write(original_line + "\n")
            result_text += f"\nAdded {added_count} shortcuts. Updated {batch_file} and {backup_file}.\n"
        else:
            result_text += "Batch addition canceled.\n"
    else:
        result_text += "No valid games to add.\n"
    batch_log_text.delete("1.0", tk.END)
    batch_log_text.insert(tk.END, result_text)

# Create the main GUI window
root = tk.Tk()
root.title("GeForce Now Shortcut Automation")

# Top frame for browser selection
top_frame = ttk.Frame(root)
top_frame.pack(pady=5)
ttk.Label(top_frame, text="Select Browser:").pack(side=tk.LEFT, padx=5)
browser_var = tk.StringVar(value=selected_browser_name)
browser_menu = ttk.OptionMenu(top_frame, browser_var, selected_browser_name, *installed_browsers.keys(), command=update_browser_selection)
browser_menu.pack(side=tk.LEFT, padx=5)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# ----- Interactive Mode Tab -----
interactive_frame = ttk.Frame(notebook)
notebook.add(interactive_frame, text="Interactive Mode")

ttk.Label(interactive_frame, text="Game Title:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
title_entry = ttk.Entry(interactive_frame, width=50)
title_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(interactive_frame, text="Game URL:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
url_entry = ttk.Entry(interactive_frame, width=50)
url_entry.grid(row=1, column=1, padx=5, pady=5)

# Bind Control-V for paste in URL entry
url_entry.bind("<Control-v>", lambda event: url_entry.insert(tk.INSERT, root.clipboard_get()))

# Create a right-click context menu for URL entry
def show_context_menu(event):
    try:
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()

context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Paste", command=lambda: url_entry.insert(tk.INSERT, root.clipboard_get()))
url_entry.bind("<Button-3>", show_context_menu)

def add_game_interactive():
    title = title_entry.get().strip()
    url = url_entry.get().strip()
    if title and url:
        add_game(title, url)
        interactive_log_text.insert(tk.END, f"Added {title} to Steam shortcuts.\n")
        title_entry.delete(0, tk.END)
        url_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Please enter both game title and URL.")

add_button = ttk.Button(interactive_frame, text="Add Game", command=add_game_interactive)
add_button.grid(row=2, column=0, columnspan=2, pady=5)

interactive_log_text = tk.Text(interactive_frame, width=70, height=10)
interactive_log_text.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

finish_button_interactive = ttk.Button(interactive_frame, text="Finish & Restart Steam",
                                         command=lambda: [save_shortcuts(shortcuts), restart_steam()])
finish_button_interactive.grid(row=4, column=0, columnspan=2, pady=10)

# ----- Batch Mode Tab -----
batch_frame = ttk.Frame(notebook)
notebook.add(batch_frame, text="Batch Mode")

def load_batch():
    batch_file = "batchadd.txt"
    if os.path.exists(batch_file):
        with open(batch_file, "r") as f:
            content = f.read()
        batch_text.delete("1.0", tk.END)
        batch_text.insert(tk.END, content)
    else:
        messagebox.showerror("Error", f"{batch_file} not found.")

load_batch_button = ttk.Button(batch_frame, text="Load Batch File", command=load_batch)
load_batch_button.grid(row=0, column=0, padx=5, pady=5)

batch_text = tk.Text(batch_frame, width=70, height=10)
batch_text.grid(row=1, column=0, padx=5, pady=5)

process_batch_button = ttk.Button(batch_frame, text="Process Batch", command=process_batch)
process_batch_button.grid(row=2, column=0, padx=5, pady=5)

batch_log_text = tk.Text(batch_frame, width=70, height=10)
batch_log_text.grid(row=3, column=0, padx=5, pady=5)

finish_button_batch = ttk.Button(batch_frame, text="Finish & Restart Steam",
                                   command=lambda: [save_shortcuts(shortcuts), restart_steam()])
finish_button_batch.grid(row=4, column=0, padx=5, pady=10)

root.mainloop()
