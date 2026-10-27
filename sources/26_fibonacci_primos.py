#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  26. Fibonacci, fatorial e primos
# ------------------------------------------------------------
# O que faz: calcula Fibonacci de três jeitos (recursivo puro, com memória e
#            iterativo) comparando tempos e chamadas, fatorial, teste de
#            primalidade e o crivo de Eratóstenes até N, e explica por que
#            a recursão pura explode.
# Como usar: python sources/26_fibonacci_primos.py --fib 25
#            python sources/26_fibonacci_primos.py --fatorial 20 --primo 1000003 --crivo 50
#            python sources/26_fibonacci_primos.py --demo
# O que você aprende: recursão e caso base, memoização com dicionário,
#            laços iterativos, math.isqrt, crivo com lista de booleanos,
#            inteiros sem limite de tamanho e medição com perf_counter.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import math
import sys
import time
from dataclasses import dataclass
from typing import Callable

LIMITE_RECURSIVO = 35  # acima disso o recursivo puro leva minutos
LIMITE_MEMO = 900  # o Python limita a profundidade da recursão perto de 1000
LIMITE_CRIVO = 10_000_000  # uma lista de booleanos por posição: acima disso pesa na memória


@dataclass
class Contador:
    """Conta quantas vezes uma função foi chamada."""

    chamadas: int = 0


def fib_recursivo(n: int, cont: Contador) -> int:
    """Definição direta: fib(n) = fib(n-1) + fib(n-2). Elegante e lentíssima."""
    cont.chamadas += 1
    if n < 2:
        return n  # caso base: fib(0) = 0, fib(1) = 1
    return fib_recursivo(n - 1, cont) + fib_recursivo(n - 2, cont)


def fib_memo(n: int, cont: Contador, memo: dict[int, int] | None = None) -> int:
    """Mesma recursão, mas guarda cada resultado num dicionário (memoização)."""
    if memo is None:
        memo = {}
    cont.chamadas += 1
    if n < 2:
        return n
    if n not in memo:  # cada n é calculado uma única vez; depois é só consulta
        memo[n] = fib_memo(n - 1, cont, memo) + fib_memo(n - 2, cont, memo)
    return memo[n]


def fib_iterativo(n: int, cont: Contador) -> int:
    """Dois acumuladores andando para a frente: sem recursão e sem memória extra."""
    cont.chamadas += 1
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b  # a vira o seguinte, b vira a soma dos dois
    return a


def fatorial(n: int) -> int:
    """n! = 1 * 2 * ... * n. O int do Python cresce sem estourar."""
    if n < 0:
        raise ValueError("fatorial só existe para inteiros não negativos")
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado


def menor_divisor(n: int) -> int:
    """Menor divisor maior que 1; é o próprio n quando n é primo."""
    if n % 2 == 0:
        return 2
    for d in range(3, math.isqrt(n) + 1, 2):  # só ímpares: os pares já caíram
        if n % d == 0:
            return d
    return n


def eh_primo(n: int) -> bool:
    """Divisão por tentativa: basta testar divisores até a raiz quadrada de n."""
    return n >= 2 and menor_divisor(n) == n


def crivo(limite: int) -> list[int]:
    """Crivo de Eratóstenes: marca os múltiplos de cada primo e devolve os primos até limite."""
    if limite < 2:
        return []
    candidato = [True] * (limite + 1)
    candidato[0] = candidato[1] = False
    for i in range(2, math.isqrt(limite) + 1):
        if candidato[i]:
            for multiplo in range(i * i, limite + 1, i):  # começa em i²: os menores já foram marcados
                candidato[multiplo] = False
    return [i for i, eh in enumerate(candidato) if eh]


def milhar(n: int) -> str:
    """Formata 2692537 como 2.692.537, no padrão brasileiro."""
    return f"{n:,}".replace(",", ".")


def cronometrar(func: Callable[[int, Contador], int], n: int) -> tuple[int, int, float]:
    """Roda uma função de Fibonacci e devolve (resultado, chamadas, milissegundos)."""
    cont = Contador()
    inicio = time.perf_counter()
    valor = func(n, cont)
    return valor, cont.chamadas, (time.perf_counter() - inicio) * 1000


