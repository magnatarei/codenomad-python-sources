#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  28. Operações com matrizes
# ------------------------------------------------------------
# O que faz: soma, subtração, multiplicação, transposta, determinante
#            (recursivo, por expansão de Laplace) e matriz identidade, com
#            validação de dimensões e impressão alinhada em colunas.
# Como usar: python sources/28_matriz_operacoes.py mult "1,2;3,4" "5,6;7,8"
#            python sources/28_matriz_operacoes.py det "2,0,1;1,3,2;1,1,4"
#            python sources/28_matriz_operacoes.py --demo
# O que você aprende: listas de listas, list comprehension aninhada, zip
#            para transpor, recursão com submatrizes, exceção própria,
#            alias de tipo e formatação alinhada com f-strings.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import math
import sys
from typing import Callable

Matriz = list[list[float]]
OPERACOES = ("soma", "sub", "mult", "transposta", "det", "identidade")
QUANTOS_ARGUMENTOS = {"soma": 2, "sub": 2, "mult": 2, "transposta": 1, "det": 1, "identidade": 1}


class ErroMatriz(ValueError):
    """Dimensões incompatíveis ou matriz mal formada."""


def validar(m: Matriz, nome: str = "matriz") -> None:
    """Garante que a matriz não é vazia e que todas as linhas têm o mesmo tamanho."""
    if not m or not m[0]:
        raise ErroMatriz(f"a {nome} está vazia")
    largura = len(m[0])
    if any(len(linha) != largura for linha in m):
        raise ErroMatriz(f"a {nome} tem linhas de tamanhos diferentes")


def dimensoes(m: Matriz) -> tuple[int, int]:
    """Devolve (linhas, colunas)."""
    return len(m), len(m[0])


def exigir_mesmas_dimensoes(a: Matriz, b: Matriz, verbo: str) -> None:
    """Soma e subtração só funcionam entre matrizes do mesmo tamanho."""
    validar(a, "primeira matriz")
    validar(b, "segunda matriz")
    if dimensoes(a) != dimensoes(b):
        (la, ca), (lb, cb) = dimensoes(a), dimensoes(b)
        raise ErroMatriz(f"não dá para {verbo} {la}x{ca} com {lb}x{cb}: as dimensões precisam ser iguais")


def somar(a: Matriz, b: Matriz) -> Matriz:
    """Soma elemento a elemento; zip anda pelas duas matrizes ao mesmo tempo."""
    exigir_mesmas_dimensoes(a, b, "somar")
    return [[x + y for x, y in zip(la, lb)] for la, lb in zip(a, b)]


def subtrair(a: Matriz, b: Matriz) -> Matriz:
    """Subtrai elemento a elemento."""
    exigir_mesmas_dimensoes(a, b, "subtrair")
    return [[x - y for x, y in zip(la, lb)] for la, lb in zip(a, b)]


def multiplicar(a: Matriz, b: Matriz) -> Matriz:
    """Produto: cada célula é a linha de A 'vezes' a coluna de B. Colunas de A = linhas de B."""
    validar(a, "primeira matriz")
    validar(b, "segunda matriz")
    (la, ca), (lb, cb) = dimensoes(a), dimensoes(b)
    if ca != lb:
        raise ErroMatriz(f"não dá para multiplicar {la}x{ca} por {lb}x{cb}: "
                         f"as colunas da primeira ({ca}) devem ser iguais às linhas da segunda ({lb})")
    return [[sum(a[i][k] * b[k][j] for k in range(ca)) for j in range(cb)] for i in range(la)]


def transpor(m: Matriz) -> Matriz:
    """Troca linhas por colunas. zip(*m) entrega as colunas uma a uma."""
    validar(m)
    return [list(coluna) for coluna in zip(*m)]


def identidade(n: int) -> Matriz:
    """Matriz quadrada com 1 na diagonal e 0 no resto: o neutro da multiplicação."""
    if n < 1:
        raise ErroMatriz("a identidade precisa de ordem pelo menos 1")
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def submatriz(m: Matriz, linha: int, coluna: int) -> Matriz:
    """Copia a matriz sem uma linha e sem uma coluna (é o que o determinante usa)."""
    return [[v for j, v in enumerate(l) if j != coluna] for i, l in enumerate(m) if i != linha]


def determinante(m: Matriz) -> float:
    """Expansão de Laplace pela primeira linha: recursiva e didática, mas O(n!)."""
    validar(m)
    n, c = dimensoes(m)
    if n != c:
        raise ErroMatriz(f"determinante só existe para matriz quadrada (esta é {n}x{c})")
    if n > 9:
        raise ErroMatriz("a versão recursiva só vai até 9x9; acima disso use eliminação de Gauss")
    if n == 1:
        return m[0][0]
    if n == 2:
        return m[0][0] * m[1][1] - m[0][1] * m[1][0]  # a*d - b*c
    total = 0.0
    for j in range(n):
        sinal = 1 if j % 2 == 0 else -1  # os sinais alternam: + - + - ...
        total += sinal * m[0][j] * determinante(submatriz(m, 0, j))
    return total


