#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  35. Detector de arquivos duplicados
# ------------------------------------------------------------
# O que faz: Percorre uma pasta e as subpastas, agrupa os arquivos primeiro
#            pelo tamanho (barato) e só depois pelo SHA-256 (caro), lista cada
#            grupo de duplicados e diz quanto espaço seria liberado mantendo
#            uma cópia de cada. Pode gravar o relatório num arquivo de texto.
# Como usar: python 35_duplicados_hash.py ~/Fotos
#            python 35_duplicados_hash.py ~/Fotos --a-partir-de 1024 --relatorio duplicados.txt
#            python 35_duplicados_hash.py --demo
# O que você aprende: hashlib com leitura em blocos, pathlib.rglob,
#            defaultdict para agrupar, dataclasses com property, a ideia de
#            filtrar pelo critério barato antes do critério caro.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário; a mensagem é mostrada sem traceback."""


@dataclass
class Grupo:
    """Arquivos com o mesmo conteúdo. O primeiro da lista é o que seria mantido."""

    digest: str
    tamanho: int
    arquivos: list[Path]

    @property
    def desperdicio(self) -> int:
        """Bytes que sobrariam apagando todas as cópias menos uma."""
        return self.tamanho * (len(self.arquivos) - 1)


@dataclass
class Resumo:
    """Contadores da varredura, para o relatório mostrar o trabalho que foi poupado."""

    vistos: int = 0
    candidatos: int = 0  # arquivos que dividem o tamanho com algum outro
    grupos: list[Grupo] = field(default_factory=list)

    @property
    def desperdicio(self) -> int:
        """Soma do desperdício de todos os grupos."""
        return sum(g.desperdicio for g in self.grupos)


def sha256_de(arquivo: Path, bloco: int = 1 << 16) -> str:
    """Lê em blocos de 64 KB: funciona igual para um arquivo de 1 KB ou de 10 GB."""
    resumo = hashlib.sha256()
    with arquivo.open("rb") as origem:
        # iter com sentinela chama origem.read(bloco) até devolver b"" (fim do arquivo).
        for pedaco in iter(lambda: origem.read(bloco), b""):
            resumo.update(pedaco)
    return resumo.hexdigest()


def por_tamanho(pasta: Path, minimo: int) -> dict[int, list[Path]]:
    """Primeira peneira: só arquivos de tamanho igual podem ser idênticos."""
    grupos: dict[int, list[Path]] = defaultdict(list)
    for caminho in sorted(pasta.rglob("*")):
        if caminho.is_file():
            tamanho = caminho.stat().st_size
            if tamanho >= minimo:
                grupos[tamanho].append(caminho)
    return grupos


def encontrar_duplicados(pasta: Path, minimo: int = 1) -> Resumo:
    """Segunda peneira: calcula o SHA-256 só de quem passou pela primeira."""
    resumo = Resumo()
    for tamanho, arquivos in sorted(por_tamanho(pasta, minimo).items(), reverse=True):
        resumo.vistos += len(arquivos)
        if len(arquivos) < 2:
            continue
        resumo.candidatos += len(arquivos)
        por_digest: dict[str, list[Path]] = defaultdict(list)
        for arquivo in arquivos:
            por_digest[sha256_de(arquivo)].append(arquivo)
        for digest, iguais in por_digest.items():
            if len(iguais) > 1:
                resumo.grupos.append(Grupo(digest, tamanho, iguais))
    # Grupos que liberam mais espaço aparecem primeiro.
    resumo.grupos.sort(key=lambda g: g.desperdicio, reverse=True)
    return resumo


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


def relatorio(pasta: Path, resumo: Resumo) -> list[str]:
    """Texto final: um bloco por grupo e o total que seria liberado."""
    linhas = [
        f"Pasta analisada: {pasta}",
        f"Arquivos vistos: {resumo.vistos}; com tamanho repetido: {resumo.candidatos} "
        f"(só estes tiveram o SHA-256 calculado)",
        f"Grupos de duplicados: {len(resumo.grupos)}",
        "",
    ]
    for numero, grupo in enumerate(resumo.grupos, start=1):
        linhas.append(f"Grupo {numero}: {len(grupo.arquivos)} cópias de {formatar_bytes(grupo.tamanho)}, "
                      f"sha256 {grupo.digest[:12]}..., libera {formatar_bytes(grupo.desperdicio)}")
        for posicao, arquivo in enumerate(grupo.arquivos):
            marca = "manter " if posicao == 0 else "cópia  "
            linhas.append(f"  {marca} {arquivo.relative_to(pasta).as_posix()}")
    if not resumo.grupos:
        linhas.append("Nenhum arquivo duplicado.")
    linhas.append("")
    linhas.append(f"Espaço que seria liberado: {formatar_bytes(resumo.desperdicio)}")
    return linhas


