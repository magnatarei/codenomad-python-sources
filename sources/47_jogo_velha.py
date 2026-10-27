#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  47. Jogo da velha com computador
# ------------------------------------------------------------
# O que faz: Jogo da velha no terminal para dois jogadores ou contra o
#            computador, que usa minimax e por isso nunca perde. Mostra o
#            tabuleiro com as casas livres numeradas e detecta vitória
#            e empate.
# Como usar: python 47_jogo_velha.py
#            python 47_jogo_velha.py --simbolo O      (você é O, o computador começa com X)
#            python 47_jogo_velha.py --dois-jogadores
#            python 47_jogo_velha.py --demo
# O que você aprende: recursão e minimax, functools.cache (memoização),
#            string imutável como tabuleiro, tuplas de linhas vencedoras
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
from functools import cache

VAZIO = "."
LINHAS_VENCEDORAS = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # horizontais
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # verticais
    (0, 4, 8), (2, 4, 6),             # diagonais
)


def oponente(jogador: str) -> str:
    """X vira O e O vira X."""
    return "O" if jogador == "X" else "X"


def vencedor(tabuleiro: str) -> str | None:
    """Devolve 'X' ou 'O' se alguém fechou uma linha; senão None."""
    for a, b, c in LINHAS_VENCEDORAS:
        if tabuleiro[a] != VAZIO and tabuleiro[a] == tabuleiro[b] == tabuleiro[c]:
            return tabuleiro[a]
    return None


def livres(tabuleiro: str) -> list[int]:
    """Índices das casas vazias."""
    return [i for i, casa in enumerate(tabuleiro) if casa == VAZIO]


def jogar(tabuleiro: str, posicao: int, jogador: str) -> str:
    """Devolve um tabuleiro novo com a jogada: strings são imutáveis, então criamos outra."""
    return tabuleiro[:posicao] + jogador + tabuleiro[posicao + 1:]


def desenhar(tabuleiro: str) -> str:
    """Tabuleiro em texto; as casas vazias mostram o número que o jogador digita."""
    casas = [casa if casa != VAZIO else str(i + 1) for i, casa in enumerate(tabuleiro)]
    linhas = [" " + " | ".join(casas[i:i + 3]) for i in (0, 3, 6)]
    return "\n---+---+---\n".join(linhas)


@cache
def avaliar(tabuleiro: str, vez: str, jogador: str) -> int:
    """Minimax: o melhor resultado que 'jogador' garante a partir daqui, com 'vez' a jogar.

    Vitória vale +10, empate 0, derrota -10. As casas vazias entram como desempate:
    vencer logo vale mais e perder tarde dói menos. O @cache guarda cada tabuleiro
    já avaliado, então o jogo inteiro cabe em poucos milhares de posições.
    """
    ganhador = vencedor(tabuleiro)
    vazias = tabuleiro.count(VAZIO)
    if ganhador == jogador:
        return 10 + vazias
    if ganhador is not None:
        return -10 - vazias
    if vazias == 0:
        return 0
    resultados = [avaliar(jogar(tabuleiro, p, vez), oponente(vez), jogador) for p in livres(tabuleiro)]
    # Na própria vez escolhe o máximo; na vez do adversário assume que ele joga o pior para nós.
    return max(resultados) if vez == jogador else min(resultados)


def melhor_jogada(tabuleiro: str, jogador: str) -> int:
    """A casa cuja avaliação é a mais alta para o jogador."""
    return max(livres(tabuleiro),
               key=lambda p: avaliar(jogar(tabuleiro, p, jogador), oponente(jogador), jogador))


def ler_jogada(tabuleiro: str, jogador: str) -> int | None:
    """Pede uma casa de 1 a 9 até receber uma válida. Devolve None se a entrada acabar."""
    while True:
        try:
            texto = input(f"Jogador {jogador}, escolha uma casa (1-9): ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if not texto.isdigit() or not 1 <= int(texto) <= 9:
            print("  Digite um número de 1 a 9.")
            continue
        posicao = int(texto) - 1
        if tabuleiro[posicao] != VAZIO:
            print("  Essa casa já está ocupada.")
            continue
        return posicao


def anunciar(tabuleiro: str) -> None:
    """Mostra o resultado final."""
    ganhador = vencedor(tabuleiro)
    print(f"Vitória de {ganhador}!" if ganhador else "Empate: ninguém fechou uma linha.")


def partida(humanos: set[str]) -> str:
    """Roda uma partida. 'humanos' diz quais símbolos vêm do teclado; X sempre começa.

    Devolve o tabuleiro final (útil para testes e para a demonstração).
    """
    tabuleiro = VAZIO * 9
    vez = "X"
    print(desenhar(tabuleiro))
    while vencedor(tabuleiro) is None and livres(tabuleiro):
        if vez in humanos:
            posicao = ler_jogada(tabuleiro, vez)
            if posicao is None:
                print("\nPartida encerrada antes do fim.")
                return tabuleiro
        else:
            posicao = melhor_jogada(tabuleiro, vez)
            print(f"\nComputador ({vez}) joga na casa {posicao + 1}:")
        tabuleiro = jogar(tabuleiro, posicao, vez)
        print(desenhar(tabuleiro))
        vez = oponente(vez)
    print()
    anunciar(tabuleiro)
    return tabuleiro


def demo() -> None:
    """Computador contra computador: com os dois jogando perfeitamente, dá empate."""
    print("=== Jogo da velha: computador contra computador ===")
    final = partida(humanos=set())
    print(f"\nTabuleiro final: {final}")
    print(f"Posições distintas avaliadas pelo minimax (graças ao cache): {avaliar.cache_info().currsize}")
    print("Dois jogadores perfeitos nunca perdem, por isso toda partida assim termina empatada.")


def main() -> None:
    """Lê os argumentos e escolhe o modo de jogo."""
    parser = argparse.ArgumentParser(description="Jogo da velha contra o computador (minimax) ou a dois.")
    parser.add_argument("--simbolo", choices=["X", "O"], default="X",
                        help="seu símbolo contra o computador; X começa (padrão: X)")
    parser.add_argument("--dois-jogadores", action="store_true", help="duas pessoas no mesmo teclado")
    parser.add_argument("--demo", action="store_true", help="computador contra computador, jogada a jogada")
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    if args.dois_jogadores:
        print("Dois jogadores: X começa. Casas de 1 a 9.")
        partida(humanos={"X", "O"})
    else:
        print(f"Você joga com {args.simbolo}; o computador nunca perde, tente ao menos empatar.")
        partida(humanos={args.simbolo})


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Adicione --nivel iniciante, em que o computador joga aleatório em metade
#    das vezes (random.random() < 0.5), e meça quantas vezes você vence.
# 2. Troque a lista de resultados por poda alfa-beta e conte quantas chamadas
#    a avaliar() foram evitadas (um contador global ou um atributo).
# 3. Generalize para um tabuleiro 4x4 com LINHAS_VENCEDORAS calculadas por
#    código, e veja por que o minimax completo fica lento nesse tamanho.
# ------------------------------------------------------------
