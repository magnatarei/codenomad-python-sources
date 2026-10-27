#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  11. Validador de CPF e CNPJ
# ------------------------------------------------------------
# O que faz: Valida os dígitos verificadores de CPF e CNPJ, aceitando o
#            número com ou sem pontuação. Rejeita sequências repetidas
#            (111.111.111-11), formata o número e gera números válidos
#            para usar em testes de software.
# Como usar: python 11_validador_cpf_cnpj.py 529.982.247-25 11222333000181
#            python 11_validador_cpf_cnpj.py --gerar cnpj --quantidade 3
#            python 11_validador_cpf_cnpj.py --demo
# O que você aprende: aritmética modular (módulo 11), fatiamento de strings,
#            zip com strict=True, dataclasses, random com semente, argparse
#            e a diferença entre validar o formato e validar o conteúdo.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import random
import sys
from dataclasses import dataclass

# Pesos da regra do módulo 11. O CPF usa pesos decrescentes a partir de 10
# (primeiro verificador) e de 11 (segundo). O CNPJ usa uma sequência que
# reinicia em 9 no meio do número.
PESOS_CPF_1 = list(range(10, 1, -1))
PESOS_CPF_2 = list(range(11, 1, -1))
PESOS_CNPJ_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
PESOS_CNPJ_2 = [6] + PESOS_CNPJ_1


@dataclass(frozen=True)
class Resultado:
    """O que foi lido, o tipo identificado e o veredito da validação."""

    entrada: str
    tipo: str
    valido: bool
    motivo: str
    formatado: str


def somente_digitos(texto: str) -> str:
    """Remove tudo o que não for dígito: pontos, traços, barra e espaços."""
    return "".join(c for c in texto if c.isdigit())


