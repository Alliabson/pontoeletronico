import streamlit as st
from datetime import datetime, time, timedelta
import pandas as pd
import re
import os
from pathlib import Path
from dotenv import load_dotenv

# --- Versão Aprimorada do Seu Código Original ---
# Mantendo toda a estrutura mas com as correções necessárias

# Configurações iniciais - SEM locale
load_dotenv()
st.set_page_config(layout="wide", page_title="Controle de Ponto Eletrônico", page_icon="⏱️")

# --- Funções de Cálculo Integradas ---
def calculate_worked_hours(ent1, sai1, ent2, sai2):
    """Calcula horas trabalhadas no formato HH:MM"""
    try:
        def time_to_minutes(t):
            if not t or t in ["--:--", ""]:
                return 0
            h, m = map(int, t.split(':'))
            return h * 60 + m
        
        total = (time_to_minutes(sai1) - time_to_minutes(ent1)) + \
                (time_to_minutes(sai2) - time_to_minutes(ent2))
        return f"{total//60:02d}:{total%60:02d}" if total > 0 else "00:00"
    except:
        return "00:00"

def calculate_daily_salary(salario_bruto, dias_base=22):
    """Calcula valor por dia de trabalho"""
    try:
        return float(salario_bruto) / dias_base
    except:
        return 0.0

def calculate_taxes(salario_bruto, dependentes=0):
    """Calcula INSS e IRRF conforme tabelas vigentes"""
    # Cálculo do INSS (atualizado)
    if salario_bruto <= 1320.00:
        inss = salario_bruto * 0.075
    elif salario_bruto <= 2571.29:
        inss = (salario_bruto - 1320.00) * 0.09 + 99.00
    elif salario_bruto <= 3856.94:
        inss = (salario_bruto - 2571.29) * 0.12 + 99.00 + 112.62
    elif salario_bruto <= 7507.49:
        inss = (salario_bruto - 3856.94) * 0.14 + 99.00 + 112.62 + 154.28
    else:
        inss = 7507.49 * 0.14
    
    # Cálculo do IRRF
    base_irrf = salario_bruto - inss - (dependentes * 189.59)
    
    if base_irrf <= 1903.98:
        irrf = 0
    elif base_irrf <= 2826.65:
        irrf = base_irrf * 0.075 - 142.80
    elif base_irrf <= 3751.05:
        irrf = base_irrf * 0.15 - 354.80
    elif base_irrf <= 4664.68:
        irrf = base_irrf * 0.225 - 636.13
    else:
        irrf = base_irrf * 0.275 - 869.36
    
    return {
        'inss': inss,
        'irrf': max(0, irrf)  # Não pode ser negativo
    }

def calculate_salary(
    salario_bruto,
    dias_trabalhados,
    horas_extras=0,
    adicional_noturno=0,
    outros_beneficios=0,
    outros_descontos=0,
    dependentes=0
):
    """Calcula o salário líquido com todos os benefícios e descontos"""
    # Cálculo de vencimentos
    valor_dia = calculate_daily_salary(salario_bruto)
    valor_hora = salario_bruto / 220  # Base de 220 horas mensais
    
    proporcional = valor_dia * dias_trabalhados
    valor_horas_extras = horas_extras * valor_hora * 1.5  # 50% de acréscimo
    
    total_vencimentos = proporcional + adicional_noturno + valor_horas_extras + outros_beneficios
    
    # Cálculo de descontos
    taxes = calculate_taxes(proporcional, dependentes)
    total_descontos = taxes['inss'] + taxes['irrf'] + outros_descontos
    
    liquido = total_vencimentos - total_descontos
    
    return {
        'bruto': salario_bruto,
        'proporcional': proporcional,
        'horas_extras': valor_horas_extras,
        'adicional_noturno': adicional_noturno,
        'outros_beneficios': outros_beneficios,
        'inss': taxes['inss'],
        'irrf': taxes['irrf'],
        'outros_descontos': outros_descontos,
        'total_vencimentos': total_vencimentos,
        'total_descontos': total_descontos,
        'liquido': max(0, liquido),  # Salário não pode ser negativo
        'dias_trabalhados': dias_trabalhados
    }

