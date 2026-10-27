#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  21. Algoritmos de ordenação com passos
# ------------------------------------------------------------
# O que faz: implementa bubble sort, insertion sort, merge sort e quick sort
#            do zero, contando comparações e trocas, com a opção de mostrar o
#            vetor a cada passo e uma tabela final comparando o desempenho.
# Como usar: python sources/21_ordenacao_visual.py 5 2 9 1 7 --algoritmo bubble --passos
#            python sources/21_ordenacao_visual.py 5 2 9 1 7 --algoritmo todos
#            python sources/21_ordenacao_visual.py --demo
# O que você aprende: funções recursivas, dataclass como contador, cópia de
#            listas, medição de tempo com perf_counter, a diferença entre
#            O(n²) e O(n log n) e por que o quick sort escolhe o pivô do meio.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import random
import sys
import time
from dataclasses import dataclass
from typing import Callable

ALGORITMOS = ("bubble", "insertion", "merge", "quick")


@dataclass
class Estatisticas:
    """Contadores de uma execução: comparações, trocas e passos registrados."""

    comparacoes: int = 0
    trocas: int = 0
    passos: int = 0
    mostrar: bool = False

    def registrar(self, vetor: list[int], rotulo: str) -> None:
        """Conta um passo e, se pedido, imprime o vetor naquele instante."""
        self.passos += 1
        if self.mostrar:
            print(f"  passo {self.passos:>3}: {vetor}  ({rotulo})")


def bubble_sort(v: list[int], est: Estatisticas) -> list[int]:
    """Bubble sort: compara vizinhos e troca os que estão fora de ordem."""
    v = v[:]  # cópia: a lista de quem chamou continua intacta
    for fim in range(len(v) - 1, 0, -1):
        trocou = False
        for i in range(fim):  # o maior do trecho "borbulha" até a posição fim
            est.comparacoes += 1
            if v[i] > v[i + 1]:
                v[i], v[i + 1] = v[i + 1], v[i]
                est.trocas += 1
                trocou = True
                est.registrar(v, f"troca {v[i + 1]} com {v[i]}")
        if not trocou:
            break  # nenhuma troca na passada: já está ordenado
    return v


def insertion_sort(v: list[int], est: Estatisticas) -> list[int]:
    """Insertion sort: cada elemento entra no lugar certo da parte já ordenada."""
    v = v[:]
    for i in range(1, len(v)):
        chave = v[i]
        j = i - 1
        while j >= 0:
            est.comparacoes += 1
            if v[j] <= chave:
                break
            v[j + 1] = v[j]  # empurra o maior uma casa para a direita
            est.trocas += 1
            j -= 1
        v[j + 1] = chave
        est.registrar(v, f"insere {chave} na posição {j + 1}")
    return v


def merge_sort(v: list[int], est: Estatisticas) -> list[int]:
    """Merge sort: divide ao meio, ordena cada metade e intercala as duas."""
    if len(v) <= 1:
        return v[:]  # caso base da recursão: 0 ou 1 elemento já está ordenado
    meio = len(v) // 2
    esquerda = merge_sort(v[:meio], est)
    direita = merge_sort(v[meio:], est)
    return intercalar(esquerda, direita, est)


def intercalar(esq: list[int], dir_: list[int], est: Estatisticas) -> list[int]:
    """Junta duas listas ordenadas em uma só, sempre pegando o menor da frente."""
    resultado: list[int] = []
    i = j = 0
    while i < len(esq) and j < len(dir_):
        est.comparacoes += 1
        if esq[i] <= dir_[j]:
            resultado.append(esq[i])
            i += 1
        else:
            resultado.append(dir_[j])
            j += 1
    resultado += esq[i:] + dir_[j:]  # o que sobrou já está em ordem
    est.trocas += len(resultado)  # no merge, cada escrita conta como movimento
    est.registrar(resultado, f"intercala {esq} e {dir_}")
    return resultado


def quick_sort(v: list[int], est: Estatisticas) -> list[int]:
    """Quick sort: fixa um pivô, separa menores e maiores e repete em cada lado."""
    v = v[:]
    _quick(v, 0, len(v) - 1, est)
    return v


def _quick(v: list[int], ini: int, fim: int, est: Estatisticas) -> None:
    """Ordena v[ini..fim] no lugar. Para quando o trecho tem 0 ou 1 elemento."""
    if ini >= fim:
        return
    p = particionar(v, ini, fim, est)
    est.registrar(v, f"pivô {v[p]} fixado na posição {p}")
    _quick(v, ini, p - 1, est)
    _quick(v, p + 1, fim, est)


