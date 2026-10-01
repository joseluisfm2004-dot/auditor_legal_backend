import json
import os
from typing import Dict, Any, List
from openai import AsyncAzureOpenAI, AsyncOpenAI

# ----------------------------------------------------------------------
# Configuración del Cliente LLM (Azure OpenAI u OpenAI)
# ----------------------------------------------------------------------
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

client = None

if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY:
    client = AsyncAzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version="2024-06-01"
    )
elif os.getenv("OPENAI_API_KEY"):
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ----------------------------------------------------------------------
# Función Principal de Análisis
# ----------------------------------------------------------------------
async def analizar_clausula_con_ia(numero: str, titulo: str, texto: str) -> Dict[str, Any]:
    """
    Analiza una cláusula individual e identifica riesgos o hallazgos jurídicos
    utilizando un modelo LLM con salida estructurada JSON, o mediante reglas
    heurísticas como respaldo.
    """
    if client:
        try:
            prompt_sistema = (
                "Eres un abogado experto en auditoría contractual y cumplimiento normativo.\n"
                "Tu tarea es analizar cláusulas contractuales e identificar riesgos legales, "
                "punitivos, financieros, ambigüedades o desequilibrios entre las partes.\n\n"
                "Debes responder EXCLUSIVAMENTE en formato JSON estricto con la siguiente estructura:\n"
                "{\n"
                '  "hallazgos": [\n'
                "    {\n"
                '      "tipo": "Categoría (ej. Riesgo Financiero, Confidencialidad, Rescisión, Ambigüedad, Jurisdicción)",\n'
                '      "nivel_riesgo": "Alto" | "Medio" | "Bajo",\n'
                '      "descripcion": "Explicación concisa y técnica del riesgo detectado",\n'
                '      "sugerencia_mejora": "Propuesta de redacción o mitigación recomendada"\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "Si la cláusula es estándar y no presenta riesgos, devuelve {\"hallazgos\": []}."
            )

            prompt_usuario = f"Identificador: {numero}\nTítulo: {titulo}\nTexto:\n{texto}"

            response = await client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": prompt_usuario}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            contenido = response.choices[0].message.content
            data = json.loads(contenido)
            return {
                "numero_clausula": numero,
                "hallazgos": data.get("hallazgos", [])
            }

        except Exception as e:
            print(f"[AI Auditor Warning] Error al invocar el servicio LLM: {e}. Usando fallback heurístico.")

    # Resguardo heurístico cuando no hay credenciales de IA o falla el LLM
    return _analizar_clausula_heuristico(numero, titulo, texto)


# ----------------------------------------------------------------------
# Fallback Heurístico (Reglas Estáticas de Resguardo)
# ----------------------------------------------------------------------
def _analizar_clausula_heuristico(numero: str, titulo: str, texto: str) -> Dict[str, Any]:
    """Análisis estático ampliado basado en patrones de palabras clave."""
    texto_lower = texto.lower()
    hallazgos = []

    # 1. Penalizaciones, Multas e Intereses
    if any(w in texto_lower for w in ["penalización", "multa", "sanción", "interés moratorio", "intereses moratorios", "pena convencional"]):
        hallazgos.append({
            "tipo": "Riesgo Financiero / Penalización",
            "nivel_riesgo": "Alto",
            "descripcion": "Se detectaron cláusulas punitivas, penas convencionales o sanciones económicas explícitas.",
            "sugerencia_mejora": "Revisar los topes porcentuales de penalización y verificar la proporcionalidad legal."
        })

    # 2. Confidencialidad y Propiedad Intelectual
    if any(w in texto_lower for w in ["confidencialidad", "secreto", "nda", "propiedad intelectual", "derechos de autor"]):
        hallazgos.append({
            "tipo": "Confidencialidad y PI",
            "nivel_riesgo": "Medio",
            "descripcion": "Cláusula con obligaciones de secreto, confidencialidad o cesión de derechos intelectuales.",
            "sugerencia_mejora": "Asegurar un plazo razonable post-terminación y delimitar qué información se considera confidencial."
        })

    # 3. Rescisión y Terminación Anticipada
    if any(w in texto_lower for w in ["rescisión", "terminación anticipada", "vencimiento", "resolución", "cancelación"]):
        hallazgos.append({
            "tipo": "Terminación Contractual",
            "nivel_riesgo": "Medio",
            "descripcion": "Establece causales o mecanismos de rescisión o terminación de contrato.",
            "sugerencia_mejora": "Asegurar plazos razonables de notificación previa por escrito (ej. 30 días) para ambas partes."
        })

    # 4. Ley Aplicable y Jurisdicción
    if any(w in texto_lower for w in ["jurisdicción", "tribunales", "competencia", "ley aplicable", "arbitraje"]):
        hallazgos.append({
            "tipo": "Jurisdicción y Ley Aplicable",
            "nivel_riesgo": "Bajo",
            "descripcion": "Establece la legislación aplicable y la competencia judicial frente a controversias.",
            "sugerencia_mejora": "Confirmar que la ubicación de los tribunales designados resulte conveniente y accesible."
        })

    # 5. Detección de Contenido Técnico u Horas de Diagnóstico
    if any(w in texto_lower for w in ["evaluación", "desarrollador", "reactivos", "sql", "programación", "examen"]):
        hallazgos.append({
            "tipo": "Validación de Contenido",
            "nivel_riesgo": "Bajo",
            "descripcion": "El texto procesado contiene evaluaciones técnicas o pruebas de código en lugar de un contrato legal formal.",
            "sugerencia_mejora": "Asegurar la carga de un instrumento jurídico adecuado (ej. Contrato de Prestación de Servicios, NDA)."
        })

    return {
        "numero_clausula": numero,
        "hallazgos": hallazgos
    }


# ----------------------------------------------------------------------
# Generación de Resumen Ejecutivo Global
# ----------------------------------------------------------------------
async def generar_resumen_ejecutivo(hallazgos_totales: List[Dict[str, Any]], puntaje_riesgo: float) -> str:
    """Genera un diagnóstico global consolidado sobre el estado del contrato."""
    if client:
        try:
            response = await client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente legal ejecutivo. Redacta un resumen ejecutivo conciso (2 párrafos max) "
                                   "que describa el nivel de riesgo global del contrato a partir de sus hallazgos."
                    },
                    {
                        "role": "user",
                        "content": f"Puntaje global de riesgo: {puntaje_riesgo}/100.\nHallazgos: {json.dumps(hallazgos_totales, ensure_ascii=False)}"
                    }
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[AI Auditor Warning] No se pudo generar el resumen ejecutivo con IA: {e}")

    # Diagnóstico sintético de resguardo
    num_hallazgos = len(hallazgos_totales)
    if puntaje_riesgo >= 70:
        nivel = "ALTO"
        rec = "Requiere revisión jurídica urgente previo a la firma."
    elif puntaje_riesgo >= 30:
        nivel = "MODERADO"
        rec = "Se sugieren ajustes preventivos en cláusulas puntuales."
    else:
        nivel = "BAJO"
        rec = "El documento presenta un perfil de riesgo aceptable con observaciones mínimas."

    return f"Auditoría completada. Nivel de riesgo general: {nivel} (Puntaje: {puntaje_riesgo:.1f}/100). Total de hallazgos registrados: {num_hallazgos}. {rec}"