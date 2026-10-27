#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  01. Calculadora de juros compostos
# ------------------------------------------------------------
# O que faz: simula um investimento com juros compostos a partir do capital
#            inicial, da taxa mensal, do prazo em meses e de um aporte mensal
#            opcional. Mostra o montante final, os juros ganhos e a tabela
#            mês a mês (saldo inicial, juros, aporte, saldo final).
# Como usar: python 01_calculadora_juros_compostos.py --capital 1000 --taxa 0.8 --meses 24 --aporte 200
#            python 01_calculadora_juros_compostos.py --demo
# O que você aprende: argparse com validação própria, dataclasses, laço de
#            acumulação, f-strings com alinhamento de colunas, formatação de
#            moeda em português e a fórmula fechada conferida contra o laço.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class LinhaMes:
    """Uma linha da tabela: o que aconteceu com o dinheiro em um único mês."""

    mes: int
    saldo_inicial: float
    juros: float
    aporte: float
    saldo_final: float


@dataclass(frozen=True)
class Resumo:
    """Totais da simulação inteira."""

    montante: float
    total_investido: float
    juros_ganhos: float


def numero(texto: str) -> float:
    """Converte texto em número, aceitando tanto '0.8' quanto '0,8'."""
    try:
        return float(texto.strip().replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um número válido") from None


def nao_negativo(texto: str) -> float:
    """Aceita apenas valores maiores ou iguais a zero (capital, taxa e aporte)."""
    valor = numero(texto)
    if valor < 0:
        raise argparse.ArgumentTypeError(f"'{texto}' é negativo; informe um valor maior ou igual a zero")
    return valor


def meses_validos(texto: str) -> int:
    """Aceita apenas um prazo inteiro entre 1 e 1200 meses (cem anos)."""
    try:
        meses = int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um prazo inteiro em meses") from None
    if not 1 <= meses <= 1200:
        raise argparse.ArgumentTypeError("o prazo precisa ficar entre 1 e 1200 meses")
    return meses


def formatar_brl(valor: float) -> str:
    """Formata 1234.5 como 'R$ 1.234,50', do jeito que se escreve no Brasil."""
    # O Python usa vírgula no milhar e ponto nos centavos. Trocamos os dois
    # passando por um símbolo provisório para as substituições não se misturarem.
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_pct(valor: float) -> str:
    """Formata 0.8 como '0,80%'."""
    return f"{valor:.2f}%".replace(".", ",")


def simular(capital: float, taxa_mensal: float, meses: int, aporte: float = 0.0) -> list[LinhaMes]:
    """Monta a tabela mês a mês. A taxa chega como fração: 0,8% vira 0.008."""
    linhas: list[LinhaMes] = []
    saldo = capital
    for mes in range(1, meses + 1):
        juros = saldo * taxa_mensal  # os juros incidem sobre tudo o que já está acumulado
        saldo_final = saldo + juros + aporte  # o aporte entra depois dos juros do mês
        linhas.append(LinhaMes(mes, saldo, juros, aporte, saldo_final))
        saldo = saldo_final  # o saldo final de um mês é o saldo inicial do seguinte
    return linhas


def montante_pela_formula(capital: float, taxa_mensal: float, meses: int, aporte: float) -> float:
    """Calcula o montante sem laço, pela fórmula fechada dos juros compostos.

    Montante = C * (1 + i)^n + A * ((1 + i)^n - 1) / i
    Com taxa zero a fórmula dividiria por zero, então devolvemos só a soma.
    """
    if taxa_mensal == 0:
        return capital + aporte * meses
    fator = (1 + taxa_mensal) ** meses
    return capital * fator + aporte * (fator - 1) / taxa_mensal


def resumir(linhas: list[LinhaMes], capital: float) -> Resumo:
    """Extrai os totais a partir da tabela já simulada."""
    montante = linhas[-1].saldo_final
    total_investido = capital + sum(linha.aporte for linha in linhas)
    return Resumo(montante, total_investido, montante - total_investido)


def imprimir_tabela(linhas: list[LinhaMes]) -> None:
    """Imprime a tabela com as colunas alinhadas à direita."""
    cabecalho = f"{'Mês':>4} | {'Saldo inicial':>16} | {'Juros':>13} | {'Aporte':>13} | {'Saldo final':>16}"
    print(cabecalho)
    print("-" * len(cabecalho))
    for linha in linhas:
        print(
            f"{linha.mes:>4} | {formatar_brl(linha.saldo_inicial):>16} | {formatar_brl(linha.juros):>13}"
            f" | {formatar_brl(linha.aporte):>13} | {formatar_brl(linha.saldo_final):>16}"
        )


def executar(capital: float, taxa_percentual: float, meses: int, aporte: float) -> None:
    """Roda a simulação completa e imprime parâmetros, tabela e resumo."""
    taxa_mensal = taxa_percentual / 100  # o usuário digita 0,8 querendo dizer 0,8%
    linhas = simular(capital, taxa_mensal, meses, aporte)
    resumo = resumir(linhas, capital)

    print(f"Capital inicial : {formatar_brl(capital)}")
    print(f"Taxa mensal     : {formatar_pct(taxa_percentual)} ao mês")
    print(f"Prazo           : {meses} meses")
    print(f"Aporte mensal   : {formatar_brl(aporte)}")
    print()
    imprimir_tabela(linhas)
    print()
    print(f"Montante final  : {formatar_brl(resumo.montante)}")
    print(f"Total investido : {formatar_brl(resumo.total_investido)}")
    print(f"Juros ganhos    : {formatar_brl(resumo.juros_ganhos)}")
    rendimento = resumo.juros_ganhos / resumo.total_investido * 100 if resumo.total_investido else 0.0
    print(f"Rendimento total: {formatar_pct(rendimento)} sobre o que foi investido")
    # Conferência: a fórmula fechada tem de bater com o laço (diferença só de arredondamento).
    pela_formula = montante_pela_formula(capital, taxa_mensal, meses, aporte)
    print(f"Pela fórmula    : {formatar_brl(pela_formula)} (diferença de {abs(pela_formula - resumo.montante):.6f})")


def demo() -> int:
    """Demonstração sem teclado: R$ 1.000 a 0,8% ao mês por 24 meses com aporte de R$ 200."""
    print("=" * 72)
    print("CodeNomad Academy | Calculadora de juros compostos | demonstração")
    print("=" * 72)
    executar(capital=1000.0, taxa_percentual=0.8, meses=24, aporte=200.0)
    return 0


def montar_parser() -> argparse.ArgumentParser:
    """Define os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Calculadora de juros compostos com aporte mensal (CodeNomad Academy).",
        epilog="Exemplo: --capital 1000 --taxa 0.8 --meses 24 --aporte 200",
    )
    parser.add_argument("--capital", type=nao_negativo, help="valor inicial investido, em reais")
    parser.add_argument("--taxa", type=nao_negativo, help="taxa de juros mensal em porcentagem (0.8 = 0,8%% ao mês)")
    parser.add_argument("--meses", type=meses_validos, help="prazo em meses (1 a 1200)")
    parser.add_argument("--aporte", type=nao_negativo, default=0.0, help="aporte mensal opcional, em reais")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa sem pedir nada")
    return parser


def main() -> None:
    """Ponto de entrada: sem argumentos mostra o uso; com --demo demonstra; senão calcula."""
    parser = montar_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.demo:
        sys.exit(demo())
    faltando = [nome for nome in ("capital", "taxa", "meses") if getattr(args, nome) is None]
    if faltando:
        parser.error("faltou informar " + ", ".join("--" + nome for nome in faltando) + " (ou use --demo)")
    executar(args.capital, args.taxa, args.meses, args.aporte)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Acrescente a opção --anual para receber a taxa ao ano e converter para a
#    mensal equivalente: (1 + anual) ** (1 / 12) - 1.
# 2. Permita aportes diferentes a cada mês, lidos de um arquivo CSV.
# 3. Grave a tabela em CSV com o módulo csv e abra o resultado em uma planilha.
# ------------------------------------------------------------
