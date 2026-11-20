"""
semantico.py - Analizador semántico (Fase 1) para MiniC.

Verifica lo que una gramática libre de contexto NO puede expresar:
  * toda variable usada debe estar declarada (dependencia entre dos
    apariciones arbitrariamente lejanas del mismo identificador: es el
    lenguaje {w ... w}, que no es libre de contexto),
  * no redeclarar en el mismo ámbito,
  * compatibilidad de tipos en asignaciones y expresiones,
  * ámbitos anidados mediante una pila de tablas de símbolos.

Como el parser de MiniC no es parte del proyecto, se trabaja sobre
"sentencias" (listas de tokens agrupadas por ; { }), tal como permite el
enunciado.  Los tipos de las expresiones se infieren con un pequeño
evaluador de tipos recursivo.
"""
import sys
from dataclasses import dataclass
from lexer import crear_lexer_minic, Token


@dataclass
class ErrorSemantico:
    mensaje: str
    linea: int

    def __str__(self):
        return f"[Error semántico] línea {self.linea}: {self.mensaje}"


class TablaSimbolos:
    """Pila de ámbitos: cada ámbito es un dict nombre -> (tipo, línea_decl)."""

    def __init__(self):
        self.ambitos = [{}]

    def entrar(self):
        self.ambitos.append({})

    def salir(self):
        self.ambitos.pop()

    def declarar(self, nombre, tipo, linea):
        if nombre in self.ambitos[-1]:
            return self.ambitos[-1][nombre][1]  # línea de la declaración previa
        self.ambitos[-1][nombre] = (tipo, linea)
        return None

    def buscar(self, nombre):
        for amb in reversed(self.ambitos):
            if nombre in amb:
                return amb[nombre][0]
        return None


NUMERICOS = {"int", "float"}


def compatible_asignacion(destino, origen):
    if destino == origen:
        return True
    return destino == "float" and origen == "int"  # ensanchamiento permitido


