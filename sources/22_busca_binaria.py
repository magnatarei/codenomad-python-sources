#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  22. Busca binária e busca linear
# ------------------------------------------------------------
# O que faz: implementa as duas buscas do zero, conta quantos passos cada uma
#            gasta em vetores de 10, 1.000 e 100.000 posições, mostra por que
#            a binária só funciona em vetor ordenado e como os passos crescem.
# Como usar: python sources/22_busca_binaria.py 3 8 15 23 42 --procurar 23
#            python sources/22_busca_binaria.py --tamanho 100000 --procurar 77777
#            python sources/22_busca_binaria.py --demo
# O que você aprende: laço while com dois limites, divisão inteira, dataclass
#            imutável com property, math.log2, crescimento linear contra
#            logarítmico e por que vale a pena ordenar antes de procurar.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import math
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Resultado:
    """Onde o valor foi achado (-1 quando não existe) e quantos passos custou."""

    posicao: int
    passos: int

    @property
    def achou(self) -> bool:
        """True quando a busca encontrou o valor."""
        return self.posicao >= 0

    def descrever(self) -> str:
        """Frase pronta para imprimir, como 'achou na posição 4 em 3 passo(s)'."""
        onde = f"achou na posição {self.posicao}" if self.achou else "não achou"
        return f"{onde} em {self.passos} passo(s)"


def busca_linear(v: list[int], alvo: int) -> Resultado:
    """Olha um elemento por vez, do início ao fim. Não exige vetor ordenado."""
    for i, valor in enumerate(v):
        if valor == alvo:
            return Resultado(i, i + 1)
    return Resultado(-1, len(v))  # percorreu tudo e não achou


def busca_binaria(v: list[int], alvo: int, rastro: list[str] | None = None) -> Resultado:
    """Corta o intervalo ao meio a cada passo. Só funciona com v ordenado."""
    baixo, alto = 0, len(v) - 1
    passos = 0
    while baixo <= alto:
        passos += 1
        meio = (baixo + alto) // 2  # divisão inteira: o índice nunca vira float
        if rastro is not None:
            rastro.append(f"passo {passos}: intervalo [{baixo}, {alto}], meio={meio}, v[{meio}]={v[meio]}")
        if v[meio] == alvo:
            return Resultado(meio, passos)
        if v[meio] < alvo:
            baixo = meio + 1  # o alvo só pode estar à direita
        else:
            alto = meio - 1  # o alvo só pode estar à esquerda
    return Resultado(-1, passos)


def esta_ordenado(v: list[int]) -> bool:
    """Confere se cada elemento é menor ou igual ao seguinte."""
    return all(v[i] <= v[i + 1] for i in range(len(v) - 1))


def gerar_vetor(tamanho: int) -> list[int]:
    """Gera um vetor ordenado com os pares 0, 2, 4, ... (ímpares nunca estão nele)."""
    return [2 * i for i in range(tamanho)]


def milhar(n: int) -> str:
    """Formata 100000 como 100.000, no padrão brasileiro."""
    return f"{n:,}".replace(",", ".")


def pior_caso_binaria(n: int) -> int:
    """Quantos passos a binária gasta, no máximo, num vetor de n posições."""
    return math.floor(math.log2(n)) + 1 if n > 0 else 0


def comparar(tamanho: int) -> None:
    """Procura três valores num vetor gerado e imprime os passos de cada busca."""
    v = gerar_vetor(tamanho)
    casos = [("primeiro", v[0]), ("último", v[-1]), ("ausente", v[-1] + 1)]
    print(f"\nVetor com {milhar(tamanho)} posições (teto da binária: {pior_caso_binaria(tamanho)} passos)")
    print(f"  {'caso':<10} {'valor':>8} {'linear':>10} {'binária':>10}")
    for rotulo, alvo in casos:
        lin = busca_linear(v, alvo)
        bin_ = busca_binaria(v, alvo)
        print(f"  {rotulo:<10} {milhar(alvo):>8} {milhar(lin.passos):>10} {milhar(bin_.passos):>10}")


