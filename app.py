import streamlit as st
from datetime import datetime, time, timedelta
import pandas as pd
import re
import os
from pathlib import Path
from dotenv import load_dotenv

# --- Configurações iniciais ---
load_dotenv()
st.set_page_config(layout="wide", page_title="Controle de Ponto Eletrônico", page_icon="⏱️")

# --- Funções de Cálculo ---
def calculate_worked_hours(ent1, sai1, ent2, sai2):
    """Calcula o total de horas trabalhadas no formato HH:MM"""
    times = [ent1, sai1, ent2, sai2]
    if any(not t or t == "--:--" for t in times):
        return "00:00"
    
    try:
        def to_minutes(time_str):
            h, m = map(int, time_str.split(':'))
            return h * 60 + m
        
        total_minutes = (to_minutes(sai1) - to_minutes(ent1)) + (to_minutes(sai2) - to_minutes(ent2))
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours:02d}:{minutes:02d}"
    except:
        return "00:00"

def calculate_daily_salary(salario_bruto, dias_base=22):
    return salario_bruto / dias_base

def calculate_taxes(salario_bruto, dependentes=0):
    """Calcula INSS e IRRF"""
    # Cálculo do INSS
    if salario_bruto <= 1320.00:
        inss = salario_bruto * 0.075
    elif salario_bruto <= 2571.29:
        inss = (salario_bruto - 1320.00) * 0.09 + 99.00
    elif salario_bruto <= 3856.94:
        inss = (salario_bruto - 2571.29) * 0.12 + 99.00 + 112.62
    else:
        inss = (salario_bruto - 3856.94) * 0.14 + 99.00 + 112.62 + 154.28
    
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
    
    return {'inss': inss, 'irrf': max(0, irrf)}

def calculate_salary(salario_bruto, dias_trabalhados, horas_extras=0, adicional_noturno=0,
                   outros_beneficios=0, outros_descontos=0, dependentes=0):
    """Calcula salário líquido"""
    valor_dia = calculate_daily_salary(salario_bruto)
    valor_hora = salario_bruto / 220
    
    proporcional = valor_dia * dias_trabalhados
    valor_he = horas_extras * valor_hora * 1.5
    
    taxes = calculate_taxes(proporcional, dependentes)
    
    return {
        'bruto': salario_bruto,
        'proporcional': proporcional,
        'horas_extras': valor_he,
        'adicional_noturno': adicional_noturno,
        'outros_beneficios': outros_beneficios,
        'inss': taxes['inss'],
        'irrf': taxes['irrf'],
        'outros_descontos': outros_descontos,
        'total_vencimentos': proporcional + valor_he + adicional_noturno + outros_beneficios,
        'total_descontos': taxes['inss'] + taxes['irrf'] + outros_descontos,
        'liquido': (proporcional + valor_he + adicional_noturno + outros_beneficios) - 
                  (taxes['inss'] + taxes['irrf'] + outros_descontos)
    }

# --- Funções de Formatação ---
def format_currency(value):
    """Formata valores monetários"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_date(date_obj):
    """Formata datas no formato dd/mm/aaaa"""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime('%d/%m/%Y')

# --- Configuração de Armazenamento ---
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
EMPLOYEE_RECORDS_FILE = DATA_DIR / "employee_records.csv"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

def load_employee_data():
    """Carrega os dados dos funcionários"""
    if EMPLOYEE_RECORDS_FILE.exists():
        df = pd.read_csv(EMPLOYEE_RECORDS_FILE, parse_dates=['periodo_inicio', 'periodo_fim'])
        time_cols = ['Ent. 1', 'Saí. 1', 'Ent. 2', 'Saí. 2']
        for col in time_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
    return pd.DataFrame()

def save_employee_data(df):
    """Salva os dados dos funcionários"""
    df.to_csv(EMPLOYEE_RECORDS_FILE, index=False)

def create_backup():
    """Cria backup dos dados"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"backup_{timestamp}.csv"
    if EMPLOYEE_RECORDS_FILE.exists():
        df = pd.read_csv(EMPLOYEE_RECORDS_FILE)
        df.to_csv(backup_file, index=False)
        st.success(f"Backup criado: {backup_file.name}")