def executar(pasta: Path, minimo: int, saida: Path | None) -> list[str]:
    """Valida a pasta, roda a varredura e grava o relatório se um arquivo foi pedido."""
    if not pasta.is_dir():
        raise ErroDeUso(f"pasta não encontrada: {pasta}")
    if minimo < 0:
        raise ErroDeUso("--a-partir-de não pode ser negativo")
    linhas = relatorio(pasta, encontrar_duplicados(pasta, minimo))
    if saida is not None:
        saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        linhas.append(f"Relatório gravado em {saida}")
    return linhas


def demo() -> None:
    """Monta uma pasta temporária com cópias espalhadas e mostra o relatório."""
    print("=== Demonstração: detector de arquivos duplicados ===")
    foto = b"\x89PNG imagem de teste " * 300          # 6,3 KB, três cópias
    musica = b"ID3 trilha sonora de teste " * 1000    # 26 KB, duas cópias
    # Literal b"..." só aceita ASCII; texto com acento vira bytes com encode().
    relatorio_a = "relatório trimestral A".encode("utf-8").ljust(500, b".")
    relatorio_b = "relatório trimestral B".encode("utf-8").ljust(500, b".")  # mesmo tamanho, outro conteúdo
    arquivos = {
        "fotos/praia.png": foto,
        "fotos/2024/praia (1).png": foto,
        "backup/praia_copia.png": foto,
        "musicas/trilha.mp3": musica,
        "backup/trilha.mp3": musica,
        "docs/relatorio_a.txt": relatorio_a,
        "docs/relatorio_b.txt": relatorio_b,
        "docs/unico.txt": "este arquivo é único\n".encode("utf-8"),
        "vazio.txt": b"",
    }
    with tempfile.TemporaryDirectory() as temporaria:
        pasta = Path(temporaria)
        for nome, conteudo in arquivos.items():
            destino = pasta / nome
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(conteudo)
        print(f"Pasta criada com {len(arquivos)} arquivos em 5 subpastas (dois deles têm o mesmo "
              "tamanho mas conteúdo diferente; o arquivo vazio é ignorado por padrão).\n")
        print("$ python 35_duplicados_hash.py ./pasta --relatorio duplicados.txt")
        for linha in executar(pasta, 1, pasta / "duplicados.txt"):
            print(linha.replace(str(pasta), "./pasta"))
        print("\n$ python 35_duplicados_hash.py ./pasta --a-partir-de 10000")
        for linha in executar(pasta, 10000, None)[:3]:
            print(linha.replace(str(pasta), "./pasta"))
        print("...")
        print("\n$ python 35_duplicados_hash.py ./pasta/nao-existe")
        try:
            executar(pasta / "nao-existe", 1, None)
        except ErroDeUso as erro:
            print(f"Erro: {erro}".replace(str(pasta), "./pasta"))


def main() -> None:
    """Ponto de entrada: --demo demonstra; sem pasta mostra o uso; senão executa."""
    parser = argparse.ArgumentParser(description="Encontra arquivos duplicados por tamanho e SHA-256.")
    parser.add_argument("pasta", nargs="?", help="pasta a analisar (inclui subpastas)")
    parser.add_argument("--a-partir-de", type=int, default=1, metavar="N",
                        help="só considera arquivos com N bytes ou mais (padrão 1, ignora vazios)")
    parser.add_argument("--relatorio", help="grava o relatório neste arquivo de texto")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    args = parser.parse_args()
    if args.demo:
        demo()
        return
    if args.pasta is None:
        parser.print_help()
        sys.exit(1)
    try:
        for linha in executar(Path(args.pasta), args.a_partir_de, Path(args.relatorio) if args.relatorio else None):
            print(linha)
    except ErroDeUso as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Adicione --apagar que remove as cópias (nunca a primeira de cada
#    grupo) só depois de pedir confirmação com input().
# 2. Troque a remoção por um link simbólico (Path.symlink_to) apontando
#    para a cópia mantida, liberando espaço sem perder o caminho.
# 3. Compare os primeiros 4 KB de cada candidato antes do SHA-256 completo
#    e meça com time.perf_counter quanto isso economiza numa pasta grande.
# ------------------------------------------------------------
