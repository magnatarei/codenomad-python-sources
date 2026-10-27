#!/usr/bin/env python3
# ============================================================
# CodeNomad Academy  |  Sources Python  |  12. Validador de e-mail e força de senha
# ------------------------------------------------------------
# O que faz: Valida um e-mail com regras claras (um único @, domínio com
#            ponto, sem espaços, limites de tamanho) e dá uma nota de 0 a
#            100 para a força de uma senha, olhando comprimento, variedade
#            de símbolos, sequências e repetições, com dicas de melhoria.
# Como usar: python 12_validador_email_senha.py --email ana@exemplo.com.br
#            python 12_validador_email_senha.py --senha "Tr3m-Azul!2024" --mostrar
#            python 12_validador_email_senha.py --demo
# O que você aprende: expressões regulares, str.partition, dataclasses com
#            field(default_factory), pontuação por critérios, any() e
#            mensagens de erro que dizem exatamente o que corrigir.
# Requisitos: Python 3.10+, só biblioteca padrão
# Licença MIT. Um projeto da CodeNomad Academy (codenomad.org)
# ============================================================
import argparse
import re
import string
import sys
from dataclasses import dataclass, field

# Parte local do e-mail (antes do @): letras, dígitos e sinais aceitos na prática.
LOCAL_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+$")
# Cada rótulo do domínio começa e termina com letra ou dígito; hífen só no meio.
ROTULO_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
TAMANHO_MAXIMO_EMAIL = 254
TAMANHO_MAXIMO_LOCAL = 64

# Senhas que aparecem em todo vazamento. A lista real tem milhões de
# entradas; esta amostra basta para mostrar a ideia.
SENHAS_COMUNS = {
    "123456", "12345678", "123456789", "senha", "password", "qwerty",
    "abc123", "111111", "admin", "letmein", "senha123", "iloveyou",
}
SEQUENCIAS = ("abcdefghijklmnopqrstuvwxyz", "0123456789", "qwertyuiop",
              "asdfghjkl", "zxcvbnm")


def validar_email(email: str) -> tuple[bool, str]:
    """Devolve (válido, motivo) aplicando as regras uma a uma."""
    if not email:
        return False, "e-mail vazio"
    if any(c.isspace() for c in email):
        return False, "e-mail não pode ter espaços"
    if len(email) > TAMANHO_MAXIMO_EMAIL:
        return False, f"e-mail passa de {TAMANHO_MAXIMO_EMAIL} símbolos"
    if email.count("@") != 1:
        return False, f"precisa ter exatamente um @ (tem {email.count('@')})"
    # partition separa em três partes; é mais claro que split quando o
    # separador deve aparecer uma única vez.
    local, _, dominio = email.partition("@")
    if not local:
        return False, "falta a parte antes do @"
    if len(local) > TAMANHO_MAXIMO_LOCAL:
        return False, f"a parte antes do @ passa de {TAMANHO_MAXIMO_LOCAL} símbolos"
    if not LOCAL_RE.match(local):
        return False, "a parte antes do @ tem símbolo não permitido"
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False, "ponto no início, no fim ou dois pontos seguidos antes do @"
    if "." not in dominio:
        return False, "o domínio precisa de pelo menos um ponto (ex.: exemplo.com)"
    rotulos = dominio.split(".")
    for rotulo in rotulos:
        if not ROTULO_RE.match(rotulo):
            return False, f"parte do domínio inválida: '{rotulo or '(vazio)'}'"
    if len(rotulos[-1]) < 2 or not rotulos[-1].isalpha():
        return False, "a terminação do domínio precisa de 2 ou mais letras"
    return True, "formato válido"


@dataclass
class AvaliacaoSenha:
    """Nota, classificação e dicas de uma senha."""

    senha: str
    pontos: int = 0
    nivel: str = ""
    # Listas mutáveis em dataclass precisam de default_factory, senão todas
    # as instâncias compartilhariam a mesma lista.
    dicas: list[str] = field(default_factory=list)


def contem_sequencia(senha: str, tamanho: int = 4) -> bool:
    """Procura trechos como 'abcd', '1234' ou 'qwer', em qualquer direção."""
    baixa = senha.lower()
    for seq in SEQUENCIAS:
        for i in range(len(seq) - tamanho + 1):
            trecho = seq[i:i + tamanho]
            if trecho in baixa or trecho[::-1] in baixa:
                return True
    return False


def contem_repeticao(senha: str, vezes: int = 3) -> bool:
    """Detecta o mesmo símbolo repetido 'vezes' seguidas, como 'aaa' ou '!!!'."""
    # (.)\1 significa "qualquer símbolo, seguido dele mesmo de novo".
    return re.search(r"(.)\1{%d,}" % (vezes - 1), senha) is not None


def classificar(pontos: int) -> str:
    """Traduz a nota em uma palavra que o usuário entende."""
    if pontos < 30:
        return "muito fraca"
    if pontos < 50:
        return "fraca"
    if pontos < 70:
        return "razoável"
    if pontos < 90:
        return "forte"
    return "muito forte"


