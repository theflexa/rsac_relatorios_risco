#!/usr/bin/env python3
"""
Script para extrair dados de garantias e grupo econômico do PDF
- Se Pessoal Alcançado = 0: não faz nada
- Se Pessoal Alcançado ≥ 1: extrai dados da tabela de Garantia Pessoal
- Extrai dados do Grupo Econômico (Nome/Razão Social e CPF/CNPJ)
- Armazena dados estruturados para reutilização
- Isola e armazena todos os CPFs/CNPJs encontrados
- PREPARADO PARA MÚLTIPLAS GARANTIAS em diferentes cenários
"""

import pdfplumber
import re
import json
from datetime import datetime
import warnings
import sys
import os

# Redirecionar stderr para suprimir warnings
stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

# Suprimir warnings do pdfplumber
warnings.filterwarnings("ignore")

def validar_cpf_cnpj(cpf_cnpj):
    """Valida se o CPF/CNPJ tem formato válido"""
    if not cpf_cnpj:
        return False
    
    # Remover pontos, traços e barras
    limpo = re.sub(r'[^\d]', '', cpf_cnpj)
    
    # CPF: 11 dígitos, CNPJ: 14 dígitos
    if len(limpo) == 11 or len(limpo) == 14:
        return True
    
    return False

def extrair_numero_conta(texto_pagina):
    """Extrai o número da conta (C/C) do texto da página"""
    padrao_cc = r'C/C:\s*(\d+)'
    match = re.search(padrao_cc, texto_pagina)
    return match.group(1) if match else None


def extrair_associado_desde(texto_pagina):
    """Extrai a data do campo "Associado desde: dd/mm/aaaa" do texto da página"""
    try:
        padrao_associado = r'Associado\s*desde:\s*([0-3]?\d/[0-1]?\d/\d{4})'
        match = re.search(padrao_associado, texto_pagina, flags=re.IGNORECASE)
        return match.group(1) if match else None
    except Exception:
        return None


