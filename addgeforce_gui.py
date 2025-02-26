# GeForce Now Shortcut Automation - Build v1.1

import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import vdf
import configparser

# Version Tracking
BUILD_VERSION = "v1.1"

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

def check_permissions_single(app_id):
    """Check if browser has correct permissions."""
    try:
        result = subprocess.run(["flatpak", "info", "--show-permissions", app_id], stdout=subprocess.PIPE, text=True)
        return "/run/udev:ro" in result.stdout
    except Exception:
        return False

def fix_permissions(app_id):
    """Apply missing permissions."""
    subprocess.run(["flatpak", "override", "--user", "--filesystem=/run/udev:ro", app_id])

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

    # Show install buttons if browser is missing
    if "Chrome" not in installed:
        install_chrome_btn.pack()
    else:
        install_chrome_btn.pack_forget()

    if "Edge" not in installed:
        install_edge_btn.pack()
    else:
        install_edge_btn.pack_forget()

# --- GUI Setup ---
root = tk.Tk()
root.title(f"GeForce Now Shortcut Automation {BUILD_VERSION}")

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

ttk.Button(config_tab, text="Check Permissions", command=check_permissions).pack(pady=5)

install_chrome_btn = ttk.Button(config_tab, text="Install Chrome", command=lambda: install_browser("com.google.Chrome", "Chrome"))
install_edge_btn = ttk.Button(config_tab, text="Install Edge", command=lambda: install_browser("com.microsoft.Edge", "Edge"))

update_browser_options()

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

# Restart Steam Button
ttk.Button(root, text="Save & Restart Steam", command=lambda: [save_config(browser_var.get(), last_collection), restart_steam()]).pack(pady=10)

update_browser_options()  # Ensure dropdown is updated on launch
root.mainloop()
