import re
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
        r"^(RUA|R\.|AVENIDA|AV\.|ALAMEDA|AL\.|TRAVESSA|TV\.|RODOVIA|ROD\.)\s+",
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
        r"Logradouro\s*:\s*([^\n\r|]+)",
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
        r"N[úu]mero\s*:\s*(.*?)(?=\s+(?:Complemento|Bairro|CEP|Logradouro)\s*:|[\n\r|]|$)",
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
        r"Bairro\s*:\s*([^\n\r|]+)",
        bloco,
        flags=re.IGNORECASE
    )

    if match and match.group(1).strip():

        dados["bairro"] = (
            match.group(1).strip()
        )

    match = re.search(
        r"Complemento\s*:\s*([^\n\r|]+)",
        bloco,
        flags=re.IGNORECASE
    )

    if match and match.group(1).strip():

        dados["complemento"] = (
            match.group(1).strip()
        )

    match = re.search(
        r"CEP\s*:\s*(\d{5}-\d{3})",
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
        r"Complemento\s*:\s*(.*)",
        texto,
        flags=re.IGNORECASE
    )

    if match:

        dados["complemento"] = (
            match.group(1).strip()
        )

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
        r"CEP\s*:\s*(\d{5}-\d{3})",
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
# INTERFACE
# ============================================================

st.title(
    "🔎 Verifica preenchimento - Cadastro - Legalização"
)

st.write(
    "Compare os dados do Cadastro Municipal "
    "com os dados da Legalização."
)


# ============================================================
# INPUTS
# ============================================================

col1, col2 = st.columns(2)


with col1:

    st.subheader(
        "📄 Arquivo 1 — Cadastro Municipal"
    )

    st.text_area(
        "Cole aqui o conteúdo completo do Cadastro Municipal",
        height=400,
        key="texto_cadastro"
    )


with col2:

    st.subheader(
        "📄 Arquivo 2 — Legalização"
    )

    st.text_area(
        "Cole aqui o conteúdo completo da Legalização",
        height=400,
        key="texto_legalizacao"
    )


# ============================================================
# BOTÕES
# ============================================================

col1, col2 = st.columns(2)


with col1:

    analisar = st.button(
        "🔎 Analisar documentos",
        type="primary",
        use_container_width=True
    )


with col2:

    st.button(
        "🧹 Limpar",
        on_click=limpar_campos,
        use_container_width=True
    )


# ============================================================
# PROCESSAMENTO
# ============================================================

