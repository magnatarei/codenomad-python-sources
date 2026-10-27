#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  25. Fila de prioridade com heap
# ------------------------------------------------------------
# O que faz: implementa um heap binário mínimo do zero (inserir, extrair,
#            espiar) e simula um pronto-socorro em que os pacientes são
#            atendidos pela gravidade, não pela ordem de chegada.
# Como usar: python sources/25_fila_prioridade.py Ana:3:0:10 Bruno:1:5:20 Carla:3:8:10
#            python sources/25_fila_prioridade.py --heap 7 3 9 1 5 2
#            python sources/25_fila_prioridade.py --demo
# O que você aprende: heap guardado em lista (pai em (i-1)//2, filhos em
#            2i+1 e 2i+2), dataclass com order=True e campo fora da comparação,
#            classe genérica, desempate estável e simulação dirigida por tempo.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import sys
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(order=True)
class Entrada(Generic[T]):
    """Item do heap: compara por prioridade e depois pela ordem de chegada."""

    prioridade: int
    ordem: int
    item: T = field(compare=False)  # o item em si nunca entra na comparação


class HeapMinimo(Generic[T]):
    """Heap binário mínimo: o menor valor de prioridade fica sempre na raiz (posição 0)."""

    def __init__(self) -> None:
        self._dados: list[Entrada[T]] = []
        self._contador = 0  # cresce a cada inserção: desempata quem chegou antes

    def inserir(self, prioridade: int, item: T) -> None:
        """Coloca no fim da lista e sobe o item até o pai ser menor ou igual."""
        self._dados.append(Entrada(prioridade, self._contador, item))
        self._contador += 1
        self._subir(len(self._dados) - 1)

    def extrair(self) -> T:
        """Tira a raiz: o último vai para o topo e desce até o lugar certo."""
        if not self._dados:
            raise IndexError("o heap está vazio")
        raiz = self._dados[0]
        ultimo = self._dados.pop()
        if self._dados:  # se sobrou alguém, o último assume a raiz e desce
            self._dados[0] = ultimo
            self._descer(0)
        return raiz.item

    def espiar(self) -> T:
        """Mostra o item de maior prioridade sem tirar."""
        if not self._dados:
            raise IndexError("o heap está vazio")
        return self._dados[0].item

    def prioridades(self) -> list[int]:
        """O vetor interno, só as prioridades: útil para enxergar a estrutura."""
        return [e.prioridade for e in self._dados]

    def __len__(self) -> int:
        return len(self._dados)

    def _subir(self, i: int) -> None:
        """Troca com o pai enquanto o item for menor que ele."""
        while i > 0:
            pai = (i - 1) // 2
            if self._dados[i] < self._dados[pai]:
                self._dados[i], self._dados[pai] = self._dados[pai], self._dados[i]
                i = pai
            else:
                break

    def _descer(self, i: int) -> None:
        """Troca com o menor dos filhos enquanto algum filho for menor."""
        n = len(self._dados)
        while True:
            menor = i
            for filho in (2 * i + 1, 2 * i + 2):
                if filho < n and self._dados[filho] < self._dados[menor]:
                    menor = filho
            if menor == i:
                return
            self._dados[i], self._dados[menor] = self._dados[menor], self._dados[i]
            i = menor


@dataclass
class Paciente:
    """Quem chega ao pronto-socorro: gravidade 1 é a mais urgente, 5 a mais leve."""

    nome: str
    gravidade: int
    chegada: int  # minuto em que chegou
    duracao: int  # minutos de atendimento


def paciente(texto: str) -> Paciente:
    """Converte 'Nome:gravidade:chegada:duracao' em Paciente, com erro claro."""
    partes = texto.split(":")
    if len(partes) != 4 or not partes[0] or not all(p.isdigit() for p in partes[1:]):
        raise argparse.ArgumentTypeError(f"'{texto}' deveria ser Nome:gravidade:chegada:duracao, como Ana:3:0:10")
    p = Paciente(partes[0], int(partes[1]), int(partes[2]), int(partes[3]))
    if not 1 <= p.gravidade <= 5:
        raise argparse.ArgumentTypeError(f"gravidade de {p.nome} deve ir de 1 (grave) a 5 (leve)")
    if p.duracao <= 0:
        raise argparse.ArgumentTypeError(f"duração de {p.nome} deve ser maior que zero")
    return p


