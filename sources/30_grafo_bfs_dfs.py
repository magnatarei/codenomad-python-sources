#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  30. Grafos: BFS e DFS num labirinto
# ------------------------------------------------------------
# O que faz: lê um labirinto em texto ('#' parede, '.' livre, S início,
#            E saída), monta o grafo das células livres, acha o caminho mais
#            curto com busca em largura (BFS), explora com busca em
#            profundidade (DFS) e desenha o caminho encontrado.
# Como usar: python sources/30_grafo_bfs_dfs.py --arquivo labirinto.txt
#            python sources/30_grafo_bfs_dfs.py --arquivo labirinto.txt --metodo dfs
#            python sources/30_grafo_bfs_dfs.py --demo
# O que você aprende: grafo como dicionário de adjacência, tuplas como
#            chaves, deque como fila e list como pilha, reconstrução de
#            caminho com dicionário de predecessores e leitura com pathlib.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path

Celula = tuple[int, int]  # (linha, coluna)
Grafo = dict[Celula, list[Celula]]

LABIRINTO_DEMO = """
###############
#S....#.......#
#.###.#.#####.#
#...#.#.....#.#
###.#.#####.#.#
#...#.......#.#
#.#########.#.#
#.......#...#.#
#######.#.###.#
#.......#....E#
###############
"""

LABIRINTO_SEM_SAIDA = """
#######
#S..#.#
#.#.#E#
#...###
#######
"""


@dataclass
class Labirinto:
    """A grade de símbolos e as posições de início e saída."""

    grade: list[list[str]]
    inicio: Celula
    saida: Celula

    @property
    def altura(self) -> int:
        """Quantidade de linhas da grade."""
        return len(self.grade)

    @property
    def largura(self) -> int:
        """Quantidade de colunas da grade."""
        return len(self.grade[0])

    def livre(self, c: Celula) -> bool:
        """Uma célula é transitável se está dentro da grade e não é parede."""
        lin, col = c
        return 0 <= lin < self.altura and 0 <= col < self.largura and self.grade[lin][col] != "#"


def carregar(texto: str) -> Labirinto:
    """Transforma o texto em grade (linhas curtas ganham parede no fim) e valida S e E."""
    linhas = [linha.rstrip() for linha in texto.strip("\n").splitlines()]
    if not linhas or not any(linhas):
        raise ValueError("o labirinto está vazio")
    largura = max(len(linha) for linha in linhas)
    grade = [list(linha.ljust(largura, "#")) for linha in linhas]
    inicios: list[Celula] = []
    saidas: list[Celula] = []
    for i, linha in enumerate(grade):
        for j, ch in enumerate(linha):
            if ch not in "#.SE":
                raise ValueError(f"símbolo inválido '{ch}' na linha {i}, coluna {j} (use # . S E)")
            if ch == "S":
                inicios.append((i, j))
            elif ch == "E":
                saidas.append((i, j))
    if len(inicios) != 1 or len(saidas) != 1:
        raise ValueError(f"precisa de exatamente um S e um E (achei {len(inicios)} S e {len(saidas)} E)")
    return Labirinto(grade, inicios[0], saidas[0])


def construir_grafo(lab: Labirinto) -> Grafo:
    """Cada célula livre vira um vértice; vizinhos ortogonais livres viram arestas."""
    grafo: Grafo = {}
    for i in range(lab.altura):
        for j in range(lab.largura):
            if lab.livre((i, j)):
                vizinhos = [(i + 1, j), (i, j + 1), (i - 1, j), (i, j - 1)]  # baixo, direita, cima, esquerda
                grafo[(i, j)] = [v for v in vizinhos if lab.livre(v)]
    return grafo


def reconstruir(anterior: dict[Celula, Celula | None], fim: Celula) -> list[Celula]:
    """Volta de célula em célula até o início (que não tem anterior) e inverte."""
    caminho: list[Celula] = []
    atual: Celula | None = fim
    while atual is not None:
        caminho.append(atual)
        atual = anterior[atual]
    return caminho[::-1]


def bfs(grafo: Grafo, inicio: Celula, fim: Celula) -> tuple[list[Celula], int]:
    """Busca em largura: visita por camadas de distância, logo o primeiro caminho até E é o mais curto."""
    fila = deque([inicio])
    anterior: dict[Celula, Celula | None] = {inicio: None}  # também serve de "já visitei"
    while fila:
        atual = fila.popleft()  # tira da frente: quem entrou primeiro sai primeiro
        if atual == fim:
            return reconstruir(anterior, fim), len(anterior)
        for vizinho in grafo[atual]:
            if vizinho not in anterior:
                anterior[vizinho] = atual
                fila.append(vizinho)
    return [], len(anterior)


