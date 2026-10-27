#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  40. Backup de pasta com data
# ------------------------------------------------------------
# O que faz: Copia uma pasta inteira para um destino cujo nome leva data e
#            hora (projeto_2026-10-25_183000), ignorando os padrões que você
#            escolher (*.log, __pycache__...). Lista o que foi copiado e, se
#            houver um backup anterior no mesmo destino, compara os dois por
#            SHA-256 e mostra arquivos novos, removidos e alterados.
# Como usar: python 40_backup_pasta.py ./projeto ./backups --ignorar "*.log" --ignorar __pycache__
#            python 40_backup_pasta.py --comparar ./backups/projeto_2026-10-25_090000 ./backups/projeto_2026-10-25_183000
#            python 40_backup_pasta.py --demo
# O que você aprende: shutil.copytree com ignore_patterns, datetime com
#            strftime, pathlib (rglob, relative_to, resolve), hashlib para
#            comparar conteúdo, operações de conjunto entre dicionários e
#            argparse com action="append".
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class ErroDeUso(Exception):
    """Erro causado pela entrada do usuário; a mensagem é mostrada sem traceback."""


@dataclass
class Resultado:
    """O que o backup produziu: a pasta criada, os arquivos copiados e o total em bytes."""

    destino: Path
    arquivos: list[Path]  # caminhos relativos ao backup
    bytes_total: int


def listar_arquivos(pasta: Path) -> list[Path]:
    """Todos os arquivos, em qualquer profundidade, como caminhos relativos ordenados."""
    return sorted(p.relative_to(pasta) for p in pasta.rglob("*") if p.is_file())


def sha256_de(arquivo: Path) -> str:
    """Lê em blocos para não carregar um arquivo grande inteiro na memória."""
    resumo = hashlib.sha256()
    with arquivo.open("rb") as origem:
        for pedaco in iter(lambda: origem.read(1 << 16), b""):
            resumo.update(pedaco)
    return resumo.hexdigest()


def assinatura(pasta: Path) -> dict[str, str]:
    """Mapa caminho relativo -> SHA-256; é o retrato da pasta num instante."""
    return {rel.as_posix(): sha256_de(pasta / rel) for rel in listar_arquivos(pasta)}


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


def nome_do_backup(origem: Path, destino_base: Path, agora: datetime) -> Path:
    """projeto_2026-10-25_183000; se dois backups caírem no mesmo segundo, acrescenta _2, _3..."""
    base = destino_base / f"{origem.name}_{agora:%Y-%m-%d_%H%M%S}"
    candidato, numero = base, 2
    while candidato.exists():
        candidato = base.with_name(f"{base.name}_{numero}")
        numero += 1
    return candidato


def fazer_backup(origem: Path, destino_base: Path, ignorar: list[str], agora: datetime | None = None) -> Resultado:
    """Copia a árvore inteira de uma vez; ignore_patterns filtra arquivos e pastas pelo nome."""
    if not origem.is_dir():
        raise ErroDeUso(f"pasta de origem não encontrada: {origem}")
    if destino_base.resolve().is_relative_to(origem.resolve()):
        raise ErroDeUso("o destino não pode ficar dentro da origem (o backup copiaria a si mesmo)")
    destino_base.mkdir(parents=True, exist_ok=True)
    destino = nome_do_backup(origem, destino_base, agora or datetime.now())
    shutil.copytree(origem, destino, ignore=shutil.ignore_patterns(*ignorar))
    arquivos = listar_arquivos(destino)
    return Resultado(destino, arquivos, sum((destino / rel).stat().st_size for rel in arquivos))


def backups_anteriores(destino_base: Path, origem: Path, atual: Path) -> list[Path]:
    """Pastas irmãs com o mesmo prefixo; o nome com data ordena do mais antigo ao mais novo."""
    prefixo = f"{origem.name}_"
    return sorted(p for p in destino_base.iterdir() if p.is_dir() and p.name.startswith(prefixo) and p != atual)


def comparar(anterior: Path, atual: Path) -> list[str]:
    """Compara os dois retratos e descreve o que mudou entre um backup e outro."""
    for pasta in (anterior, atual):
        if not pasta.is_dir():
            raise ErroDeUso(f"backup não encontrado: {pasta}")
    antes, depois = assinatura(anterior), assinatura(atual)
    novos = sorted(set(depois) - set(antes))
    removidos = sorted(set(antes) - set(depois))
    alterados = sorted(nome for nome in antes.keys() & depois.keys() if antes[nome] != depois[nome])
    iguais = len(antes.keys() & depois.keys()) - len(alterados)
    linhas = [f"Comparando {anterior.name} -> {atual.name}:"]
    for rotulo, lista in (("novo", novos), ("removido", removidos), ("alterado", alterados)):
        linhas += [f"  {rotulo:<9} {nome}" for nome in lista]
    linhas.append(f"  {len(novos)} novo(s), {len(removidos)} removido(s), {len(alterados)} alterado(s), "
                  f"{iguais} sem mudança")
    return linhas


