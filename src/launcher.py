import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import json
import shutil
import subprocess
from PIL import Image, ImageTk

# ---------------- CONFIG ----------------

EXECUTABLE_FILE_NAME = "Slipstream.exe"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_DIR = os.path.join(ROOT_DIR, "accounts")
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")
SOURCE_EXE = os.path.join(ROOT_DIR, EXECUTABLE_FILE_NAME)
BACKGROUND_IMAGE = os.path.join(ROOT_DIR, "background.png")

os.makedirs(ACCOUNTS_DIR, exist_ok=True)

# ---------------- CONFIG FILE ----------------

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"accounts": {}, "last_used": None}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---------------- LOGIC ----------------

def add_account():
    if not os.path.exists(SOURCE_EXE):
        messagebox.showerror("Erreur", "Slipstream.exe introuvable")
        return

    name = simpledialog.askstring("Nouveau compte", "Nom du compte :")
    if not name:
        return

    config = load_config()
    if name in config["accounts"]:
        messagebox.showerror("Erreur", "Compte déjà existant")
        return

    account_dir = os.path.join(ACCOUNTS_DIR, name)
    os.makedirs(account_dir)
    exe_dest = os.path.join(account_dir, EXECUTABLE_FILE_NAME)
    shutil.copy(SOURCE_EXE, exe_dest)

    config["accounts"][name] = exe_dest
    config["last_used"] = config["last_used"] or name
    save_config(config)
    update_ui()

def delete_account():
    config = load_config()
    name = config["last_used"]
    if not name:
        return

    if not messagebox.askyesno("Confirmation", f"Supprimer '{name}' ?"):
        return

    shutil.rmtree(os.path.join(ACCOUNTS_DIR, name), ignore_errors=True)
    del config["accounts"][name]
    config["last_used"] = next(iter(config["accounts"]), None)
    save_config(config)
    close_dropdown()
    update_ui()

def launch_account():
    config = load_config()
    name = config["last_used"]
    if not name:
        return

    exe = config["accounts"][name]
    subprocess.Popen(
        exe,
        cwd=os.path.dirname(exe),
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )
    root.destroy()

def switch_account(name):
    config = load_config()
    config["last_used"] = name
    save_config(config)
    close_dropdown()
    update_ui()

# ---------------- UI ----------------

root = tk.Tk()
root.title("Rocket League Launcher")
root.geometry("800x600")
root.resizable(False, False)

canvas = tk.Canvas(root, width=800, height=600, highlightthickness=0)
canvas.pack()

# Background
try:
    bg = Image.open(BACKGROUND_IMAGE).resize((800, 600))
    bg_img = ImageTk.PhotoImage(bg)
    canvas.create_image(0, 0, image=bg_img, anchor="nw")
except:
    canvas.configure(bg="#0a0e27")

dropdown_visible = False
dropdown_items = []
dropdown_area = (0, 0, 0, 0)  # zone clic dropdown
name_button_area = (0, 0, 0, 0)  # zone clic nom du compte

# ---------------- DRAW BUTTONS ----------------

def draw_button(x1, y1, x2, y2, text, command, anchor="center"):
    rect = canvas.create_rectangle(x1, y1, x2, y2, fill="", outline="", tags="ui")
    txt = canvas.create_text(
        (x1 + x2)//2, (y1 + y2)//2,
        text=text,
        font=("Arial", 12, "bold"),
        fill="white",
        anchor=anchor,
        tags="ui"
    )
    canvas.tag_bind(rect, "<Button-1>", lambda e: command())
    canvas.tag_bind(txt, "<Button-1>", lambda e: command())
    return rect, txt

# ---------------- DROPDOWN ----------------

def toggle_dropdown():
    global dropdown_visible
    dropdown_visible = not dropdown_visible
    draw_dropdown()

def close_dropdown():
    global dropdown_visible, dropdown_items
    if dropdown_visible:
        dropdown_visible = False
        for i in dropdown_items:
            canvas.delete(i)
        dropdown_items = []

def draw_dropdown():
    global dropdown_items, dropdown_area
    for i in dropdown_items:
        canvas.delete(i)
    dropdown_items = []

    if not dropdown_visible:
        dropdown_area = (0, 0, 0, 0)
        return

    config = load_config()
    accounts = [a for a in config["accounts"] if a != config["last_used"]]
    if not accounts:
        dropdown_area = (0, 0, 0, 0)
        return

    x1, y1 = 420, 520 - len(accounts)*45
    x2, y2 = 620, 520
    dropdown_area = (x1, y1, x2, y2)

    y = y1
    for acc in accounts:
        r = canvas.create_rectangle(x1, y, x2, y+45, fill="#111", outline="white", tags="ui")
        t = canvas.create_text(x1+10, y+22, text=acc, fill="white", anchor="w", tags="ui")
        canvas.tag_bind(r, "<Button-1>", lambda e, a=acc: switch_account(a))
        canvas.tag_bind(t, "<Button-1>", lambda e, a=acc: switch_account(a))
        dropdown_items.extend([r, t])
        y += 45

# ---------------- UPDATE UI ----------------

def update_ui():
    global name_button_area
    canvas.delete("ui")
    config = load_config()
    name = config["last_used"] or "Aucun compte"

    # Nouveau compte
    draw_button(20, 520, 380, 580, "New Account", add_account)

    # Nom compte (dropdown)
    rect, txt = draw_button(420, 520, 620, 580, name, toggle_dropdown, anchor="w")
    canvas.coords(txt, 435, 550)
    name_button_area = (420, 520, 620, 580)  # zone pour toggle

    # Delete
    draw_button(620, 520, 680, 580, "🗑️", delete_account)

    # Launch
    draw_button(680, 520, 780, 580, "Start", launch_account)

    draw_dropdown()

# ---------------- CLICK OUTSIDE ----------------

def on_canvas_click(event):
    global dropdown_visible
    x, y = event.x, event.y
    x1, y1, x2, y2 = dropdown_area
    nx1, ny1, nx2, ny2 = name_button_area

    # Si clic hors dropdown ET hors nom du compte
    if dropdown_visible and not (x1 <= x <= x2 and y1 <= y <= y2) and not (nx1 <= x <= nx2 and ny1 <= y <= ny2):
        close_dropdown()
        update_ui()

canvas.bind("<Button-1>", on_canvas_click, add="+")

update_ui()
root.mainloop()
