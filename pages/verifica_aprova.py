import re
import pandas as pd
import unicodedata
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Verifica preenchimento - Cadastro - Legalização",
    page_icon="🔎",
    layout="wide"
)


# ============================================================
# MENU LATERAL
# ============================================================

st.sidebar.title("Aplicações")

st.sidebar.markdown(
    """
    - [App](https://pmiappnovo-copia.streamlit.app/)
    - [CV Zona](https://pmiappnovo-copia.streamlit.app/cv_zona)
    - [Documentação Complementar - ALF](https://pmiappnovo-copia.streamlit.app/documentacao-complementar-ALF)
    - [Estudo de Impacto de Vizinhança](https://pmiappnovo-copia.streamlit.app/estudo-de-impacto-de-vizinhanca)
    - [Links](https://pmiappnovo-copia.streamlit.app/links)
    - [Verifica Aprova](https://pmiappnovo-copia.streamlit.app/verifica-aprova)
    """
)


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================

def normalizar_texto(valor):

    if valor is None:
        return ""

    valor = str(valor)

    valor = unicodedata.normalize(
        "NFKC",
        valor
    )

    valor = re.sub(
        r"\s+",
        " ",
        valor
    )

    return valor.strip().upper()


def normalizar_sem_acentos(valor):

    valor = normalizar_texto(valor)

    valor = unicodedata.normalize(
        "NFD",
        valor
    )

    return "".join(
        c
        for c in valor
        if unicodedata.category(c) != "Mn"
    )


def normalizar_razao_social(valor):

    valor = normalizar_sem_acentos(valor)

    return re.sub(
        r"[^A-Z0-9]",
        "",
        valor
    )


def normalizar_natureza_juridica(valor):

    valor = normalizar_sem_acentos(valor)

    return re.sub(
        r"[^A-Z0-9]",
        "",
        valor
    )


def normalizar_logradouro(valor):

    valor = normalizar_sem_acentos(valor)

    valor = re.sub(
        r"\bN[º°]?\s*\d+\b",
        "",
        valor
    )

    valor = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        valor
    )

    valor = re.sub(
        r"\s+",
        " ",
        valor
    ).strip()

    valor = re.sub(
        r"^(R\.?|RUA|AVENIDA|AV\.?|ALAMEDA|AL\.?|TRAVESSA|TV\.?|RODOVIA|ROD\.?)\s+",
        "",
        valor
    )

    return valor


def normalizar_numero(valor):

    if not valor:
        return ""

    match = re.search(
        r"\d+",
        str(valor)
    )

    return (
        match.group(0)
        if match
        else ""
    )


def normalizar_cep(valor):

    if not valor:
        return ""

    return re.sub(
        r"\D",
        "",
        str(valor)
    )


def normalizar_complemento(valor):

    valor = normalizar_sem_acentos(
        valor
    )

    valor = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        valor
    )

    valor = re.sub(
        r"\s+",
        " ",
        valor
    )

    return valor.strip()


def normalizar_cnae(valor):

    if not valor:
        return ""

    return re.sub(
        r"\D",
        "",
        str(valor)
    )


def formatar_cnae(codigo):

    codigo = normalizar_cnae(
        codigo
    )

    if len(codigo) != 7:
        return codigo

    return (
        codigo[:2]
        + "."
        + codigo[2:4]
        + "-"
        + codigo[4]
        + "/"
        + codigo[5:]
    )


# ============================================================
# EXTRAÇÃO DE BLOCOS
# ============================================================

def extrair_bloco(
    texto,
    inicio,
    fim=None
):

    if not texto:
        return ""

    texto_lower = texto.lower()

    pos_inicio = texto_lower.find(
        inicio.lower()
    )

    if pos_inicio == -1:
        return ""

    pos_inicio += len(inicio)

    if fim:

        pos_fim = texto_lower.find(
            fim.lower(),
            pos_inicio
        )

        if pos_fim != -1:

            return texto[
                pos_inicio:pos_fim
            ]

    return texto[
        pos_inicio:
    ]


# ============================================================
# EXTRAÇÃO DO CNPJ
# ============================================================

def extrair_cnpj(texto):

    if not texto:
        return ""

    padroes = [

        r"CPF/CNPJ\s*:\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",

        r"CNPJ\s*:\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",

        r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b"
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE
        )

        if match:

            return re.sub(
                r"\D",
                "",
                match.group(1)
            )

    return ""


# ============================================================
# EXTRAÇÃO DOS CNAEs DO CADASTRO
# ============================================================

def extrair_cnaes_cadastro(texto):

    cnaes = []

    if not texto:
        return cnaes

    # --------------------------------------------------------
    # Isola somente a seção de CNAEs.
    # --------------------------------------------------------

    bloco = extrair_bloco(
        texto,
        "Atividade Econômica CNAE",
        "Atividade Econômica Atual"
    )

    if not bloco:

        bloco = extrair_bloco(
            texto,
            "Atividade Econômica CNAE"
        )

    if not bloco:
        return cnaes

    # --------------------------------------------------------
    # Formato tabular:
    #
    # 7112000 | SERVIÇOS DE ENGENHARIA
    #
    # Também aceita:
    #
    # | 7112000 | SERVIÇOS DE ENGENHARIA
    # --------------------------------------------------------

    padroes = [

        r"(?:^|\||\n)\s*(\d{7})\s*(?=\||\n|$)",

        r"^\s*(\d{7})\s+\S"
    ]

    for padrao in padroes:

        for match in re.finditer(
            padrao,
            bloco,
            flags=re.MULTILINE
        ):

            codigo = normalizar_cnae(
                match.group(1)
            )

            if (
                len(codigo) == 7
                and codigo not in cnaes
            ):

                cnaes.append(
                    codigo
                )

    return cnaes


# ============================================================
# EXTRAÇÃO DO ENDEREÇO DO CADASTRO
# ============================================================