def extrair_garantias(pdf_path):
    """Extrai dados de garantias do PDF - PREPARADO PARA MÚLTIPLAS GARANTIAS"""
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_paginas = len(pdf.pages)
            
            # Lista para armazenar todos os CPFs/CNPJs encontrados
            cpfs_cnpjs_encontrados = []
            # Lista para armazenar todas as garantias pessoais encontradas
            todas_garantias_pessoais = []
            dados_garantias = None
            
            # Primeiro, procurar pelos dados básicos de garantias
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                
                # Procurar por dados de garantias
                padrao_real = r'Real Exigido\s*([\d,\.]+)%?\s*Real Alcançado\s*([\d,\.]+)%?'
                padrao_pessoal = r'Pessoal Exigido\s*(\d+)\s*Pessoal Alcançado\s*(\d+)'
                
                match_real = re.search(padrao_real, text)
                match_pessoal = re.search(padrao_pessoal, text)
                
                if match_real or match_pessoal:
                    dados_garantias = {
                        'real_exigido': match_real.group(1) if match_real else 'N/A',
                        'real_alcancado': match_real.group(2) if match_real else 'N/A',
                        'pessoal_exigido': match_pessoal.group(1) if match_pessoal else 'N/A',
                        'pessoal_alcancado': match_pessoal.group(2) if match_pessoal else 'N/A'
                    }
                    break
            
            # Agora procurar por garantias pessoais em TODAS as páginas
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                
                # Se encontrou dados de garantias e Pessoal Alcançado >= 1, procurar garantias pessoais
                if dados_garantias:
                    pessoal_alcancado = int(dados_garantias['pessoal_alcancado']) if dados_garantias['pessoal_alcancado'] != 'N/A' else 0
                    
                    if pessoal_alcancado >= 1:
                        # Extrair TODAS as tabelas de Garantia Pessoal da página
                        garantias_pagina = extrair_todas_garantias_pessoais(page, text, page_num)
                        todas_garantias_pessoais.extend(garantias_pagina)
                        
                        # Adicionar CPFs/CNPJs das garantias encontradas
                        for garantia in garantias_pagina:
                            if garantia['dados_estruturados']['cpf_cnpj']:
                                # Validar CPF/CNPJ antes de adicionar
                                if validar_cpf_cnpj(garantia['dados_estruturados']['cpf_cnpj']):
                                    cpfs_cnpjs_encontrados.append({
                                        'cpf_cnpj': garantia['dados_estruturados']['cpf_cnpj'],
                                        'nome': garantia['dados_estruturados']['nome'],
                                        'pagina': page_num,
                                        'tipo': 'garantia_pessoal',
                                        'indice_garantia': garantia['indice_garantia']
                                    })
                
                # Se não encontrou dados de garantias, procurar por CPFs/CNPJs gerais
                else:
                    cpfs_pagina = extrair_cpfs_cnpjs_pagina(text, page_num)
                    cpfs_cnpjs_encontrados.extend(cpfs_pagina)
            
            # Adicionar listas aos dados de garantias
            if dados_garantias:
                dados_garantias['cpfs_cnpjs_encontrados'] = cpfs_cnpjs_encontrados
                dados_garantias['todas_garantias_pessoais'] = todas_garantias_pessoais
                dados_garantias['total_garantias_encontradas'] = len(todas_garantias_pessoais)
                dados_garantias['total_cpfs_cnpjs_encontrados'] = len(cpfs_cnpjs_encontrados)
            
            # Extrair número da conta (C/C) da primeira página
            primeira_pagina = pdf.pages[0].extract_text()
            numero_conta = extrair_numero_conta(primeira_pagina)
            associado_desde = extrair_associado_desde(primeira_pagina)
            
            # Extrair dados do Grupo Econômico
            grupo_economico_dados = []
            grupo_economico_iniciado = False
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                
                # Verificar se encontrou o início do Grupo Econômico
                if 'Grupo Econômico' in text:
                    grupo_economico_iniciado = True
                
                # Se já iniciou o Grupo Econômico, processar a página
                if grupo_economico_iniciado:
                    # Processar página e verificar se deve parar
                    dados_pagina = extrair_dados_grupo_economico_pagina(text, page_num)
                    grupo_economico_dados.extend(dados_pagina)
                    
                    # Verificar se chegou ao fim da seção APÓS processar
                    if 'Anotação de Crédito' in text:
                        break
            
            # Extrair apenas os CPFs/CNPJs para uso posterior
            cpfs_avalistas = []
            if todas_garantias_pessoais:
                for garantia in todas_garantias_pessoais:
                    if 'dados_estruturados' in garantia:
                        cpf_cnpj = garantia['dados_estruturados'].get('cpf_cnpj')
                        if cpf_cnpj:
                            cpfs_avalistas.append(cpf_cnpj)
            
            cpfs_grupo_economico = []
            if grupo_economico_dados:
                for membro in grupo_economico_dados:
                    cpf_cnpj = membro.get('cpf_cnpj')
                    if cpf_cnpj:
                        cpfs_grupo_economico.append(cpf_cnpj)
            
            # Retornar dados encontrados
            if cpfs_cnpjs_encontrados or todas_garantias_pessoais or numero_conta or grupo_economico_dados:
                return {
                    'numero_conta': numero_conta,
                    'associado_desde': associado_desde,
                    'cpfs_cnpjs_encontrados': cpfs_cnpjs_encontrados,
                    'todas_garantias_pessoais': todas_garantias_pessoais,
                    'grupo_economico': grupo_economico_dados,
                    'dados_garantias': dados_garantias,
                    'cpfs_avalistas': cpfs_avalistas,
                    'cpfs_grupo_economico': cpfs_grupo_economico,
                    'resumo_extracao': {
                        'total_paginas_processadas': total_paginas,
                        'total_garantias_encontradas': len(todas_garantias_pessoais),
                        'total_cpfs_cnpjs_encontrados': len(cpfs_cnpjs_encontrados),
                        'total_grupo_economico_encontrados': len(grupo_economico_dados),
                        'pessoal_alcancado': dados_garantias['pessoal_alcancado'] if dados_garantias else 'N/A',
                        'numero_conta_encontrado': numero_conta is not None
                    }
                }
        
        return None
        
    except Exception as e:
        return None

