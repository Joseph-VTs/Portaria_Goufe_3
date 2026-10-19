import sqlite3
import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Portaria Inteligente - Controle de Acesso de Veículos")

# Nome do banco de dados local
DB_NAME = "portaria.db"

def inicializar_banco():
    """Cria o banco de dados e as tabelas se não existirem, e insere dados de teste."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de veículos autorizados (Moradores com passagem livre)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS veiculos_autorizados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT UNIQUE NOT NULL,
            proprietario TEXT NOT NULL,
            unidade TEXT NOT NULL,
            status TEXT DEFAULT 'ativo'
        )
    ''')
    
    # Tabela de histórico de acessos da portaria
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_acessos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            status_acesso TEXT NOT NULL,
            detalhes TEXT
        )
    ''')
    
    # Inserir o veículo de teste (INSERT OR IGNORE evita erros se já existir)
    cursor.execute('''
        INSERT OR IGNORE INTO veiculos_autorizados (placa, proprietario, unidade, status)
        VALUES ('IRV4I78', 'Morador Principal', 'Bloco A - Apt 101', 'ativo')
    ''')
    
    conn.commit()
    conn.close()

# Inicializa o banco ao subir o script
inicializar_banco()

# Modelo de dados recebido
class LeituraPlacaRequest(BaseModel):
    placa: str
    confianca: float

@app.post("/api/v1/acesso/verificar-placa")
def verificar_placa_morador(dados: LeituraPlacaRequest):
    """
    Rota principal da portaria: recebe a placa lida,
    consulta o banco e decide a liberação (passagem livre).
    """
    placa_limpa = dados.placa.upper().strip()
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT proprietario, unidade, status FROM veiculos_autorizados WHERE placa = ?", 
        (placa_limpa,)
    )
    resultado = cursor.fetchone()
    
    status_acesso = "NEGADO"
    comando_cancela = "MANTER_FECHADA"
    mensagem = "Veículo não cadastrado ou acesso inativo."
    
    if resultado:
        proprietario, unidade, status = resultado
        if status == 'ativo':
            status_acesso = "AUTORIZADO"
            comando_cancela = "ABRIR_CANCELA"
            mensagem = f"Acesso liberado para {proprietario} ({unidade}). Passagem livre."
        else:
            mensagem = f"Acesso bloqueado para a unidade {unidade} (Status: inativo)."
            
    cursor.execute(
        "INSERT INTO historico_acessos (placa, data_hora, status_acesso, detalhes) VALUES (?, ?, ?, ?)",
        (placa_limpa, agora, status_acesso, mensagem)
    )
    conn.commit()
    conn.close()
    
    return {
        "placa": placa_limpa,
        "status_acesso": status_acesso,
        "comando": comando_cancela,
        "mensagem": mensagem,
        "timestamp": agora
    }

if __name__ == "__main__":
    print("Iniciando Servidor Backend da Portaria em http://127.0.0.1:8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)