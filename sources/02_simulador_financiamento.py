#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  02. Simulador de financiamento (Price e SAC)
# ------------------------------------------------------------
# O que faz: recebe o valor financiado, a taxa mensal e o prazo, e gera a
#            tabela de parcelas nos dois sistemas mais comuns no Brasil:
#            Price (parcelas iguais) e SAC (amortização constante). No fim,
#            compara o total pago e o total de juros de cada sistema.
# Como usar: python 02_simulador_financiamento.py --valor 50000 --taxa 1 --meses 12
#            python 02_simulador_financiamento.py --valor 250000 --taxa 0.9 --meses 360 --resumo
#            python 02_simulador_financiamento.py --demo
# O que você aprende: funções puras que devolvem listas de dataclasses, a
#            diferença real entre os dois sistemas de amortização, potência
#            com expoente negativo, cuidado com taxa zero e com os restos de
#            ponto flutuante, e impressão de tabelas alinhadas.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Parcela:
    """Uma parcela do financiamento e a sua composição."""

    mes: int
    valor: float
    juros: float
    amortizacao: float
    saldo_devedor: float


@dataclass(frozen=True)
class Resumo:
    """Os totais de um sistema de amortização."""

    sistema: str
    total_pago: float
    total_juros: float
    primeira_parcela: float
    ultima_parcela: float


