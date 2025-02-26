# SteamOS Shortcut Automation Tool - Build v1.3

import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import vdf
import configparser
import webbrowser

# Version Tracking
BUILD_VERSION = "v1.3"

# --- Utility Functions ---
CONFIG_FILE = "config.ini"

def load_config():
    """Load last used browser & collection from config.ini"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.get("Settings", "browser", fallback="Chrome"), config.get("Settings", "collection", fallback="Steam Shortcuts")
    return "Chrome", "Steam Shortcuts"

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

def check_permissions():
    """Check permissions for all installed browsers and apply fixes if needed."""
    installed = check_installed_browsers()
    fixed = []
    for browser, app_id in installed.items():
        if not check_permissions_single(app_id):
            fix_permissions(app_id)
            fixed.append(browser)
    
    if not fixed:
        messagebox.showinfo("Permissions Check", "All installed browsers have correct permissions.")
    else:
        messagebox.showinfo("Permissions Fixed", f"Permissions updated for: {', '.join(fixed)}")

def remove_permissions():
    """Popup to remove browser permissions."""
    choice = simpledialog.askstring("Remove Permissions", "Select: Chrome, Edge, Both, or Cancel")
    if choice:
        choice = choice.lower()
        if choice in ["chrome", "both"]:
            subprocess.run(["flatpak", "override", "--user", "--nofilesystem=/run/udev:ro", "com.google.Chrome"])
        if choice in ["edge", "both"]:
            subprocess.run(["flatpak", "override", "--user", "--nofilesystem=/run/udev:ro", "com.microsoft.Edge"])
        if choice in ["chrome", "edge", "both"]:
            messagebox.showinfo("Permissions Removed", f"Permissions removed for: {choice.capitalize()}")

def restart_steam():
    """Restart Steam only if it's running."""
    result = subprocess.run(["pgrep", "-x", "steam"], stdout=subprocess.PIPE)
    if result.returncode == 0:
        os.system("steam -shutdown")
        time.sleep(5)
        subprocess.Popen(["steam"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setpgrp)
        messagebox.showinfo("Info", "Steam restarted. Check your library for new shortcuts!")

def add_luna_options(url):
    """Detect Amazon Luna URLs and append user-agent launch options if needed."""
    if "luna.amazon." in url:
        return f'--kiosk "{url}" --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.54"'
    return f'--kiosk "{url}"'

def update_browser_options():
    """Dynamically update available browser options."""
    installed = check_installed_browsers()
    browser_menu["menu"].delete(0, "end")  
    for browser in installed.keys():
        browser_menu["menu"].add_command(label=browser, command=lambda v=browser: browser_var.set(v))
    if browser_var.get() not in installed:
        browser_var.set(next(iter(installed), "Chrome"))  

# --- GUI Setup ---
root = tk.Tk()
root.title(f"SteamOS Shortcut Automation Tool {BUILD_VERSION}")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

### CONFIG TAB ###
config_tab = ttk.Frame(notebook)
notebook.add(config_tab, text="Config")

browser_var = tk.StringVar(value=load_config()[0])

ttk.Label(config_tab, text="Select Browser:").pack(pady=5)
browser_menu = ttk.OptionMenu(config_tab, browser_var, *check_installed_browsers().keys())
browser_menu.pack(pady=5)

ttk.Button(config_tab, text="Check Permissions", command=check_permissions).pack(pady=5)
ttk.Button(config_tab, text="Remove Permissions", command=remove_permissions).pack(pady=5)

update_browser_options()

### MANUAL TAB ###
manual_tab = ttk.Frame(notebook)
notebook.add(manual_tab, text="Manual")

ttk.Label(manual_tab, text="Game Title:").pack(pady=5)
title_entry = ttk.Entry(manual_tab, width=50)
title_entry.pack(pady=5)

ttk.Button(manual_tab, text="Paste", command=lambda: title_entry.insert(tk.END, root.clipboard_get())).pack(pady=5)

ttk.Label(manual_tab, text="Game URL:").pack(pady=5)
url_entry = ttk.Entry(manual_tab, width=50)
url_entry.pack(pady=5)

ttk.Button(manual_tab, text="Paste", command=lambda: url_entry.insert(tk.END, root.clipboard_get())).pack(pady=5)

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
            readable_data = "\n".join([f"{line.split(': ')[0]} - {line.split(': ')[1].replace('http://', '').replace('https://', '')[:7]}...{line.split(': ')[1][-7:]}" for line in data if ": " in line])
            batch_preview.config(state=tk.NORMAL)
            batch_preview.delete("1.0", tk.END)
            batch_preview.insert(tk.END, readable_data)
            batch_preview.config(state=tk.DISABLED)
    else:
        messagebox.showerror("Error", "batchadd.txt not found.")

ttk.Button(batch_tab, text="Load Batch Preview", command=load_batch_preview).pack(pady=5)

# Restart Steam Button
ttk.Button(root, text="Save & Restart Steam", command=restart_steam).pack(pady=10)

root.mainloop()