def comparar_fibonacci(n: int) -> None:
    """Tabela com os três jeitos; pula uma versão quando n passa do limite dela."""
    print(f"Fibonacci de {n}:")
    print(f"  {'versão':<12} {'resultado':>16} {'chamadas':>12} {'tempo (ms)':>11}")
    versoes: list[tuple[str, Callable[[int, Contador], int], int]] = [
        ("recursivo", fib_recursivo, LIMITE_RECURSIVO),
        ("com memória", fib_memo, LIMITE_MEMO),
        ("iterativo", fib_iterativo, 1_000_000),
    ]
    for nome, func, limite in versoes:
        if n > limite:
            print(f"  {nome:<12} pulado: esta versão só vai até n={limite}")
            continue
        valor, chamadas, ms = cronometrar(func, n)
        texto = milhar(valor) if valor < 10 ** 14 else f"{len(str(valor))} dígitos"
        print(f"  {nome:<12} {texto:>16} {milhar(chamadas):>12} {ms:>11.3f}")


def explicar_explosao() -> None:
    """Mostra com números por que a recursão pura cresce de forma exponencial."""
    print("Por que o recursivo puro explode?")
    print("  fib(30) chama fib(29) e fib(28); fib(29) chama fib(28) de novo, e assim por diante.")
    for n in (10, 20, 30):
        _, chamadas, _ = cronometrar(fib_recursivo, n)
        print(f"  fib({n}) faz {milhar(chamadas)} chamadas")
    print("  Somar 10 ao n multiplica as chamadas por cerca de 123: crescimento exponencial.")
    print("  Com memória, cada fib(k) é calculado uma única vez: cerca de 2n chamadas.")


def demo() -> None:
    """Demonstração: três Fibonacci para n=30, a explosão, fatorial e primos."""
    print("=== Fibonacci, fatorial e primos: CodeNomad Academy ===\n")
    comparar_fibonacci(30)
    print()
    explicar_explosao()
    print(f"\nFatorial de 20: {milhar(fatorial(20))}")
    print(f"Fatorial de 50 tem {len(str(fatorial(50)))} dígitos: o int do Python não estoura.")
    primos = crivo(100)
    print(f"\nPrimos até 100 ({len(primos)} no total):\n  {primos}")
    for n in (97, 1_000_003, 1_000_001):
        if eh_primo(n):
            print(f"  {milhar(n)} é primo? sim")
        else:
            print(f"  {milhar(n)} é primo? não, é divisível por {menor_divisor(n)}")


def nao_negativo(texto: str) -> int:
    """Converte o argumento em inteiro maior ou igual a zero, com erro em português."""
    if not texto.isdigit():
        raise argparse.ArgumentTypeError(f"'{texto}' não é um inteiro maior ou igual a zero")
    return int(texto)


def main() -> None:
    """Lê os argumentos e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Fibonacci de três jeitos, fatorial, primos e crivo.")
    ap.add_argument("--fib", type=nao_negativo, metavar="N", help="compara as três versões de Fibonacci")
    ap.add_argument("--fatorial", type=nao_negativo, metavar="N", help="calcula N!")
    ap.add_argument("--primo", type=nao_negativo, metavar="N", help="testa se N é primo")
    ap.add_argument("--crivo", type=nao_negativo, metavar="N", help="lista os primos até N")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    args = ap.parse_args()
    if args.demo:
        demo()
        return
    if all(v is None for v in (args.fib, args.fatorial, args.primo, args.crivo)):
        ap.print_help()
        sys.exit(2)
    if args.fib is not None:
        comparar_fibonacci(args.fib)
    if args.fatorial is not None:
        if args.fatorial > 10_000:
            ap.error("--fatorial só até 10000 (o resultado teria dezenas de milhares de dígitos)")
        valor = fatorial(args.fatorial)
        print(f"{args.fatorial}! = {milhar(valor) if valor < 10 ** 30 else f'{len(str(valor))} dígitos'}")
    if args.primo is not None:
        if eh_primo(args.primo):
            print(f"{milhar(args.primo)} é primo")
        else:
            print(f"{milhar(args.primo)} não é primo: divisível por {menor_divisor(args.primo)}" if args.primo >= 2
                  else f"{args.primo} não é primo: primos começam no 2")
    if args.crivo is not None:
        if args.crivo > LIMITE_CRIVO:
            ap.error(f"--crivo só até {milhar(LIMITE_CRIVO)}")
        primos = crivo(args.crivo)
        print(f"{len(primos)} primos até {milhar(args.crivo)}: {primos if len(primos) <= 50 else '...'}")


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Troque o dicionário de fib_memo por @functools.lru_cache e compare
#    o número de chamadas.
# 2. Escreva fatorial_recursivo(n) e descubra a partir de qual n o Python
#    reclama (RecursionError). Depois leia sobre sys.setrecursionlimit.
# 3. Faça o crivo contar quantos primos existem até 10 milhões e meça o
#    tempo; depois tente fazer o mesmo com eh_primo e compare.
# ------------------------------------------------------------
