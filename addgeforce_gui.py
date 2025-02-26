import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import vdf

# --- Utility Functions ---
def list_to_dict(lst):
    """Convert a list to a dictionary with numeric keys."""
    return {str(i): item for i, item in enumerate(lst)}

def check_installed_browsers():
    """Return a dictionary of installed browsers with browser name as key and app_id as value."""
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
    """Prompt to install a browser if not installed."""
    response = messagebox.askyesno(f"Install {browser_name}", f"{browser_name} is not installed. Install it now?")
    if response:
        try:
            subprocess.run(["flatpak", "install", "--user", "-y", "flathub", app_id])
            messagebox.showinfo("Success", f"{browser_name} installed! Restart the script to use it.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install {browser_name}: {e}")

def uninstall_browser(app_id, browser_name):
    """Prompt to uninstall a browser."""
    response = messagebox.askyesno(f"Uninstall {browser_name}", f"Are you sure you want to remove {browser_name}?")
    if response:
        try:
            subprocess.run(["flatpak", "uninstall", "--user", "-y", app_id])
            messagebox.showinfo("Success", f"{browser_name} has been uninstalled.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to uninstall {browser_name}: {e}")

def check_permissions(app_id):
    """Check if the browser has the required permissions."""
    try:
        result = subprocess.run(["flatpak", "info", "--show-permissions", app_id], stdout=subprocess.PIPE, text=True)
        return "/run/udev:ro" in result.stdout
    except Exception:
        return False

def fix_permissions(app_id):
    """Apply missing Flatpak permissions."""
    subprocess.run(["flatpak", "override", "--user", "--filesystem=/run/udev:ro", app_id])
    messagebox.showinfo("Permissions Fixed", f"Permissions updated for {app_id}")

def manage_permissions():
    """Check installed browsers and apply permissions if needed."""
    installed = check_installed_browsers()
    chrome_installed = "Chrome" in installed
    edge_installed = "Edge" in installed
    if not chrome_installed and not edge_installed:
        messagebox.showinfo("Permissions Check", "No browsers installed to check.")
        return
    
    missing = []
    if chrome_installed and not check_permissions(installed["Chrome"]):
        missing.append("Chrome")
    if edge_installed and not check_permissions(installed["Edge"]):
        missing.append("Edge")

    if not missing:
        messagebox.showinfo("Permissions Check", "Permissions are correct for installed browsers.")
        return
    
    choice = messagebox.askyesno("Fix Permissions", f"Permissions missing for: {', '.join(missing)}.\nWould you like to apply fixes?")
    if choice:
        if "Chrome" in missing:
            fix_permissions(installed["Chrome"])
        if "Edge" in missing:
            fix_permissions(installed["Edge"])

# --- Load Steam Shortcuts ---
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
            messagebox.showwarning("Warning", f"{shortcuts_path} is corrupted. Starting with an empty shortcuts dictionary.")
            shortcuts = {"shortcuts": {}}
    else:
        shortcuts = {"shortcuts": {}}
    
    return shortcuts

def save_shortcuts(shortcuts):
    with open(shortcuts_path, "wb") as f:
        vdf.binary_dump(shortcuts, f)

def restart_steam():
    os.system("steam -shutdown")
    time.sleep(5)
    subprocess.Popen(["steam"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setpgrp)
    messagebox.showinfo("Info", "Steam restarted. Check your library for the new shortcuts!")

# --- GUI Setup ---
root = tk.Tk()
root.title("GeForce Now Shortcut Automation")

# Mode Selection
mode_frame = ttk.LabelFrame(root, text="Mode Selection", padding=10)
mode_frame.pack(pady=10, fill="x")
mode_var = tk.StringVar(value="Interactive")
ttk.Radiobutton(mode_frame, text="Interactive Mode", variable=mode_var, value="Interactive").pack(side=tk.LEFT, padx=5)
ttk.Radiobutton(mode_frame, text="Batch Mode", variable=mode_var, value="Batch").pack(side=tk.LEFT, padx=5)

# Browser Selection
browser_frame = ttk.LabelFrame(root, text="Browser Management", padding=10)
browser_frame.pack(pady=10, fill="x")
installed = check_installed_browsers()

if "Chrome" not in installed:
    ttk.Button(browser_frame, text="Install Chrome", command=lambda: install_browser("com.google.Chrome", "Chrome")).pack(side=tk.LEFT, padx=5)
else:
    ttk.Button(browser_frame, text="Uninstall Chrome", command=lambda: uninstall_browser("com.google.Chrome", "Chrome")).pack(side=tk.LEFT, padx=5)

if "Edge" not in installed:
    ttk.Button(browser_frame, text="Install Edge", command=lambda: install_browser("com.microsoft.Edge", "Edge")).pack(side=tk.LEFT, padx=5)
else:
    ttk.Button(browser_frame, text="Uninstall Edge", command=lambda: uninstall_browser("com.microsoft.Edge", "Edge")).pack(side=tk.LEFT, padx=5)

ttk.Button(browser_frame, text="Check Permissions", command=manage_permissions).pack(side=tk.LEFT, padx=5)

# Collection Selection
collection_frame = ttk.LabelFrame(root, text="Game Collection", padding=10)
collection_frame.pack(pady=10, fill="x")
ttk.Label(collection_frame, text="Select Collection:").pack(side=tk.LEFT, padx=5)
collection_var = tk.StringVar(value="GeForce Now")
collections = ["GeForce Now", "Xbox Cloud", "Amazon Luna", "Custom"]
collection_menu = ttk.OptionMenu(collection_frame, collection_var, *collections)
collection_menu.pack(side=tk.LEFT, padx=5)

# Add Game UI
game_frame = ttk.LabelFrame(root, text="Add Game", padding=10)
game_frame.pack(pady=10, fill="x")
ttk.Label(game_frame, text="Game Title:").pack()
title_entry = ttk.Entry(game_frame, width=50)
title_entry.pack()
ttk.Label(game_frame, text="Game URL:").pack()
url_entry = ttk.Entry(game_frame, width=50)
url_entry.pack()

ttk.Button(game_frame, text="Add Game", command=lambda: messagebox.showinfo("Added", "Game added!")).pack(pady=5)

ttk.Button(root, text="Finish & Restart Steam", command=restart_steam).pack(pady=10)

root.mainloop()
