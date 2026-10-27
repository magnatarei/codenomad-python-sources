#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  33. Renomeador de arquivos em lote
# ------------------------------------------------------------
# O que faz: Renomeia os arquivos de uma pasta seguindo regras que você
#            combina: prefixo, sufixo, numeração sequencial, troca de texto e
#            minúsculas. Sempre mostra a prévia (dry-run) e só mexe nos
#            arquivos com --aplicar; nunca sobrescreve um arquivo existente.
# Como usar: python 33_renomeador_lote.py ./fotos --extensao .jpg --prefixo viagem_ --minusculas
#            python 33_renomeador_lote.py ./fotos --trocar DSC foto --numerar --aplicar
#            python 33_renomeador_lote.py --demo
# O que você aprende: pathlib (stem, suffix, with_name, rename), dataclasses,
#            detecção de conflitos com set, o padrão "prévia antes de aplicar"
#            e argparse com nargs=2 e flags combinadas.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário; a mensagem é mostrada sem traceback."""


@dataclass
class Regras:
    """Tudo o que pode ser feito com um nome. Os campos vazios são ignorados."""

    prefixo: str = ""
    sufixo: str = ""
    numerar: bool = False
    inicio: int = 1
    digitos: int = 3
    trocar: tuple[str, str] | None = None
    minusculas: bool = False
    extensao: str | None = None  # só renomeia arquivos com esta extensão, ex.: ".jpg"

    def ativa(self) -> bool:
        """True quando ao menos uma regra que muda o nome foi escolhida."""
        return bool(self.prefixo or self.sufixo or self.numerar or self.trocar or self.minusculas)


@dataclass
class Mudanca:
    """Um par origem/destino; bloqueio diferente de None quer dizer que não será aplicada."""

    origem: Path
    destino: Path
    bloqueio: str | None = None


def novo_nome(arquivo: Path, regras: Regras, posicao: int) -> str:
    """Aplica as regras ao nome. stem é o nome sem extensão; suffix é a extensão com ponto."""
    base = arquivo.stem
    if regras.trocar:
        base = base.replace(regras.trocar[0], regras.trocar[1])
    if regras.numerar:
        # :0{n}d preenche com zeros à esquerda: 1 vira 001 quando digitos é 3.
        base = f"{regras.inicio + posicao:0{regras.digitos}d}_{base}"
    nome = regras.prefixo + base + regras.sufixo + arquivo.suffix
    return nome.lower() if regras.minusculas else nome


def planejar(pasta: Path, regras: Regras) -> list[Mudanca]:
    """Calcula o destino de cada arquivo e marca os que não podem ser renomeados."""
    arquivos = sorted(p for p in pasta.iterdir() if p.is_file())
    if regras.extensao:
        arquivos = [p for p in arquivos if p.suffix.lower() == regras.extensao.lower()]
    plano: list[Mudanca] = []
    reservados: set[str] = set()  # nomes de destino já prometidos nesta rodada
    for posicao, arquivo in enumerate(arquivos):
        destino = arquivo.with_name(novo_nome(arquivo, regras, posicao))
        chave = destino.name.lower()
        bloqueio = None
        if destino.name == arquivo.name:
            bloqueio = "o nome não muda"
        elif chave in reservados:
            bloqueio = "outro arquivo já vai receber este nome"
        elif destino.exists() and chave != arquivo.name.lower():
            # No Windows "Foto.JPG" e "foto.jpg" são o mesmo arquivo, por isso a comparação em minúsculas.
            bloqueio = "já existe um arquivo com este nome"
        reservados.add(chave)
        plano.append(Mudanca(arquivo, destino, bloqueio))
    return plano


def descrever(plano: list[Mudanca]) -> list[str]:
    """Linhas da prévia: origem -> destino, ou o motivo do bloqueio."""
    if not plano:
        return ["(nenhum arquivo para renomear)"]
    largura = max(len(m.origem.name) for m in plano)
    linhas = []
    for m in plano:
        if m.bloqueio:
            linhas.append(f"  {m.origem.name.ljust(largura)}    (pulado: {m.bloqueio})")
        else:
            linhas.append(f"  {m.origem.name.ljust(largura)} -> {m.destino.name}")
    prontos = sum(1 for m in plano if not m.bloqueio)
    linhas.append(f"  {prontos} de {len(plano)} arquivo(s) seriam renomeados")
    return linhas


def aplicar(plano: list[Mudanca]) -> int:
    """Renomeia só as mudanças sem bloqueio e devolve quantas foram feitas."""
    feitas = 0
    for m in plano:
        if m.bloqueio is None:
            m.origem.rename(m.destino)
            feitas += 1
    return feitas


