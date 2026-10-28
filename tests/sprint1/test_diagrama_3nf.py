"""Contrasta el E-R normalizado con las FK y columnas del DDL vigente.

El lector está acotado al formato actual del proyecto, no es un parser SQL general.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DiagramaNormalizadoTests(unittest.TestCase):
    def test_tablas_columnas_y_cardinalidades_coinciden_con_ddl(self):
        ddl = (ROOT / 'sprint1/postgres/schema_v2_3nf.sql').read_text()
        documento = (ROOT / 'docs/arquitectura/diagrama_3nf.md').read_text()
        mermaid = documento.split('```mermaid', 1)[1].split('```', 1)[0]
        tablas = dict(re.findall(r'CREATE TABLE (\w+)\s*\((.*?)\n?\);', ddl, re.S))
        entidades = dict(re.findall(r'^  (\w+) \{\n(.*?)^  \}', mermaid, re.M | re.S))
        self.assertEqual(set(tablas), set(entidades))
        self.assertEqual(len(tablas), 14)

        relaciones = set()
        for tabla, cuerpo in tablas.items():
            columnas = {}
            # Las comas dentro de CHECK/UNIQUE no separan columnas.
            nivel = 0
            inicio = 0
            partes = []
            for indice, caracter in enumerate(cuerpo):
                if caracter == '(':
                    nivel += 1
                elif caracter == ')':
                    nivel -= 1
                elif caracter == ',' and nivel == 0:
                    partes.append(cuerpo[inicio:indice].strip())
                    inicio = indice + 1
            partes.append(cuerpo[inicio:].strip())

            for parte in partes:
                if parte.startswith(('CHECK', 'UNIQUE')):
                    continue
                nombre = parte.split()[0]
                columnas[nombre] = parte
                referencia = re.search(r'REFERENCES (\w+)', parte)
                if referencia:
                    padre = referencia.group(1)
                    obligatorio = 'NOT NULL' in parte or 'PRIMARY KEY' in parte
                    extremo_padre = '||' if obligatorio else 'o|'
                    extremo_hijo = 'o|' if 'PRIMARY KEY' in parte else 'o{'
                    relaciones.add((padre, extremo_padre, extremo_hijo, tabla, nombre))

            atributos = set(re.findall(r'^    \w+ (\w+)', entidades[tabla], re.M))
            self.assertEqual(set(columnas), atributos, tabla)

        dibujadas = set(re.findall(
            r'^  (\w+) (\|\||o\|)\.\.(o\{|o\|) (\w+) : (\w+)$', mermaid, re.M
        ))
        self.assertEqual(len(relaciones), 17)
        self.assertEqual(relaciones, dibujadas)


if __name__ == '__main__':
    unittest.main()
