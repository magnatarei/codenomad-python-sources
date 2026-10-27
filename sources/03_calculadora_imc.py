#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  03. Calculadora de IMC
# ------------------------------------------------------------
# O que faz: recebe peso e altura, valida os dois, e devolve o IMC, a
#            classificação oficial (abaixo do peso, normal, sobrepeso,
#            obesidade graus I, II e III) e a faixa de peso considerada
#            saudável para aquela altura, com quanto falta para entrar nela.
# Como usar: python 03_calculadora_imc.py --peso 82 --altura 1.78 --nome "Marcos"
#            python 03_calculadora_imc.py --peso 60,5 --altura 165
#            python 03_calculadora_imc.py --demo
# O que você aprende: validação de faixas, tabela de classificação em lista
#            de tuplas percorrida em ordem, dataclasses com valores derivados,
#            arredondamento e impressão de tabela com colunas alinhadas.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import sys
from dataclasses import dataclass

# Limites superiores de cada faixa, em ordem crescente. A primeira faixa cujo
# limite é maior que o IMC é a classificação. O infinito fecha a lista.
FAIXAS: list[tuple[float, str]] = [
    (18.5, "Abaixo do peso"),
    (25.0, "Peso normal"),
    (30.0, "Sobrepeso"),
    (35.0, "Obesidade grau I"),
    (40.0, "Obesidade grau II"),
    (float("inf"), "Obesidade grau III"),
]
IMC_MINIMO_SAUDAVEL = 18.5
IMC_MAXIMO_SAUDAVEL = 24.9


@dataclass(frozen=True)
class Pessoa:
    """Os dados de entrada: nome, peso em quilos e altura em metros."""

    nome: str
    peso: float
    altura: float


@dataclass(frozen=True)
class Avaliacao:
    """O resultado: IMC, classificação, faixa saudável e o ajuste de peso."""

    imc: float
    classificacao: str
    peso_minimo: float
    peso_maximo: float
    ajuste: float  # negativo = precisa perder, positivo = precisa ganhar, zero = dentro da faixa


