"""Demo en vivo para la presentación.  Escribe una oración y se muestra estado, causa, árbol(es) y PNG.
Uso: python demo.py        (línea vacía para salir)     |     python demo.py "Ana come una manzana."
"""
import sys, os
from parser_es import procesar

AQUI = os.path.dirname(os.path.abspath(__file__))


def mostrar(o):
    r = procesar(o)
    print(f"\n  Estado: {r.estado}   (árboles sintácticos encontrados: {r.n_arboles})")
    for e in r.errores:
        print("   ✗", e)
    if r.arbol:
        print("   Árbol:", r.arbol)
        print("   Roles:", r.roles)
        ruta = os.path.join(AQUI, "arboles", "demo.png")
        r.arbol.guardar_png(ruta, o)
        print("   Imagen:", ruta)
        for i, a in enumerate(r.arboles[1:], 2):
            print(f"   Lectura alternativa {i}:", a)
    elif r.arboles:
        print("   (la estructura sintáctica existe, pero ninguna lectura concuerda) Árbol sin concordancia:")
        print("  ", r.arboles[0])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mostrar(" ".join(sys.argv[1:]))
    else:
        while True:
            o = input("\nOración> ").strip()
            if not o:
                break
            mostrar(o)
