"""
lexico.py - Lexicón del español (vocabulario reducido y controlado).

Mapea cada forma de superficie a una LISTA de análisis (hay ambigüedad
léxica: 'la' es determinante y clítico; 'canta' podría ser otra cosa en un
lexicón mayor; 'vivimos' es presente y pretérito a la vez).

Cada análisis es un dict con:
  cat   : Det, N, NProp, Pron, Adj, Adv, AdvGrado, Neg, Prep, V, Inf, Clit, Conj, Rel, Punt
  gen   : 'm' | 'f' | 'c' (común: sirve para ambos) | None (sin género: invariable)
  num   : 's' | 'p'
  pers  : 1 | 2 | 3 (verbos y pronombres)
  tiempo: 'pres' | 'pret' (verbos)
  trans : 'tr' | 'intr' | 'both' | 'cop' | 'comp' (subcategorización del verbo)
  pre   : True si el adjetivo puede ir antepuesto al sustantivo
"""
from collections import defaultdict

LEX = defaultdict(list)


def _add(forma, **rasgos):
    LEX[forma.lower()].append(rasgos)


# ------------------------------------------------------------ sustantivos
SUSTANTIVOS = [
    ("niño", "niños", "m"), ("niña", "niñas", "f"), ("perro", "perros", "m"), ("perra", "perras", "f"),
    ("gato", "gatos", "m"), ("gata", "gatas", "f"), ("libro", "libros", "m"), ("casa", "casas", "f"),
    ("mesa", "mesas", "f"), ("profesor", "profesores", "m"), ("profesora", "profesoras", "f"),
    ("estudiante", "estudiantes", "c"), ("manzana", "manzanas", "f"), ("pan", "panes", "m"),
    ("carta", "cartas", "f"), ("pelota", "pelotas", "f"), ("parque", "parques", "m"),
    ("jardín", "jardines", "m"), ("escuela", "escuelas", "f"), ("ciudad", "ciudades", "f"),
    ("mujer", "mujeres", "f"), ("hombre", "hombres", "m"), ("amigo", "amigos", "m"),
    ("amiga", "amigas", "f"), ("maestro", "maestros", "m"), ("maestra", "maestras", "f"),
    ("pájaro", "pájaros", "m"), ("flor", "flores", "f"), ("canción", "canciones", "f"),
    ("coche", "coches", "m"), ("ventana", "ventanas", "f"), ("queso", "quesos", "m"),
    ("leche", "leches", "f"), ("pescado", "pescados", "m"), ("médico", "médicos", "m"),
    ("médica", "médicas", "f"), ("cocinero", "cocineros", "m"), ("cocinera", "cocineras", "f"),
    ("música", "músicas", "f"), ("telescopio", "telescopios", "m"), ("playa", "playas", "f"),
    ("río", "ríos", "m"), ("montaña", "montañas", "f"), ("mercado", "mercados", "m"),
    ("vecino", "vecinos", "m"), ("vecina", "vecinas", "f"), ("película", "películas", "f"),
    ("historia", "historias", "f"), ("examen", "exámenes", "m"), ("tarea", "tareas", "f"),
    ("regalo", "regalos", "m"), ("pastel", "pasteles", "m"), ("sopa", "sopas", "f"),
]
for s, p, g in SUSTANTIVOS:
    _add(s, cat="N", lemma=s, gen=g, num="s")
    _add(p, cat="N", lemma=s, gen=g, num="p")

NOMBRES_PROPIOS = [("Ana", "f"), ("Luis", "m"), ("María", "f"), ("Carlos", "m"), ("Pedro", "m"),
                   ("Sofía", "f"), ("Lucía", "f"), ("Miguel", "m"), ("Elena", "f"), ("Juan", "m")]
for n, g in NOMBRES_PROPIOS:
    _add(n, cat="NProp", lemma=n, gen=g, num="s", pers=3)

# ------------------------------------------------------------ determinantes
DETERMINANTES = {
    "el": ("m", "s"), "la": ("f", "s"), "los": ("m", "p"), "las": ("f", "p"),
    "un": ("m", "s"), "una": ("f", "s"), "unos": ("m", "p"), "unas": ("f", "p"),
    "este": ("m", "s"), "esta": ("f", "s"), "estos": ("m", "p"), "estas": ("f", "p"),
    "ese": ("m", "s"), "esa": ("f", "s"), "esos": ("m", "p"), "esas": ("f", "p"),
    "mi": (None, "s"), "mis": (None, "p"), "tu": (None, "s"), "tus": (None, "p"),
    "su": (None, "s"), "sus": (None, "p"),
}
for f, (g, n) in DETERMINANTES.items():
    _add(f, cat="Det", lemma=f, gen=g, num=n)

# ------------------------------------------------------------ pronombres
PRONOMBRES = {
    "yo": (None, "s", 1), "tú": (None, "s", 2), "él": ("m", "s", 3), "ella": ("f", "s", 3),
    "usted": (None, "s", 3), "nosotros": ("m", "p", 1), "nosotras": ("f", "p", 1),
    "vosotros": ("m", "p", 2), "vosotras": ("f", "p", 2), "ellos": ("m", "p", 3),
    "ellas": ("f", "p", 3), "ustedes": (None, "p", 3),
}
for f, (g, n, p) in PRONOMBRES.items():
    _add(f, cat="Pron", lemma=f, gen=g, num=n, pers=p)
for c in ["lo", "la", "los", "las", "le", "les", "se", "me", "te", "nos"]:
    _add(c, cat="Clit", lemma=c)

