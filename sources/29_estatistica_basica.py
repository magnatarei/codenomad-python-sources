#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  29. Estatística descritiva
# ------------------------------------------------------------
# O que faz: calcula média, mediana, moda, variância, desvio padrão, mínimo,
#            máximo, amplitude e quartis de uma lista de números vinda dos
#            argumentos ou de um arquivo, e desenha um histograma em texto.
# Como usar: python sources/29_estatistica_basica.py 7.5 8 6.5 9 8 7 10 8.5
#            python sources/29_estatistica_basica.py --arquivo notas.txt --classes 6
#            python sources/29_estatistica_basica.py --demo
# O que você aprende: as fórmulas implementadas à mão e conferidas com o
#            módulo statistics, collections.Counter, sorted e fatias, leitura
#            de arquivo com pathlib, tempfile e desenho de barras em texto.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import math
import random
import statistics
import sys
import tempfile
from collections import Counter
from pathlib import Path


def media(dados: list[float]) -> float:
    """Soma de tudo dividida pela quantidade."""
    return sum(dados) / len(dados)


def mediana(dados: list[float]) -> float:
    """Valor do meio depois de ordenar; com quantidade par, a média dos dois do meio."""
    ordenados = sorted(dados)
    n = len(ordenados)
    meio = n // 2
    if n % 2 == 1:
        return ordenados[meio]
    return (ordenados[meio - 1] + ordenados[meio]) / 2


def moda(dados: list[float]) -> list[float]:
    """Valores mais frequentes (pode haver mais de um). Lista vazia se nenhum se repete."""
    contagem = Counter(dados)
    maior = max(contagem.values())
    if maior == 1:
        return []
    return sorted(valor for valor, vezes in contagem.items() if vezes == maior)


def variancia(dados: list[float], amostral: bool = True) -> float:
    """Média dos desvios ao quadrado. Amostral divide por n-1; populacional, por n."""
    m = media(dados)
    soma_quadrados = sum((x - m) ** 2 for x in dados)
    divisor = len(dados) - 1 if amostral else len(dados)
    return soma_quadrados / divisor


def desvio_padrao(dados: list[float], amostral: bool = True) -> float:
    """Raiz quadrada da variância: volta para a mesma unidade dos dados."""
    return math.sqrt(variancia(dados, amostral))


def quartis(dados: list[float]) -> tuple[float, float, float]:
    """Q1, Q2 e Q3 pelo método das metades: mediana da metade de baixo e da de cima."""
    ordenados = sorted(dados)
    n = len(ordenados)
    meio = n // 2
    baixo = ordenados[:meio]
    cima = ordenados[meio + 1:] if n % 2 == 1 else ordenados[meio:]  # ímpar: a mediana fica de fora
    return mediana(baixo), mediana(ordenados), mediana(cima)


def histograma(dados: list[float], classes: int = 8, largura: int = 40) -> list[str]:
    """Divide a amplitude em classes iguais e desenha uma barra proporcional por classe."""
    menor, maior = min(dados), max(dados)
    if menor == maior:
        return [f"  [{menor:g}] {'#' * largura} {len(dados)}"]
    passo = (maior - menor) / classes
    contagens = [0] * classes
    for x in dados:
        i = min(int((x - menor) / passo), classes - 1)  # o máximo cai na última classe
        contagens[i] += 1
    pico = max(contagens)
    linhas = []
    for i, c in enumerate(contagens):
        ini, fim = menor + i * passo, menor + (i + 1) * passo
        fecha = "]" if i == classes - 1 else ")"  # só a última classe inclui o limite de cima
        barra = "#" * round(c / pico * largura)
        linhas.append(f"  [{ini:>7.2f}, {fim:>7.2f}{fecha} {barra:<{largura}} {c}")
    return linhas


def numero(texto: str) -> float:
    """Converte '7,5' ou '7.5' em 7.5, com erro claro."""
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        raise ValueError(f"'{texto}' não é um número") from None


def numero_arg(texto: str) -> float:
    """Mesma conversão, mas com o erro que o argparse sabe mostrar."""
    try:
        return numero(texto)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from None


def ler_arquivo(caminho: str) -> list[float]:
    """Lê números separados por espaço, quebra de linha ou ';' (7,5 e 7.5 valem)."""
    arquivo = Path(caminho)
    if not arquivo.is_file():
        raise ValueError(f"arquivo não encontrado: {caminho}")
    texto = arquivo.read_text(encoding="utf-8").replace(";", " ")
    return [numero(t) for t in texto.split()]


def conferir(dados: list[float]) -> bool:
    """Compara as contas feitas à mão com o módulo statistics da biblioteca padrão."""
    return (math.isclose(media(dados), statistics.mean(dados))
            and math.isclose(mediana(dados), statistics.median(dados))
            and math.isclose(desvio_padrao(dados), statistics.stdev(dados))
            and math.isclose(desvio_padrao(dados, False), statistics.pstdev(dados))
            and sorted(moda(dados) or []) == (sorted(statistics.multimode(dados)) if moda(dados) else []))


