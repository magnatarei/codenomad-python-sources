#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  46. Jogo da forca
# ------------------------------------------------------------
# O que faz: Sorteia uma palavra do banco (com dica), desenha a forca em
#            texto a cada erro, mostra as letras já tentadas e decide vitória
#            ou derrota. Acentos não atrapalham: digitar "a" revela "ã" e "á",
#            e "c" revela "ç".
# Como usar: python 46_jogo_forca.py
#            python 46_jogo_forca.py --erros 8 --semente 3
#            python 46_jogo_forca.py --demo
# O que você aprende: dataclasses com métodos, conjuntos, unicodedata para
#            tirar acentos, random.Random com semente, laço de jogo com input
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import random
import sys
import unicodedata
from dataclasses import dataclass, field

# Palavra e dica. As palavras têm acento de verdade; a comparação é que ignora.
BANCO = [
    ("python", "A linguagem que você está aprendendo"),
    ("função", "Bloco de código reutilizável, criado com def"),
    ("variável", "Um nome que guarda um valor"),
    ("dicionário", "Estrutura de chave e valor"),
    ("iteração", "Cada volta de um laço for ou while"),
    ("módulo", "Arquivo .py que você importa"),
    ("exceção", "Erro que você captura com try e except"),
    ("recursão", "Função que chama a si mesma"),
    ("compilador", "Programa que traduz código-fonte para a máquina"),
    ("algoritmo", "Sequência de passos para resolver um problema"),
    ("depuração", "Procurar e corrigir defeitos no programa"),
    ("terminal", "Onde você digita comandos"),
]
PARTES_DO_BONECO = 6
# Ordem em que um jogador automático chuta: das letras mais comuns em português às raras.
LETRAS_POR_FREQUENCIA = "aeosrindmutclpvgqbfhjxzkwy"


