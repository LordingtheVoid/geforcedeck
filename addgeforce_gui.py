# SteamOS Shortcut Automation Tool - Build v1.4

import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import vdf
import configparser
import webbrowser

# Version Tracking
BUILD_VERSION = "v1.4"

# --- Utility Functions ---
CONFIG_FILE = "config.ini"

def load_config():
    """Load last used browser & collection from config.ini"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.get("Settings", "browser", fallback="Chrome"), config.get("Settings", "collection", fallback="")
    return "Chrome", ""

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
    """Check permissions for all installed browsers and show results."""
    installed = check_installed_browsers()
    results = []
    for browser, app_id in installed.items():
        if check_permissions_single(app_id):
            results.append(f"{browser}: ✅ OK")
        else:
            fix_permissions(app_id)
            results.append(f"{browser}: ❌ Fixed")

    if results:
        messagebox.showinfo("Permissions Check", "\n".join(results))
    else:
        messagebox.showinfo("Permissions Check", "No browsers detected.")

def remove_permissions():
    """Popup to remove browser permissions with button selection."""
    def remove_perm(browser):
        if browser in ["Chrome", "Both"]:
            subprocess.run(["flatpak", "override", "--user", "--nofilesystem=/run/udev:ro", "com.google.Chrome"])
        if browser in ["Edge", "Both"]:
            subprocess.run(["flatpak", "override", "--user", "--nofilesystem=/run/udev:ro", "com.microsoft.Edge"])
        messagebox.showinfo("Permissions Removed", f"Permissions removed for: {browser}")

    remove_win = tk.Toplevel(root)
    remove_win.title("Remove Permissions")
    ttk.Label(remove_win, text="Select Browser to Remove Permissions:").pack(pady=10)
    ttk.Button(remove_win, text="Chrome", command=lambda: remove_perm("Chrome")).pack(pady=5)
    ttk.Button(remove_win, text="Edge", command=lambda: remove_perm("Edge")).pack(pady=5)
    ttk.Button(remove_win, text="Both", command=lambda: remove_perm("Both")).pack(pady=5)
    ttk.Button(remove_win, text="Cancel", command=remove_win.destroy).pack(pady=10)

def add_luna_options(url):
    """Detect Amazon Luna URLs and append user-agent launch options if needed."""
    if "luna.amazon." in url:
        return f'--kiosk "{url}" --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.54"'
    return f'--kiosk "{url}"'

# --- GUI Setup ---
root = tk.Tk()
root.title(f"SteamOS Shortcut Automation Tool {BUILD_VERSION}")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

### CONFIG TAB ###
config_tab = ttk.Frame(notebook)
notebook.add(config_tab, text="Config")

ttk.Button(config_tab, text="Check Permissions", command=check_permissions).pack(pady=5)
ttk.Button(config_tab, text="Remove Permissions", command=remove_permissions).pack(pady=5)

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

### COLLECTIONS ###
collection_var = tk.StringVar(value="Blank")
ttk.Label(manual_tab, text="Select Collection:").pack(pady=5)
collections_menu = ttk.Combobox(manual_tab, textvariable=collection_var, values=["Blank", "GeForce Now", "Xbox Cloud Gaming", "Amazon Luna", "Custom"])
collections_menu.pack(pady=5)

custom_collection_entry = ttk.Entry(manual_tab, width=50)
custom_collection_entry.pack(pady=5)
custom_collection_entry.pack_forget()

def toggle_custom_collection(event):
    if collection_var.get() == "Custom":
        custom_collection_entry.pack(pady=5)
    else:
        custom_collection_entry.pack_forget()

collections_menu.bind("<<ComboboxSelected>>", toggle_custom_collection)

### ABOUT TAB ###
about_tab = ttk.Frame(notebook)
notebook.add(about_tab, text="About")

ttk.Label(about_tab, text=f"SteamOS Shortcut Automation Tool {BUILD_VERSION}\nGitHub:").pack(pady=5)
ttk.Button(about_tab, text="Open GitHub", command=lambda: webbrowser.open("https://github.com/LordingtheVoid")).pack(pady=5)

root.mainloop()
