import cv2
import easyocr
import re
import json
import os
import time

class LeitorPlacaLocal:
    def __init__(self):
        print("Carregando motor de OCR local (EasyOCR)...")
        # Idioma 'en' (inglês) costuma ser mais preciso para caracteres isolados de placas
        self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)

    def sanitizar_placa(self, texto):
        """Aplica correções comuns de OCR para formato Mercosul e Antigo."""
        texto = texto.upper().strip()
        texto = re.sub(r'[^A-Z0-9]', '', texto)
        
        if len(texto) < 7:
            return None

        # Se tiver mais de 7 caracteres, tenta pegar subsequências
        if len(texto) > 7:
            for i in range(len(texto) - 6):
                sub = texto[i:i+7]
                res = self.sanitizar_placa(sub)
                if res:
                    return res
            return None

        # Tenta ajustar substituições típicas nos 3 primeiros caracteres (letras)
        letras = list(texto[:3])
        mapa_letras = {'1': 'I', '4': 'A', '0': 'O', '5': 'S', '8': 'B', '3': 'E'}
        for i in range(3):
            if letras[i] in mapa_letras:
                letras[i] = mapa_letras[letras[i]]

        # Tenta ajustar substituições típicas nos dígitos finais
        numeros = list(texto[3:])
        mapa_numeros = {'I': '1', 'O': '0', 'S': '5', 'B': '8', 'Z': '2', 'A': '4'}
        for i in range(len(numeros)):
            if i != 1: # No padrão Mercosul (ABC1D23), a 5ª posição (índice 1 de números) é letra
                if numeros[i] in mapa_numeros:
                    numeros[i] = mapa_numeros[numeros[i]]

        placa_corrigida = "".join(letras) + "".join(numeros)
        
        # Expressão regular: ABC1234 ou ABC1D23
        if re.match(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$', placa_corrigida):
            return placa_corrigida

        return None

    def extrair_placa(self, caminho_imagem):
        if not os.path.exists(caminho_imagem):
            return {"sucesso": False, "erro": f"Arquivo '{caminho_imagem}' não encontrado."}

        inicio = time.time()
        img = cv2.imread(caminho_imagem)

        if img is None:
            return {"sucesso": False, "erro": "Falha ao carregar a imagem com OpenCV."}

        # Redimensiona para acelerar o processamento
        altura, largura = img.shape[:2]
        if largura > 1000:
            proporcao = 1000 / largura
            nova_altura = int(altura * proporcao)
            img = cv2.resize(img, (1000, nova_altura), interpolation=cv2.INTER_AREA)

        # Lê o texto diretamente na imagem
        resultados = self.reader.readtext(img)

        leituras_brutas = []
        melhor_placa = None
        maior_confianca = 0.0

        for (bbox, texto, confianca) in resultados:
            leituras_brutas.append({"texto": texto, "confianca": round(confianca, 2)})
            
            placa_sanitizada = self.sanitizar_placa(texto)
            if placa_sanitizada and confianca > maior_confianca:
                maior_confianca = confianca
                melhor_placa = placa_sanitizada

        fim = time.time()

        return {
            "sucesso": melhor_placa is not None,
            "placa_identificada": melhor_placa,
            "confianca": round(maior_confianca, 2) if melhor_placa else 0.0,
            "tempo_execucao_segundos": round(fim - inicio, 2),
            "todas_leituras_detectadas": leituras_brutas
        }

if __name__ == "__main__":
    leitor = LeitorPlacaLocal()
    arquivo_foto = "carro_exemplo2.jpg"

    print(f"\nIniciando análise local de '{arquivo_foto}'...")
    resultado = leitor.extrair_placa(arquivo_foto)

    print("\n--- RESULTADO DA PORTARIA (LOCAL) ---")
    print(json.dumps(resultado, ensure_ascii=False, indent=4))