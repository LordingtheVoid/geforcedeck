import vdf
import os
import time
import subprocess

def list_to_dict(lst):
    """Convert a list to a dictionary with numeric keys."""
    return {str(i): item for i, item in enumerate(lst)}

# Find the shortcuts.vdf path
userdata_path = "/home/deck/.local/share/Steam/userdata"
user_ids = [d for d in os.listdir(userdata_path) if os.path.isdir(os.path.join(userdata_path, d))]
if len(user_ids) == 1:
    user_id = user_ids[0]
else:
    print("Multiple user IDs found, please specify.")
    exit(1)
shortcuts_path = os.path.join(userdata_path, user_id, "config", "shortcuts.vdf")

# Load or initialize shortcuts
if os.path.exists(shortcuts_path) and os.path.getsize(shortcuts_path) > 0:
    try:
        with open(shortcuts_path, "rb") as f:
            shortcuts_dict = vdf.binary_load(f)
    except SyntaxError:
        print(f"Error: {shortcuts_path} is corrupted. Starting with an empty shortcuts dictionary.")
        shortcuts_dict = {"shortcuts": {}}
else:
    print(f"{shortcuts_path} is empty or doesn’t exist. Starting with an empty shortcuts dictionary.")
    shortcuts_dict = {"shortcuts": {}}

# Find existing Chrome entry
chrome_entry = None
for key, entry in shortcuts_dict.get('shortcuts', {}).items():
    app_name = entry.get('appname', '').lower()
    if 'chrome' in app_name:
        chrome_entry = entry
        break

if chrome_entry is None:
    print("No Chrome entry found. Please add Chrome manually as a non-Steam game first.")
    exit(1)

exe = chrome_entry['exe']
start_dir = chrome_entry['StartDir']

# Function to add a game entry
def add_game(game_title, game_url, shortcuts_dict):
    launch_options = (
        f'run --branch=stable --arch=x86_64 --command=/app/bin/chrome --file-forwarding '
        f'com.google.Chrome @@u @@ --window-size=1024,640 --force-device-scale-factor=1.25 '
        f'--device-scale-factor=1.25 --kiosk "{game_url}"'
    )
    existing_keys = [int(k) for k in shortcuts_dict['shortcuts'].keys() if k.isdigit()]
    new_key = str(max(existing_keys) + 1) if existing_keys else "0"
    new_entry = {
        "appname": game_title,
        "exe": exe,
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
        # Convert the tags list to a dictionary for vdf.binary_dump
        "tags": list_to_dict(["GeForce Now"])
    }
    shortcuts_dict['shortcuts'][new_key] = new_entry
    return True

# Ask if batch mode should be used
batch_mode = input("Run batch file (batchadd.txt)? (yes/no): ").lower() == 'yes'

if batch_mode:
    batch_file = "batchadd.txt"
    backup_file = "batchbackup.txt"
    if not os.path.exists(batch_file):
        print(f"Error: {batch_file} not found in the current directory.")
        exit(1)

    # Scan and preview games
    to_add = []
    to_skip = []
    with open(batch_file, "r") as f:
        lines = f.readlines()
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

    # Show preview
    if to_add:
        print("\nGames to be added:")
        for title, url, _ in to_add:
            print(f"  {title}: {url}")
    else:
        print("\nNo valid games to add.")
    if to_skip:
        print("\nGames to be skipped (no URL or malformed):")
        for title in to_skip:
            print(f"  {title}")

    # Confirm
    if to_add:
        confirm = input("\nProceed with adding these games? (yes/no): ").lower()
        if confirm == 'yes':
            added_count = 0
            # Add games to shortcuts
            for game_title, game_url, _ in to_add:
                add_game(game_title, game_url, shortcuts_dict)
                print(f"Added {game_title} to Steam shortcuts.")
                added_count += 1
            
            # Update batchadd.txt (remove added lines)
            remaining_lines = [line for line in lines if line.strip() not in [entry[2] for entry in to_add]]
            with open(batch_file, "w") as f:
                f.writelines(remaining_lines)
            
            # Append to batchbackup.txt
            with open(backup_file, "a") as f:
                for _, _, original_line in to_add:
                    f.write(original_line + "\n")
            
            print(f"\nAdded {added_count} shortcuts. Updated {batch_file} and {backup_file}.")
        else:
            print("Batch addition canceled.")
    else:
        print("Nothing to add. Exiting.")
else:
    # Interactive multi-entry mode
    added_count = 0
    while True:
        game_title = input("Enter the game title: ")
        game_url = input("Enter the GeForce Now URL for the game: ")
        
        if game_url:  # Only add if URL is provided
            add_game(game_title, game_url, shortcuts_dict)
            print(f"Added {game_title} to Steam shortcuts.")
            added_count += 1
        else:
            print(f"Skipped {game_title} (no URL provided).")

        more = input("Add another game? (yes/no): ").lower()
        if more != 'yes':
            break
    print(f"\nAdded {added_count} shortcuts.")

# Save shortcuts
with open(shortcuts_path, "wb") as f:
    vdf.binary_dump(shortcuts_dict, f)

print("All shortcuts saved. Restarting Steam...")

# Restart Steam automatically
os.system("steam -shutdown")
time.sleep(5)  # Wait briefly to ensure Steam closes

# Launch Steam detached using subprocess to avoid interactive restart prompt
subprocess.Popen(
    ["steam"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    preexec_fn=os.setpgrp
)

print("Steam restarted. Check your library for the new shortcuts!")
