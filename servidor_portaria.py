import sqlite3
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Portaria Inteligente - Controle de Acesso de Veículos")

DB_NAME = "portaria.db"

def inicializar_banco():
    """Cria o banco de dados e as tabelas se não existirem, e insere dados de teste."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS veiculos_autorizados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT UNIQUE NOT NULL,
            proprietario TEXT NOT NULL,
            unidade TEXT NOT NULL,
            status TEXT DEFAULT 'ativo'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_acessos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            status_acesso TEXT NOT NULL,
            detalhes TEXT
        )
    ''')
    
    # Inserir o veículo de teste inicial
    cursor.execute('''
        INSERT OR IGNORE INTO veiculos_autorizados (placa, proprietario, unidade, status)
        VALUES ('Placa', 'Morador Principal', 'Bloco A - Apt 101', 'ativo')
    ''')
    
    conn.commit()
    conn.close()

inicializar_banco()

# Modelos de Dados (Pydantic)
class LeituraPlacaRequest(BaseModel):
    placa: str
    confianca: float

class CadastroVeiculoRequest(BaseModel):
    placa: str
    proprietario: str
    unidade: str

@app.post("/api/v1/acesso/verificar-placa")
def verificar_placa_morador(dados: LeituraPlacaRequest):
    """Verifica se a placa lida pela câmera está autorizada no condomínio."""
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

@app.post("/api/v1/veiculos/cadastrar")
def cadastrar_veiculo(dados: CadastroVeiculoRequest):
    """Cadastra um novo morador / veículo no sistema de passagem livre."""
    placa_limpa = dados.placa.upper().strip()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO veiculos_autorizados (placa, proprietario, unidade, status) VALUES (?, ?, ?, 'ativo')",
            (placa_limpa, dados.proprietario, dados.unidade)
        )
        conn.commit()
        conn.close()
        return {"sucesso": True, "mensagem": f"Veículo de placa {placa_limpa} cadastrado com sucesso para {dados.proprietario} ({dados.unidade})."}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail=f"A placa {placa_limpa} já está cadastrada no sistema.")

@app.get("/api/v1/veiculos")
def listar_veiculos():
    """Lista todos os veículos cadastrados no sistema de portaria."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT placa, proprietario, unidade, status FROM veiculos_autorizados")
    linhas = cursor.fetchall()
    conn.close()
    
    veiculos = []
    for linha in linhas:
        veiculos.append({
            "placa": linha[0],
            "proprietario": linha[1],
            "unidade": linha[2],
            "status": linha[3]
        })
    return {"total": len(veiculos), "veiculos": veiculos}

if __name__ == "__main__":
    print("Iniciando Servidor Backend da Portaria em http://127.0.0.1:8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)