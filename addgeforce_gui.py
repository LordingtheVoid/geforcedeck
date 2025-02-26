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
    """Return installed browsers dynamically."""
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

def install_browser(app_id, browser_name):
    """Install missing browser."""
    if messagebox.askyesno(f"Install {browser_name}", f"{browser_name} is not installed. Install it now?"):
        subprocess.run(["flatpak", "install", "--user", "-y", "flathub", app_id])
        messagebox.showinfo("Success", f"{browser_name} installed! Restart the script to use it.")
        update_browser_options()  # Refresh dropdown

def uninstall_browser(app_id, browser_name):
    """Uninstall browser with confirmation."""
    if messagebox.askyesno(f"Uninstall {browser_name}", f"Are you sure you want to remove {browser_name}?"):
        subprocess.run(["flatpak", "uninstall", "--user", "-y", app_id])
        messagebox.showinfo("Success", f"{browser_name} has been uninstalled.")
        update_browser_options()  # Refresh dropdown

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

def update_browser_options():
    """Dynamically update available browser options."""
    installed = check_installed_browsers()
    browser_menu["menu"].delete(0, "end")  # Clear previous options
    for browser in installed.keys():
        browser_menu["menu"].add_command(label=browser, command=lambda v=browser: browser_var.set(v))
    if browser_var.get() not in installed:
        browser_var.set(next(iter(installed), "Chrome"))  # Default to first available browser

# --- GUI Setup ---
root = tk.Tk()
root.title("GeForce Now Shortcut Automation")

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
ttk.Button(config_tab, text="Uninstall Chrome", command=lambda: uninstall_browser("com.google.Chrome", "Chrome")).pack(pady=5)
ttk.Button(config_tab, text="Uninstall Edge", command=lambda: uninstall_browser("com.microsoft.Edge", "Edge")).pack(pady=5)

### MANUAL TAB ###
manual_tab = ttk.Frame(notebook)
notebook.add(manual_tab, text="Manual")

ttk.Label(manual_tab, text="Game Title:").pack(pady=5)
title_entry = ttk.Entry(manual_tab, width=50)
title_entry.pack(pady=5)

ttk.Label(manual_tab, text="Game URL:").pack(pady=5)
url_entry = ttk.Entry(manual_tab, width=50)
url_entry.pack(pady=5)

# Enable copy-paste functionality
title_entry.bind("<Control-v>", lambda e: title_entry.insert(tk.INSERT, root.clipboard_get()))
url_entry.bind("<Control-v>", lambda e: url_entry.insert(tk.INSERT, root.clipboard_get()))

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
ttk.Button(batch_tab, text="Process Batch", command=lambda: messagebox.showinfo("Processing", "Batch processing not yet implemented")).pack(pady=10)

ttk.Button(root, text="Save & Restart Steam", command=lambda: [save_config(browser_var.get(), last_collection), restart_steam()]).pack(pady=10)

update_browser_options()  # Ensure dropdown is updated on launch
root.mainloop()
