"""
comparar_spacy.py - Procesa el set con spaCy (es_core_news_sm) -> resultados/spacy_basico.json y spacy_rasgos.json

spaCy NO es un validador: siempre produce un análisis.  Para poder compararlo con nuestro parser
(que acepta/rechaza) definimos dos reglas de decisión explícitas:

  spacy_basico : acepta si el análisis tiene una raíz verbal (o predicado copulativo) con un sujeto (nsubj)
                 y ningún token etiquetado X/INTJ.   (= "spaCy casi siempre acepta")
  spacy_rasgos : spacy_basico + comprobación de concordancia con los rasgos morfológicos de spaCy
                 (Number/Gender entre det/amod y su núcleo; Number/Person entre nsubj y verbo;
                 Number/Gender entre sujeto y adjetivo predicativo).

Instalación:  pip install spacy && python -m spacy download es_core_news_sm
Uso:
  python comparar_spacy.py                    # modelo por defecto es_core_news_sm -> resultados/spacy_basico.json y spacy_rasgos.json
  python comparar_spacy.py es_core_news_md    # otro modelo -> resultados/spacy_modelos/es_core_news_md_{basico,rasgos}.json
Cambio: se añadió el argumento opcional del modelo para probar md/lg (comparar_modelos_spacy.py compara los tres). Con
cualquier modelo distinto del por defecto NO se tocan los archivos principales, así evaluar.py y el informe no cambian.
"""
import json, os, sys, time
import spacy

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO = sys.argv[1] if len(sys.argv) > 1 else "es_core_news_sm"
nlp = spacy.load(MODELO)


def feat(tok, k):
    v = tok.morph.get(k)
    return v[0] if v else None


def estructura(doc):
    """Devuelve (sujeto, verbo, objeto, tiene_estructura_basica)."""
    raiz = next((t for t in doc if t.dep_ == "ROOT"), None)
    if raiz is None:
        return None, None, None, False
    cop = next((c for c in raiz.children if c.dep_ == "cop"), None)
    verbo = cop if cop is not None else (raiz if raiz.pos_ in ("VERB", "AUX") else None)
    suj = next((c for c in raiz.children if c.dep_.startswith("nsubj")), None)
    obj = next((c for c in raiz.children if c.dep_ in ("obj", "dobj")), None)
    ok = verbo is not None and suj is not None and not any(t.pos_ in ("X", "INTJ") for t in doc)
    return suj, verbo, obj, ok


def concuerda(doc, suj, verbo, raiz_pred):
    """True si no se detecta ninguna discordancia con los rasgos de spaCy."""
    for t in doc:
        if t.dep_ in ("det", "amod") and t.head.pos_ in ("NOUN", "PROPN") and t.pos_ in ("DET", "ADJ"):
            for k in ("Number", "Gender"):
                a, b = feat(t, k), feat(t.head, k)
                if a and b and a != b:
                    return False
    if suj is not None and verbo is not None:
        n_s, n_v = feat(suj, "Number"), feat(verbo, "Number")
        if suj.pos_ == "PRON":
            p_s, p_v = feat(suj, "Person"), feat(verbo, "Person")
            if p_s and p_v and p_s != p_v:
                return False
        if n_s and n_v and n_s != n_v:
            return False
    if raiz_pred is not None and raiz_pred.pos_ == "ADJ" and suj is not None:
        for k in ("Number", "Gender"):
            a, b = feat(raiz_pred, k), feat(suj, k)
            if a and b and a != b:
                return False
    return True


def main():
    D = json.load(open(os.path.join(AQUI, "dataset.json"), encoding="utf-8"))
    basico, rasgos = [], []
    for d in D:
        t0 = time.perf_counter()
        doc = nlp(d["oracion"])
        ms = (time.perf_counter() - t0) * 1000
        suj, verbo, obj, ok = estructura(doc)
        raiz = next((t for t in doc if t.dep_ == "ROOT"), None)
        pred = raiz if (raiz is not None and any(c.dep_ == "cop" for c in raiz.children)) else None
        roles = dict(sujeto=suj.text.lower() if suj is not None else None,
                     verbo=verbo.text.lower() if verbo is not None else None,
                     objeto=obj.text.lower() if obj is not None else None)
        det = [dict(texto=t.text, pos=t.pos_, dep=t.dep_, cabeza=t.head.text, morph=str(t.morph)) for t in doc]
        basico.append(dict(id=d["id"], nivel=d["nivel"], pred_acepta=bool(ok), roles=roles, ms=ms, analisis=det))
        rasgos.append(dict(id=d["id"], nivel=d["nivel"], pred_acepta=bool(ok and concuerda(doc, suj, verbo, pred)),
                           roles=roles, ms=ms, analisis=det))
    if MODELO == "es_core_news_sm":
        carpeta, nombres = os.path.join(AQUI, "resultados"), ("spacy_basico", "spacy_rasgos")
    else:   # otros modelos: carpeta aparte para no mezclarlos con los sistemas principales de evaluar.py
        carpeta, nombres = os.path.join(AQUI, "resultados", "spacy_modelos"), (MODELO + "_basico", MODELO + "_rasgos")
    os.makedirs(carpeta, exist_ok=True)
    for nombre, datos in zip(nombres, (basico, rasgos)):
        json.dump(datos, open(os.path.join(carpeta, nombre + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[{MODELO}] guardado {os.path.relpath(carpeta, AQUI)}/{nombres[0]}.json y {nombres[1]}.json")


if __name__ == "__main__":
    main()
