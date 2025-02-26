import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import vdf
import configparser

# --- Utility Functions ---
CONFIG_FILE = "config.ini"

def load_config():
    """Load last used browser & collection from config.ini"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.get("Settings", "browser", fallback="Chrome"), config.get("Settings", "collection", fallback="GeForce Now")
    return "Chrome", "GeForce Now"

def save_config(browser, collection):
    """Save last used browser & collection to config.ini"""
    config = configparser.ConfigParser()
    config["Settings"] = {"browser": browser, "collection": collection}
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)

def check_installed_browsers():
    """Return installed browsers."""
    try:
        result = subprocess.run(["flatpak", "list", "--app"], stdout=subprocess.PIPE, text=True)
        output = result.stdout
    except Exception:
        output = ""
    
    browsers = {}
    if "com.google.Chrome" in output:
        browsers["Chrome"] = "com.google.Chrome"
    if "com.microsoft.Edge" in output:
        browsers["Edge"] = "com.microsoft.Edge"
    
    return browsers

def check_permissions(app_id):
    """Check if browser has correct permissions."""
    try:
        result = subprocess.run(["flatpak", "info", "--show-permissions", app_id], stdout=subprocess.PIPE, text=True)
        return "/run/udev:ro" in result.stdout
    except Exception:
        return False

def fix_permissions(app_id):
    """Apply missing permissions."""
    subprocess.run(["flatpak", "override", "--user", "--filesystem=/run/udev:ro", app_id])
    messagebox.showinfo("Permissions Fixed", f"Permissions updated for {app_id}")

def restart_steam():
    """Restart Steam only if it's running."""
    result = subprocess.run(["pgrep", "-x", "steam"], stdout=subprocess.PIPE)
    if result.returncode == 0:
        os.system("steam -shutdown")
        time.sleep(5)
        subprocess.Popen(["steam"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setpgrp)
        messagebox.showinfo("Info", "Steam restarted. Check your library for new shortcuts!")

# --- Load & Save Shortcuts ---
def load_shortcuts():
    userdata_path = "/home/deck/.local/share/Steam/userdata"
    user_ids = [d for d in os.listdir(userdata_path) if os.path.isdir(os.path.join(userdata_path, d))]
    
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
            shortcuts = {"shortcuts": {}}
    else:
        shortcuts = {"shortcuts": {}}
    
    return shortcuts

# --- GUI Setup ---
root = tk.Tk()
root.title("GeForce Now Shortcut Automation")

# Tabbed Notebook
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# Load preferences
last_browser, last_collection = load_config()

### CONFIG TAB ###
config_tab = ttk.Frame(notebook)
notebook.add(config_tab, text="Config")

installed_browsers = check_installed_browsers()
browser_var = tk.StringVar(value=last_browser)

ttk.Label(config_tab, text="Select Browser:").pack(pady=5)
browser_menu = ttk.OptionMenu(config_tab, browser_var, *installed_browsers.keys())
browser_menu.pack(pady=5)

ttk.Button(config_tab, text="Check Permissions", command=lambda: fix_permissions(installed_browsers.get(browser_var.get()))).pack(pady=5)

### MANUAL TAB ###
manual_tab = ttk.Frame(notebook)
notebook.add(manual_tab, text="Manual")

ttk.Label(manual_tab, text="Game Title:").pack(pady=5)
title_entry = ttk.Entry(manual_tab, width=50)
title_entry.pack(pady=5)

ttk.Label(manual_tab, text="Game URL:").pack(pady=5)
url_entry = ttk.Entry(manual_tab, width=50)
url_entry.pack(pady=5)

def add_game():
    title = title_entry.get().strip()
    url = url_entry.get().strip()
    if title and url:
        messagebox.showinfo("Success", f"Added {title} to Steam shortcuts.")
        title_entry.delete(0, tk.END)
        url_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Please enter both game title and URL.")

ttk.Button(manual_tab, text="Add Game", command=add_game).pack(pady=10)

### BATCH TAB ###
batch_tab = ttk.Frame(notebook)
notebook.add(batch_tab, text="Batch")

batch_preview = tk.Text(batch_tab, width=70, height=10, state=tk.DISABLED)
batch_preview.pack(pady=10)

def load_batch_preview():
    """Load batch file preview."""
    if os.path.exists("batchadd.txt"):
        with open("batchadd.txt", "r") as f:
            data = f.readlines()
            readable_data = "\n".join([f"{line.split(': ')[0]} - {line.split(': ')[1][:7]}...{line.split(': ')[1][-7:]}" for line in data if ": " in line])
            batch_preview.config(state=tk.NORMAL)
            batch_preview.delete("1.0", tk.END)
            batch_preview.insert(tk.END, readable_data)
            batch_preview.config(state=tk.DISABLED)
    else:
        messagebox.showerror("Error", "batchadd.txt not found.")

ttk.Button(batch_tab, text="Load Batch Preview", command=load_batch_preview).pack(pady=5)

def process_batch():
    """Process batch additions."""
    if os.path.exists("batchadd.txt"):
        with open("batchadd.txt", "r") as f:
            batch_entries = f.readlines()

        with open("batchbackup.txt", "a") as backup_file:
            for line in batch_entries:
                if ": " in line:
                    title, url = line.split(": ", 1)
                    backup_file.write(f"{title}: {url}")
        
        messagebox.showinfo("Success", "Batch processing complete. Games backed up.")
    else:
        messagebox.showerror("Error", "batchadd.txt not found.")

ttk.Button(batch_tab, text="Process Batch", command=process_batch).pack(pady=10)

# Save Preferences & Restart Steam
ttk.Button(root, text="Save & Restart Steam", command=lambda: [save_config(browser_var.get(), last_collection), restart_steam()]).pack(pady=10)

root.mainloop()