def extrair_endereco_cadastro(
    texto
):

    dados = {
        "logradouro": "",
        "numero": "",
        "bairro": "",
        "complemento": "",
        "cep": ""
    }

    # --------------------------------------------------------
    # Localiza o primeiro "Endereço" depois da identificação.
    # --------------------------------------------------------

    pos_identificacao = texto.lower().find(
        "identificação do contribuinte"
    )

    if pos_identificacao >= 0:

        texto_endereco = texto[
            pos_identificacao:
        ]

    else:

        texto_endereco = texto

    bloco = extrair_bloco(
        texto_endereco,
        "Endereço",
        "Endereço Correspondência"
    )

    if not bloco:
        return dados

    # ========================================================
    # CASO 1 - DOCUMENTO COM RÓTULOS E VALORES NA MESMA LINHA
    # ========================================================

    match = re.search(
        r"Logradouro[ \t]*:[ \t]*(.*?)(?=[ \t]+(?:N[úu]mero|Complemento|Bairro|CEP)[ \t]*:|[\n\r|]|$)",
        bloco,
        flags=re.IGNORECASE
    )

    if match and match.group(1).strip():

        dados["logradouro"] = (
            match.group(1).strip()
        )

    # O valor do número pode estar na mesma linha de Complemento,
    # Bairro ou CEP. Interrompe a captura antes do próximo rótulo.
    match = re.search(
        r"N[úu]mero[ \t]*:[ \t]*(.*?)(?=[ \t]+(?:Complemento|Bairro|CEP|Logradouro)[ \t]*:|[\n\r|]|$)",
        bloco,
        flags=re.IGNORECASE
    )

    if match and match.group(1).strip():

        candidato = match.group(1).strip()

        if re.fullmatch(
            r"\d+",
            candidato
        ):

            dados["numero"] = candidato

    match = re.search(
        r"Bairro[ \t]*:[ \t]*(.*?)(?=[ \t]+(?:CEP|Logradouro|N[úu]mero|Complemento)[ \t]*:|[\n\r|]|$)",
        bloco,
        flags=re.IGNORECASE
    )

    if match and match.group(1).strip():

        dados["bairro"] = (
            match.group(1).strip()
        )

    match = re.search(
        r"Complemento[ \t]*:[ \t]*(.*?)(?=[ \t]+(?:Bairro|CEP|Logradouro|N[úu]mero)[ \t]*:|[\n\r|]|$)",
        bloco,
        flags=re.IGNORECASE
    )

    if match and match.group(1).strip():

        dados["complemento"] = (
            match.group(1).strip()
        )

    match = re.search(
        r"CEP\s*:\s*(\d{2}\.?\d{3}-?\d{3})",
        bloco,
        flags=re.IGNORECASE
    )

    if match:

        dados["cep"] = (
            match.group(1)
        )

    # ========================================================
    # CASO 2 - EXTRAÇÃO TABULAR DO PDF
    # ========================================================

    linhas = [
        linha.strip()
        for linha in bloco.splitlines()
        if linha.strip()
    ]

    # --------------------------------------------------------
    # CEP
    # --------------------------------------------------------

    ceps = re.findall(
        r"\b\d{5}-\d{3}\b",
        bloco
    )

    if ceps:

        dados["cep"] = ceps[-1]

    # --------------------------------------------------------
    # Procura especificamente a sequência dos rótulos:
    #
    # Logradouro:
    # Número:
    # Bairro:
    # Complemento:
    # CEP:
    #
    # e então analisa os valores que aparecem posteriormente.
    # --------------------------------------------------------

    indice_logradouro = None

    for i, linha in enumerate(linhas):

        if normalizar_texto(
            linha
        ) in (
            "LOGRADOURO:",
            "LOGRADOURO"
        ):

            indice_logradouro = i
            break

    if indice_logradouro is None:

        return dados

    # --------------------------------------------------------
    # Localiza os quatro rótulos seguintes.
    # --------------------------------------------------------

    indices_rotulos = {}

    for i in range(
        indice_logradouro,
        min(
            indice_logradouro + 10,
            len(linhas)
        )
    ):

        texto_linha = normalizar_texto(
            linhas[i]
        )

        if texto_linha in (
            "LOGRADOURO:",
            "LOGRADOURO"
        ):

            indices_rotulos[
                "logradouro"
            ] = i

        elif texto_linha in (
            "NÚMERO:",
            "NUMERO:",
            "NÚMERO",
            "NUMERO"
        ):

            indices_rotulos[
                "numero"
            ] = i

        elif texto_linha in (
            "BAIRRO:",
            "BAIRRO"
        ):

            indices_rotulos[
                "bairro"
            ] = i

        elif texto_linha in (
            "COMPLEMENTO:",
            "COMPLEMENTO"
        ):

            indices_rotulos[
                "complemento"
            ] = i

        elif texto_linha in (
            "CEP:",
            "CEP"
        ):

            indices_rotulos[
                "cep"
            ] = i

    if len(indices_rotulos) < 4:

        return dados

    # --------------------------------------------------------
    # Os valores podem aparecer depois de todos os rótulos.
    #
    # Exemplo real:
    #
    # Logradouro:
    # Número:
    # Bairro:
    # Complemento:
    # CEP:
    #
    # 88303-040
    # 2 ANDAR SALA 03 BOX 56
    # 657
    # CENTRO
    # ALMIRANTE BARROSO
    # --------------------------------------------------------

    indice_ultimo_rotulo = max(
        indices_rotulos.values()
    )

    valores = []

    for linha in linhas[
        indice_ultimo_rotulo + 1:
    ]:

        # Não avançar para outra seção.
        if normalizar_texto(
            linha
        ) in (
            "ENDEREÇO CORRESPONDÊNCIA",
            "INSCRIÇÃO MUNICIPAL",
            "CONTADOR",
            "NOME:",
            "IM:",
            "TELEFONE:",
            "CORREIO ELETRÔNICO:"
        ):

            break

        if linha.endswith(":"):
            continue

        valores.append(
            linha
        )

    # --------------------------------------------------------
    # Identifica CEP
    # --------------------------------------------------------

    valores_sem_cep = []

    for valor in valores:

        if re.fullmatch(
            r"\d{5}-\d{3}",
            valor
        ):

            dados["cep"] = valor

        else:

            valores_sem_cep.append(
                valor
            )

    valores = valores_sem_cep

    # --------------------------------------------------------
    # Identifica número ISOLADO.
    #
    # Isso é fundamental:
    #
    # 657              -> número
    #
    # 2 ANDAR SALA...  -> complemento
    #
    # Portanto não usamos simplesmente o primeiro número.
    # --------------------------------------------------------

    numero_encontrado = ""

    for valor in valores:

        if re.fullmatch(
            r"\d+",
            valor
        ):

            numero_encontrado = valor
            break

    if numero_encontrado:

        dados["numero"] = (
            numero_encontrado
        )

    # --------------------------------------------------------
    # Identifica complemento
    # --------------------------------------------------------

    complemento_encontrado = ""

    palavras_complemento = (
        "ANDAR",
        "SALA",
        "BOX",
        "GALPAO",
        "GALPÃO",
        "BLOCO",
        "APTO",
        "APT",
        "LOJA",
        "FUNDOS",
        "CONJUNTO",
        "CJ"
    )

    for valor in valores:

        if valor == numero_encontrado:
            continue

        normalizado = (
            normalizar_sem_acentos(
                valor
            )
        )

        if any(
            palavra in normalizado
            for palavra in palavras_complemento
        ):

            complemento_encontrado = valor

            # Remove somente o número inicial
            # quando ele faz parte do complemento.
            if (
                numero_encontrado
                and complemento_encontrado.startswith(
                    numero_encontrado + " "
                )
            ):

                complemento_encontrado = (
                    complemento_encontrado[
                        len(numero_encontrado):
                    ].strip()
                )

            break

    if complemento_encontrado:

        dados["complemento"] = (
            complemento_encontrado
        )

    # --------------------------------------------------------
    # Os valores restantes normalmente são:
    #
    # CENTRO
    # ALMIRANTE BARROSO
    #
    # Portanto:
    # penúltimo = bairro
    # último = logradouro
    # --------------------------------------------------------

    restantes = []

    for valor in valores:

        if valor == numero_encontrado:
            continue

        if valor == complemento_encontrado:
            continue

        restantes.append(
            valor
        )

    if len(restantes) >= 2:

        dados["bairro"] = (
            restantes[-2]
        )

        dados["logradouro"] = (
            restantes[-1]
        )

    elif len(restantes) == 1:

        if not dados["logradouro"]:

            dados["logradouro"] = (
                restantes[0]
            )

    # --------------------------------------------------------
    # Remove eventual "RUA" do início para comparação.
    # --------------------------------------------------------

    if dados["logradouro"]:

        dados["logradouro"] = re.sub(
            r"^(RUA|R\.|AVENIDA|AV\.|ALAMEDA|AL\.|TRAVESSA|TV\.)\s+",
            "",
            dados["logradouro"],
            flags=re.IGNORECASE
        ).strip()

    return dados



# ============================================================
# EXTRAÇÃO DOS SÓCIOS
# ============================================================

def extrair_socios_cadastro(texto):
    """Extrai os sócios da seção Sócios do Cadastro Municipal."""
    socios = []
    bloco = extrair_bloco(texto, "Sócios", "Responsáveis")
    if not bloco:
        return socios

    padrao = re.compile(
        r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\s+'
        r'(.+?)\s+(\d+(?:[.,]\d+)?)\s+'
        r'(Sócio(?:-administrador)?|Administrador|Titular|'
        r'Acionista|Representante legal)\b',
        flags=re.IGNORECASE
    )

    for match in padrao.finditer(bloco):
        cpf = re.sub(r"\D", "", match.group(1))
        nome = match.group(2).strip(" \t|-\n\r")
        qualificacao = match.group(4).strip()
        if nome and not any(s["cpf"] == cpf and s["nome"] == nome for s in socios):
            socios.append({
                "cpf": cpf,
                "nome": nome,
                "qualificacao": qualificacao
            })

    # Alternativa para documentos em que participação/qualificação
    # aparecem separados em linhas ou colunas.
    if not socios:
        for linha in bloco.splitlines():
            match = re.search(
                r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\s+(.+?)\s+'
                r'(Sócio(?:-administrador)?|Administrador|Titular|Acionista)\b',
                linha,
                flags=re.IGNORECASE
            )
            if match:
                socios.append({
                    "cpf": re.sub(r"\D", "", match.group(1)),
                    "nome": match.group(2).strip(" \t|-"),
                    "qualificacao": match.group(3).strip()
                })
    return socios