def particionar(v: list[int], ini: int, fim: int, est: Estatisticas) -> int:
    """Esquema de Lomuto: leva o pivô para o fim e devolve sua posição final."""
    meio = (ini + fim) // 2  # pivô do meio evita o pior caso em vetor já ordenado
    v[meio], v[fim] = v[fim], v[meio]
    pivo = v[fim]
    i = ini  # fronteira: tudo antes de i é menor que o pivô
    for j in range(ini, fim):
        est.comparacoes += 1
        if v[j] < pivo:
            if i != j:
                v[i], v[j] = v[j], v[i]
                est.trocas += 1
            i += 1
    v[i], v[fim] = v[fim], v[i]
    est.trocas += 1
    return i


FUNCOES: dict[str, Callable[[list[int], Estatisticas], list[int]]] = {
    "bubble": bubble_sort,
    "insertion": insertion_sort,
    "merge": merge_sort,
    "quick": quick_sort,
}


def milhar(n: int) -> str:
    """Formata 1234567 como 1.234.567, no padrão brasileiro."""
    return f"{n:,}".replace(",", ".")


def ordenar(nome: str, v: list[int], mostrar: bool = False) -> tuple[list[int], Estatisticas, float]:
    """Roda um algoritmo pelo nome e devolve (vetor ordenado, contadores, segundos)."""
    est = Estatisticas(mostrar=mostrar)
    inicio = time.perf_counter()
    resultado = FUNCOES[nome](v, est)
    segundos = time.perf_counter() - inicio
    if resultado != sorted(v):  # conferência honesta: o algoritmo acertou?
        raise RuntimeError(f"{nome} devolveu um vetor fora de ordem")
    return resultado, est, segundos


def tabela(v: list[int]) -> None:
    """Imprime uma tabela comparando os quatro algoritmos sobre o mesmo vetor."""
    print(f"  {'algoritmo':<10} {'comparações':>12} {'trocas/mov.':>12} {'tempo (ms)':>11}")
    for nome in ALGORITMOS:
        _, est, seg = ordenar(nome, v)
        print(f"  {nome:<10} {milhar(est.comparacoes):>12} {milhar(est.trocas):>12} {seg * 1000:>11.2f}")


def demo() -> None:
    """Demonstração completa: passos do bubble, tabela pequena e tabela grande."""
    vetor = [5, 2, 9, 1, 7, 3, 8]
    print("=== Ordenação passo a passo: CodeNomad Academy ===")
    print(f"Vetor original: {vetor}\n")
    print("Bubble sort, mostrando cada troca:")
    resultado, est, _ = ordenar("bubble", vetor, mostrar=True)
    print(f"Resultado: {resultado}  ({est.comparacoes} comparações, {est.trocas} trocas)\n")
    print("Os quatro algoritmos no mesmo vetor pequeno:")
    tabela(vetor)
    random.seed(42)  # semente fixa: a demonstração é igual em qualquer máquina
    grande = [random.randint(0, 9999) for _ in range(1500)]
    print(f"\nAgora com {milhar(len(grande))} números aleatórios:")
    tabela(grande)
    print("\nLeitura: bubble e insertion crescem com n², merge e quick com n log n.")
    print("Com 10 vezes mais dados, os dois primeiros ficam 100 vezes mais lentos.")


def inteiro(texto: str) -> int:
    """Converte o argumento em inteiro com mensagem de erro em português."""
    try:
        return int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um número inteiro") from None


def main() -> None:
    """Lê os argumentos e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Ordena números contando comparações, trocas e passos.")
    ap.add_argument("numeros", nargs="*", type=inteiro, help="números inteiros a ordenar")
    ap.add_argument("--algoritmo", choices=ALGORITMOS + ("todos",), default="todos",
                    help="qual algoritmo usar (todos = tabela comparativa)")
    ap.add_argument("--passos", action="store_true", help="imprime o vetor a cada passo")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    args = ap.parse_args()
    if args.demo:
        demo()
        return
    if not args.numeros:
        ap.print_help()
        sys.exit(2)
    if args.algoritmo == "todos":
        tabela(args.numeros)
        return
    resultado, est, seg = ordenar(args.algoritmo, args.numeros, mostrar=args.passos)
    print(f"{args.algoritmo}: {resultado}")
    print(f"{est.comparacoes} comparações, {est.trocas} trocas, {seg * 1000:.2f} ms")


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Implemente o selection sort e inclua na tabela comparativa.
# 2. Rode a tabela com um vetor já ordenado e com um invertido: qual
#    algoritmo sofre mais em cada caso? Por quê?
# 3. Adicione a opção --reverso que ordena do maior para o menor mudando
#    só as comparações, sem inverter a lista no fim.
# ------------------------------------------------------------
