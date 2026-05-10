import tkinter as tk
import requests
import threading
import cv2
from PIL import Image, ImageTk

CAMERA_INDEX = 0

ESP_IP = "10.0.0.31"
PORTA = 80

URL_BASE = f"http://{ESP_IP}:{PORTA}"

# =========================
# CAMERA
# =========================

cap = cv2.VideoCapture(CAMERA_INDEX)

# =========================
# FUNCOES
# =========================

def atualizar_camera():
    ret, frame = cap.read()

    if ret:
        largura = root.winfo_width()
        altura = root.winfo_height() - 120

        if largura < 100:
            largura = 1280

        if altura < 100:
            altura = 720

        frame = cv2.resize(frame, (largura, altura))

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        imagem = Image.fromarray(frame_rgb)

        imgtk = ImageTk.PhotoImage(image=imagem)

        label_camera.imgtk = imgtk
        label_camera.configure(image=imgtk)

    root.after(10, atualizar_camera)

def enviar_comando(direcao):
    try:
        tempo = tempo_motor.get()

        url = f"{URL_BASE}/{direcao}/{tempo}"

        response = requests.get(url, timeout=1)

        console.insert(tk.END, f"{direcao.upper()} -> {response.status_code}\n")
        console.see(tk.END)

    except Exception as e:
        console.insert(tk.END, f"Erro: {e}\n")
        console.see(tk.END)

def thread_comando(direcao):
    threading.Thread(
        target=enviar_comando,
        args=(direcao,),
        daemon=True
    ).start()

def verificar_status():
    try:
        response = requests.get(f"{URL_BASE}/health", timeout=1)

        if response.status_code == 200:
            canvas_status.itemconfig(status_circle, fill="green")
            label_status.config(text="ONLINE")
        else:
            canvas_status.itemconfig(status_circle, fill="red")
            label_status.config(text="OFFLINE")

    except:
        canvas_status.itemconfig(status_circle, fill="red")
        label_status.config(text="OFFLINE")

    root.after(1000, verificar_status)

# =========================
# TECLADO
# =========================

def tecla_pressionada(event):
    tecla = event.keysym

    if tecla == "Up":
        thread_comando("front")

    elif tecla == "Left":
        thread_comando("left")

    elif tecla == "Right":
        thread_comando("right")

# =========================
# FECHAR
# =========================

def fechar():
    cap.release()
    root.destroy()

# =========================
# INTERFACE
# =========================

root = tk.Tk()

root.title("Controle Carrinho ESP32")

# TELA CHEIA
root.state("zoomed")

# TOPO
frame_topo = tk.Frame(root, bg="#222")
frame_topo.pack(fill=tk.X)

# STATUS
frame_status = tk.Frame(frame_topo, bg="#222")
frame_status.pack(side=tk.LEFT, padx=20, pady=10)

canvas_status = tk.Canvas(
    frame_status,
    width=30,
    height=30,
    highlightthickness=0,
    bg="#222"
)
canvas_status.pack(side=tk.LEFT)

status_circle = canvas_status.create_oval(
    5,
    5,
    25,
    25,
    fill="red"
)

label_status = tk.Label(
    frame_status,
    text="OFFLINE",
    fg="white",
    bg="#222",
    font=("Arial", 14, "bold")
)
label_status.pack(side=tk.LEFT, padx=10)

# ACELERACAO
frame_tempo = tk.Frame(frame_topo, bg="#222")
frame_tempo.pack(side=tk.LEFT, padx=20)

tk.Label(
    frame_tempo,
    text="Aceleração:",
    fg="white",
    bg="#222",
    font=("Arial", 14, "bold")
).pack(side=tk.LEFT)

tempo_motor = tk.Entry(
    frame_tempo,
    width=8,
    font=("Arial", 14)
)
tempo_motor.pack(side=tk.LEFT, padx=10)
tempo_motor.insert(0, "100")

# BOTOES
frame_botoes = tk.Frame(frame_topo, bg="#222")
frame_botoes.pack(side=tk.LEFT, padx=20)

btn_esquerda = tk.Button(
    frame_botoes,
    text="⬅ ESQUERDA",
    width=15,
    height=2,
    bg="#2196F3",
    fg="white",
    font=("Arial", 12, "bold"),
    command=lambda: thread_comando("left")
)
btn_esquerda.grid(row=0, column=0, padx=5)

btn_frente = tk.Button(
    frame_botoes,
    text="⬆ FRENTE",
    width=15,
    height=2,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 12, "bold"),
    command=lambda: thread_comando("front")
)
btn_frente.grid(row=0, column=1, padx=5)

btn_direita = tk.Button(
    frame_botoes,
    text="➡ DIREITA",
    width=15,
    height=2,
    bg="#FF9800",
    fg="white",
    font=("Arial", 12, "bold"),
    command=lambda: thread_comando("right")
)
btn_direita.grid(row=0, column=2, padx=5)

# CAMERA
label_camera = tk.Label(root, bg="black")
label_camera.pack(fill=tk.BOTH, expand=True)

# CONSOLE
console = tk.Text(
    root,
    height=5,
    bg="black",
    fg="lime",
    font=("Consolas", 10)
)
console.pack(fill=tk.X)

# EVENTOS TECLADO
root.bind("<Up>", tecla_pressionada)
root.bind("<Left>", tecla_pressionada)
root.bind("<Right>", tecla_pressionada)

# START
atualizar_camera()
verificar_status()

root.protocol("WM_DELETE_WINDOW", fechar)

root.mainloop()