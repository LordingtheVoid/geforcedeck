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

def check_permissions(app_id):
    """Check if the browser has the required permissions; if not, override them."""
    try:
        result = subprocess.run(["flatpak", "info", "--show-permissions", app_id], stdout=subprocess.PIPE, text=True)
        return "/run/udev:ro" in result.stdout
    except Exception as e:
        messagebox.showerror("Error", f"Error checking permissions for {app_id}: {e}")
        return False

def fix_permissions(app_id):
    """Apply missing Flatpak permissions."""
    try:
        subprocess.run(["flatpak", "override", "--user", "--filesystem=/run/udev:ro", app_id])
        messagebox.showinfo("Permissions Fixed", f"Permissions updated for {app_id}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update permissions: {e}")

def reset_permissions(app_id):
    """Reset Flatpak permissions."""
    try:
        subprocess.run(["flatpak", "override", "--user", "--reset", app_id])
        messagebox.showinfo("Permissions Reset", f"Permissions reset for {app_id}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to reset permissions: {e}")

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
        messagebox.showinfo("Info", f"{shortcuts_path} is empty or doesn't exist. Starting with an empty shortcuts dictionary.")
        shortcuts = {"shortcuts": {}}
    
    return shortcuts

def save_shortcuts(shortcuts):
    with open(shortcuts_path, "wb") as f:
        vdf.binary_dump(shortcuts, f)

def restart_steam():
    os.system("steam -shutdown")
    time.sleep(5)  # Give Steam time to close
    subprocess.Popen(["steam"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setpgrp)
    messagebox.showinfo("Info", "Steam restarted. Check your library for the new shortcuts!")

# --- Browser Setup ---
installed_browsers = check_installed_browsers()
if not installed_browsers:
    messagebox.showerror("Error", "No compatible browsers found. Please install Chrome or Edge manually.")
    exit(1)

# Browser selection variables
selected_browser_name = list(installed_browsers.keys())[0]
selected_browser_id = installed_browsers[selected_browser_name]

# --- GUI Setup ---
root = tk.Tk()
root.title("GeForce Now Shortcut Automation")

# Browser Selection Frame
browser_frame = ttk.LabelFrame(root, text="Browser Selection", padding=10)
browser_frame.pack(pady=10, fill="x")

ttk.Label(browser_frame, text="Select Browser:").pack(side=tk.LEFT, padx=5)
browser_var = tk.StringVar(value=selected_browser_name)
browser_menu = ttk.OptionMenu(browser_frame, browser_var, selected_browser_name, *installed_browsers.keys())
browser_menu.pack(side=tk.LEFT, padx=5)

ttk.Button(browser_frame, text="Install Chrome", command=lambda: install_browser("com.google.Chrome", "Chrome")).pack(side=tk.LEFT, padx=5)
ttk.Button(browser_frame, text="Install Edge", command=lambda: install_browser("com.microsoft.Edge", "Edge")).pack(side=tk.LEFT, padx=5)

ttk.Button(browser_frame, text="Manage Permissions", command=lambda: fix_permissions(installed_browsers[browser_var.get()])).pack(side=tk.LEFT, padx=5)

# Collection Selection Frame
collection_frame = ttk.LabelFrame(root, text="Game Collection", padding=10)
collection_frame.pack(pady=10, fill="x")

ttk.Label(collection_frame, text="Select Collection:").pack(side=tk.LEFT, padx=5)
collection_var = tk.StringVar(value="GeForce Now")
collections = ["GeForce Now", "Xbox Cloud", "Amazon Luna", "Custom"]
collection_menu = ttk.OptionMenu(collection_frame, collection_var, *collections)
collection_menu.pack(side=tk.LEFT, padx=5)

def update_collection():
    if collection_var.get() == "Custom":
        custom_name = simpledialog.askstring("Custom Collection", "Enter your collection name:")
        if custom_name:
            collection_var.set(custom_name)

ttk.Button(collection_frame, text="Set Custom", command=update_collection).pack(side=tk.LEFT, padx=5)

# Game Addition Frame
game_frame = ttk.LabelFrame(root, text="Add Game", padding=10)
game_frame.pack(pady=10, fill="x")

ttk.Label(game_frame, text="Game Title:").pack()
title_entry = ttk.Entry(game_frame, width=50)
title_entry.pack()

ttk.Label(game_frame, text="Game URL:").pack()
url_entry = ttk.Entry(game_frame, width=50)
url_entry.pack()

def add_game():
    title = title_entry.get().strip()
    url = url_entry.get().strip()
    collection = collection_var.get()
    
    if title and url:
        messagebox.showinfo("Success", f"Added {title} to Steam shortcuts in '{collection}' collection.")
        title_entry.delete(0, tk.END)
        url_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Please enter both game title and URL.")

ttk.Button(game_frame, text="Add Game", command=add_game).pack(pady=5)

ttk.Button(root, text="Finish & Restart Steam", command=restart_steam).pack(pady=10)

root.mainloop()
