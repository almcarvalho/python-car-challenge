import tkinter as tk
import requests
import threading
import cv2
import pyttsx3
import numpy as np
import time
from PIL import Image, ImageTk

CAMERA_INDEX = 0

ESP_IP = "10.0.0.31"
PORTA = 80

URL_BASE = f"http://{ESP_IP}:{PORTA}"

desafio_ativo = False
ultimo_frame = None

pos_carrinho = None
pos_bola = None
pos_alvo = None

# =========================
# VOZ DO SISTEMA
# =========================

voz = pyttsx3.init()
voz.setProperty('rate', 170)
voz.setProperty('volume', 1.0)

try:
    voices = voz.getProperty('voices')

    for v in voices:
        nome = str(v.name).lower()
        idioma = str(v.languages).lower()

        if (
            "english" in nome or
            "en-us" in nome or
            "en_us" in nome or
            "en" in idioma
        ):
            voz.setProperty('voice', v.id)
            break

except:
    pass

lock_voz = threading.Lock()

def falar(texto):
    def run():
        with lock_voz:
            try:
                voz.stop()
                voz.say(texto)
                voz.runAndWait()
            except:
                pass

    threading.Thread(
        target=run,
        daemon=True
    ).start()

# =========================
# CAMERA
# =========================

cap = cv2.VideoCapture(CAMERA_INDEX)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# =========================
# DETECCAO
# =========================

def detectar_objetos(frame):
    global pos_carrinho, pos_bola, pos_alvo

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Azul - carrinho
    azul_baixo = np.array([90, 80, 50])
    azul_alto = np.array([130, 255, 255])

    # Amarelo - bolinha
    amarelo_baixo = np.array([20, 80, 80])
    amarelo_alto = np.array([40, 255, 255])

    # Preto - quadrado
    preto_baixo = np.array([0, 0, 0])
    preto_alto = np.array([180, 255, 60])

    mascara_azul = cv2.inRange(hsv, azul_baixo, azul_alto)
    mascara_amarelo = cv2.inRange(hsv, amarelo_baixo, amarelo_alto)
    mascara_preto = cv2.inRange(hsv, preto_baixo, preto_alto)

    pos_carrinho = encontrar_centro(mascara_azul, frame, "CAR", (255, 0, 0))
    pos_bola = encontrar_centro(mascara_amarelo, frame, "BALL", (0, 255, 255))
    pos_alvo = encontrar_centro(mascara_preto, frame, "TARGET", (0, 0, 255))

    if pos_carrinho:
        cv2.circle(frame, pos_carrinho, 10, (255, 0, 0), -1)

    if pos_bola:
        cv2.circle(frame, pos_bola, 10, (0, 255, 255), -1)

    if pos_alvo:
        cv2.circle(frame, pos_alvo, 10, (0, 0, 255), -1)

    if pos_bola and pos_alvo:
        cv2.line(frame, pos_bola, pos_alvo, (255, 255, 255), 2)

    return frame