def montar_parser() -> argparse.ArgumentParser:
    """Define a pasta, as regras de nome e as flags de controle."""
    parser = argparse.ArgumentParser(description="Renomeia arquivos em lote com prévia.")
    parser.add_argument("pasta", nargs="?", help="pasta com os arquivos")
    parser.add_argument("--prefixo", default="", help="texto no começo do nome")
    parser.add_argument("--sufixo", default="", help="texto antes da extensão")
    parser.add_argument("--numerar", action="store_true", help="numera em sequência: 001_nome")
    parser.add_argument("--inicio", type=int, default=1, help="primeiro número (padrão 1)")
    parser.add_argument("--digitos", type=int, default=3, help="largura do número (padrão 3)")
    parser.add_argument("--trocar", nargs=2, metavar=("ANTIGO", "NOVO"), help="substitui um trecho")
    parser.add_argument("--minusculas", action="store_true", help="deixa tudo em minúsculas")
    parser.add_argument("--extensao", help="só arquivos com esta extensão, ex.: .jpg")
    parser.add_argument("--aplicar", action="store_true", help="renomeia de verdade (sem isto, só prévia)")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    return parser


def regras_de(args: argparse.Namespace) -> Regras:
    """Converte os argumentos em Regras, validando o que o argparse não valida."""
    if not 1 <= args.digitos <= 6:
        raise ErroDeUso("--digitos precisa ficar entre 1 e 6")
    if args.inicio < 0:
        raise ErroDeUso("--inicio não pode ser negativo")
    extensao = args.extensao
    if extensao and not extensao.startswith("."):
        extensao = "." + extensao
    regras = Regras(args.prefixo, args.sufixo, args.numerar, args.inicio, args.digitos,
                    tuple(args.trocar) if args.trocar else None, args.minusculas, extensao)
    if not regras.ativa():
        raise ErroDeUso("informe pelo menos uma regra (--prefixo, --sufixo, --numerar, --trocar ou --minusculas)")
    return regras


def executar(pasta: Path, regras: Regras, aplicar_mesmo: bool) -> list[str]:
    """Prévia sempre; aplicação só quando pedida."""
    if not pasta.is_dir():
        raise ErroDeUso(f"pasta não encontrada: {pasta}")
    plano = planejar(pasta, regras)
    linhas = [f"Prévia em {pasta}:"] + descrever(plano)
    if aplicar_mesmo:
        linhas.append(f"Aplicado: {aplicar(plano)} arquivo(s) renomeado(s).")
    else:
        linhas.append("Nada foi alterado. Use --aplicar para renomear.")
    return linhas


def demo() -> None:
    """Cria uma pasta temporária com arquivos e mostra prévia, conflito e aplicação."""
    print("=== Demonstração: renomeador de arquivos em lote ===")
    nomes = ["DSC_0001.JPG", "DSC_0002.JPG", "IMG_0003.jpg", "Relatório Final.PDF",
             "notas.txt", "viagem_dsc_0001.jpg"]
    parser = montar_parser()
    with tempfile.TemporaryDirectory() as temporaria:
        pasta = Path(temporaria)
        for nome in nomes:
            (pasta / nome).write_text(f"conteúdo de {nome}\n", encoding="utf-8")
        print("Arquivos criados: " + ", ".join(nomes))
        roteiro = [
            ["--extensao", ".jpg", "--prefixo", "viagem_", "--minusculas"],
            ["--extensao", ".jpg", "--prefixo", "viagem_", "--minusculas", "--aplicar"],
            ["--trocar", "viagem_", "foto_", "--numerar", "--digitos", "2", "--aplicar"],
            ["--digitos", "9"],
        ]
        for comando in roteiro:
            print(f"\n$ python 33_renomeador_lote.py ./fotos {' '.join(comando)}")
            args = parser.parse_args([str(pasta), *comando])
            try:
                for linha in executar(pasta, regras_de(args), args.aplicar):
                    print(linha.replace(str(pasta), "./fotos"))
            except ErroDeUso as erro:
                print(f"Erro: {erro}")
        print("\nPasta no fim: " + ", ".join(sorted(p.name for p in pasta.iterdir())))


def main() -> None:
    """Ponto de entrada: --demo demonstra; sem pasta mostra o uso; senão executa."""
    parser = montar_parser()
    args = parser.parse_args()
    if args.demo:
        demo()
        return
    if args.pasta is None:
        parser.print_help()
        sys.exit(1)
    try:
        for linha in executar(Path(args.pasta), regras_de(args), args.aplicar):
            print(linha)
    except ErroDeUso as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Adicione --regex para trocar trechos com expressões regulares
#    (re.sub) em vez de texto fixo.
# 2. Grave um arquivo "desfazer.txt" com os pares antigo/novo e crie a
#    opção --desfazer que lê esse arquivo e volta os nomes.
# 3. Permita --data para colocar a data de modificação do arquivo no nome
#    (Path.stat().st_mtime e datetime.fromtimestamp).
# ------------------------------------------------------------