# --- Componentes da UI ---
def load_css():
    """Carrega CSS personalizado"""
    st.markdown("""
    <style>
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid #eee; }
        .company-info h2 { margin: 0; color: #1e3a8a; }
        .time-input { font-family: monospace; }
        .stButton>button { background-color: #1e3a8a; color: white; }
        .summary-card { border-radius: 0.5rem; padding: 1rem; background-color: #f8f9fa; margin-bottom: 1rem; }
        .history-table { font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Renderiza o cabeçalho"""
    st.markdown(f"""
    <div class="header">
        <div class="company-info">
            <h2>Imobiliaria Celeste LTDA EPP</h2>
            <p>Rua das Aroeiras, 617 - Sinop/MT - CEP: 78550-224</p>
            <p>CNPJ: 04.052.691/0001-28 - Emissão: {datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def employee_info_form(employee_data_df):
    """Formulário de informações do funcionário"""
    with st.expander("Informações do Funcionário", expanded=True):
        matricula = st.text_input("Matrícula (ID único)*", key="matricula_input")
        if not matricula:
            st.warning("Por favor, insira a matrícula para continuar")
            return None
        
        is_new_employee = True
        existing_data = None
        
        if not employee_data_df.empty:
            employee_data_df['matricula'] = employee_data_df['matricula'].astype(str)
            if matricula in employee_data_df['matricula'].values:
                is_new_employee = False
                existing_records = employee_data_df[employee_data_df['matricula'] == matricula]
                existing_data = existing_records.iloc[-1].to_dict()
                st.success("Dados do funcionário carregados!")
        
        nome = st.text_input("Nome do Funcionário*", value=existing_data.get('nome', '') if existing_data else "")
        departamento = st.text_input("Departamento*", value=existing_data.get('departamento', 'Geral') if existing_data else "Geral")
        cargo = st.text_input("Cargo*", value=existing_data.get('cargo', 'AUXILIAR ADMINISTRATIVO') if existing_data else "AUXILIAR ADMINISTRATIVO")
        salario_bruto = st.number_input("Salário Bruto (R$)*", min_value=0.0, value=float(existing_data.get('salario_bruto', 0.0)) if existing_data else 0.0, step=100.0)
        
        def parse_date(date_str, default):
            if isinstance(date_str, str):
                try: return datetime.strptime(date_str, '%Y-%m-%d').date()
                except: return default
            return date_str if date_str else default
        
        periodo_inicio = st.date_input("Período Início*", value=parse_date(existing_data.get('periodo_inicio'), datetime.now().replace(day=1).date()) if existing_data else datetime.now().replace(day=1).date())
        periodo_fim = st.date_input("Período Fim*", value=parse_date(existing_data.get('periodo_fim'), datetime.now().date()) if existing_data else datetime.now().date())
        
        if is_new_employee:
            st.info("Novo funcionário detectado. Preencha todos os campos obrigatórios (*)")
        
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
    """Tabela de registro de ponto"""
    st.subheader("Registro Diário de Ponto")
    
    existing_records = pd.DataFrame()
    if not employee_data_df.empty:
        periodo_inicio_str = employee_data['periodo_inicio'].strftime('%Y-%m-%d')
        periodo_fim_str = employee_data['periodo_fim'].strftime('%Y-%m-%d')
        mask = ((employee_data_df['matricula'].astype(str) == str(employee_data['matricula'])) & \
               (employee_data_df['periodo_inicio'].astype(str) == periodo_inicio_str) & \
               (employee_data_df['periodo_fim'].astype(str) == periodo_fim_str)
        existing_records = employee_data_df[mask]
    
    dates = pd.date_range(start=employee_data["periodo_inicio"], end=employee_data["periodo_fim"])
    data = []
    
    for date in dates:
        weekday = date.strftime('%a')[:3].upper()
        day_str = f"{date.day:02d}/{date.month:02d} {weekday}"
        
        existing_day_data = None
        if not existing_records.empty:
            day_mask = existing_records['Dia'].str.startswith(f"{date.day:02d}/{date.month:02d}")
            if any(day_mask):
                existing_day_data = existing_records[day_mask].iloc[0]
        
        if date.weekday() < 5:
            data.append({
                "Dia": day_str,
                "Turno": "07:12 10:30 12:00 17:30",
                "Ent. 1": existing_day_data['Ent. 1'] if existing_day_data else "07:12",
                "Saí. 1": existing_day_data['Saí. 1'] if existing_day_data else "10:30",
                "Ent. 2": existing_day_data['Ent. 2'] if existing_day_data else "12:00",
                "Saí. 2": existing_day_data['Saí. 2'] if existing_day_data else "17:30",
                "Horas": existing_day_data['Horas'] if existing_day_data else "08:48",
                "Observações": existing_day_data['Observações'] if existing_day_data else ""
            })
        else:
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
    
    for idx in edited_df.index:
        if edited_df.at[idx, 'Turno'] != "--:-- --:-- --:-- --:--":
            horas = calculate_worked_hours(
                edited_df.at[idx, 'Ent. 1'],
                edited_df.at[idx, 'Saí. 1'],
                edited_df.at[idx, 'Ent. 2'],
                edited_df.at[idx, 'Saí. 2']
            )
            edited_df.at[idx, 'Horas'] = horas
    
    return edited_df

def save_current_data(employee_data, ponto_data, employee_data_df):
    """Salva os dados atuais"""
    save_data = ponto_data.copy()
    for key, value in employee_data.items():
        save_data[key] = value
    
    save_data['periodo_inicio'] = employee_data['periodo_inicio'].strftime('%Y-%m-%d')
    save_data['periodo_fim'] = employee_data['periodo_fim'].strftime('%Y-%m-%d')
    
    if not employee_data_df.empty:
        mask = ~((employee_data_df['matricula'] == employee_data['matricula']) & 
                (employee_data_df['periodo_inicio'] == save_data['periodo_inicio'].iloc[0]) & 
                (employee_data_df['periodo_fim'] == save_data['periodo_fim'].iloc[0]))
        employee_data_df = employee_data_df[mask]
    
    updated_df = pd.concat([employee_data_df, save_data], ignore_index=True)
    save_employee_data(updated_df)
    st.success("Dados salvos com sucesso!")
    create_backup()

def render_summary(employee_data, df_ponto):
    """Renderiza o resumo mensal"""
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
            
            if st.button("Gerar Relatório Completo em PDF"):
                generate_pdf(employee_data, df_ponto, salary_data)
                
            if st.button("Salvar Dados do Cálculo"):
                save_data = df_ponto.copy()
                for key, value in employee_data.items():
                    save_data[key] = value
                save_data['horas_extras'] = horas_extras
                save_data['salario_liquido'] = salary_data['liquido']
                save_current_data(employee_data, save_data, load_employee_data())
                st.success("Dados do cálculo salvos com sucesso!")

def generate_pdf(employee_data, ponto_data, salary_data=None):
    """Gera PDF do relatório (implementação simplificada)"""
    st.warning("Funcionalidade de PDF simplificada para demonstração")
    st.info("Na implementação real, esta função geraria um PDF com todas as informações")
    st.json({
        "employee": employee_data,
        "ponto_data": ponto_data.to_dict(),
        "salary_data": salary_data
    })

def show_history(employee_data):
    """Mostra histórico do funcionário"""
    st.subheader("Histórico de Registros")
    employee_data_df = load_employee_data()
    
    if not employee_data_df.empty and 'matricula' in employee_data:
        history_df = employee_data_df[employee_data_df['matricula'] == employee_data['matricula']]
        
        if not history_df.empty:
            st.dataframe(
                history_df.sort_values('periodo_inicio', ascending=False).head(10),
                use_container_width=True,
                column_order=["periodo_inicio", "periodo_fim", "Horas", "Observações"]
            )
            
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

# --- Aplicação Principal ---
def main():
    try:
        load_css()
        render_header()
        employee_data_df = load_employee_data()
        employee_data = employee_info_form(employee_data_df)
        
        if employee_data:
            df_ponto = ponto_table(employee_data, employee_data_df)
            render_summary(employee_data, df_ponto)
            show_history(employee_data)
            
            if st.button("Salvar Registros de Ponto"):
                save_current_data(employee_data, df_ponto, employee_data_df)
            
            st.divider()
            st.text_input("Assinatura:", value=employee_data["nome"])
    except Exception as e:
        st.error(f"Ocorreu um erro: {str(e)}")

if __name__ == "__main__":
    main()
