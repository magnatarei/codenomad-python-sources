#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  05. Conversor de moedas com tabela de taxas
# ------------------------------------------------------------
# O que faz: converte um valor entre duas moedas usando uma tabela de taxas
#            embutida no código (com a data em que ela foi montada). Lista a
#            tabela inteira e mostra a taxa cruzada de cada conversão.
#            Para atualizar: edite DATA_DA_TABELA e TAXAS logo abaixo com as
#            cotações de uma fonte confiável. Todas as taxas são "quantos
#            reais vale uma unidade", então basta manter essa única coluna.
# Como usar: python 05_conversor_moedas.py --valor 100 --de USD --para EUR
#            python 05_conversor_moedas.py --listar
#            python 05_conversor_moedas.py --demo
# O que você aprende: constantes de configuração no topo do arquivo,
#            dicionário como tabela de consulta, conversão por uma moeda
#            pivô, normalização de entrada (maiúsculas) e formatação de números.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import sys

# Valores aproximados, apenas para estudo. Antes de usar de verdade, atualize
# com cotações do dia e troque a data abaixo.
DATA_DA_TABELA = "2026-10-01"
MOEDA_PIVO = "BRL"
# sigla -> (nome, quantos reais vale UMA unidade desta moeda)
TAXAS: dict[str, tuple[str, float]] = {
    "BRL": ("Real brasileiro", 1.0),
    "USD": ("Dólar americano", 5.42),
    "EUR": ("Euro", 6.31),
    "GBP": ("Libra esterlina", 7.24),
    "JPY": ("Iene japonês", 0.0362),
    "ARS": ("Peso argentino", 0.0039),
    "CHF": ("Franco suíço", 6.78),
    "CAD": ("Dólar canadense", 3.93),
    "AUD": ("Dólar australiano", 3.57),
    "CNY": ("Yuan chinês", 0.76),
    "MXN": ("Peso mexicano", 0.29),
    "CLP": ("Peso chileno", 0.0057),
    "UYU": ("Peso uruguaio", 0.13),
}


def numero(texto: str) -> float:
    """Converte texto em número, aceitando tanto '100.5' quanto '100,5'."""
    try:
        valor = float(texto.strip().replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um número válido") from None
    if valor < 0:
        raise argparse.ArgumentTypeError("o valor não pode ser negativo")
    return valor


def sigla(texto: str) -> str:
    """Normaliza a sigla (usd vira USD) e confere se ela existe na tabela."""
    codigo_moeda = texto.strip().upper()
    if codigo_moeda not in TAXAS:
        conhecidas = ", ".join(TAXAS)
        raise argparse.ArgumentTypeError(f"moeda desconhecida: '{texto}'. Conhecidas: {conhecidas}")
    return codigo_moeda


def taxa_cruzada(de: str, para: str) -> float:
    """Quantas unidades de 'para' valem uma unidade de 'de'.

    Passamos pela moeda pivô (o real): 1 de = X reais, e 1 para = Y reais,
    logo 1 de = X / Y para. Assim a tabela precisa de uma coluna só.
    """
    return TAXAS[de][1] / TAXAS[para][1]


def converter(valor: float, de: str, para: str) -> float:
    """Aplica a taxa cruzada ao valor."""
    return valor * taxa_cruzada(de, para)


def formatar(valor: float, casas: int = 2) -> str:
    """Formata com separador de milhar e vírgula, no padrão brasileiro."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def imprimir_conversao(valor: float, de: str, para: str) -> None:
    """Imprime o resultado e a taxa usada, para o usuário conferir a conta."""
    resultado = converter(valor, de, para)
    taxa = taxa_cruzada(de, para)
    print(
        f"{formatar(valor)} {de} ({TAXAS[de][0]}) = {formatar(resultado)} {para} ({TAXAS[para][0]})"
        f"   [1 {de} = {formatar(taxa, 4)} {para}]"
    )


def imprimir_tabela() -> None:
    """Lista todas as moedas com a taxa em reais e o inverso (quanto vale 1 real)."""
    print(f"Tabela de taxas de {DATA_DA_TABELA} (moeda pivô: {MOEDA_PIVO})")
    cabecalho = f"{'Sigla':<6}{'Moeda':<20}{'1 unidade em BRL':>18}{'1 BRL em unidades':>20}"
    print(cabecalho)
    print("-" * len(cabecalho))
    for codigo_moeda, (nome, em_reais) in TAXAS.items():
        print(f"{codigo_moeda:<6}{nome:<20}{formatar(em_reais, 4):>18}{formatar(1 / em_reais, 4):>20}")


def demo() -> int:
    """Demonstração sem teclado: 100 unidades em seis pares de moedas e a tabela."""
    print("=" * 72)
    print("CodeNomad Academy | Conversor de moedas | demonstração")
    print("=" * 72)
    pares = [("USD", "BRL"), ("EUR", "USD"), ("BRL", "ARS"), ("GBP", "JPY"), ("JPY", "BRL"), ("CHF", "EUR")]
    for de, para in pares:
        imprimir_conversao(100, de, para)
    print()
    imprimir_tabela()
    print()
    print("Para atualizar as taxas, edite TAXAS e DATA_DA_TABELA no topo do arquivo.")
    return 0


def montar_parser() -> argparse.ArgumentParser:
    """Define os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description=f"Conversor de moedas com tabela embutida de {DATA_DA_TABELA} (CodeNomad Academy).",
        epilog="Exemplo: --valor 100 --de USD --para EUR",
    )
    parser.add_argument("--valor", type=numero, help="quantidade a converter")
    parser.add_argument("--de", type=sigla, help="sigla da moeda de origem (ex.: USD)")
    parser.add_argument("--para", type=sigla, help="sigla da moeda de destino (ex.: BRL)")
    parser.add_argument("--listar", action="store_true", help="imprime a tabela de taxas")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa sem pedir nada")
    return parser


def main() -> None:
    """Ponto de entrada: sem argumentos mostra o uso; --listar, --demo ou uma conversão."""
    parser = montar_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.demo:
        sys.exit(demo())
    if args.listar:
        imprimir_tabela()
        return
    if args.valor is None or args.de is None or args.para is None:
        parser.error("informe --valor, --de e --para (ou use --listar / --demo)")
    imprimir_conversao(args.valor, args.de, args.para)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Leia a tabela de um arquivo CSV (sigla;nome;taxa) em vez de deixá-la no código.
# 2. Acrescente --spread para simular a diferença entre compra e venda de uma casa de câmbio.
# 3. Mostre quantos dias se passaram desde DATA_DA_TABELA e avise quando passar de 30.
# ------------------------------------------------------------
