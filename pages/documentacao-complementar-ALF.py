import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk
import re
import os
from itertools import chain

#Configurações do Streamlit

st.set_page_config(page_title='Documentação complementar - ALF', 
                   layout="centered", 
                   initial_sidebar_state='expanded',
                   page_icon=('images/favicon.png'), 
                   menu_items=None
                   )

logo_image = ('images/logo.png')

#page_icon=('images/favicon.png'), 
#logo_image = ('images/logo.png')

#Sidebar
st.sidebar.image(logo_image, width=150)
st.sidebar.divider()
st.sidebar.page_link("app.py", label="01_Consulta de Viabilidade (inscr.)")
st.sidebar.page_link("pages/cv_zona.py", label="__Consulta de Viabilidade (zona)")
st.sidebar.page_link("pages/verifica_aprova.py", label="02_Verifica processo ALF")
st.sidebar.page_link("pages/links.py", label="03_Links úteis")
st.sidebar.page_link("pages/documentacao-complementar-ALF.py", label="04_Doc. complementar ALF")
st.sidebar.page_link("pages/estudo-de-impacto-de-vizinhanca.py", label="05_EIV")

#Tabelas CSV

df_docs=pd.read_csv("dados/relacao_docs_alf.csv")

#Página principal do Streamlit - fixa
st.subheader('Documentação complementar - ALF - Aprova Digital')

ib_cnpj = st.text_input(
    "Cole todo o texto do CNPJ ou do processo do Aprova Digital",
    key="ib_cnpj"
    )

#Botão limpar

def clear_text():
    st.session_state["ib_aprova"] = ""
    st.session_state["ib_cnpj"] = ""
st.button("Limpar", on_click=clear_text)

#Análise da documentação complementar
try:
    if ib_cnpj != "":
        cnaes_cnpj = re.findall(r'\d\d.\d\d-\d-\d\d', ib_cnpj)


        cnaes_cnpj=pd.DataFrame(cnaes_cnpj)
        cnaes_cnpj = cnaes_cnpj.rename(columns={'0': 'codigo'})
        df_filtrado=df_docs.merge(cnaes_cnpj,left_on='codigo', right_on=0)
        st.dataframe(df_filtrado)

except:
    st.markdown(''':red[Verifique o correto preenchimento de todos os campos.]''')
