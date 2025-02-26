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

def list_to_dict(lst):
    """Convert a list to a dictionary with numeric keys."""
    return {str(i): item for i, item in enumerate(lst)}

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

def install_browser(app_id, browser_name):
    """Install missing browser."""
    if messagebox.askyesno(f"Install {browser_name}", f"{browser_name} is not installed. Install it now?"):
        subprocess.run(["flatpak", "install", "--user", "-y", "flathub", app_id])
        messagebox.showinfo("Success", f"{browser_name} installed! Restart the script to use it.")

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

def manage_permissions():
    """Check installed browsers & apply fixes if needed."""
    installed = check_installed_browsers()
    missing = [b for b in installed if not check_permissions(installed[b])]
    
    if not missing:
        messagebox.showinfo("Permissions Check", "Permissions are correct for installed browsers.")
        return
    
    choice = messagebox.askyesno("Fix Permissions", f"Permissions missing for: {', '.join(missing)}.\nApply fixes?")
    if choice:
        for browser in missing:
            fix_permissions(installed[browser])

def is_steam_running():
    """Check if Steam is running before restarting."""
    result = subprocess.run(["pgrep", "-x", "steam"], stdout=subprocess.PIPE)
    return result.returncode == 0

def restart_steam():
    """Restart Steam only if it's running."""
    if is_steam_running():
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

def save_shortcuts(shortcuts):
    with open(shortcuts_path, "wb") as f:
        vdf.binary_dump(shortcuts, f)

# --- GUI Setup ---
root = tk.Tk()
root.title("GeForce Now Shortcut Automation")

# Load preferences
last_browser, last_collection = load_config()

# Browser Selection
browser_frame = ttk.LabelFrame(root, text="Browser Management", padding=10)
browser_frame.pack(pady=10, fill="x")
installed = check_installed_browsers()

browser_var = tk.StringVar(value=last_browser)
browser_menu = ttk.OptionMenu(browser_frame, browser_var, *installed.keys())
browser_menu.pack(side=tk.LEFT, padx=5)

ttk.Button(browser_frame, text="Check Permissions", command=manage_permissions).pack(side=tk.LEFT, padx=5)

# Collection Selection
collection_frame = ttk.LabelFrame(root, text="Game Collection", padding=10)
collection_frame.pack(pady=10, fill="x")

collections = ["GeForce Now", "Xbox Cloud", "Amazon Luna", "Custom"]
collection_var = tk.StringVar(value=last_collection)
collection_menu = ttk.OptionMenu(collection_frame, collection_var, *collections)
collection_menu.pack(side=tk.LEFT, padx=5)

def update_collection():
    if collection_var.get() == "Custom":
        custom_name = simpledialog.askstring("Custom Collection", "Enter your collection name:")
        if custom_name:
            collection_var.set(custom_name)

ttk.Button(collection_frame, text="Set Custom", command=update_collection).pack(side=tk.LEFT, padx=5)

# Batch Mode Preview
batch_frame = ttk.LabelFrame(root, text="Batch Mode Preview", padding=10)
batch_frame.pack(pady=10, fill="x")

batch_preview = tk.Text(batch_frame, width=70, height=10, state=tk.DISABLED)
batch_preview.pack()

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

load_batch_preview()

# Restart Steam Button
ttk.Button(root, text="Finish & Restart Steam", command=lambda: [save_config(browser_var.get(), collection_var.get()), restart_steam()]).pack(pady=10)

root.mainloop()
