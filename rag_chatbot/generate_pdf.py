from fpdf import FPDF

def create_example_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    content = """
    Acme Corp Employee Handbook
    
    1. Introduction
    Welcome to Acme Corp! This document outlines our company policies.
    
    2. Working Hours
    Standard working hours are from 9:00 AM to 5:00 PM, Monday through Friday.
    Employees are entitled to a one-hour lunch break to be taken between 12:00 PM and 2:00 PM.
    
    3. Remote Work Policy
    Employees may work from home up to two days a week, subject to manager approval.
    Core hours for remote workers are 10:00 AM to 3:00 PM.
    
    4. Vacation and Leave
    All full-time employees are entitled to 20 days of paid time off (PTO) per year.
    Unused PTO up to 5 days can be carried over to the next year.
    Sick leave is 10 days per year.
    
    5. IT Equipment
    The company provides a laptop and accessories. 
    Lost or damaged equipment must be reported immediately to the IT helpdesk.
    """
    
    for line in content.split('\n'):
        pdf.cell(200, 10, txt=line.strip(), ln=1)
        
    pdf.output("example_rag_doc.pdf")
    print("example_rag_doc.pdf created successfully.")

if __name__ == "__main__":
    create_example_pdf()
