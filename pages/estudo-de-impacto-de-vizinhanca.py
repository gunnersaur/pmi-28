import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk
import re
import os
from itertools import chain

#Configurações do Streamlit

st.set_page_config(page_title='Estudo de Impacto de vizinhança - EIV', 
                   layout="centered", 
                   initial_sidebar_state='expanded',
                   page_icon=('images/favicon.png'), 
                   menu_items=None
                   )

logo_image = ('images/logo.png')


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

df_insc=pd.read_csv("dados/inscricao_zoneamento-antigo.csv")
df_eiv=pd.read_csv("dados/anexo_eiv.csv", nrows=2000)

#Página principal do Streamlit - fixa
st.subheader('Estudo de Impacto de Vizinhança - EIV')

col1, col2 = st.columns(2)

with col1:
    ib_insc = st.text_input(
    "Inscrição Imobiliária (Padrão 000.000.00.0000)",
    key="ib_isc"
    )

with col2:
    ib_tipo = st.selectbox(
      "Tipo de empreendimento ou Atividade",
      ('','Residencial Multifamiliar', 'Uso Misto','Residencial Multifamiliar (Caixa da via < 8m)','Uso Misto (Caixa da via < 8m)','Residencial Multifamiliar (Caixa da via < 6m)', 'Uso Misto (Caixa da via < 6m)', 'Comércio e serviços', 'Educacional', 'Hospitais, clínicas, centros de zoonose e similares','Ginásios esportivos e estádios', 'Postos de combustível', 'Restaurantes, bares, tabacarias, casas noturnas, casa de jogos e similares','Industrial','Loteamento','Triagem, reciclagem, transbordo e aterro','Templos, igrejas, centros culturais e outros','Centro de convenções, eventos, pavilhões e feiras', 'Clubes recreativos, de lazer, esportivo e similares','Autódromo, kártódromo, hipódromo, aeródromo e similares', 'Depósito, armazéns, pátio de veículos, transportadoras e afins', 'Terminais urbanos, interurbanos de qualquer modal', 'Penitenciárias e presídios','Parques de diversão (Não itinerantes)', 'Cemitério e crematório', 'Condomínio horizontal','Estação de tratamento de água e esgoto','Portos, terminais portuários e portos secos','Estaleiros ou marinas'),
      key="ib_tipo"
      )



def clear_text():
    st.session_state["ib_tipo"] = ""
    st.session_state["ib_insc"] = ""
st.button("Limpar", on_click=clear_text)
st.markdown('De acordo com a LC414/2022. Anexo I da lei considera o antigo zoneamento - LC215/2012')
st.divider() 

#Printa elementos
try:
  if ib_insc != "":
    st.subheader('Zoneamento')
    df_insc = df_insc.loc[df_insc['inscricao'] == ib_insc]
    st.dataframe(df_insc, hide_index=True)
    st.subheader('Verificação necessidade EIV')
    zona=df_insc['nome'].unique().tolist()
    zona=''.join(zona)
    df_eiv = df_eiv.loc[df_eiv['ZONEAMENTO'] == str(zona)]
    if ib_tipo != "":
      df_eiv = df_eiv.loc[df_eiv['USO/ ATIVIDADE'] == ib_tipo]
    st.dataframe(df_eiv, hide_index=True)
    st.markdown('https://docs.google.com/spreadsheets/d/1vwx3hPDPmSIU-N1KE2iXfstt-ZH1jGQhhz0ZPNrA-vY/edit#gid=0')
except:
    st.markdown(''':red[Verifique o correto preenchimento de todos os campos.]''')