if analisar:

    texto_cadastro = st.session_state[
        "texto_cadastro"
    ]

    texto_legalizacao = st.session_state[
        "texto_legalizacao"
    ]

    if (
        not texto_cadastro
        or not texto_legalizacao
    ):

        st.warning(
            "⚠️ Informe os dois documentos "
            "antes de realizar a análise."
        )

    else:

        cadastro = (
            extrair_cadastro_municipal(
                texto_cadastro
            )
        )

        legalizacao = (
            extrair_legalizacao(
                texto_legalizacao
            )
        )

        # ====================================================
        # DADOS IDENTIFICADOS
        # ====================================================

        st.divider()

        st.header(
            "📋 Dados identificados"
        )

        col1, col2 = st.columns(2)

        # ----------------------------------------------------
        # CADASTRO
        # ----------------------------------------------------

        with col1:

            st.subheader(
                "Cadastro Municipal"
            )

            st.write(
                f"**CNPJ:** "
                f"{cadastro['cnpj'] or 'Não informado'}"
            )

            st.write(
                f"**Razão Social:** "
                f"{cadastro['razao_social'] or 'Não informado'}"
            )

            st.write(
                f"**Natureza Jurídica:** "
                f"{cadastro['natureza_juridica'] or 'Não informado'}"
            )

            st.write(
                f"**Logradouro:** "
                f"{cadastro['logradouro'] or 'Não informado'}"
            )

            st.write(
                f"**Número:** "
                f"{cadastro['numero'] or 'Não informado'}"
            )

            st.write(
                f"**Bairro:** "
                f"{cadastro['bairro'] or 'Não informado'}"
            )

            st.write(
                f"**Complemento:** "
                f"{cadastro['complemento'] or 'Não informado'}"
            )

            st.write(
                f"**CEP:** "
                f"{cadastro['cep'] or 'Não informado'}"
            )

        # ----------------------------------------------------
        # LEGALIZAÇÃO
        # ----------------------------------------------------

        with col2:

            st.subheader(
                "Legalização"
            )

            st.write(
                f"**CNPJ:** "
                f"{legalizacao['cnpj'] or 'Não informado'}"
            )

            st.write(
                f"**Razão Social:** "
                f"{legalizacao['razao_social'] or 'Não informado'}"
            )

            st.write(
                f"**Natureza Jurídica:** "
                f"{legalizacao['natureza_juridica'] or 'Não informado'}"
            )

            st.write(
                f"**Logradouro:** "
                f"{legalizacao['logradouro'] or 'Não informado'}"
            )

            st.write(
                f"**Número:** "
                f"{legalizacao['numero'] or 'Não informado'}"
            )

            st.write(
                f"**Bairro:** "
                f"{legalizacao['bairro'] or 'Não informado'}"
            )

            st.write(
                f"**Complemento:** "
                f"{legalizacao['complemento'] or 'Não informado'}"
            )

            st.write(
                f"**CEP:** "
                f"{legalizacao['cep'] or 'Não informado'}"
            )

        # ====================================================
        # COMPARAÇÃO DOS DADOS
        # ====================================================

        st.divider()

        st.header(
            "🔍 Comparação dos dados"
        )

        resultados = {}

        resultados["CNPJ"] = (
            mostrar_comparacao(
                "CNPJ",
                cadastro["cnpj"],
                legalizacao["cnpj"],
                normalizar_cep
            )
        )

        resultados["Razão Social"] = (
            mostrar_comparacao(
                "Razão Social",
                cadastro["razao_social"],
                legalizacao["razao_social"],
                normalizar_razao_social
            )
        )

        resultados["Natureza Jurídica"] = (
            mostrar_comparacao(
                "Natureza Jurídica",
                cadastro["natureza_juridica"],
                legalizacao["natureza_juridica"],
                normalizar_natureza_juridica
            )
        )

        resultados["Logradouro"] = (
            mostrar_comparacao(
                "Logradouro",
                cadastro["logradouro"],
                legalizacao["logradouro"],
                normalizar_logradouro
            )
        )

        resultados["Número"] = (
            mostrar_comparacao(
                "Número",
                cadastro["numero"],
                legalizacao["numero"],
                normalizar_numero
            )
        )

        resultados["Bairro"] = (
            mostrar_comparacao(
                "Bairro",
                cadastro["bairro"],
                legalizacao["bairro"],
                normalizar_sem_acentos
            )
        )

        resultados["Complemento"] = (
            mostrar_comparacao(
                "Complemento",
                cadastro["complemento"],
                legalizacao["complemento"],
                normalizar_complemento
            )
        )

        resultados["CEP"] = (
            mostrar_comparacao(
                "CEP",
                cadastro["cep"],
                legalizacao["cep"],
                normalizar_cep
            )
        )

        # ====================================================
        # CNAEs
        # ====================================================

        st.divider()

        mostrar_cnaes(
            cadastro["cnaes"],
            legalizacao["cnaes"]
        )

        # ====================================================
        # COMPARAÇÃO DOS SÓCIOS
        # ====================================================

        st.divider()
        divergencia_socios = mostrar_socios(
            cadastro["socios"],
            legalizacao["socios"]
        )

        # ====================================================
        # RESULTADO FINAL
        # ====================================================

        st.divider()

        st.header(
            "📊 Resultado da análise"
        )

        divergencias = []
        pendencias = []

        for campo, status in (
            resultados.items()
        ):

            if status in (
                "diferente",
                "ausente_cadastro",
                "ausente_legalizacao"
            ):

                divergencias.append(
                    campo
                )

            elif status == (
                "ambos_nao_informados"
            ):

                pendencias.append(
                    campo
                )

        (
            _,
            somente_cadastro,
            somente_legalizacao
        ) = comparar_cnaes(
            cadastro["cnaes"],
            legalizacao["cnaes"]
        )

        if (
            somente_cadastro
            or somente_legalizacao
        ):

            divergencias.append(
                "CNAEs"
            )

        socios_comuns, socios_somente_cadastro, socios_somente_legalizacao = comparar_socios(
            cadastro["socios"], legalizacao["socios"]
        )
        if socios_somente_cadastro or socios_somente_legalizacao:
            divergencias.append("Sócios")
        elif not cadastro["socios"] or not legalizacao["socios"]:
            pendencias.append("Sócios (extração não confirmada)")

        if divergencias:

            st.error(
                "🔴 Foram encontradas divergências."
            )

            st.write(
                "**Campos com divergência:** "
                + ", ".join(
                    divergencias
                )
            )

        elif pendencias:

            st.warning(
                "🟠 Não foram encontradas divergências "
                "nos dados informados, mas existem campos "
                "não informados nos dois documentos."
            )

            st.write(
                "**Campos não informados:** "
                + ", ".join(
                    pendencias
                )
            )

        else:

            st.success(
                "🟢 Os dados analisados estão consistentes "
                "entre o Cadastro Municipal e a Legalização."
            )

        # ====================================================
        # CONFERÊNCIA TÉCNICA
        # ====================================================

        with st.expander(
            "🛠️ Conferência técnica da extração"
        ):

            st.write(
                "**Quantidade de CNAEs no Cadastro:**",
                len(cadastro["cnaes"])
            )

            st.write(
                [
                    formatar_cnae(cnae)
                    for cnae in cadastro["cnaes"]
                ]
            )

            st.write(
                "**Quantidade de CNAEs na Legalização:**",
                len(legalizacao["cnaes"])
            )

            st.write(
                [
                    formatar_cnae(cnae)
                    for cnae in legalizacao["cnaes"]
                ]
            )

            st.write(
                "**Número extraído do Cadastro:**",
                cadastro["numero"]
            )

            st.write(
                "**Logradouro extraído do Cadastro:**",
                cadastro["logradouro"]
            )

            st.write(
                "**Bairro extraído do Cadastro:**",
                cadastro["bairro"]
            )

            st.write(
                "**Complemento extraído do Cadastro:**",
                cadastro["complemento"]
            )

            st.write(
                "**CEP extraído do Cadastro:**",
                cadastro["cep"]
            )

            st.write("**Sócios extraídos do Cadastro Municipal:**", cadastro["socios"])
            st.write("**Sócios extraídos da Legalização:**", legalizacao["socios"])