def numero(texto: str) -> float:
    """Converte texto em número, aceitando tanto '0.9' quanto '0,9'."""
    try:
        return float(texto.strip().replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um número válido") from None


def positivo(texto: str) -> float:
    """Aceita apenas valores maiores que zero (o valor financiado)."""
    valor = numero(texto)
    if valor <= 0:
        raise argparse.ArgumentTypeError(f"'{texto}' precisa ser maior que zero")
    return valor


def nao_negativo(texto: str) -> float:
    """Aceita zero ou mais (a taxa pode ser zero em promoções sem juros)."""
    valor = numero(texto)
    if valor < 0:
        raise argparse.ArgumentTypeError(f"'{texto}' é negativo; a taxa não pode ser negativa")
    return valor


def meses_validos(texto: str) -> int:
    """Aceita apenas um prazo inteiro entre 1 e 600 meses (cinquenta anos)."""
    try:
        meses = int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um prazo inteiro em meses") from None
    if not 1 <= meses <= 600:
        raise argparse.ArgumentTypeError("o prazo precisa ficar entre 1 e 600 meses")
    return meses


def formatar_brl(valor: float) -> str:
    """Formata 1234.5 como 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def tabela_price(valor: float, taxa: float, meses: int) -> list[Parcela]:
    """Sistema Price: todas as parcelas são iguais; os juros caem e a amortização sobe.

    A parcela vem da fórmula P = V * i / (1 - (1 + i) ** -n). Com taxa zero a
    fórmula dividiria por zero, então a parcela é simplesmente V / n.
    """
    parcela = valor / meses if taxa == 0 else valor * taxa / (1 - (1 + taxa) ** -meses)
    parcelas: list[Parcela] = []
    saldo = valor
    for mes in range(1, meses + 1):
        juros = saldo * taxa  # juros sempre sobre o que ainda falta pagar
        amortizacao = parcela - juros  # o que sobra da parcela abate a dívida
        saldo -= amortizacao
        # max() evita um saldo final como -0,0000001 vindo do ponto flutuante.
        parcelas.append(Parcela(mes, parcela, juros, amortizacao, max(saldo, 0.0)))
    return parcelas


def tabela_sac(valor: float, taxa: float, meses: int) -> list[Parcela]:
    """Sistema SAC: a amortização é fixa; as parcelas começam altas e vão caindo."""
    amortizacao = valor / meses
    parcelas: list[Parcela] = []
    saldo = valor
    for mes in range(1, meses + 1):
        juros = saldo * taxa
        saldo -= amortizacao
        parcelas.append(Parcela(mes, amortizacao + juros, juros, amortizacao, max(saldo, 0.0)))
    return parcelas


def resumir(sistema: str, parcelas: list[Parcela]) -> Resumo:
    """Soma a tabela inteira e guarda a primeira e a última parcela."""
    total_pago = sum(p.valor for p in parcelas)
    total_juros = sum(p.juros for p in parcelas)
    return Resumo(sistema, total_pago, total_juros, parcelas[0].valor, parcelas[-1].valor)


def imprimir_tabela(titulo: str, parcelas: list[Parcela]) -> None:
    """Imprime a tabela de um sistema com as colunas alinhadas."""
    print(titulo)
    cabecalho = f"{'Mês':>4} | {'Parcela':>14} | {'Juros':>13} | {'Amortização':>14} | {'Saldo devedor':>16}"
    print(cabecalho)
    print("-" * len(cabecalho))
    for p in parcelas:
        print(
            f"{p.mes:>4} | {formatar_brl(p.valor):>14} | {formatar_brl(p.juros):>13}"
            f" | {formatar_brl(p.amortizacao):>14} | {formatar_brl(p.saldo_devedor):>16}"
        )
    print()


def imprimir_comparacao(price: Resumo, sac: Resumo, valor: float) -> None:
    """Coloca os dois sistemas lado a lado e diz qual custa menos."""
    print(f"{'Resumo':<22}{'Price':>18}{'SAC':>18}")
    print("-" * 58)
    print(f"{'Valor financiado':<22}{formatar_brl(valor):>18}{formatar_brl(valor):>18}")
    print(f"{'Primeira parcela':<22}{formatar_brl(price.primeira_parcela):>18}{formatar_brl(sac.primeira_parcela):>18}")
    print(f"{'Última parcela':<22}{formatar_brl(price.ultima_parcela):>18}{formatar_brl(sac.ultima_parcela):>18}")
    print(f"{'Total de juros':<22}{formatar_brl(price.total_juros):>18}{formatar_brl(sac.total_juros):>18}")
    print(f"{'Total pago':<22}{formatar_brl(price.total_pago):>18}{formatar_brl(sac.total_pago):>18}")
    diferenca = price.total_pago - sac.total_pago
    if abs(diferenca) < 0.005:
        print("\nOs dois sistemas custam o mesmo (isso só acontece com taxa zero).")
    else:
        print(f"\nO SAC sai {formatar_brl(diferenca)} mais barato no total, mas começa com parcela maior.")
        print("A Price tem parcelas iguais, o que facilita o planejamento, e cobra mais juros no total.")


def executar(valor: float, taxa_percentual: float, meses: int, so_resumo: bool) -> None:
    """Gera as duas tabelas, imprime (se pedido) e compara."""
    taxa = taxa_percentual / 100  # 1 digitado pelo usuário quer dizer 1% ao mês
    price = tabela_price(valor, taxa, meses)
    sac = tabela_sac(valor, taxa, meses)
    taxa_texto = f"{taxa_percentual:.2f}".replace(".", ",")
    print(f"Valor financiado: {formatar_brl(valor)} | taxa {taxa_texto}% ao mês | {meses} meses\n")
    if not so_resumo:
        imprimir_tabela("Sistema Price (parcelas iguais)", price)
        imprimir_tabela("Sistema SAC (amortização constante)", sac)
    imprimir_comparacao(resumir("Price", price), resumir("SAC", sac), valor)


def demo() -> int:
    """Demonstração sem teclado: R$ 50.000 a 1% ao mês em 12 meses."""
    print("=" * 72)
    print("CodeNomad Academy | Simulador de financiamento (Price e SAC) | demonstração")
    print("=" * 72)
    executar(valor=50_000.0, taxa_percentual=1.0, meses=12, so_resumo=False)
    return 0


def montar_parser() -> argparse.ArgumentParser:
    """Define os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Simulador de financiamento nos sistemas Price e SAC (CodeNomad Academy).",
        epilog="Exemplo: --valor 50000 --taxa 1 --meses 12",
    )
    parser.add_argument("--valor", type=positivo, help="valor financiado, em reais")
    parser.add_argument("--taxa", type=nao_negativo, help="taxa mensal em porcentagem (1 = 1%% ao mês)")
    parser.add_argument("--meses", type=meses_validos, help="prazo em meses (1 a 600)")
    parser.add_argument("--resumo", action="store_true", help="mostra só a comparação, sem as tabelas")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa sem pedir nada")
    return parser


def main() -> None:
    """Ponto de entrada: sem argumentos mostra o uso; com --demo demonstra; senão simula."""
    parser = montar_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.demo:
        sys.exit(demo())
    faltando = [nome for nome in ("valor", "taxa", "meses") if getattr(args, nome) is None]
    if faltando:
        parser.error("faltou informar " + ", ".join("--" + nome for nome in faltando) + " (ou use --demo)")
    executar(args.valor, args.taxa, args.meses, args.resumo)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Acrescente --entrada para descontar um valor pago à vista antes de financiar.
# 2. Calcule o CET aproximado somando uma tarifa fixa mensal às parcelas.
# 3. Mostre em que mês a parcela do SAC fica menor que a da Price.
# ------------------------------------------------------------
