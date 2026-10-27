#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  19. Conversor de bases numéricas
# ------------------------------------------------------------
# O que faz: Converte números entre binário, octal, base dez e hexadecimal
#            (na verdade, entre quaisquer bases de 2 a 36), explica o
#            cálculo passo a passo, e converte texto para binário (bytes
#            UTF-8) e de volta.
# Como usar: python 19_conversor_bases.py 255 --de 10 --para 2 --passos
#            python 19_conversor_bases.py FF --de 16
#            python 19_conversor_bases.py --texto "Oi!"
#            python 19_conversor_bases.py --demo
# O que você aprende: divmod e o método de Horner, string.digits e
#            ascii_uppercase como tabela de dígitos, f-strings com formato
#            (08b), bytes e UTF-8, exceções próprias e argparse.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import re
import string
import sys

# Os dígitos de todas as bases até 36: 0 a 9 e depois A a Z.
DIGITOS = string.digits + string.ascii_uppercase
BASES_PADRAO = (2, 8, 10, 16)


def validar_base(base: int) -> None:
    """Garante que a base está no intervalo que a tabela de dígitos cobre."""
    if not 2 <= base <= 36:
        raise ValueError(f"a base precisa estar entre 2 e 36; recebi {base}")


def para_inteiro(texto: str, base: int) -> int:
    """Lê um número escrito em qualquer base e devolve o valor como int."""
    validar_base(base)
    limpo = texto.strip().upper().replace("_", "")
    negativo = limpo.startswith("-")
    if negativo:
        limpo = limpo[1:]
    if not limpo:
        raise ValueError("número vazio")
    valor = 0
    for simbolo in limpo:
        posicao = DIGITOS.find(simbolo)
        if posicao < 0 or posicao >= base:
            raise ValueError(f"o dígito '{simbolo}' não existe na base {base}")
        # Método de Horner: a cada dígito, desloca o que já tinha e soma.
        valor = valor * base + posicao
    return -valor if negativo else valor


def de_inteiro(valor: int, base: int) -> str:
    """Escreve um int em qualquer base: 255 na base 16 vira FF."""
    validar_base(base)
    if valor == 0:
        return "0"
    negativo = valor < 0
    valor = abs(valor)
    digitos: list[str] = []
    while valor:
        valor, resto = divmod(valor, base)
        digitos.append(DIGITOS[resto])
    # Os restos saem do dígito menos significativo para o mais; por isso invertemos.
    return ("-" if negativo else "") + "".join(reversed(digitos))


def converter(texto: str, base_origem: int, base_destino: int) -> str:
    """Passa pelo int, que é a representação neutra entre as bases."""
    return de_inteiro(para_inteiro(texto, base_origem), base_destino)


def explicar_leitura(texto: str, base: int) -> list[str]:
    """Passo a passo de ler um número na base dada: cada dígito vezes base^posição."""
    valor = para_inteiro(texto, base)
    limpo = texto.strip().upper().lstrip("-").replace("_", "")
    linhas = [f"Lendo {limpo} na base {base}, da direita para a esquerda:"]
    for posicao, simbolo in enumerate(reversed(limpo)):
        peso = base ** posicao
        linhas.append(f"  {simbolo} x {base}^{posicao} = {DIGITOS.index(simbolo)} x {peso} = {DIGITOS.index(simbolo) * peso}")
    linhas.append(f"  soma = {abs(valor)}")
    return linhas


def explicar_escrita(valor: int, base: int) -> list[str]:
    """Passo a passo das divisões sucessivas, lendo os restos de baixo para cima."""
    linhas = [f"Escrevendo {valor} na base {base} por divisões sucessivas:"]
    restante = abs(valor)
    restos: list[str] = []
    while restante:
        quociente, resto = divmod(restante, base)
        linhas.append(f"  {restante} / {base} = {quociente}, resto {resto} ({DIGITOS[resto]})")
        restos.append(DIGITOS[resto])
        restante = quociente
    linhas.append(f"  restos de baixo para cima: {de_inteiro(valor, base)}")
    return linhas


def texto_para_binario(texto: str) -> str:
    """Cada byte UTF-8 vira um grupo de 8 bits: 'Oi' vira 01001111 01101001."""
    # :08b formata em binário com 8 posições, completando com zeros à esquerda.
    return " ".join(f"{byte:08b}" for byte in texto.encode("utf-8"))


