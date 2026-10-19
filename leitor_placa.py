import cv2
import pytesseract

# Aponta para o Tesseract instalado no seu AppData
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\User\AppData\Local\Tesseract-OCR\tesseract.exe'

def ler_placa_veiculo(caminho_imagem):
    # 1. Carregar a imagem com OpenCV
    img = cv2.imread(caminho_imagem)
    
    if img is None:
        return "Erro: Não foi possível carregar a imagem do veículo."

    # 2. Converter para escala de cinza (remove ruídos de cores)
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. Aplicar filtro bilateral para suavizar mantendo as bordas das letras nítidas
    filtrada = cv2.bilateralFilter(cinza, 11, 17, 17)
    
    # 4. Configuração avançada do Tesseract (PSM 8 trata a imagem como uma única palavra/linha, ideal para placas)
    # Definimos também uma whitelist opcional para ajudar (letras de A-Z e números de 0-9)
    # config_tesseract = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    config_tesseract = r'--oem 3 --psm 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
    # 5. Executar o OCR na imagem tratada
    texto_placa = pytesseract.image_to_string(filtrada, config=config_tesseract)
    
    # Limpar espaços em branco ou quebras de linha indesejadas
    return texto_placa.strip()

if __name__ == "__main__":
    # Substitua pelo caminho de uma foto de teste de um carro/placa
    arquivo_teste = "placaDeCarroTeste.jpg"
    
    print("Processando imagem do veículo...")
    placa_encontrada = ler_placa_veiculo(arquivo_teste)
    
    print(f"\n--- PLACA IDENTIFICADA ---")
    print(f"Resultado: {placa_encontrada}")