def buscar(v: list[int], alvo: int) -> None:
    """Uso normal: roda as duas buscas no vetor informado e mostra o rastro."""
    print(f"Vetor ({len(v)} posições): {v if len(v) <= 20 else 'grande demais para mostrar'}")
    print(f"Busca linear : {busca_linear(v, alvo).descrever()}")
    if not esta_ordenado(v):
        print("Busca binária: pulada, o vetor não está ordenado (passe os números em ordem)")
        return
    rastro: list[str] = []
    resultado = busca_binaria(v, alvo, rastro)
    for linha in rastro:
        print("  " + linha)
    print(f"Busca binária: {resultado.descrever()}")


def demo() -> None:
    """Demonstração: rastro num vetor pequeno, três tamanhos e o vetor sem ordem."""
    print("=== Busca linear e busca binária: CodeNomad Academy ===")
    pequeno = gerar_vetor(10)
    print(f"Vetor de 10 posições: {pequeno}")
    print("Procurando 14 com a binária, passo a passo:")
    rastro: list[str] = []
    r = busca_binaria(pequeno, 14, rastro)
    for linha in rastro:
        print("  " + linha)
    print(f"  binária: {r.descrever()}; linear: {busca_linear(pequeno, 14).descrever()}")
    for tamanho in (10, 1_000, 100_000):
        comparar(tamanho)
    print("\nPor que a binária exige vetor ordenado?")
    bagunca = [14, 2, 8, 0, 18, 6, 4, 16, 10, 12]
    print(f"  vetor fora de ordem: {bagunca}")
    print(f"  binária procurando 14: {busca_binaria(bagunca, 14).descrever()}")
    print(f"  linear procurando 14 : {busca_linear(bagunca, 14).descrever()}")
    print("  A binária descarta metade do vetor supondo ordem; sem ordem, joga fora o lado certo.")
    print("\nCrescimento dos passos no pior caso (valor ausente):")
    print(f"  {'n':>10} {'linear':>10} {'binária':>8}")
    for n in (10, 100, 1_000, 10_000, 100_000, 1_000_000):
        print(f"  {milhar(n):>10} {milhar(n):>10} {pior_caso_binaria(n):>8}")
    print("  Dobrar o vetor custa um passo a mais para a binária e o dobro para a linear.")


def inteiro(texto: str) -> int:
    """Converte o argumento em inteiro com mensagem de erro em português."""
    try:
        return int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um número inteiro") from None


def main() -> None:
    """Lê os argumentos e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Compara busca linear e busca binária contando passos.")
    ap.add_argument("numeros", nargs="*", type=inteiro, help="vetor onde procurar (em ordem crescente)")
    ap.add_argument("--procurar", type=inteiro, help="valor a procurar")
    ap.add_argument("--tamanho", type=inteiro, help="gera um vetor ordenado com esse tamanho")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    args = ap.parse_args()
    if args.demo:
        demo()
        return
    if not args.numeros and args.tamanho is None:
        ap.print_help()
        sys.exit(2)
    if args.procurar is None:
        ap.error("informe o valor com --procurar")
    if args.tamanho is not None:
        if args.tamanho <= 0:
            ap.error("--tamanho precisa ser maior que zero")
        vetor = gerar_vetor(args.tamanho)
    else:
        vetor = args.numeros
    buscar(vetor, args.procurar)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Escreva a busca binária recursiva e confira se o número de passos
#    é o mesmo da versão com while.
# 2. Adapte a binária para devolver a PRIMEIRA posição quando o valor
#    aparece repetido (hoje ela devolve qualquer uma).
# 3. Meça com time.perf_counter o tempo das duas buscas num vetor de
#    10 milhões de posições e compare com a contagem de passos.
# ------------------------------------------------------------