# --- Funções de Formatação Alternativas ---
def format_currency(value):
    """Formata valores monetários sem dependência de locale"""
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def format_date(date_obj):
    """Formata datas no formato dd/mm/aaaa"""
    if isinstance(date_obj, str):
        return date_obj
    try:
        return date_obj.strftime('%d/%m/%Y')
    except:
        return "00/00/0000"

# --- Configuração de Armazenamento (Mantido do seu original) ---
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
EMPLOYEE_RECORDS_FILE = DATA_DIR / "employee_records.csv"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

def load_employee_data():
    """Carrega os dados dos funcionários do arquivo CSV"""
    if EMPLOYEE_RECORDS_FILE.exists():
        df = pd.read_csv(EMPLOYEE_RECORDS_FILE, parse_dates=['periodo_inicio', 'periodo_fim'])
        time_cols = ['Ent. 1', 'Saí. 1', 'Ent. 2', 'Saí. 2']
        for col in time_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
    return pd.DataFrame()

def save_employee_data(df):
    """Salva os dados dos funcionários no arquivo CSV"""
    df.to_csv(EMPLOYEE_RECORDS_FILE, index=False)

def create_backup():
    """Cria um backup dos dados"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"backup_{timestamp}.csv"
    
    if EMPLOYEE_RECORDS_FILE.exists():
        df = pd.read_csv(EMPLOYEE_RECORDS_FILE)
        df.to_csv(backup_file, index=False)
        st.success(f"Backup criado: {backup_file.name}")

# --- Funções auxiliares ---
def load_css():
    """Carrega o CSS personalizado"""
    css = """
    <style>
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #eee;
        }
        .company-info h2 {
            margin: 0;
            color: #1e3a8a;
        }
        .time-input {
            font-family: monospace;
        }
        .stButton>button {
            background-color: #1e3a8a;
            color: white;
        }
        .summary-card {
            border-radius: 0.5rem;
            padding: 1rem;
            background-color: #f8f9fa;
            margin-bottom: 1rem;
        }
        .history-table {
            font-size: 0.9rem;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def validate_time(time_str):
    """Valida se a string está no formato HH:MM"""
    if not time_str or time_str in ["--:--", ""]:
        return None
    return re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time_str)

def calculate_day_hours(row):
    """Calcula horas trabalhadas e verifica atrasos"""
    turno_parts = row['Turno'].split()
    expected = {
        'ent1': turno_parts[0] if len(turno_parts) > 0 else None,
        'sai1': turno_parts[1] if len(turno_parts) > 1 else None,
        'ent2': turno_parts[2] if len(turno_parts) > 2 else None,
        'sai2': turno_parts[3] if len(turno_parts) > 3 else None
    }
    
    # Obter horários registrados
    registrado = {
        'ent1': row['Ent. 1'] if validate_time(row['Ent. 1']) else None,
        'sai1': row['Saí. 1'] if validate_time(row['Saí. 1']) else None,
        'ent2': row['Ent. 2'] if validate_time(row['Ent. 2']) else None,
        'sai2': row['Saí. 2'] if validate_time(row['Saí. 2']) else None
    }
    
    # Calcular horas trabalhadas
    horas_trabalhadas = calculate_worked_hours(
        registrado['ent1'], registrado['sai1'],
        registrado['ent2'], registrado['sai2']
    )
    
    # Verificar atrasos
    observacoes = []
    if all([expected['ent1'], registrado['ent1']]):
        expected_min = int(expected['ent1'].split(':')[0]) * 60 + int(expected['ent1'].split(':')[1])
        registered_min = int(registrado['ent1'].split(':')[0]) * 60 + int(registrado['ent1'].split(':')[1])
        
        if registered_min > expected_min:
            atraso_min = registered_min - expected_min
            observacoes.append(f"Entr. Atrasada ({atraso_min}min)")
    
    return horas_trabalhadas, ", ".join(observacoes) if observacoes else ""

