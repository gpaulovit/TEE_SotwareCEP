import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

def calibrar_limites_xr(df_calibracao: pd.DataFrame, n_amostra: int, constantes_db: dict) -> dict | None:
    print(f"Calculando limites de controle X-R para n={n_amostra}...")
    
    n_str = str(n_amostra)
    
    if n_str not in constantes_db:
        print(f"ERRO: Constantes para n={n_amostra} não encontradas no banco de dados.")
        return None

    constantes = constantes_db[n_str]
    A2 = constantes.get('A2')
    D3 = constantes.get('D3')
    D4 = constantes.get('D4')
    
    if A2 is None or D3 is None or D4 is None:
        print(f"ERRO: Faltando constantes A2, D3 ou D4 para n={n_amostra} no JSON.")
        return None

    print(f"Constantes usadas: A2={A2}, D3={D3}, D4={D4}")
    
    X_barra_barra = df_calibracao['X_barra'].mean()
    R_barra = df_calibracao['R'].mean()
    
    LM_X = X_barra_barra
    fator_X = A2 * R_barra
    LSC_X = LM_X + fator_X
    LIC_X = LM_X - fator_X
    
    LM_R = R_barra
    LSC_R = D4 * R_barra
    LIC_R = D3 * R_barra

    info_limites = {
        'tipo_grafico': 'X-R',
        'n_amostra': n_amostra,
        'X_barra_barra': X_barra_barra,
        'R_barra': R_barra,
        'constantes_usadas': {'A2': A2, 'D3': D3, 'D4': D4},
        'limites_X_barra': {
            'LSC': LSC_X,
            'LM': LM_X,
            'LIC': LIC_X
        },
        'limites_R': {
            'LSC': LSC_R,
            'LM': LM_R,
            'LIC': LIC_R
        }
    }
    
    print("Limites X-R calibrados com sucesso.")
    return info_limites

def plotar_grafico_calibracao_xr(df_calibracao: pd.DataFrame, info_limites: dict, caminho_saida_grafico: str) -> bool:
    print(f"Gerando gráfico de calibração X-R em: {caminho_saida_grafico}")
    try:
        limites_x = info_limites['limites_X_barra']
        limites_r = info_limites['limites_R']
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle('Gráficos de Controle X-R (Calibração)', fontsize=16)
        
        amostras = df_calibracao['Amostra']

        ax1.plot(amostras, df_calibracao['X_barra'], 
                 marker='o', linestyle='-', color='b', label='Média da Amostra (X-barra)')
        
        ax1.axhline(y=limites_x['LSC'], color='r', linestyle='--', label=f"LSC={limites_x['LSC']:.4f}")
        ax1.axhline(y=limites_x['LM'], color='g', linestyle='-', label=f"LM={limites_x['LM']:.4f}")
        ax1.axhline(y=limites_x['LIC'], color='r', linestyle='--', label=f"LIC={limites_x['LIC']:.4f}")
        
        ax1.set_title('Gráfico X-barra (Médias)')
        ax1.set_xlabel('Amostra')
        ax1.set_ylabel('Valor da Média')
        ax1.legend(loc='upper right')
        ax1.grid(True, linestyle=':', alpha=0.6)
        ax1.set_xticks(amostras[::1])

        ax2.plot(amostras, df_calibracao['R'], 
                 marker='s', linestyle='-', color='c', label='Amplitude da Amostra (R)')
        
        ax2.axhline(y=limites_r['LSC'], color='r', linestyle='--', label=f"LSC={limites_r['LSC']:.4f}")
        ax2.axhline(y=limites_r['LM'], color='g', linestyle='-', label=f"LM={limites_r['LM']:.4f}")
        ax2.axhline(y=limites_r['LIC'], color='r', linestyle='--', label=f"LIC={limites_r['LIC']:.4f}")
        
        ax2.set_title('Gráfico R (Amplitudes)')
        ax2.set_xlabel('Amostra')
        ax2.set_ylabel('Valor da Amplitude')
        ax2.legend(loc='upper right')
        ax2.grid(True, linestyle=':', alpha=0.6)
        ax2.set_xticks(amostras[::1])

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(caminho_saida_grafico)
        plt.close(fig)
        return True
        
    except Exception as e:
        print(f"ERRO ao gerar gráfico de calibração X-R: {e}")
        return False

def _calcular_zonas_weco(limites_x: dict) -> dict:
    lm = limites_x['LM']
    lsc = limites_x['LSC']
    dist_3sigma = lsc - lm
    dist_1sigma = dist_3sigma / 3.0
    dist_2sigma = 2.0 * dist_1sigma
    
    return {
        'LM': lm,
        'LSC': lsc,
        'LIC': limites_x['LIC'],
        'LSC_2S': lm + dist_2sigma,
        'LSC_1S': lm + dist_1sigma,
        'LIC_1S': lm - dist_1sigma,
        'LIC_2S': lm - dist_2sigma
    }