# ------------------------------------------------------------ adjetivos
ADJ_O = [("pequeño", True), ("rojo", False), ("bonito", True), ("viejo", True), ("nuevo", True),
         ("blanco", False), ("negro", False), ("cansado", False), ("rápido", False), ("lento", False),
         ("alto", False), ("simpático", False), ("hambriento", False), ("tranquilo", False),
         ("ocupado", False), ("contento", False), ("enfermo", False), ("limpio", False),
         ("sucio", False), ("delicioso", False)]
ADJ_E = [("grande", "grandes", True), ("verde", "verdes", False), ("inteligente", "inteligentes", False),
         ("amable", "amables", False), ("interesante", "interesantes", False),
         ("difícil", "difíciles", False), ("fácil", "fáciles", False), ("joven", "jóvenes", False),
         ("feliz", "felices", False), ("azul", "azules", False), ("caliente", "calientes", False)]
for base, pre in ADJ_O:
    r = base[:-1]
    for suf, g, n in [("o", "m", "s"), ("a", "f", "s"), ("os", "m", "p"), ("as", "f", "p")]:
        _add(r + suf, cat="Adj", lemma=base, gen=g, num=n, pre=pre)
for s, p, pre in ADJ_E:
    _add(s, cat="Adj", lemma=s, gen=None, num="s", pre=pre)
    _add(p, cat="Adj", lemma=s, gen=None, num="p", pre=pre)

# ------------------------------------------------------------ adverbios, etc.
for a in ["rápidamente", "lentamente", "ayer", "hoy", "siempre", "bien", "mal", "ahora", "aquí",
          "allí", "mucho", "temprano", "claramente", "tranquilamente"]:
    _add(a, cat="Adv", lemma=a)
_add("muy", cat="AdvGrado", lemma="muy")
_add("no", cat="Neg", lemma="no")
for p in ["a", "en", "con", "de", "para", "sobre", "por", "sin", "hacia", "desde", "entre"]:
    _add(p, cat="Prep", lemma=p)
for c in ["y", "o", "pero", "porque", "cuando", "si", "aunque"]:
    _add(c, cat="Conj", lemma=c)
for r in ["que", "donde", "quien", "cual"]:
    _add(r, cat="Rel", lemma=r)

# ------------------------------------------------------------ verbos regulares
# (infinitivo, transitividad)
VERBOS = [
    ("cantar", "both"), ("comer", "both"), ("beber", "both"), ("mirar", "tr"), ("comprar", "tr"),
    ("vender", "tr"), ("escribir", "both"), ("abrir", "tr"), ("tomar", "tr"), ("lavar", "tr"),
    ("pintar", "tr"), ("ayudar", "tr"), ("estudiar", "both"), ("correr", "intr"), ("caminar", "intr"),
    ("hablar", "intr"), ("trabajar", "intr"), ("preparar", "tr"), ("visitar", "tr"), ("aprender", "tr"),
    ("vivir", "intr"), ("subir", "both"), ("recibir", "tr"), ("cocinar", "both"), ("limpiar", "tr"),
    ("saltar", "intr"), ("nadar", "intr"), ("llorar", "intr"), ("esperar", "tr"), ("escuchar", "tr"),
    ("saludar", "tr"), ("dibujar", "tr"), ("cuidar", "tr"), ("romper", "tr"), ("terminar", "both"),
]
TERM = {
    ("ar", "pres"): ["o", "as", "a", "amos", "áis", "an"],
    ("er", "pres"): ["o", "es", "e", "emos", "éis", "en"],
    ("ir", "pres"): ["o", "es", "e", "imos", "ís", "en"],
    ("ar", "pret"): ["é", "aste", "ó", "amos", "asteis", "aron"],
    ("er", "pret"): ["í", "iste", "ió", "imos", "isteis", "ieron"],
    ("ir", "pret"): ["í", "iste", "ió", "imos", "isteis", "ieron"],
}
PERSONAS = [(1, "s"), (2, "s"), (3, "s"), (1, "p"), (2, "p"), (3, "p")]
for inf, trans in VERBOS:
    raiz, tipo = inf[:-2], inf[-2:]
    _add(inf, cat="Inf", lemma=inf)
    for tiempo in ("pres", "pret"):
        for (pers, num), suf in zip(PERSONAS, TERM[(tipo, tiempo)]):
            _add(raiz + suf, cat="V", lemma=inf, pers=pers, num=num, tiempo=tiempo, trans=trans)

# copulativos ser / estar
for lemma, pres, pret in [
    ("ser", ["soy", "eres", "es", "somos", "sois", "son"], ["fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"]),
    ("estar", ["estoy", "estás", "está", "estamos", "estáis", "están"],
     ["estuve", "estuviste", "estuvo", "estuvimos", "estuvisteis", "estuvieron"]),
]:
    for tiempo, formas in (("pres", pres), ("pret", pret)):
        for (pers, num), f in zip(PERSONAS, formas):
            _add(f, cat="V", lemma=lemma, pers=pers, num=num, tiempo=tiempo, trans="cop")

# verbos con complemento oracional / infinitivo (la gramática NO los cubre; están en el
# lexicón para que el rechazo sea sintáctico y no un simple "palabra desconocida")
for lemma, formas in [("decir", {"dice": (3, "s", "pres"), "dijo": (3, "s", "pret")}),
                      ("querer", {"quiere": (3, "s", "pres"), "quiso": (3, "s", "pret"), "quieren": (3, "p", "pres")}),
                      ("pensar", {"piensa": (3, "s", "pres"), "pensó": (3, "s", "pret")})]:
    for f, (p, n, t) in formas.items():
        _add(f, cat="V", lemma=lemma, pers=p, num=n, tiempo=t, trans="comp")

def analizar_palabra(palabra):
    """Devuelve la lista de análisis posibles de una palabra (lista vacía si es desconocida)."""
    return LEX.get(palabra.lower(), [])


def tamano_lexico():
    return len(LEX), sum(len(v) for v in LEX.values())