def extrair_cpfs_cnpjs_pagina(text, page_num):
    """Extrai todos os CPFs/CNPJs de uma página"""
    cpfs_encontrados = []
    
    # Padrões para CPF e CNPJ
    padrao_cpf = r'(\d{3}\.\d{3}\.\d{3}-\d{2})'
    padrao_cnpj = r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})'
    
    # Procurar CPFs
    cpfs = re.findall(padrao_cpf, text)
    for cpf in cpfs:
        cpfs_encontrados.append({
            'cpf_cnpj': cpf,
            'nome': extrair_nome_proximo(text, cpf),
            'pagina': page_num,
            'tipo': 'cpf'
        })
    
    # Procurar CNPJs
    cnpjs = re.findall(padrao_cnpj, text)
    for cnpj in cnpjs:
        cpfs_encontrados.append({
            'cpf_cnpj': cnpj,
            'nome': extrair_nome_proximo(text, cnpj),
            'pagina': page_num,
            'tipo': 'cnpj'
        })
    
    return cpfs_encontrados

def extrair_nome_proximo(text, cpf_cnpj):
    """Tenta extrair o nome próximo ao CPF/CNPJ"""
    try:
        # Procurar por padrões comuns de nome próximo ao CPF/CNPJ
        linhas = text.split('\n')
        
        for idx_linha, linha in enumerate(linhas):
            if cpf_cnpj in linha:
                # Procurar por "Nome:" ou "Razão Social:" na mesma linha ou próxima
                if 'Nome:' in linha:
                    match = re.search(r'Nome:\s*(.+)', linha)
                    if match:
                        return match.group(1).strip()
                
                if 'Razão Social:' in linha:
                    match = re.search(r'Razão Social:\s*(.+)', linha)
                    if match:
                        return match.group(1).strip()
                
                # Se não encontrou na mesma linha, procurar na próxima
                if idx_linha + 1 < len(linhas):
                    prox_linha = linhas[idx_linha + 1]
                    if 'Nome:' in prox_linha:
                        match = re.search(r'Nome:\s*(.+)', prox_linha)
                        if match:
                            return match.group(1).strip()
                    
                    if 'Razão Social:' in prox_linha:
                        match = re.search(r'Razão Social:\s*(.+)', prox_linha)
                        if match:
                            return match.group(1).strip()
        
        return "Nome não encontrado"
        
    except:
        return "Nome não encontrado"

def extrair_tabela_garantia_pessoal(page, page_text):
    """Extrai dados da tabela de Garantia Pessoal"""
    try:
        # Verificar se há texto sobre "Garantia Pessoal" na página
        if 'Garantia Pessoal' not in page_text:
            return {'encontrada': False, 'dados': None, 'motivo': 'Texto "Garantia Pessoal" não encontrado'}
        
        # Extrair tabelas da página
        tables = page.extract_tables()
        
        for table_num, table in enumerate(tables):
            if table:
                # Converter tabela para texto para verificar conteúdo
                table_text = ''
                for row in table:
                    if row:
                        row_text = ' '.join([str(cell) if cell else '' for cell in row])
                        table_text += row_text + ' '
                
                # Procurar por tabela que contenha "Garantia Pessoal"
                if 'Garantia Pessoal' in table_text:
                    return {
                        'encontrada': True,
                        'dados': table,
                        'motivo': f'Tabela {table_num + 1} contém "Garantia Pessoal"'
                    }
        
        return {'encontrada': False, 'dados': None, 'motivo': 'Nenhuma tabela com dados de garantia pessoal encontrada'}
        
    except Exception as e:
        return {'encontrada': False, 'dados': None, 'motivo': f'Erro: {e}'}

