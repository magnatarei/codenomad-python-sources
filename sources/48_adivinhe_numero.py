#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  48. Adivinhe o número, nos dois sentidos
# ------------------------------------------------------------
# O que faz: Modo 1: o computador sorteia um número e você adivinha com dicas
#            de "maior" ou "menor". Modo 2: você pensa num número e o
#            computador adivinha por busca binária, em até 7 palpites entre
#            1 e 100, e ainda percebe quando as respostas se contradizem.
# Como usar: python 48_adivinhe_numero.py                       (modo 1, de 1 a 100)
#            python 48_adivinhe_numero.py --computador --max 1000  (modo 2)
#            python 48_adivinhe_numero.py --demo
# O que você aprende: busca binária, funções como argumento (Callable),
#            exceção própria, random com semente, math.log2, laços while
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import math
import random
from typing import Callable

# O "oráculo" é quem sabe o segredo: responde a cada palpite com uma destas palavras.
MAIOR, MENOR, ACERTOU = "maior", "menor", "acertou"
Oraculo = Callable[[int], str]


class EntradaEncerrada(Exception):
    """O jogador fechou a entrada (Ctrl+C, Ctrl+D ou fim do arquivo)."""


def palpites_necessarios(minimo: int, maximo: int) -> int:
    """Quantos palpites a busca binária precisa, no pior caso, para o intervalo."""
    return math.ceil(math.log2(maximo - minimo + 1))


def ler_inteiro(pergunta: str) -> int:
    """Lê um inteiro do teclado; insiste enquanto vier texto inválido."""
    while True:
        try:
            texto = input(pergunta).strip()
        except (EOFError, KeyboardInterrupt):
            raise EntradaEncerrada() from None
        try:
            return int(texto)
        except ValueError:
            print(f"  '{texto}' não é um número inteiro.")


def comentario(tentativas: int, limite: int) -> str:
    """Compara o desempenho do jogador com o da busca binária."""
    if tentativas < limite:
        return f"Melhor que a busca binária, que precisaria de até {limite}."
    if tentativas == limite:
        return "Exatamente o limite da busca binária."
    return f"A busca binária faria em até {limite}."


def modo_voce_adivinha(minimo: int, maximo: int, rng: random.Random) -> None:
    """Modo 1: o computador sorteia, você chuta e recebe dicas."""
    segredo = rng.randint(minimo, maximo)
    limite = palpites_necessarios(minimo, maximo)
    print(f"Pensei num número entre {minimo} e {maximo}. Dica: cortando o intervalo ao meio, "
          f"dá para acertar em até {limite} palpites.")
    tentativas = 0
    while True:
        try:
            palpite = ler_inteiro(f"Palpite {tentativas + 1}: ")
        except EntradaEncerrada:
            print(f"\nEntrada encerrada. O número era {segredo}.")
            return
        if not minimo <= palpite <= maximo:
            print(f"  Fique entre {minimo} e {maximo}.")
            continue
        tentativas += 1
        if palpite == segredo:
            print(f"Acertou em {tentativas} palpite(s)! {comentario(tentativas, limite)}")
            return
        print("  O número é maior." if palpite < segredo else "  O número é menor.")


def busca_binaria(minimo: int, maximo: int, oraculo: Oraculo) -> int | None:
    """Adivinha perguntando ao oráculo: cada resposta corta o intervalo pela metade.

    Devolve o número descoberto, ou None quando as respostas se contradizem
    (o intervalo fica vazio sem ninguém ter dito "acertou").
    """
    baixo, alto = minimo, maximo
    tentativa = 0
    while baixo <= alto:
        tentativa += 1
        palpite = (baixo + alto) // 2  # o meio do intervalo que ainda é possível
        resposta = oraculo(palpite)
        if resposta == ACERTOU:
            print(f"Palpite {tentativa}: {palpite}? Acertou!")
            return palpite
        if resposta == MAIOR:
            baixo = palpite + 1
        else:
            alto = palpite - 1
        if baixo <= alto:
            print(f"Palpite {tentativa}: {palpite}? {resposta}. Agora só pode ser de {baixo} a {alto}.")
        else:
            print(f"Palpite {tentativa}: {palpite}? {resposta}. Não sobrou nenhum número possível.")
    return None