def extrair_socios_legalizacao(texto):
    """Extrai os sócios da seção Quadro Societário do Aprova Digital."""
    socios = []
    bloco = extrair_bloco(
        texto,
        "Quadro Societário",
        "Informações Complementares"
    )
    if not bloco:
        # O quadro pode ser a última seção do texto copiado.
        bloco = extrair_bloco(texto, "Quadro Societário")

    if not bloco:
        return socios

    qualificacoes = (
        r"S[ÓO]CIO(?:-ADMINISTRADOR)?|ADMINISTRADOR|TITULAR|"
        r"ACIONISTA|S[ÓO]CIO|REPRESENTANTE\s+LEGAL"
    )
    padrao = re.compile(
        r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\s+'
        r'(.+?)\s+(' + qualificacoes + r')\b',
        flags=re.IGNORECASE
    )

    for match in padrao.finditer(bloco):
        cpf = re.sub(r"\D", "", match.group(1))
        nome = match.group(2).strip(" \t|-\n\r")
        qualificacao = match.group(3).strip()
        if nome and not any(s["cpf"] == cpf and s["nome"] == nome for s in socios):
            socios.append({
                "cpf": cpf,
                "nome": nome,
                "qualificacao": qualificacao
            })
    return socios


def comparar_socios(socios_cadastro, socios_legalizacao):
    """Compara sócios por nome normalizado, usando CPF como apoio."""
    normalizados_cadastro = {
        normalizar_sem_acentos(s.get("nome", "")): s
        for s in socios_cadastro
    }
    normalizados_legalizacao = {
        normalizar_sem_acentos(s.get("nome", "")): s
        for s in socios_legalizacao
    }

    comuns = [
        nome for nome in normalizados_cadastro
        if nome in normalizados_legalizacao
    ]
    somente_cadastro = [
        s for s in socios_cadastro
        if normalizar_sem_acentos(s.get("nome", "")) not in normalizados_legalizacao
    ]
    somente_legalizacao = [
        s for s in socios_legalizacao
        if normalizar_sem_acentos(s.get("nome", "")) not in normalizados_cadastro
    ]
    return comuns, somente_cadastro, somente_legalizacao


def mostrar_socios(socios_cadastro, socios_legalizacao):
    st.markdown("## 👥 Comparação dos sócios")
    comuns, somente_cadastro, somente_legalizacao = comparar_socios(
        socios_cadastro, socios_legalizacao
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Sócios no Cadastro", len(socios_cadastro))
    col2.metric("Sócios na Legalização", len(socios_legalizacao))
    col3.metric("Nomes correspondentes", len(comuns))

    if not socios_cadastro and not socios_legalizacao:
        st.warning(
            "Não foi possível identificar sócios em nenhum dos documentos. "
            "Confira a extração antes de concluir que não há sócios."
        )
    else:
        linhas = []
        nomes_vistos = set()
        for socio in socios_cadastro:
            nome_norm = normalizar_sem_acentos(socio.get("nome", ""))
            correspondente = next(
                (s for s in socios_legalizacao
                 if normalizar_sem_acentos(s.get("nome", "")) == nome_norm),
                None
            )
            linhas.append({
                "Nome no Cadastro Municipal": socio.get("nome", ""),
                "Nome na Legalização": correspondente.get("nome", "") if correspondente else "—",
                "CPF no Cadastro": socio.get("cpf", ""),
                "CPF na Legalização": correspondente.get("cpf", "") if correspondente else "—",
                "Situação": "🟢 Nome correspondente" if correspondente else "🔴 Não encontrado na Legalização"
            })
            nomes_vistos.add(nome_norm)

        for socio in somente_legalizacao:
            linhas.append({
                "Nome no Cadastro Municipal": "—",
                "Nome na Legalização": socio.get("nome", ""),
                "CPF no Cadastro": "—",
                "CPF na Legalização": socio.get("cpf", ""),
                "Situação": "🔴 Somente na Legalização"
            })

        st.dataframe(linhas, use_container_width=True, hide_index=True)

    if socios_cadastro and socios_legalizacao and not somente_cadastro and not somente_legalizacao:
        st.success("🟢 Todos os nomes de sócios identificados correspondem nos dois documentos.")
    elif somente_cadastro or somente_legalizacao:
        st.error("🔴 Foram encontradas diferenças entre os quadros societários.")
    return not socios_cadastro or not socios_legalizacao or bool(somente_cadastro or somente_legalizacao)


# ============================================================
# EXTRAÇÃO COMPLETA DO CADASTRO
# ============================================================

def extrair_cadastro_municipal(
    texto
):

    dados = {
        "cnpj": "",
        "razao_social": "",
        "natureza_juridica": "",
        "logradouro": "",
        "numero": "",
        "bairro": "",
        "complemento": "",
        "cep": "",
        "cnaes": [],
        "socios": []
    }

    if not texto:
        return dados

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------

    dados["cnpj"] = (
        extrair_cnpj(texto)
    )

    # --------------------------------------------------------
    # RAZÃO SOCIAL
    # --------------------------------------------------------

    bloco_identificacao = extrair_bloco(
        texto,
        "Identificação do Contribuinte",
        "Endereço Correspondência"
    )

    if not bloco_identificacao:

        bloco_identificacao = extrair_bloco(
            texto,
            "Identificação do Contribuinte",
            "Endereço"
        )

    linhas = [
        linha.strip()
        for linha in bloco_identificacao.splitlines()
        if linha.strip()
    ]

    # --------------------------------------------------------
    # Procura o valor do Nome.
    # --------------------------------------------------------

    indice_nome = None

    for i, linha in enumerate(linhas):

        if normalizar_texto(
            linha
        ) in (
            "NOME:",
            "NOME"
        ):

            indice_nome = i
            break

    if indice_nome is not None:

        candidatos = []

        for linha in linhas[
            indice_nome + 1:
        ]:

            if normalizar_texto(
                linha
            ) in (
                "NOME FANTASIA:",
                "DESC. NATUREZA JURÍDICA:",
                "CORREIO ELETRÔNICO:"
            ):

                break

            if "@" in linha:
                continue

            if re.fullmatch(
                r"\d+",
                linha
            ):
                continue

            if linha:

                candidatos.append(
                    linha
                )

        if candidatos:

            dados["razao_social"] = (
                candidatos[0]
            )

    # --------------------------------------------------------
    # FALLBACK RAZÃO SOCIAL
    # --------------------------------------------------------

    if not dados["razao_social"]:

        match = re.search(
            r"\b([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ0-9&.\- ]{3,}\s+(?:LTDA|S\.?\s*A\.?|EIRELI|ME|EPP))\b",
            texto,
            flags=re.IGNORECASE
        )

        if match:

            dados["razao_social"] = (
                match.group(1).strip()
            )

    # --------------------------------------------------------
    # NATUREZA JURÍDICA
    # --------------------------------------------------------

    padroes_natureza = [

        r"\b(\d{3}-\d)\s+Sociedade\s+Anônima\s+Fechada\b",

        r"\b(\d{3}-\d)\s+Sociedade\s+Empresária\s+Limitada\b",

        r"\b(\d{3}-\d)\s+([A-Za-zÀ-ÿ][^\n\r]+)"
    ]

    for padrao in padroes_natureza:

        match = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE
        )

        if match:

            if len(
                match.groups()
            ) == 1:

                dados[
                    "natureza_juridica"
                ] = match.group(1)

            else:

                dados[
                    "natureza_juridica"
                ] = (
                    match.group(1)
                    + " "
                    + match.group(2).strip()
                )

            break

    if not dados["natureza_juridica"]:
        match = re.search(
            r"Desc\.?\s*Natureza\s+Jur[ií]dic[^\r\n]*?(?<!\d)(\d{3}-\d)\s+(Sociedade\s+Empres[aá]ria\s+Limitada)",
            texto,
            flags=re.IGNORECASE
        )
        if match:
            dados["natureza_juridica"] = match.group(1) + " " + match.group(2).strip()

    # --------------------------------------------------------
    # ENDEREÇO
    # --------------------------------------------------------

    endereco = (
        extrair_endereco_cadastro(
            texto
        )
    )

    dados.update(
        endereco
    )

    # --------------------------------------------------------
    # CNAEs
    # --------------------------------------------------------

    dados["cnaes"] = (
        extrair_cnaes_cadastro(
            texto
        )
    )

    # Quadro societário do Cadastro Municipal
    dados["socios"] = extrair_socios_cadastro(texto)

    return dados


