"""
dataset.py - Conjunto de prueba (3 niveles) con la salida esperada.  Genera dataset.json.

Etiquetas por oración:
  valida       : ¿es una oración bien formada del español? (juicio del grupo, hablante nativo)
  en_gramatica : ¿DEBE aceptarla nuestra CFG + concordancia? (verdad de referencia para depurar el parser)
  sujeto, verbo, objeto : núcleos esperados (solo cuando en_gramatica=True) para medir extracción de roles
  fenomeno     : fenómeno lingüístico que se prueba

Nivel 1: simples que la gramática debe aceptar.
Nivel 2: con modificadores/variaciones (válidas) y errores de concordancia (inválidas).
Nivel 3: fenómenos que exceden la gramática (válidas fuera de gramática) + agramaticales + casos límite.
"""
import json
import os

# (nivel, oración, valida, en_gramatica, sujeto, verbo, objeto, fenómeno)
D = []


def add(nivel, o, valida, en_g, s=None, v=None, ob=None, fen=""):
    D.append(dict(nivel=nivel, oracion=o, valida=valida, en_gramatica=en_g,
                  sujeto=s, verbo=v, objeto=ob, fenomeno=fen))


# ------------------------------------------------------------- NIVEL 1
for o, s, v, ob, f in [
    ("Ana come una manzana.", "ana", "come", "manzana", "SVO presente"),
    ("El niño escribe una carta.", "niño", "escribe", "carta", "SVO presente"),
    ("Los niños comen manzanas.", "niños", "comen", "manzanas", "objeto sin determinante"),
    ("La profesora canta una canción.", "profesora", "canta", "canción", "SVO presente"),
    ("Luis compra pan.", "luis", "compra", "pan", "objeto sin determinante"),
    ("El perro corre.", "perro", "corre", None, "intransitivo"),
    ("Las niñas caminan.", "niñas", "caminan", None, "intransitivo"),
    ("Yo bebo leche.", "yo", "bebo", "leche", "pronombre sujeto"),
    ("Tú vendes coches.", "tú", "vendes", "coches", "pronombre sujeto"),
    ("Nosotros vivimos aquí.", "nosotros", "vivimos", None, "adverbio final"),
    ("Ellos abren la ventana.", "ellos", "abren", "ventana", "SVO presente"),
    ("María pintó una casa.", "maría", "pintó", "casa", "pretérito"),
    ("El gato miró un pájaro.", "gato", "miró", "pájaro", "pretérito"),
    ("Los estudiantes limpiaron la mesa.", "estudiantes", "limpiaron", "mesa", "pretérito, género común"),
    ("La mujer cantó.", "mujer", "cantó", None, "intransitivo pretérito"),
    ("Carlos estudia.", "carlos", "estudia", None, "verbo ambitransitivo"),
    ("Ella prepara la sopa.", "ella", "prepara", "sopa", "pronombre sujeto"),
    ("Pedro visitó el parque.", "pedro", "visitó", "parque", "pretérito"),
    ("Los perros corrieron.", "perros", "corrieron", None, "intransitivo pretérito"),
    ("El profesor habla.", "profesor", "habla", None, "intransitivo"),
    ("Ana es feliz.", "ana", "es", None, "copulativo ser"),
    ("Los niños están cansados.", "niños", "están", None, "copulativo estar"),
    ("La casa es grande.", "casa", "es", None, "copulativo ser"),
    ("Ustedes cocinan pasteles.", "ustedes", "cocinan", "pasteles", "pronombre sujeto"),
    ("Un hombre trabaja.", "hombre", "trabaja", None, "intransitivo"),
    ("Elena escuchó la música.", "elena", "escuchó", "música", "pretérito"),
]:
    add(1, o, True, True, s, v, ob, f)