def sem_acento(texto: str) -> str:
    """Remove acentos e cedilha ('ç' vira 'c', 'ã' vira 'a'). NFD separa cada letra do seu acento."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def desenhar(partes: int) -> str:
    """Desenha a forca com as partes do boneco reveladas (0 a 6)."""
    cabeca = "O" if partes > 0 else " "
    braco_esq = "/" if partes > 1 else " "
    tronco = "|" if partes > 2 else " "
    braco_dir = "\\" if partes > 3 else " "
    perna_esq = "/" if partes > 4 else " "
    perna_dir = "\\" if partes > 5 else " "
    linhas = [
        "  +---+",
        "  |   |",
        f"  {cabeca}   |",
        f" {braco_esq}{tronco}{braco_dir}  |",
        f" {perna_esq} {perna_dir}  |",
        "      |",
        "=========",
    ]
    return "\n".join(linhas)


@dataclass
class Partida:
    """Estado de uma partida: palavra secreta, letras tentadas e erros."""

    palavra: str
    dica: str
    max_erros: int = 6
    tentadas: set[str] = field(default_factory=set)
    erros: int = 0

    def mascara(self) -> str:
        """Letras acertadas à mostra e _ nas que faltam."""
        return " ".join(letra if sem_acento(letra) in self.tentadas else "_" for letra in self.palavra)

    def tentar(self, letra: str) -> bool:
        """Registra a tentativa e devolve True quando a letra está na palavra."""
        self.tentadas.add(letra)
        if letra in sem_acento(self.palavra):
            return True
        self.erros += 1
        return False

    def ganhou(self) -> bool:
        """Todas as letras da palavra já foram tentadas?"""
        return all(sem_acento(letra) in self.tentadas for letra in self.palavra)

    def perdeu(self) -> bool:
        """Os erros chegaram ao limite?"""
        return self.erros >= self.max_erros

    def partes_reveladas(self) -> int:
        """Converte os erros em partes do boneco, seja qual for o limite escolhido."""
        return round(PARTES_DO_BONECO * self.erros / self.max_erros)


def validar_palpite(palpite: str, partida: Partida) -> str:
    """Devolve a letra normalizada ou levanta ValueError com a explicação."""
    letra = sem_acento(palpite.strip().lower())
    if not letra:
        raise ValueError("Digite uma letra.")
    if len(letra) > 1:
        raise ValueError("Só uma letra por vez.")
    if not letra.isalpha():
        raise ValueError(f"'{palpite}' não é uma letra.")
    if letra in partida.tentadas:
        raise ValueError(f"Você já tentou '{letra}'.")
    return letra


def mostrar(partida: Partida) -> None:
    """Desenho, palavra mascarada e letras já tentadas."""
    print(desenhar(partida.partes_reveladas()))
    print(f"Palavra: {partida.mascara()}")
    print(f"Tentadas: {' '.join(sorted(partida.tentadas)) or '(nenhuma)'}   "
          f"Erros: {partida.erros}/{partida.max_erros}")


def encerrar(partida: Partida) -> None:
    """Mensagem final de vitória ou derrota."""
    if partida.ganhou():
        print(f"Você venceu! A palavra era '{partida.palavra}' com {partida.erros} erro(s).")
    else:
        print(f"Enforcado! A palavra era '{partida.palavra}'.")


def nova_partida(rng: random.Random, max_erros: int) -> Partida:
    """Sorteia uma palavra do banco."""
    palavra, dica = rng.choice(BANCO)
    return Partida(palavra, dica, max_erros)


def jogar_interativo(partida: Partida) -> None:
    """Laço de jogo com o teclado."""
    print(f"Dica: {partida.dica}  ({len(partida.palavra)} letras)")
    while not (partida.ganhou() or partida.perdeu()):
        mostrar(partida)
        try:
            palpite = input("Letra: ")
        except (EOFError, KeyboardInterrupt):
            print(f"\nJogo encerrado. A palavra era '{partida.palavra}'.")
            return
        try:
            letra = validar_palpite(palpite, partida)
        except ValueError as erro:
            print(f"  {erro}")
            continue
        print("  Acertou!" if partida.tentar(letra) else "  Errou!")
    mostrar(partida)
    encerrar(partida)


def demo() -> None:
    """Um jogador automático joga uma partida inteira, mostrando cada rodada."""
    print("=== Jogo da forca: partida automática ===")
    partida = nova_partida(random.Random(11), max_erros=6)
    print(f"Dica: {partida.dica}  ({len(partida.palavra)} letras)")
    print(f"Palavra: {partida.mascara()}\n")
    for rodada, letra in enumerate(LETRAS_POR_FREQUENCIA, start=1):
        acertou = partida.tentar(letra)
        resultado = "acertou" if acertou else "errou"
        print(f"Rodada {rodada:>2}: tenta '{letra}' -> {resultado:<8} {partida.mascara()}")
        if not acertou:
            print(desenhar(partida.partes_reveladas()))
        if partida.ganhou() or partida.perdeu():
            break
    print()
    encerrar(partida)


def main() -> None:
    """Lê os argumentos e inicia o jogo interativo ou a demonstração."""
    parser = argparse.ArgumentParser(description="Jogo da forca no terminal.")
    parser.add_argument("--erros", type=int, default=6, help="erros permitidos, de 1 a 10 (padrão: 6)")
    parser.add_argument("--semente", type=int, help="semente do sorteio, para repetir a mesma palavra")
    parser.add_argument("--demo", action="store_true", help="um jogador automático joga uma partida completa")
    args = parser.parse_args()

    if args.demo:
        demo()
        return
    if not 1 <= args.erros <= 10:
        parser.error("--erros precisa estar entre 1 e 10")
    rng = random.Random(args.semente)  # semente None usa o relógio: cada partida diferente
    jogar_interativo(nova_partida(rng, args.erros))


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Leia o banco de palavras de um arquivo texto (uma linha "palavra;dica")
#    com --arquivo, validando linhas malformadas.
# 2. Aceite o chute da palavra inteira: se acertar, vence na hora; se errar,
#    conta como dois erros.
# 3. Guarde um placar em JSON (vitórias, derrotas, melhor partida) e mostre
#    no início do jogo.
# ------------------------------------------------------------
