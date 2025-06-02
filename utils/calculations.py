import locale
from datetime import datetime

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def calculate_worked_hours(ent1, sai1, ent2, sai2):
    """Calcula o total de horas trabalhadas no formato HH:MM"""
    times = [ent1, sai1, ent2, sai2]
    if any(not t or t == "--:--" for t in times):
        return "00:00"
    
    try:
        # Converter para minutos
        def to_minutes(time_str):
            h, m = map(int, time_str.split(':'))
            return h * 60 + m
        
        total_minutes = (to_minutes(sai1) - to_minutes(ent1)) + (to_minutes(sai2) - to_minutes(ent2))
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours:02d}:{minutes:02d}"
    except:
        return "00:00"

def calculate_daily_salary(salario_bruto, dias_base=22):
    """Calcula o valor do salário por dia"""
    return salario_bruto / dias_base

def calculate_hourly_salary(salario_bruto, horas_base=220):
    """Calcula o valor do salário por hora"""
    return salario_bruto / horas_base

def calculate_taxes(salario_bruto, dependentes=0):
    """Calcula INSS e IRRF conforme tabelas vigentes"""
    # Cálculo do INSS (2023)
    if salario_bruto <= 1320.00:
        inss = salario_bruto * 0.075
    elif 1320.01 <= salario_bruto <= 2571.29:
        inss = (salario_bruto - 1320.00) * 0.09 + 99.00
    elif 2571.30 <= salario_bruto <= 3856.94:
        inss = (salario_bruto - 2571.29) * 0.12 + 99.00 + 112.62
    elif 3856.95 <= salario_bruto <= 7507.49:
        inss = (salario_bruto - 3856.94) * 0.14 + 99.00 + 112.62 + 154.28
    else:
        inss = 7507.49 * 0.14
    
    # Cálculo do IRRF
    base_irrf = salario_bruto - inss - (dependentes * 189.59)
    
    if base_irrf <= 1903.98:
        irrf = 0
    elif 1903.99 <= base_irrf <= 2826.65:
        irrf = base_irrf * 0.075 - 142.80
    elif 2826.66 <= base_irrf <= 3751.05:
        irrf = base_irrf * 0.15 - 354.80
    elif 3751.06 <= base_irrf <= 4664.68:
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
    dependentes=0,
    dias_base=22,
    horas_base=220
):
    """Calcula o salário líquido com todos os benefícios e descontos"""
    # Cálculo de vencimentos
    valor_dia = salario_bruto / dias_base
    valor_hora = salario_bruto / horas_base
    
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
        'adicional_noturno': adicional_noturno,
        'horas_extras': valor_horas_extras,
        'outros_beneficios': outros_beneficios,
        'total_vencimentos': total_vencimentos,
        'inss': taxes['inss'],
        'irrf': taxes['irrf'],
        'outros_descontos': outros_descontos,
        'total_descontos': total_descontos,
        'liquido': max(0, liquido),  # Salário não pode ser negativo
        'worked_days': dias_trabalhados
    }
