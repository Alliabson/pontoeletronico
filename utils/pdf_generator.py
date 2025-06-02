from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import locale
from datetime import datetime
import os

# Configuração de localização
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class PDFGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        self.styles = getSampleStyleSheet()
        self.elements = []
        
        # Estilos customizados
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            fontSize=14,
            leading=16,
            alignment=1,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            fontSize=12,
            leading=14,
            alignment=1,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='EmployeeInfo',
            fontSize=10,
            leading=12,
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            fontSize=9,
            leading=10,
            alignment=1,
            textColor=colors.white,
            backColor=colors.HexColor('#1e3a8a')
        ))
        self.styles.add(ParagraphStyle(
            name='TableCell',
            fontSize=8,
            leading=9,
            alignment=1
        ))
        self.styles.add(ParagraphStyle(
            name='Footer',
            fontSize=9,
            leading=10,
            alignment=2
        ))

    def add_header(self, company_info):
        """Adiciona cabeçalho com informações da empresa"""
        # Adicionar logo se existir
        if os.path.exists('assets/logo.png'):
            logo = Image('assets/logo.png', width=1.5*inch, height=0.5*inch)
            self.elements.append(logo)
        
        # Informações da empresa
        company_name = Paragraph(company_info['name'], self.styles['CompanyName'])
        self.elements.append(company_name)
        
        address = Paragraph(
            f"{company_info['address']}<br/>{company_info['city']}/{company_info['state']} - CEP: {company_info['cep']}",
            self.styles['EmployeeInfo']
        )
        self.elements.append(address)
        
        cnpj = Paragraph(f"CNPJ: {company_info['cnpj']}", self.styles['EmployeeInfo'])
        self.elements.append(cnpj)
        
        self.elements.append(Spacer(1, 0.25*inch))

    def add_report_title(self, title, period):
        """Adiciona título do relatório e período"""
        title = Paragraph(title, self.styles['ReportTitle'])
        self.elements.append(title)
        
        period_text = Paragraph(
            f"Período: {period['start']} a {period['end']}<br/>Emissão: {datetime.now().strftime('%d/%m/%Y')}",
            self.styles['EmployeeInfo']
        )
        self.elements.append(period_text)
        
        self.elements.append(Spacer(1, 0.25*inch))

    def add_employee_info(self, employee_data):
        """Adiciona informações do funcionário"""
        info_lines = [
            f"<b>Funcionário:</b> {employee_data['name']}",
            f"<b>Departamento:</b> {employee_data['department']}",
            f"<b>Matrícula:</b> {employee_data['id']}",
            f"<b>Data de admissão:</b> {employee_data['admission_date']}",
            f"<b>Cargo:</b> {employee_data['position']}",
            f"<b>CTPS:</b> {employee_data['ctps']}",
            f"<b>PIS:</b> {employee_data['pis']}"
        ]
        
        for line in info_lines:
            p = Paragraph(line, self.styles['EmployeeInfo'])
            self.elements.append(p)
        
        self.elements.append(Spacer(1, 0.25*inch))

    def add_time_table(self, data):
        """Adiciona tabela de registros de ponto"""
        # Cabeçalho da tabela
        header = [
            "Dia", "Turno", "Ent. 1", "Saí. 1", 
            "Ent. 2", "Saí. 2", "Horas", "Observações"
        ]
        
        # Converter dados para formato de tabela
        table_data = [header]
        for row in data:
            table_data.append([
                row['day'],
                row['shift'],
                row['entry1'],
                row['exit1'],
                row['entry2'],
                row['exit2'],
                row['hours'],
                row['notes']
            ])
        
        # Criar tabela
        table = Table(table_data, colWidths=[0.8*inch, 1.2*inch] + [0.6*inch]*5 + [1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.25*inch))

    def add_summary(self, summary_data):
        """Adiciona resumo mensal"""
        summary_lines = [
            f"<b>Totais:</b> {summary_data['total_hours']}",
            f"<b>Dias trabalhados:</b> {summary_data['worked_days']}",
            f"<b>Faltas:</b> {summary_data['absences']}",
            f"<b>Atrasos:</b> {summary_data['delays']}"
        ]
        
        for line in summary_lines:
            p = Paragraph(line, self.styles['EmployeeInfo'])
            self.elements.append(p)
        
        self.elements.append(Spacer(1, 0.25*inch))

    def add_salary_info(self, salary_data):
        """Adiciona informações salariais"""
        salary_lines = [
            "<b>Cálculo Salarial:</b>",
            f"Salário Bruto: R$ {locale.currency(salary_data['bruto'], grouping=True, symbol=False)}",
            f"INSS: R$ {locale.currency(salary_data['inss'], grouping=True, symbol=False)}",
            f"IRRF: R$ {locale.currency(salary_data['irrf'], grouping=True, symbol=False)}",
            f"Salário Líquido: R$ {locale.currency(salary_data['liquido'], grouping=True, symbol=False)}",
            f"Proporcional ({salary_data['worked_days']} dias): R$ {locale.currency(salary_data['proporcional'], grouping=True, symbol=False)}"
        ]
        
        for line in salary_lines:
            p = Paragraph(line, self.styles['EmployeeInfo'])
            self.elements.append(p)
        
        self.elements.append(Spacer(1, 0.25*inch))

    def add_footer(self, employee_name):
        """Adiciona rodapé com assinatura"""
        self.elements.append(Spacer(1, 0.5*inch))
        self.elements.append(Paragraph("Confirmo as informações acima.", self.styles['EmployeeInfo']))
        
        date_info = Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", self.styles['EmployeeInfo'])
        signature_line = "_" * 30
        signature = Paragraph(f"{signature_line}<br/>{employee_name}", self.styles['EmployeeInfo'])
        
        col_widths = [3*inch, 3*inch]
        footer_table = Table([[date_info, signature]], colWidths=col_widths)
        self.elements.append(footer_table)

    def generate(self):
        """Gera o documento PDF"""
        self.doc.build(self.elements)
        return self.filename