def encontrar_centro(mascara, frame, nome, cor):
    contornos, _ = cv2.findContours(
        mascara,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contornos:
        return None

    maior = max(contornos, key=cv2.contourArea)

    area = cv2.contourArea(maior)

    if area < 300:
        return None

    x, y, w, h = cv2.boundingRect(maior)

    centro_x = x + w // 2
    centro_y = y + h // 2

    cv2.rectangle(
        frame,
        (x, y),
        (x + w, y + h),
        cor,
        3
    )

    cv2.putText(
        frame,
        nome,
        (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        cor,
        2
    )

    return (centro_x, centro_y)

# =========================
# FUNCOES
# =========================

def atualizar_camera():
    global ultimo_frame

    ret, frame = cap.read()

    if ret:
        largura_tela = root.winfo_width()
        altura_tela = root.winfo_height()

        if largura_tela < 300:
            largura_tela = 1280

        if altura_tela < 300:
            altura_tela = 720

        altura_disponivel = altura_tela - 180
        tamanho = min(largura_tela, altura_disponivel)

        if tamanho < 100:
            tamanho = 600

        h, w, _ = frame.shape
        lado = min(h, w)

        x_inicio = (w // 2) - (lado // 2)
        y_inicio = (h // 2) - (lado // 2)

        frame = frame[
            y_inicio:y_inicio + lado,
            x_inicio:x_inicio + lado
        ]

        frame = cv2.resize(frame, (tamanho, tamanho))

        frame = detectar_objetos(frame)

        ultimo_frame = frame.copy()

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

        if direcao == "front":
            falar("MOVING CAR FRONT")

        elif direcao == "left":
            falar("MOVING CAR LEFT")

        elif direcao == "right":
            falar("MOVING CAR RIGHT")

        console.insert(
            tk.END,
            f"{direcao.upper()} -> {response.status_code}\n"
        )

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
        response = requests.get(
            f"{URL_BASE}/health",
            timeout=1
        )

        if response.status_code == 200:
            canvas_status.itemconfig(
                status_circle,
                fill="green"
            )

            label_status.config(text="ONLINE")

        else:
            canvas_status.itemconfig(
                status_circle,
                fill="red"
            )

            label_status.config(text="OFFLINE")

    except:
        canvas_status.itemconfig(
            status_circle,
            fill="red"
        )

        label_status.config(text="OFFLINE")

    root.after(1000, verificar_status)

# =========================
# DESAFIO
# =========================

def iniciar_desafio():
    global desafio_ativo

    if desafio_ativo:
        return

    desafio_ativo = True

    falar("STARTING CHALLENGE")

    console.insert(tk.END, "DESAFIO INICIADO\n")
    console.see(tk.END)

    threading.Thread(
        target=executar_desafio,
        daemon=True
    ).start()

def parar_desafio():
    global desafio_ativo

    desafio_ativo = False

    console.insert(tk.END, "DESAFIO PARADO\n")
    console.see(tk.END)

def executar_desafio():
    global desafio_ativo

    while desafio_ativo:
        if pos_carrinho is None or pos_bola is None or pos_alvo is None:
            console.insert(
                tk.END,
                "Procurando carrinho, bola e alvo...\n"
            )
            console.see(tk.END)

            time.sleep(1)
            continue

        bola_x, bola_y = pos_bola
        alvo_x, alvo_y = pos_alvo

        erro_x = alvo_x - bola_x
        erro_y = alvo_y - bola_y

        distancia = ((erro_x ** 2) + (erro_y ** 2)) ** 0.5

        if distancia < 40:
            falar("CHALLENGE COMPLETE")
            console.insert(tk.END, "BOLA CHEGOU NO ALVO\n")
            console.see(tk.END)
            desafio_ativo = False
            break

        if abs(erro_x) > 50:
            if erro_x > 0:
                thread_comando("right")
            else:
                thread_comando("left")

            time.sleep(0.8)

        else:
            thread_comando("front")
            time.sleep(0.8)

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
    global desafio_ativo

    desafio_ativo = False

    cap.release()
    root.destroy()

# =========================
# INTERFACE
# =========================

root = tk.Tk()

root.title("Controle Carrinho ESP32")

root.state("zoomed")

# =========================
# TOPO
# =========================

frame_topo = tk.Frame(
    root,
    bg="#222",
    height=80
)

frame_topo.pack(fill=tk.X)

# STATUS

frame_status = tk.Frame(
    frame_topo,
    bg="#222"
)

frame_status.pack(
    side=tk.LEFT,
    padx=20,
    pady=10
)

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

label_status.pack(
    side=tk.LEFT,
    padx=10
)

# ACELERACAO

frame_tempo = tk.Frame(
    frame_topo,
    bg="#222"
)

frame_tempo.pack(
    side=tk.LEFT,
    padx=20
)

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

tempo_motor.pack(
    side=tk.LEFT,
    padx=10
)

tempo_motor.insert(0, "100")

# BOTOES

frame_botoes = tk.Frame(
    frame_topo,
    bg="#222"
)

frame_botoes.pack(
    side=tk.LEFT,
    padx=20
)

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

btn_esquerda.grid(
    row=0,
    column=0,
    padx=5
)

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

btn_frente.grid(
    row=0,
    column=1,
    padx=5
)

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

btn_direita.grid(
    row=0,
    column=2,
    padx=5
)

btn_desafio = tk.Button(
    frame_botoes,
    text="🔴 INICIAR DESAFIO",
    width=18,
    height=2,
    bg="red",
    fg="white",
    font=("Arial", 12, "bold"),
    command=iniciar_desafio
)

btn_desafio.grid(
    row=0,
    column=3,
    padx=5
)

btn_parar = tk.Button(
    frame_botoes,
    text="PARAR DESAFIO",
    width=15,
    height=2,
    bg="#555",
    fg="white",
    font=("Arial", 12, "bold"),
    command=parar_desafio
)

btn_parar.grid(
    row=0,
    column=4,
    padx=5
)

# =========================
# CAMERA
# =========================

frame_camera = tk.Frame(
    root,
    bg="black"
)

frame_camera.pack(
    fill=tk.BOTH,
    expand=True
)

label_camera = tk.Label(
    frame_camera,
    bg="black"
)

label_camera.pack(expand=True)

# =========================
# CONSOLE
# =========================

console = tk.Text(
    root,
    height=5,
    bg="black",
    fg="lime",
    font=("Consolas", 10)
)

console.pack(fill=tk.X)

# =========================
# TECLAS
# =========================

root.bind("<Up>", tecla_pressionada)
root.bind("<Left>", tecla_pressionada)
root.bind("<Right>", tecla_pressionada)

# =========================
# START
# =========================

atualizar_camera()
verificar_status()

root.protocol(
    "WM_DELETE_WINDOW",
    fechar
)

root.mainloop()