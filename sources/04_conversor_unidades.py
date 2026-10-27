#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  04. Conversor de unidades
# ------------------------------------------------------------
# O que faz: converte valores entre unidades de comprimento, massa, volume,
#            velocidade e temperatura. Cada categoria tem uma tabela de
#            fatores em relação a uma unidade base; a temperatura é a exceção
#            e usa fórmulas próprias. Também lista as unidades disponíveis.
# Como usar: python 04_conversor_unidades.py --valor 10 --de km --para mi
#            python 04_conversor_unidades.py --valor 36 --de c --para f
#            python 04_conversor_unidades.py --listar
#            python 04_conversor_unidades.py --demo
# O que você aprende: dicionários aninhados como tabela de dados, a técnica
#            de converter sempre passando pela unidade base, tratamento de
#            exceções com mensagens claras e busca em estruturas de dados.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import sys

# Para cada categoria: sigla -> (nome, quantas unidades BASE cabem em uma unidade).
# A base é a unidade com fator 1.0. Converter de A para B é multiplicar pelo
# fator de A (vira base) e dividir pelo fator de B (sai da base).
CATEGORIAS: dict[str, dict[str, tuple[str, float]]] = {
    "comprimento": {
        "mm": ("milímetro", 0.001),
        "cm": ("centímetro", 0.01),
        "m": ("metro", 1.0),
        "km": ("quilômetro", 1000.0),
        "in": ("polegada", 0.0254),
        "ft": ("pé", 0.3048),
        "yd": ("jarda", 0.9144),
        "mi": ("milha", 1609.344),
    },
    "massa": {
        "mg": ("miligrama", 0.000001),
        "g": ("grama", 0.001),
        "kg": ("quilograma", 1.0),
        "t": ("tonelada", 1000.0),
        "oz": ("onça", 0.028349523125),
        "lb": ("libra", 0.45359237),
    },
    "volume": {
        "ml": ("mililitro", 0.001),
        "l": ("litro", 1.0),
        "m3": ("metro cúbico", 1000.0),
        "xic": ("xícara de 240 ml", 0.24),
        "gal": ("galão americano", 3.785411784),
    },
    "velocidade": {
        "m/s": ("metro por segundo", 1.0),
        "km/h": ("quilômetro por hora", 1 / 3.6),
        "mph": ("milha por hora", 0.44704),
        "kn": ("nó", 0.514444),
    },
}
# A temperatura não é proporcional (0 °C não é 0 °F), então tem tratamento próprio.
TEMPERATURAS: dict[str, str] = {"c": "grau Celsius", "f": "grau Fahrenheit", "k": "kelvin"}
ZERO_ABSOLUTO_C = -273.15


