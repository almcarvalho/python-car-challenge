import requests

ip_encontrado = None

for i in range(1, 101):
    ip = f"10.0.0.{i}"

    try:
        url = f"http://{ip}:80/health"

        response = requests.get(url, timeout=2)

        print(f"[{ip}] Status Code: {response.status_code}")
        print(f"[{ip}] Resposta: {response.text}")

        if response.status_code == 200:
            ip_encontrado = ip
            print(f"\nIP ENCONTRADO: {ip}")
            break

    except Exception as e:
        print(f"[{ip}] Erro: {e}")

print("\n========== RESULTADO FINAL ==========")

if ip_encontrado:
    print(f"IP que respondeu 200: {ip_encontrado}")
else:
    print("Nenhum IP respondeu com status 200")