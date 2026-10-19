import cv2
import easyocr
import re
import requests
import json
import time

print("Carregando leitor de placas local...")
reader = easyocr.Reader(['en'], gpu=False, verbose=False)

API_URL = "http://127.0.0.1:8000/api/v1/acesso/verificar-placa"

def sanitizar_placa(texto):
    texto = re.sub(r'[^A-Z0-9]', '', texto.upper().strip())
    if len(texto) == 7:
        if re.match(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$', texto):
            return texto
    return None

# Força a abertura usando o DirectShow (cv2.CAP_DSHOW) para evitar erros no Windows
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Erro: Não foi possível acessar a webcam. Verifique se outro aplicativo (como a Câmera do Windows) está com ela aberta.")
    exit()

print("\n--- CÂMERA DE PORTARIA ATIVA ---")
print("Enquadre a placa dentro do retângulo verde na tela. Pressione 'q' para sair.\n")

ultimo_envio = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Erro ao capturar o frame da câmera.")
        break

    altura, largura = frame.shape[:2]

    # Desenha o retângulo guia (ROI) centralizado
    x1, y1 = int(largura * 0.25), int(altura * 0.25)
    x2, y2 = int(largura * 0.75), int(altura * 0.75)
    
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(frame, "POSICIONE A PLACA AQUI", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Exibe o vídeo na tela
    cv2.imshow("Portaria Inteligente - Alinhamento de Placa", frame)

    agora = time.time()
    if agora - ultimo_envio > 1.5:
        # Recorta apenas a área de interesse para acelerar a leitura
        recorte_placa = frame[y1:y2, x1:x2]
        
        resultados = reader.readtext(recorte_placa if recorte_placa.size > 0 else frame)
        
        for (bbox, texto, confianca) in resultados:
            placa = sanitizar_placa(texto)
            if placa:
                print(f"\n[PLACA DETECTADA NO GUIA]: {placa} (Confiança: {confianca:.2f})")
                
                payload = {"placa": placa, "confianca": float(confianca)}
                try:
                    res = requests.post(API_URL, json=payload)
                    resposta_json = res.json()
                    
                    print("--- RESPOSTA DA PORTARIA ---")
                    print(json.dumps(resposta_json, ensure_ascii=False, indent=4))
                    
                    if resposta_json.get("comando") == "ABRIR_CANCELA":
                        print(">>> [CANCELA ACIONADA]: PORTÃO ABERTO COM SUCESSO! <<<")
                except Exception as e:
                    print(f"Erro ao conectar com o servidor da portaria: {e}")
                
                ultimo_envio = time.time()
                break

    # Pressione 'q' para fechar a janela da câmera
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()