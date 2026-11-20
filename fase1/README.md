# Fase 1 – Lexer y analizador semántico (MiniC)

Lenguaje elegido: **MiniC**, un subconjunto de C con tipos `int float bool string`, declaraciones, asignaciones,
`if/else`, `while`, `print`, bloques `{ }` y operadores aritméticos, relacionales y lógicos.

## Archivos
| Archivo | Contenido |
|---|---|
| `lexer.py` | Clase `Lexer` genérica (reglas = expresiones regulares) + reglas de MiniC. Reporta línea, columna y errores léxicos. |
| `semantico.py` | Tabla de símbolos con ámbitos, declaración previa, redeclaración, tipos en asignaciones y expresiones. |
| `pruebas/casos.py` | 22 casos (7 válidos, 5 errores léxicos, 10 errores semánticos) con el error esperado y su línea. |
| `ejemplos/*.minic` | Tres programas para la demo: `valido`, `error_lexico` y `error_semantico` (comentados línea a línea). |
| `correr_pruebas.py` | Ejecuta todos los casos. `python correr_pruebas.py -v` muestra los mensajes. |

## Ejecución
Solo requiere Python 3.8 o superior; no usa librerías externas. Desde la carpeta `fase1/`:
```bash
python correr_pruebas.py -v                          # batería de pruebas (22/22)
python lexer.py ejemplos/valido.minic                # lista de tokens (línea:columna) y errores léxicos
python lexer.py ejemplos/error_lexico.minic          # 5 errores léxicos con línea y columna
python semantico.py ejemplos/valido.minic            # sin errores
python semantico.py ejemplos/error_semantico.minic   # 7 errores semánticos con línea y causa
```
Con cualquier archivo propio: `python lexer.py programa.minic` o `python semantico.py programa.minic`. Sin argumento, ambos leen de la entrada estándar.
Si el archivo tiene errores léxicos, `semantico.py` los reporta y no ejecuta la fase semántica.

## Especificación de tokens (expresiones regulares)
| Token | Regex | | Token | Regex |
|---|---|---|---|---|
| `ID` | `[A-Za-z_][A-Za-z_0-9]*` | | `INT_LIT` | `\d+` |
| `FLOAT_LIT` | `\d+\.\d+` | | `STRING_LIT` | `"[^"\n]*"` |
| `OP_REL` | `==\|!=\|<=\|>=\|<\|>` | | `OP_LOG` | `&&\|\|\|` |
| `OP_ARIT` | `[+\-*/%]` | | `ASIGNA` | `=` |
Palabras reservadas: `int float bool string if else while print true false`.
Errores léxicos detectados: carácter inválido, cadena sin cerrar, número mal formado (`1.2.3`, `12abc`), comentario de bloque sin cerrar.

## Diseño del analizador semántico
* **Tabla de símbolos**: pila de diccionarios (un ámbito por `{ }`); `buscar` recorre de adentro hacia afuera.
* **Sentencias**: como permite el enunciado, no hay parser; los tokens se agrupan por sentencia (`;`, `{`, `}`).
* **Tipos de expresiones**: evaluador recursivo con precedencia (`||/&&` < relacionales < `+ -` < `* / %` < unarios < primarios).
  `int → float` se permite (ensanchamiento); `string + string` concatena; las condiciones deben ser `bool`.
* Con errores léxicos no se ejecuta la fase semántica (evita errores en cascada, como un compilador real).

## Reflexión: qué verificaciones NO puede expresar una CFG
1. **"Toda variable usada debe estar declarada."** Equivale a reconocer el lenguaje `{ w … w }` (la misma cadena `w`
   —el identificador— aparece en la declaración y en el uso, a distancia arbitraria). Ese lenguaje **no es libre de
   contexto** (lo prueba el lema de bombeo); una CFG solo puede decir "aquí va un `ID`", no "un `ID` ya visto".
2. **No redeclarar en el mismo ámbito** y **resolución de ámbitos**: requieren recordar un conjunto de nombres y su
   anidamiento, es decir, memoria no acotada que compara símbolos: de nuevo la forma `{ w … w }`.
3. **Compatibilidad de tipos**: el tipo de `x` depende de su declaración (otro lugar del texto); la gramática no
   distingue `int x; x = "hola";` de `int x; x = 3;` porque ambos son `ID = expresión ;`.
   Se podría "forzar" con una gramática por tipo y por variable, pero eso exigiría una producción por cada
   identificador posible: infinitas reglas, ya no es una CFG finita.
4. **Condición booleana en `if`/`while`** y tipos de operadores: mismo problema (dependen del contexto).

**Conexión con Chomsky**: el lexer es *regular* (nivel 3, AFD/regex); el parser sería *libre de contexto* (nivel 2,
autómata de pila); estas verificaciones corresponden al nivel *sensible al contexto* (nivel 1), que en la práctica se
implementa con una **gramática de atributos / tabla de símbolos**, no con un autómata lineal acotado explícito.
Esto prepara la Fase 2: la **concordancia** del español (género, número, persona) es exactamente el mismo fenómeno.
