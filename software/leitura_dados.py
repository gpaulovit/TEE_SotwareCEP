# Nome do Script: analise_capacidade_ppm_v2.py
import pandas as pd
import numpy as np
import json

ARQUIVO_LIMITES = 'limites_controle.json'
ARQUIVO_CONSTANTES = 'constants_cep.json' 


def carregar_constantes_cep(caminho_arquivo: str) -> dict | None:
    print(f"Lendo constantes de: {caminho_arquivo}")
    try:
        with open(caminho_arquivo, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo de constantes não encontrado em {caminho_arquivo}")
        return None
    except json.JSONDecodeError:
        print(f"ERRO: O arquivo de constantes não é um JSON válido.")
        return None

def carregar_especificacoes(caminho_arquivo: str, nome_processo: str) -> dict | None:
    print(f"Lendo especificações de: {caminho_arquivo}")
    try:
        with open(caminho_arquivo, 'r') as f:
            todas_especs = json.load(f)
        
        espec_processo = todas_especs.get(nome_processo)
        if espec_processo is None:
            print(f"ERRO: O nome do processo '{nome_processo}' não foi encontrado em {caminho_arquivo}")
            return None
        
        return espec_processo
        
    except FileNotFoundError:
        print(f"ERRO: Arquivo de especificações não encontrado em {caminho_arquivo}")
        return None
    except json.JSONDecodeError:
        print(f"ERRO: O arquivo de especificações não é um JSON válido.")
        return None

def carregar_dados_calibracao_xr(caminho_arquivo: str) -> tuple[pd.DataFrame | None, int | None]:
    print(f"Lendo dados de calibração X-R de: {caminho_arquivo}")
    try:
        df_bruto = pd.read_json(caminho_arquivo)
        
        if 'Dados' not in df_bruto.columns:
            print("ERRO: O JSON não contém a coluna 'Dados' esperada.")
            return None, None
        if len(df_bruto) == 0:
            print("ERRO: O arquivo de dados está vazio.")
            return None, None

        n_amostra = len(df_bruto['Dados'].iloc[0])
        print(f"Tamanho da amostra (n) detectado: {n_amostra}")

        df_bruto['X_barra'] = df_bruto['Dados'].apply(np.mean)
        df_bruto['R'] = df_bruto['Dados'].apply(lambda lista: np.max(lista) - np.min(lista))
        
        df_processado = df_bruto[['Amostra', 'X_barra', 'R']]
        return df_processado, n_amostra
        
    except FileNotFoundError:
        print(f"ERRO: Arquivo de dados não encontrado em {caminho_arquivo}")
        return None, None
    except Exception as e:
        print(f"ERRO ao processar dados X-R: {e}")
        return None, None

def carregar_dados_calibracao_p(caminho_arquivo: str) -> pd.DataFrame | None:
    print(f"Lendo dados de calibração Gráfico P de: {caminho_arquivo}")
    try:
        df = pd.read_json(caminho_arquivo)
        df.rename(columns={'n_inspecionados': 'n', 'n_defeituosos': 'np'}, inplace=True)
        
        if 'n' not in df.columns or 'np' not in df.columns:
            print("ERRO: JSON do Gráfico P deve conter 'n_inspecionados' e 'n_defeituosos'.")
            return None
        
        df['p'] = df['np'].divide(df['n']).fillna(0)
        
        return df[['lote', 'n', 'np', 'p']]
        
    except FileNotFoundError:
        print(f"ERRO: Arquivo de dados não encontrado em {caminho_arquivo}")
        return None
    except Exception as e:
        print(f"ERRO ao processar dados do Gráfico P: {e}")
        return None

def carregar_dados_calibracao_u(caminho_arquivo: str) -> pd.DataFrame | None:
    print(f"Lendo dados de calibração Gráfico U de: {caminho_arquivo}")
    try:
        df = pd.read_json(caminho_arquivo)
        df.rename(columns={'unidades_inspecionadas': 'n', 'total_defeitos': 'c'}, inplace=True)
        
        if 'n' not in df.columns or 'c' not in df.columns:
            print("ERRO: JSON do Gráfico U deve conter 'unidades_inspecionadas' e 'total_defeitos'.")
            return None
        
        df['u'] = df['c'].divide(df['n']).fillna(0)
        
        return df[['amostra', 'n', 'c', 'u']]
        
    except FileNotFoundError:
        print(f"ERRO: Arquivo de dados não encontrado em {caminho_arquivo}")
        return None
    except Exception as e:
        print(f"ERRO ao processar dados do Gráfico U: {e}")
        return None

def carregar_dados_monitoramento_xr(caminho_arquivo: str) -> pd.DataFrame | None:
    print(f"Lendo dados de MONITORAMENTO X-R de: {caminho_arquivo}")
    try:
        df_bruto = pd.read_json(caminho_arquivo)
        
        if 'Dados' not in df_bruto.columns or 'Amostra' not in df_bruto.columns:
            print("ERRO: O JSON não contém as colunas 'Dados'/'Amostra' esperadas.")
            return None
        
        df_bruto['X_barra'] = df_bruto['Dados'].apply(np.mean)
        df_bruto['R'] = df_bruto['Dados'].apply(lambda lista: np.max(lista) - np.min(lista))
        
        df_processado = df_bruto[['Amostra', 'X_barra', 'R']]
        return df_processado
        
    except FileNotFoundError:
        print(f"ERRO: Arquivo de dados não encontrado em {caminho_arquivo}")
        return None
    except Exception as e:
        print(f"ERRO ao processar novos dados X-R: {e}")
        return None