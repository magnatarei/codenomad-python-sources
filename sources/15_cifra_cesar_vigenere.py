#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  15. Cifra de César e de Vigenère
# ------------------------------------------------------------
# O que faz: Codifica e decodifica textos com a cifra de César (um
#            deslocamento fixo) e com a de Vigenère (uma palavra-chave),
#            preservando maiúsculas, espaços e pontuação. Inclui um
#            quebrador de César que descobre a chave comparando a
#            frequência das letras com a do português.
# Como usar: python 15_cifra_cesar_vigenere.py cesar "Ataque ao amanhecer" --chave 3
#            python 15_cifra_cesar_vigenere.py vigenere "Dwdtxh" --chave LIMAO --decifrar
#            python 15_cifra_cesar_vigenere.py quebrar "DWDTXH DR DPDQKHFHU"
#            python 15_cifra_cesar_vigenere.py --demo
# O que você aprende: aritmética modular com letras (ord e chr), subcomandos
#            do argparse, Counter, qui-quadrado como medida de ajuste,
#            dicionários de frequência e unicodedata para tirar acentos.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import string
import sys
import unicodedata
from collections import Counter

ALFABETO = string.ascii_uppercase
TAMANHO = len(ALFABETO)

# Frequência (em porcentagem) de cada letra em textos longos de português.
FREQUENCIA_PT = {
    "A": 14.63, "B": 1.04, "C": 3.88, "D": 4.99, "E": 12.57, "F": 1.02,
    "G": 1.30, "H": 1.28, "I": 6.18, "J": 0.40, "K": 0.02, "L": 2.78,
    "M": 4.74, "N": 5.05, "O": 10.73, "P": 2.52, "Q": 1.20, "R": 6.53,
    "S": 7.81, "T": 4.34, "U": 4.63, "V": 1.67, "W": 0.01, "X": 0.21,
    "Y": 0.01, "Z": 0.47,
}

TEXTO_LONGO = (
    "A cifra de César é uma das mais antigas que se conhece. Júlio César a usava "
    "para proteger mensagens militares, deslocando cada letra três posições. Hoje "
    "ela serve para ensinar: com apenas vinte e seis chaves possíveis, qualquer "
    "computador a quebra em um piscar de olhos, e a frequência das letras entrega "
    "a chave sem esforço."
)