def generate_pdf(employee_data, ponto_data, salary_data=None):
    """Gera o PDF do relatório de ponto"""
    pdf = PDFGenerator("relatorio_ponto.pdf")
    
    # Informações da empresa
    company_info = {
        'name': 'Imobiliaria Celeste LTDA EPP',
        'address': 'Rua das Aroeiras, 617',
        'city': 'Sinop',
        'state': 'MT',
        'cep': '78550-224',
        'cnpj': '04.052.691/0001-28'
    }
    
    # Informações do funcionário
    employee_pdf_data = {
        'name': employee_data['nome'],
        'department': employee_data.get('departamento', 'Geral'),
        'id': employee_data['matricula'],
        'admission_date': employee_data.get('admission_date', '17/05/2017'),
        'position': employee_data.get('cargo', 'AUXILIAR ADMINISTRATIVO'),
        'ctps': employee_data.get('ctps', '71840'),
        'pis': employee_data.get('pis', '203.68460.25-2')
    }
    
    # Adicionar conteúdo ao PDF
    pdf.add_header(company_info)
    pdf.add_report_title("Relatório de Frequência Individual", {
        'start': employee_data['periodo_inicio'].strftime('%d/%m/%Y'),
        'end': employee_data['periodo_fim'].strftime('%d/%m/%Y')
    })
    pdf.add_employee_info(employee_pdf_data)
    
    # Preparar dados da tabela de ponto
    table_data = []
    for _, row in ponto_data.iterrows():
        table_data.append({
            'day': row['Dia'],
            'shift': row['Turno'],
            'entry1': row['Ent. 1'],
            'exit1': row['Saí. 1'],
            'entry2': row['Ent. 2'],
            'exit2': row['Saí. 2'],
            'hours': row['Horas'],
            'notes': row['Observações']
        })
    
    pdf.add_time_table(table_data)
    
    # Adicionar cálculo salarial se disponível
    if salary_data:
        pdf.add_salary_info(salary_data)
    
    # Gerar PDF
    pdf_path = pdf.generate()
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    st.download_button(
        label="Baixar Relatório em PDF",
        data=pdf_bytes,
        file_name="relatorio_ponto.pdf",
        mime="application/pdf"
    )

# --- Componentes da UI ---
def render_header():
    """Renderiza o cabeçalho da aplicação"""
    st.markdown("""
    <div class="header">
        <div class="company-info">
            <h2>Imobiliaria Celeste LTDA EPP</h2>
            <p>Rua das Aroeiras, 617 - Sinop/MT - CEP: 78550-224</p>
            <p>CNPJ: 04.052.691/0001-28 - Emissão: {}</p>
        </div>
    </div>
    """.format(datetime.now().strftime('%d/%m/%Y')), unsafe_allow_html=True)

def employee_info_form(employee_data_df):
    """Formulário de informações do funcionário com opção para novo cadastro"""
    with st.expander("Informações do Funcionário", expanded=True):
        # Campo de matrícula (ID único)
        matricula = st.text_input("Matrícula (ID único)*", key="matricula_input")
        
        if not matricula:
            st.warning("Por favor, insira a matrícula para continuar")
            return None
        
        # Verificar se é um funcionário novo
        is_new_employee = True
        existing_data = None
        
        if not employee_data_df.empty:
            # Converter matrícula para string para comparação
            employee_data_df['matricula'] = employee_data_df['matricula'].astype(str)
            if matricula in employee_data_df['matricula'].values:
                is_new_employee = False
                # Pegar o registro mais recente para esta matrícula
                existing_records = employee_data_df[employee_data_df['matricula'] == matricula]
                existing_data = existing_records.iloc[-1].to_dict()
                st.success("Dados do funcionário carregados!")
        
        # Campos do formulário com valores padrão ou existentes
        nome = st.text_input("Nome do Funcionário*", 
                           value=existing_data.get('nome', '') if existing_data else "")
        departamento = st.text_input("Departamento*", 
                                   value=existing_data.get('departamento', 'Geral') if existing_data else "Geral")
        cargo = st.text_input("Cargo*", 
                            value=existing_data.get('cargo', 'AUXILIAR ADMINISTRATIVO') if existing_data else "AUXILIAR ADMINISTRATIVO")
        
        # Converter string para date se necessário
        def parse_date(date_str, default):
            if isinstance(date_str, str):
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    return default
            return date_str if date_str else default
        
        salario_bruto = st.number_input("Salário Bruto (R$)*", 
                                      min_value=0.0, 
                                      value=float(existing_data.get('salario_bruto', 0.0)) if existing_data else 0.0, 
                                      step=100.0)
        
        periodo_inicio = st.date_input("Período Início*", 
                                     value=parse_date(existing_data.get('periodo_inicio'), datetime.now().replace(day=1).date()) if existing_data else datetime.now().replace(day=1).date())
        
        periodo_fim = st.date_input("Período Fim*", 
                                  value=parse_date(existing_data.get('periodo_fim'), datetime.now().date()) if existing_data else datetime.now().date())
        
        # Mensagem para novo funcionário
        if is_new_employee:
            st.info("Novo funcionário detectado. Preencha todos os campos obrigatórios (*)")
        
        # Validar campos obrigatórios
        if not nome or not departamento or not cargo or salario_bruto <= 0:
            st.error("Preencha todos os campos obrigatórios (*)")
            return None
    
    return {
        "matricula": matricula,
        "nome": nome,
        "departamento": departamento,
        "cargo": cargo,
        "salario_bruto": salario_bruto,
        "periodo_inicio": periodo_inicio,
        "periodo_fim": periodo_fim
    }

