"""
comparar_hf.py - Aceptabilidad con HuggingFace Transformers -> resultados/hf_pll.json

Un modelo enmascarado (BETO, BERT en español) no produce árboles: se usa su "pseudo-log-verosimilitud"
(PLL, Salazar et al. 2020) como medida de naturalidad: se enmascara cada token y se suma log P(token | resto).
Regla de decisión (SIN usar las etiquetas de validez del conjunto):
   umbral = percentil 10 del PLL/token de las oraciones del Nivel 1 (todas simples y válidas)
   acepta  = PLL/token >= umbral
Se guarda también el puntaje por oración para poder probar otros umbrales.

Instalación:  pip install transformers torch
Ejecución  :  python comparar_hf.py [nombre_modelo]      (por defecto dccuchile/bert-base-spanish-wwm-cased)
"""
import json, os, sys, time
# Cambio: en Windows el backend Xet de huggingface_hub dejó la descarga de los pesos en 0 bytes indefinidamente.
# Se desactiva (descarga HTTP normal) ANTES de importar transformers.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
import numpy as np
import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO = sys.argv[1] if len(sys.argv) > 1 else "dccuchile/bert-base-spanish-wwm-cased"


def pll_por_token(oracion, tok, modelo):
    ids = tok(oracion, return_tensors="pt")["input_ids"][0]
    n = len(ids)
    if n <= 2:
        return 0.0
    lotes = ids.repeat(n - 2, 1)
    for j in range(1, n - 1):                       # enmascara cada token real (no [CLS]/[SEP])
        lotes[j - 1, j] = tok.mask_token_id
    with torch.no_grad():
        logits = modelo(lotes).logits
    logp = torch.log_softmax(logits, dim=-1)
    total = sum(logp[j - 1, j, ids[j]].item() for j in range(1, n - 1))
    return total / (n - 2)


def main():
    tok = AutoTokenizer.from_pretrained(MODELO)
    modelo = AutoModelForMaskedLM.from_pretrained(MODELO).eval()
    D = json.load(open(os.path.join(AQUI, "dataset.json"), encoding="utf-8"))
    puntajes, tiempos = {}, {}
    for d in D:
        t0 = time.perf_counter()
        puntajes[d["id"]] = pll_por_token(d["oracion"], tok, modelo)
        tiempos[d["id"]] = (time.perf_counter() - t0) * 1000
    umbral = float(np.percentile([puntajes[d["id"]] for d in D if d["nivel"] == 1], 10))
    salida = [dict(id=d["id"], nivel=d["nivel"], pred_acepta=bool(puntajes[d["id"]] >= umbral),
                   puntaje=puntajes[d["id"]], umbral=umbral, ms=tiempos[d["id"]], roles=None) for d in D]
    json.dump(salida, open(os.path.join(AQUI, "resultados", "hf_pll.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"modelo={MODELO} umbral={umbral:.3f} aceptadas={sum(s['pred_acepta'] for s in salida)}/{len(salida)}")


if __name__ == "__main__":
    main()
