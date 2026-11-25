"""
lexer_es.py - Lexer del español.  Reutiliza la clase `Lexer` de la Fase 1 (fase1/lexer.py):
solo cambian las reglas (expresiones regulares) y se añade la consulta al lexicón.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fase1"))
from lexer import Lexer  # noqa: E402  (reutilización de la Fase 1)
from lexico import analizar_palabra  # noqa: E402

REGLAS_ES = [
    ("_ESPACIO", r"\s+"),
    ("PALABRA", r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+"),
    ("ERR_NUM", r"\d+"),
    ("PUNTO", r"\."),
    ("COMA", r","),
    ("INTERR", r"[¿?]"),
    ("EXCL", r"[¡!]"),
]
_LEXER = Lexer(REGLAS_ES)


def tokenizar_es(texto):
    """Devuelve (lista de (palabra, analisis, token), lista de errores léxicos como str)."""
    toks, errs = _LEXER.tokenizar(texto)
    errores = [str(e).replace("literal numérico mal formado", "números no soportados") for e in errs]
    salida = []
    for t in toks:
        if t.tipo == "PALABRA":
            an = analizar_palabra(t.lexema)
            if not an:
                errores.append(f"[Error léxico] línea {t.linea}, col {t.columna}: palabra fuera del vocabulario {t.lexema!r}")
            salida.append((t.lexema, an, t))
        else:
            salida.append((t.lexema, [{"cat": "Punt", "lemma": t.lexema}], t))
    return salida, errores