def relatorio(dados: list[float], casas: int, classes: int) -> None:
    """Imprime todas as medidas, o histograma e a conferência."""
    fmt = f".{casas}f"
    modas = moda(dados)
    q1, q2, q3 = quartis(dados)
    print(f"  quantidade       : {len(dados)}")
    print(f"  mínimo / máximo  : {min(dados):{fmt}} / {max(dados):{fmt}}")
    print(f"  amplitude        : {max(dados) - min(dados):{fmt}}")
    print(f"  média            : {media(dados):{fmt}}")
    print(f"  mediana          : {mediana(dados):{fmt}}")
    texto_moda = ", ".join(f"{m:{fmt}}" for m in modas) if modas else "não há (nenhum valor se repete)"
    print(f"  moda             : {texto_moda}")
    print(f"  variância        : {variancia(dados):{fmt}} (amostral, n-1)  |  {variancia(dados, False):{fmt}} (populacional, n)")
    print(f"  desvio padrão    : {desvio_padrao(dados):{fmt}} (amostral)  |  {desvio_padrao(dados, False):{fmt}} (populacional)")
    print(f"  quartis Q1/Q2/Q3 : {q1:{fmt}} / {q2:{fmt}} / {q3:{fmt}}   (intervalo interquartil {q3 - q1:{fmt}})")
    print(f"  histograma ({classes} classes):")
    for linha in histograma(dados, classes):
        print(linha)
    print(f"  conferência com o módulo statistics: {'tudo bate' if conferir(dados) else 'DIFERENÇA ENCONTRADA'}")


def demo() -> None:
    """Analisa uma amostra de 40 valores e mostra a leitura a partir de arquivo."""
    print("=== Estatística descritiva: CodeNomad Academy ===\n")
    random.seed(2024)  # semente fixa: a mesma amostra em qualquer máquina
    dados = [float(min(100, max(0, round(random.gauss(72, 11))))) for _ in range(40)]
    print("Amostra: pontuação (0 a 100) de 40 alunos num simulado de lógica")
    print(f"  {[int(x) for x in dados]}")
    print("\nMedidas:")
    relatorio(dados, casas=2, classes=8)
    # Demonstra a leitura de arquivo gravando a amostra na pasta temporária do sistema
    caminho = Path(tempfile.gettempdir()) / "codenomad_amostra_29.txt"
    caminho.write_text("\n".join(f"{x:g}".replace(".", ",") for x in dados), encoding="utf-8")
    lidos = ler_arquivo(str(caminho))
    print(f"\nA amostra gravada em {caminho.name} e lida de volta: {len(lidos)} valores, média {media(lidos):.2f}")
    caminho.unlink()  # apaga o arquivo temporário
    print("\nLeitura: média e mediana próximas indicam amostra simétrica; desvio padrão")
    print("pequeno diante da amplitude indica valores concentrados perto da média.")


def main() -> None:
    """Lê os argumentos e decide entre a demonstração e o uso normal."""
    ap = argparse.ArgumentParser(description="Estatística descritiva de uma lista de números, com histograma.")
    ap.add_argument("numeros", nargs="*", type=numero_arg, help="valores (7.5 ou 7,5)")
    ap.add_argument("--arquivo", help="arquivo com números separados por espaço, linha ou ';'")
    ap.add_argument("--casas", type=int, default=2, help="casas após a vírgula na saída (padrão 2)")
    ap.add_argument("--classes", type=int, default=8, help="quantidade de classes do histograma (padrão 8)")
    ap.add_argument("--demo", action="store_true", help="roda a demonstração completa")
    args = ap.parse_args()
    if args.demo:
        demo()
        return
    dados = list(args.numeros)
    if args.arquivo:
        try:
            dados += ler_arquivo(args.arquivo)
        except ValueError as e:
            sys.exit(f"Erro: {e}")
    if not dados:
        ap.print_help()
        sys.exit(2)
    if len(dados) < 2:
        ap.error("informe pelo menos 2 valores (a variância amostral divide por n-1)")
    if args.classes < 1 or args.casas < 0:
        ap.error("--classes precisa ser pelo menos 1 e --casas não pode ser negativo")
    relatorio(dados, args.casas, args.classes)


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# Para ir além
# 1. Acrescente a assimetria (skewness): média dos desvios ao cubo dividida
#    pelo desvio padrão ao cubo. O que o sinal dela diz sobre a amostra?
# 2. Implemente o cálculo de outliers pela regra 1,5 x intervalo interquartil
#    e marque-os no histograma.
# 3. Leia um CSV com duas colunas (turma, nota) usando o módulo csv e gere
#    um relatório por turma.
# ------------------------------------------------------------
