#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  24. Lista ligada do zero
# ------------------------------------------------------------
# O que faz: implementa uma lista simplesmente ligada com inserir no início,
#            no fim e em qualquer posição, remover, buscar, inverter, tamanho
#            e impressão, e compara com a list do Python em duas operações.
# Como usar: python sources/24_lista_ligada.py inicio:5 fim:9 em:1:7 buscar:9 inverter remover:5
#            python sources/24_lista_ligada.py --comparar 20000
#            python sources/24_lista_ligada.py --demo
# O que você aprende: referências entre objetos, dataclass com campo opcional,
#            __iter__ com yield, __len__ e __str__, percorrer com ponteiros,
#            e quando uma lista ligada ganha (ou perde) da list nativa.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import sys
import time
from dataclasses import dataclass
from typing import Iterator


@dataclass
class No:
    """Um nó guarda o valor e a referência para o seguinte (None no fim)."""

    valor: int
    seguinte: "No | None" = None


class ListaLigada:
    """Lista simplesmente ligada: só conhecemos a cabeça; o resto se alcança nó a nó."""

    def __init__(self) -> None:
        self.cabeca: No | None = None
        self.tamanho = 0

    def inserir_inicio(self, valor: int) -> None:
        """O novo nó aponta para a antiga cabeça e vira a nova cabeça: O(1)."""
        self.cabeca = No(valor, self.cabeca)
        self.tamanho += 1

    def inserir_fim(self, valor: int) -> None:
        """Caminha até o último nó e pendura o novo nele: O(n)."""
        novo = No(valor)
        if self.cabeca is None:
            self.cabeca = novo
        else:
            atual = self.cabeca
            while atual.seguinte is not None:
                atual = atual.seguinte
            atual.seguinte = novo
        self.tamanho += 1

    def _no_em(self, pos: int) -> No:
        """Devolve o nó da posição pos (0 é a cabeça). Erro se a posição não existe."""
        if not 0 <= pos < self.tamanho:
            raise IndexError(f"posição {pos} não existe (tamanho atual: {self.tamanho})")
        atual = self.cabeca
        for _ in range(pos):
            assert atual is not None  # garantido pela checagem de tamanho acima
            atual = atual.seguinte
        assert atual is not None
        return atual

    def inserir_em(self, pos: int, valor: int) -> None:
        """Insere antes do item que hoje ocupa pos; pos igual ao tamanho insere no fim."""
        if not 0 <= pos <= self.tamanho:
            raise IndexError(f"não dá para inserir na posição {pos} (use de 0 a {self.tamanho})")
        if pos == 0:
            self.inserir_inicio(valor)
            return
        if pos == self.tamanho:
            self.inserir_fim(valor)
            return
        anterior = self._no_em(pos - 1)
        anterior.seguinte = No(valor, anterior.seguinte)
        self.tamanho += 1

    def obter(self, pos: int) -> int:
        """Valor da posição pos. Na list nativa isso é O(1); aqui é O(n)."""
        return self._no_em(pos).valor

    def buscar(self, valor: int) -> int:
        """Posição da primeira ocorrência do valor, ou -1 se não estiver na lista."""
        for pos, item in enumerate(self):
            if item == valor:
                return pos
        return -1

    def remover(self, valor: int) -> bool:
        """Remove a primeira ocorrência do valor. Devolve False se não achou."""
        anterior: No | None = None
        atual = self.cabeca
        while atual is not None and atual.valor != valor:
            anterior, atual = atual, atual.seguinte
        if atual is None:
            return False
        if anterior is None:
            self.cabeca = atual.seguinte  # removendo a cabeça
        else:
            anterior.seguinte = atual.seguinte  # pula o nó removido
        self.tamanho -= 1
        return True

    def inverter(self) -> None:
        """Inverte os ponteiros no lugar com três referências: anterior, atual, seguinte."""
        anterior: No | None = None
        atual = self.cabeca
        while atual is not None:
            seguinte = atual.seguinte
            atual.seguinte = anterior  # vira o ponteiro para trás
            anterior, atual = atual, seguinte
        self.cabeca = anterior

    def __iter__(self) -> Iterator[int]:
        atual = self.cabeca
        while atual is not None:
            yield atual.valor
            atual = atual.seguinte

    def __len__(self) -> int:
        return self.tamanho

    def __str__(self) -> str:
        if self.cabeca is None:
            return "(vazia)"
        return " -> ".join(str(v) for v in self) + " -> None"


