"""
parser_es.py - Parser descendente recursivo CON BACKTRACKING para el subconjunto del español.

Cada función `p_X(pos)` devuelve TODAS las formas de reconocer la categoría X desde la posición
`pos`: una lista de (árbol, nueva_posición).  Así el parser enumera todos los árboles posibles,
lo que permite medir la ambigüedad estructural (p. ej. adjunción de un SP al verbo o al sustantivo).
Se usa en lugar de LL(1) porque la gramática del español no es LL(1): hay prefijos comunes y
ambigüedad real (documentado en el informe).

Uso:   python parser_es.py "Ana come una manzana roja."  [--png salida.png]
"""
import sys
from dataclasses import dataclass, field
from lexer_es import tokenizar_es
from arbol import Arbol
import concordancia

MAX_ARBOLES = 200


@dataclass
class Resultado:
    oracion: str
    estado: str                       # ACEPTADA | RECHAZADA_LEXICO | RECHAZADA_SINTAXIS | RECHAZADA_CONCORDANCIA
    errores: list = field(default_factory=list)
    arboles: list = field(default_factory=list)   # todos los árboles sintácticos
    arbol: Arbol = None               # árbol elegido (el primero que concuerda)
    roles: dict = None                # sujeto / verbo / objeto del árbol elegido

    @property
    def aceptada(self):
        return self.estado == "ACEPTADA"

    @property
    def n_arboles(self):
        return len(self.arboles)


class Parser:
    def __init__(self, toks):
        self.toks = toks
        self.n = len(toks)
        self.max_pos = 0  # posición más lejana alcanzada (para mensajes de error)

    # ---------- terminales
    def hoja(self, pos, cat, filtro=None):
        if pos >= self.n:
            return None
        palabra, analisis, _ = self.toks[pos]
        an = [a for a in analisis if a["cat"] == cat and (filtro is None or filtro(a))]
        if not an:
            return None
        self.max_pos = max(self.max_pos, pos + 1)
        return Arbol(cat, [palabra], an)

    # ---------- SAdj, SP, SN
    def p_sadj(self, pos, pre=False):
        filtro = (lambda a: a.get("pre")) if pre else None
        res = []
        h = self.hoja(pos, "Adj", filtro)
        if h:
            res.append((Arbol("SAdj", [h]), pos + 1))
        g = self.hoja(pos, "AdvGrado")
        if g:
            h = self.hoja(pos + 1, "Adj", filtro)
            if h:
                res.append((Arbol("SAdj", [g, h]), pos + 2))
        return res

    def seq_adjs(self, pos, pre):
        """0 o más adjetivos (todas las longitudes posibles)."""
        res = [([], pos)]
        frontera = [([], pos)]
        while frontera:
            nueva = []
            for nodos, p in frontera:
                for adj, q in self.p_sadj(p, pre):
                    nueva.append((nodos + [adj], q))
            res.extend(nueva)
            frontera = nueva
        return res

    def p_sp(self, pos):
        prep = self.hoja(pos, "Prep")
        if not prep:
            return []
        return [(Arbol("SP", [prep, sn]), q) for sn, q in self.p_sn(pos + 1, bare_ok=True)]

    def p_sn(self, pos, bare_ok):
        bases = []
        for cat in ("Pron", "NProp"):
            h = self.hoja(pos, cat)
            if h:
                bases.append((Arbol("SN", [h]), pos + 1, False))  # False = no admite SP
        det = self.hoja(pos, "Det")
        if det:
            for pres, p1 in self.seq_adjs(pos + 1, pre=True):
                n = self.hoja(p1, "N")
                if n:
                    for posts, p2 in self.seq_adjs(p1 + 1, pre=False):
                        bases.append((Arbol("SN", [det] + pres + [n] + posts), p2, True))
        if bare_ok:
            n = self.hoja(pos, "N")
            if n:
                for posts, p2 in self.seq_adjs(pos + 1, pre=False):
                    bases.append((Arbol("SN", [n] + posts), p2, True))
        res = [(a, p) for a, p, _ in bases]
        # SN -> SN SP  (adjunción al sustantivo; iterativo para evitar recursión por la izquierda)
        frontera = [(a, p) for a, p, ext in bases if ext]
        while frontera:
            nueva = []
            for a, p in frontera:
                for sp, q in self.p_sp(p):
                    nueva.append((Arbol("SN", [a, sp]), q))
            res.extend(nueva)
            frontera = nueva
            if len(res) > 400:
                break
        return res

    # ---------- SV
    def p_mods(self, pos):
        """Mod* donde Mod -> SP | Adv."""
        res = [([], pos)]
        frontera = [([], pos)]
        while frontera:
            nueva = []
            for nodos, p in frontera:
                for sp, q in self.p_sp(p):
                    nueva.append((nodos + [sp], q))
                a = self.hoja(p, "Adv")
                if a:
                    nueva.append((nodos + [a], p + 1))
            res.extend(nueva)
            frontera = nueva
            if len(res) > 400:
                break
        return res

    def p_sv(self, pos):
        pre = [([], pos)]
        neg = self.hoja(pos, "Neg")
        if neg:
            pre.append(([neg], pos + 1))
        for nodos, p in list(pre):
            adv = self.hoja(p, "Adv")
            if adv:
                pre.append((nodos + [adv], p + 1))
        res = []
        for nodos, p in pre:
            vhoja = self.hoja(p, "V")
            if not vhoja:
                continue
            tipos = {a["trans"] for a in vhoja.analisis}
            q = p + 1
            marcos = []  # lista de (nodos_complemento, pos)
            if tipos & {"tr", "both"}:
                marcos += [([sn], r) for sn, r in self.p_sn(q, bare_ok=True)]
            if tipos & {"intr", "both"}:
                marcos.append(([], q))
            if "cop" in tipos:
                marcos += [([sa], r) for sa, r in self.p_sadj(q)]
                marcos += [([sp], r) for sp, r in self.p_sp(q)]
            # 'comp' (decir, querer...) no tiene regla: no genera marcos
            for comp, r in marcos:
                for mods, s in self.p_mods(r):
                    res.append((Arbol("SV", nodos + [vhoja] + comp + mods), s))
        return res

    # ---------- O
    def p_o(self):
        res = []
        inicios = [([], 0)]
        adv = self.hoja(0, "Adv")
        if adv:
            inicios.append(([Arbol("SAdv", [adv])], 1))
        for nodos, p in inicios:
            for sn, q in self.p_sn(p, bare_ok=False):
                for sv, r in self.p_sv(q):
                    if r == self.n:
                        res.append(Arbol("O", nodos + [sn, sv]))
        return res


