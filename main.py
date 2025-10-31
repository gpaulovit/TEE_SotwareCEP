import sys
import os
import json
import pandas as pd
from software import leitura_dados
from software import graficos_variaveis
from software import graficos_atributos
from software import analise_capacidade

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PASTA_DADOS_ENTRADA = os.path.join(BASE_DIR, "dados_entrada")
PASTA_CONFIG = os.path.join(BASE_DIR, "configuracao")
PASTA_OUTPUT = os.path.join(BASE_DIR, "resultados")

PASTA_GRAFICOS = os.path.join(PASTA_OUTPUT, "graficos")
PASTA_LIMITES = os.path.join(PASTA_OUTPUT, "limites_calculados")
PASTA_PROCESSADOS = os.path.join(PASTA_OUTPUT, "dados_processados")

CAMINHO_CONSTANTES = os.path.join(PASTA_CONFIG, "constants_cep.json")
CAMINHO_ESPECS = os.path.join(PASTA_CONFIG, "especificacoes.json")

NOME_PROCESSO_XR = "dados_simulado_prova_1"
NOME_PROCESSO_P = "grafico_p"
NOME_PROCESSO_U = "grafico_u"

CAMINHO_CALIB_XR = os.path.join(PASTA_DADOS_ENTRADA, "calibracao", "dados_simulado_prova_1.json")
CAMINHO_CALIB_P = os.path.join(PASTA_DADOS_ENTRADA, "calibracao", "grafico_p.json")
CAMINHO_CALIB_U = os.path.join(PASTA_DADOS_ENTRADA, "calibracao", "grafico_u.json")

CAMINHO_MONIT_XR = os.path.join(PASTA_DADOS_ENTRADA, "monitoramento", "novas_medicoes.json")

CAMINHO_LIMITES_XR_OUT = os.path.join(PASTA_LIMITES, f"limites_{NOME_PROCESSO_XR}.json")
CAMINHO_GRAFICO_CALIB_XR_OUT = os.path.join(PASTA_GRAFICOS, f"calibracao_{NOME_PROCESSO_XR}.png")
CAMINHO_GRAFICO_MONIT_XR_OUT = os.path.join(PASTA_GRAFICOS, f"monitoramento_{NOME_PROCESSO_XR}.png")
CAMINHO_DADOS_PROC_XR_OUT = os.path.join(PASTA_PROCESSADOS, f"calibracao_{NOME_PROCESSO_XR}.csv")

CAMINHO_LIMITES_P_OUT = os.path.join(PASTA_LIMITES, f"limites_{NOME_PROCESSO_P}.json")
CAMINHO_GRAFICO_CALIB_P_OUT = os.path.join(PASTA_GRAFICOS, f"calibracao_{NOME_PROCESSO_P}.png")

CAMINHO_LIMITES_U_OUT = os.path.join(PASTA_LIMITES, f"limites_{NOME_PROCESSO_U}.json")
CAMINHO_GRAFICO_CALIB_U_OUT = os.path.join(PASTA_GRAFICOS, f"calibracao_{NOME_PROCESSO_U}.png")


def verificar_pastas_output():
    os.makedirs(PASTA_GRAFICOS, exist_ok=True)
    os.makedirs(PASTA_LIMITES, exist_ok=True)
    os.makedirs(PASTA_PROCESSADOS, exist_ok=True)

