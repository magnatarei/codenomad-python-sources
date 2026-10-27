#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  36. Relatório de vendas a partir de CSV
# ------------------------------------------------------------
# O que faz: Lê um CSV de vendas com as colunas data, produto, categoria,
#            quantidade e valor (preço unitário) e imprime um relatório
#            alinhado: total geral, totais por categoria e por mês com barras,
#            ticket médio e mediana, produto mais vendido e o de maior receita.
#            Aponta a linha exata de qualquer dado inválido.
# Como usar: python 36_relatorio_csv.py vendas.csv
#            python 36_relatorio_csv.py --gerar-exemplo vendas.csv
#            python 36_relatorio_csv.py --demo
# O que você aprende: csv.DictReader, dataclasses imutáveis com property,
#            defaultdict e Counter para agrupar, statistics (mean, median),
#            datetime.strptime, random com semente e formatação de f-strings
#            com alinhamento e largura.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import csv
import random
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable

COLUNAS = ["data", "produto", "categoria", "quantidade", "valor"]


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário; a mensagem é mostrada sem traceback."""


@dataclass(frozen=True)
class Venda:
    """Uma linha do CSV já convertida: data de verdade, inteiro e float."""

    data: date
    produto: str
    categoria: str
    quantidade: int
    valor: float  # preço unitário

    @property
    def receita(self) -> float:
        """Quanto a venda rendeu: quantidade vezes preço unitário."""
        return self.quantidade * self.valor


def interpretar(linha: dict[str, str], numero: int) -> Venda:
    """Converte os textos de uma linha; qualquer problema vira ErroDeUso com o número da linha."""
    try:
        data = datetime.strptime(linha["data"].strip(), "%Y-%m-%d").date()
        quantidade = int(linha["quantidade"])
        valor = float(linha["valor"].replace(",", "."))
    except (ValueError, TypeError) as erro:
        raise ErroDeUso(f"linha {numero}: dado inválido ({erro})") from erro
    if quantidade <= 0 or valor < 0:
        raise ErroDeUso(f"linha {numero}: quantidade precisa ser positiva e valor não pode ser negativo")
    produto, categoria = linha["produto"].strip(), linha["categoria"].strip()
    if not produto or not categoria:
        raise ErroDeUso(f"linha {numero}: produto e categoria não podem ficar vazios")
    return Venda(data, produto, categoria, quantidade, valor)


def ler_vendas(caminho: Path) -> list[Venda]:
    """Lê o CSV inteiro para uma lista de Venda, validando o cabeçalho antes."""
    if not caminho.is_file():
        raise ErroDeUso(f"arquivo não encontrado: {caminho}")
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        faltando = [c for c in COLUNAS if c not in (leitor.fieldnames or [])]
        if faltando:
            raise ErroDeUso(f"colunas ausentes no CSV: {', '.join(faltando)}")
        # start=2 porque a linha 1 é o cabeçalho; assim o número bate com o editor.
        vendas = [interpretar(linha, numero) for numero, linha in enumerate(leitor, start=2)]
    if not vendas:
        raise ErroDeUso("o CSV não tem nenhuma venda")
    return vendas


def totais_por(vendas: list[Venda], chave: Callable[[Venda], str]) -> list[tuple[str, float]]:
    """Soma a receita por qualquer critério (categoria, mês...) e ordena do maior para o menor."""
    somas: dict[str, float] = defaultdict(float)
    for venda in vendas:
        somas[chave(venda)] += venda.receita
    return sorted(somas.items(), key=lambda par: par[1], reverse=True)


def dinheiro(valor: float) -> str:
    """1234.5 vira "R$ 1.234,50": formata no padrão americano e troca os separadores."""
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def barra(valor: float, maximo: float, largura: int = 24) -> str:
    """Barra proporcional ao maior valor, para comparar de relance."""
    cheios = round(valor / maximo * largura) if maximo else 0
    return "#" * cheios + "." * (largura - cheios)


def secao(titulo: str, pares: list[tuple[str, float]]) -> list[str]:
    """Bloco alinhado: nome, barra e valor, com largura calculada pelos dados."""
    maior = max(v for _, v in pares)
    largura_nome = max(len(nome) for nome, _ in pares)
    linhas = ["", titulo, "-" * len(titulo)]
    for nome, valor in pares:
        linhas.append(f"{nome:<{largura_nome}}  {barra(valor, maior)}  {dinheiro(valor):>14}")
    return linhas


def montar_relatorio(vendas: list[Venda]) -> list[str]:
    """Junta todas as métricas num texto pronto para imprimir."""
    receitas = [v.receita for v in vendas]
    por_produto = Counter()
    for v in vendas:
        por_produto[v.produto] += v.quantidade
    mais_vendido, unidades = por_produto.most_common(1)[0]
    campeao, receita_campeao = totais_por(vendas, lambda v: v.produto)[0]
    primeira, ultima = min(v.data for v in vendas), max(v.data for v in vendas)
    linhas = [
        "RELATÓRIO DE VENDAS",
        "===================",
        f"Período: {primeira:%d/%m/%Y} a {ultima:%d/%m/%Y}",
        f"Vendas registradas: {len(vendas)}",
        f"Itens vendidos: {sum(v.quantidade for v in vendas)}",
        f"Receita total: {dinheiro(sum(receitas))}",
        f"Ticket médio: {dinheiro(statistics.mean(receitas))} (mediana {dinheiro(statistics.median(receitas))})",
        f"Produto mais vendido: {mais_vendido} ({unidades} unidades)",
        f"Maior receita: {campeao} ({dinheiro(receita_campeao)})",
    ]
    linhas += secao("Receita por categoria", totais_por(vendas, lambda v: v.categoria))
    # Ordenar por mês (e não por valor) conta a história na ordem do calendário.
    por_mes = sorted(totais_por(vendas, lambda v: f"{v.data:%Y-%m}"))
    linhas += secao("Receita por mês", por_mes)
    return linhas


PRODUTOS = [  # (produto, categoria, preço unitário) de uma loja fictícia
    ("Caderno pautado", "papelaria", 18.90), ("Caneta gel", "papelaria", 4.50),
    ("Mochila escolar", "acessórios", 149.00), ("Estojo", "acessórios", 32.00),
    ("Livro de lógica", "livros", 59.90), ("Livro de Python", "livros", 89.00),
    ("Fone de ouvido", "eletrônicos", 120.00), ("Mouse sem fio", "eletrônicos", 75.50),
]


def gerar_csv_exemplo(caminho: Path, quantidade: int = 60, semente: int = 7) -> None:
    """Grava um CSV fictício. A semente fixa faz o mesmo arquivo sair toda vez."""
    sorteio = random.Random(semente)
    inicio = date(2026, 7, 1)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(COLUNAS)
        for _ in range(quantidade):
            produto, categoria, preco = sorteio.choice(PRODUTOS)
            dia = inicio + timedelta(days=sorteio.randint(0, 91))
            escritor.writerow([dia.isoformat(), produto, categoria, sorteio.randint(1, 5), f"{preco:.2f}"])


def demo() -> None:
    """Gera 60 vendas num CSV temporário, imprime o relatório e mostra um erro apontado por linha."""
    print("=== Demonstração: relatório de vendas a partir de CSV ===")
    with tempfile.TemporaryDirectory() as temporaria:
        caminho = Path(temporaria) / "vendas.csv"
        gerar_csv_exemplo(caminho)
        texto = caminho.read_text(encoding="utf-8").splitlines()
        print(f"CSV gerado com {len(texto) - 1} vendas. Primeiras linhas:")
        print("\n".join("  " + linha for linha in texto[:4]))
        print("\n$ python 36_relatorio_csv.py vendas.csv")
        print("\n".join(montar_relatorio(ler_vendas(caminho))))
        quebrado = Path(temporaria) / "quebrado.csv"
        quebrado.write_text("\n".join(texto[:3] + ["2026-08-15,Estojo,acessórios,dois,32.00"]) + "\n", encoding="utf-8")
        print("\n$ python 36_relatorio_csv.py quebrado.csv   (quantidade escrita por extenso)")
        try:
            ler_vendas(quebrado)
        except ErroDeUso as erro:
            print(f"Erro: {erro}")


def main() -> None:
    """Ponto de entrada: --demo demonstra; --gerar-exemplo grava o CSV; senão relata."""
    parser = argparse.ArgumentParser(description="Relatório de vendas a partir de um CSV.")
    parser.add_argument("arquivo", nargs="?", help="CSV com data, produto, categoria, quantidade, valor")
    parser.add_argument("--gerar-exemplo", metavar="CAMINHO", help="grava um CSV fictício com 60 vendas e sai")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    args = parser.parse_args()
    if args.demo:
        demo()
        return
    try:
        if args.gerar_exemplo:
            gerar_csv_exemplo(Path(args.gerar_exemplo))
            print(f"CSV de exemplo gravado em {args.gerar_exemplo}")
            return
        if args.arquivo is None:
            parser.print_help()
            sys.exit(1)
        print("\n".join(montar_relatorio(ler_vendas(Path(args.arquivo)))))
    except ErroDeUso as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Adicione --inicio e --fim para filtrar o período antes de calcular,
#    e mostre a variação percentual de um mês para o outro.
# 2. Exporte o relatório em CSV ou JSON com --formato, reaproveitando as
#    mesmas funções de cálculo.
# 3. Descubra o dia da semana que mais vende (date.weekday) e o horário,
#    acrescentando uma coluna "hora" ao CSV.
# ------------------------------------------------------------