def avaliar_senha(senha: str) -> AvaliacaoSenha:
    """Pontua de 0 a 100 e devolve dicas do que melhorar."""
    av = AvaliacaoSenha(senha)
    n = len(senha)
    if senha.lower() in SENHAS_COMUNS:
        av.pontos, av.nivel = 0, "muito fraca"
        av.dicas.append("esta senha está em listas públicas de vazamentos; troque")
        return av

    # Comprimento vale até 40 pontos: é o fator que mais pesa.
    if n >= 16:
        av.pontos += 40
    elif n >= 12:
        av.pontos += 30
    elif n >= 8:
        av.pontos += 20
        av.dicas.append("use 12 ou mais símbolos")
    else:
        av.pontos += 5
        av.dicas.append("senha curta: use pelo menos 8, de preferência 12 ou mais")

    # Cada classe presente vale 15 pontos (até 60).
    classes = {
        "letras minúsculas": any(c.islower() for c in senha),
        "letras maiúsculas": any(c.isupper() for c in senha),
        "dígitos": any(c.isdigit() for c in senha),
        "símbolos": any(c in string.punctuation for c in senha),
    }
    av.pontos += 15 * sum(classes.values())
    for nome, presente in classes.items():
        if not presente:
            av.dicas.append(f"acrescente {nome}")

    if contem_sequencia(senha):
        av.pontos -= 15
        av.dicas.append("evite sequências como abcd, 1234 ou qwer")
    if contem_repeticao(senha):
        av.pontos -= 10
        av.dicas.append("evite o mesmo símbolo três vezes seguidas")

    av.pontos = max(0, min(100, av.pontos))
    av.nivel = classificar(av.pontos)
    return av


def mascarar(senha: str) -> str:
    """Mostra só o primeiro e o último símbolo, para não expor a senha."""
    if len(senha) <= 2:
        return "*" * len(senha)
    return senha[0] + "*" * (len(senha) - 2) + senha[-1]


def imprimir_email(email: str) -> bool:
    """Imprime o veredito de um e-mail e devolve se ele é válido."""
    valido, motivo = validar_email(email)
    marca = "[OK]" if valido else "[X] "
    print(f"{marca} {email:<32} {motivo}")
    return valido


def imprimir_senha(senha: str, mostrar: bool = False) -> None:
    """Imprime a nota, uma barra visual e as dicas de uma senha."""
    if not senha:
        print("[X]  senha vazia: nada para avaliar")
        return
    av = avaliar_senha(senha)
    exibida = senha if mostrar else mascarar(senha)
    cheios = av.pontos // 10
    barra = "#" * cheios + "." * (10 - cheios)
    print(f"{exibida:<30} [{barra}] {av.pontos:>3}/100  {av.nivel}")
    for dica in av.dicas:
        print(f"{'':30}  dica: {dica}")


def demo() -> None:
    """Avalia cinco e-mails e cinco senhas de exemplo."""
    print("=" * 64)
    print("Validador de e-mail e força de senha: demonstração")
    print("=" * 64)
    print("\nE-mails:\n")
    emails = ["ana.souza@exemplo.com.br", "joao@@exemplo.com",
              "maria silva@exemplo.com", "pedro@exemplo", "lia@sub.exemplo.org"]
    for email in emails:
        imprimir_email(email)
    print("\nSenhas (mostradas por inteiro só na demonstração):\n")
    senhas = ["123456", "gato", "Senha2024", "Tr3m-Azul!2024",
              "cavalo-bateria-grampo-correto"]
    for senha in senhas:
        imprimir_senha(senha, mostrar=True)
    print("\nA nota soma comprimento (até 40) e classes de símbolos (até 60),")
    print("e desconta sequências e repetições. Senhas vazadas valem 0.")


def construir_parser() -> argparse.ArgumentParser:
    """Define a linha de comando do programa."""
    parser = argparse.ArgumentParser(
        description="Valida e-mails e avalia a força de senhas.",
        epilog="Exemplo: python 12_validador_email_senha.py --email ana@exemplo.com --senha Abc123",
    )
    parser.add_argument("--email", nargs="+", metavar="EMAIL",
                        help="um ou mais e-mails para validar")
    parser.add_argument("--senha", nargs="+", metavar="SENHA",
                        help="uma ou mais senhas para avaliar")
    parser.add_argument("--mostrar", action="store_true",
                        help="imprime a senha inteira em vez de mascarar")
    parser.add_argument("--demo", action="store_true",
                        help="roda uma demonstração completa sem pedir nada")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: devolve 1 se algum e-mail for inválido."""
    argv = sys.argv[1:] if argv is None else argv
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.demo:
        demo()
        return 0
    if not args.email and not args.senha:
        parser.print_help()
        return 0
    tudo_ok = True
    for email in args.email or []:
        tudo_ok = imprimir_email(email) and tudo_ok
    for senha in args.senha or []:
        imprimir_senha(senha, args.mostrar)
    return 0 if tudo_ok else 1


if __name__ == "__main__":
    sys.exit(main())

# ------------------------------------------------------------
# Para ir além
#   1. Leia e-mails de um arquivo CSV e grave dois arquivos: válidos e
#      inválidos, com o motivo ao lado de cada um.
#   2. Calcule a entropia da senha em bits (tamanho vezes log2 do alfabeto)
#      e compare com a nota deste programa.
#   3. Troque as dicas por sugestões concretas: gere uma senha forte a
#      partir da fraca, trocando e acrescentando símbolos.
# ------------------------------------------------------------