def numero(x: float) -> str:
    """6.0 vira '6'; 2.5 continua '2.5'; -0.0 vira '0'."""
    if x == int(x):
        return str(int(x))
    return f"{x:.4g}"


def formatar(m: Matriz) -> str:
    """Imprime com colunas alinhadas pela célula mais larga."""
    textos = [[numero(x) for x in linha] for linha in m]
    largura = max(len(t) for linha in textos for t in linha)
    return "\n".join("  [ " + "  ".join(t.rjust(largura) for t in linha) + " ]" for linha in textos)


def ler_matriz(texto: str) -> Matriz:
    """Converte '1,2;3,4' em [[1.0, 2.0], [3.0, 4.0]]: ';' separa linhas, ',' separa colunas."""
    try:
        m = [[float(v) for v in linha.split(",")] for linha in texto.split(";")]
    except ValueError:
        raise ErroMatriz(f"'{texto}' tem algo que não é número (use o formato 1,2;3,4)") from None
    if any(not math.isfinite(v) for linha in m for v in linha):
        raise ErroMatriz("use só números finitos (nada de inf ou nan)")
    validar(m)
    return m


def mostrar(titulo: str, m: Matriz) -> None:
    """Imprime um título e a matriz formatada."""
    print(f"{titulo}:\n{formatar(m)}")


def demo() -> None:
    """Executa todas as operações com matrizes 2x2 e 3x3 de exemplo."""
    print("=== Operações com matrizes: CodeNomad Academy ===\n")
    a = ler_matriz("1,2;3,4")
    b = ler_matriz("5,6;7,8")
    c = ler_matriz("2,0,1;1,3,2;1,1,4")
    mostrar("A (2x2)", a)
    mostrar("B (2x2)", b)
    mostrar("C (3x3)", c)
    mostrar("\nA + B", somar(a, b))
    mostrar("A - B", subtrair(a, b))
    mostrar("A x B", multiplicar(a, b))
    mostrar("B x A (a ordem importa)", multiplicar(b, a))
    mostrar("Transposta de C", transpor(c))
    print(f"\ndet(A) = {numero(determinante(a))}   (1*4 - 2*3)")
    print(f"det(C) = {numero(determinante(c))}   (Laplace pela primeira linha)")
    mostrar("\nIdentidade 3x3", identidade(3))
    mostrar("C x I3 (devolve a própria C)", multiplicar(c, identidade(3)))
    print("\nErros tratados:")
    tentativas: list[tuple[str, Callable[[], object]]] = [
        ("A + C", lambda: somar(a, c)),
        ("A x C", lambda: multiplicar(a, c)),
        ("det de 2x3", lambda: determinante(ler_matriz("1,2,3;4,5,6"))),
        ("texto ruim", lambda: ler_matriz("1,x;3,4")),
    ]
    for descricao, tentativa in tentativas:
        try:
            tentativa()
        except ErroMatriz as e:
            print(f"  {descricao:<12} -> {e}")


def executar(operacao: str, args: list[str]) -> Matriz | str:
    """Despacha a operação pedida na linha de comando, conferindo a quantidade de argumentos."""
    precisa = QUANTOS_ARGUMENTOS[operacao]
    if len(args) != precisa:
        raise ErroMatriz(f"{operacao} precisa de {precisa} argumento(s), mas veio {len(args)}")
    if operacao == "identidade":
        if not args[0].isdigit():
            raise ErroMatriz(f"identidade precisa da ordem N (um inteiro), veio '{args[0]}'")
        return identidade(int(args[0]))
    ms = [ler_matriz(t) for t in args]
    if operacao == "soma":
        return somar(ms[0], ms[1])
    if operacao == "sub":
        return subtrair(ms[0], ms[1])
    if operacao == "mult":
        return multiplicar(ms[0], ms[1])
    if operacao == "transposta":
        return transpor(ms[0])
    return f"det = {numero(determinante(ms[0]))}"


def main() -> None:
    """Lê os argumentos e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Soma, subtrai, multiplica, transpõe e calcula determinantes.")
    ap.add_argument("operacao", nargs="?", choices=OPERACOES, help="qual operação fazer")
    ap.add_argument("matrizes", nargs="*", help="matrizes no formato 1,2;3,4 (ou a ordem N na identidade)")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    args = ap.parse_args()
    if args.demo:
        demo()
        return
    if args.operacao is None:
        ap.print_help()
        sys.exit(2)
    try:
        resultado = executar(args.operacao, args.matrizes)
    except ErroMatriz as e:
        sys.exit(f"Erro: {e}")
    print(resultado if isinstance(resultado, str) else formatar(resultado))


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Implemente o determinante por eliminação de Gauss, que é O(n³), e
#    compare o tempo com o de Laplace numa matriz 9x9.
# 2. Escreva inversa(m) para matrizes 2x2 e confira que m x inversa(m)
#    dá a identidade.
# 3. Leia as matrizes de um arquivo CSV com o módulo csv, uma linha por
#    linha da matriz.
# ------------------------------------------------------------
