import base64
import os
import time
from google import genai
import cv2

os.environ["GEMINI_API_KEY"] = "###"
client = genai.Client()

def analisar_veiculo_portaria(caminho_imagem):
    if not os.path.exists(caminho_imagem):
        return f'{{"erro": "Arquivo \'{caminho_imagem}\' não encontrado."}}'

    # OTIMIZAÇÃO: Reduz o tamanho da imagem com OpenCV para envio ultrarrápido
    img = cv2.imread(caminho_imagem)
    if img is None:
        return '{"erro": "Falha ao ler imagem com OpenCV."}'
    
    # Redimensiona mantendo a proporção para largura máxima de 800px
    altura, largura = img.shape[:2]
    if largura > 800:
        proporcao = 800 / largura
        nova_altura = int(altura * proporcao)
        img = cv2.resize(img, (800, nova_altura), interpolation=cv2.INTER_AREA)
        cv2.imwrite("imagem_otimizada.tmp", img)
        arquivo_envio = "imagem_otimizada.tmp"
    else:
        arquivo_envio = caminho_imagem

    # Converte para base64
    with open(arquivo_envio, "rb") as f:
        image_bytes = f.read()

    extensao = arquivo_envio.lower().split('.')[-1]
    mime_type = "image/png" if extensao == "png" else "image/jpeg"

    prompt = """
        Analise a foto deste veículo na portaria e extraia:
        1. A placa (sem traços ou espaços).
        2. A marca e o modelo.
        3. A cor predominante.
        4. Confiança (float entre 0.0 e 1.0).
        Retorne estritamente em JSON com as chaves: "placa", "modelo", "cor" e "confianca".
    """

    # SISTEMA DE RETRY (Tenta até 3 vezes caso dê erro 503 de alta demanda)
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            interaction = client.interactions.create(
                model="gemini-3.8-flash",
                input=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "data": base64.b64encode(image_bytes).decode("utf-8"),
                        "mime_type": mime_type,
                    },
                ],
            )
            # Limpa arquivo temporário se existir
            if os.path.exists("imagem_otimizada.tmp"):
                os.remove("imagem_otimizada.tmp")
                
            return interaction.output_text

        except Exception as e:
            if "503" in str(e) and tentativa < tentativas - 1:
                print(f"Servidor ocupado (503). Tentando novamente em 2 segundos... (Tentativa {tentativa + 1}/{tentativas})")
                time.sleep(2)
            else:
                if os.path.exists("imagem_otimizada.tmp"):
                    os.remove("imagem_otimizada.tmp")
                return f'{{"erro": "{str(e)}"}}'

if __name__ == "__main__":
    arquivo_teste = "carro_exemplo1.jpg"
    
    print(f"Processando e enviando '{arquivo_teste}' para a IA...")
    inicio = time.time()
    resultado = analisar_veiculo_portaria(arquivo_teste)
    fim = time.time()
    
    print(f"\nTempo de resposta: {fim - inicio:.2f} segundos")
    print("--- DADOS EXTRAÍDOS DO VEÍCULO ---")
    print(resultado)
    
# O Próximo Passo para o seu Sistema de Portaria
# Agora que o seu script Python consegue extrair esses dados perfeitamente, o próximo passo natural é integrar essa função ao restante do seu sistema (que gerencia moradores e visitantes).

# Por exemplo, podemos fazer o script:

# Ler o JSON retornado pela IA.

# Consultar a lista de moradores/veículos cadastrados no seu sistema de portaria.

# Decidir automaticamente se libera a entrada, se avisa o morador ou se emite um alerta caso o veículo não esteja cadastrado.