def ponto_table(employee_data, employee_data_df):
    """Tabela de registro de ponto com cálculo automático"""
    st.subheader("Registro Diário de Ponto")
    
    # Verificar se há dados anteriores para este funcionário no período
    existing_records = pd.DataFrame()
    if not employee_data_df.empty:
        # Converter para strings para comparação
        periodo_inicio_str = employee_data['periodo_inicio'].strftime('%Y-%m-%d')
        periodo_fim_str = employee_data['periodo_fim'].strftime('%Y-%m-%d')
        
        mask = (employee_data_df['matricula'].astype(str) == str(employee_data['matricula'])) & \
               (employee_data_df['periodo_inicio'].astype(str) == periodo_inicio_str) & \
               (employee_data_df['periodo_fim'].astype(str) == periodo_fim_str)
        
        existing_records = employee_data_df[mask]
    
    # Criar dataframe com os dias do período
    dates = pd.date_range(start=employee_data["periodo_inicio"], end=employee_data["periodo_fim"])
    data = []
    
    for date in dates:
        weekday = date.strftime('%a')[:3].upper()
        day_str = f"{date.day:02d}/{date.month:02d} {weekday}"
        
        # Verificar se já existe registro para este dia
        existing_day_data = None
        if not existing_records.empty:
            day_mask = existing_records['Dia'].str.startswith(f"{date.day:02d}/{date.month:02d}")
            if any(day_mask):
                existing_day_data = existing_records[day_mask].iloc[0]
        
        if date.weekday() < 5:  # Dias úteis
            data.append({
                "Dia": day_str,
                "Turno": "07:12 10:30 12:00 17:30",
                "Ent. 1": existing_day_data['Ent. 1'] if existing_day_data is not None else "07:12",
                "Saí. 1": existing_day_data['Saí. 1'] if existing_day_data is not None else "10:30",
                "Ent. 2": existing_day_data['Ent. 2'] if existing_day_data is not None else "12:00",
                "Saí. 2": existing_day_data['Saí. 2'] if existing_day_data is not None else "17:30",
                "Horas": existing_day_data['Horas'] if existing_day_data is not None else "08:48",
                "Observações": existing_day_data['Observações'] if existing_day_data is not None else ""
            })
        else:  # Final de semana
            data.append({
                "Dia": day_str,
                "Turno": "--:-- --:-- --:-- --:--",
                "Ent. 1": "--:--",
                "Saí. 1": "--:--",
                "Ent. 2": "--:--",
                "Saí. 2": "--:--",
                "Horas": "00:00",
                "Observações": ""
            })
    
    df = pd.DataFrame(data)
    
    # Criar editor de dados com atualização em tempo real
    edited_df = st.data_editor(
        df,
        num_rows="fixed",
        column_config={
            "Dia": st.column_config.TextColumn("Dia", disabled=True),
            "Turno": st.column_config.TextColumn("Turno", disabled=True),
            "Ent. 1": st.column_config.TextColumn("Ent. 1"),
            "Saí. 1": st.column_config.TextColumn("Saí. 1"),
            "Ent. 2": st.column_config.TextColumn("Ent. 2"),
            "Saí. 2": st.column_config.TextColumn("Saí. 2"),
            "Horas": st.column_config.TextColumn("Horas", disabled=True),
            "Observações": st.column_config.TextColumn("Observações", disabled=True)
        },
        key="ponto_editor",
        hide_index=True,
        use_container_width=True
    )
    
    # Atualizar cálculos para cada linha
    for idx in edited_df.index:
        if edited_df.at[idx, 'Turno'] != "--:-- --:-- --:-- --:--":
            horas, obs = calculate_day_hours(edited_df.loc[idx])
            edited_df.at[idx, 'Horas'] = horas
            edited_df.at[idx, 'Observações'] = obs
    
    return edited_df

