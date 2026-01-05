import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import json
import shutil
import subprocess
from PIL import Image, ImageTk

EXECUTABLE_FILE_NAME = "Slipstream.exe"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_DIR = os.path.join(ROOT_DIR, "accounts")
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")
SOURCE_EXE = os.path.join(ROOT_DIR, EXECUTABLE_FILE_NAME)
BACKGROUND_IMAGE = os.path.join(ROOT_DIR, "background.png")

os.makedirs(ACCOUNTS_DIR, exist_ok=True)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"accounts": {}, "last_used": None}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Migration ancien format
        if "last_used" not in data:
            return {"accounts": data, "last_used": None}
        return data


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def add_account():
    if not os.path.exists(SOURCE_EXE):
        messagebox.showerror("Erreur", f"{EXECUTABLE_FILE_NAME} est introuvable à la racine.")
        return

    name = simpledialog.askstring("Nouveau compte", "Nom du compte :")
    if not name:
        return

    config = load_config()
    
    if name in config["accounts"]:
        messagebox.showerror("Erreur", "Ce compte existe déjà.")
        return

    account_dir = os.path.join(ACCOUNTS_DIR, name)
    os.makedirs(account_dir)

    exe_dest = os.path.join(account_dir, EXECUTABLE_FILE_NAME)
    shutil.copy(SOURCE_EXE, exe_dest)

    config["accounts"][name] = exe_dest
    if config["last_used"] is None:
        config["last_used"] = name
    save_config(config)

    update_ui()


def delete_account(name):
    config = load_config()

    if name not in config["accounts"]:
        return

    confirm = messagebox.askyesno(
        "Confirmation",
        f"Supprimer le compte '{name}' ?\n\nCette action est irréversible."
    )

    if not confirm:
        return

    account_dir = os.path.join(ACCOUNTS_DIR, name)

    try:
        if os.path.exists(account_dir):
            shutil.rmtree(account_dir)
    except Exception as e:
        messagebox.showerror("Erreur", str(e))
        return

    del config["accounts"][name]
    
    # Si on supprime le dernier compte utilisé
    if config["last_used"] == name:
        if config["accounts"]:
            config["last_used"] = list(config["accounts"].keys())[0]
        else:
            config["last_used"] = None
    
    save_config(config)
    update_ui()