# Exemplo de uso
if __name__ == "__main__":
    # Dados de exemplo
    company_info = {
        'name': 'Imobiliaria Celeste LTDA EPP',
        'address': 'Rua das Aroeiras, 617',
        'city': 'Sinop',
        'state': 'MT',
        'cep': '78550-224',
        'cnpj': '04.052.691/0001-28'
    }
    
    employee_data = {
        'name': 'Alliabson Lourenço da Fonseca',
        'department': 'Geral',
        'id': '146',
        'admission_date': '17/05/2017',
        'position': 'AUXILIAR ADMINISTRATIVO',
        'ctps': '71840',
        'pis': '203.68460.25-2'
    }
    
    # Gerar PDF
    pdf = PDFGenerator("relatorio_ponto.pdf")
    pdf.add_header(company_info)
    pdf.add_report_title("Relatório de Frequência Individual", {
        'start': '01/05/2025',
        'end': '31/05/2025'
    })
    pdf.add_employee_info(employee_data)
    
    # Adicionar dados de exemplo à tabela
    sample_data = [
        {
            'day': '01/05 Qui',
            'shift': '07:12 10:30 12:00 17:30',
            'entry1': '07:12',
            'exit1': '10:30',
            'entry2': '12:00',
            'exit2': '17:30',
            'hours': '08:48',
            'notes': ''
        },
        {
            'day': '02/05 Sex',
            'shift': '07:12 10:30 12:00 17:30',
            'entry1': '07:12',
            'exit1': '10:30',
            'entry2': '12:00',
            'exit2': '17:30',
            'hours': '08:48',
            'notes': 'Entr. Atrasada(*)'
        }
    ]
    pdf.add_time_table(sample_data)
    
    pdf.add_summary({
        'total_hours': '177:42',
        'worked_days': 22,
        'absences': 0,
        'delays': 5
    })
    
    pdf.add_salary_info({
        'bruto': 2500.00,
        'inss': 225.00,
        'irrf': 142.80,
        'liquido': 2132.20,
        'proporcional': 2500.00,
        'worked_days': 22
    })
    
    pdf.add_footer(employee_data['name'])
    pdf.generate()
