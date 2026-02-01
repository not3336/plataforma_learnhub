# app/services/certificate_gen.py
from fpdf import FPDF

def generate_pdf_certificate(student_name, course_name):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # Design inspirado no estilo do seu HTML
    pdf.set_font("Arial", 'B', 40)
    pdf.set_text_color(45, 91, 227) # Sua cor --primary-color #2d5be3
    pdf.cell(0, 50, "Certificado de Conclusão", align='C', ln=1)
    
    pdf.set_font("Arial", '', 20)
    pdf.set_text_color(30, 41, 59) # --dark-color
    pdf.cell(0, 30, f"Certificamos que {student_name}", align='C', ln=1)
    pdf.cell(0, 30, f"Concluiu o curso: {course_name}", align='C', ln=1)
    
    filename = f"cert_{student_name}_{course_name}.pdf".replace(" ", "_")
    pdf.output(f"app/temp/{filename}")
    return f"app/temp/{filename}"