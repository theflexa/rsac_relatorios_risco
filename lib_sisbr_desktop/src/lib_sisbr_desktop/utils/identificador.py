import re

def tipo_documento(cpf_cnpj: str) -> str:
    """
    Retorna 'CPF' se o valor for um CPF, 'CNPJ' se for um CNPJ, ou 'DESCONHECIDO' caso contrário.
    """
    numeros = re.sub(r'\D', '', cpf_cnpj)
    if len(numeros) == 11:
        return 'CPF'
    elif len(numeros) == 14:
        return 'CNPJ'
    else:
        return 'DESCONHECIDO' 