import requests

url = "http://127.0.0.1:8000/api/v1/veiculos/cadastrar"
novo_veiculo = {
    "placa": "ABC1D23",
    "proprietario": "João da Silva",
    "unidade": "Bloco B - Apt 202"
}

response = requests.post(url, json=novo_veiculo)
print(response.json())