def calcular_digito(digitos: str, pesos: list[int]) -> int:
    """Aplica a regra do módulo 11 usada por CPF e CNPJ.

    Cada dígito é multiplicado pelo peso da sua posição. O resto da soma
    dividida por 11 define o verificador: resto menor que 2 vira 0,
    qualquer outro vira 11 menos o resto.
    """
    # strict=True faz o zip reclamar se digitos e pesos tiverem tamanhos
    # diferentes, em vez de truncar em silêncio.
    soma = sum(int(d) * p for d, p in zip(digitos, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def validar_cpf(cpf: str) -> tuple[bool, str]:
    """Devolve (válido, motivo) para um CPF com ou sem pontuação."""
    d = somente_digitos(cpf)
    if len(d) != 11:
        return False, f"CPF precisa ter 11 dígitos, este tem {len(d)}"
    # 111.111.111-11 passa na conta do módulo 11, por isso a regra extra.
    if d == d[0] * 11:
        return False, "sequência de dígitos repetidos não é aceita"
    dv1 = calcular_digito(d[:9], PESOS_CPF_1)
    dv2 = calcular_digito(d[:9] + str(dv1), PESOS_CPF_2)
    if d[9:] != f"{dv1}{dv2}":
        return False, f"dígitos verificadores deveriam ser {dv1}{dv2}"
    return True, "dígitos verificadores conferem"


def validar_cnpj(cnpj: str) -> tuple[bool, str]:
    """Devolve (válido, motivo) para um CNPJ com ou sem pontuação."""
    d = somente_digitos(cnpj)
    if len(d) != 14:
        return False, f"CNPJ precisa ter 14 dígitos, este tem {len(d)}"
    if d == d[0] * 14:
        return False, "sequência de dígitos repetidos não é aceita"
    dv1 = calcular_digito(d[:12], PESOS_CNPJ_1)
    dv2 = calcular_digito(d[:12] + str(dv1), PESOS_CNPJ_2)
    if d[12:] != f"{dv1}{dv2}":
        return False, f"dígitos verificadores deveriam ser {dv1}{dv2}"
    return True, "dígitos verificadores conferem"


def formatar_cpf(cpf: str) -> str:
    """Escreve 11 dígitos no formato 000.000.000-00."""
    d = somente_digitos(cpf)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def formatar_cnpj(cnpj: str) -> str:
    """Escreve 14 dígitos no formato 00.000.000/0000-00."""
    d = somente_digitos(cnpj)
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def gerar_cpf(rng: random.Random) -> str:
    """Sorteia 9 dígitos e calcula os dois verificadores. Só para testes."""
    while True:
        base = "".join(str(rng.randint(0, 9)) for _ in range(9))
        if base != base[0] * 9:
            break
    dv1 = calcular_digito(base, PESOS_CPF_1)
    dv2 = calcular_digito(base + str(dv1), PESOS_CPF_2)
    return formatar_cpf(f"{base}{dv1}{dv2}")


def gerar_cnpj(rng: random.Random) -> str:
    """Sorteia a raiz de 8 dígitos, usa a filial 0001 e calcula os verificadores."""
    raiz = "".join(str(rng.randint(0, 9)) for _ in range(8))
    base = raiz + "0001"
    dv1 = calcular_digito(base, PESOS_CNPJ_1)
    dv2 = calcular_digito(base + str(dv1), PESOS_CNPJ_2)
    return formatar_cnpj(f"{base}{dv1}{dv2}")


def analisar(entrada: str) -> Resultado:
    """Descobre pelo tamanho se é CPF ou CNPJ e valida."""
    d = somente_digitos(entrada)
    if len(d) == 11:
        valido, motivo = validar_cpf(d)
        return Resultado(entrada, "CPF", valido, motivo, formatar_cpf(d))
    if len(d) == 14:
        valido, motivo = validar_cnpj(d)
        return Resultado(entrada, "CNPJ", valido, motivo, formatar_cnpj(d))
    motivo = f"tamanho inválido: {len(d)} dígitos (CPF tem 11, CNPJ tem 14)"
    return Resultado(entrada, "?", False, motivo, d or "(vazio)")


def imprimir_resultado(r: Resultado) -> None:
    """Mostra uma linha por número, com veredito e motivo."""
    marca = "[OK] " if r.valido else "[X]  "
    print(f"{marca}{r.tipo:<5} {r.formatado:<20} {r.motivo}")


def demo() -> None:
    """Valida uma lista de casos conhecidos e gera números de teste."""
    print("=" * 64)
    print("Validador de CPF e CNPJ: demonstração")
    print("=" * 64)
    casos = [
        "529.982.247-25",      # CPF válido, com pontuação
        "52998224725",         # o mesmo CPF, sem pontuação
        "111.111.111-11",      # sequência repetida
        "123.456.789-00",      # verificadores errados
        "11.222.333/0001-81",  # CNPJ válido
        "11222333000181",      # o mesmo CNPJ, sem pontuação
        "00.000.000/0000-00",  # sequência repetida
        "11.222.333/0001-80",  # verificadores errados
        "1234",                # tamanho errado
    ]
    print(f"\n{len(casos)} casos de entrada:\n")
    for caso in casos:
        imprimir_resultado(analisar(caso))

    # A semente fixa faz o sorteio repetir, o que é ótimo para testes.
    rng = random.Random(2024)
    print("\nNúmeros válidos para teste (semente 2024):\n")
    for gerado in (gerar_cpf(rng), gerar_cnpj(rng)):
        imprimir_resultado(analisar(gerado))
    print("\nAtenção: números de teste são sorteados e não pertencem a ninguém.")


def construir_parser() -> argparse.ArgumentParser:
    """Define a linha de comando do programa."""
    parser = argparse.ArgumentParser(
        description="Valida, formata e gera CPF e CNPJ (confere os dígitos verificadores).",
        epilog="Exemplo: python 11_validador_cpf_cnpj.py 529.982.247-25 --gerar cnpj",
    )
    parser.add_argument("numeros", nargs="*", metavar="NÚMERO",
                        help="CPF ou CNPJ, com ou sem pontuação")
    parser.add_argument("--gerar", choices=["cpf", "cnpj"],
                        help="gera números válidos para teste")
    parser.add_argument("--quantidade", type=int, default=1,
                        help="quantos números gerar (padrão: 1)")
    parser.add_argument("--semente", type=int,
                        help="semente do sorteio, para repetir o resultado")
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: devolve 0 quando tudo é válido e 1 se algo falha."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    if not args.numeros and not args.gerar:
        parser.print_help()
        return 0
    if args.quantidade < 1:
        parser.error("--quantidade precisa ser pelo menos 1")

    houve_invalido = False
    for numero in args.numeros:
        resultado = analisar(numero)
        imprimir_resultado(resultado)
        houve_invalido = houve_invalido or not resultado.valido

    if args.gerar:
        rng = random.Random(args.semente)
        gerador = gerar_cpf if args.gerar == "cpf" else gerar_cnpj
        for _ in range(args.quantidade):
            print(gerador(rng))
    return 1 if houve_invalido else 0


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Aceite um arquivo com um número por linha e imprima um resumo
#      com a contagem de válidos e inválidos.
#   2. Adicione a validação de PIS/PASEP, que também usa módulo 11,
#      mas com os pesos 3, 2, 9, 8, 7, 6, 5, 4, 3, 2.
#   3. Escreva testes com unittest cobrindo cada motivo de rejeição.
# ------------------------------------------------------------
