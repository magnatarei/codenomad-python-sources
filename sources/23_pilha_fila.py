#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  23. Pilha e fila na prática
# ------------------------------------------------------------
# O que faz: implementa pilha (LIFO) e fila (FIFO) com as operações clássicas
#            e usa as duas em três problemas reais: parênteses balanceados,
#            desfazer/refazer de um editor e fila de atendimento com espera.
# Como usar: python sources/23_pilha_fila.py parenteses "{[(1+2)*3]}"
#            python sources/23_pilha_fila.py editor "escrever=Olá" "escrever=, mundo" desfazer refazer
#            python sources/23_pilha_fila.py fila Ana:4 Bruno:2 Carla:6 --guiches 2
#            python sources/23_pilha_fila.py --demo
# O que você aprende: classes genéricas com TypeVar, collections.deque,
#            subcomandos no argparse, LIFO contra FIFO e simulação de tempo.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import sys
from collections import deque
from typing import Generic, TypeVar

T = TypeVar("T")


class Pilha(Generic[T]):
    """Pilha LIFO: o último a entrar é o primeiro a sair, como pratos empilhados."""

    def __init__(self) -> None:
        self._itens: list[T] = []

    def empilhar(self, item: T) -> None:
        """Coloca um item no topo."""
        self._itens.append(item)

    def desempilhar(self) -> T:
        """Tira e devolve o item do topo. Erro claro se a pilha estiver vazia."""
        if not self._itens:
            raise IndexError("a pilha está vazia")
        return self._itens.pop()

    def topo(self) -> T:
        """Mostra o item do topo sem tirar."""
        if not self._itens:
            raise IndexError("a pilha está vazia")
        return self._itens[-1]

    def vazia(self) -> bool:
        """True quando não há itens."""
        return not self._itens

    def __len__(self) -> int:
        return len(self._itens)


class Fila(Generic[T]):
    """Fila FIFO: o primeiro a entrar é o primeiro a sair, como fila de padaria."""

    def __init__(self) -> None:
        self._itens: deque[T] = deque()  # deque tira da frente em O(1); list.pop(0) é O(n)

    def enfileirar(self, item: T) -> None:
        """Coloca um item no fim da fila."""
        self._itens.append(item)

    def desenfileirar(self) -> T:
        """Tira e devolve o item da frente. Erro claro se a fila estiver vazia."""
        if not self._itens:
            raise IndexError("a fila está vazia")
        return self._itens.popleft()

    def frente(self) -> T:
        """Mostra quem está na frente sem tirar."""
        if not self._itens:
            raise IndexError("a fila está vazia")
        return self._itens[0]

    def vazia(self) -> bool:
        """True quando não há itens."""
        return not self._itens

    def __len__(self) -> int:
        return len(self._itens)


PARES = {")": "(", "]": "[", "}": "{"}


def parenteses_balanceados(texto: str) -> tuple[bool, str]:
    """Usa uma pilha para conferir se cada fechamento casa com a última abertura."""
    pilha: Pilha[tuple[str, int]] = Pilha()
    for pos, ch in enumerate(texto):
        if ch in "([{":
            pilha.empilhar((ch, pos))  # guarda a posição para a mensagem de erro
        elif ch in PARES:
            if pilha.vazia():
                return False, f"'{ch}' na posição {pos} fecha sem ter aberto"
            aberto, onde = pilha.desempilhar()
            if aberto != PARES[ch]:
                return False, f"'{ch}' na posição {pos} não casa com '{aberto}' da posição {onde}"
    if not pilha.vazia():
        aberto, onde = pilha.topo()
        return False, f"'{aberto}' aberto na posição {onde} nunca fechou"
    return True, "balanceado"


class Editor:
    """Editor de texto mínimo: cada ação guarda o estado anterior numa pilha."""

    def __init__(self) -> None:
        self.texto = ""
        self._desfazer: Pilha[str] = Pilha()
        self._refazer: Pilha[str] = Pilha()

    def _aplicar(self, novo: str) -> None:
        """Troca o texto guardando o anterior; uma ação nova apaga o que podia ser refeito."""
        self._desfazer.empilhar(self.texto)
        self.texto = novo
        self._refazer = Pilha()

    def escrever(self, trecho: str) -> None:
        """Acrescenta texto no fim."""
        self._aplicar(self.texto + trecho)

    def apagar(self, quantos: int) -> None:
        """Apaga os últimos N símbolos do fim do texto."""
        if quantos <= 0:
            raise ValueError("apague pelo menos 1 caractere")
        self._aplicar(self.texto[:-quantos])

    def desfazer(self) -> bool:
        """Volta ao estado anterior. Devolve False se não havia o que desfazer."""
        if self._desfazer.vazia():
            return False
        self._refazer.empilhar(self.texto)
        self.texto = self._desfazer.desempilhar()
        return True

    def refazer(self) -> bool:
        """Refaz o que foi desfeito. Devolve False se não havia o que refazer."""
        if self._refazer.vazia():
            return False
        self._desfazer.empilhar(self.texto)
        self.texto = self._refazer.desempilhar()
        return True