def extrair_dados_estruturados(dados_tabela):
    """Extrai dados estruturados da tabela de garantia pessoal"""
    dados_estruturados = {
        'cpf_cnpj': None,
        'nome': None,
        'risco': None,
        'responsabilidade': None,
        'renda_fixa': None,
        'renda_variavel': None,
        'qtd_op_direta': None,
        'qtd_op_indireta': None,
        'valor_op_direta': None,
        'valor_op_indireta': None
    }
    
    if not dados_tabela or not dados_tabela['encontrada'] or not dados_tabela['dados']:
        return dados_estruturados
    
    tabela = dados_tabela['dados']
    
    for row in tabela:
        if not row:
            continue
            
        row_text = ' '.join([str(cell) if cell else '' for cell in row])
        
        # Extrair CPF/CNPJ e Nome
        if 'CPF/CNPJ:' in row_text:
            padrao_cpf = r'CPF/CNPJ:\s*([\d\.\-/]+)\s*Nome\s*/\s*Razão\s*Social:\s*(.+)'
            match = re.search(padrao_cpf, row_text)
            if match:
                dados_estruturados['cpf_cnpj'] = match.group(1).strip()
                dados_estruturados['nome'] = match.group(2).strip()
        
        # Extrair Risco e Responsabilidade
        if 'Risco:' in row_text:
            padrao_risco = r'Risco:\s*([^\s]+)\s*Responsabilidade:\s*(.+)'
            match = re.search(padrao_risco, row_text)
            if match:
                dados_estruturados['risco'] = match.group(1).strip()
                dados_estruturados['responsabilidade'] = match.group(2).strip()
        
        # Extrair Renda Fixa e Quantidades
        if 'Renda Fixa:' in row_text:
            padrao_renda_fixa = r'Renda Fixa:\s*([\d\.,]+)'
            match = re.search(padrao_renda_fixa, row_text)
            if match:
                dados_estruturados['renda_fixa'] = match.group(1).strip()
            
            padrao_qtd_direta = r'Qtd\. Op\. Direta:\s*(\d+)'
            match = re.search(padrao_qtd_direta, row_text)
            if match:
                dados_estruturados['qtd_op_direta'] = match.group(1).strip()
            
            padrao_qtd_indireta = r'Qtd\. Op\. Indireta:\s*(\d+)'
            match = re.search(padrao_qtd_indireta, row_text)
            if match:
                dados_estruturados['qtd_op_indireta'] = match.group(1).strip()
        
        # Extrair Renda Variável e Valores
        if 'Renda Variável:' in row_text:
            padrao_renda_variavel = r'Renda Variável:\s*([\d\.,]+)'
            match = re.search(padrao_renda_variavel, row_text)
            if match:
                dados_estruturados['renda_variavel'] = match.group(1).strip()
            
            padrao_valor_direta = r'Valor Op\. Direta:\s*([\d\.,]+)'
            match = re.search(padrao_valor_direta, row_text)
            if match:
                dados_estruturados['valor_op_direta'] = match.group(1).strip()
            
            padrao_valor_indireta = r'Valor Op\. Indireta:\s*([\d\.,]+)'
            match = re.search(padrao_valor_indireta, row_text)
            if match:
                dados_estruturados['valor_op_indireta'] = match.group(1).strip()
    
    return dados_estruturados

