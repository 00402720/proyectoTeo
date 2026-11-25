"""
arbol.py - Árbol de análisis sintáctico + visualización.

Exporta a: notación de corchetes (estilo nltk), DOT (graphviz) y PNG (matplotlib).
"""
import os


class Arbol:
    """Nodo del árbol.  Las hojas son Arbol(cat, [palabra]) con `analisis` = lista de
    análisis léxicos compatibles con la categoría (se usan en la verificación de concordancia)."""

    def __init__(self, etiqueta, hijos, analisis=None):
        self.etiqueta = etiqueta
        self.hijos = hijos
        self.analisis = analisis or []

    def es_preterminal(self):
        return len(self.hijos) == 1 and isinstance(self.hijos[0], str)

    @property
    def palabra(self):
        return self.hijos[0] if self.es_preterminal() else None

    def hojas(self):
        if self.es_preterminal():
            return [self]
        return [h for c in self.hijos for h in c.hojas()]

    def recorrer(self):
        yield self
        if not self.es_preterminal():
            for h in self.hijos:
                yield from h.recorrer()

    def corchetes(self):
        if self.es_preterminal():
            return f"({self.etiqueta} {self.hijos[0]})"
        return f"({self.etiqueta} " + " ".join(h.corchetes() for h in self.hijos) + ")"

    def estructura(self):
        """Corchetes sin palabras (solo etiquetas) para comparar estructuras."""
        if self.es_preterminal():
            return self.etiqueta
        return f"({self.etiqueta} " + " ".join(h.estructura() for h in self.hijos) + ")"

    def __repr__(self):
        return self.corchetes()

    # ---- DOT / graphviz
    def a_dot(self):
        lineas = ["digraph G {", '  node [shape=plaintext, fontname="Helvetica"];', "  edge [arrowhead=none];"]
        cont = [0]

        def rec(n):
            mi = cont[0]; cont[0] += 1
            if n.es_preterminal():
                lineas.append(f'  n{mi} [label="{n.etiqueta}"];')
                lineas.append(f'  p{mi} [label=<<I>{n.hijos[0]}</I>>];')
                lineas.append(f"  n{mi} -> p{mi};")
            else:
                lineas.append(f'  n{mi} [label="{n.etiqueta}"];')
                for h in n.hijos:
                    hi = rec(h)
                    lineas.append(f"  n{mi} -> n{hi};")
            return mi
        rec(self)
        lineas.append("}")
        return "\n".join(lineas)

    # ---- PNG con matplotlib
    def guardar_png(self, ruta, titulo=None):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        pos = {}
        siguiente = [0]

        def profundidad(n):
            return 1 if n.es_preterminal() else 1 + max(profundidad(h) for h in n.hijos)
        prof = profundidad(self)

        def layout(n, d):
            if n.es_preterminal():
                x = siguiente[0]; siguiente[0] += 1
                pos[id(n)] = (x, -d)
                return x
            xs = [layout(h, d + 1) for h in n.hijos]
            x = sum(xs) / len(xs)
            pos[id(n)] = (x, -d)
            return x
        layout(self, 0)
        ancho = max(6, siguiente[0] * 1.15)
        fig, ax = plt.subplots(figsize=(ancho, 1.0 + prof * 0.85))

        def dibujar(n):
            x, y = pos[id(n)]
            if n.es_preterminal():
                ax.text(x, y, n.etiqueta, ha="center", va="center", fontsize=10, color="#1f4e79",
                        bbox=dict(boxstyle="round,pad=0.2", fc="#eaf2fb", ec="#1f4e79"))
                ax.plot([x, x], [y - 0.18, y - 0.55], color="gray", lw=0.8)
                ax.text(x, y - 0.7, n.hijos[0], ha="center", va="center", fontsize=11, style="italic")
            else:
                ax.text(x, y, n.etiqueta, ha="center", va="center", fontsize=10, fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.2", fc="#fff6e5", ec="#b36b00"))
                for h in n.hijos:
                    hx, hy = pos[id(h)]
                    ax.plot([x, hx], [y - 0.18, hy + 0.18], color="gray", lw=0.8)
                    dibujar(h)
        dibujar(self)
        ax.set_xlim(-0.7, siguiente[0] - 0.3)
        ax.set_ylim(-prof - 0.2, 0.5)
        ax.axis("off")
        if titulo:
            ax.set_title(titulo, fontsize=12)
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        fig.savefig(ruta, dpi=130, bbox_inches="tight")
        plt.close(fig)
