#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  13. Gerador de senhas seguras
# ------------------------------------------------------------
# O que faz: Cria senhas com o módulo secrets (sorteio criptográfico da
#            biblioteca padrão), com comprimento e classes de símbolos à
#            escolha, garantia de pelo menos um símbolo de cada classe
#            pedida, opção de evitar símbolos ambíguos (l, 1, I, O, 0) e
#            estimativa da entropia em bits com o tempo de um ataque.
# Como usar: python 13_gerador_senhas.py --tamanho 20 --quantidade 3
#            python 13_gerador_senhas.py --tamanho 12 --sem-simbolos --sem-ambiguos
#            python 13_gerador_senhas.py --demo
# O que você aprende: a diferença entre random e secrets, as constantes de
#            string, dataclasses com métodos, math.log2, embaralhar com
#            SystemRandom, flags negativas no argparse e números grandes.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import math
import secrets
import string
import sys
from dataclasses import dataclass

# Símbolos que se confundem em fontes comuns: l com 1 e I, O com 0.
AMBIGUOS = set("l1IO0|")
# Pontuação enxuta: sem aspas e barras, que atrapalham em terminais e shells.
SIMBOLOS = "!@#$%&*+-=?_"
# Palpite conservador para um ataque offline com placas de vídeo atuais.
TENTATIVAS_POR_SEGUNDO = 1e11


@dataclass(frozen=True)
class Perfil:
    """Quais classes de símbolos entram na senha e com que tamanho."""

    tamanho: int = 16
    minusculas: bool = True
    maiusculas: bool = True
    digitos: bool = True
    simbolos: bool = True
    sem_ambiguos: bool = False

    def classes(self) -> list[str]:
        """Monta a lista de alfabetos escolhidos, já sem os ambíguos se pedido."""
        escolhidas: list[str] = []
        if self.minusculas:
            escolhidas.append(string.ascii_lowercase)
        if self.maiusculas:
            escolhidas.append(string.ascii_uppercase)
        if self.digitos:
            escolhidas.append(string.digits)
        if self.simbolos:
            escolhidas.append(SIMBOLOS)
        if self.sem_ambiguos:
            escolhidas = ["".join(c for c in cls if c not in AMBIGUOS) for cls in escolhidas]
        return escolhidas

    def alfabeto(self) -> str:
        """Todos os símbolos possíveis, juntos em uma única string."""
        return "".join(self.classes())

    def descricao(self) -> str:
        """Resumo legível do perfil, para os relatórios."""
        nomes = []
        if self.minusculas:
            nomes.append("minúsculas")
        if self.maiusculas:
            nomes.append("maiúsculas")
        if self.digitos:
            nomes.append("dígitos")
        if self.simbolos:
            nomes.append("símbolos")
        extra = ", sem ambíguos" if self.sem_ambiguos else ""
        return f"{self.tamanho} símbolos: {' + '.join(nomes)}{extra}"


def gerar_senha(perfil: Perfil) -> str:
    """Sorteia uma senha que tem pelo menos um símbolo de cada classe."""
    classes = perfil.classes()
    if not classes:
        raise ValueError("escolha pelo menos uma classe de símbolos")
    if perfil.tamanho < len(classes):
        raise ValueError(
            f"tamanho {perfil.tamanho} não comporta {len(classes)} classes obrigatórias"
        )
    # secrets.choice usa a fonte de aleatoriedade do sistema operacional.
    # random.choice não serve para senhas: a sequência dele é previsível.
    senha = [secrets.choice(cls) for cls in classes]
    alfabeto = perfil.alfabeto()
    senha += [secrets.choice(alfabeto) for _ in range(perfil.tamanho - len(senha))]
    # Sem embaralhar, os primeiros símbolos seguiriam sempre a ordem das classes.
    secrets.SystemRandom().shuffle(senha)
    return "".join(senha)


def entropia_bits(perfil: Perfil) -> float:
    """Entropia = tamanho da senha vezes log2 do tamanho do alfabeto."""
    return perfil.tamanho * math.log2(len(perfil.alfabeto()))


def classificar(bits: float) -> str:
    """Faixas usuais: abaixo de 40 bits é fraca, acima de 80 é muito forte."""
    if bits < 40:
        return "fraca"
    if bits < 60:
        return "razoável"
    if bits < 80:
        return "forte"
    return "muito forte"


