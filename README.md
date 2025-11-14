# Software de Análise de Controle Estatístico de Processo (CEP)

Este projeto é uma ferramenta de linha de comando em Python para realizar análises de Controle Estatístico de Processo (CEP). Ele é projetado para processar dados de calibração e monitoramento, gerar gráficos de controle, analisar a capacidade do processo e verificar violações de regras da Western Electric.

## Requisitos

O software requer as seguintes bibliotecas Python:
 ```bash
pandas
numpy
matplotlib
scipy
```

## Instalação

1.  Instale as dependências usando o `pip` e o arquivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

## Configuração antes da Execução

Antes de executar o `main.py`, você **precisa** configurar os arquivos de entrada:

1.  **Constantes CEP (`configuracao/constants_cep.json`):**
    * Verifique se este arquivo contém as constantes (d2, A2, D3, D4) corretas para o tamanho da sua amostra (`n`). A chave do objeto deve ser o `n` (como string).

2.  **Especificações do Processo (`configuracao/especificacoes.json`):**
    * `LSE`: Limite Superior de Especificação.
    * `LIE`: Limite Inferior de Especificação.
    * `valor_prob_arbitrario`: O valor para o qual você quer calcular P(X > valor).

3.  **Dados de Entrada (`dados_entrada/calibracao/`):**
    * Coloque seus arquivos JSON de calibração aqui.



## Execução

Após a instalação e configuração, execute o software a partir do diretório raiz (`Topicos_Cep`) usando o seguinte comando no seu terminal:

```bash
python main.py
