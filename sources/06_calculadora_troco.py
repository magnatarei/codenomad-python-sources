#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  06. Calculadora de troco
# ------------------------------------------------------------
# O que faz: recebe o valor da compra e o valor pago e devolve o troco
#            decomposto no menor número de cédulas e moedas (algoritmo
#            guloso, do maior valor para o menor). Avisa quando o pagamento
#            é insuficiente e aceita limitar a maior cédula disponível no caixa.
# Como usar: python 06_calculadora_troco.py --compra 37.45 --pago 50
#            python 06_calculadora_troco.py --compra 12,90 --pago 100 --maior-cedula 20
#            python 06_calculadora_troco.py --demo
# O que você aprende: por que dinheiro se calcula em centavos inteiros e não
#            em ponto flutuante, algoritmo guloso com divmod, exceções
#            próprias para erros de regra de negócio e plural nas mensagens.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import sys

# Cada denominação em centavos, do maior para o menor: a ordem importa para o
# algoritmo guloso. Trabalhar em centavos inteiros evita o clássico
# 0.1 + 0.2 != 0.3 do ponto flutuante.
DENOMINACOES: list[tuple[int, str]] = [
    (20000, "cédula"), (10000, "cédula"), (5000, "cédula"), (2000, "cédula"),
    (1000, "cédula"), (500, "cédula"), (200, "cédula"),
    (100, "moeda"), (50, "moeda"), (25, "moeda"), (10, "moeda"), (5, "moeda"), (1, "moeda"),
]


class PagamentoInsuficiente(ValueError):
    """Levantada quando o valor pago não cobre a compra."""


def numero(texto: str) -> float:
    """Converte texto em número, aceitando tanto '37.45' quanto '37,45'."""
    try:
        valor = float(texto.strip().replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' não é um valor válido") from None
    if valor < 0:
        raise argparse.ArgumentTypeError("o valor não pode ser negativo")
    return valor


def para_centavos(valor: float) -> int:
    """37.45 vira 3745. O round() corrige restos como 3744.9999999 do ponto flutuante."""
    return round(valor * 100)


def formatar_brl(centavos: int) -> str:
    """Formata 123456 centavos como 'R$ 1.234,56'."""
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def calcular_troco(compra: int, pago: int) -> int:
    """Troco em centavos. Levanta PagamentoInsuficiente quando falta dinheiro."""
    if pago < compra:
        falta = compra - pago
        raise PagamentoInsuficiente(f"pagamento insuficiente: faltam {formatar_brl(falta)}")
    return pago - compra


def decompor(troco: int, maior_cedula: int = 20000) -> list[tuple[int, int, str]]:
    """Decompõe o troco em (quantidade, valor em centavos, tipo), do maior para o menor.

    Com as denominações brasileiras o guloso sempre acha o menor número de
    peças, porque cada valor é múltiplo (ou combinação direta) dos menores.
    """
    pecas: list[tuple[int, int, str]] = []
    restante = troco
    for valor, tipo in DENOMINACOES:
        if valor > maior_cedula:
            continue  # o caixa não tem esta cédula: pula para a próxima
        quantidade, restante = divmod(restante, valor)
        if quantidade:
            pecas.append((quantidade, valor, tipo))
    return pecas


def descrever_peca(quantidade: int, valor: int, tipo: str) -> str:
    """'3 moedas de R$ 0,25' ou '1 cédula de R$ 50,00', com o plural certo."""
    nome = tipo if quantidade == 1 else tipo + "s"
    return f"{quantidade} {nome} de {formatar_brl(valor)}"


def imprimir_troco(compra: float, pago: float, maior_cedula: int = 20000) -> bool:
    """Imprime a compra, o pagamento e o troco decomposto. Devolve False se faltou dinheiro."""
    compra_c, pago_c = para_centavos(compra), para_centavos(pago)
    print(f"Compra: {formatar_brl(compra_c)} | Pago: {formatar_brl(pago_c)}")
    try:
        troco = calcular_troco(compra_c, pago_c)
    except PagamentoInsuficiente as erro:
        print(f"  Aviso: {erro}")
        return False
    if troco == 0:
        print("  Pagamento exato, não há troco.")
        return True
    pecas = decompor(troco, maior_cedula)
    total_pecas = sum(quantidade for quantidade, _, _ in pecas)
    print(f"  Troco: {formatar_brl(troco)} em {total_pecas} peça{'s' if total_pecas > 1 else ''}:")
    for quantidade, valor, tipo in pecas:
        print(f"    {descrever_peca(quantidade, valor, tipo)}")
    return True


def demo() -> int:
    """Demonstração sem teclado: quatro compras, uma com cédula limitada e um pagamento curto."""
    print("=" * 72)
    print("CodeNomad Academy | Calculadora de troco | demonstração")
    print("=" * 72)
    compras = [(37.45, 50.0), (12.90, 100.0), (199.99, 200.0), (85.0, 85.0)]
    for compra, pago in compras:
        imprimir_troco(compra, pago)
    print()
    print("O mesmo troco de R$ 87,10 quando o caixa só tem cédulas até R$ 20:")
    imprimir_troco(12.90, 100.0, maior_cedula=2000)
    print()
    print("E quando o cliente paga menos do que deve:")
    imprimir_troco(50.0, 20.0)
    return 0


def maior_cedula_valida(texto: str) -> int:
    """A maior cédula precisa ser uma das cédulas que existem."""
    centavos = para_centavos(numero(texto))
    cedulas = [valor for valor, tipo in DENOMINACOES if tipo == "cédula"]
    if centavos not in cedulas:
        opcoes = ", ".join(formatar_brl(c) for c in cedulas)
        raise argparse.ArgumentTypeError(f"'{texto}' não é uma cédula. Use uma destas: {opcoes}")
    return centavos


def montar_parser() -> argparse.ArgumentParser:
    """Define os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Calculadora de troco em cédulas e moedas (CodeNomad Academy).",
        epilog="Exemplo: --compra 37.45 --pago 50",
    )
    parser.add_argument("--compra", type=numero, help="valor da compra, em reais")
    parser.add_argument("--pago", type=numero, help="valor entregue pelo cliente, em reais")
    parser.add_argument("--maior-cedula", type=maior_cedula_valida, default=20000,
                        help="maior cédula disponível no caixa (padrão 200)")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa sem pedir nada")
    return parser


def main() -> None:
    """Ponto de entrada: sem argumentos mostra o uso; com --demo demonstra; senão calcula."""
    parser = montar_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.demo:
        sys.exit(demo())
    if args.compra is None or args.pago is None:
        parser.error("informe --compra e --pago (ou use --demo)")
    deu_certo = imprimir_troco(args.compra, args.pago, args.maior_cedula)
    sys.exit(0 if deu_certo else 1)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Permita informar o pagamento em várias cédulas (--pago 50 --pago 20) e some tudo.
# 2. Acrescente --sem-moeda-de-1 e arredonde o troco para múltiplos de 5 centavos.
# 3. Troque a tabela por outra moeda (dólar, euro) e veja se o guloso continua ótimo.
# ------------------------------------------------------------