def tempo_legivel(segundos: float) -> str:
    """Converte segundos em uma frase como '3 dias' ou '2.1e+12 anos'."""
    if segundos < 1:
        return "menos de 1 segundo"
    escalas = [("ano", 365 * 86400), ("dia", 86400), ("hora", 3600),
               ("minuto", 60), ("segundo", 1)]
    for nome, tamanho in escalas:
        if segundos >= tamanho:
            valor = segundos / tamanho
            if valor >= 1e6:
                return f"{valor:.1e} {nome}s"
            plural = "s" if valor >= 2 else ""
            return f"{valor:,.0f} {nome}{plural}".replace(",", ".")
    return "menos de 1 segundo"


def tempo_para_quebrar(bits: float) -> str:
    """Tempo médio de um ataque: em média ele acerta na metade das tentativas."""
    segundos = (2 ** bits) / 2 / TENTATIVAS_POR_SEGUNDO
    return tempo_legivel(segundos)


def relatorio(perfil: Perfil, quantidade: int) -> None:
    """Imprime as senhas e, em seguida, a análise do perfil usado."""
    for _ in range(quantidade):
        print("  " + gerar_senha(perfil))
    bits = entropia_bits(perfil)
    print(f"  perfil:   {perfil.descricao()}")
    print(f"  alfabeto: {len(perfil.alfabeto())} símbolos possíveis")
    print(f"  entropia: {bits:.1f} bits ({classificar(bits)})")
    print(f"  ataque a {TENTATIVAS_POR_SEGUNDO:.0e} tentativas/s: {tempo_para_quebrar(bits)}")


def demo() -> None:
    """Gera senhas de 12, 16 e 24 símbolos com perfis diferentes."""
    print("=" * 64)
    print("Gerador de senhas seguras: demonstração")
    print("=" * 64)
    perfis = [
        ("Perfil 1: 12 símbolos, letras e dígitos", Perfil(12, simbolos=False)),
        ("Perfil 2: 16 símbolos, todas as classes", Perfil(16)),
        ("Perfil 3: 24 símbolos, sem símbolos e sem ambíguos",
         Perfil(24, simbolos=False, sem_ambiguos=True)),
    ]
    for titulo, perfil in perfis:
        print(f"\n{titulo}")
        relatorio(perfil, quantidade=2)
    fraca = Perfil(6, minusculas=False, maiusculas=False, simbolos=False)
    print("\nPara comparar, um PIN de 6 dígitos:")
    relatorio(fraca, quantidade=1)
    print("\nCada símbolo a mais multiplica o trabalho do ataque pelo tamanho do alfabeto.")


def construir_parser() -> argparse.ArgumentParser:
    """Define a linha de comando do programa."""
    parser = argparse.ArgumentParser(
        description="Gera senhas com o módulo secrets e estima a entropia.",
        epilog="Exemplo: python 13_gerador_senhas.py --tamanho 20 --sem-ambiguos",
    )
    parser.add_argument("--tamanho", type=int, default=16,
                        help="quantidade de símbolos da senha (padrão: 16)")
    parser.add_argument("--quantidade", type=int, default=1,
                        help="quantas senhas gerar (padrão: 1)")
    parser.add_argument("--sem-minusculas", action="store_true", help="não usa a-z")
    parser.add_argument("--sem-maiusculas", action="store_true", help="não usa A-Z")
    parser.add_argument("--sem-digitos", action="store_true", help="não usa 0-9")
    parser.add_argument("--sem-simbolos", action="store_true",
                        help="não usa pontuação (!@#...)")
    parser.add_argument("--sem-ambiguos", action="store_true",
                        help="evita l, 1, I, O, 0 e |")
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: devolve 0 no sucesso e 1 quando o perfil não serve."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    if not argv:
        parser.print_help()
        return 0
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    if args.tamanho < 1 or args.quantidade < 1:
        parser.error("--tamanho e --quantidade precisam ser pelo menos 1")
    perfil = Perfil(
        tamanho=args.tamanho,
        minusculas=not args.sem_minusculas,
        maiusculas=not args.sem_maiusculas,
        digitos=not args.sem_digitos,
        simbolos=not args.sem_simbolos,
        sem_ambiguos=args.sem_ambiguos,
    )
    try:
        relatorio(perfil, args.quantidade)
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Gere frases-senha no estilo "cavalo-bateria-grampo" sorteando
#      palavras de uma lista com secrets.choice e calcule a entropia delas.
#   2. Adicione a opção --pronunciavel, alternando consoantes e vogais
#      para senhas mais fáceis de ditar.
#   3. Gere 10 mil senhas e conte os símbolos com collections.Counter para
#      confirmar que o sorteio é uniforme.
# ------------------------------------------------------------
