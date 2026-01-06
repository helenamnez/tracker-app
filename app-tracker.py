import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Mi Tracker Cloud", layout="wide")

# 1. PEGA AQUÍ TU URL DE GOOGLE SHEETS
URL_HOJA = "https://docs.google.com/spreadsheets/d/1RGWplM97f0gzTGB06UuJwvH8el_DbbYv_1SfXf2CIkY/edit?usp=sharing"

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos(pestana):
    try:
        # ttl=0 para que no use caché y veamos los datos al momento
        return conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
    except:
        return pd.DataFrame()

def guardar_datos(df_nuevo, pestana):
    df_actual = leer_datos(pestana)
    df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
    conn.update(spreadsheet=URL_HOJA, worksheet=pestana, data=df_final)
    st.success(f"¡{pestana} actualizado en la nube!")
    st.rerun()

# --- INTERFAZ ---
tab_hab, tab_gas, tab_gym = st.tabs(["📊 Habit tracker", "💰 Butxaca", "🏋️ Gym"])

# --- TAB HÁBITOS ---
with tab_hab:
    st.header("Habit Tracker (máx 9)")
    df_h = leer_datos("habitos")
    
    if not df_h.empty:
        # Lógica de puntos
        h_bool = ['CCCCM', 'Hielo+hipo AM', 'Esport', 'Cepillo', 'Exfoliante', 'Modo_avion', 'Lectura']
        for h in h_bool:
            if h in df_h.columns:
                df_h[f'p_{h}'] = df_h[h].apply(lambda x: 1 if str(x).lower() in ['true', '1', 'si', 'sí', 't'] else 0)
        
        df_h['p_Prote'] = df_h['Prote'].apply(lambda x: 1 if x >= 120 else 0) if 'Prote' in df_h.columns else 0
        df_h['p_Pasos'] = df_h['Pasos'].apply(lambda x: 1 if x >= 10000 else 0) if 'Pasos' in df_h.columns else 0
        
        cols_p = [c for c in df_h.columns if c.startswith('p_')]
        df_h['%'] = (df_h[cols_p].sum(axis=1) / 9) * 100
        st.plotly_chart(px.line(df_h, x='Fecha', y='%', markers=True))

    with st.expander("📝 Registrar Día"):
        with st.form("f_hab", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            f_fecha = c1.date_input("Fecha", date.today())
            f_pro = c1.number_input("Proteína", 0)
            f_pas = c1.number_input("Pasos", 0)
            f_cc = c2.checkbox("CCCCM")
            f_hi = c2.checkbox("Hielo")
            f_es = c2.checkbox("Esport")
            f_ce = c3.checkbox("Cepillo")
            f_ex = c3.checkbox("Exfoliante")
            f_le = c3.checkbox("Lectura")
            f_mo = st.checkbox("Modo avion")
            
            if st.form_submit_button("Guardar"):
                nuevo = pd.DataFrame([{'Fecha': str(f_fecha), 'CCCCM': f_cc, 'Hielo+hipo AM': f_hi, 'Prote': f_pro, 'Pasos': f_pas, 'Esport': f_es, 'Cepillo': f_ce, 'Exfoliante': f_ex, 'Lectura': f_le, 'Modo_avion': f_mo}])
                guardar_datos(nuevo, "habitos")

# --- TAB GASTOS ---
with tab_gas:
    st.header("Gastos")
    df_g = leer_datos("gastos")
    if not df_g.empty:
        df_g['Monto'] = df_g.apply(lambda x: x['Cantidad'] if str(x['Naturalesa']).lower() == 'ingreso' else x['Cantidad'] * -1, axis=1)
        st.metric("Balance Total", f"{df_g['€'].sum():.2f} €")
        st.plotly_chart(px.bar(df_g, x='Fecha', y='€', color='Monto'))

    with st.expander("💶 Nuevo Gasto/Ingreso"):
        with st.form("f_gas", clear_on_submit=True):
            fg_f = st.date_input("Fecha")
            fg_con = st.text_input("Concepto")
            fg_can = st.number_input("Cantidad", 0.0)
            fg_nat = st.selectbox("Naturaleza", ["Gasto", "Ingreso"])
            if st.form_submit_button("Guardar"):
                nuevo_g = pd.DataFrame([{'Fecha': str(fg_f), 'Concepto': fg_con, 'Cantidad': fg_can, 'Naturalesa': fg_nat}])
                guardar_datos(nuevo_g, "gastos")

# --- TAB GYM ---
with tab_gym:
    st.header("Gym: Siguiente Nivel")
    df_gym = leer_datos("gym")
    
    # Para el filtro, usamos una lista fija o cargamos del Sheet de config si lo creas
    ej_list = ["Prensa de piernas", "Extension cuadriceps", "Hip thrust", "Abductor fuera", "Sentadilla", "Bulgaras"] 
    
    sel = st.selectbox("Ejercicio:", ej_list)
    
    if not df_gym.empty and sel in df_gym['Ejercicio'].values:
        d_ej = df_gym[df_gym['Ejercicio'] == sel]
        d_ej['Volumen'] = d_ej['Peso'] * d_ej['Reps']
        st.plotly_chart(px.area(d_ej, x='Fecha', y='Volumen', markers=True))
        
        if d_ej.iloc[-1]['Esfuerzo'] <= 7:
            st.success("🚀 ¡Nivel subiendo! Dale más peso.")

    with st.expander("🏋️ Nueva Serie"):
        with st.form("f_gym", clear_on_submit=True):
            gy_f = st.date_input("Fecha")
            gy_ej = st.selectbox("Ejercicio", ej_list)
            gy_p = st.number_input("Peso", 0.0)
            gy_r = st.number_input("Reps", 0)
            gy_e = st.slider("RPE (Esfuerzo)", 1, 10, 7)
            if st.form_submit_button("Guardar Serie"):
                nuevo_s = pd.DataFrame([{'Fecha': str(gy_f), 'Ejercicio': gy_ej, 'Peso': gy_p, 'Reps': gy_r, 'Esfuerzo': gy_e}])
                guardar_datos(nuevo_s, "gym")
