"""Verifica el parser frente a la etiqueta `en_gramatica` y los roles esperados (correctitud técnica).
Uso: python verificar_parser.py   -> imprime las discrepancias (el parser debería coincidir salvo límites conocidos)."""
import json, os
from parser_es import procesar

D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.json"), encoding="utf-8"))
mal = 0
for d in D:
    r = procesar(d["oracion"])
    roles_ok = (not (r.aceptada and d["en_gramatica"] and d["sujeto"])) or \
        (r.roles["sujeto"], r.roles["verbo"], r.roles["objeto"]) == (d["sujeto"], d["verbo"], d["objeto"])
    if r.aceptada != d["en_gramatica"] or not roles_ok:
        mal += 1
        print(f"DISCREPANCIA [{d['fenomeno']}] {d['oracion']} -> {r.estado}")
print(f"\n{len(D) - mal}/{len(D)} oraciones coinciden con la verdad de referencia del parser")