def oraculo_do_teclado(palpite: int) -> str:
    """Pergunta ao jogador se o número dele é maior, menor ou igual ao palpite."""
    opcoes = {"m": MAIOR, "n": MENOR, "a": ACERTOU}
    while True:
        try:
            resposta = input(f"É {palpite}? Responda (m)aior, me(n)or ou (a)certou: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise EntradaEncerrada() from None
        if resposta[:1] in opcoes:
            return opcoes[resposta[:1]]
        print("  Responda com m, n ou a.")


def modo_computador_adivinha(minimo: int, maximo: int) -> None:
    """Modo 2: você pensa num número e o computador descobre."""
    print(f"Pense num número entre {minimo} e {maximo}. Descubro em até "
          f"{palpites_necessarios(minimo, maximo)} palpites.")
    try:
        resultado = busca_binaria(minimo, maximo, oraculo_do_teclado)
    except EntradaEncerrada:
        print("\nEntrada encerrada.")
        return
    if resultado is None:
        print("As respostas se contradizem. Você trocou de número no meio do jogo?")
    else:
        print(f"Seu número é {resultado}.")


def demo() -> None:
    """O computador adivinha 73 entre 1 e 100, mostrando cada palpite e o intervalo que sobra."""
    segredo = 73
    print("=== Adivinhe o número: o computador adivinha por busca binária ===")
    print(f"Número secreto fixo: {segredo}, entre 1 e 100. "
          f"Limite teórico: {palpites_necessarios(1, 100)} palpites (log2 de 100, arredondado para cima).\n")

    def oraculo_honesto(palpite: int) -> str:
        """Responde comparando com o segredo, como faria um jogador sincero."""
        if palpite == segredo:
            return ACERTOU
        return MAIOR if segredo > palpite else MENOR

    resultado = busca_binaria(1, 100, oraculo_honesto)
    print(f"\nDescoberto: {resultado}.")
    print("\nE se o jogador mentir? Respondendo 'maior' para tudo, entre 1 e 8:")
    busca_binaria(1, 8, lambda palpite: MAIOR)
    print("A busca percebe a contradição em vez de rodar para sempre.")


def main() -> None:
    """Lê os argumentos e escolhe o modo."""
    parser = argparse.ArgumentParser(description="Adivinhe o número: você adivinha, ou o computador adivinha o seu.")
    parser.add_argument("--min", type=int, default=1, help="menor número possível (padrão: 1)")
    parser.add_argument("--max", type=int, default=100, help="maior número possível (padrão: 100)")
    parser.add_argument("--computador", action="store_true", help="modo 2: o computador adivinha o seu número")
    parser.add_argument("--semente", type=int, help="semente do sorteio no modo 1, para repetir a partida")
    parser.add_argument("--demo", action="store_true", help="o computador adivinha 73 entre 1 e 100")
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    if args.min >= args.max:
        parser.error(f"--min ({args.min}) precisa ser menor que --max ({args.max})")
    if args.computador:
        modo_computador_adivinha(args.min, args.max)
    else:
        modo_voce_adivinha(args.min, args.max, random.Random(args.semente))


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. No modo 1, registre cada palpite numa lista e, ao final, mostre quais
#    foram "desperdiçados" (fora do intervalo que as dicas já tinham fechado).
# 2. Troque a busca binária por uma que começa com saltos de 10 em 10 e só
#    depois refina; compare o número de palpites nos dois métodos.
# 3. Crie um placar em arquivo com os melhores resultados do modo 1 por
#    tamanho de intervalo, usando json e pathlib.
# ------------------------------------------------------------