class ExprTipador:
    """Infiere el tipo de una lista de tokens de expresión.
    Precedencia: || < && < relacionales < + - < * / % < unarios < primarios.
    Devuelve el tipo ('int','float','bool','string') o None si hubo error."""

    def __init__(self, toks, tabla, errores):
        self.t, self.i, self.tabla, self.err = toks, 0, tabla, errores

    def _peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def _linea(self):
        return (self._peek() or self.t[-1]).linea

    def _tomar(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def tipo(self):
        if not self.t:
            return None
        r = self._or()
        if self.i < len(self.t):
            self.err.append(ErrorSemantico(
                f"expresión mal formada cerca de {self._peek().lexema!r}", self._peek().linea))
            return None
        return r

    def _binario(self, sub, tipos_op, regla):
        izq = sub()
        while self._peek() and self._peek().tipo in tipos_op:
            op = self._tomar()
            der = sub()
            izq = regla(izq, der, op)
        return izq

    def _or(self):
        return self._and()

    def _and(self):
        return self._binario(self._rel, {"OP_LOG"}, self._r_logica)

    def _rel(self):
        return self._binario(self._arit, {"OP_REL"}, self._r_rel)

    def _arit(self):
        izq = self._term()
        while self._peek() and self._peek().tipo == "OP_ARIT" and self._peek().lexema in "+-":
            op = self._tomar()
            izq = self._r_arit(izq, self._term(), op)
        return izq

    def _term(self):
        izq = self._unario()
        while self._peek() and self._peek().tipo == "OP_ARIT" and self._peek().lexema in "*/%":
            op = self._tomar()
            izq = self._r_arit(izq, self._unario(), op)
        return izq

    def _unario(self):
        p = self._peek()
        if p and p.tipo == "NOT":
            self._tomar()
            t = self._unario()
            if t is not None and t != "bool":
                self.err.append(ErrorSemantico(f"el operador '!' requiere bool, no {t}", p.linea))
                return None
            return t
        if p and p.tipo == "OP_ARIT" and p.lexema == "-":
            self._tomar()
            t = self._unario()
            if t is not None and t not in NUMERICOS:
                self.err.append(ErrorSemantico(f"el operador '-' unario requiere número, no {t}", p.linea))
                return None
            return t
        return self._primario()

    def _primario(self):
        p = self._peek()
        if p is None:
            self.err.append(ErrorSemantico("expresión incompleta", self.t[-1].linea))
            return None
        if p.tipo == "INT_LIT":
            self._tomar(); return "int"
        if p.tipo == "FLOAT_LIT":
            self._tomar(); return "float"
        if p.tipo == "BOOL_LIT":
            self._tomar(); return "bool"
        if p.tipo == "STRING_LIT":
            self._tomar(); return "string"
        if p.tipo == "ID":
            self._tomar()
            t = self.tabla.buscar(p.lexema)
            if t is None:
                self.err.append(ErrorSemantico(f"variable {p.lexema!r} usada sin declarar", p.linea))
            return t
        if p.tipo == "LPAREN":
            self._tomar()
            t = self._or()
            if self._peek() and self._peek().tipo == "RPAREN":
                self._tomar()
            else:
                self.err.append(ErrorSemantico("falta ')'", p.linea))
            return t
        self._tomar()
        self.err.append(ErrorSemantico(f"token inesperado {p.lexema!r} en expresión", p.linea))
        return None

    # --- reglas de tipos ---
    def _r_arit(self, a, b, op):
        if a is None or b is None:
            return None
        if op.lexema == "+" and a == "string" and b == "string":
            return "string"  # concatenación
        if a in NUMERICOS and b in NUMERICOS:
            return "float" if "float" in (a, b) else "int"
        self.err.append(ErrorSemantico(f"operación {a} {op.lexema} {b} no permitida", op.linea))
        return None

    def _r_rel(self, a, b, op):
        if a is None or b is None:
            return None
        if (a in NUMERICOS and b in NUMERICOS) or (a == b and op.lexema in ("==", "!=")):
            return "bool"
        self.err.append(ErrorSemantico(f"comparación {a} {op.lexema} {b} no permitida", op.linea))
        return None

    def _r_logica(self, a, b, op):
        if a is None or b is None:
            return None
        if a == b == "bool":
            return "bool"
        self.err.append(ErrorSemantico(f"operador {op.lexema} requiere bool, recibió {a} y {b}", op.linea))
        return None


def dividir_sentencias(tokens):
    """Agrupa tokens por sentencia.  Cada elemento: ('sent', [tokens]),
    ('abre', cabecera_tokens) para '{', o ('cierra', tok) para '}'."""
    res, actual = [], []
    for t in tokens:
        if t.tipo == "PUNTOYCOMA":
            res.append(("sent", actual)); actual = []
        elif t.tipo == "LBRACE":
            res.append(("abre", actual)); actual = []
        elif t.tipo == "RBRACE":
            if actual:
                res.append(("sent", actual)); actual = []
            res.append(("cierra", t))
        else:
            actual.append(t)
    if actual:
        res.append(("sent", actual))
    return res


def analizar(tokens):
    tabla, errores = TablaSimbolos(), []
    pila_bloques = []  # linea de cada '{' abierto
    sentencias = dividir_sentencias(tokens)
    for tipo, dato in sentencias:
        if tipo == "cierra":
            if len(tabla.ambitos) == 1:
                errores.append(ErrorSemantico("'}' sin '{' correspondiente", dato.linea))
            else:
                tabla.salir(); pila_bloques.pop()
            continue
        toks = dato
        if tipo == "abre":
            _cabecera(toks, tabla, errores)
            tabla.entrar()
            pila_bloques.append(toks[0].linea if toks else 0)
            continue
        if toks:
            _sentencia(toks, tabla, errores)
    for ln in pila_bloques:
        errores.append(ErrorSemantico("bloque '{' sin cerrar", ln))
    return errores, tabla


def _cabecera(toks, tabla, errores):
    """if (cond) / else / while (cond) {  -> la condición debe ser bool."""
    if not toks:
        return
    if toks[0].tipo in ("IF", "WHILE"):
        interior = toks[1:]
        if not (interior and interior[0].tipo == "LPAREN" and interior[-1].tipo == "RPAREN"):
            errores.append(ErrorSemantico(f"'{toks[0].lexema}' requiere condición entre paréntesis", toks[0].linea))
            return
        t = ExprTipador(interior[1:-1], tabla, errores).tipo()
        if t is not None and t != "bool":
            errores.append(ErrorSemantico(f"la condición de '{toks[0].lexema}' debe ser bool, no {t}", toks[0].linea))
    elif toks[0].tipo == "ELSE":
        pass
    else:
        errores.append(ErrorSemantico(f"bloque inesperado tras {toks[0].lexema!r}", toks[0].linea))


def _sentencia(toks, tabla, errores):
    p = toks[0]
    if p.tipo == "TIPO":  # declaración: tipo ID [= expr]
        if len(toks) < 2 or toks[1].tipo != "ID":
            errores.append(ErrorSemantico("declaración sin nombre de variable", p.linea)); return
        nombre, tipo_decl = toks[1].lexema, p.lexema
        prev = tabla.declarar(nombre, tipo_decl, p.linea)
        if prev is not None:
            errores.append(ErrorSemantico(
                f"redeclaración de {nombre!r} en el mismo ámbito (ya declarada en línea {prev})", p.linea))
        if len(toks) > 2:
            if toks[2].tipo != "ASIGNA":
                errores.append(ErrorSemantico("se esperaba '=' o ';' tras el nombre", p.linea)); return
            t = ExprTipador(toks[3:], tabla, errores).tipo()
            if t is not None and not compatible_asignacion(tipo_decl, t):
                errores.append(ErrorSemantico(f"no se puede asignar {t} a {nombre!r} de tipo {tipo_decl}", p.linea))
    elif p.tipo == "ID" and len(toks) > 1 and toks[1].tipo == "ASIGNA":  # asignación
        destino = tabla.buscar(p.lexema)
        t = ExprTipador(toks[2:], tabla, errores).tipo()
        if destino is None:
            errores.append(ErrorSemantico(f"variable {p.lexema!r} usada sin declarar", p.linea))
        elif t is not None and not compatible_asignacion(destino, t):
            errores.append(ErrorSemantico(f"no se puede asignar {t} a {p.lexema!r} de tipo {destino}", p.linea))
    elif p.tipo == "PRINT":
        ExprTipador(toks[1:], tabla, errores).tipo()
    else:
        errores.append(ErrorSemantico(f"sentencia no reconocida que empieza con {p.lexema!r}", p.linea))


def verificar_fuente(texto):
    """Lexer + semántico.  Devuelve (tokens, errores_lexicos, errores_semanticos)."""
    toks, elex = crear_lexer_minic().tokenizar(texto)
    if elex:  # como en un compilador real: con errores léxicos no se sigue (evita errores en cascada)
        return toks, elex, []
    esem, _ = analizar(toks)
    return toks, elex, esem


if __name__ == "__main__":
    # "utf-8-sig": ignora la marca BOM que añaden algunos editores y PowerShell 5.1; sin ella el BOM se reportaba como
    # un falso error léxico (carácter inválido '\ufeff') en la línea 1.
    fuente = open(sys.argv[1], encoding="utf-8-sig").read() if len(sys.argv) > 1 else sys.stdin.read()
    toks, elex, esem = verificar_fuente(fuente)
    for e in elex + esem:
        print(e)
    if not elex and not esem:
        print("OK: sin errores léxicos ni semánticos")