def extrair_todas_garantias_de_tabela(tabela, page_num, table_num):
    """Extrai TODAS as garantias pessoais de uma tabela - VERSÃO ROBUSTA"""
    garantias_encontradas = []
    
    if not tabela:
        return garantias_encontradas
    
    for row_num, row in enumerate(tabela):
        if not row:
            continue
            
        row_text = ' '.join([str(cell) if cell else '' for cell in row])
        
        # Procurar por CPF/CNPJ na linha
        if 'CPF/CNPJ:' in row_text:
            # Padrão mais flexível para capturar diferentes formatos
            padroes_cpf = [
                r'CPF/CNPJ:\s*([\d\.\-/]+)\s*Nome\s*/\s*Razão\s*Social:\s*(.+)',
                r'CPF/CNPJ:\s*([\d\.\-/]+)\s*Nome:\s*(.+)',
                r'CPF/CNPJ:\s*([\d\.\-/]+)\s*Razão\s*Social:\s*(.+)',
                r'CPF/CNPJ:\s*([\d\.\-/]+)\s*(.+)'
            ]
            
            cpf_cnpj = None
            nome = None
            
            for padrao in padroes_cpf:
                match = re.search(padrao, row_text)
                if match:
                    cpf_cnpj = match.group(1).strip()
                    nome = match.group(2).strip()
                    break
            
            if cpf_cnpj and nome:
                
                # Procurar dados desta garantia nas linhas seguintes
                dados_garantia = {
                    'cpf_cnpj': cpf_cnpj,
                    'nome': nome,
                    'risco': None,
                    'responsabilidade': None,
                    'renda_fixa': None,
                    'renda_variavel': None,
                    'qtd_op_direta': None,
                    'qtd_op_indireta': None,
                    'valor_op_direta': None,
                    'valor_op_indireta': None
                }
                
                # Procurar dados nas próximas linhas (até encontrar outro CPF ou fim da tabela)
                for i in range(row_num + 1, len(tabela)):
                    prox_row = tabela[i]
                    if not prox_row:
                        continue
                    
                    prox_row_text = ' '.join([str(cell) if cell else '' for cell in prox_row])
                    
                    # Se encontrar outro CPF, parar
                    if 'CPF/CNPJ:' in prox_row_text:
                        break
                    
                    # Extrair Risco e Responsabilidade
                    if 'Risco:' in prox_row_text and not dados_garantia['risco']:
                        padroes_risco = [
                            r'Risco:\s*([^\s]+)\s*Responsabilidade:\s*(.+)',
                            r'Risco:\s*([^\s]+)\s*Resp\.:\s*(.+)',
                            r'Risco:\s*([^\s]+)\s*(.+)'
                        ]
                        
                        for padrao in padroes_risco:
                            match = re.search(padrao, prox_row_text)
                            if match:
                                dados_garantia['risco'] = match.group(1).strip()
                                dados_garantia['responsabilidade'] = match.group(2).strip()
                                break
                    
                    # Extrair Renda Fixa e Quantidades
                    if 'Renda Fixa:' in prox_row_text and not dados_garantia['renda_fixa']:
                        padrao_renda_fixa = r'Renda Fixa:\s*([\d\.,]+)'
                        match = re.search(padrao_renda_fixa, prox_row_text)
                        if match:
                            dados_garantia['renda_fixa'] = match.group(1).strip()
                        
                        padrao_qtd_direta = r'Qtd\. Op\. Direta:\s*(\d+)'
                        match = re.search(padrao_qtd_direta, prox_row_text)
                        if match:
                            dados_garantia['qtd_op_direta'] = match.group(1).strip()
                        
                        padrao_qtd_indireta = r'Qtd\. Op\. Indireta:\s*(\d+)'
                        match = re.search(padrao_qtd_indireta, prox_row_text)
                        if match:
                            dados_garantia['qtd_op_indireta'] = match.group(1).strip()
                    
                    # Extrair Renda Variável e Valores
                    if 'Renda Variável:' in prox_row_text and not dados_garantia['renda_variavel']:
                        padrao_renda_variavel = r'Renda Variável:\s*([\d\.,]+)'
                        match = re.search(padrao_renda_variavel, prox_row_text)
                        if match:
                            dados_garantia['renda_variavel'] = match.group(1).strip()
                        
                        padrao_valor_direta = r'Valor Op\. Direta:\s*([\d\.,]+)'
                        match = re.search(padrao_valor_direta, prox_row_text)
                        if match:
                            dados_garantia['valor_op_direta'] = match.group(1).strip()
                        
                        padrao_valor_indireta = r'Valor Op\. Indireta:\s*([\d\.,]+)'
                        match = re.search(padrao_valor_indireta, prox_row_text)
                        if match:
                            dados_garantia['valor_op_indireta'] = match.group(1).strip()
                
                # Validar se a garantia tem dados mínimos antes de adicionar
                if dados_garantia['cpf_cnpj'] and dados_garantia['nome']:
                    garantias_encontradas.append({
                        'indice_garantia': len(garantias_encontradas) + 1,
                        'pagina': page_num,
                        'tabela_numero': table_num + 1,
                        'dados_tabela': tabela,
                        'dados_estruturados': dados_garantia,
                        'motivo': f'Tabela {table_num + 1} contém "Garantia Pessoal"',
                        'linha_inicio': row_num + 1
                    })
                else:
                    pass # Garantia ignorada - dados insuficientes
    
    return garantias_encontradas

