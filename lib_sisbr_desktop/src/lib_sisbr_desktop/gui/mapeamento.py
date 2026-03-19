# --- COORDENADAS DOS RETÂNGULOS DAS LINHAS DA TABELA ---
RETANGULOS_CONTACORRENTE_RECT = [
    {'l':50, 't':253, 'r':271, 'b':268},
    {'l':50, 't':277, 'r':271, 'b':292},
    {'l':50, 't':301, 'r':271, 'b':316},
    {'l':50, 't':325, 'r':271, 'b':340},
    {'l':50, 't':349, 'r':271, 'b':364},
    {'l':50, 't':373, 'r':271, 'b':388},
    {'l':50, 't':397, 'r':271, 'b':412},
    {'l':50, 't':421, 'r':271, 'b':436},
    {'l':50, 't':445, 'r':271, 'b':460},
    {'l':50, 't':469, 'r':271, 'b':484},
    {'l':50, 't':493, 'r':271, 'b':508},
    {'l':50, 't':517, 'r':271, 'b':532},
    {'l':50, 't':541, 'r':271, 'b':556},
    {'l':50, 't':565, 'r':271, 'b':580},
    {'l':50, 't':589, 'r':271, 'b':604},
    {'l':50, 't':613, 'r':271, 'b':628},
    {'l':50, 't':637, 'r':271, 'b':652},
    {'l':50, 't':661, 'r':271, 'b':676},
    {'l':50, 't':685, 'r':271, 'b':700},
    {'l':50, 't':709, 'r':271, 'b':724},
    {'l':50, 't':733, 'r':271, 'b':748},
    {'l':50, 't':757, 'r':271, 'b':772},
    {'l':50, 't':781, 'r':271, 'b':796},
    {'l':50, 't':805, 'r':271, 'b':820},
    {'l':50, 't':829, 'r':271, 'b':844},
    {'l':50, 't':853, 'r':271, 'b':868},
    {'l':50, 't':877, 'r':271, 'b':892},
    {'l':50, 't':901, 'r':271, 'b':916},
    {'l':50, 't':925, 'r':271, 'b':940},
    {'l':50, 't':949, 'r':271, 'b':964},
    {'l':50, 't':973, 'r':271, 'b':988},
    {'l':50, 't':997, 'r':271, 'b':1012},
    {'l':50, 't':1021, 'r':271, 'b':1036},
]
#CONTA CORRENTE
RETANGULOS_DADOS = [
    {'l': 46, 't': 173, 'r': 185, 'b': 192},
    {'l': 427, 't': 350, 'r': 645, 'b': 389},
]

# --- REGIÃO DE INTERESSE PARA CAPTURA DE PRINT ---
REGIAO_PRINT = (40, 146, 823, 745)

# --- TELA DE LOGIN ---
CAMPOS_LOGIN_RECT = {
    "usuario": {
        "label": "USUÁRIO",
        "bounds": (916, 512, 1072, 529),
        "verificar": True
    },
    "senha": {
        "label": "SENHA",
        "bounds": (916, 5529, 1072, 518),
        "verificar": False  # campo não exibe texto
    }
}

# --- TELA PRINCIPAL ---
CAMPOS_ACESSO_MODULO_RECT = {

    "campo_busca_modulo": {"bounds": (28, 981, 258, 1003), "control_type": "Edit"},
    "nova_cooperativa_valor": {"title": "NOVA COOPERATIVA:", "name": "NOVA COOPERATIVA:", "control_type": "Edit"},
    "nova_cooperativa_confirmar": {"title": "CONFIRMAR:", "name": "CONFIRMAR:", "control_type": "Button"},
    "nova_cooperativa_sim": {"title": "SIM:", "name": "SIM:", "control_type": "Button"},
}

# --- PLATAFORMA DE ATENDIMENTO ---
PLATAFORMA_DE_ATENDIMENTO = {
    # geral
    "bureau_credit": {"bounds": (0, 23, 1921, 1018), "control_type": "Edit"},
    "edit_cpfcnpj": {"title": "PARCEIRO:", "name": "PARCEIRO:", "control_type": "Edit"},
    "edit_search_submodulo": {"bounds": (9, 583, 292, 602), "control_type": "Edit"},
    "btn_relatorio": {"bounds": (1777, 903, 1850, 967), "control_type": "Button"},
    "btn_imprimir": {"title": "IMPRIMIR", "control_type": "Button"},
    # consultas_externas
    "btn_serasa": {"bounds": (1727, 262, 1880, 310)},
    # serasa
    "btn_checkbox_score": {"bounds": (47, 240, 832, 262), "control_type": "Image"},
    "btn_consultar": {"bounds": (47, 268, 127, 290), "control_type": "Image"},
    "btn_nova_consulta": {"title": "NOVA CONSULTA", "control_type": "Button"},
    # bacen
    "edit_data_base": {"title": "Data-base:", "name": "Data-base:", "control_type": "Edit"},
}