def simular_pronto_socorro(pacientes: list[Paciente]) -> None:
    """Um médico atende sempre o mais grave entre os que já chegaram."""
    chegadas = sorted(pacientes, key=lambda p: p.chegada)
    fila: HeapMinimo[Paciente] = HeapMinimo()
    tempo = 0
    proximo_a_chegar = 0
    print(f"  {'ordem':<6} {'paciente':<10} {'grav.':>5} {'chegou':>7} {'começou':>8} {'esperou':>8}")
    atendidos = 0
    while proximo_a_chegar < len(chegadas) or len(fila) > 0:
        while proximo_a_chegar < len(chegadas) and chegadas[proximo_a_chegar].chegada <= tempo:
            p = chegadas[proximo_a_chegar]
            fila.inserir(p.gravidade, p)  # quem chegou primeiro ganha o desempate
            proximo_a_chegar += 1
        if len(fila) == 0:  # ninguém esperando: o relógio pula para a chegada seguinte
            tempo = chegadas[proximo_a_chegar].chegada
            continue
        p = fila.extrair()
        atendidos += 1
        print(f"  {atendidos:<6} {p.nome:<10} {p.gravidade:>5} {p.chegada:>7} {tempo:>8} {tempo - p.chegada:>8}")
        tempo += p.duracao
    print(f"  Todos atendidos no minuto {tempo}.")


def mostrar_heap_de_numeros(numeros: list[int]) -> None:
    """Insere números um a um mostrando o vetor interno e depois extrai em ordem."""
    heap: HeapMinimo[int] = HeapMinimo()
    for n in numeros:
        heap.inserir(n, n)
        print(f"  insere {n:>3} -> vetor interno {heap.prioridades()}")
    print(f"  espiar: {heap.espiar()} (a raiz é sempre o menor)")
    saida = [heap.extrair() for _ in range(len(heap))]
    print(f"  extraindo tudo: {saida}  (isso é o heapsort)")


def demo() -> None:
    """Mostra o heap com números e a simulação do pronto-socorro."""
    print("=== Fila de prioridade com heap: CodeNomad Academy ===\n")
    print("1) Heap mínimo com números:")
    mostrar_heap_de_numeros([7, 3, 9, 1, 5, 2, 8])
    print("\n2) Pronto-socorro: ordem de chegada contra ordem de atendimento")
    pacientes = [
        Paciente("Dona Zilá", 4, 0, 10),
        Paciente("Pedro", 3, 2, 15),
        Paciente("Joana", 1, 5, 30),
        Paciente("Marcos", 3, 6, 10),
        Paciente("Beatriz", 5, 8, 5),
        Paciente("Seu Osmar", 2, 20, 20),
        Paciente("Lúcia", 4, 25, 10),
    ]
    print("  Chegada: " + ", ".join(f"{p.nome} (grav. {p.gravidade}, min {p.chegada})" for p in pacientes))
    simular_pronto_socorro(pacientes)
    print("\n  Joana (gravidade 1) chegou no minuto 5, depois de Pedro, e foi atendida antes dele.")
    print("  Seu Osmar (gravidade 2) chegou no minuto 20 e ainda assim passou na frente de Pedro.")
    print("  Pedro e Marcos têm a mesma gravidade: o desempate é a ordem de chegada.")
    print("  Um sort a cada chegada custaria O(n log n); o heap faz cada operação em O(log n).")


def main() -> None:
    """Lê os argumentos e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Heap mínimo do zero e simulação de pronto-socorro.")
    ap.add_argument("pacientes", nargs="*", type=paciente, help="Nome:gravidade:chegada:duracao")
    ap.add_argument("--heap", nargs="+", type=int, metavar="N", help="só mostra o heap com esses números")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    args = ap.parse_args()
    if args.demo:
        demo()
        return
    if not args.pacientes and not args.heap:
        ap.print_help()
        sys.exit(2)
    if args.heap:
        mostrar_heap_de_numeros(args.heap)
    if args.pacientes:
        simular_pronto_socorro(args.pacientes)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Troque a comparação para fazer um heap MÁXIMO e use-o para achar os
#    3 maiores números de uma lista sem ordenar tudo.
# 2. Adicione um segundo médico à simulação: cada um pega o próximo do
#    heap assim que fica livre.
# 3. Compare sua classe com o módulo heapq da biblioteca padrão: insira
#    100.000 números nos dois e meça o tempo com time.perf_counter.
# ------------------------------------------------------------
