import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os

st.set_page_config(page_title="Mi Tracker Total", layout="wide")

# --- FUNCIONES DE SEGURIDAD ---

def cargar_csv(nombre_archivo):
    if os.path.exists(nombre_archivo):
        try:
            df = pd.read_csv(nombre_archivo)
            df.columns = df.columns.str.strip()
            if not df.empty:
                col_f = next((c for c in df.columns if 'fecha' in c.lower() or 'date' in c.lower()), None)
                if col_f:
                    df = df.rename(columns={col_f: 'Fecha'})
                    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            return df
        except:
            # Si falla, reseteamos para evitar el error de "tokenizing data"
            os.rename(nombre_archivo, f"corrupto_{nombre_archivo}")
            st.warning(f"Archivo {nombre_archivo} reseteado por error de formato.")
            return pd.DataFrame()
    return pd.DataFrame()

def guardar_datos_seguro(df_nuevo, nombre_archivo):
    if not os.path.exists(nombre_archivo):
        df_nuevo.to_csv(nombre_archivo, index=False)
    else:
        df_existente = pd.read_csv(nombre_archivo)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        df_final.to_csv(nombre_archivo, index=False)

def procesar_habitos(df):
    if df.empty: return df
    h_bool = ['CCCCM', 'Hielo+hipo AM', 'Esport', 'Cepillo', 'Exfoliante', 'Modo avion', 'Lectura']
    for h in h_bool:
        if h in df.columns:
            df[f'p_{h}'] = df[h].apply(lambda x: 1 if str(x).lower() in ['true', '1', 'si', 'sí', 't'] else 0)
    df['p_Prote'] = df['Prote (g)'].apply(lambda x: 1 if x >= 120 else 0) if 'Prote (g)' in df.columns else 0
    df['p_Pasos'] = df['Pasos'].apply(lambda x: 1 if x >= 10000 else 0) if 'Pasos' in df.columns else 0
    cols_p = [c for c in df.columns if c.startswith('p_')]
    df['Porcentaje_Total'] = (df[cols_p].sum(axis=1) / 9) * 100
    return df

# --- INTERFAZ ---
tab_hab, tab_gas, tab_gym = st.tabs(["📊 Hábitos", "💰 Gastos", "🏋️ Gym"])

