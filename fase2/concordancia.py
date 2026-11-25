"""
concordancia.py - Verificador de concordancia (capa "semántica" del español).

La CFG de gramatica.py ignora género, número y persona.  Comprobarlos exige
comparar rasgos de nodos arbitrariamente lejanos del árbol (p. ej. el sujeto
con el verbo o con un adjetivo predicativo): es una restricción sensible al
contexto.  Aquí se hace sobre el árbol ya construido, igual que el analizador
semántico de la Fase 1 hace con los tipos de las variables.
"""
NOM_GEN = {"m": "masc.", "f": "fem."}
NOM_NUM = {"s": "sing.", "p": "plural"}


def pares(analisis_lista):
    """Conjunto de (género, número) compatibles con una lista de análisis."""
    res = set()
    for a in analisis_lista:
        gens = ("m", "f") if a.get("gen") in (None, "c") else (a["gen"],)
        for g in gens:
            res.add((g, a["num"]))
    return res


def describir(pp):
    return " / ".join(sorted(f"{NOM_GEN[g]} {NOM_NUM[n]}" for g, n in pp))


def cabeza(sn):
    while isinstance(sn.hijos[0], type(sn)) and sn.hijos[0].etiqueta == "SN":
        sn = sn.hijos[0]
    return sn


def hoja_nucleo(sn_base):
    """Hoja (N, NProp o Pron) que es el núcleo de un SN base."""
    for h in sn_base.hijos:
        if h.es_preterminal() and h.etiqueta in ("N", "NProp", "Pron"):
            return h
    return None


def verificar(arbol):
    """Devuelve la lista de errores de concordancia (vacía si todo concuerda)."""
    errores = []

    # 1) concordancia interna de cada SN: Det - N - Adj
    for nodo in arbol.recorrer():
        if nodo.etiqueta != "SN" or nodo.hijos[0].etiqueta == "SN":
            continue
        nuc = hoja_nucleo(nodo)
        if nuc is None or nuc.etiqueta != "N":
            continue
        pn = pares(nuc.analisis)
        for h in nodo.hojas():
            if h.etiqueta in ("Det", "Adj"):
                px = pares(h.analisis)
                if not (px & pn):
                    errores.append(f"{h.etiqueta} '{h.palabra}' ({describir(px)}) no concuerda con "
                                   f"el sustantivo '{nuc.palabra}' ({describir(pn)})")

    # 2) concordancia sujeto - verbo y sujeto - adjetivo predicativo
    sujeto = next((h for h in arbol.hijos if h.etiqueta == "SN"), None)
    sv = next((h for h in arbol.hijos if h.etiqueta == "SV"), None)
    if sujeto is None or sv is None:
        return errores
    base = cabeza(sujeto)
    nuc = hoja_nucleo(base)
    if nuc.etiqueta == "Pron":
        opciones = {(a["pers"], a["num"]) for a in nuc.analisis}
    else:
        opciones = {(3, a["num"]) for a in nuc.analisis}
    p_suj = pares(nuc.analisis)
    verbo = next(h for h in sv.hijos if h.etiqueta == "V")
    if not any((a["pers"], a["num"]) in opciones for a in verbo.analisis):
        desc_v = ", ".join(sorted({f"{a['pers']}ª pers. {NOM_NUM[a['num']]}" for a in verbo.analisis}))
        desc_s = ", ".join(sorted({f"{p}ª pers. {NOM_NUM[n]}" for p, n in opciones}))
        errores.append(f"el verbo '{verbo.palabra}' ({desc_v}) no concuerda con el sujeto "
                       f"'{nuc.palabra}' ({desc_s})")
    pred = next((h for h in sv.hijos if h.etiqueta == "SAdj"), None)
    if pred is not None:
        adj = next(h for h in pred.hojas() if h.etiqueta == "Adj")
        pa = pares(adj.analisis)
        if not (pa & p_suj):
            errores.append(f"el adjetivo predicativo '{adj.palabra}' ({describir(pa)}) no concuerda con el "
                           f"sujeto '{nuc.palabra}' ({describir(p_suj)})")
    return errores