def numero(texto: str) -> float:
    """Converte texto em número, aceitando tanto '1.78' quanto '1,78'."""
    try:
        return float(texto.strip().replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um número válido") from None


def peso_valido(texto: str) -> float:
    """Peso em quilos, entre 2 e 500."""
    peso = numero(texto)
    if not 2 <= peso <= 500:
        raise argparse.ArgumentTypeError(f"peso {texto} fora da faixa aceita (2 a 500 kg)")
    return peso


def altura_valida(texto: str) -> float:
    """Altura em metros entre 0,5 e 2,8. Se vier acima de 3, entendemos centímetros."""
    altura = numero(texto)
    if altura > 3:
        altura /= 100  # 175 vira 1,75: facilita a vida de quem pensa em centímetros
    if not 0.5 <= altura <= 2.8:
        raise argparse.ArgumentTypeError(f"altura {texto} fora da faixa aceita (0,50 a 2,80 m)")
    return altura


def calcular_imc(peso: float, altura: float) -> float:
    """IMC = peso dividido pela altura ao quadrado."""
    return peso / (altura ** 2)


def classificar(imc: float) -> str:
    """Percorre as faixas em ordem e devolve a primeira em que o IMC cabe."""
    for limite, nome in FAIXAS:
        if imc < limite:
            return nome
    return FAIXAS[-1][1]  # nunca chega aqui por causa do infinito, mas deixa a função completa


def faixa_saudavel(altura: float) -> tuple[float, float]:
    """Pesos que dão IMC 18,5 e 24,9 para esta altura: é só inverter a fórmula."""
    return IMC_MINIMO_SAUDAVEL * altura ** 2, IMC_MAXIMO_SAUDAVEL * altura ** 2


def avaliar(pessoa: Pessoa) -> Avaliacao:
    """Junta todas as contas em um único resultado."""
    imc = calcular_imc(pessoa.peso, pessoa.altura)
    minimo, maximo = faixa_saudavel(pessoa.altura)
    if pessoa.peso < minimo:
        ajuste = minimo - pessoa.peso
    elif pessoa.peso > maximo:
        ajuste = maximo - pessoa.peso
    else:
        ajuste = 0.0
    return Avaliacao(imc, classificar(imc), minimo, maximo, ajuste)


def descrever_ajuste(ajuste: float) -> str:
    """Transforma o ajuste numérico em uma frase."""
    if abs(ajuste) < 0.05:
        return "dentro da faixa saudável"
    if ajuste < 0:
        return f"perder {abs(ajuste):.1f} kg para entrar na faixa"
    return f"ganhar {ajuste:.1f} kg para entrar na faixa"


def imprimir_detalhado(pessoa: Pessoa, avaliacao: Avaliacao) -> None:
    """Relatório de uma pessoa só, linha a linha."""
    print(f"Nome          : {pessoa.nome}")
    print(f"Peso          : {pessoa.peso:.1f} kg")
    print(f"Altura        : {pessoa.altura:.2f} m")
    print(f"IMC           : {avaliacao.imc:.1f}")
    print(f"Classificação : {avaliacao.classificacao}")
    print(f"Faixa saudável: {avaliacao.peso_minimo:.1f} kg a {avaliacao.peso_maximo:.1f} kg")
    print(f"Ajuste        : {descrever_ajuste(avaliacao.ajuste)}")


def imprimir_tabela(pessoas: list[Pessoa]) -> None:
    """Uma linha por pessoa, com as colunas alinhadas."""
    cabecalho = f"{'Nome':<10}{'Peso':>8}{'Altura':>8}{'IMC':>7}  {'Classificação':<20}{'Faixa saudável':<20}Ajuste"
    print(cabecalho)
    print("-" * (len(cabecalho) + 30))
    for pessoa in pessoas:
        a = avaliar(pessoa)
        faixa = f"{a.peso_minimo:.1f} a {a.peso_maximo:.1f} kg"
        print(
            f"{pessoa.nome:<10}{pessoa.peso:>6.1f}kg{pessoa.altura:>7.2f}m{a.imc:>7.1f}  "
            f"{a.classificacao:<20}{faixa:<20}{descrever_ajuste(a.ajuste)}"
        )


def imprimir_faixas() -> None:
    """Mostra a tabela de referência usada na classificação."""
    print("Faixas de classificação (IMC):")
    inferior = 0.0
    for limite, nome in FAIXAS:
        topo = "em diante" if limite == float("inf") else f"até {limite:.1f}".replace(".", ",")
        print(f"  {inferior:>5.1f} {topo:<10} {nome}".replace(".", ","))
        inferior = limite


def demo() -> int:
    """Demonstração sem teclado: três pessoas com perfis diferentes."""
    print("=" * 72)
    print("CodeNomad Academy | Calculadora de IMC | demonstração")
    print("=" * 72)
    pessoas = [
        Pessoa("Ana", 52.0, 1.70),
        Pessoa("Bruno", 84.5, 1.78),
        Pessoa("Carla", 98.0, 1.62),
    ]
    imprimir_tabela(pessoas)
    print()
    imprimir_faixas()
    print()
    print("Detalhe da primeira pessoa:")
    imprimir_detalhado(pessoas[0], avaliar(pessoas[0]))
    return 0


def montar_parser() -> argparse.ArgumentParser:
    """Define os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Calculadora de IMC com classificação e faixa de peso saudável (CodeNomad Academy).",
        epilog="Exemplo: --peso 82 --altura 1.78 --nome Marcos",
    )
    parser.add_argument("--peso", type=peso_valido, help="peso em quilos (2 a 500)")
    parser.add_argument("--altura", type=altura_valida, help="altura em metros (1.78) ou centímetros (178)")
    parser.add_argument("--nome", default="Você", help="nome para aparecer no relatório (opcional)")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa sem pedir nada")
    return parser


def main() -> None:
    """Ponto de entrada: sem argumentos mostra o uso; com --demo demonstra; senão avalia."""
    parser = montar_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.demo:
        sys.exit(demo())
    if args.peso is None or args.altura is None:
        parser.error("informe --peso e --altura (ou use --demo)")
    pessoa = Pessoa(args.nome, args.peso, args.altura)
    imprimir_detalhado(pessoa, avaliar(pessoa))


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Leia várias pessoas de um arquivo CSV (nome;peso;altura) e imprima a tabela.
# 2. Acrescente --idade e --sexo e mostre um aviso de que o IMC não se aplica
#    do mesmo jeito a crianças, idosos e atletas.
# 3. Calcule também a taxa metabólica basal com a equação de Mifflin-St Jeor.
# ------------------------------------------------------------
