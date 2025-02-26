# SteamOS Shortcut Automation Tool - Build v1.2

import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import vdf
import configparser
import webbrowser

# Version Tracking
BUILD_VERSION = "v1.2"

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
    browser_menu["menu"].delete(0, "end")  
    for browser in installed.keys():
        browser_menu["menu"].add_command(label=browser, command=lambda v=browser: browser_var.set(v))
    if browser_var.get() not in installed:
        browser_var.set(next(iter(installed), "Chrome"))  

    if "Chrome" not in installed:
        install_chrome_btn.pack()
        uninstall_chrome_btn.pack_forget()
    else:
        install_chrome_btn.pack_forget()
        uninstall_chrome_btn.pack()

    if "Edge" not in installed:
        install_edge_btn.pack()
        uninstall_edge_btn.pack_forget()
    else:
        install_edge_btn.pack_forget()
        uninstall_edge_btn.pack()

# --- GUI Setup ---
root = tk.Tk()
root.title(f"SteamOS Shortcut Automation Tool {BUILD_VERSION}")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# Load preferences
last_browser, last_collection = load_config()

### CONFIG TAB ###
config_tab = ttk.Frame(notebook)
notebook.add(config_tab, text="Config")

browser_var = tk.StringVar(value=last_browser)

ttk.Label(config_tab, text="Select Browser:").pack(pady=5)
browser_menu = ttk.OptionMenu(config_tab, browser_var, *check_installed_browsers().keys())
browser_menu.pack(pady=5)

install_chrome_btn = ttk.Button(config_tab, text="Install Chrome", command=lambda: install_browser("com.google.Chrome", "Chrome"))
install_edge_btn = ttk.Button(config_tab, text="Install Edge", command=lambda: install_browser("com.microsoft.Edge", "Edge"))

uninstall_chrome_btn = ttk.Button(config_tab, text="Uninstall Chrome", command=lambda: uninstall_browser("com.google.Chrome", "Chrome"))
uninstall_edge_btn = ttk.Button(config_tab, text="Uninstall Edge", command=lambda: uninstall_browser("com.microsoft.Edge", "Edge"))

ttk.Button(config_tab, text="Check Permissions", command=check_permissions).pack(pady=5)

update_browser_options()

### MANUAL TAB ###
manual_tab = ttk.Frame(notebook)
notebook.add(manual_tab, text="Manual")

ttk.Button(manual_tab, text="Paste", command=lambda: title_entry.insert(tk.END, root.clipboard_get())).pack(side=tk.LEFT, padx=5)
title_entry = ttk.Entry(manual_tab, width=50)
title_entry.pack(pady=5)

ttk.Button(manual_tab, text="Paste", command=lambda: url_entry.insert(tk.END, root.clipboard_get())).pack(side=tk.LEFT, padx=5)
url_entry = ttk.Entry(manual_tab, width=50)
url_entry.pack(pady=5)

### ABOUT TAB ###
about_tab = ttk.Frame(notebook)
notebook.add(about_tab, text="About")

ttk.Label(about_tab, text=f"SteamOS Shortcut Automation Tool {BUILD_VERSION}\nGitHub:").pack(pady=5)
ttk.Button(about_tab, text="Open GitHub", command=lambda: webbrowser.open("https://github.com/LordingtheVoid")).pack(pady=5)

# Restart Steam Button
ttk.Button(root, text="Save & Restart Steam", command=lambda: [save_config(browser_var.get(), last_collection), restart_steam()]).pack(pady=10)

update_browser_options()
root.mainloop()
