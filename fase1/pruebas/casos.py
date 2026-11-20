"""Casos de prueba de la Fase 1.  Cada caso: (nombre, código, errores esperados)
donde errores esperados es una lista de (tipo, fragmento_del_mensaje, línea)."""

CASOS = [
 # ---------------- válidos ----------------
 ("valido_declaraciones", "int x = 5;\nfloat y = 2.5;\nbool b = true;\nstring s = \"hola\";\n", []),
 ("valido_ensanchamiento", "int a = 3;\nfloat f = a;\nf = a + 1;\n", []),
 ("valido_expresiones", "int a = 2;\nint b = a * 3 + (4 - a) % 2;\nbool c = a < b && b != 0;\n", []),
 ("valido_if_while", "int i = 0;\nwhile (i < 10) {\n  i = i + 1;\n}\nif (i == 10) {\n  print i;\n} else {\n  print \"no\";\n}\n", []),
 ("valido_ambitos_sombra", "int x = 1;\n{\n  int x = 2;\n  print x;\n}\nprint x;\n", []),
 ("valido_comentarios", "// comentario\nint x = 1; /* bloque\nmultilínea */\nprint x;\n", []),
 ("valido_concat", "string a = \"ho\";\nstring b = a + \"la\";\n", []),
 # ---------------- errores léxicos ----------------
 ("lex_caracter_invalido", "int x = 5 @ 3;\n", [("lex", "carácter inválido '@'", 1)]),
 ("lex_cadena_sin_cerrar", "string s = \"hola;\nint y = 1;\n", [("lex", "cadena sin cerrar", 1)]),
 ("lex_numero_mal_formado", "float f = 1.2.3;\n", [("lex", "mal formado", 1)]),
 ("lex_identificador_numero", "int z = 12abc;\n", [("lex", "mal formado", 1)]),
 ("lex_comentario_sin_cerrar", "int x = 1;\n/* nunca se cierra\nint y = 2;\n", [("lex", "comentario de bloque sin cerrar", 2)]),
 # ---------------- errores semánticos ----------------
 ("sem_no_declarada", "int x = 1;\ny = x + 1;\n", [("sem", "'y' usada sin declarar", 2)]),
 ("sem_no_declarada_expr", "int x = z + 1;\n", [("sem", "'z' usada sin declarar", 1)]),
 ("sem_redeclaracion", "int x = 1;\nint x = 2;\n", [("sem", "redeclaración de 'x'", 2)]),
 ("sem_tipo_asignacion", "int x = 1;\nx = \"texto\";\n", [("sem", "no se puede asignar string", 2)]),
 ("sem_float_a_int", "float f = 1.5;\nint i = f;\n", [("sem", "no se puede asignar float a 'i'", 2)]),
 ("sem_suma_string_int", "string s = \"a\";\nint n = s + 1;\n", [("sem", "string + int no permitida", 2)]),
 ("sem_condicion_no_bool", "int x = 1;\nif (x + 1) {\n  print x;\n}\n", [("sem", "debe ser bool", 2)]),
 ("sem_fuera_de_ambito", "{\n  int tmp = 1;\n}\nprint tmp;\n", [("sem", "'tmp' usada sin declarar", 4)]),
 ("sem_logico_con_int", "int a = 1;\nbool b = a && true;\n", [("sem", "requiere bool", 2)]),
 ("sem_llave_sin_cerrar", "int x = 1;\nwhile (x < 3) {\n  x = x + 1;\n", [("sem", "sin cerrar", 2)]),
]