def numero(texto: str) -> float:
    """Converte texto em número, aceitando tanto '2.5' quanto '2,5'."""
    try:
        return float(texto.strip().replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um número válido") from None


def categoria_de(unidade: str) -> str:
    """Descobre em qual categoria a sigla está. Levanta ValueError se não existir."""
    if unidade in TEMPERATURAS:
        return "temperatura"
    for nome, tabela in CATEGORIAS.items():
        if unidade in tabela:
            return nome
    raise ValueError(f"unidade desconhecida: '{unidade}' (use --listar para ver as siglas)")


def para_celsius(valor: float, unidade: str) -> float:
    """Leva qualquer temperatura para Celsius, a base desta categoria."""
    if unidade == "f":
        return (valor - 32) * 5 / 9
    if unidade == "k":
        return valor + ZERO_ABSOLUTO_C
    return valor


def de_celsius(valor: float, unidade: str) -> float:
    """Leva uma temperatura em Celsius para a unidade pedida."""
    if unidade == "f":
        return valor * 9 / 5 + 32
    if unidade == "k":
        return valor - ZERO_ABSOLUTO_C
    return valor


def converter(valor: float, de: str, para: str) -> float:
    """Converte entre duas unidades da mesma categoria. Levanta ValueError se não der."""
    de, para = de.lower(), para.lower()
    categoria_origem, categoria_destino = categoria_de(de), categoria_de(para)
    if categoria_origem != categoria_destino:
        raise ValueError(
            f"não dá para converter {categoria_origem} em {categoria_destino} ('{de}' para '{para}')"
        )
    if categoria_origem == "temperatura":
        celsius = para_celsius(valor, de)
        if celsius < ZERO_ABSOLUTO_C:
            raise ValueError(f"{valor} {de} fica abaixo do zero absoluto ({ZERO_ABSOLUTO_C} °C)")
        return de_celsius(celsius, para)
    tabela = CATEGORIAS[categoria_origem]
    return valor * tabela[de][1] / tabela[para][1]


def nome_da_unidade(unidade: str) -> str:
    """Nome por extenso da sigla, para as mensagens ficarem legíveis."""
    unidade = unidade.lower()
    if unidade in TEMPERATURAS:
        return TEMPERATURAS[unidade]
    return CATEGORIAS[categoria_de(unidade)][unidade][0]


def formatar(valor: float) -> str:
    """Mostra até 6 casas, cortando zeros à direita, com vírgula brasileira."""
    texto = f"{valor:,.6f}".rstrip("0").rstrip(".")
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def listar_unidades() -> None:
    """Imprime todas as siglas, agrupadas por categoria."""
    for categoria, tabela in CATEGORIAS.items():
        print(f"{categoria.capitalize()}:")
        for sigla, (nome, fator) in tabela.items():
            print(f"  {sigla:<6} {nome:<22} (1 {sigla} = {formatar(fator)} da unidade base)")
    print("Temperatura:")
    for sigla, nome in TEMPERATURAS.items():
        print(f"  {sigla:<6} {nome}")


def imprimir_conversao(valor: float, de: str, para: str) -> None:
    """Converte e imprime no formato 'de onde para onde'."""
    resultado = converter(valor, de, para)
    print(f"{formatar(valor)} {de} ({nome_da_unidade(de)}) = {formatar(resultado)} {para} ({nome_da_unidade(para)})")


def demo() -> int:
    """Demonstração sem teclado: dez conversões variadas e um erro tratado."""
    print("=" * 72)
    print("CodeNomad Academy | Conversor de unidades | demonstração")
    print("=" * 72)
    exemplos: list[tuple[float, str, str]] = [
        (10, "km", "mi"), (1.80, "m", "ft"), (12, "in", "cm"), (75, "kg", "lb"),
        (500, "g", "oz"), (2, "l", "xic"), (10, "gal", "l"), (100, "km/h", "m/s"),
        (30, "kn", "km/h"), (36.6, "c", "f"),
    ]
    for valor, de, para in exemplos:
        imprimir_conversao(valor, de, para)
    print()
    print("Tentando converter quilos em metros (erro esperado e tratado):")
    try:
        converter(1, "kg", "m")
    except ValueError as erro:
        print(f"  Erro: {erro}")
    return 0


def montar_parser() -> argparse.ArgumentParser:
    """Define os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Conversor de unidades de comprimento, massa, volume, velocidade e temperatura.",
        epilog="Exemplo: --valor 10 --de km --para mi",
    )
    parser.add_argument("--valor", type=numero, help="quantidade a converter")
    parser.add_argument("--de", help="sigla da unidade de origem (ex.: km, kg, l, km/h, c)")
    parser.add_argument("--para", help="sigla da unidade de destino")
    parser.add_argument("--listar", action="store_true", help="lista as unidades disponíveis")
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
        listar_unidades()
        return
    if args.valor is None or not args.de or not args.para:
        parser.error("informe --valor, --de e --para (ou use --listar / --demo)")
    try:
        imprimir_conversao(args.valor, args.de.lower(), args.para.lower())
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Acrescente a categoria "área" (m2, ha, km2, acre) seguindo o mesmo padrão.
# 2. Aceite a entrada no formato "10km" em um argumento só, separando o número da sigla.
# 3. Leia várias conversões de um arquivo de texto e imprima todas de uma vez.
# ------------------------------------------------------------
