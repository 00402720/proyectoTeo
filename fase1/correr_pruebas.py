"""Ejecuta todos los casos y compara con lo esperado.  Uso: python correr_pruebas.py [-v]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pruebas"))
from semantico import verificar_fuente
from casos import CASOS


def main(verbose=False):
    fallos = 0
    for nombre, codigo, esperados in CASOS:
        toks, elex, esem = verificar_fuente(codigo)
        obtenidos = [("lex", e.mensaje, e.linea) for e in elex] + [("sem", e.mensaje, e.linea) for e in esem]
        ok = len(obtenidos) == len(esperados) and all(
            o[0] == e[0] and e[1] in o[1] and o[2] == e[2] for o, e in zip(obtenidos, esperados))
        fallos += not ok
        print(("PASS " if ok else "FAIL ") + nombre)
        if verbose or not ok:
            for e in elex + esem:
                print("     ", e)
            if not ok:
                print("      esperado:", esperados)
    print(f"\n{len(CASOS) - fallos}/{len(CASOS)} casos correctos")
    return fallos


if __name__ == "__main__":
    sys.exit(1 if main("-v" in sys.argv) else 0)