def binario_para_texto(bits: str) -> str:
    """Faz o caminho inverso: grupos de 8 bits viram bytes, e os bytes viram texto."""
    limpo = re.sub(r"\s+", "", bits)
    if not limpo or re.search(r"[^01]", limpo):
        raise ValueError("a entrada precisa ter só 0 e 1 (espaços são ignorados)")
    if len(limpo) % 8:
        raise ValueError(f"a quantidade de bits precisa ser múltipla de 8; recebi {len(limpo)}")
    dados = bytes(int(limpo[i:i + 8], 2) for i in range(0, len(limpo), 8))
    try:
        return dados.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("esses bytes não formam um texto UTF-8") from None


def imprimir_tabela(texto: str, base_origem: int, bases: tuple[int, ...]) -> None:
    """Mostra o número em cada base de destino, uma por linha."""
    valor = para_inteiro(texto, base_origem)
    print(f"{texto.strip().upper()} (base {base_origem}) = {valor} na base dez")
    for base in bases:
        print(f"  base {base:>2}: {de_inteiro(valor, base)}")


def demo() -> None:
    """Converte vários números, explica um deles e codifica uma palavra."""
    print("=" * 64)
    print("Conversor de bases numéricas: demonstração")
    print("=" * 64)
    print("\nTabela de conversões:\n")
    cabecalho = f"{'entrada':>12} {'base':>4} | {'bin':>14} {'oct':>6} {'dez':>6} {'hex':>5} {'b36':>4}"
    print(cabecalho)
    print("-" * len(cabecalho))
    for texto, base in (("255", 10), ("1024", 10), ("11111111", 2), ("777", 8), ("1AF", 16), ("ZZ", 36)):
        valor = para_inteiro(texto, base)
        colunas = [de_inteiro(valor, b) for b in (2, 8, 10, 16, 36)]
        print(f"{texto:>12} {base:>4} | {colunas[0]:>14} {colunas[1]:>6} {colunas[2]:>6} {colunas[3]:>5} {colunas[4]:>4}")
    print()
    print("\n".join(explicar_escrita(173, 2)))
    print()
    print("\n".join(explicar_leitura("1AF", 16)))
    palavra = "Oi!"
    bits = texto_para_binario(palavra)
    print(f"\nTexto para binário: {palavra!r} -> {bits}")
    print(f"Binário para texto: {bits} -> {binario_para_texto(bits)!r}")
    print(f"Com acento, 'ç' ocupa dois bytes: {texto_para_binario('ç')}")


def construir_parser() -> argparse.ArgumentParser:
    """Define a linha de comando do programa."""
    parser = argparse.ArgumentParser(
        description="Converte números entre bases de 2 a 36 e texto para binário.",
        epilog="Exemplo: python 19_conversor_bases.py 1AF --de 16 --para 2 --passos",
    )
    parser.add_argument("numero", nargs="?",
                        help="o número a converter (negativo com letras, como -1F: escreva -- antes dele)")
    parser.add_argument("--de", type=int, default=10, metavar="BASE",
                        help="base de origem (padrão: 10)")
    parser.add_argument("--para", type=int, metavar="BASE",
                        help="base de destino (sem ela, mostra 2, 8, 10 e 16)")
    parser.add_argument("--passos", action="store_true",
                        help="explica o cálculo passo a passo")
    parser.add_argument("--texto", metavar="TEXTO", help="codifica um texto em binário")
    parser.add_argument("--bits", metavar="BITS", help="decodifica bits em texto")
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: devolve 1 quando a entrada não pode ser convertida."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    if args.numero is None and not args.texto and not args.bits:
        parser.print_help()
        return 0
    try:
        if args.texto:
            print(texto_para_binario(args.texto))
        if args.bits:
            print(binario_para_texto(args.bits))
        if args.numero is not None:
            if args.para is None:
                imprimir_tabela(args.numero, args.de, BASES_PADRAO)
            else:
                print(converter(args.numero, args.de, args.para))
            if args.passos:
                valor = para_inteiro(args.numero, args.de)
                if args.de != 10:
                    print("\n".join(explicar_leitura(args.numero, args.de)))
                print("\n".join(explicar_escrita(valor, args.para or 2)))
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Aceite os prefixos 0b, 0o e 0x na entrada e descubra a base sozinho.
#   2. Converta números com parte fracionária: 0.1 em binário é uma dízima,
#      e isso explica por que 0.1 + 0.2 não dá exatamente 0.3.
#   3. Mostre negativos em complemento de dois com 8, 16 e 32 bits.
# ------------------------------------------------------------