def executar_editor(comandos: list[str]) -> None:
    """Interpreta comandos como escrever=Olá, apagar=2, desfazer e refazer."""
    editor = Editor()
    for cmd in comandos:
        nome, _, arg = cmd.partition("=")
        aviso = ""
        if nome == "escrever":
            editor.escrever(arg)
        elif nome == "apagar":
            if not arg.isdigit():
                raise ValueError(f"apagar precisa de um número, veio '{arg}'")
            editor.apagar(int(arg))
        elif nome == "desfazer":
            aviso = "" if editor.desfazer() else "  (nada para desfazer)"
        elif nome == "refazer":
            aviso = "" if editor.refazer() else "  (nada para refazer)"
        else:
            raise ValueError(f"comando desconhecido: '{cmd}' (use escrever=, apagar=, desfazer, refazer)")
        print(f"  {cmd:<20} -> {editor.texto!r}{aviso}")


def simular_atendimento(clientes: list[tuple[str, int]], guiches: int) -> float:
    """Atende por ordem de chegada; cada guichê pega o próximo quando libera. Devolve a espera média."""
    fila: Fila[tuple[str, int]] = Fila()
    for cliente in clientes:
        fila.enfileirar(cliente)
    livre_em = [0] * guiches  # minuto em que cada guichê fica livre (todos chegam no minuto 0)
    esperas: list[int] = []
    while not fila.vazia():
        g = livre_em.index(min(livre_em))  # o guichê que libera primeiro
        nome, duracao = fila.desenfileirar()
        inicio = livre_em[g]
        livre_em[g] = inicio + duracao
        esperas.append(inicio)
        print(f"  {nome:<8} guichê {g + 1}: esperou {inicio:>2} min, atendido do minuto {inicio} ao {inicio + duracao}")
    media = sum(esperas) / len(esperas)
    print(f"  espera média: {media:.1f} min; o último sai no minuto {max(livre_em)}")
    return media


def cliente(texto: str) -> tuple[str, int]:
    """Converte 'Nome:minutos' em (nome, minutos), com erro claro."""
    nome, sep, minutos = texto.partition(":")
    if not sep or not nome or not minutos.isdigit() or int(minutos) <= 0:
        raise argparse.ArgumentTypeError(f"'{texto}' deveria ser Nome:minutos, como Ana:4")
    return nome, int(minutos)


def demo() -> None:
    """Roda os três problemas com dados de exemplo."""
    print("=== Pilha e fila na prática: CodeNomad Academy ===\n")
    print("1) Parênteses balanceados (pilha):")
    for expressao in ["{[(1+2)*3]}", "(1+2]", "((1+2)", "if (x) { y[0] = (1); }", ")("]:
        ok, motivo = parenteses_balanceados(expressao)
        print(f"  {expressao:<24} {'OK' if ok else 'ERRO'}: {motivo}")
    print("\n2) Desfazer e refazer (duas pilhas):")
    executar_editor(["escrever=Olá", "escrever=, mundo", "apagar=7", "desfazer",
                     "desfazer", "refazer", "escrever=!", "refazer"])
    clientes = [("Ana", 4), ("Bruno", 2), ("Carla", 6), ("Diego", 3), ("Elisa", 5)]
    print("\n3) Fila de atendimento com 1 guichê (fila):")
    media1 = simular_atendimento(clientes, 1)
    print("\n   Mesmos clientes com 2 guichês:")
    media2 = simular_atendimento(clientes, 2)
    print(f"\n   Abrir o segundo guichê reduziu a espera média de {media1:.1f} para {media2:.1f} min.")


def main() -> None:
    """Lê o subcomando escolhido e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Pilha e fila aplicadas a três problemas do dia a dia.")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    sub = ap.add_subparsers(dest="comando")
    p1 = sub.add_parser("parenteses", help="confere parênteses, colchetes e chaves")
    p1.add_argument("texto")
    p2 = sub.add_parser("editor", help="comandos: escrever=TEXTO, apagar=N, desfazer, refazer")
    p2.add_argument("comandos", nargs="+")
    p3 = sub.add_parser("fila", help="fila de atendimento: Nome:minutos ...")
    p3.add_argument("clientes", nargs="+", type=cliente)
    p3.add_argument("--guiches", type=int, default=1, help="quantos guichês atendem (padrão 1)")
    args = ap.parse_args()
    if args.demo:
        demo()
    elif args.comando == "parenteses":
        ok, motivo = parenteses_balanceados(args.texto)
        print(f"{'OK' if ok else 'ERRO'}: {motivo}")
        sys.exit(0 if ok else 1)
    elif args.comando == "editor":
        try:
            executar_editor(args.comandos)
        except ValueError as e:
            sys.exit(f"Erro: {e}")
    elif args.comando == "fila":
        if args.guiches < 1:
            ap.error("--guiches precisa ser pelo menos 1")
        simular_atendimento(args.clientes, args.guiches)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Dê um horário de chegada a cada cliente (Ana:4:10 = chega no minuto 10)
#    e faça a simulação respeitar quem ainda não chegou.
# 2. Implemente a Fila usando duas Pilhas (clássico de entrevista) e
#    confira que a ordem de saída continua FIFO.
# 3. Limite o histórico do Editor a 5 ações: ao desfazer a sexta, o que
#    deve acontecer? Decida e implemente.
# ------------------------------------------------------------