def extrair_todas_garantias_pessoais(page, page_text, page_num):
    """Extrai TODAS as tabelas de Garantia Pessoal de uma página"""
    garantias_encontradas = []
    
    try:
        # Verificar se há texto sobre "Garantia Pessoal" na página
        if 'Garantia Pessoal' not in page_text:
            return []
        
        # Extrair tabelas da página
        tables = page.extract_tables()
        
        for table_num, table in enumerate(tables):
            if table:
                # Converter tabela para texto para verificar conteúdo
                table_text = ''
                for row in table:
                    if row:
                        row_text = ' '.join([str(cell) if cell else '' for cell in row])
                        table_text += row_text + ' '
                
                # Procurar por tabela que contenha "Garantia Pessoal"
                if 'Garantia Pessoal' in table_text:
                    # Extrair TODAS as garantias desta tabela
                    garantias_tabela = extrair_todas_garantias_de_tabela(table, page_num, table_num)
                    garantias_encontradas.extend(garantias_tabela)
        
        return garantias_encontradas
        
    except Exception as e:
        return []

def extrair_grupo_economico(pdf_path):
    """Extrai dados do Grupo Econômico do PDF"""
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            grupo_economico_dados = []
            
            # Procurar em todas as páginas
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                
                # Verificar se há seção "Grupo Econômico" na página
                if 'Grupo Econômico' in text:
                    # Extrair dados do grupo econômico desta página
                    dados_pagina = extrair_dados_grupo_economico_pagina(text, page_num)
                    grupo_economico_dados.extend(dados_pagina)
            
            return grupo_economico_dados
            
    except Exception as e:
        return []

