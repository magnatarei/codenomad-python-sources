#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  34. Organizador de pasta por tipo
# ------------------------------------------------------------
# O que faz: Move os arquivos soltos de uma pasta (a de downloads, por
#            exemplo) para subpastas por categoria: imagens, documentos,
#            planilhas, áudio, vídeo, código ou outros, decidindo pela
#            extensão. Mostra a prévia, o relatório do que moveu e sabe
#            desfazer, porque grava um diário das movimentações na pasta.
# Como usar: python 34_organizador_pastas.py ~/Downloads
#            python 34_organizador_pastas.py ~/Downloads --aplicar
#            python 34_organizador_pastas.py ~/Downloads --desfazer
#            python 34_organizador_pastas.py --demo
# O que você aprende: pathlib (iterdir, suffix, mkdir, rglob), shutil.move,
#            dicionários de conjuntos, Counter, json como diário de operações
#            e o padrão prévia / aplicar / desfazer.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

# Extensões sempre em minúsculas e com ponto; a comparação também usa lower().
CATEGORIAS: dict[str, set[str]] = {
    "imagens": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic"},
    "documentos": {".pdf", ".doc", ".docx", ".odt", ".txt", ".md", ".rtf", ".epub"},
    "planilhas": {".xls", ".xlsx", ".ods", ".csv", ".tsv"},
    "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv"},
    "codigo": {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".go", ".rs", ".sh", ".sql"},
}
DIARIO = ".organizador.json"  # fica dentro da pasta organizada; é o que permite desfazer


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário; a mensagem é mostrada sem traceback."""


@dataclass
class Movimento:
    """Um arquivo solto e o destino planejado para ele."""

    origem: Path
    destino: Path
    categoria: str
    tamanho: int


def categoria_de(arquivo: Path) -> str:
    """Devolve a categoria pela extensão; o que não casa com nenhuma vai para "outros"."""
    extensao = arquivo.suffix.lower()
    for nome, extensoes in CATEGORIAS.items():
        if extensao in extensoes:
            return nome
    return "outros"


def destino_livre(destino: Path, reservados: set[Path]) -> Path:
    """Se "foto.jpg" já existe na subpasta, ou já foi prometido a outro arquivo nesta
    rodada, usa "foto (2).jpg", "foto (3).jpg"... Nunca sobrescreve."""
    candidato, numero = destino, 2
    while candidato.exists() or candidato in reservados:
        candidato = destino.with_name(f"{destino.stem} ({numero}){destino.suffix}")
        numero += 1
    reservados.add(candidato)
    return candidato


def planejar(pasta: Path) -> list[Movimento]:
    """Olha só os arquivos soltos na raiz da pasta; subpastas e o diário ficam em paz."""
    plano: list[Movimento] = []
    reservados: set[Path] = set()  # destinos já prometidos, para dois arquivos não colidirem
    for arquivo in sorted(pasta.iterdir()):
        if not arquivo.is_file() or arquivo.name == DIARIO:
            continue
        categoria = categoria_de(arquivo)
        destino = destino_livre(pasta / categoria / arquivo.name, reservados)
        plano.append(Movimento(arquivo, destino, categoria, arquivo.stat().st_size))
    return plano


def formatar_bytes(total: int) -> str:
    """1536 vira "1,5 KB": divide por 1024 enquanto couber."""
    if total < 1024:
        return f"{total} B"
    valor = total / 1024
    for unidade in ("KB", "MB", "GB"):
        if valor < 1024 or unidade == "GB":
            return f"{valor:.1f} {unidade}".replace(".", ",")
        valor /= 1024
    return f"{total} B"


def relatorio(plano: list[Movimento]) -> list[str]:
    """Quantos arquivos e quantos bytes vão para cada categoria."""
    if not plano:
        return ["(nenhum arquivo solto para organizar)"]
    quantidade = Counter(m.categoria for m in plano)
    tamanho = Counter()
    for m in plano:
        tamanho[m.categoria] += m.tamanho
    linhas = [f"{'categoria':<12}{'arquivos':>9}{'tamanho':>12}"]
    for categoria, total in quantidade.most_common():
        linhas.append(f"{categoria:<12}{total:>9}{formatar_bytes(tamanho[categoria]):>12}")
    linhas.append(f"{'total':<12}{len(plano):>9}{formatar_bytes(sum(tamanho.values())):>12}")
    return linhas


def aplicar(pasta: Path, plano: list[Movimento]) -> None:
    """Move cada arquivo e grava o diário com os caminhos relativos para poder desfazer."""
    registros = []
    for m in plano:
        m.destino.parent.mkdir(exist_ok=True)
        shutil.move(str(m.origem), str(m.destino))
        # as_posix() grava "imagens/foto.jpg" em qualquer sistema; Path lê de volta sem problema.
        registros.append({"de": m.origem.name, "para": m.destino.relative_to(pasta).as_posix()})
    (pasta / DIARIO).write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")


def desfazer(pasta: Path) -> list[str]:
    """Lê o diário, devolve cada arquivo ao lugar de origem e apaga as subpastas vazias."""
    diario = pasta / DIARIO
    if not diario.exists():
        raise ErroDeUso(f"não há diário em {pasta}; nada para desfazer")
    registros = json.loads(diario.read_text(encoding="utf-8"))
    linhas, voltaram = [], 0
    for registro in registros:
        atual, original = pasta / registro["para"], pasta / registro["de"]
        if not atual.exists():
            linhas.append(f"  aviso: {registro['para']} não está mais lá")
        elif original.exists():
            linhas.append(f"  aviso: {registro['de']} já existe na raiz, mantido em {registro['para']}")
        else:
            shutil.move(str(atual), str(original))
            voltaram += 1
    for subpasta in pasta.iterdir():
        if subpasta.is_dir() and subpasta.name in (*CATEGORIAS, "outros") and not any(subpasta.iterdir()):
            subpasta.rmdir()
    diario.unlink()
    return [f"Desfeito: {voltaram} de {len(registros)} arquivo(s) voltaram para a raiz."] + linhas


def arvore(pasta: Path) -> list[str]:
    """Lista tudo que está dentro da pasta, com recuo por nível."""
    linhas = []
    for caminho in sorted(pasta.rglob("*")):
        if caminho.name == DIARIO:
            continue
        nivel = len(caminho.relative_to(pasta).parts) - 1
        marca = "/" if caminho.is_dir() else ""
        linhas.append("  " * nivel + caminho.name + marca)
    return linhas


def executar(pasta: Path, aplicar_mesmo: bool, desfazer_mesmo: bool) -> list[str]:
    """Prévia sempre; move ou desfaz só quando pedido. Devolve as linhas de saída."""
    if not pasta.is_dir():
        raise ErroDeUso(f"pasta não encontrada: {pasta}")
    if desfazer_mesmo:
        return desfazer(pasta)
    plano = planejar(pasta)
    linhas = [f"Prévia em {pasta}:"] + [f"  {m.origem.name:<28} -> {m.categoria}/{m.destino.name}" for m in plano]
    linhas += [""] + relatorio(plano)
    if plano and aplicar_mesmo:
        aplicar(pasta, plano)
        linhas.append(f"Pronto: {len(plano)} arquivo(s) movido(s). Diário gravado em {DIARIO}.")
    elif plano:
        linhas.append("Nada foi movido. Use --aplicar para organizar.")
    return linhas


def demo() -> None:
    """Bagunça uma pasta temporária, organiza, mostra o relatório e desfaz."""
    print("=== Demonstração: organizador de pasta por tipo ===")
    arquivos = {"ferias.jpg": 3000, "logo.PNG": 1200, "contrato.pdf": 5000, "anotações.txt": 300,
                "gastos.xlsx": 2200, "clientes.csv": 800, "aula.mp3": 9000, "intro.mp4": 20000,
                "script.py": 400, "index.html": 650, "backup.zip": 7000, "sem_extensao": 50,
                "ferias (2).jpg": 100}
    with tempfile.TemporaryDirectory() as temporaria:
        pasta = Path(temporaria)
        for nome, tamanho in arquivos.items():
            (pasta / nome).write_bytes(b"x" * tamanho)
        (pasta / "imagens").mkdir()
        (pasta / "imagens" / "ferias.jpg").write_bytes(b"y" * 10)  # força o sufixo (2)
        print(f"Pasta bagunçada com {len(arquivos)} arquivos soltos e uma subpasta imagens/ já existente.\n")
        print("$ python 34_organizador_pastas.py ./bagunca --aplicar")
        for linha in executar(pasta, aplicar_mesmo=True, desfazer_mesmo=False):
            print(linha.replace(str(pasta), "./bagunca"))
        print("\nComo ficou a pasta:")
        print("\n".join(arvore(pasta)))
        print("\n$ python 34_organizador_pastas.py ./bagunca --desfazer")
        print("\n".join(executar(pasta, aplicar_mesmo=False, desfazer_mesmo=True)))
        print("\n$ python 34_organizador_pastas.py ./bagunca --desfazer   (de novo, sem diário)")
        try:
            executar(pasta, aplicar_mesmo=False, desfazer_mesmo=True)
        except ErroDeUso as erro:
            print(f"Erro: {erro}".replace(str(pasta), "./bagunca"))
        print("\nArquivos soltos de volta na raiz: " + str(sum(1 for p in pasta.iterdir() if p.is_file())))


def main() -> None:
    """Ponto de entrada: --demo demonstra; sem pasta mostra o uso; senão executa."""
    parser = argparse.ArgumentParser(description="Organiza os arquivos de uma pasta em subpastas por tipo.")
    parser.add_argument("pasta", nargs="?", help="pasta a organizar")
    parser.add_argument("--aplicar", action="store_true", help="move de verdade (sem isto, só prévia)")
    parser.add_argument("--desfazer", action="store_true", help="devolve os arquivos usando o diário")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    args = parser.parse_args()
    if args.demo:
        demo()
        return
    if args.pasta is None:
        parser.print_help()
        sys.exit(1)
    try:
        for linha in executar(Path(args.pasta), args.aplicar, args.desfazer):
            print(linha)
    except ErroDeUso as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Deixe o usuário escolher as categorias num arquivo JSON próprio
#    (--regras regras.json) em vez do dicionário fixo.
# 2. Adicione --por-data para criar subpastas ano/mês a partir da data de
#    modificação (Path.stat().st_mtime).
# 3. Guarde vários diários com data e hora e permita desfazer só o último
#    ou todos, do mais recente para o mais antigo.
# ------------------------------------------------------------