# ============================================================
# EXTRAÇÃO DA LEGALIZAÇÃO
# ============================================================

def extrair_legalizacao(
    texto
):

    dados = {
        "cnpj": "",
        "razao_social": "",
        "natureza_juridica": "",
        "logradouro": "",
        "numero": "",
        "bairro": "",
        "complemento": "",
        "cep": "",
        "cnae_principal": "",
        "cnaes_secundarios": [],
        "cnaes": [],
        "socios": []
    }

    if not texto:
        return dados

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------

    dados["cnpj"] = (
        extrair_cnpj(texto)
    )

    # --------------------------------------------------------
    # RAZÃO SOCIAL
    # --------------------------------------------------------

    match = re.search(
        r"Nome Empresarial\s*:\s*(.+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["razao_social"] = (
            match.group(1).strip()
        )

    # --------------------------------------------------------
    # NATUREZA JURÍDICA
    # --------------------------------------------------------

    match = re.search(
        r"Natureza Jurídica\s*:\s*(.+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["natureza_juridica"] = (
            match.group(1).strip()
        )

    # --------------------------------------------------------
    # LOGRADOURO E NÚMERO
    # --------------------------------------------------------

    match = re.search(
        r"Logradouro\s*:\s*(.+)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        endereco = match.group(1).strip()

        numero_match = re.search(
            r"N[º°]\s*(\d+)",
            endereco,
            flags=re.IGNORECASE
        )

        if numero_match:

            dados["numero"] = (
                numero_match.group(1)
            )

            dados["logradouro"] = (
                endereco[
                    :numero_match.start()
                ].rstrip(" ,")
            )

        else:

            dados["logradouro"] = (
                endereco
            )

    # --------------------------------------------------------
    # COMPLEMENTO
    # --------------------------------------------------------

    match = re.search(
        r"(?im)^\\s*Complemento\\s*:\\s*(.*?)(?=\\s+(?:Referência|Bairro|Município|Estado|CEP)\\s*:|[\\r\\n]|$)",
        texto
    )

    if match and match.group(1).strip() not in ("", "—", "-"):
        dados["complemento"] = match.group(1).strip()

    # --------------------------------------------------------
    # BAIRRO
    # --------------------------------------------------------

    match = re.search(
        r"Bairro\s*:\s*(.*)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["bairro"] = (
            match.group(1).strip()
        )

    # --------------------------------------------------------
    # CEP
    # --------------------------------------------------------

    match = re.search(
        r"CEP\s*:\s*(\d{2}\.?\d{3}-?\d{3})",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["cep"] = (
            match.group(1)
        )

    # ========================================================
    # CNAEs
    # ========================================================

    padrao_cnae = re.compile(
        r"^\s*(\d{2}\.\d{2}-\d/\d{2})\s*-\s*(.+)$"
    )

    # --------------------------------------------------------
    # CNAE PRINCIPAL
    # --------------------------------------------------------

    secao_principal = extrair_bloco(
        texto,
        "Atividade Econômica Principal",
        "Atividades Econômicas Secundárias"
    )

    for linha in secao_principal.splitlines():

        linha = linha.strip()

        match = padrao_cnae.match(
            linha
        )

        if match:

            dados[
                "cnae_principal"
            ] = normalizar_cnae(
                match.group(1)
            )

            break

    # --------------------------------------------------------
    # CNAEs SECUNDÁRIOS
    # --------------------------------------------------------

    secao_secundaria = extrair_bloco(
        texto,
        "Atividades Econômicas Secundárias",
        "Objeto Social"
    )

    for linha in secao_secundaria.splitlines():

        linha = linha.strip()

        match = padrao_cnae.match(
            linha
        )

        if match:

            codigo = normalizar_cnae(
                match.group(1)
            )

            if codigo not in (
                dados[
                    "cnaes_secundarios"
                ]
            ):

                dados[
                    "cnaes_secundarios"
                ].append(
                    codigo
                )

    # --------------------------------------------------------
    # LISTA COMPLETA
    # --------------------------------------------------------

    if dados["cnae_principal"]:

        dados["cnaes"].append(
            dados["cnae_principal"]
        )

    for cnae in (
        dados["cnaes_secundarios"]
    ):

        if cnae not in dados["cnaes"]:

            dados["cnaes"].append(
                cnae
            )

    # Quadro societário do Aprova Digital
    dados["socios"] = extrair_socios_legalizacao(texto)

    return dados


# ============================================================
# COMPARAÇÃO DE CAMPOS
# ============================================================

def comparar_campo(
    valor_cadastro,
    valor_legalizacao,
    normalizador
):

    cadastro = normalizador(
        valor_cadastro
    )

    legalizacao = normalizador(
        valor_legalizacao
    )

    if not cadastro and not legalizacao:

        return "ambos_nao_informados"

    if not cadastro:

        return "ausente_cadastro"

    if not legalizacao:

        return "ausente_legalizacao"

    if cadastro == legalizacao:

        return "igual"

    return "diferente"


# ============================================================
# EXIBIÇÃO DA COMPARAÇÃO
# ============================================================

def mostrar_comparacao(
    titulo,
    cadastro,
    legalizacao,
    normalizador
):

    status = comparar_campo(
        cadastro,
        legalizacao,
        normalizador
    )

    st.markdown(
        f"### {titulo}"
    )

    col1, col2, col3 = st.columns(
        [2, 2, 1]
    )

    with col1:

        st.caption(
            "Cadastro Municipal"
        )

        st.write(
            cadastro
            if cadastro
            else "— Não informado —"
        )

    with col2:

        st.caption(
            "Legalização"
        )

        st.write(
            legalizacao
            if legalizacao
            else "— Não informado —"
        )

    with col3:

        if status == "igual":

            st.success(
                "🟢 IGUAL"
            )

        elif status == "diferente":

            st.error(
                "🔴 DIVERGENTE"
            )

        elif status == "ausente_cadastro":

            st.warning(
                "🟠 AUSENTE NO CADASTRO"
            )

        elif status == "ausente_legalizacao":

            st.warning(
                "🟠 AUSENTE NA LEGALIZAÇÃO"
            )

        else:

            st.info(
                "⚪ NÃO INFORMADO"
            )

    return status


# ============================================================
# COMPARAÇÃO DOS CNAEs
# ============================================================

def comparar_cnaes(
    cadastro,
    legalizacao
):

    cadastro_set = set(
        cadastro
    )

    legalizacao_set = set(
        legalizacao
    )

    somente_cadastro = [
        cnae
        for cnae in cadastro
        if cnae not in legalizacao_set
    ]

    somente_legalizacao = [
        cnae
        for cnae in legalizacao
        if cnae not in cadastro_set
    ]

    comuns = [
        cnae
        for cnae in cadastro
        if cnae in legalizacao_set
    ]

    return (
        comuns,
        somente_cadastro,
        somente_legalizacao
    )


# ============================================================
# EXIBIÇÃO DOS CNAEs
# ============================================================

def mostrar_cnaes(
    cadastro,
    legalizacao
):

    st.markdown(
        "## 🏭 Comparação dos CNAEs"
    )

    (
        comuns,
        somente_cadastro,
        somente_legalizacao
    ) = comparar_cnaes(
        cadastro,
        legalizacao
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "CNAEs no Cadastro",
            len(cadastro)
        )

    with col2:

        st.metric(
            "CNAEs na Legalização",
            len(legalizacao)
        )

    with col3:

        st.metric(
            "CNAEs em comum",
            len(comuns)
        )

    # --------------------------------------------------------
    # CNAE PRINCIPAL
    # --------------------------------------------------------

    if legalizacao:

        principal = legalizacao[0]

        st.markdown(
            "### CNAE principal da Legalização"
        )

        if principal in set(cadastro):

            st.success(
                f"🟢 {formatar_cnae(principal)} "
                "— presente no Cadastro Municipal."
            )

        else:

            st.error(
                f"🔴 {formatar_cnae(principal)} "
                "— NÃO encontrado no Cadastro Municipal."
            )

    # --------------------------------------------------------
    # CNAEs somente no Cadastro
    # --------------------------------------------------------

    if somente_cadastro:

        st.error(
            "🔴 CNAE(s) existente(s) no Cadastro "
            "Municipal e ausente(s) na Legalização:"
        )

        for cnae in somente_cadastro:

            st.write(
                f"- **{formatar_cnae(cnae)}**"
            )

    # --------------------------------------------------------
    # CNAEs somente na Legalização
    # --------------------------------------------------------

    if somente_legalizacao:

        st.error(
            "🔴 CNAE(s) existente(s) na Legalização "
            "e ausente(s) no Cadastro Municipal:"
        )

        for cnae in somente_legalizacao:

            st.write(
                f"- **{formatar_cnae(cnae)}**"
            )

    # --------------------------------------------------------
    # TODOS IGUAIS
    # --------------------------------------------------------

    if (
        not somente_cadastro
        and not somente_legalizacao
    ):

        st.success(
            f"🟢 Todos os {len(cadastro)} CNAEs "
            "do Cadastro Municipal estão presentes "
            "na Legalização e vice-versa."
        )

    # --------------------------------------------------------
    # TABELA COMPLETA
    # --------------------------------------------------------

    with st.expander(
        "📋 Ver comparação completa dos CNAEs"
    ):

        cadastro_set = set(
            cadastro
        )

        legalizacao_set = set(
            legalizacao
        )

        todos = []

        for cnae in cadastro:

            if cnae not in todos:

                todos.append(cnae)

        for cnae in legalizacao:

            if cnae not in todos:

                todos.append(cnae)

        tabela = []

        for cnae in todos:

            no_cadastro = (
                cnae in cadastro_set
            )

            na_legalizacao = (
                cnae in legalizacao_set
            )

            if (
                no_cadastro
                and na_legalizacao
            ):

                situacao = (
                    "🟢 Presente nos dois"
                )

            elif no_cadastro:

                situacao = (
                    "🔴 Somente no Cadastro"
                )

            else:

                situacao = (
                    "🔴 Somente na Legalização"
                )

            tabela.append(
                {
                    "CNAE": formatar_cnae(
                        cnae
                    ),
                    "Cadastro": (
                        "✅"
                        if no_cadastro
                        else "❌"
                    ),
                    "Legalização": (
                        "✅"
                        if na_legalizacao
                        else "❌"
                    ),
                    "Situação": situacao
                }
            )

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# LIMPAR CAMPOS
# ============================================================

def limpar_campos():

    st.session_state[
        "texto_cadastro"
    ] = ""

    st.session_state[
        "texto_legalizacao"
    ] = ""



# ============================================================
# EXTRAÇÃO DOS DOCUMENTOS 1 E 2
# ============================================================

def primeiro_match(padroes, texto, flags=re.IGNORECASE | re.MULTILINE):
    if not texto:
        return ""
    for padrao in padroes:
        m = re.search(padrao, texto, flags)
        if m:
            return m.group(1).strip(" \t\r\n:;|")
    return ""


def extrair_cnaes_generico(texto):
    """Extrai CNAEs em formatos comuns de documentos cadastrais."""
    if not texto:
        return []

    encontrados = []
    # Formatos usuais: 00.00-0/00, 00.00-0-00 ou 0000000.
    for m in re.finditer(r'(?<!\d)(\d{2})[.]?(\d{2})[-.]?(\d)[/-]?(\d{2})(?!\d)', texto):
        codigo = "".join(m.groups())
        if codigo not in encontrados:
            encontrados.append(codigo)
    for linha in texto.splitlines():
        m = re.match(r'\s*(\d{7})\s*(?:\||\s+-\s+|\s{2,})', linha)
        if m and m.group(1) not in encontrados:
            encontrados.append(m.group(1))
    return encontrados


def extrair_cnaes_aprova(texto):
    """Extrai CNAEs do Documento 1 somente dentro do trecho definido do Aprova Digital."""
    if not texto:
        return []

    # O trecho começa na pergunta sobre a solicitação e termina no status REGIN.
    marcador_inicio = (
        r"Qual\s+[ée]\s+sua\s+solicita[cç][aã]o\?"
        r"\s*\(\s*Para\s+altera[cç][aã]o\s+de\s+[ÁA]rea\s+Ocupada"
        r"\s+ou\s+Endere[cç]o,?\s*deve\s+ser\s+preenchido"
        r"\s+todos\s+os\s+CNAES\s+existentes\s+que\s+ir[aã]o\s+permanecer\s*\)"
    )
    inicio = re.search(marcador_inicio, texto, flags=re.IGNORECASE | re.DOTALL)
    fim = re.search(r"REGIN\s*\(\s*Deferido\s*\)", texto, flags=re.IGNORECASE)

    # Não procurar em outras partes do documento se qualquer marcador estiver ausente.
    if not inicio or not fim or fim.start() < inicio.start():
        return []

    trecho = texto[inicio.start():fim.end()]
    encontrados = []
    for m in re.finditer(r'(?<!\d)(\d{2})[.]?(\d{2})[-.]?(\d)[/-]?(\d{2})(?!\d)', trecho):
        codigo = "".join(m.groups())
        if codigo not in encontrados:
            encontrados.append(codigo)
    for linha in trecho.splitlines():
        m = re.match(r'\s*(\d{7})\s*(?:\||\s+-\s+|\s{2,})', linha)
        if m and m.group(1) not in encontrados:
            encontrados.append(m.group(1))
    return encontrados


def extrair_aprova_completo(texto):
    """Extrai os campos relevantes do texto copiado do Aprova Digital."""
    texto = texto or ""
    dados = {
        "cnpj": extrair_cnpj(texto),
        "razao_social": "",
        "natureza_juridica": "",
        "logradouro": "",
        "numero": "",
        "bairro": "",
        "complemento": "",
        "cep": "",
        "cnaes": extrair_cnaes_aprova(texto),
        "socios": [],
    }

    # Evita capturar a palavra "ou" da pergunta "Alterar Razão Social ou Nome Fantasia".
    dados["razao_social"] = primeiro_match([
        r"(?im)^\s*Raz[aã]o\s+Social\s*:\s*([^\r\n|]+)\s*$",
        r"(?im)^\s*Raz[aã]o\s+Social\s*$\s*^\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ0-9&.,'’()\- ]{4,})\s*$",
        r"(?im)^\s*Nome\s+Empresarial\s*:\s*([^\r\n|]+)\s*$",
    ], texto)

    # No formulário, o código de natureza jurídica pode vir numa linha com
    # texto auxiliar. Captura o código oficial 206-2 quando presente.
    bloco_natureza = primeiro_match([
        r"(?im)^\s*Natureza\s+jur[ií]dica\s*$\s*^\s*([^\r\n]+)\s*$",
        r"(?im)^\s*Natureza\s+Jur[ií]dica\s*:\s*([^\r\n|]+)\s*$",
    ], texto)
    m_natureza = re.search(
        r"\b(206[-.]?2)\s*[- ]*\s*(Sociedade\s+Empresária\s+Limitada)\b",
        bloco_natureza,
        flags=re.IGNORECASE
    )
    if m_natureza:
        dados["natureza_juridica"] = f"{m_natureza.group(1).replace('.', '-')} - {m_natureza.group(2)}"
    else:
        dados["natureza_juridica"] = bloco_natureza.strip()

    dados["logradouro"] = primeiro_match([
        r"Logradouro\s*:\s*([^\r\n|]+)",
        r"Logradouro\s+(.+?)\s+(?:N[úu]mero|N[º°]|Predial)\b",
    ], texto)
    dados["numero"] = primeiro_match([
        r"N[úu]mero\s*:\s*(\d+[A-Za-z]?)",
        r"N[úu]mero\s+Predial\s*[: ]*\s*(\d+[A-Za-z]?)",
        r"Predial\s+(\d+[A-Za-z]?)",
    ], texto)
    dados["bairro"] = primeiro_match([
        r"Bairro\s*:\s*([^\r\n|]+)",
        r"\bBairro\s+(.+?)\s+Logradouro\b",
    ], texto)
    dados["complemento"] = primeiro_match([
        r"Complemento\s*:\s*([^\r\n|]+)",
    ], texto)
    dados["cep"] = primeiro_match([
        r"\bCEP\s*:\s*(\d{2}\.?\d{3}-?\d{3})",
        r"\bCEP\s+(\d{2}\.?\d{3}-?\d{3})",
    ], texto)
    dados["cep"] = re.sub(r"(\d{5})(\d{3})", r"\1-\2", re.sub(r"\D", "", dados["cep"])) if dados["cep"] else ""

    # Para comparar o endereço do estabelecimento, priorizar os campos do
    # bloco REGIN (Deferido), e não os dados auxiliares da inscrição imobiliária.
    regin_match = re.search(
        r"REGIN\s*\(\s*Deferido\s*\)(.*?)(?=^\s*Raz[aã]o\s+Social\s*$)",
        texto,
        flags=re.IGNORECASE | re.DOTALL | re.MULTILINE
    )
    if regin_match:
        bloco_regin = regin_match.group(1)
        valor = primeiro_match([
            r"(?im)^\s*Logradouro\s*$\s*^\s*([^\r\n]+)",
            r"(?im)^\s*Logradouro\s*:\s*([^\r\n]+)",
        ], bloco_regin)
        if valor:
            dados["logradouro"] = valor.strip()

        valor = primeiro_match([
            r"(?im)^\s*N[uú]mero\s+Predial\s*$\s*^\s*(\d+[A-Za-z]?)",
            r"(?im)^\s*N[uú]mero\s+Predial\s*:?\s*(\d+[A-Za-z]?)",
        ], bloco_regin)
        if valor:
            dados["numero"] = valor.strip()

        valor = primeiro_match([
            r"(?im)^\s*Bairro\s*$\s*^\s*([^\r\n]+)",
            r"(?im)^\s*Bairro\s*:\s*([^\r\n]+)",
        ], bloco_regin)
        if valor:
            dados["bairro"] = valor.strip()

        valor = primeiro_match([
            r"(?im)^\s*CEP\s*$\s*^\s*(\d{8}|\d{5}-\d{3})",
            r"(?im)^\s*CEP\s*:\s*(\d{8}|\d{5}-\d{3})",
        ], bloco_regin)
        if valor:
            cep_digitos = re.sub(r"\D", "", valor)
            if len(cep_digitos) == 8:
                dados["cep"] = cep_digitos[:5] + "-" + cep_digitos[5:]

        complementos_regin = []
        for rotulo in ("Complemento 1", "Complemento 2", "Complemento 3"):
            valor = primeiro_match([
                rf"(?im)^\s*{re.escape(rotulo)}[^\r\n]*\s*$\s*^\s*([^\r\n]+)",
            ], bloco_regin)
            if valor and normalizar_sem_acentos(valor) not in ("NAO ESPECIFICADO", "NÃO ESPECIFICADO", "-", "—"):
                complementos_regin.append(valor.strip())
        if complementos_regin:
            dados["complemento"] = " / ".join(complementos_regin)
        else:
            dados["complemento"] = ""

    # Sócios no Aprova: seção de inclusão/atualização, diferente do quadro
    # societário da tela de Legalização.
    bloco_socio = extrair_bloco(
        texto,
        "Sócio/Responsável a ser INCLUÍDO/ATUALIZADO",
        "Sócio/Responsável a ser REMOVIDO"
    )
    if bloco_socio:
        nome = primeiro_match([
            r"(?im)^\s*Nome/Razão\s+Social\s*$\s*^\s*([^\r\n]+)",
            r"(?im)^\s*Nome/Razão\s+Social\s*:?\s*([^\r\n]+)",
        ], bloco_socio).strip(" ,;")
        cpf_match = re.search(
            r"(?<!\d)(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})(?!\d)",
            bloco_socio
        )
        qualificacao = primeiro_match([
            r"(?im)^\s*Qualificação\s*$\s*^\s*(?:\d+\s+)?([^\r\n]+)",
            r"(?im)^\s*Qualificação\s*:?\s*(?:\d+\s+)?([^\r\n]+)",
        ], bloco_socio)
        if nome and cpf_match:
            dados["socios"] = [{
                "cpf": re.sub(r"\D", "", cpf_match.group(1)),
                "nome": nome,
                "qualificacao": qualificacao.strip()
            }]

    if not dados["socios"]:
        dados["socios"] = extrair_socios_legalizacao(texto)
    if not dados["socios"]:
        dados["socios"] = extrair_socios_cadastro(texto)
    return dados

def extrair_cnpj_documento(texto):
    """Extrai campos do comprovante CNPJ, incluindo rótulos em linhas separadas."""
    texto = texto or ""
    dados = {
        "cnpj": extrair_cnpj(texto),
        "razao_social": "",
        "natureza_juridica": "",
        "logradouro": "",
        "numero": "",
        "bairro": "",
        "complemento": "",
        "cep": "",
        "cnaes": extrair_cnaes_generico(texto),
        "cnae_principal": "",
        "socios": [],
    }
    bloco_principal = extrair_bloco(
        texto,
        "CÓDIGO E DESCRIÇÃO DA ATIVIDADE ECONÔMICA PRINCIPAL",
        "CÓDIGO E DESCRIÇÃO DAS ATIVIDADES ECONÔMICAS SECUNDÁRIAS"
    )
    principal_match = re.search(
        r"(?<!\d)(\d{2})\.(\d{2})[-.]?(\d)[/-]?(\d{2})(?!\d)",
        bloco_principal
    )
    if principal_match:
        dados["cnae_principal"] = "".join(principal_match.groups())
    else:
        principal_match = re.search(r"(?<!\d)(\d{7})(?!\d)", bloco_principal)
        if principal_match:
            dados["cnae_principal"] = principal_match.group(1)

    dados["razao_social"] = primeiro_match([
        r"(?im)^\s*NOME\s+EMPRESARIAL\s*$\s*^\s*([^\r\n]+)\s*$",
        r"(?im)^\s*NOME\s+EMPRESARIAL\s*:\s*([^\r\n]+)",
    ], texto)
    dados["natureza_juridica"] = primeiro_match([
        r"(?im)^\s*CÓDIGO\s+E\s+DESCRIÇÃO\s+DA\s+NATUREZA\s+JURÍDICA\s*$\s*^\s*([^\r\n]+)\s*$",
        r"(?im)^\s*CÓDIGO\s+E\s+DESCRIÇÃO\s+DA\s+NATUREZA\s+JURÍDICA\s*:\s*([^\r\n]+)",
        r"(?im)^\s*NATUREZA\s+JURÍDICA\s*$\s*^\s*([^\r\n]+)\s*$",
    ], texto)
    dados["logradouro"] = primeiro_match([
        r"(?im)^\s*LOGRADOURO\s*$\s*^\s*([^\r\n]+)\s*$",
        r"(?im)^\s*LOGRADOURO\s*:\s*([^\r\n]+)",
    ], texto)
    dados["numero"] = primeiro_match([
        # Exige o rótulo isolado para não capturar "NÚMERO DE INSCRIÇÃO".
        r"(?im)^\s*N[ÚU]MERO\s*$\s*^\s*(\d+[A-Za-z]?)\s*$",
        r"(?im)^\s*N[ÚU]MERO\s*:\s*(\d+[A-Za-z]?)\s*$",
    ], texto)
    dados["complemento"] = primeiro_match([
        r"(?im)^\s*COMPLEMENTO\s*$\s*^\s*([^\r\n]*)\s*$",
        r"(?im)^\s*COMPLEMENTO\s*:\s*([^\r\n]*)",
    ], texto)
    dados["bairro"] = primeiro_match([
        r"(?im)^\s*BAIRRO/DISTRITO\s*$\s*^\s*([^\r\n]+)\s*$",
        r"(?im)^\s*BAIRRO\s*$\s*^\s*([^\r\n]+)\s*$",
        r"(?im)^\s*BAIRRO/DISTRITO\s*:\s*([^\r\n]+)",
        r"(?im)^\s*BAIRRO\s*:\s*([^\r\n]+)",
    ], texto)
    dados["cep"] = primeiro_match([
        r"(?im)^\s*CEP\s*$\s*^\s*(\d{2}\.?\d{3}-?\d{3})\s*$",
        r"(?im)^\s*CEP\s*:\s*(\d{2}\.?\d{3}-?\d{3})",
    ], texto)
    dados["numero"] = "" if normalizar_texto(dados["numero"]) in ("S/N", "SN", "NÃO INFORMADO") else dados["numero"]
    if dados["complemento"].strip() and set(dados["complemento"].strip()) == {"*"}:
        dados["complemento"] = ""
    dados["cep"] = re.sub(r"(\d{5})(\d{3})", r"\1-\2", re.sub(r"\D", "", dados["cep"])) if dados["cep"] else ""
    return dados

def formatar_lista(valores):
    return ", ".join(formatar_cnae(x) for x in valores) if valores else ""


def status_campo(valores, normalizador):
    presentes = [(nome, normalizador(valor)) for nome, valor in valores.items() if valor and normalizador(valor)]
    if not presentes:
        return "⚪ Não informado"
    unicos = {v for _, v in presentes}
    if len(unicos) == 1 and len(presentes) == len(valores):
        return "🟢 Coincide em todos"
    if len(unicos) == 1:
        return "🟠 Coincide nos informados; há campo ausente"
    return "🔴 Divergência"


def normalizar_simples(valor):
    return normalizar_sem_acentos(valor or "").strip()


def mostrar_comparacao_quatro_documentos(dados_docs):
    campos = [
        ("CNPJ", "cnpj", normalizar_cnpj_local),
        ("Razão social", "razao_social", normalizar_razao_social),
        ("Natureza jurídica", "natureza_juridica", normalizar_natureza_juridica),
        ("Logradouro", "logradouro", normalizar_logradouro),
        ("Número", "numero", normalizar_numero),
        ("Bairro", "bairro", normalizar_simples),
        ("Complemento", "complemento", normalizar_complemento),
        ("CEP", "cep", normalizar_cep),
    ]
    linhas = []
    for titulo, chave, norm in campos:
        valores = {nome: d.get(chave, "") for nome, d in dados_docs.items()}
        preenchidos = [(nome, norm(v)) for nome, v in valores.items() if v and norm(v)]
        diferentes = len({v for _, v in preenchidos}) > 1
        ausentes = len(preenchidos) < len(valores)
        if not preenchidos:
            status = "⚪ Não informado"
        elif diferentes:
            status = "🔴 Divergência"
        elif ausentes:
            status = "🟠 Parcial / campo ausente"
        else:
            status = f"🟢 Coincide nos {len(dados_docs)} documentos informados"
        linha = {"Campo": titulo}
        linha.update({nome: (valores[nome] or "— Não informado —") for nome in dados_docs})
        linha["Resultado"] = status
        linhas.append(linha)
    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)


def normalizar_cnpj_local(valor):
    return re.sub(r"\D", "", str(valor or ""))


def mostrar_cnaes_quatro(dados_docs):
    st.subheader("Comparação dos CNAEs")
    todos = sorted(set(c for d in dados_docs.values() for c in d.get("cnaes", [])))
    if not todos:
        st.warning("Nenhum CNAE foi identificado nos textos. Confira a extração antes de concluir que não existem atividades.")
        return
    linhas = []
    for cnae in todos:
        linha = {"CNAE": formatar_cnae(cnae)}
        for nome, dados in dados_docs.items():
            linha[nome] = "✅" if cnae in dados.get("cnaes", []) else "—"
        presentes = sum(cnae in d.get("cnaes", []) for d in dados_docs.values())
        linha["Resultado"] = f"🟢 Em todos os {len(dados_docs)} informados" if presentes == len(dados_docs) else f"🟠 Em {presentes}/{len(dados_docs)} documento(s)"
        linhas.append(linha)
    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)
    conjuntos = {nome: set(d.get("cnaes", [])) for nome, d in dados_docs.items()}
    base = next(iter(conjuntos.values()))
    iguais = all(s == base for s in conjuntos.values())
    if iguais:
        st.success(f"Os CNAEs extraídos coincidem entre os {len(dados_docs)} documentos informados.")
    else:
        st.warning("Há diferenças nas listas de CNAEs. Verifique a tabela acima; a extração automática depende do formato do texto copiado.")

    # Se o CNAE principal está identificado no comprovante CNPJ, mas não aparece
    # no intervalo deliberadamente delimitado do Aprova, destacar essa pendência.
    if "Aprova Digital" in dados_docs:
        principal = (
            dados_docs.get("CNPJ", {}).get("cnae_principal", "")
            or dados_docs.get("Legalização", {}).get("cnae_principal", "")
        )
        cnaes_aprova = set(dados_docs["Aprova Digital"].get("cnaes", []))
        if principal and principal not in cnaes_aprova:
            st.warning(
                f"O CNAE principal {formatar_cnae(principal)} foi identificado em outro documento, "
                "mas não aparece no trecho delimitado da solicitação do Aprova Digital. "
                "Confira se a atividade principal deveria constar no formulário, especialmente "
                "quando a solicitação envolve alteração de endereço."
            )

    # Não acrescenta códigos de fora do intervalo do Aprova. Apenas alerta
    # quando os demais documentos apontam atividades que não aparecem nele.
    if "Aprova Digital" in dados_docs and len(dados_docs) >= 2:
        cnaes_aprova = set(dados_docs["Aprova Digital"].get("cnaes", []))
        listas_outros = [
            set(dados.get("cnaes", []))
            for nome, dados in dados_docs.items()
            if nome != "Aprova Digital"
        ]
        comuns_outros = set.intersection(*listas_outros) if listas_outros else set()
        ausentes_aprova = sorted(comuns_outros - cnaes_aprova)
        if ausentes_aprova:
            st.info(
                "Conferência do Aprova Digital: estes CNAEs aparecem nos demais documentos, "
                "mas não foram encontrados no trecho delimitado da solicitação: "
                + ", ".join(formatar_cnae(c) for c in ausentes_aprova)
                + ". Não foram adicionados automaticamente, pois a extração respeita o intervalo definido. "
                "Confirme se o CNAE principal deve constar na solicitação."
            )


