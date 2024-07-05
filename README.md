# find_bitcoin_GPU
Procurar a privatekey das wallets do bitcoin-puzzle-tx usando a GPU

Está em desenvolvimento.
Caso queira ajudar, o arquivo kernel.py é onde fica o código que é processado pela GPU
A linguagem utilizada no código do kernel é OpenCL C

Lá tem a função find_bitcoins onde ele pega o array de private_keys e de addresses e converte em publickey_x e publickey_y de uma forma bem básica usando a curva secp256k1
verifica se a publickey_x e publickey_y são iguais a address, mas ainda falta alguns ajustes, pois a conversão para publickey ainda não está certo
Mas esse código ja é um inicio para executar o código usando a GPU
está retornando a publickey_x e publickey_y para testar a velocidade e esse é o resultado em 60 segundos buscando no range 66

Resumo:
Tempo:  60.04217338562012
Velocidade: 1848700.5673013178 haves por segundo
Chaves buscadas:  111000000
Ultima chave tentada:  00000000000000000000000000000000000000000000000200000000069db9bf


INSTALAÇÃO

clonar o projeto com o comando:

git clone https://github.com/DanteKiller/find_bitcoin_GPU.git .

obs: use o ponto final para baixar os arquivos na pasta raiz, ou remova o ponto final para baixar a pasta do projeto

Após clonar, entre na pasta onde está os arquivos do projeto

Instale o Virtualenv com o comando:

python -m venv venv

selecione o interpretador python 3^ (venv:venv)

execute o comando:

venv\Scripts\Activate

Comando para iniciar o Virtualenv

Instale as bibliotecas com o comando:

pip install -r requirements.txt

Execute o projeto com o comando:

python btc_finder_GPU.py