def executar(origem: Path, destino_base: Path, ignorar: list[str], agora: datetime | None = None) -> list[str]:
    """Faz o backup, lista o que foi copiado e compara com o backup mais recente, se houver."""
    resultado = fazer_backup(origem, destino_base, ignorar, agora)
    linhas = [f"Backup criado em {resultado.destino}"]
    linhas += [f"  {rel.as_posix():<32} {formatar_bytes((resultado.destino / rel).stat().st_size):>10}"
               for rel in resultado.arquivos]
    linhas.append(f"  {len(resultado.arquivos)} arquivo(s), {formatar_bytes(resultado.bytes_total)} no total")
    anteriores = backups_anteriores(destino_base, origem, resultado.destino)
    if anteriores:
        linhas += [""] + comparar(anteriores[-1], resultado.destino)
    else:
        linhas.append("Primeiro backup desta pasta: nada para comparar ainda.")
    return linhas


def demo() -> None:
    """Dois backups de uma pasta temporária, com alterações entre eles, e a comparação."""
    print("=== Demonstração: backup de pasta com data ===")
    with tempfile.TemporaryDirectory() as temporaria:
        raiz = Path(temporaria)
        projeto, backups = raiz / "projeto", raiz / "backups"
        conteudo = {"README.md": "# Projeto de exemplo\n", "src/app.py": "print('olá')\n",
                    "src/util.py": "def dobro(x):\n    return 2 * x\n", "dados/clientes.csv": "nome,cidade\nAna,Recife\n",
                    "debug.log": "linha de log\n" * 50, "__pycache__/app.cpython.pyc": "bytes compilados"}
        for nome, texto in conteudo.items():
            (projeto / nome).parent.mkdir(parents=True, exist_ok=True)
            (projeto / nome).write_text(texto, encoding="utf-8")
        ignorar = ["*.log", "__pycache__"]
        print(f"Pasta projeto/ com {len(conteudo)} arquivos; ignorando {', '.join(ignorar)}.\n")
        print("$ python 40_backup_pasta.py ./projeto ./backups --ignorar \"*.log\" --ignorar __pycache__")
        for linha in executar(projeto, backups, ignorar, datetime(2026, 10, 25, 9, 0, 0)):
            print(linha.replace(str(backups), "./backups"))
        (projeto / "src/app.py").write_text("print('olá, mundo')\n", encoding="utf-8")
        (projeto / "src/novo.py").write_text("NOVO = True\n", encoding="utf-8")
        (projeto / "dados/clientes.csv").unlink()
        print("\nAlterações: src/app.py editado, src/novo.py criado, dados/clientes.csv apagado.\n")
        print("$ python 40_backup_pasta.py ./projeto ./backups --ignorar \"*.log\" --ignorar __pycache__")
        for linha in executar(projeto, backups, ignorar, datetime(2026, 10, 25, 18, 30, 0)):
            print(linha.replace(str(backups), "./backups"))
        print("\n$ python 40_backup_pasta.py ./projeto ./projeto/backups")
        try:
            executar(projeto, projeto / "backups", ignorar)
        except ErroDeUso as erro:
            print(f"Erro: {erro}")


def main() -> None:
    """Ponto de entrada: --demo demonstra; --comparar só compara; senão faz o backup."""
    parser = argparse.ArgumentParser(description="Backup de pasta com carimbo de data e comparação.")
    parser.add_argument("origem", nargs="?", help="pasta a copiar")
    parser.add_argument("destino", nargs="?", help="pasta onde os backups ficam")
    parser.add_argument("--ignorar", action="append", default=[], metavar="PADRÃO",
                        help="padrão a ignorar (repita a opção para vários)")
    parser.add_argument("--comparar", nargs=2, metavar=("ANTERIOR", "ATUAL"), help="só compara dois backups")
    parser.add_argument("--demo", action="store_true", help="roda uma demonstração completa")
    args = parser.parse_args()
    if args.demo:
        demo()
        return
    try:
        if args.comparar:
            print("\n".join(comparar(Path(args.comparar[0]), Path(args.comparar[1]))))
            return
        if args.origem is None or args.destino is None:
            parser.print_help()
            sys.exit(1)
        print("\n".join(executar(Path(args.origem), Path(args.destino), args.ignorar)))
    except ErroDeUso as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Adicione --zip para gravar o backup como um único arquivo compactado
#    (shutil.make_archive) em vez de uma pasta.
# 2. Crie --manter N que apaga os backups mais antigos, deixando só os N
#    mais recentes (shutil.rmtree, com cuidado).
# 3. Faça um backup incremental: copie só os arquivos cujo SHA-256 mudou
#    desde o backup anterior e registre o restante num índice JSON.
# ------------------------------------------------------------
