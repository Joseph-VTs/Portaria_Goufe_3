import base64
import os
from google import genai

# Se preferir colar a chave direto para testar:
os.environ["GEMINI_API_KEY"] = "###"

# Inicializa o cliente da API
client = genai.Client()

# Lê a imagem do carro em formato binário (base64) para enviar na Interactions API
caminho_imagem = "carro_exemplo1.jpg"

with open(caminho_imagem, "rb") as f:
    image_bytes = f.read()

# Prompt instruindo a IA a extrair os dados e responder em JSON
prompt = """
Analise a foto deste veículo na portaria e extraia as seguintes informações:
1. A placa do veículo (sem traços ou espaços).
2. A marca e o modelo do veículo.
3. A cor predominante do veículo.
4. O nível de confiança na leitura da placa (valor float entre 0.0 e 1.0).

Retorne estritamente em formato JSON estruturado com as chaves: 
"placa", "modelo", "cor" e "confianca".
"""

# Chamada usando a Interactions API moderna
interaction = client.interactions.create(
    model="gemini-2.5-flash",
    input=[
        {"type": "text", "text": prompt},
        {
            "type": "image",
            "data": base64.b64encode(image_bytes).decode("utf-8"),
            "mime_type": "image/jpeg",
        },
    ],
)

# Exibe o resultado JSON retornado pela IA
print("--- DADOS EXTRAÍDOS DO VEÍCULO ---")
print(interaction.output_text)