def launch_account(name):
    config = load_config()
    
    if name not in config["accounts"]:
        messagebox.showerror("Erreur", "Compte introuvable.")
        return
        
    exe_path = config["accounts"][name]
    
    if not os.path.exists(exe_path):
        messagebox.showerror("Erreur", "Executable introuvable.")
        return

    config["last_used"] = name
    save_config(config)
    
    # Lancer le jeu sans fenêtre console
    subprocess.Popen(
        exe_path,
        cwd=os.path.dirname(exe_path),
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    
    # Fermer le launcher
    root.destroy()


def switch_account(name):
    config = load_config()
    config["last_used"] = name
    save_config(config)
    update_ui()


def toggle_dropdown():
    global dropdown_visible
    dropdown_visible = not dropdown_visible
    update_dropdown()


def update_dropdown():
    config = load_config()
    
    if dropdown_visible and len(config["accounts"]) > 1:
        # Afficher le dropdown
        accounts = [acc for acc in config["accounts"].keys() if acc != config["last_used"]]
        
        dropdown_height = len(accounts) * 50
        
        y_pos = 0
        for acc in accounts:
            btn = tk.Button(
                dropdown_frame,
                text=acc,
                font=("Arial", 12),
                bg="#2a2a4e",
                fg="white",
                activebackground="#3a3a6e",
                bd=0,
                padx=20,
                pady=10,
                anchor="w",
                command=lambda a=acc: [switch_account(a), toggle_dropdown()]
            )
            btn.place(x=0, y=y_pos, width=360, height=50)
            y_pos += 50
        
        # Placer le dropdown juste au-dessus du bouton principal
        dropdown_frame.place(x=420, y=520 - dropdown_height, width=360, height=dropdown_height)
    else:
        # Cacher le dropdown
        for widget in dropdown_frame.winfo_children():
            widget.destroy()
        dropdown_frame.place_forget()


def update_ui():
    config = load_config()
    last_used = config["last_used"]
    
    # Mettre à jour le bouton du dernier compte utilisé
    if last_used and last_used in config["accounts"]:
        # Cadre principal du compte
        account_btn_frame.configure(bg="#16213e")
        
        # Nom du compte (cliquable pour dropdown)
        name_btn.configure(
            text=last_used,
            state="normal",
            command=toggle_dropdown
        )
        
        # Bouton supprimer
        delete_btn.configure(
            state="normal",
            command=lambda: delete_account(last_used)
        )
        
        # Bouton lancer
        launch_btn.configure(
            state="normal",
            command=lambda: launch_account(last_used)
        )
    else:
        # Aucun compte
        account_btn_frame.configure(bg="#1a1a2e")
        name_btn.configure(text="Aucun compte", state="disabled", command=None)
        delete_btn.configure(state="disabled", command=None)
        launch_btn.configure(state="disabled", command=None)
    
    # Fermer le dropdown
    global dropdown_visible
    dropdown_visible = False
    update_dropdown()


# ---- Interface ----

root = tk.Tk()
root.title("Rocket League Launcher")
root.geometry("800x600")
root.resizable(False, False)

dropdown_visible = False

# Canvas pour l'image de fond
canvas = tk.Canvas(root, width=800, height=600, highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Charger et afficher l'image de fond
try:
    bg_image = Image.open(BACKGROUND_IMAGE)
    bg_image = bg_image.resize((800, 600), Image.Resampling.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_image)
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")
    canvas.image = bg_photo
except FileNotFoundError:
    canvas.configure(bg="#0a0e27")

# Bouton "Nouveau compte" (Bouton 2 - gris, en bas à gauche)
new_account_btn = tk.Button(
    root,
    text="Nouveau compte",
    font=("Arial", 12),
    bg="#4a4a6e",
    fg="white",
    activebackground="#5a5a7e",
    bd=2,
    relief="solid",
    padx=20,
    pady=15,
    command=add_account,
    cursor="hand2"
)
new_account_btn.place(x=20, y=520, width=360, height=60)

# Cadre principal du dernier compte utilisé (Bouton 1 - rose, en bas à droite)
account_btn_frame = tk.Frame(root, bg="#16213e", bd=3, relief="solid", highlightbackground="#ff1493", highlightthickness=2)
account_btn_frame.place(x=420, y=520, width=360, height=60)

# Partie gauche : Nom du compte (cliquable pour dropdown)
name_btn = tk.Button(
    account_btn_frame,
    text="Aucun compte",
    font=("Arial", 12, "bold"),
    bg="#16213e",
    fg="white",
    activebackground="#1a2540",
    bd=0,
    highlightthickness=0,
    anchor="w",
    padx=15,
    cursor="hand2"
)
name_btn.place(x=0, y=0, width=200, height=60)

# Partie centre : Bouton supprimer
delete_btn = tk.Button(
    account_btn_frame,
    text="🗑️",
    font=("Arial", 14),
    bg="#533483",
    fg="white",
    activebackground="#6a4a9a",
    bd=0,
    highlightthickness=0,
    cursor="hand2"
)
delete_btn.place(x=200, y=0, width=60, height=60)

# Partie droite : Bouton lancer
launch_btn = tk.Button(
    account_btn_frame,
    text="Lancer",
    font=("Arial", 11, "bold"),
    bg="#0f3460",
    fg="white",
    activebackground="#1a4a7a",
    bd=0,
    highlightthickness=0,
    cursor="hand2"
)
launch_btn.place(x=260, y=0, width=100, height=60)

# Frame pour le dropdown (liste déroulante)
dropdown_frame = tk.Frame(root, bg="#2a2a4e", bd=0, highlightthickness=0)

# Initialiser l'interface
update_ui()

# Cliquer ailleurs pour fermer le dropdown
def close_dropdown(event):
    global dropdown_visible
    if dropdown_visible:
        # Vérifier si le clic est en dehors du dropdown et du bouton nom
        widget = event.widget
        if widget not in [dropdown_frame, name_btn] and widget.master not in [dropdown_frame]:
            dropdown_visible = False
            update_dropdown()

root.bind("<Button-1>", close_dropdown)

root.mainloop()