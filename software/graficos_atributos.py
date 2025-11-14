import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json


def calibrar_limites_p(df_calibracao_p: pd.DataFrame) -> dict | None:
    print("Calculando linha média (p-barra) para Gráfico P...")
    try:
        total_defeituosos = df_calibracao_p["np"].sum()
        total_inspecionados = df_calibracao_p["n"].sum()

        if total_inspecionados == 0:
            print("ERRO: Total de inspecionados é zero, impossível calcular p-barra.")
            return None

        p_barra = total_defeituosos / total_inspecionados

        info_limites_p = {
            "tipo_grafico": "P",
            "p_barra": p_barra,
            "total_defeituosos": int(total_defeituosos),
            "total_inspecionados": int(total_inspecionados),
        }

        print(f"Linha Média (p-barra) calculada: {p_barra:.6f}")
        return info_limites_p

    except Exception as e:
        print(f"ERRO ao calibrar Gráfico P: {e}")
        return None


def plotar_grafico_calibracao_p(
    df_calibracao: pd.DataFrame, info_limites_p: dict, caminho_saida_grafico: str
) -> bool:
    print(f"Gerando gráfico de calibração P em: {caminho_saida_grafico}")
    try:
        p_barra = info_limites_p["p_barra"]

        df = df_calibracao.copy()

        variacao_base = np.sqrt(p_barra * (1 - p_barra))

        df["LSC_p"] = p_barra + 3 * (variacao_base / np.sqrt(df["n"]))
        df["LIC_p"] = p_barra - 3 * (variacao_base / np.sqrt(df["n"]))
        df["LIC_p"] = df["LIC_p"].apply(lambda x: max(x, 0))

        df["fora_limite"] = (df["p"] > df["LSC_p"]) | (df["p"] < df["LIC_p"])
        pontos_fora = df[df["fora_limite"] == True]

        if len(pontos_fora) > 0:
            print(
                "Aviso de Calibração P: Pontos encontrados fora dos limites de controle."
            )

        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(
            df["lote"],
            df["p"],
            marker="o",
            linestyle="-",
            color="b",
            label="Proporção (p) do Lote",
        )
        ax.axhline(
            p_barra,
            color="g",
            linestyle="-",
            label=f"Linha Média (p-barra)={p_barra:.4f}",
        )
        ax.step(
            df["lote"],
            df["LSC_p"],
            color="r",
            linestyle="--",
            where="mid",
            label="LSC (Variável)",
        )
        ax.step(
            df["lote"],
            df["LIC_p"],
            color="r",
            linestyle="--",
            where="mid",
            label="LIC (Variável)",
        )

        if len(pontos_fora) > 0:
            ax.scatter(
                pontos_fora["lote"],
                pontos_fora["p"],
                s=100,
                facecolors="none",
                edgecolors="r",
                label="Fora de Controle",
            )

        ax.set_title("Gráfico P de Controle (Calibração)")
        ax.set_xlabel("Lote de Inspeção")
        ax.set_ylabel("Proporção de Defeituosos (p)")
        ax.legend(loc="best")
        ax.grid(True, linestyle=":", alpha=0.6)

        plt.tight_layout()
        plt.savefig(caminho_saida_grafico)
        plt.close(fig)
        return True

    except Exception as e:
        print(f"ERRO ao gerar gráfico de calibração P: {e}")
        return False


def calibrar_limites_u(df_calibracao_u: pd.DataFrame) -> dict | None:
    print("Calculando linha média (u-barra) para Gráfico U...")
    try:
        total_defeitos = df_calibracao_u["c"].sum()
        total_unidades = df_calibracao_u["n"].sum()

        if total_unidades == 0:
            print("ERRO: Total de unidades é zero, impossível calcular u-barra.")
            return None

        u_barra = total_defeitos / total_unidades

        info_limites_u = {
            "tipo_grafico": "U",
            "u_barra": u_barra,
            "total_defeitos": int(total_defeitos),
            "total_unidades": int(total_unidades),
        }

        print(f"Linha Média (u-barra) calculada: {u_barra:.4f}")
        return info_limites_u

    except Exception as e:
        print(f"ERRO ao calibrar Gráfico U: {e}")
        return None


def plotar_grafico_calibracao_u(
    df_calibracao: pd.DataFrame, info_limites_u: dict, caminho_saida_grafico: str
) -> bool:
    print(f"Gerando gráfico de calibração U em: {caminho_saida_grafico}")
    try:
        u_barra = info_limites_u["u_barra"]

        df = df_calibracao.copy()

        variacao_base = np.sqrt(u_barra)

        df["LSC_u"] = u_barra + 3 * (variacao_base / np.sqrt(df["n"]))
        df["LIC_u"] = u_barra - 3 * (variacao_base / np.sqrt(df["n"]))
        df["LIC_u"] = df["LIC_u"].apply(lambda x: max(x, 0))

        df["fora_limite"] = (df["u"] > df["LSC_u"]) | (df["u"] < df["LIC_u"])
        pontos_fora = df[df["fora_limite"] == True]

        if len(pontos_fora) > 0:
            print(
                "Aviso de Calibração U: Pontos encontrados fora dos limites de controle."
            )

        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(
            df["amostra"],
            df["u"],
            marker="o",
            linestyle="-",
            color="b",
            label="Taxa de Defeitos (u)",
        )
        ax.axhline(
            u_barra,
            color="g",
            linestyle="-",
            label=f"Linha Média (u-barra)={u_barra:.4f}",
        )
        ax.step(
            df["amostra"],
            df["LSC_u"],
            color="r",
            linestyle="--",
            where="mid",
            label="LSC (Variável)",
        )
        ax.step(
            df["amostra"],
            df["LIC_u"],
            color="r",
            linestyle="--",
            where="mid",
            label="LIC (Variável)",
        )

        if len(pontos_fora) > 0:
            ax.scatter(
                pontos_fora["amostra"],
                pontos_fora["u"],
                s=100,
                facecolors="none",
                edgecolors="r",
                label="Fora de Controle",
            )

        ax.set_title("Gráfico U de Controle (Calibração)")
        ax.set_xlabel("Amostra de Inspeção")
        ax.set_ylabel("Defeitos por Unidade (u)")
        ax.legend(loc="best")
        ax.grid(True, linestyle=":", alpha=0.6)

        plt.tight_layout()
        plt.savefig(caminho_saida_grafico)
        plt.close(fig)
        return True

    except Exception as e:
        print(f"ERRO ao gerar gráfico de calibração U: {e}")
        return False
