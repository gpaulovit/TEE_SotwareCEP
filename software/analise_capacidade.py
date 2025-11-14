import numpy as np
import json
from scipy.stats import norm


def calcular_sigma_estimado(
    R_barra: float, n_amostra: int, constantes_db: dict
) -> float | None:
    print(f"Calculando Sigma (Desvio Padrão) para n={n_amostra}...")

    n_str = str(n_amostra)
    if n_str not in constantes_db:
        print(f"ERRO: Constantes para n={n_amostra} não encontradas.")
        return None

    d2 = constantes_db[n_str].get("d2")
    if d2 is None:
        print(f"ERRO: Constante 'd2' não encontrada para n={n_amostra}.")
        return None

    if d2 == 0:
        print(f"ERRO: Constante 'd2' é zero, divisão impossível.")
        return None

    sigma = R_barra / d2
    print(f"Sigma (R_barra / d2) calculado: {sigma:.6f}")
    return sigma


def calcular_capacidade_cpk(mu: float, sigma: float, LSE: float, LIE: float) -> dict:
    print("Calculando Cp e Cpk...")

    largura_especificacao = LSE - LIE
    largura_processo_6s = 6 * sigma

    Cp = 0.0
    if largura_processo_6s > 0:
        Cp = largura_especificacao / largura_processo_6s

    tres_sigma = 3 * sigma
    Cps = 0.0
    Cpi = 0.0

    if tres_sigma > 0:
        Cps = (LSE - mu) / tres_sigma
        Cpi = (mu - LIE) / tres_sigma

    Cpk = min(Cps, Cpi)

    print(f"Capacidade Calculada: Cp={Cp:.3f}, Cpk={Cpk:.3f}")

    return {
        "especificacoes": {"LSE": LSE, "LIE": LIE},
        "Cp": Cp,
        "Cpk": Cpk,
        "Cps": Cps,
        "Cpi": Cpi,
    }


def calcular_probabilidade_st(mu: float, sigma: float, LSE: float, LIE: float) -> dict:
    print("Calculando probabilidade de Curto Prazo (ST) / PPM...")

    prob_defeito_abaixo = norm.cdf(LIE, loc=mu, scale=sigma)
    prob_defeito_acima = 1.0 - norm.cdf(LSE, loc=mu, scale=sigma)

    prob_defeito_total = prob_defeito_abaixo + prob_defeito_acima
    prob_sucesso = 1.0 - prob_defeito_total
    PPM_st = prob_defeito_total * 1_000_000

    if prob_sucesso == 1.0:
        Z_level_st = 8.0
    elif prob_sucesso == 0.0:
        Z_level_st = -8.0
    else:
        Z_level_st = norm.ppf(prob_sucesso) + 1.5

    return {
        "prob_sucesso": prob_sucesso,
        "prob_defeito_total": prob_defeito_total,
        "prob_defeito_abaixo_LIE": prob_defeito_abaixo,
        "prob_defeito_acima_LSE": prob_defeito_acima,
        "ppm_st": PPM_st,
        "Z_level_st": Z_level_st,
    }


def calcular_probabilidade_lt(
    mu: float, sigma: float, LSE: float, LIE: float, Cpk: float
) -> dict:
    print("Calculando probabilidade de Longo Prazo (LT) / PPM com shift de 1.5s...")

    shift = 1.5 * sigma
    mu_lt = mu

    if (LSE - mu) < (mu - LIE):
        mu_lt = mu - shift
    else:
        mu_lt = mu + shift

    prob_defeito_abaixo_lt = norm.cdf(LIE, loc=mu_lt, scale=sigma)
    prob_defeito_acima_lt = 1.0 - norm.cdf(LSE, loc=mu_lt, scale=sigma)

    prob_defeito_total_lt = prob_defeito_abaixo_lt + prob_defeito_acima_lt
    prob_sucesso_lt = 1.0 - prob_defeito_total_lt
    PPM_lt = prob_defeito_total_lt * 1_000_000

    Z_level_lt = Cpk * 3.0

    return {
        "media_deslocada_lt": mu_lt,
        "prob_sucesso_lt": prob_sucesso_lt,
        "prob_defeito_total_lt": prob_defeito_total_lt,
        "ppm_lt": PPM_lt,
        "Z_level_lt": Z_level_lt,
    }


def executar_analise_completa(
    info_limites_xr: dict, constantes_db: dict, especificacoes: dict
) -> dict | None:
    print("\nIniciando análise completa de capacidade e probabilidade...")
    try:
        mu = info_limites_xr["X_barra_barra"]
        R_barra = info_limites_xr["R_barra"]
        n_amostra = info_limites_xr["n_amostra"]

        LSE = especificacoes["LSE"]
        LIE = especificacoes["LIE"]

        sigma = calcular_sigma_estimado(R_barra, n_amostra, constantes_db)
        if sigma is None or sigma == 0:
            print("ERRO: Sigma inválido, impossível continuar análise.")
            return None

        info_capacidade = calcular_capacidade_cpk(mu, sigma, LSE, LIE)

        info_prob_st = calcular_probabilidade_st(mu, sigma, LSE, LIE)

        info_prob_lt = calcular_probabilidade_lt(
            mu, sigma, LSE, LIE, info_capacidade["Cpk"]
        )

        valor_arbitrario = especificacoes.get("valor_prob_arbitrario")
        prob_arbitraria_info = {}

        if valor_arbitrario is not None:
            try:
                valor_arb_float = float(valor_arbitrario)
                print(
                    f"Calculando probabilidade arbitrária para P(X > {valor_arb_float})..."
                )

                prob_acima = 1.0 - norm.cdf(valor_arb_float, loc=mu, scale=sigma)

                prob_arbitraria_info = {
                    "valor_referencia": valor_arb_float,
                    "prob_acima_desse_valor": prob_acima,
                    "ppm_acima_desse_valor": prob_acima * 1_000_000,
                }
                print(
                    f"Resultado: P(X > {valor_arb_float}) = {prob_acima:.6f} ({prob_acima * 1_000_000:.2f} PPM)"
                )

            except ValueError:
                print(
                    f"AVISO: 'valor_prob_arbitrario' ({valor_arbitrario}) não é um número válido. Cálculo pulado."
                )
            except Exception as e:
                print(
                    f"AVISO: Erro ao calcular probabilidade arbitrária: {e}. Cálculo pulado."
                )

        resultados_finais = {
            "sigma_estimado": sigma,
            **info_capacidade,
            "probabilidade_curto_prazo_st": info_prob_st,
            "probabilidade_longo_prazo_lt": info_prob_lt,
            "confiabilidade_st_1_menos_F": info_prob_st["prob_sucesso"],
        }

        if prob_arbitraria_info:
            resultados_finais["probabilidade_arbitraria_q2_3"] = prob_arbitraria_info

        print("Análise de capacidade e probabilidade concluída.")
        return resultados_finais

    except KeyError as e:
        print(f"ERRO: Chave faltando para análise de capacidade: {e}")
        return None
    except Exception as e:
        print(f"ERRO inesperado na análise de capacidade: {e}")
        return None
