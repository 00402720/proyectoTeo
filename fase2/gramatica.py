"""
gramatica.py - Especificación formal de la CFG del subconjunto del español.

El texto GRAMATICA se usa (a) como documentación y (b) como parte del prompt
del experimento con el LLM (llm_experimento.py).  La implementación en
parser_es.py sigue estas producciones una por una.

Terminales: categorías léxicas (Det, N, NProp, Pron, Adj, Adv, AdvGrado, Neg, Prep, V_*).
Los verbos se subdividen por subcategorización (V_tr, V_intr, V_cop) porque una CFG
solo puede expresar transitividad separando categorías.
IMPORTANTE: la gramática es una CFG pura: NO verifica concordancia de género, número ni
persona (esos rasgos se comprueban después en concordancia.py).
"""

GRAMATICA = r"""
O      -> SAdv_ini SN_suj SV | SN_suj SV
SAdv_ini -> Adv
SN_suj -> SN_nuc | SN_suj SP
SN     -> SN_nuc | SN_bare | SN SP
SN_nuc -> Pron | NProp | Det SAdjPre* N SAdj*
SN_bare-> N SAdj*                       (solo como complemento: "come manzanas")
SAdjPre-> Adj_pre                       (adjetivos antepuestos: grande, pequeño, bonito, nuevo, viejo)
SAdj   -> Adj | AdvGrado Adj
SP     -> Prep SN
SV     -> Neg? Adv? V_tr  SN   Mod*
       |  Neg? Adv? V_intr    Mod*
       |  Neg? Adv? V_tr_o_intr (con o sin SN)
       |  Neg? Adv? V_cop (SAdj | SP) Mod*
Mod    -> SP | Adv
Tiempos: presente y pretérito perfecto simple (indicativo), 6 personas.
Categorías: Det Adv AdvGrado Neg Prep N NProp Pron Adj V (con rasgos).
"""

# Fenómenos que la gramática NO cubre (por diseño): oraciones subordinadas y relativas
# (que...), coordinación (y, o, pero), clíticos (la compró), sujeto omitido (pro-drop),
# interrogativas (¿...?), complementos infinitivos (quiere comer), adverbio entre
# verbo y objeto.
