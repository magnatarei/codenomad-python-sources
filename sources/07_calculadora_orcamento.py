#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  07. Calculadora de orçamento mensal
# ------------------------------------------------------------
# O que faz: recebe receitas e despesas por categoria, pelos argumentos ou
#            por um arquivo de texto simples (uma linha por lançamento no
#            formato tipo;categoria;valor). Mostra o total de cada lado, o
#            saldo do mês, o percentual de cada categoria sobre a receita com
#            barras de texto, e um alerta para a categoria que mais pesa.
# Como usar: python 07_calculadora_orcamento.py --receita "Salário=4500" --despesa "Aluguel=1500" --despesa "Mercado=900"
#            python 07_calculadora_orcamento.py --arquivo meu_orcamento.txt
#            python 07_calculadora_orcamento.py --demo
# O que você aprende: argparse com action="append", leitura de arquivo com
#            pathlib e tratamento de linha inválida, agrupamento com
#            dicionário, ordenação por valor, barras de texto e arquivos
#            temporários com o módulo tempfile.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

TIPOS = ("receita", "despesa")
LARGURA_BARRA = 40  # quantos símbolos tem uma barra de 100%
LIMITE_ALERTA = 30.0  # uma despesa acima deste percentual da receita merece atenção

EXEMPLO = """\
# Orçamento de exemplo (linhas com # são ignoradas)
receita;Salário;4500
receita;Trabalho extra;500
despesa;Aluguel;1500
despesa;Mercado;900
despesa;Transporte;350
despesa;Internet e celular;180
despesa;Lazer;400
despesa;Curso de programação;120
despesa;Saúde;250
despesa;Outros;250
"""


@dataclass(frozen=True)
class Lancamento:
    """Uma entrada do orçamento: receita ou despesa, categoria e valor."""

    tipo: str
    categoria: str
    valor: float


def numero(texto: str) -> float:
    """Converte '1.500,00', '1500,00' ou '1500.00' em float. Levanta ValueError se não der."""
    limpo = texto.strip().replace("R$", "").replace(" ", "")
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")  # formato brasileiro: ponto de milhar e vírgula
    valor = float(limpo)  # aqui o ValueError do Python já tem a mensagem certa para o chamador tratar
    if valor < 0:
        raise ValueError(f"valor negativo: {texto}")
    return valor


def analisar_item(texto: str, tipo: str) -> Lancamento:
    """Transforma 'Aluguel=1500' em um Lancamento do tipo pedido."""
    if "=" not in texto:
        raise ValueError(f"'{texto}' não está no formato Categoria=valor")
    categoria, valor_texto = texto.split("=", 1)
    categoria = categoria.strip()
    if not categoria:
        raise ValueError(f"'{texto}' está sem o nome da categoria")
    try:
        return Lancamento(tipo, categoria, numero(valor_texto))
    except ValueError as erro:
        raise ValueError(f"'{texto}': {erro}") from None


def ler_arquivo(caminho: Path) -> list[Lancamento]:
    """Lê linhas 'tipo;categoria;valor'. Linhas vazias e comentários com # são ignorados."""
    if not caminho.is_file():
        raise ValueError(f"arquivo não encontrado: {caminho}")
    lancamentos: list[Lancamento] = []
    for n, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), start=1):
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        partes = [parte.strip() for parte in linha.split(";")]
        if len(partes) != 3:
            raise ValueError(f"linha {n}: esperava tipo;categoria;valor, veio '{linha}'")
        tipo, categoria, valor_texto = partes
        if tipo.lower() not in TIPOS:
            raise ValueError(f"linha {n}: tipo '{tipo}' desconhecido (use receita ou despesa)")
        try:
            lancamentos.append(Lancamento(tipo.lower(), categoria, numero(valor_texto)))
        except ValueError as erro:
            raise ValueError(f"linha {n}: {erro}") from None
    return lancamentos


def somar_por_categoria(lancamentos: list[Lancamento], tipo: str) -> dict[str, float]:
    """Agrupa os valores de um tipo por categoria, do maior para o menor."""
    totais: dict[str, float] = {}
    for item in lancamentos:
        if item.tipo == tipo:
            totais[item.categoria] = totais.get(item.categoria, 0.0) + item.valor
    return dict(sorted(totais.items(), key=lambda par: par[1], reverse=True))