# --- PLATAFORMA DE CRÉDITO ---
PLATAFORMA_DE_CREDITO = {
    # Campo de busca de submódulo
    "edit_search_submodulo": {"bounds": (65, 656, 312, 675), "control_type": "Edit"},
    
    # Campos de entrada de dados
    "campo_cpf_cnpj": {"bounds": (315, 253, 315, 253), "control_type": "Edit"},  # Coordenada central
    "campo_data_associado": {"bounds": (357, 318, 357, 318), "control_type": "Edit"},  # Coordenada central
    
    # Campos de consulta de carteira
    "campo_cpf_cnpj_carteira": {"bounds": (132, 236, 238, 253), "control_type": "Edit"},  # Centro do BoundingRectangle {l:102 t:206 r:208 b:223}
    "campo_data_inicio": {"bounds": (147, 346, 236, 363), "control_type": "Edit"},  # Centro do BoundingRectangle {l:117 t:316 r:206 b:333}
    "campo_data_fim": {"bounds": (285, 346, 374, 363), "control_type": "Edit"},  # Centro do BoundingRectangle {l:255 t:316 r:344 b:333}
    
    # Região para captura de print
    "regiao_print": {"bounds": (81, 143, 904, 797), "control_type": "Region"},
    
    # --- COORDENADAS PARA DOWNLOAD DE DOCUMENTOS (teste_slc.py) ---
    # Regiões de screenshot para busca de imagens
    "regiao_outros_documentacao": {"bounds": (269, 394, 771, 801), "control_type": "Region"},
    "regiao_ancora_tela_inteira": {"bounds": (239, 321, 1498, 849), "control_type": "Region"},
    "regiao_ancora_download": {"bounds": (239, 321, 1498, 849), "control_type": "Region"},
    "regiao_ancora_primeira_coluna": {"bounds": (249, 363, 400, 646), "control_type": "Region"},  # Região restrita à primeira coluna
    "regiao_exit_button": {"bounds": (1581, 240, 224, 957), "control_type": "Region"},
    "regiao_mudanca_cor_dinamica": {"bounds": (816, 416, 1291, 799), "control_type": "Region"},
    
    # Coordenadas dos itens de garantia para verificação de mudança de cor
    "coordenadas_garantias": [
        {"l": 524, "t": 531, "r": 767, "b": 547},  # Item 1
        {"l": 523, "t": 554, "r": 769, "b": 566},  # Item 2
        {"l": 523, "t": 575, "r": 769, "b": 587},  # Item 3
        {"l": 523, "t": 596, "r": 769, "b": 608},  # Item 4
        {"l": 523, "t": 617, "r": 769, "b": 629},  # Item 5
        {"l": 523, "t": 638, "r": 769, "b": 650},  # Item 6
        {"l": 523, "t": 659, "r": 769, "b": 671},  # Item 7
        {"l": 523, "t": 680, "r": 769, "b": 692},  # Item 8
        {"l": 523, "t": 701, "r": 769, "b": 713},  # Item 9
        {"l": 523, "t": 722, "r": 769, "b": 734},  # Item 10
        {"l": 523, "t": 743, "r": 769, "b": 755},  # Item 11
        {"l": 523, "t": 764, "r": 769, "b": 776}   # Item 12
     ],
     
     # Coordenadas para captura de screenshot de garantias
     "coordenadas_screenshot_garantias": {"bounds": (284, 249, 1284, 855), "control_type": "Region"},
}

# --- COBRANCA BANCÁRIA ---
COBRANCA_BANCARIA = {
    # Campos de data para inserção
    "campo_data_inicio": {"bounds": (161, 324, 161, 324), "control_type": "Edit"},  # Coordenada central
    "campo_data_fim": {"bounds": (299, 324, 299, 324), "control_type": "Edit"},  # Coordenada central
    
    # Região para verificar "finalizado"
    "regiao_finalizado": {"bounds": (216, 393, 1897, 435), "control_type": "Region"},
    
    # Coordenadas finais para clique
    "coordenadas_finais": {"bounds": (1800, 438, 1821, 459), "control_type": "Region"},
    
    # Região para captura de print (se necessário)
    "regiao_print": {"bounds": (81, 143, 904, 797), "control_type": "Region"},
}

# --- PLATAFORMA DE CREDENCIAMENTO ---
PLATAFORMA_DE_CREDENCIAMENTO = {
    # Campos usados no fluxo de Relatórios -> Liquidação SLC
    # BoundingRectangles conforme teste_slc.py
    "campo_cpf_cnpj": {"bounds": (862, 580, 1158, 597), "control_type": "Edit"},
    "campo_data_1": {"bounds": (862, 657, 951, 674), "control_type": "Edit"},
    "campo_data_2": {"bounds": (978, 657, 1067, 674), "control_type": "Edit"},
}


# --- REGIÃO DE INTERESSE PARA RELATÓRIOS (ROI) ---
ROI_RELATORIO = {'l': 525, 't': 287, 'w': 870, 'h': 496}

# --- POP-UPS E ALERTAS GERAIS ---
POPUPS_GERAIS = {
    "ok_button": {"title": "OK", "control_type": "Button"},
    "sim_button": {"title": "SIM", "control_type": "Button"},
    "fechar_button": {"title": "FECHAR", "control_type": "Button"},
    "nenhum_registro_encontrado": {"title": "Nenhum registro foi encontrado.", "control_type": "Text"},
    "acesso_restrito": {"title_re": "Você não tem acesso a esse cadastro.*", "control_type": "Text"},
}