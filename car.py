import tkinter as tk
import requests
import threading
import cv2
from PIL import Image, ImageTk

CAMERA_INDEX = 0

ESP_IP = "10.0.0.31"
PORTA = 80

URL_BASE = f"http://{ESP_IP}:{PORTA}"

LARGURA_CAMERA = 900
ALTURA_CAMERA = 650

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, LARGURA_CAMERA)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTURA_CAMERA)

def atualizar_camera():
    ret, frame = cap.read()

    if ret:
        frame = cv2.resize(frame, (LARGURA_CAMERA, ALTURA_CAMERA))
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

def fechar():
    cap.release()
    root.destroy()

root = tk.Tk()
root.title("Controle Carrinho ESP32")
root.geometry("1000x850")
root.resizable(False, False)

# TOPO
frame_topo = tk.Frame(root)
frame_topo.pack(pady=10)

# STATUS
frame_status = tk.Frame(frame_topo)
frame_status.grid(row=0, column=0, padx=15)

canvas_status = tk.Canvas(frame_status, width=30, height=30, highlightthickness=0)
canvas_status.pack(side=tk.LEFT)

status_circle = canvas_status.create_oval(5, 5, 25, 25, fill="red")

label_status = tk.Label(
    frame_status,
    text="OFFLINE",
    font=("Arial", 12, "bold")
)
label_status.pack(side=tk.LEFT, padx=5)

# ACELERACAO
frame_tempo = tk.Frame(frame_topo)
frame_tempo.grid(row=0, column=1, padx=15)

tk.Label(
    frame_tempo,
    text="Aceleração:",
    font=("Arial", 12, "bold")
).pack(side=tk.LEFT)

tempo_motor = tk.Entry(frame_tempo, width=8, font=("Arial", 12))
tempo_motor.pack(side=tk.LEFT, padx=5)
tempo_motor.insert(0, "100")

# BOTOES
frame_botoes = tk.Frame(frame_topo)
frame_botoes.grid(row=0, column=2, padx=15)

btn_esquerda = tk.Button(
    frame_botoes,
    text="ESQUERDA",
    width=12,
    height=2,
    bg="#2196F3",
    fg="white",
    font=("Arial", 11, "bold"),
    command=lambda: thread_comando("left")
)
btn_esquerda.grid(row=0, column=0, padx=5)

btn_frente = tk.Button(
    frame_botoes,
    text="FRENTE",
    width=12,
    height=2,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 11, "bold"),
    command=lambda: thread_comando("front")
)
btn_frente.grid(row=0, column=1, padx=5)

btn_direita = tk.Button(
    frame_botoes,
    text="DIREITA",
    width=12,
    height=2,
    bg="#FF9800",
    fg="white",
    font=("Arial", 11, "bold"),
    command=lambda: thread_comando("right")
)
btn_direita.grid(row=0, column=2, padx=5)

# CAMERA
label_camera = tk.Label(root)
label_camera.pack(pady=5)

# CONSOLE
console = tk.Text(root, height=5, width=110)
console.pack(pady=5)

atualizar_camera()
verificar_status()

root.protocol("WM_DELETE_WINDOW", fechar)
root.mainloop()