def remover_acentos(texto: str) -> str:
    """Troca é por e, ç por c etc. As cifras só trabalham com A a Z."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def deslocar_letra(letra: str, deslocamento: int) -> str:
    """Desloca uma letra A-Z ou a-z dentro do alfabeto; o resto passa intacto."""
    if not (letra.isascii() and letra.isalpha()):
        return letra
    base = ord("A") if letra.isupper() else ord("a")
    # ord dá o código da letra; o módulo 26 faz Z voltar para A.
    return chr(base + (ord(letra) - base + deslocamento) % TAMANHO)


def cesar(texto: str, chave: int, decifrar: bool = False) -> str:
    """Aplica o mesmo deslocamento a todas as letras do texto."""
    passo = -chave if decifrar else chave
    return "".join(deslocar_letra(c, passo) for c in texto)


def vigenere(texto: str, chave: str, decifrar: bool = False) -> str:
    """Cada letra do texto usa a próxima letra da chave como deslocamento."""
    letras_chave = [c for c in remover_acentos(chave).upper() if c.isalpha()]
    if not letras_chave:
        raise ValueError("a chave precisa ter pelo menos uma letra")
    saida: list[str] = []
    posicao = 0  # só avança quando ciframos uma letra de verdade
    for c in texto:
        if c.isascii() and c.isalpha():
            passo = ord(letras_chave[posicao % len(letras_chave)]) - ord("A")
            saida.append(deslocar_letra(c, -passo if decifrar else passo))
            posicao += 1
        else:
            saida.append(c)
    return "".join(saida)


def pontuar(texto: str) -> float:
    """Qui-quadrado: quanto menor, mais o texto parece português."""
    contagem = Counter(c for c in texto.upper() if c in FREQUENCIA_PT)
    total = sum(contagem.values())
    if total == 0:
        return float("inf")
    pontos = 0.0
    for letra, esperado_pct in FREQUENCIA_PT.items():
        esperado = total * esperado_pct / 100
        pontos += (contagem[letra] - esperado) ** 2 / esperado
    return pontos


def quebrar_cesar(texto: str, candidatos: int = 3) -> list[tuple[int, float, str]]:
    """Testa os 26 deslocamentos e devolve os mais prováveis, do melhor ao pior."""
    resultados = []
    for chave in range(TAMANHO):
        tentativa = cesar(texto, chave, decifrar=True)
        resultados.append((chave, pontuar(tentativa), tentativa))
    resultados.sort(key=lambda item: item[1])
    return resultados[:candidatos]


def imprimir_candidatos(texto: str, candidatos: int) -> None:
    """Mostra a tabela de chaves prováveis e o texto da melhor."""
    melhores = quebrar_cesar(texto, candidatos)
    print(f"{'chave':>5}  {'qui-quadrado':>12}  início do texto decifrado")
    for chave, pontos, tentativa in melhores:
        print(f"{chave:>5}  {pontos:>12.1f}  {tentativa[:48]}")
    print(f"\nMelhor candidata (chave {melhores[0][0]}):\n{melhores[0][2]}")


def demo() -> None:
    """Cifra e decifra uma frase nos dois métodos e quebra um texto de César."""
    print("=" * 64)
    print("Cifra de César e de Vigenère: demonstração")
    print("=" * 64)
    frase = remover_acentos("Programar bem exige paciência, prática e café.")
    print(f"\nFrase (sem acentos):   {frase}")
    cifrada = cesar(frase, 3)
    print(f"César, chave 3:        {cifrada}")
    print(f"Decifrada:             {cesar(cifrada, 3, decifrar=True)}")
    cifrada = vigenere(frase, "NOMADE")
    print(f"Vigenère, chave NOMADE: {cifrada}")
    print(f"Decifrada:             {vigenere(cifrada, 'NOMADE', decifrar=True)}")

    print("\nQuebrando um texto cifrado com César sem conhecer a chave:")
    segredo = cesar(remover_acentos(TEXTO_LONGO), 11)
    print(f"{segredo[:72]}...\n")
    imprimir_candidatos(segredo, candidatos=3)
    print("\nAs letras acentuadas passam intactas pelas cifras; por isso o")
    print("programa oferece --sem-acentos para trocá-las antes de cifrar.")


def construir_parser() -> argparse.ArgumentParser:
    """Define os três subcomandos: cesar, vigenere e quebrar."""
    parser = argparse.ArgumentParser(
        description="Cifra de César, cifra de Vigenère e quebra de César por frequência.",
        epilog="Exemplo: python 15_cifra_cesar_vigenere.py cesar \"Ola mundo\" --chave 5",
    )
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    sub = parser.add_subparsers(dest="comando", metavar="COMANDO")

    p_cesar = sub.add_parser("cesar", help="desloca cada letra um número fixo de posições")
    p_cesar.add_argument("texto")
    p_cesar.add_argument("--chave", type=int, required=True, help="deslocamento (ex.: 3)")
    p_cesar.add_argument("--decifrar", action="store_true", help="desfaz a cifra")
    p_cesar.add_argument("--sem-acentos", action="store_true", help="tira os acentos antes")

    p_vig = sub.add_parser("vigenere", help="usa uma palavra-chave como deslocamentos")
    p_vig.add_argument("texto")
    p_vig.add_argument("--chave", required=True, help="palavra-chave (só letras)")
    p_vig.add_argument("--decifrar", action="store_true", help="desfaz a cifra")
    p_vig.add_argument("--sem-acentos", action="store_true", help="tira os acentos antes")

    p_quebrar = sub.add_parser("quebrar", help="descobre a chave de César pela frequência")
    p_quebrar.add_argument("texto")
    p_quebrar.add_argument("--candidatos", type=int, default=3,
                           help="quantas chaves prováveis mostrar (padrão: 3)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: devolve 1 quando a chave não serve."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    if args.comando is None:
        parser.print_help()
        return 0
    try:
        if args.comando == "cesar":
            texto = remover_acentos(args.texto) if args.sem_acentos else args.texto
            print(cesar(texto, args.chave, args.decifrar))
        elif args.comando == "vigenere":
            texto = remover_acentos(args.texto) if args.sem_acentos else args.texto
            print(vigenere(texto, args.chave, args.decifrar))
        else:
            if args.candidatos < 1:
                raise ValueError("--candidatos precisa ser pelo menos 1")
            if not any(c.isascii() and c.isalpha() for c in args.texto):
                raise ValueError("o texto não tem letras para analisar")
            imprimir_candidatos(args.texto, args.candidatos)
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Implemente a cifra Atbash (A vira Z, B vira Y) e a ROT13, que é
#      um César de chave 13 que se desfaz aplicando de novo.
#   2. Quebre Vigenère: use o exame de Kasiski para estimar o tamanho da
#      chave e aplique quebrar_cesar em cada coluna do texto.
#   3. Amplie o alfabeto para incluir dígitos e letras acentuadas, cuidando
#      para que o módulo use o novo tamanho.
# ------------------------------------------------------------