def mostrar_socios_quatro(dados_docs):
    st.subheader("Comparação dos sócios")

    # O comprovante padrão de CNPJ não contém quadro societário.
    # Portanto, ele não deve contar como "sócio ausente".
    docs_societarios = {
        nome: dados
        for nome, dados in dados_docs.items()
        if nome in ("Aprova Digital", "Cadastro Municipal", "Legalização")
    }

    if len(docs_societarios) < 2:
        st.info(
            "A consulta padrão do CNPJ não apresenta quadro societário. "
            "Para comparar sócios, informe pelo menos dois destes documentos: "
            "Aprova Digital, Cadastro Municipal e Legalização."
        )
        return

    todos = []
    for nome_doc, dados in docs_societarios.items():
        for socio in dados.get("socios", []):
            nome = socio.get("nome", "").strip()
            if nome:
                chave = normalizar_sem_acentos(nome)
                if not any(x["chave"] == chave and x["documento"] == nome_doc for x in todos):
                    todos.append({
                        "chave": chave,
                        "nome": nome,
                        "documento": nome_doc,
                        "cpf": socio.get("cpf", ""),
                        "qualificacao": socio.get("qualificacao", "")
                    })

    if not todos:
        st.warning(
            "Não foi possível identificar sócios nos documentos que contêm quadro societário. "
            "Confira a extração; ausência de identificação não significa ausência de sócios."
        )
        return

    nomes = sorted(set(x["chave"] for x in todos))
    linhas = []
    for chave in nomes:
        linha = {"Sócio": next(x["nome"] for x in todos if x["chave"] == chave)}
        docs_presentes = []
        for nome_doc, dados in docs_societarios.items():
            socio = next(
                (s for s in dados.get("socios", [])
                 if normalizar_sem_acentos(s.get("nome", "")) == chave),
                None
            )
            linha[nome_doc] = socio.get("nome", "—") if socio else "—"
            if socio:
                docs_presentes.append(nome_doc)
        linha["Resultado"] = (
            f"🟢 Presente nos {len(docs_societarios)} documentos com quadro societário"
            if len(docs_presentes) == len(docs_societarios)
            else f"🟠 Presente em {len(docs_presentes)}/{len(docs_societarios)} documentos com quadro societário"
        )
        linhas.append(linha)

    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)
    if all(
        all(
            any(normalizar_sem_acentos(s.get("nome", "")) == chave for s in dados.get("socios", []))
            for dados in docs_societarios.values()
        )
        for chave in nomes
    ):
        st.success("Os sócios identificados coincidem entre os documentos que apresentam quadro societário.")
    else:
        st.warning(
            "Há sócios identificados em apenas parte dos documentos com quadro societário. "
            "Verifique os dados e as seções extraídas."
        )