def extrair_dados_grupo_economico_pagina(text, page_num):
    """Extrai dados do Grupo Econômico de uma página específica"""
    dados_encontrados = []
    
    try:
        print(f"\n=== PROCESSANDO PÁGINA {page_num} ===")
        print(f"Texto da página (primeiras 500 chars): {text[:500]}...")
        # Dividir o texto em linhas para análise sequencial
        linhas = text.split('\n')
        
        # Padrões flexíveis para identificar dados de pessoas
        padroes_pessoa = [
            r'Nome\s*/\s*Razão\s+Social:',
            r'Nome/Razão\s+Social:',
            r'Nome\s*:\s*',
            r'Razão\s+Social\s*:',
            r'CPF\s*/\s*CNPJ:',
            r'CPF/CNPJ:'
        ]
        
        # Verificar se há dados de pessoas na página
        tem_pessoas = False
        for linha in linhas:
            for padrao in padroes_pessoa:
                if re.search(padrao, linha, re.IGNORECASE):
                    tem_pessoas = True
                    break
            if tem_pessoas:
                break
        
        if not tem_pessoas:
            return dados_encontrados
        
        # Verificar se cliente não participa de grupo econômico
        if re.search(r'Cliente\s+não\s+participa\s+de\s+Grupo\s+Econômico', text, re.IGNORECASE):
            return []
        
        # Identificar pontos de parada flexíveis
        padroes_parada = [
            r'Anotação\s+de\s+Crédito',
            r'Análise\s+de\s+Crédito',
            r'Conclusão',
            r'Parecer',
            r'Observações',
            r'Garantias\s+Pessoais',
            r'Avalistas',
            r'Fiadores'
        ]
        
        # Encontrar limite de processamento
        linha_limite = len(linhas)
        for idx, linha_temp in enumerate(linhas):
            for padrao in padroes_parada:
                if re.search(padrao, linha_temp, re.IGNORECASE):
                    print(f"Encontrado ponto de parada '{padrao}' na linha {idx}: {linha_temp}")
                    linha_limite = idx
                    break
            if linha_limite < len(linhas):
                break
        
        # Sempre processar do início da página
        i = 0
        print(f"Processando linhas de {i} até {linha_limite-1}")
        
        while i < linha_limite:
            linha = linhas[i].strip()
            print(f"Processando linha {i}: '{linha}'")
            
            # Outros critérios de parada para segurança
            if any(keyword in linha for keyword in ['Análise de Crédito', 'Conclusão', 'Parecer']):
                break
            
            # Padrões flexíveis para extrair dados de pessoa
            padroes_extracao = [
                  # Padrão específico: Nome / Razão Social: NOME CPF / CNPJ: NUMERO
                  r'Nome\s*/\s*Razão\s+Social:\s*(.+?)\s+CPF\s*/\s*CNPJ:\s*([\d.-/]+(?:-\d+)?)',
                  # Padrão: Nome: NOME CPF: NUMERO
                  r'Nome\s*:\s*(.+?)\s+CPF\s*:\s*([\d.-]+(?:-\d+)?)',
                  # Padrão: Razão Social: NOME CNPJ: NUMERO
                  r'Razão\s+Social\s*:\s*(.+?)\s+CNPJ\s*:\s*([\d.-/]+(?:-\d+)?)',
                  # Padrão mais específico para o formato da súmula
                  r'Nome\s*/\s*Razão\s+Social:\s*([A-Z\s]+?)\s+CPF\s*/\s*CNPJ:\s*([\d.-/]+)\s+Risco:'
              ]
            
            pessoa_encontrada = False
            for padrao in padroes_extracao:
                match = re.search(padrao, linha, re.IGNORECASE)
                if match:
                    nome = match.group(1).strip()
                    cpf_cnpj = match.group(2).strip()
                    
                    # Limpar nome de caracteres indesejados
                    nome = re.sub(r'\s+', ' ', nome)  # Múltiplos espaços
                    nome = nome.strip()
                    
                    # Remover espaços do CPF/CNPJ
                    cpf_cnpj = re.sub(r'\s+', '', cpf_cnpj)
                    
                    # Remover texto extra após o CPF/CNPJ (como "Risco: R7")
                    cpf_cnpj = re.split(r'\s+[A-Za-z]', cpf_cnpj)[0]
                    
                    # Validar se o nome não está vazio e tem pelo menos 2 caracteres
                    if len(nome) >= 2 and validar_cpf_cnpj(cpf_cnpj):
                        print(f"✓ PESSOA ENCONTRADA (linha completa): Nome='{nome}', CPF/CNPJ='{cpf_cnpj}'")
                        dados_encontrados.append({
                            'nome_razao_social': nome,
                            'cpf_cnpj': cpf_cnpj,
                            'pagina': page_num,
                            'tipo': 'grupo_economico'
                        })
                        pessoa_encontrada = True
                        break
                    else:
                        print(f"✗ Dados inválidos: Nome='{nome}', CPF/CNPJ='{cpf_cnpj}'")
            
            # Comentário: Removida lógica de busca por CPF isolado para evitar duplicatas
            # A extração agora funciona apenas com dados completos na mesma linha
            
            i += 1
        
        print(f"=== PÁGINA {page_num} FINALIZADA: {len(dados_encontrados)} pessoas encontradas ===")
        return dados_encontrados
        
    except Exception as e:
        print(f"ERRO na página {page_num}: {e}")
        return dados_encontrados