"""
lexer.py - Analizador léxico (Fase 1).

Un lexer implementa un lenguaje REGULAR (nivel 3 de la jerarquía de Chomsky):
cada token se describe con una expresión regular (equivalente a un AFD).

La clase `Lexer` es genérica (recibe una lista de reglas), de modo que la
Fase 2 la reutiliza para el español.  Aquí se define además el lenguaje
elegido para la Fase 1: "MiniC", un subconjunto de C con
  - tipos: int, float, bool, string
  - sentencias: declaración, asignación, if/else, while, print, bloques { }
  - operadores aritméticos, relacionales y lógicos.
"""
import re
import sys
from dataclasses import dataclass


@dataclass
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int

    def __repr__(self):
        return f"Token({self.tipo}, {self.lexema!r}, {self.linea}:{self.columna})"


@dataclass
class ErrorLexico:
    mensaje: str
    linea: int
    columna: int

    def __str__(self):
        return f"[Error léxico] línea {self.linea}, col {self.columna}: {self.mensaje}"


class Lexer:
    """Lexer basado en una lista ordenada de reglas (tipo, regex).

    El orden importa: se usa la primera regla que coincide (las reglas de
    error por literal mal formado van ANTES de las genéricas).
    Los tipos que empiezan con '_' se descartan (espacios, comentarios).
    Los tipos que empiezan con 'ERR_' producen un error léxico.
    """

    def __init__(self, reglas, palabras_reservadas=None):
        self.reglas = [(t, re.compile(p, re.DOTALL)) for t, p in reglas]
        self.reservadas = palabras_reservadas or {}

    def tokenizar(self, texto):
        tokens, errores = [], []
        pos, linea, col_inicio_linea = 0, 1, 0
        while pos < len(texto):
            for tipo, rx in self.reglas:
                m = rx.match(texto, pos)
                if m and m.end() > pos:
                    lex = m.group(0)
                    col = pos - col_inicio_linea + 1
                    if tipo.startswith("ERR_"):
                        errores.append(ErrorLexico(self._msg(tipo, lex), linea, col))
                    elif not tipo.startswith("_"):
                        if tipo == "ID" and lex in self.reservadas:
                            tipo = self.reservadas[lex]
                        tokens.append(Token(tipo, lex, linea, col))
                    saltos = lex.count("\n")
                    if saltos:
                        linea += saltos
                        col_inicio_linea = pos + lex.rfind("\n") + 1
                    pos = m.end()
                    break
            else:  # ninguna regla coincidió -> carácter inválido
                col = pos - col_inicio_linea + 1
                errores.append(ErrorLexico(f"carácter inválido {texto[pos]!r}", linea, col))
                pos += 1
        return tokens, errores

    @staticmethod
    def _msg(tipo, lex):
        return {
            "ERR_STRING": f"cadena sin cerrar {lex!r}",
            "ERR_NUM": f"literal numérico mal formado {lex!r}",
            "ERR_COMENT": "comentario de bloque sin cerrar",
        }.get(tipo, f"error léxico {lex!r}")


# ---------------------------------------------------------------- MiniC ----
RESERVADAS_MINIC = {
    "int": "TIPO", "float": "TIPO", "bool": "TIPO", "string": "TIPO",
    "if": "IF", "else": "ELSE", "while": "WHILE", "print": "PRINT",
    "true": "BOOL_LIT", "false": "BOOL_LIT",
}

REGLAS_MINIC = [
    ("_ESPACIO", r"[ \t\r\n]+"),
    ("_COMENT_LINEA", r"//[^\n]*"),
    ("_COMENT_BLOQUE", r"/\*.*?\*/"),
    ("ERR_COMENT", r"/\*.*"),                          # /* sin cierre (hasta el fin)
    ("ERR_NUM", r"\d+\.\d*\.[\d.]*|\d+[A-Za-z_]\w*"),  # 1.2.3  o  12abc
    ("FLOAT_LIT", r"\d+\.\d+"),
    ("INT_LIT", r"\d+"),
    ("STRING_LIT", r'"[^"\n]*"'),
    ("ERR_STRING", r'"[^"\n]*'),                       # comilla sin cerrar
    ("ID", r"[A-Za-z_][A-Za-z_0-9]*"),
    ("OP_REL", r"==|!=|<=|>=|<|>"),
    ("OP_LOG", r"&&|\|\|"),
    ("ASIGNA", r"="),
    ("OP_ARIT", r"[+\-*/%]"),
    ("NOT", r"!"),
    ("LPAREN", r"\("), ("RPAREN", r"\)"),
    ("LBRACE", r"\{"), ("RBRACE", r"\}"),
    ("PUNTOYCOMA", r";"),
]


def crear_lexer_minic():
    return Lexer(REGLAS_MINIC, RESERVADAS_MINIC)


if __name__ == "__main__":
    # "utf-8-sig": ignora la marca BOM que añaden algunos editores y PowerShell 5.1; sin ella el BOM se reportaba como
    # un falso error léxico (carácter inválido '\ufeff') en la línea 1.
    fuente = open(sys.argv[1], encoding="utf-8-sig").read() if len(sys.argv) > 1 else sys.stdin.read()
    toks, errs = crear_lexer_minic().tokenizar(fuente)
    for t in toks:
        print(t)
    for e in errs:
        print(e)
    print(f"\n{len(toks)} tokens, {len(errs)} errores léxicos")