# INTERFACE UNIFICADA — QUATRO DOCUMENTOS
# ============================================================

st.title("🔎 Verifica preenchimento — comparação de documentos")
st.write("Cole os documentos que deseja comparar. É possível analisar a partir de dois documentos; os campos vazios serão ignorados.")

if "texto_aprova" not in st.session_state:
    st.session_state["texto_aprova"] = ""
if "texto_cnpj" not in st.session_state:
    st.session_state["texto_cnpj"] = ""
if "texto_cadastro" not in st.session_state:
    st.session_state["texto_cadastro"] = ""
if "texto_legalizacao" not in st.session_state:
    st.session_state["texto_legalizacao"] = ""

col1, col2 = st.columns(2)
with col1:
    st.subheader("📄 Documento 1 — Aprova Digital")
    st.text_area("Texto do Aprova Digital", height=300, key="texto_aprova", placeholder="Cole aqui o texto completo do Aprova Digital...")
with col2:
    st.subheader("📄 Documento 2 — CNPJ")
    st.text_area("Texto do CNPJ", height=300, key="texto_cnpj", placeholder="Cole aqui o texto completo da consulta do CNPJ...")

col3, col4 = st.columns(2)
with col3:
    st.subheader("📄 Documento 3 — Cadastro Municipal")
    st.text_area("Texto do Cadastro Municipal", height=300, key="texto_cadastro", placeholder="Cole aqui o texto completo do Cadastro Municipal...")
