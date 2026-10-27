#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  18. Conversor de números romanos
# ------------------------------------------------------------
# O que faz: Converte inteiros de 1 a 3999 para algarismos romanos e
#            romanos para inteiros, rejeitando formas mal escritas como
#            IIII, VX ou IM. Mostra a decomposição de cada número e uma
#            tabela de referência com os símbolos e os pares subtrativos.
# Como usar: python 18_numeros_romanos.py 1994 MMXXIV 3999 --explicar
#            python 18_numeros_romanos.py --tabela
#            python 18_numeros_romanos.py --demo
# O que você aprende: divmod, listas de tuplas como tabela de consulta,
#            algoritmo guloso, validação por ida e volta (codifica de novo e
#            compara), exceções com mensagens úteis e enumerate.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import sys

# Do maior para o menor, incluindo os pares subtrativos (CM, XC, IV...).
# A ordem importa: o algoritmo guloso tenta sempre o maior valor que cabe.
VALORES: list[tuple[int, str]] = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
    (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]
SIMBOLOS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
MINIMO, MAXIMO = 1, 3999


def decompor(numero: int) -> list[tuple[str, int]]:
    """Quebra o número nos pedaços romanos: 1994 vira M, CM, XC, IV."""
    if not MINIMO <= numero <= MAXIMO:
        raise ValueError(f"só existem romanos de {MINIMO} a {MAXIMO}; recebi {numero}")
    partes: list[tuple[str, int]] = []
    restante = numero
    for valor, simbolo in VALORES:
        # divmod devolve quantas vezes o valor cabe e o que sobra.
        vezes, restante = divmod(restante, valor)
        partes.extend([(simbolo, valor)] * vezes)
    return partes


def para_romano(numero: int) -> str:
    """Inteiro para romano: 1994 vira MCMXCIV."""
    return "".join(simbolo for simbolo, _ in decompor(numero))


def para_inteiro(romano: str) -> int:
    """Romano para inteiro, aceitando minúsculas e rejeitando formas erradas."""
    texto = romano.strip().upper()
    if not texto:
        raise ValueError("texto vazio")
    estranhos = sorted(set(texto) - SIMBOLOS.keys())
    if estranhos:
        raise ValueError(f"'{romano}' tem símbolos que não são romanos: {', '.join(estranhos)}")
    total = 0
    for i, simbolo in enumerate(texto):
        valor = SIMBOLOS[simbolo]
        proximo = SIMBOLOS[texto[i + 1]] if i + 1 < len(texto) else 0
        # Um símbolo menor antes de um maior subtrai: IV = 4, IX = 9.
        total += -valor if valor < proximo else valor
    # Validação por ida e volta: se escrever o total de novo não der o mesmo
    # texto, a forma original estava errada (IIII, VX, IM, MMMM...).
    if not MINIMO <= total <= MAXIMO or para_romano(total) != texto:
        correta = para_romano(total) if MINIMO <= total <= MAXIMO else "nada"
        raise ValueError(f"'{romano}' não é uma forma válida; {total} se escreve {correta}")
    return total


def explicar(numero: int) -> str:
    """Monta a frase 'MCMXCIV = M (1000) + CM (900) + XC (90) + IV (4)'."""
    partes = " + ".join(f"{simbolo} ({valor})" for simbolo, valor in decompor(numero))
    return f"{para_romano(numero)} = {partes}"


def converter(valor: str) -> str:
    """Decide pelo conteúdo: só dígitos vira romano, letras viram inteiro."""
    if valor.strip().isdigit():
        return f"{int(valor):>6}  ->  {para_romano(int(valor))}"
    return f"{valor.strip().upper():>6}  ->  {para_inteiro(valor)}"


def tabela_referencia() -> None:
    """Imprime os símbolos básicos, os pares subtrativos e as regras."""
    print("Símbolos básicos:")
    for simbolo, valor in SIMBOLOS.items():
        print(f"  {simbolo} = {valor:>4}")
    print("\nPares subtrativos (menor antes do maior):")
    for valor, simbolo in VALORES:
        if len(simbolo) == 2:
            print(f"  {simbolo} = {valor:>4}")
    print("\nRegras: I, X, C e M repetem no máximo três vezes; V, L e D nunca repetem;")
    print(f"só I, X e C subtraem, e apenas do par seguinte. Faixa: {MINIMO} a {MAXIMO}.")


def demo() -> None:
    """Converte nos dois sentidos, explica dois números e rejeita entradas ruins."""
    print("=" * 64)
    print("Conversor de números romanos: demonstração")
    print("=" * 64)
    print("\nInteiro para romano e de volta:\n")
    for numero in (1, 4, 9, 14, 40, 90, 400, 1994, 2024, 3999):
        romano = para_romano(numero)
        print(f"  {numero:>5}  ->  {romano:<10}  ->  {para_inteiro(romano)}")
    print("\nDecomposição:\n")
    for numero in (1994, 2024, 3888):
        print(f"  {explicar(numero)}")
    print("\nEntradas rejeitadas:\n")
    for ruim in ("IIII", "VX", "IM", "ABC", "4000", "0"):
        try:
            print(f"  {converter(ruim)}")
        except ValueError as erro:
            print(f"  {ruim:<6}  ->  erro: {erro}")


def construir_parser() -> argparse.ArgumentParser:
    """Define a linha de comando do programa."""
    parser = argparse.ArgumentParser(
        description="Converte inteiros em romanos e romanos em inteiros (1 a 3999).",
        epilog="Exemplo: python 18_numeros_romanos.py 2024 MCMXCIV --explicar",
    )
    parser.add_argument("valores", nargs="*", metavar="VALOR",
                        help="inteiros ou romanos, em qualquer ordem")
    parser.add_argument("--explicar", action="store_true",
                        help="mostra a decomposição de cada número")
    parser.add_argument("--tabela", action="store_true",
                        help="imprime a tabela de referência")
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: devolve 1 se algum valor não puder ser convertido."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    if args.tabela:
        tabela_referencia()
    if not args.valores and not args.tabela:
        parser.print_help()
        return 0
    falhas = 0
    for valor in args.valores:
        try:
            print(converter(valor))
            if args.explicar:
                numero = int(valor) if valor.strip().isdigit() else para_inteiro(valor)
                print(f"        {explicar(numero)}")
        except ValueError as erro:
            print(f"Erro: {erro}", file=sys.stderr)
            falhas += 1
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Aceite números acima de 3999 usando a notação com traço em cima
#      (vinculum), representada aqui por um sublinhado: _V = 5000.
#   2. Escreva os anos de 1 a 3999 em romano e descubra qual é o mais
#      longo e quantos têm exatamente quatro letras.
#   3. Faça a validação sem recodificar: implemente as regras de repetição
#      e subtração uma a uma e compare os dois jeitos.
# ------------------------------------------------------------
