import re
from typing import List, Dict


def segmentar_texto_en_clausulas(texto: str) -> List[Dict[str, str]]:
    """Toma el texto completo de un contrato y lo divide en cláusulas individuales."""
    if not texto:
        return []

    # Patrón Regex enfocado exclusivamente en apartados y cláusulas jurídicas
    patron_clausula = r'(?i)(?=(?:^|\n)\s*(?:CLÁUSULA\s+(?:[A-ZÁÉÍÓÚ0-9]+|[I|V|X]+)|SECCIÓN\s+[0-9]+|DECLARACIO(?:N|NES)|CONSIDERANDOS|ANTECEDENTES|(?:DÉCIMA|DECIMA|NOVENA|OCTAVA|SÉPTIMA|SEPTIMA|SEXTA|QUINTA|CUARTA|TERCERA|SEGUNDA|PRIMERA)(?:\s+(?:PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SÉPTIMA|SEPTIMA|OCTAVA|NOVENA))?))'

    # Dividir el texto en bloques
    bloques = re.split(patron_clausula, texto)
    clausulas_procesadas = []

    orden = 1
    for bloque in bloques:
        bloque_limpio = bloque.strip()
        if not bloque_limpio:
            continue

        lineas = bloque_limpio.split('\n')
        primera_linea = lineas[0].strip()

        numero = None
        titulo = None

        # Identificar la denominación de la cláusula en la primera línea del bloque
        coincidencia_num = re.search(
            r'(?i)(CLÁUSULA\s+(?:[A-ZÁÉÍÓÚ0-9]+|[I|V|X]+)|SECCIÓN\s+[0-9]+|DECLARACIO(?:N|NES)|CONSIDERANDOS|ANTECEDENTES|(?:DÉCIMA|DECIMA|NOVENA|OCTAVA|SÉPTIMA|SEPTIMA|SEXTA|QUINTA|CUARTA|TERCERA|SEGUNDA|PRIMERA)(?:\s+(?:PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SÉPTIMA|SEPTIMA|OCTAVA|NOVENA))?)',
            primera_linea
        )

        if coincidencia_num:
            numero = coincidencia_num.group(0).upper()
            titulo = primera_linea
        elif len(primera_linea) < 80:
            titulo = primera_linea

        clausulas_procesadas.append({
            "numero": numero or f"Sección {orden}",
            "titulo": titulo or f"Cláusula {orden}",
            "texto": bloque_limpio,
            "orden": orden
        })
        orden += 1

    return clausulas_procesadas