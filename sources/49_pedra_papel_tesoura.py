#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  49. Pedra, papel e tesoura com placar
# ------------------------------------------------------------
# O que faz: Melhor de N rodadas contra o computador, com placar a cada
#            rodada e fim antecipado quando alguém garante a maioria.
#            O computador aprende: conta as jogadas que você mais usa e
#            passa a escolher a que vence a sua favorita.
# Como usar: python 49_pedra_papel_tesoura.py --rodadas 5
#            python 49_pedra_papel_tesoura.py --rodadas 7 --semente 3
#            python 49_pedra_papel_tesoura.py --demo
# O que você aprende: dicionário de regras, collections.Counter, classe com
#            estado, dataclasses, função como argumento, random com semente
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import random
from collections import Counter
from dataclasses import dataclass
from typing import Callable

JOGADAS = ("pedra", "papel", "tesoura")
VENCE = {"pedra": "tesoura", "papel": "pedra", "tesoura": "papel"}  # a chave vence o valor
PERDE_PARA = {perdedor: vencedor for vencedor, perdedor in VENCE.items()}  # o contrário
ATALHOS = {"1": "pedra", "2": "papel", "3": "tesoura", "pe": "pedra", "pa": "papel", "t": "tesoura"}
FRASES = {"empate": "Empate.", "jogador": "Você venceu a rodada!", "computador": "O computador venceu a rodada."}


def resultado(jogador: str, computador: str) -> str:
    """Quem levou a rodada: 'jogador', 'computador' ou 'empate'."""
    if jogador == computador:
        return "empate"
    return "jogador" if VENCE[jogador] == computador else "computador"


def interpretar(texto: str) -> str | None:
    """Converte o que foi digitado numa jogada válida, ou None quando não entende."""
    texto = texto.strip().lower()
    if texto in JOGADAS:
        return texto
    return ATALHOS.get(texto)


class Computador:
    """Adversário que observa o histórico do jogador e joga contra a jogada favorita dele."""

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.historico: Counter[str] = Counter()

    def escolher(self) -> tuple[str, str]:
        """Devolve (jogada, motivo). Com menos de duas observações ainda joga aleatório."""
        if sum(self.historico.values()) < 2:
            return self.rng.choice(JOGADAS), "ainda não conheço você, vou de aleatório"
        favorita, vezes = self.historico.most_common(1)[0]
        jogada = PERDE_PARA[favorita]
        return jogada, f"você já jogou {favorita} {vezes}x, e {jogada} vence {favorita}"

    def observar(self, jogada: str) -> None:
        """Registra a jogada do jogador para as próximas decisões."""
        self.historico[jogada] += 1


@dataclass
class Placar:
    """Pontos de cada lado e empates."""

    jogador: int = 0
    computador: int = 0
    empates: int = 0

    def registrar(self, quem: str) -> None:
        """Soma um ponto a quem venceu (ou um empate)."""
        if quem == "empate":
            self.empates += 1
        elif quem == "jogador":
            self.jogador += 1
        else:
            self.computador += 1

    def __str__(self) -> str:
        """Linha curta para mostrar depois de cada rodada."""
        return f"Você {self.jogador} x {self.computador} Computador (empates: {self.empates})"


def jogada_do_teclado(numero: int) -> str | None:
    """Lê a jogada do jogador; aceita nome, atalho ou número. None encerra."""
    while True:
        try:
            texto = input(f"Rodada {numero}. Sua jogada (pedra/papel/tesoura, 1/2/3 ou sair): ")
        except (EOFError, KeyboardInterrupt):
            return None
        if texto.strip().lower() == "sair":
            return None
        jogada = interpretar(texto)
        if jogada:
            return jogada
        print("  Não entendi. Digite pedra, papel, tesoura ou 1, 2, 3.")


def serie(rodadas: int, obter_jogada: Callable[[int], str | None], computador: Computador) -> Placar:
    """Joga até alguém garantir a maioria das rodadas ou até o jogador parar."""
    necessario = rodadas // 2 + 1
    placar = Placar()
    print(f"Melhor de {rodadas}: vence quem chegar a {necessario} rodada(s).")
    for numero in range(1, rodadas + 1):
        if max(placar.jogador, placar.computador) >= necessario:
            break
        jogada = obter_jogada(numero)
        if jogada is None:
            print("\nSérie encerrada pelo jogador.")
            break
        escolha, motivo = computador.escolher()
        quem = resultado(jogada, escolha)
        computador.observar(jogada)  # aprende depois de escolher, senão veria a jogada atual
        placar.registrar(quem)
        print(f"Rodada {numero}: você {jogada}, computador {escolha} ({motivo}). {FRASES[quem]}")
        print(f"   Placar: {placar}")
    return placar


def encerrar(placar: Placar, computador: Computador) -> None:
    """Resultado da série e o que o computador aprendeu."""
    print("\nPlacar final:", placar)
    if placar.jogador > placar.computador:
        print("Você venceu a série!")
    elif placar.computador > placar.jogador:
        print("O computador venceu a série.")
    else:
        print("Série empatada.")
    if computador.historico:
        favorita, vezes = computador.historico.most_common(1)[0]
        contagem = ", ".join(f"{j} {n}x" for j, n in computador.historico.most_common())
        print(f"O computador aprendeu: {contagem}. Sua favorita é {favorita} ({vezes}x), "
              f"então ele responderia com {PERDE_PARA[favorita]}.")


def demo() -> None:
    """Simula uma série de 7 rodadas com jogadas pré-definidas do jogador."""
    print("=== Pedra, papel e tesoura: série simulada ===")
    jogadas = ["pedra", "pedra", "papel", "pedra", "tesoura", "pedra", "pedra"]
    print(f"Jogadas do jogador, em ordem: {', '.join(jogadas)}\n")
    computador = Computador(random.Random(7))
    placar = serie(7, lambda numero: jogadas[numero - 1], computador)
    encerrar(placar, computador)


def main() -> None:
    """Lê os argumentos e inicia a série."""
    parser = argparse.ArgumentParser(description="Pedra, papel e tesoura contra um computador que aprende.")
    parser.add_argument("--rodadas", type=int, default=5, help="número ímpar de rodadas (padrão: 5)")
    parser.add_argument("--semente", type=int, help="semente do sorteio, para repetir a mesma série")
    parser.add_argument("--demo", action="store_true", help="simula 7 rodadas com jogadas pré-definidas")
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    if args.rodadas < 1 or args.rodadas % 2 == 0:
        parser.error("--rodadas precisa ser um número ímpar (1, 3, 5, 7...) para não empatar a série")
    computador = Computador(random.Random(args.semente))
    placar = serie(args.rodadas, jogada_do_teclado, computador)
    encerrar(placar, computador)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Deixe o computador menos previsível: em 30% das rodadas ele ignora o
#    histórico e joga aleatório (random.random() < 0.3). Ele fica melhor ou pior?
# 2. Troque a contagem simples por "o que você joga depois de perder": um
#    Counter por situação (última rodada ganha, perdida, empatada).
# 3. Acrescente lagarto e Spock (cinco jogadas) só mudando o dicionário VENCE
#    para um dicionário de conjuntos.
# ------------------------------------------------------------