# ------------------------------------------------------------- NIVEL 2 (válidas)
for o, s, v, ob, f in [
    ("El niño pequeño come una manzana roja.", "niño", "come", "manzana", "adjetivos postnominales"),
    ("La profesora simpática escribe una carta bonita.", "profesora", "escribe", "carta", "adjetivos postnominales"),
    ("Ana come una manzana rápidamente.", "ana", "come", "manzana", "adverbio final"),
    ("Ayer Luis compró un libro nuevo.", "luis", "compró", "libro", "adverbio inicial"),
    ("Los perros grandes corren rápidamente.", "perros", "corren", None, "adjetivo + adverbio"),
    ("La niña canta una canción bonita en la escuela.", "niña", "canta", "canción", "SP (ambiguo: 2 adjunciones)"),
    ("El gato negro camina en el jardín.", "gato", "camina", None, "SP locativo"),
    ("Mi amigo trabaja en una escuela grande.", "amigo", "trabaja", None, "posesivo + SP"),
    ("Ana vive en una casa muy bonita.", "ana", "vive", None, "adverbio de grado"),
    ("Los estudiantes inteligentes estudian siempre.", "estudiantes", "estudian", None, "adverbio final"),
    ("Hoy María prepara una sopa caliente.", "maría", "prepara", "sopa", "adverbio inicial"),
    ("Ellos vendieron los coches viejos en el mercado.", "ellos", "vendieron", "coches", "SP + pretérito"),
    ("Un hombre alto visitó la ciudad con su amiga.", "hombre", "visitó", "ciudad", "SP (ambiguo)"),
    ("La mesa blanca está en la casa.", "mesa", "está", None, "estar + SP"),
    ("Las flores rojas son muy bonitas.", "flores", "son", None, "ser + adjetivo con grado"),
    ("El profesor no come pescado.", "profesor", "come", "pescado", "negación"),
    ("Nosotras escuchamos la música tranquilamente.", "nosotras", "escuchamos", "música", "adverbio final"),
    ("Carlos habla con la maestra de la escuela.", "carlos", "habla", None, "SP encadenados (ambiguo)"),
    ("Ana miró el gato con el telescopio.", "ana", "miró", "gato", "ambigüedad estructural clásica"),
    ("El pequeño perro come un pastel.", "perro", "come", "pastel", "adjetivo antepuesto"),
]:
    add(2, o, True, True, s, v, ob, f)
# ------------------------------------------------------------- NIVEL 2 (errores de concordancia)
for o, f in [
    ("Los niño comen manzanas.", "Det-N número"),
    ("La perro corre.", "Det-N género"),
    ("Las casas son grande.", "sujeto-adjetivo predicativo número"),
    ("Yo comes pan.", "sujeto-verbo persona"),
    ("Ellos come una manzana.", "sujeto-verbo número"),
    ("El niño pequeña come una manzana.", "N-Adj género"),
]:
    add(2, o, False, False, fen=f)

# ------------------------------------------------------------- NIVEL 3 (válidas FUERA de la gramática)
for o, f in [
    ("El niño que corre en el parque come una manzana.", "oración de relativo"),
    ("Ana come una manzana y Luis bebe leche.", "coordinación de oraciones"),
    ("Ana come rápidamente una manzana.", "adverbio entre verbo y objeto"),
    ("Come manzanas.", "sujeto omitido (pro-drop)"),
    ("Ana dice que Luis compró un libro.", "subordinada completiva"),
    ("¿Come Ana una manzana?", "interrogativa con inversión"),
    ("Ana la compró.", "clítico de objeto"),
    ("Cuando Ana cantó, los niños comieron.", "subordinada temporal"),
    ("Ana quiere comer una manzana.", "complemento infinitivo"),
    ("El libro que Ana compró es interesante.", "relativo de objeto (dependencia a distancia)"),
]:
    add(3, o, True, False, fen=f)
# ------------------------------------------------------------- NIVEL 3 (válidas sintácticamente, anómalas semánticamente)
for o, s, v, ob, f in [
    ("El perro bebe una canción.", "perro", "bebe", "canción", "anomalía semántica (selección léxica)"),
    ("La mesa escribe un examen.", "mesa", "escribe", "examen", "anomalía semántica (selección léxica)"),
]:
    add(3, o, True, True, s, v, ob, f)
# ------------------------------------------------------------- NIVEL 3 (inválidas)
for o, f in [
    ("Ana come manzana una roja.", "orden de palabras desordenado"),
    ("Los niños que corre en el parque come una manzana.", "concordancia a distancia en relativo"),
    ("Comen niños los manzanas.", "orden de palabras desordenado"),
    ("Yo ellos come pan.", "dos sujetos"),
    ("Ana come come manzana.", "verbo repetido"),
    ("Las niñas bonito comen.", "orden y concordancia"),
    ("La casa que compraron los vecinos es grandes.", "concordancia a distancia con relativo"),
    ("Las niñas que estudian en la escuela están cansado.", "concordancia a distancia con relativo"),
    ("Ana saluda yo.", "caso del pronombre (yo en función de objeto)"),
]:
    add(3, o, False, False, fen=f)

if __name__ == "__main__":
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.json")
    for i, d in enumerate(D, 1):
        d["id"] = i
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(D, f, ensure_ascii=False, indent=1)
    import collections
    c = collections.Counter(d["nivel"] for d in D)
    print(f"{len(D)} oraciones:", dict(c))
