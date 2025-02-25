# GeForce Now Shortcut Automation for Steam Deck

Welcome to the GeForce Now Shortcut Automation project! This tool helps Steam Deck owners add GeForce Now games to their Steam library with custom launch options and a "GeForce Now" collection tag. Since Nvidia’s been dragging their feet on official Steam Deck support, this is about the best we can do as a community.

> **Note:**  
> The current Python implementation works well for automating game addition. A basic GUI version (using Tkinter) is also provided for easier interaction. While tagging (and thereby automatic collection grouping) isn’t perfect due to limitations with non-Steam game tagging, this script saves tons of time.  
>  
> **GUI version file:** `addgeforce_gui.py`

## Why This Exists

GeForce Now is awesome for playing PC games on your Steam Deck, but adding each game manually is a slog. This script automates that process a little, saving you time and sanity. It’s not perfect (thanks, Nvidia), but it’s a solid workaround to streamline your gaming setup.

## What We Need
- Nvidia needs to provide an API to easily grab games you want and provide URLs. At this time, every game must be found manually.
- Valve needs to improve the limitations with non-Steam game tagging to easily assign games to collections. [steam-shortcut-editor](https://github.com/tirish/steam-shortcut-editor) (Node.js based) seems like a solid solution, but for now a simple Python script works.

## Working Features
- **Batch Mode:** Add multiple games at once via `batchadd.txt`.
- **Interactive Mode:** Add games one-by-one with prompts.
- **GUI Version:** Use a simple graphical interface for both interactive and batch modes.
- **Steam Restart:** Automatically restarts Steam to refresh your library.
- **Backup:** Tracks added games in `batchbackup.txt` to avoid duplicates and save links for resets.
- **Tagging:** Attempts to add a "GeForce Now" tag for easy organization.

## Broken Features
- **Tagging:** Although a "GeForce Now" tag is added, due to Steam limitations non-Steam shortcuts may not automatically appear in the desired collection and thus no further customization is being developed

## Prerequisites

You’ll need:
- A Steam Deck (or similar) running SteamOS.
- Access to Desktop Mode.
- Chrome installed and added as a non-Steam game in Steam (see instructions below).
- Python 3 (SteamOS comes with Python) and the `vdf` module installed.

## Setup Instructions

### Step 1: Switch to Desktop Mode

- In Gaming Mode, go to **Power > Switch to Desktop**.

### Step 2: Install Chrome and Set Permissions

Chrome is essential for GeForce Now, and it needs specific permissions to work properly.

1. **Install Chrome**
    - Open the Discover Store (in the taskbar).
    - Search for "Chrome" and install it.
    
2. **Set Permissions**
    - Open Konsole (terminal) and run:
    
    ```bash
    flatpak --user override --filesystem=/run/udev:ro com.google.Chrome
    ```
    
This ensures Chrome has the right access to launch GeForce Now games.

### Step 3: Add Chrome to Steam

The script needs Chrome’s executable path, so let’s add it.

1. Open the menu in Desktop Mode.
2. Go to **Internet > Chrome > Right-Click (L2) > Add to Steam**.
3. Restart Steam.

### Step 4: Set Up Python

1. **Check Python**

    ```bash
    python3 --version
    ```
    
    Expect something like Python 3.11.7.
    
2. **Make a Directory**

    ```bash
    mkdir -p ~/Documents/Scripts
    cd ~/Documents/Scripts
    ```
    
3. **Set Up a Virtual Environment**

    ```bash
    python3 -m venv myenv
    ```
    
4. **Activate It**

    Run this every time you work with the script:
    
    ```bash
    source myenv/bin/activate
    ```
    
5. **Install vdf**

    For editing Steam’s shortcut file:
    
    ```bash
    pip install vdf
    ```

### Step 5: Backup Your Shortcuts File

Before running the script, it’s **highly recommended** to back up your `shortcuts.vdf` file. This file is where Steam stores your non-Steam shortcuts, and having a backup ensures you can restore your library if anything goes wrong.

1. Open Konsole (terminal) in Desktop Mode.
2. Locate your `shortcuts.vdf` file, typically found at:
    ```
    ~/.local/share/Steam/userdata/<STEAM_USER_ID>/config/shortcuts.vdf
    ```
3. Back it up by running a command like:
    ```bash
    cp ~/.local/share/Steam/userdata/<STEAM_USER_ID>/config/shortcuts.vdf ~/Documents/Scripts/shortcuts_backup.vdf
    ```
   Replace `<STEAM_USER_ID>` with your actual Steam user ID (the folder name in `userdata`).

### Step 6: Get the Script Ready

You’ll need the following files in `~/Documents/Scripts`:
- `addgeforce.py` (the CLI version)
- `addgeforce_gui.py` (the GUI version)
- `batchadd.txt`
- `batchbackup.txt` (if it doesn’t exist, create it with `touch batchbackup.txt`)

1. **Download**
    - Clone or download this repo and move the Python scripts to `~/Documents/Scripts/`.
    
2. **Create batchadd.txt**
    - For batch mode, list games like this:
    
    ```bash
    nano ~/Documents/Scripts/batchadd.txt
    ```
    
    **Example:**
    
    ```
    Cuphead: https://play.geforcenow.com/games?game-id=44a455e6-b60e-4016-b62a-d0c13052c8c2&lang=en_US&asset-id=01_c728aa54-5891-4fe5-a80d-5346028d6cff
    Cyberpunk 2077: https://play.geforcenow.com/games?game-id=another-id-here
    ```
    
    Save and exit (Ctrl+O, Enter, Ctrl+X).

3. **(Optional) Create batchbackup.txt**
    
    ```bash
    touch ~/Documents/Scripts/batchbackup.txt
    ```

### Step 7: Run the Script

You have two options:

#### Option A: Command-Line Interface (CLI) Version

1. **Navigate and Activate the Environment**

    ```bash
    cd ~/Documents/Scripts
    source myenv/bin/activate
    ```
    
2. **Run the Script**

    ```bash
    python3 addgeforce.py
    ```
    
    - **Batch Mode:** Respond "yes" to use `batchadd.txt`. Confirm after previewing; added games move to `batchbackup.txt`.
    - **Interactive Mode:** Respond "no" and then enter game titles and URLs manually.
    
3. **Steam Restarts:**  
   The script saves the shortcuts and automatically restarts Steam.

#### Option B: Graphical User Interface (GUI) Version

1. **Navigate and Activate the Environment**

    ```bash
    cd ~/Documents/Scripts
    source myenv/bin/activate
    ```
    
2. **Run the GUI Script**

    ```bash
    python3 addgeforce_gui.py
    ```
    
    - **Interactive Mode Tab:**  
      Enter the game title and URL (you can now paste the URL using Control‑V or right‑click), then click "Add Game" to add it.
      
    - **Batch Mode Tab:**  
      Load your `batchadd.txt` file, then click "Process Batch" to add all valid entries. The text area will display the results.
      
    - **Finish & Restart Steam:**  
      When done, click the finish button on either tab to save changes and restart Steam.

### Step 8: Check It Out

- **Library:** Your new games (e.g., "Cuphead") should appear in your Steam library.
- **Collections:** Look for "GeForce Now" (you may need to manually add the collection once).
- **Test:** Launch a game to confirm it redirects to GeForce Now.
- **Files:** Verify that `batchadd.txt` shrinks and `batchbackup.txt` grows as games are processed.

## How It Works

- **Batch Mode:**  
  Reads `batchadd.txt`, adds valid games (title + URL), then moves those entries to `batchbackup.txt`. This prevents duplicates and backs up your added games. If your Steam Deck gets wiped, simply copy `batchbackup.txt` back to `batchadd.txt` to re-add the shortcuts.

- **Interactive Mode:**  
  Adds games manually without touching the batch files.

- **GUI Version:**  
  A Tkinter-based interface allows you to add games interactively or via batch processing with a user-friendly interface, including improved URL pasting functionality.

## Optional: Customize with Decky or EmuDeck

Want your GeForce Now games to look slick with custom artwork? Try these optional tools:

- **Decky Loader:** A plugin loader for Steam Deck. Install the SteamGridDB plugin to set custom artwork for non-Steam games easily.  
  [Decky Loader GitHub](https://github.com/steam-deck-tools/decky-loader)
  
- **EmuDeck:** Focused on emulation, but it includes artwork management tools that can be adapted for non-Steam games.  
  [EmuDeck Website](https://www.emudeck.com)

Both are optional but can make your library pop!

## Troubleshooting

- **Chrome Issues:**  
  If Chrome doesn’t launch GeForce Now, re-run the permission command or reinstall Chrome.
  
- **Python Missing?**

    ```bash
    sudo steamos-readonly disable
    sudo pacman -Syu
    sudo pacman -S python
    sudo steamos-readonly enable
    ```
    
- **Keyring Woes?**

    ```bash
    sudo pacman-key --init
    sudo pacman-key --populate archlinux
    ```
    
- **Script Fails?**  
  Check the error—could be a typo or missing Chrome.

## Tips

- **Backup:**  
  Store your `batchbackup.txt` (and the `shortcuts.vdf` backup) somewhere safe (USB or cloud) for recovery. Batch mode cleans up `batchadd.txt` after processing and backs up added entries in `batchbackup.txt`.
  
- **URLs:**  
  Get them from [GeForce Now](https://play.geforcenow.com) by:
  - Searching for a game you own,
  - Clicking the box (and ensuring the URL changes),
  - Copying the URL.

## License

This project is licensed under the MIT License. It’s permissive and community-friendly—use it, tweak it, share it, just keep the license and copyright.