def extraer_roles(arbol):
    sn = next(h for h in arbol.hijos if h.etiqueta == "SN")
    sv = next(h for h in arbol.hijos if h.etiqueta == "SV")
    nuc = concordancia.hoja_nucleo(concordancia.cabeza(sn))
    verbo = next(h for h in sv.hijos if h.etiqueta == "V")
    objeto = None
    vistos_v = False
    for h in sv.hijos:
        if h is verbo:
            vistos_v = True
        elif vistos_v and h.etiqueta == "SN":
            o = concordancia.hoja_nucleo(concordancia.cabeza(h))
            objeto = o.palabra.lower()
            break
    return {"sujeto": nuc.palabra.lower(), "verbo": verbo.palabra.lower(), "objeto": objeto}


def procesar(oracion):
    toks, errores = tokenizar_es(oracion)
    if errores:
        return Resultado(oracion, "RECHAZADA_LEXICO", errores)
    # quitar punto final; otros signos (¿ ? ¡ ! , y puntos intermedios) quedan y fallan en la sintaxis
    if toks and toks[-1][2].tipo == "PUNTO":
        toks = toks[:-1]
    if not toks:
        return Resultado(oracion, "RECHAZADA_SINTAXIS", ["oración vacía"])
    p = Parser(toks)
    arboles = p.p_o()[:MAX_ARBOLES]
    if not arboles:
        fallo = toks[min(p.max_pos, len(toks) - 1)][0]
        return Resultado(oracion, "RECHAZADA_SINTAXIS",
                         [f"la gramática no puede analizar la oración (bloqueo cerca de {fallo!r})"])
    errores_por_arbol = [concordancia.verificar(a) for a in arboles]
    for a, e in zip(arboles, errores_por_arbol):
        if not e:
            return Resultado(oracion, "ACEPTADA", [], arboles, a, extraer_roles(a))
    return Resultado(oracion, "RECHAZADA_CONCORDANCIA", errores_por_arbol[0], arboles)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    r = procesar(sys.argv[1])
    print(f"Oración: {r.oracion}\nEstado : {r.estado}   (árboles sintácticos: {r.n_arboles})")
    for e in r.errores:
        print("  -", e)
    if r.arbol:
        print("Árbol  :", r.arbol)
        print("Roles  :", r.roles)
        if "--png" in sys.argv:
            ruta = sys.argv[sys.argv.index("--png") + 1]
            r.arbol.guardar_png(ruta, r.oracion)
            print("PNG guardado en", ruta)