def main():
    print("--- INICIANDO SOFTWARE CEP ---")
    
    verificar_pastas_output()
    print(f"Pastas de output verificadas/criadas em: {PASTA_OUTPUT}")
    
    
    print("\nEtapa 1: Carregando todos os dados e configurações...")
    sucesso = True
    
    constantes_cep = leitura_dados.carregar_constantes_cep(CAMINHO_CONSTANTES)
    if constantes_cep is None:
        sucesso = False
    
    especs_xr = leitura_dados.carregar_especificacoes(CAMINHO_ESPECS, NOME_PROCESSO_XR)
    if especs_xr is None:
        sucesso = False
        
    df_xr, n_xr = leitura_dados.carregar_dados_calibracao_xr(CAMINHO_CALIB_XR)
    if df_xr is None:
        sucesso = False
        
    df_p = leitura_dados.carregar_dados_calibracao_p(CAMINHO_CALIB_P)
    if df_p is None:
        sucesso = False
        
    df_u = leitura_dados.carregar_dados_calibracao_u(CAMINHO_CALIB_U)
    if df_u is None:
        sucesso = False
        
    df_monit_xr = leitura_dados.carregar_dados_monitoramento_xr(CAMINHO_MONIT_XR)
    if df_monit_xr is None:
        print("*Aviso: Não foi possível carregar dados de monitoramento X-R.")
    
    if not sucesso:
        print("\nERRO FATAL: Falha ao carregar arquivos de calibração ou configuração.")
        sys.exit(1)
        
    print("\n--- Etapa 1 Concluída: Todos os arquivos essenciais foram carregados. ---")
    
 
    print("\nEtapa 2: Iniciando calibração dos gráficos X-R...")
    
    info_limites_xr = graficos_variaveis.calibrar_limites_xr(df_xr, n_xr, constantes_cep)
    
    if info_limites_xr is None:
        print("ERRO FATAL: Falha ao calibrar limites X-R.")
        sys.exit(1)
    
    try:
        with open(CAMINHO_LIMITES_XR_OUT, 'w') as f:
            json.dump(info_limites_xr, f, indent=4)
        print(f"Limites X-R (base) salvos em: {CAMINHO_LIMITES_XR_OUT}")
    except Exception as e:
        print(f"ERRO ao salvar arquivo de limites JSON: {e}")
        sys.exit(1)
        
    graficos_variaveis.plotar_grafico_calibracao_xr(df_xr, info_limites_xr, CAMINHO_GRAFICO_CALIB_XR_OUT)
    
    try:
        df_xr.to_csv(CAMINHO_DADOS_PROC_XR_OUT, index=False)
        print(f"Dados X-R processados salvos em: {CAMINHO_DADOS_PROC_XR_OUT}")
    except Exception as e:
        print(f"ERRO ao salvar dados processados CSV: {e}")

    print("\n--- Etapa 2 Concluída: Calibração X-R finalizada. ---")
    
   
    print("\nEtapa 3: Iniciando calibração dos gráficos de atributos (P e U)...")
    
    info_limites_p = graficos_atributos.calibrar_limites_p(df_p)
    if info_limites_p:
        try:
            with open(CAMINHO_LIMITES_P_OUT, 'w') as f:
                json.dump(info_limites_p, f, indent=4)
            print(f"Limites Gráfico P salvos em: {CAMINHO_LIMITES_P_OUT}")
            graficos_atributos.plotar_grafico_calibracao_p(df_p, info_limites_p, CAMINHO_GRAFICO_CALIB_P_OUT)
        except Exception as e:
            print(f"ERRO ao salvar resultados do Gráfico P: {e}")
    else:
        print("ERRO: Falha ao calibrar Gráfico P.")

    info_limites_u = graficos_atributos.calibrar_limites_u(df_u)
    if info_limites_u:
        try:
            with open(CAMINHO_LIMITES_U_OUT, 'w') as f:
                json.dump(info_limites_u, f, indent=4)
            print(f"Limites Gráfico U salvos em: {CAMINHO_LIMITES_U_OUT}")
            graficos_atributos.plotar_grafico_calibracao_u(df_u, info_limites_u, CAMINHO_GRAFICO_CALIB_U_OUT)
        except Exception as e:
            print(f"ERRO ao salvar resultados do Gráfico U: {e}")
    else:
        print("ERRO: Falha ao calibrar Gráfico U.")

    print("\n--- Etapa 3 Concluída: Calibração de Atributos finalizada. ---")
    
   
    print("\nEtapa 4: Iniciando análise de capacidade e probabilidade (para X-R)...")
    
    info_capacidade_completa = analise_capacidade.executar_analise_completa(info_limites_xr, constantes_cep, especs_xr)
    
    if info_capacidade_completa:
        info_limites_xr['analise_capacidade'] = info_capacidade_completa
        try:
            with open(CAMINHO_LIMITES_XR_OUT, 'w') as f:
                json.dump(info_limites_xr, f, indent=4)
            print(f"Limites X-R atualizados com análise de capacidade.")
        except Exception as e:
            print(f"ERRO ao salvar limites X-R atualizados: {e}")
    else:
        print("ERRO: Falha ao executar análise de capacidade.")
        
    print("\n--- Etapa 4 Concluída: Análise de capacidade finalizada. ---")
    
   
    print("\nEtapa 5: Iniciando monitoramento (para X-R)...")
    
    if df_monit_xr is not None:
        df_total_xr = pd.concat([df_xr, df_monit_xr], ignore_index=True)
        indice_inicio_novos = len(df_xr)
        
        graficos_variaveis.analisar_regras_weco(df_total_xr, info_limites_xr, indice_inicio_novos)
        
        graficos_variaveis.plotar_grafico_monitoramento_xr(df_total_xr, info_limites_xr, indice_inicio_novos, CAMINHO_GRAFICO_MONIT_XR_OUT)
        
        print("Gráfico de monitoramento salvo.")
    else:
        print("Nenhum dado de monitoramento X-R encontrado, pulando Etapa 5.")
        
    print("\n--- Etapa 5 Concluída: Monitoramento finalizado. ---")
    
    print("\n--- SOFTWARE CEP CONCLUÍDO ---")

if __name__ == "__main__":
    main()