def analisar_regras_weco(df_total: pd.DataFrame, info_limites: dict, indice_inicio_novos: int) -> list[str]:
    print("Analisando regras WECO para novos dados...")
    zonas = _calcular_zonas_weco(info_limites['limites_X_barra'])
    alertas = []
    
    pontos_x_barra = df_total['X_barra'].values
    
    for i in range(indice_inicio_novos, len(df_total)):
        amostra_atual = df_total.iloc[i]['Amostra']
        ponto_atual = pontos_x_barra[i]
        
        if ponto_atual > zonas['LSC'] or ponto_atual < zonas['LIC']:
            msg = f"ALERTA (Amostra {amostra_atual}): Regra 1 - Ponto fora do limite ({ponto_atual:.5f})"
            alertas.append(msg)
            print(msg)

        if i >= 7:
            ultimos_8 = pontos_x_barra[i-7:i+1]
            if all(p > zonas['LM'] for p in ultimos_8) or all(p < zonas['LM'] for p in ultimos_8):
                msg = f"ALERTA (Amostra {amostra_atual}): Regra 4 - 8 pontos no mesmo lado da média."
                alertas.append(msg)
                print(msg)

        if i >= 4:
            ultimos_5 = pontos_x_barra[i-4:i+1]
            acima_1s = sum(1 for p in ultimos_5 if p > zonas['LSC_1S'])
            abaixo_1s = sum(1 for p in ultimos_5 if p < zonas['LIC_1S'])
            if acima_1s >= 4 or abaixo_1s >= 4:
                msg = f"ALERTA (Amostra {amostra_atual}): Regra 3 - 4 de 5 pontos além de 1-sigma."
                alertas.append(msg)
                print(msg)

        if i >= 2:
            ultimos_3 = pontos_x_barra[i-2:i+1]
            acima_2s = sum(1 for p in ultimos_3 if p > zonas['LSC_2S'])
            abaixo_2s = sum(1 for p in ultimos_3 if p < zonas['LIC_2S'])
            if acima_2s >= 2 or abaixo_2s >= 2:
                msg = f"ALERTA (Amostra {amostra_atual}): Regra 2 - 2 de 3 pontos além de 2-sigma."
                alertas.append(msg)
                print(msg)
                
    if not alertas:
        print("Nenhum alerta (WECO) detectado nas novas medições.")
    
    return alertas

def plotar_grafico_monitoramento_xr(df_total: pd.DataFrame, info_limites: dict, indice_inicio_novos: int, caminho_saida_grafico: str) -> bool:
    print(f"Gerando gráfico de monitoramento X-R em: {caminho_saida_grafico}")
    try:
        zonas = _calcular_zonas_weco(info_limites['limites_X_barra'])
        limites_r = info_limites['limites_R']
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        fig.suptitle('Gráficos de Controle X-R (Monitoramento)', fontsize=16)

        amostras = df_total['Amostra']
        
        ax1.set_title('Gráfico X-barra (Médias)')
        ax1.axhline(y=zonas['LSC'], color='r', linestyle='--', label=f"LSC={zonas['LSC']:.4f}")
        ax1.axhline(y=zonas['LSC_2S'], color='y', linestyle=':', label='Zona 2-Sigma')
        ax1.axhline(y=zonas['LSC_1S'], color='y', linestyle=':', label='Zona 1-Sigma')
        ax1.axhline(y=zonas['LM'], color='g', linestyle='-', label=f"LM={zonas['LM']:.4f}")
        ax1.axhline(y=zonas['LIC_1S'], color='y', linestyle=':')
        ax1.axhline(y=zonas['LIC_2S'], color='y', linestyle=':')
        ax1.axhline(y=zonas['LIC'], color='r', linestyle='--', label=f"LIC={zonas['LIC']:.4f}")
        
        ax1.plot(amostras[:indice_inicio_novos], df_total['X_barra'][:indice_inicio_novos], 
                 marker='o', linestyle='-', color='b', label='Calibração')
        ax1.plot(amostras[indice_inicio_novos-1:], df_total['X_barra'][indice_inicio_novos-1:], 
                 marker='o', linestyle='-', color='orange', label='Monitoramento')
        ax1.legend(loc='upper right')
        ax1.grid(True, linestyle=':', alpha=0.6)

        ax2.set_title('Gráfico R (Amplitudes)')
        ax2.axhline(y=limites_r['LSC'], color='r', linestyle='--', label=f"LSC={limites_r['LSC']:.4f}")
        ax2.axhline(y=limites_r['LM'], color='g', linestyle='-', label=f"LM={limites_r['LM']:.4f}")
        ax2.axhline(y=limites_r['LIC'], color='r', linestyle='--', label=f"LIC={limites_r['LIC']:.4f}")
        
        ax2.plot(amostras[:indice_inicio_novos], df_total['R'][:indice_inicio_novos], 
                 marker='s', linestyle='-', color='c', label='Calibração')
        ax2.plot(amostras[indice_inicio_novos-1:], df_total['R'][indice_inicio_novos-1:], 
                 marker='s', linestyle='-', color='magenta', label='Monitoramento')
        
        ax2.legend(loc='upper right')
        ax2.grid(True, linestyle=':', alpha=0.6)

        plt.xticks(rotation=90, fontsize=8)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(caminho_saida_grafico)
        plt.close(fig)
        return True
    
    except Exception as e:
        print(f"ERRO ao gerar gráfico de monitoramento X-R: {e}")
        return False