def save_current_data(employee_data, ponto_data, employee_data_df):
    """Salva os dados atuais no arquivo CSV"""
    # Preparar dados para salvar
    save_data = ponto_data.copy()
    for key, value in employee_data.items():
        save_data[key] = value
    
    # Converter datas para string
    save_data['periodo_inicio'] = employee_data['periodo_inicio'].strftime('%Y-%m-%d')
    save_data['periodo_fim'] = employee_data['periodo_fim'].strftime('%Y-%m-%d')
    
    # Remover registros antigos do mesmo período
    if not employee_data_df.empty:
        mask = ~((employee_data_df['matricula'] == employee_data['matricula']) & 
                (employee_data_df['periodo_inicio'] == save_data['periodo_inicio'].iloc[0]) & 
                (employee_data_df['periodo_fim'] == save_data['periodo_fim'].iloc[0]))
        employee_data_df = employee_data_df[mask]
    
    # Concatenar com dados existentes
    updated_df = pd.concat([employee_data_df, save_data], ignore_index=True)
    
    # Salvar dados
    save_employee_data(updated_df)
    st.success("Dados salvos com sucesso!")
    create_backup()


def render_summary(employee_data, df_ponto):
    """Renderiza o resumo mensal com cálculos"""
    st.subheader("Resumo Mensal")
    
    total_minutos = sum(
        int(h.split(':')[0]) * 60 + int(h.split(':')[1]) 
        for h in df_ponto['Horas'] if h != "00:00"
    )
    horas_trabalhadas = f"{total_minutos // 60:02d}:{total_minutos % 60:02d}"
    
    dias_uteis = len([d for d in pd.date_range(
        start=employee_data["periodo_inicio"],
        end=employee_data["periodo_fim"]
    ) if d.weekday() < 5])
    
    dias_trabalhados = len([h for h in df_ponto['Horas'] if h != "00:00"])
    faltas = max(0, dias_uteis - dias_trabalhados)
    
    salario_diario = calculate_daily_salary(employee_data["salario_bruto"])
    
    cols = st.columns(4)
    cols[0].metric("Horas Trabalhadas", horas_trabalhadas)
    cols[1].metric("Dias Trabalhados", dias_trabalhados)
    cols[2].metric("Faltas", faltas)
    cols[3].metric("Valor por Dia", format_currency(salario_diario))
    
    with st.expander("Cálculo Salarial Detalhado", expanded=True):
        cols = st.columns(2)
        
        with cols[0]:
            horas_extras = st.number_input("Horas Extras", min_value=0.0, value=0.0, step=0.5)
            adicional_noturno = st.number_input("Adicional Noturno (R$)", min_value=0.0, value=0.0)
            dependentes = st.number_input("Dependentes IR", min_value=0, value=0, max_value=10)
        
        with cols[1]:
            outros_descontos = st.number_input("Outros Descontos (R$)", min_value=0.0, value=0.0)
            outros_beneficios = st.number_input("Outros Benefícios (R$)", min_value=0.0, value=0.0)
        
        if st.button("Calcular Salário Líquido"):
            salary_data = calculate_salary(
                salario_bruto=employee_data["salario_bruto"],
                dias_trabalhados=dias_trabalhados,
                horas_extras=horas_extras,
                adicional_noturno=adicional_noturno,
                outros_beneficios=outros_beneficios,
                outros_descontos=outros_descontos,
                dependentes=dependentes
            )
            
            st.markdown("### Resultado do Cálculo")
            
            cols = st.columns(2)
            with cols[0]:
                st.markdown(f"""
                **Salário Bruto:** {format_currency(salary_data['bruto'])}  
                **Adicional Noturno:** {format_currency(salary_data['adicional_noturno'])}  
                **Horas Extras:** {format_currency(salary_data['horas_extras'])}  
                **Outros Benefícios:** {format_currency(salary_data['outros_beneficios'])}  
                **Total de Vencimentos:** {format_currency(salary_data['total_vencimentos'])}
                """)
            
            with cols[1]:
                st.markdown(f"""
                **INSS:** {format_currency(salary_data['inss'])}  
                **IRRF:** {format_currency(salary_data['irrf'])}  
                **Outros Descontos:** {format_currency(salary_data['outros_descontos'])}  
                **Total de Descontos:** {format_currency(salary_data['total_descontos'])}  
                **Salário Líquido:** {format_currency(salary_data['liquido'])}
                """)
            
            st.markdown(f"""
            **Proporcional ({dias_trabalhados} dias):** {format_currency(salary_data['proporcional'])}
            """)
            
            # Botão para gerar PDF com os cálculos
            if st.button("Gerar Relatório Completo em PDF"):
                generate_pdf(employee_data, df_ponto, salary_data)
                
            # Botão para salvar os dados
            if st.button("Salvar Dados do Cálculo"):
                # Adicionar dados do cálculo ao DataFrame de pontos
                save_data = df_ponto.copy()
                for key, value in employee_data.items():
                    save_data[key] = value
                save_data['horas_extras'] = horas_extras
                save_data['salario_liquido'] = salary_data['liquido']
                
                save_current_data(employee_data, save_data, load_employee_data())
                st.success("Dados do cálculo salvos com sucesso!")