def aplicar(lista: ListaLigada, comando: str) -> str:
    """Executa um comando como inicio:5, fim:9, em:1:7, remover:5, buscar:9 ou inverter."""
    partes = comando.split(":")
    nome, args = partes[0], partes[1:]
    if any(not p.lstrip("-").isdigit() for p in args):
        raise ValueError(f"'{comando}': os valores depois de ':' precisam ser inteiros")
    nums = [int(p) for p in args]
    if nome == "inicio" and len(nums) == 1:
        lista.inserir_inicio(nums[0])
        return f"inserir {nums[0]} no início"
    if nome == "fim" and len(nums) == 1:
        lista.inserir_fim(nums[0])
        return f"inserir {nums[0]} no fim"
    if nome == "em" and len(nums) == 2:
        lista.inserir_em(nums[0], nums[1])
        return f"inserir {nums[1]} na posição {nums[0]}"
    if nome == "remover" and len(nums) == 1:
        achou = lista.remover(nums[0])
        return f"remover {nums[0]}: {'removido' if achou else 'não estava na lista'}"
    if nome == "buscar" and len(nums) == 1:
        pos = lista.buscar(nums[0])
        return f"buscar {nums[0]}: {'posição ' + str(pos) if pos >= 0 else 'não encontrado'}"
    if nome == "inverter" and not nums:
        lista.inverter()
        return "inverter"
    raise ValueError(f"comando desconhecido: '{comando}' (use inicio:N, fim:N, em:POS:N, remover:N, buscar:N, inverter)")


def executar(comandos: list[str]) -> ListaLigada:
    """Aplica os comandos em ordem, imprimindo a lista depois de cada um."""
    lista = ListaLigada()
    for comando in comandos:
        descricao = aplicar(lista, comando)
        print(f"  {descricao:<36} {lista}  (tamanho {len(lista)})")
    return lista


def comparar_com_list(n: int) -> None:
    """Mede inserir n vezes no início e ler o meio: cada estrutura ganha uma rodada."""
    ligada = ListaLigada()
    t0 = time.perf_counter()
    for i in range(n):
        ligada.inserir_inicio(i)
    t_ligada = time.perf_counter() - t0
    nativa: list[int] = []
    t0 = time.perf_counter()
    for i in range(n):
        nativa.insert(0, i)  # a list precisa deslocar todos os itens a cada inserção
    t_nativa = time.perf_counter() - t0
    print(f"  inserir {n} itens no início: ligada {t_ligada * 1000:.1f} ms, list {t_nativa * 1000:.1f} ms")
    meio = n // 2
    t0 = time.perf_counter()
    for _ in range(200):
        ligada.obter(meio)  # caminha meio nó a nó, 200 vezes
    t_ligada = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(200):
        nativa[meio]
    t_nativa = time.perf_counter() - t0
    print(f"  ler a posição {meio} 200 vezes: ligada {t_ligada * 1000:.1f} ms, list {t_nativa * 1000:.3f} ms")
    print("  Moral: a ligada insere no início sem deslocar nada; a list acessa qualquer posição na hora.")


def demo() -> None:
    """Executa todas as operações mostrando a lista a cada passo, e a comparação."""
    print("=== Lista ligada do zero: CodeNomad Academy ===\n")
    print("Operações passo a passo:")
    lista = executar(["inicio:5", "inicio:3", "fim:9", "fim:12", "em:2:7", "buscar:9",
                      "buscar:100", "remover:3", "remover:100", "inverter", "em:4:1"])
    print(f"\nPercorrendo com for (graças ao __iter__): {[v for v in lista]}")
    print(f"Valor na posição 2: {lista.obter(2)}")
    try:
        lista.obter(50)
    except IndexError as e:
        print(f"Erro tratado: {e}")
    print("\nLista ligada contra a list nativa:")
    comparar_com_list(20_000)


def main() -> None:
    """Lê os argumentos e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Lista ligada com inserir, remover, buscar e inverter.")
    ap.add_argument("comandos", nargs="*", help="inicio:N fim:N em:POS:N remover:N buscar:N inverter")
    ap.add_argument("--comparar", type=int, metavar="N", help="compara com a list usando N itens")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    args = ap.parse_args()
    if args.demo:
        demo()
        return
    if not args.comandos and args.comparar is None:
        ap.print_help()
        sys.exit(2)
    try:
        if args.comandos:
            executar(args.comandos)
        if args.comparar is not None:
            if args.comparar < 10:
                ap.error("--comparar precisa de pelo menos 10 itens")
            comparar_com_list(args.comparar)
    except (ValueError, IndexError) as e:
        sys.exit(f"Erro: {e}")


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Guarde também uma referência para a cauda e faça inserir_fim ficar O(1).
# 2. Transforme em lista duplamente ligada (cada nó conhece o anterior) e
#    escreva um método que percorre de trás para a frente.
# 3. Implemente remover_duplicados() sem usar set nem list, só caminhando
#    pelos nós. Qual é a complexidade da sua solução?
# ------------------------------------------------------------
