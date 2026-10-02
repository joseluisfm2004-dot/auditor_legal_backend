import os
from fpdf import FPDF
from datetime import datetime

class ReporteAuditoriaPDF(FPDF):
    def header(self):
        # Título / Membrete
        self.set_font("helvetica", "B", 16)
        self.set_text_color(33, 37, 41) # Gris oscuro
        self.cell(0, 10, "Reporte de Auditoría Legal Asistida por IA", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        # Pie de página con numeración
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Generado por Auditor Legal IA - Página {self.page_no()}/{{nb}}", align="C")

def generar_pdf(datos: dict, ruta_salida: str):
    """
    Recibe un diccionario con los datos de la auditoría y genera un PDF.
    """
    pdf = ReporteAuditoriaPDF()
    pdf.alias_nb_pages() # Para que funcione el total de páginas {nb}
    pdf.add_page()
    
    # --- 1. Información del Contrato ---
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Documento: {datos.get('nombre_contrato', 'Desconocido')}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, f"Fecha de Auditoría: {datos.get('fecha', datetime.now().strftime('%d/%m/%Y'))}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Puntaje de Riesgo Global: {datos.get('riesgo_global', 0)} / 100", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # --- 2. Resumen Ejecutivo ---
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Resumen Ejecutivo", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    
    # multi_cell permite saltos de línea automáticos
    resumen = datos.get('resumen_ejecutivo', 'No hay resumen disponible.')
    pdf.multi_cell(0, 6, resumen)
    pdf.ln(8)

    # --- 3. Detalle de Hallazgos (Cláusulas) ---
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Detalle de Hallazgos y Sugerencias", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    for hallazgo in datos.get("hallazgos", []):
        nivel_riesgo = hallazgo.get("nivel_riesgo", "Bajo")
        
        # Seleccionar color según el riesgo
        if nivel_riesgo.lower() == "alto":
            pdf.set_text_color(220, 53, 69) # Rojo
        elif nivel_riesgo.lower() == "medio":
            pdf.set_text_color(255, 152, 0) # Naranja
        else:
            pdf.set_text_color(40, 167, 69) # Verde

        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 8, f"Riesgo {nivel_riesgo.upper()} - Cláusula #{hallazgo.get('orden_clausula', 0)}", new_x="LMARGIN", new_y="NEXT")
        
        # Reset color a negro para el texto
        pdf.set_text_color(0, 0, 0)
        
        # Texto original (resumido si es muy largo para no saturar el PDF)
        texto_orig = hallazgo.get("texto_clausula", "")
        if len(texto_orig) > 200:
            texto_orig = texto_orig[:200] + "..."
            
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(0, 5, f'"{texto_orig}"')
        
        # Observación
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(0, 6, "Observación Legal:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 9)
        pdf.multi_cell(0, 5, hallazgo.get("descripcion", ""))
        
        # Recomendación
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(0, 6, "Sugerencia de Mejora:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 9)
        pdf.multi_cell(0, 5, hallazgo.get("recomendacion", ""))
        
        pdf.ln(5) # Espacio antes de la siguiente cláusula

    # Crear directorio si no existe y guardar
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    pdf.output(ruta_salida)
    return ruta_salida