with col4:
    st.subheader("📄 Documento 4 — Legalização")
    st.text_area("Texto da Legalização", height=300, key="texto_legalizacao", placeholder="Cole aqui o texto completo da Legalização...")

def limpar_todos_campos():
    for chave in ("texto_aprova", "texto_cnpj", "texto_cadastro", "texto_legalizacao"):
        st.session_state[chave] = ""

b1, b2, _ = st.columns([1, 1, 4])
with b1:
    analisar = st.button("🔎 Comparar documentos preenchidos", type="primary", use_container_width=True)
with b2:
    st.button("🧹 Limpar", on_click=limpar_todos_campos, use_container_width=True)

if analisar:
    textos = {
        "Aprova Digital": st.session_state["texto_aprova"],
        "CNPJ": st.session_state["texto_cnpj"],
        "Cadastro Municipal": st.session_state["texto_cadastro"],
        "Legalização": st.session_state["texto_legalizacao"],
    }
    textos_preenchidos = {nome: texto for nome, texto in textos.items() if texto.strip()}
    if len(textos_preenchidos) < 2:
        st.warning("Informe pelo menos dois documentos para realizar a comparação.")
    else:
        extratores = {
            "Aprova Digital": extrair_aprova_completo,
            "CNPJ": extrair_cnpj_documento,
            "Cadastro Municipal": extrair_cadastro_municipal,
            "Legalização": extrair_legalizacao,
        }
        dados_docs = {
            nome: extratores[nome](texto)
            for nome, texto in textos_preenchidos.items()
        }
        st.info(f"Análise realizada com {len(dados_docs)} documentos: " + ", ".join(dados_docs.keys()) + ".")
        st.divider()
        st.header("📋 Resumo dos dados identificados")
        cols = st.columns(len(dados_docs))
        for col, (nome, dados) in zip(cols, dados_docs.items()):
            with col:
                st.markdown(f"**{nome}**")
                st.write("CNPJ:", dados.get("cnpj") or "Não identificado")
                st.write("Razão social:", dados.get("razao_social") or "Não identificada")
                st.write("CNAEs identificados:", len(dados.get("cnaes", [])))
                if nome == "CNPJ":
                    st.write("Quadro societário: não consta no comprovante padrão")
                else:
                    st.write("Sócios identificados:", len(dados.get("socios", [])))
        st.divider()
        st.header("🔍 Comparação geral dos campos")
        mostrar_comparacao_quatro_documentos(dados_docs)
        st.divider()
        mostrar_cnaes_quatro(dados_docs)
        st.divider()
        mostrar_socios_quatro(dados_docs)
        st.divider()
        st.header("📊 Resultado geral")
        # Contagem baseada nos valores extraídos, sem declarar conformidade quando nada foi extraído.
        campos_chave = ("cnpj", "razao_social", "logradouro", "numero", "bairro", "cep")
        divergencias = []
        pendencias = []
        normalizadores_campos = {
            "cnpj": normalizar_cnpj_local,
            "razao_social": normalizar_razao_social,
            "logradouro": normalizar_logradouro,
            "numero": normalizar_numero,
            "bairro": normalizar_simples,
            "cep": normalizar_cep,
        }
        for campo in campos_chave:
            normalizador = normalizadores_campos.get(campo, normalizar_simples)
            valores = [normalizador(d.get(campo, "")) for d in dados_docs.values()]
            preenchidos = [v for v in valores if v]
            if len(set(preenchidos)) > 1:
                divergencias.append(campo.replace("_", " ").title())
            if len(preenchidos) < len(valores):
                pendencias.append(campo.replace("_", " ").title())
        if divergencias:
            st.error("Foram encontradas divergências nos campos: " + ", ".join(divergencias) + ".")
        elif pendencias:
            st.warning("Não foram detectadas divergências entre os valores extraídos, mas há campos não identificados em alguma fonte: " + ", ".join(pendencias) + ".")
        else:
            st.success(f"Os campos principais extraídos coincidem entre os {len(dados_docs)} documentos informados. Confira também CNAEs, sócios e a tabela completa.")
        with st.expander("🛠️ Conferência técnica da extração"):
            for nome, dados in dados_docs.items():
                st.markdown(f"**{nome}**")
                st.json(dados)
