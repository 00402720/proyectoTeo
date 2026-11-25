"""Corre el parser propio sobre dataset.json -> resultados/parser.json y árboles PNG/DOT.
Uso: python correr_parser.py [--arboles]"""
import json, os, sys, time
from parser_es import procesar

AQUI = os.path.dirname(os.path.abspath(__file__))


def main(dibujar):
    D = json.load(open(os.path.join(AQUI, "dataset.json"), encoding="utf-8"))
    salida = []
    for d in D:
        t0 = time.perf_counter()
        r = procesar(d["oracion"])
        ms = (time.perf_counter() - t0) * 1000
        salida.append(dict(id=d["id"], nivel=d["nivel"], pred_acepta=r.aceptada, estado=r.estado,
                           n_arboles=r.n_arboles, roles=r.roles, errores=r.errores, ms=ms,
                           arbol=r.arbol.corchetes() if r.arbol else None))
        if dibujar and r.arbol:
            os.makedirs(os.path.join(AQUI, "arboles"), exist_ok=True)
            r.arbol.guardar_png(os.path.join(AQUI, "arboles", f"oracion_{d['id']:02d}.png"), d["oracion"])
            open(os.path.join(AQUI, "arboles", f"oracion_{d['id']:02d}.dot"), "w").write(r.arbol.a_dot())
    os.makedirs(os.path.join(AQUI, "resultados"), exist_ok=True)
    json.dump(salida, open(os.path.join(AQUI, "resultados", "parser.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"{len(salida)} oraciones procesadas -> resultados/parser.json")
    from collections import Counter
    print(Counter(s["estado"] for s in salida))


if __name__ == "__main__":
    main("--arboles" in sys.argv)