def show_history(employee_data):
    """Mostra o histórico do funcionário"""
    st.subheader("Histórico de Registros")
    
    employee_data_df = load_employee_data()
    if not employee_data_df.empty and 'matricula' in employee_data:
        history_df = employee_data_df[employee_data_df['matricula'] == employee_data['matricula']]
        
        if not history_df.empty:
            # Mostrar últimos registros
            st.dataframe(
                history_df.sort_values('periodo_inicio', ascending=False).head(10),
                use_container_width=True,
                column_order=["periodo_inicio", "periodo_fim", "Horas", "Observações"]
            )
            
            # Opção para restaurar um registro antigo
            with st.expander("Restaurar Registro Antigo"):
                selected_period = st.selectbox(
                    "Selecione um período para restaurar",
                    options=history_df['periodo_inicio'].unique()
                )
                
                if st.button("Restaurar Registro Selecionado"):
                    selected_data = history_df[history_df['periodo_inicio'] == selected_period].iloc[0]
                    st.session_state['restore_data'] = selected_data
                    st.success("Registro selecionado pronto para restauração!")
        else:
            st.info("Nenhum histórico encontrado para este funcionário.")
    else:
        st.info("Nenhum histórico disponível.")

# --- Aplicação principal ---
def main():
    try:
        load_css()
        render_header()
        
        # Carregar dados existentes
        employee_data_df = load_employee_data()
        
        # Informações do funcionário
        employee_data = employee_info_form(employee_data_df)
        
        if employee_data:
            # Tabela de ponto
            df_ponto = ponto_table(employee_data, employee_data_df)
            
            # Resumo e cálculos
            render_summary(employee_data, df_ponto)
            
            # Mostrar histórico
            show_history(employee_data)
            
            # Botão para salvar os dados do ponto
            if st.button("Salvar Registros de Ponto"):
                save_current_data(employee_data, df_ponto, employee_data_df)
            
            # Assinatura
            st.divider()
            st.text_input("Assinatura:", value=employee_data["nome"])
            
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {str(e)}")
        st.info("Por favor, recarregue a página e tente novamente. Se o problema persistir, entre em contato com o suporte.")

if __name__ == "__main__":
    main()