def dfs(grafo: Grafo, inicio: Celula, fim: Celula) -> tuple[list[Celula], int]:
    """Busca em profundidade: a mesma ideia com uma pilha. Acha UM caminho, não o mais curto."""
    pilha = [inicio]
    anterior: dict[Celula, Celula | None] = {inicio: None}
    while pilha:
        atual = pilha.pop()  # tira do fim: mergulha pelo vizinho descoberto por último
        if atual == fim:
            return reconstruir(anterior, fim), len(anterior)
        for vizinho in grafo[atual]:
            if vizinho not in anterior:
                anterior[vizinho] = atual
                pilha.append(vizinho)
    return [], len(anterior)


def desenhar(lab: Labirinto, caminho: list[Celula]) -> str:
    """Copia a grade e marca o caminho com '*', preservando S e E."""
    copia = [linha[:] for linha in lab.grade]
    for i, j in caminho:
        if copia[i][j] == ".":
            copia[i][j] = "*"
    return "\n".join("".join(linha) for linha in copia)


def resolver(lab: Labirinto, metodo: str) -> None:
    """Roda o método pedido, imprime as contagens e desenha o resultado."""
    grafo = construir_grafo(lab)
    busca = bfs if metodo == "bfs" else dfs
    nome = "BFS (largura)" if metodo == "bfs" else "DFS (profundidade)"
    caminho, visitadas = busca(grafo, lab.inicio, lab.saida)
    if not caminho:
        print(f"{nome}: sem saída. Visitou {visitadas} de {len(grafo)} células livres e nunca chegou ao E.")
        return
    print(f"{nome}: caminho com {len(caminho) - 1} passos, {visitadas} células visitadas de {len(grafo)}")
    print(desenhar(lab, caminho))


def demo() -> None:
    """Resolve o labirinto embutido com os dois métodos e mostra um sem saída."""
    print("=== Grafos: BFS e DFS num labirinto: CodeNomad Academy ===\n")
    lab = carregar(LABIRINTO_DEMO)
    grafo = construir_grafo(lab)
    arestas = sum(len(v) for v in grafo.values()) // 2  # cada ligação aparece nos dois lados
    print(f"Labirinto {lab.altura}x{lab.largura}: {len(grafo)} células livres (vértices), {arestas} ligações (arestas)")
    print(f"Início em {lab.inicio}, saída em {lab.saida}; vizinhos do início: {grafo[lab.inicio]}\n")
    resolver(lab, "bfs")
    print()
    resolver(lab, "dfs")
    print("\nA BFS garante o caminho mais curto. A DFS visitou menos células, mas o caminho")
    print("que ela achou é mais longo: ela mergulha no primeiro corredor e só volta se bater na parede.")
    print("\nLabirinto em que o E está murado:")
    sem_saida = carregar(LABIRINTO_SEM_SAIDA)
    print(desenhar(sem_saida, []))
    resolver(sem_saida, "bfs")


def main() -> None:
    """Lê os argumentos e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Resolve labirintos em texto com BFS e DFS.")
    ap.add_argument("--arquivo", help="arquivo de texto com o labirinto (# parede, . livre, S início, E saída)")
    ap.add_argument("--metodo", choices=("bfs", "dfs", "ambos"), default="ambos", help="qual busca rodar")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    args = ap.parse_args()
    if args.demo:
        demo()
        return
    if not args.arquivo:
        ap.print_help()
        sys.exit(2)
    arquivo = Path(args.arquivo)
    if not arquivo.is_file():
        sys.exit(f"Erro: arquivo não encontrado: {args.arquivo}")
    try:
        lab = carregar(arquivo.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.exit(f"Erro: {e}")
    metodos = ("bfs", "dfs") if args.metodo == "ambos" else (args.metodo,)
    for metodo in metodos:
        resolver(lab, metodo)
        print()


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Permita movimento na diagonal (8 vizinhos) e veja como o caminho
#    mais curto muda.
# 2. Dê pesos às células (areia custa 3, grama custa 1) e troque a BFS
#    pelo algoritmo de Dijkstra usando heapq.
# 3. Gere labirintos aleatórios com DFS recursiva (o clássico "recursive
#    backtracker") e resolva-os com o seu próprio código.
# ------------------------------------------------------------