def formatar_brl(valor: float) -> str:
    """Formata 1234.5 como 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_pct(valor: float) -> str:
    """Formata 30.0 como '30,0%'."""
    return f"{valor:.1f}%".replace(".", ",")


def barra(percentual: float) -> str:
    """Barra de texto proporcional ao percentual (100% = LARGURA_BARRA símbolos)."""
    cheios = min(LARGURA_BARRA, round(percentual / 100 * LARGURA_BARRA))
    return "#" * cheios


def imprimir_bloco(titulo: str, totais: dict[str, float], receita_total: float) -> None:
    """Imprime as categorias de um tipo com valor, percentual sobre a receita e barra."""
    print(titulo)
    if not totais:
        print("  (nenhum lançamento)")
    for categoria, valor in totais.items():
        percentual = valor / receita_total * 100 if receita_total else 0.0
        print(f"  {categoria:<24}{formatar_brl(valor):>15}  {formatar_pct(percentual):>6}  {barra(percentual)}")


def relatorio(lancamentos: list[Lancamento]) -> None:
    """Monta o relatório completo: blocos, totais, saldo e alertas."""
    receitas = somar_por_categoria(lancamentos, "receita")
    despesas = somar_por_categoria(lancamentos, "despesa")
    receita_total = sum(receitas.values())
    despesa_total = sum(despesas.values())
    saldo = receita_total - despesa_total

    imprimir_bloco("Receitas (percentual sobre a receita total)", receitas, receita_total)
    print(f"  {'Total de receitas':<24}{formatar_brl(receita_total):>15}\n")
    imprimir_bloco("Despesas (percentual sobre a receita total)", despesas, receita_total)
    comprometido = despesa_total / receita_total * 100 if receita_total else 0.0
    print(f"  {'Total de despesas':<24}{formatar_brl(despesa_total):>15}  {formatar_pct(comprometido):>6} da receita")
    print()
    print(f"Saldo do mês: {formatar_brl(saldo)}")
    if not receita_total:
        print("Alerta: nenhuma receita informada; os percentuais ficaram em zero.")
    if saldo < 0:
        print(f"Alerta: as despesas passam da receita em {formatar_brl(-saldo)}.")
    if despesas:
        maior, valor = next(iter(despesas.items()))  # o dicionário já vem ordenado do maior para o menor
        peso = valor / receita_total * 100 if receita_total else 0.0
        aviso = " Vale rever." if peso > LIMITE_ALERTA else ""
        print(f"Alerta: a categoria que mais pesa é '{maior}', com {formatar_pct(peso)} da receita.{aviso}")


def demo() -> int:
    """Demonstração sem teclado: grava o exemplo na pasta temporária, lê de volta e relata."""
    print("=" * 72)
    print("CodeNomad Academy | Calculadora de orçamento mensal | demonstração")
    print("=" * 72)
    arquivo = Path(tempfile.gettempdir()) / "codenomad_orcamento_exemplo.txt"
    arquivo.write_text(EXEMPLO, encoding="utf-8")
    print(f"Arquivo de exemplo gravado em: {arquivo}\n")
    try:
        relatorio(ler_arquivo(arquivo))
    finally:
        arquivo.unlink(missing_ok=True)  # limpa o que criamos, aconteça o que acontecer
    return 0


def montar_parser() -> argparse.ArgumentParser:
    """Define os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Calculadora de orçamento mensal por categoria (CodeNomad Academy).",
        epilog='Exemplo: --receita "Salário=4500" --despesa "Aluguel=1500" --despesa "Mercado=900"',
    )
    parser.add_argument("--receita", action="append", default=[], metavar="CATEGORIA=VALOR",
                        help="uma receita; repita a opção para cada categoria")
    parser.add_argument("--despesa", action="append", default=[], metavar="CATEGORIA=VALOR",
                        help="uma despesa; repita a opção para cada categoria")
    parser.add_argument("--arquivo", type=Path, help="arquivo com linhas tipo;categoria;valor")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa sem pedir nada")
    return parser


def main() -> None:
    """Ponto de entrada: sem argumentos mostra o uso; com --demo demonstra; senão relata."""
    parser = montar_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()
    if args.demo:
        sys.exit(demo())
    try:
        lancamentos = [analisar_item(texto, "receita") for texto in args.receita]
        lancamentos += [analisar_item(texto, "despesa") for texto in args.despesa]
        if args.arquivo:
            lancamentos += ler_arquivo(args.arquivo)
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(1)
    if not lancamentos:
        parser.error("informe ao menos uma --receita, --despesa ou --arquivo (ou use --demo)")
    relatorio(lancamentos)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Aplique a regra 50/30/20 (essencial, lazer, poupança) marcando cada categoria.
# 2. Compare dois meses lidos de dois arquivos e mostre o que subiu e o que caiu.
# 3. Exporte o relatório em CSV com o módulo csv para abrir em uma planilha.
# ------------------------------------------------------------
