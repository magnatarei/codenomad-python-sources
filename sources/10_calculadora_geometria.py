#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  10. Calculadora de geometria
# ------------------------------------------------------------
# O que faz: calcula área e perímetro de quadrado, retângulo, triângulo
#            (conferindo se o triângulo existe), círculo e trapézio, e o
#            volume (com a área da superfície) de cubo, esfera e cilindro.
#            Cada figura é um subcomando com as suas próprias medidas.
# Como usar: python 10_calculadora_geometria.py triangulo 3 4 5
#            python 10_calculadora_geometria.py trapezio 10 6 4 --lados 5 5
#            python 10_calculadora_geometria.py cilindro 2 10
#            python 10_calculadora_geometria.py --demo
# O que você aprende: argparse com subcomandos e argumentos posicionais,
#            o módulo math (pi, sqrt, isclose), dataclasses com campos
#            opcionais, fórmula de Heron e a desigualdade triangular, e
#            impressão de uma tabela com valores que podem não existir.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import math
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Resultado:
    """O que cada figura devolve. O que não se aplica fica como None."""

    forma: str
    medidas: str
    area: float | None = None
    perimetro: float | None = None
    volume: float | None = None
    observacao: str = ""


def positivo(texto: str) -> float:
    """Toda medida precisa ser um número maior que zero. Aceita vírgula."""
    try:
        valor = float(texto.strip().replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um número válido") from None
    if valor <= 0:
        raise argparse.ArgumentTypeError(f"a medida precisa ser maior que zero (veio {texto})")
    return valor


def medida(valor: float) -> str:
    """Mostra a medida sem zeros inúteis e com vírgula: 3.5 vira '3,5' e 4.0 vira '4'."""
    return f"{valor:g}".replace(".", ",")


def quadrado(lado: float) -> Resultado:
    """Área = lado ao quadrado; perímetro = quatro lados."""
    return Resultado("Quadrado", f"lado {medida(lado)}", area=lado ** 2, perimetro=4 * lado)


def retangulo(base: float, altura: float) -> Resultado:
    """Área = base vezes altura; perímetro = duas bases e duas alturas."""
    return Resultado("Retângulo", f"{medida(base)} x {medida(altura)}", area=base * altura, perimetro=2 * (base + altura))


def triangulo(a: float, b: float, c: float) -> Resultado:
    """Área pela fórmula de Heron. Antes, confere a desigualdade triangular.

    Um triângulo só existe se cada lado for menor que a soma dos outros dois.
    Com lados 1, 2 e 3, por exemplo, os dois menores não "fecham" a figura.
    """
    if a >= b + c or b >= a + c or c >= a + b:
        raise ValueError(f"não existe triângulo com lados {medida(a)}, {medida(b)} e {medida(c)}")
    s = (a + b + c) / 2  # semiperímetro
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    lados = sorted((a, b, c))
    if math.isclose(a, b) and math.isclose(b, c):
        tipo = "equilátero"
    elif math.isclose(a, b) or math.isclose(b, c) or math.isclose(a, c):
        tipo = "isósceles"
    else:
        tipo = "escaleno"
    # Pitágoras com isclose(): comparar floats com == falharia por restos de arredondamento.
    if math.isclose(lados[0] ** 2 + lados[1] ** 2, lados[2] ** 2):
        tipo += ", retângulo"
    return Resultado("Triângulo", f"lados {medida(a)}, {medida(b)}, {medida(c)}", area=area, perimetro=a + b + c, observacao=tipo)


def circulo(raio: float) -> Resultado:
    """Área = pi vezes raio ao quadrado; perímetro (circunferência) = 2 vezes pi vezes raio."""
    return Resultado("Círculo", f"raio {medida(raio)}", area=math.pi * raio ** 2, perimetro=2 * math.pi * raio)


def trapezio(base_maior: float, base_menor: float, altura: float,
             lados: tuple[float, float] | None = None) -> Resultado:
    """Área = média das bases vezes altura. O perímetro só sai se os lados inclinados forem informados."""
    if base_menor >= base_maior:
        raise ValueError(f"a base menor ({medida(base_menor)}) precisa ser menor que a base maior ({medida(base_maior)})")
    area = (base_maior + base_menor) * altura / 2
    perimetro = base_maior + base_menor + lados[0] + lados[1] if lados else None
    observacao = "" if lados else "sem os lados inclinados não dá para calcular o perímetro"
    return Resultado("Trapézio", f"bases {medida(base_maior)} e {medida(base_menor)}, altura {medida(altura)}",
                     area=area, perimetro=perimetro, observacao=observacao)


def cubo(aresta: float) -> Resultado:
    """Volume = aresta ao cubo; superfície = seis quadrados."""
    return Resultado("Cubo", f"aresta {medida(aresta)}", area=6 * aresta ** 2, volume=aresta ** 3,
                     observacao="área = superfície total")


def esfera(raio: float) -> Resultado:
    """Volume = 4/3 pi r ao cubo; superfície = 4 pi r ao quadrado."""
    return Resultado("Esfera", f"raio {medida(raio)}", area=4 * math.pi * raio ** 2,
                     volume=4 / 3 * math.pi * raio ** 3, observacao="área = superfície total")


def cilindro(raio: float, altura: float) -> Resultado:
    """Volume = área da base vezes altura; superfície = duas tampas mais a lateral."""
    base = math.pi * raio ** 2
    return Resultado("Cilindro", f"raio {medida(raio)}, altura {medida(altura)}", area=2 * base + 2 * math.pi * raio * altura,
                     volume=base * altura, observacao="área = superfície total")


def formatar(valor: float | None) -> str:
    """Duas casas com vírgula, ou um traço quando a medida não se aplica."""
    if valor is None:
        return "-"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def imprimir(resultado: Resultado) -> None:
    """Relatório de uma figura só."""
    print(f"{resultado.forma} ({resultado.medidas})")
    print(f"  Área      : {formatar(resultado.area)}")
    print(f"  Perímetro : {formatar(resultado.perimetro)}")
    print(f"  Volume    : {formatar(resultado.volume)}")
    if resultado.observacao:
        print(f"  Observação: {resultado.observacao}")


def imprimir_tabela(resultados: list[Resultado]) -> None:
    """Todas as figuras em uma tabela só."""
    cabecalho = f"{'Forma':<11}{'Medidas':<34}{'Área':>12}{'Perímetro':>12}{'Volume':>12}  Observação"
    print(cabecalho)
    print("-" * (len(cabecalho) + 10))
    for r in resultados:
        print(f"{r.forma:<11}{r.medidas:<34}{formatar(r.area):>12}{formatar(r.perimetro):>12}"
              f"{formatar(r.volume):>12}  {r.observacao}")


def demo() -> int:
    """Demonstração sem teclado: todas as figuras com medidas de exemplo e um erro tratado."""
    print("=" * 72)
    print("CodeNomad Academy | Calculadora de geometria | demonstração")
    print("=" * 72)
    resultados = [
        quadrado(4), retangulo(6, 3.5), triangulo(3, 4, 5), triangulo(5, 5, 5),
        circulo(2), trapezio(10, 6, 4, (5, 5)), cubo(3), esfera(2), cilindro(2, 10),
    ]
    imprimir_tabela(resultados)
    print()
    print("Tentando um triângulo de lados 1, 2 e 3 (erro esperado e tratado):")
    try:
        triangulo(1, 2, 3)
    except ValueError as erro:
        print(f"  Erro: {erro}")
    return 0


def montar_parser() -> argparse.ArgumentParser:
    """Um subcomando por figura, cada um com as medidas que precisa."""
    parser = argparse.ArgumentParser(description="Calculadora de geometria plana e espacial (CodeNomad Academy).")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa sem pedir nada")
    sub = parser.add_subparsers(dest="forma", metavar="forma")
    # (nome do subcomando, ajuda, nomes das medidas posicionais)
    figuras: list[tuple[str, str, list[str]]] = [
        ("quadrado", "área e perímetro do quadrado", ["lado"]),
        ("retangulo", "área e perímetro do retângulo", ["base", "altura"]),
        ("triangulo", "área e perímetro do triângulo", ["a", "b", "c"]),
        ("circulo", "área e perímetro do círculo", ["raio"]),
        ("trapezio", "área (e perímetro com --lados) do trapézio", ["base_maior", "base_menor", "altura"]),
        ("cubo", "volume e superfície do cubo", ["aresta"]),
        ("esfera", "volume e superfície da esfera", ["raio"]),
        ("cilindro", "volume e superfície do cilindro", ["raio", "altura"]),
    ]
    for nome, ajuda, medidas in figuras:
        p = sub.add_parser(nome, help=ajuda)
        for nome_medida in medidas:
            p.add_argument(nome_medida, type=positivo)
        if nome == "trapezio":
            p.add_argument("--lados", type=positivo, nargs=2, metavar=("LADO1", "LADO2"),
                           help="os dois lados inclinados, para calcular o perímetro")
    return parser


def main() -> None:
    """Ponto de entrada: sem argumentos mostra o uso; --demo demonstra; senão calcula a figura."""
    parser = montar_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.demo:
        sys.exit(demo())
    if args.forma is None:
        parser.error("escolha uma forma (quadrado, retangulo, triangulo, circulo, trapezio, cubo, esfera, cilindro)")
    try:
        match args.forma:
            case "quadrado":
                resultado = quadrado(args.lado)
            case "retangulo":
                resultado = retangulo(args.base, args.altura)
            case "triangulo":
                resultado = triangulo(args.a, args.b, args.c)
            case "circulo":
                resultado = circulo(args.raio)
            case "trapezio":
                lados = tuple(args.lados) if args.lados else None
                resultado = trapezio(args.base_maior, args.base_menor, args.altura, lados)
            case "cubo":
                resultado = cubo(args.aresta)
            case "esfera":
                resultado = esfera(args.raio)
            case _:
                resultado = cilindro(args.raio, args.altura)
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(1)
    imprimir(resultado)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Acrescente o cone (volume = um terço do cilindro) e a pirâmide de base quadrada.
# 2. Aceite --unidade (cm, m) e mostre as áreas em cm² ou m² e os volumes em cm³ ou m³.
# 3. Calcule os três ângulos internos do triângulo com a lei dos cossenos (math.acos).
# ------------------------------------------------------------