# --- TAB HÁBITOS ---
with tab_hab:
    st.header("Habit Tracker")
    df_h = cargar_csv('habit_tracker.csv')
    if not df_h.empty:
        df_h = procesar_habitos(df_h)
        st.plotly_chart(px.line(df_h, x='Fecha', y='Porcentaje_Total', markers=True), use_container_width=True)
    
    with st.expander("📝 Nuevo Registro Diario"):
        with st.form("f_hab", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            f_fecha = c1.date_input("Fecha", date.today())
            f_prote = c1.number_input("Proteína (g)", 0)
            f_pasos = c1.number_input("Pasos", 0)
            f_cc = c2.checkbox("CCCCM")
            f_hi = c2.checkbox("Hielo+hipo AM")
            f_es = c2.checkbox("Esport")
            f_ce = c3.checkbox("Cepillo")
            f_ex = c3.checkbox("Exfoliante")
            f_le = c3.checkbox("Lectura")
            f_mo = st.checkbox("Modo avion")
            if st.form_submit_button("Guardar"):
                nueva_f = pd.DataFrame([{'Fecha': f_fecha, 'CCCCM': f_cc, 'Hielo+hipo AM': f_hi, 'Prote (g)': f_prote, 'Pasos': f_pasos, 'Esport': f_es, 'Cepillo': f_ce, 'Exfoliante': f_ex, 'Lectura': f_le, 'Modo avion': f_mo}])
                guardar_datos_seguro(nueva_f, 'habit_tracker.csv')
                st.rerun()

# --- TAB GASTOS ---
with tab_gas:
    st.header("Gastos y Balance")
    df_g = cargar_csv('gastos.csv')
    if not df_g.empty:
        df_g['Monto'] = df_g.apply(lambda x: x['Cantidad'] if str(x['Naturalesa']).lower() == 'ingreso' else x['Cantidad'] * -1, axis=1)
        df_g['Mes'] = df_g['Fecha'].dt.strftime('%Y-%m')
        st.metric("Balance Total", f"{df_g['Monto'].sum():.2f} €")
        st.plotly_chart(px.bar(df_g.groupby('Mes')['Monto'].sum().reset_index(), x='Mes', y='Monto', color='Monto', color_continuous_scale='RdYlGn'), use_container_width=True)

    with st.expander("💶 Añadir Movimiento"):
        with st.form("f_gas", clear_on_submit=True):
            f_f = st.date_input("Fecha")
            f_con = st.text_input("Concepto")
            f_can = st.number_input("Cantidad", 0.0)
            f_nat = st.selectbox("Naturaleza", ["Gasto", "Ingreso"])
            if st.form_submit_button("Guardar"):
                nueva_g = pd.DataFrame([{'Fecha': f_f, 'Concepto': f_con, 'Cantidad': f_can, 'Naturalesa': f_nat}])
                guardar_datos_seguro(nueva_g, 'gastos.csv')
                st.rerun()

# --- TAB GYM ---
with tab_gym:
    st.header("Gym: Rumbo al Siguiente Nivel")
    df_gym = cargar_csv('gym.csv')
    
    # 1. ARREGLO DEL FILTRO: Cogemos la lista de TODOS los ejercicios del config
    if os.path.exists('config.csv'):
        # Leemos el config para que el filtro tenga TODO (Sentadilla, Búlgaras, etc.)
        lista_completa_ej = pd.read_csv('config.csv')['Ejercicio'].unique().tolist()
    else:
        lista_completa_ej = df_gym['Ejercicio'].unique().tolist() if not df_gym.empty else []

    if lista_completa_ej:
        sel = st.selectbox("Analizar Ejercicio:", lista_completa_ej)
        
        # Filtramos los datos registrados para ese ejercicio
        if not df_gym.empty and sel in df_gym['Ejercicio'].values:
            d_ej = df_gym[df_gym['Ejercicio'] == sel].sort_values('Fecha')
            d_ej['Volumen'] = d_ej['Peso'] * d_ej['Reps']
            
            # Gráfico de progreso
            st.plotly_chart(px.area(d_ej, x='Fecha', y='Volumen', 
                                    title=f"Evolución de Fuerza: {sel}", 
                                    markers=True, color_discrete_sequence=['#00CC96']))
            
            # Lógica de nivel
            ultima = d_ej.iloc[-1]
            if ultima['Esfuerzo'] <= 7: 
                st.success(f"💪 RPE {ultima['Esfuerzo']}: ¡Estás sobrando! Sube peso en la próxima sesión.")
            else:
                st.info(f"🔥 RPE {ultima['Esfuerzo']}: Intensidad perfecta. Mantente ahí.")
        else:
            st.info(f"Aún no tienes datos registrados para '{sel}'. ¡Dale caña al entreno!")

    # 2. REGISTRO (Mantiene tu lógica de antes)
    with st.expander("🏋️ Registrar Serie"):
        with st.form("f_gym", clear_on_submit=True):
            g_f = st.date_input("Fecha", date.today())
            g_ej = st.selectbox("Ejercicio", lista_completa_ej)
            g_p = st.number_input("Peso (kg)", 0.0, step=0.5)
            g_r = st.number_input("Reps", 0, step=1)
            g_e = st.slider("Esfuerzo (RPE)", 1, 10, 7)
            if st.form_submit_button("Guardar Serie"):
                nueva_s = pd.DataFrame([{'Fecha': g_f, 'Ejercicio': g_ej, 'Peso': g_p, 'Reps': g_r, 'Esfuerzo': g_e}])
                guardar_datos_seguro(nueva_s, 'gym.csv')
                st.rerun()