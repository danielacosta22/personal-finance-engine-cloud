import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import random
import database as db

# Configuración Inicial
st.set_page_config(
    page_title="Personal Finance Engine v1.0",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos Personalizados
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #00BCD4;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #FFFFFF;
    }
    .metric-title {
        font-size: 1rem;
        color: #A0A0A0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar Base de Datos
db.init_db()

# --- Funciones Auxiliares ---
def get_daniel_factor():
    frases = [
        "Ingeniero Daniel, la eficiencia de su flujo de efectivo está dentro de los parámetros nominales. Siga así.",
        "Alerta de sobrecarga: Asegure que sus pasivos no superen el coeficiente de fricción de sus activos.",
        "Diagnóstico completado: El sistema financiero requiere mantenimiento preventivo en el rubro de 'Alimentación'.",
        "Calibración exitosa: Su nivel de ahorro muestra una tendencia asintótica hacia la riqueza.",
        "Error 404: Excesos no encontrados. Procesos financieros corriendo a máxima eficiencia.",
        "El throughput de sus ingresos es estable. ¿Hora de escalar operaciones?",
        "Se ha detectado una alta latencia en la consecución de sus metas. Sugerimos inyectar capital."
    ]
    return random.choice(frases)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/900/900782.png", width=100)
    st.title("Daniel Acosta Edition")
    st.markdown("---")
    navegacion = st.radio("Módulos del Sistema", 
                          ["Control Center", "Gestor de Flujos", "Laboratorio de Metas", "Configuración de Categorías", "Telemetría y Reportes"])
    
    st.markdown("---")
    st.info(f"**El Factor Daniel:**\n\n_{get_daniel_factor()}_")


# --- PANEL PRINCIPAL ---

if navegacion == "Control Center":
    st.header("⚙️ Control Center (Dashboard 360)")
    
    ingresos, gastos, balance = db.get_balance_global()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Balance Neto</div><div class="metric-value">${balance:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card" style="border-left-color: #4CAF50;"><div class="metric-title">Ingresos Totales</div><div class="metric-value">${ingresos:,.2f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card" style="border-left-color: #F44336;"><div class="metric-title">Gastos Totales</div><div class="metric-value">${gastos:,.2f}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    st.subheader("🔋 Visualizador de Metas Dinámico")
    metas_df = db.get_metas()
    if metas_df.empty:
        st.info("Aún no tienes metas activas. Ve al Laboratorio de Metas para inicializar un proyecto.")
    else:
        # Calcular progreso y tarjetas
        cols = st.columns(3)
        for i, row in metas_df.iterrows():
            with cols[i % 3]:
                st.markdown(f"#### {row['icono']} {row['nombre_meta']}")
                progreso = min(1.0, row['monto_actual'] / row['monto_objetivo']) if row['monto_objetivo'] > 0 else 0
                st.progress(progreso, text=f"{progreso*100:.1f}% Completado (${row['monto_actual']:,.2f} / ${row['monto_objetivo']:,.2f})")
                st.caption(f"Fecha límite: {row['fecha_limite']}")

elif navegacion == "Gestor de Flujos":
    st.header("🔀 Gestor de Flujos (Transacciones)")
    
    tipo_txn = st.selectbox("Tipo de Operación", ["Ingreso", "Gasto"])
    
    # Obtener categorías según el tipo
    categorias_df = db.get_categorias(tipo_txn)
    opciones_cat = categorias_df['nombre'].tolist() if not categorias_df.empty else ["Sin categorías"]
    
    # Obtener metas para asociar (si es gasto)
    metas_df = db.get_metas()
    opciones_metas = ["Ninguna"] + metas_df['nombre_meta'].tolist() if not metas_df.empty else ["Ninguna"]
    
    with st.expander("➕ Ingresar Nueva Transacción", expanded=True):
        with st.form("form_txn", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha de Registro", datetime.now())
                monto = st.number_input("Monto Numérico ($)", min_value=0.01, step=100.0)
            with col2:
                categoria = st.selectbox("Categoría Clasificatoria", opciones_cat)
                
                meta_asociada = None
                meta_id = None
                if tipo_txn == "Gasto":
                    meta_asociada = st.selectbox("Asociar a Meta (Opcional)", opciones_metas)
                    if meta_asociada != "Ninguna":
                        meta_id = metas_df[metas_df['nombre_meta'] == meta_asociada]['id'].iloc[0]
                        st.info(f"El monto ingresado aquí se inyectará automáticamente a la meta '{meta_asociada}'")
            
            descripcion = st.text_input("Descripción (Log)")
            submit_btn = st.form_submit_button("Confirmar Transacción")
            
            if submit_btn:
                # Validaciones
                if categoria == "Sin categorías":
                    st.error("Error: Se requiere al menos una categoría válida configurada.")
                else:
                    db.add_transaccion(fecha.strftime("%Y-%m-%d"), tipo_txn, categoria, monto, descripcion, meta_id)
                    
                    if meta_asociada and meta_asociada != "Ninguna" and meta_id:
                        db.update_meta_funds(meta_id, monto)
                        st.success(f"Transacción registrada. Capital inyectado a la meta '{meta_asociada}' exitosamente.")
                    else:
                        st.success("Transacción registrada en el log del sistema.")

    # Mostrar historial reciente
    st.subheader("📜 Historial Reciente")
    df_txns = db.get_transacciones()
    if not df_txns.empty:
        # Boton de borrar opcional (simple implementation)
        st.dataframe(df_txns[['fecha', 'tipo', 'categoria', 'monto', 'descripcion']], use_container_width=True)
    else:
        st.write("No hay registros en la base de datos.")

elif navegacion == "Laboratorio de Metas":
    st.header("🧪 Laboratorio de Metas")
    
    with st.expander("🏗️ Construir Nueva Meta", expanded=False):
        with st.form("form_meta", clear_on_submit=True):
            nombre = st.text_input("Nombre de la Meta (ej. Laptop Pro)")
            icono = st.text_input("Icono (Emoji)", value="🚀", max_chars=2)
            monto_obj = st.number_input("Monto Objetivo ($)", min_value=1.0, step=1000.0)
            fecha_lim = st.date_input("Fecha Límite Estimada")
            
            if st.form_submit_button("Inicializar Meta"):
                db.add_meta(nombre, monto_obj, fecha_lim.strftime("%Y-%m-%d"), icono)
                st.success("Nueva meta registrada y compilada en el sistema.")
                st.rerun()

    st.markdown("---")
    st.subheader("💉 Inyección de Capital a Metas Activas")
    metas_df = db.get_metas()
    if metas_df.empty:
        st.info("Inicia una meta primero para poder inyectarle capital.")
    else:
        with st.form("form_inyeccion", clear_on_submit=True):
            meta_sel = st.selectbox("Seleccionar Meta Destino", metas_df['nombre_meta'].tolist())
            monto_inyeccion = st.number_input("Monto a Inyectar ($)", min_value=0.01, step=100.0)
            
            if st.form_submit_button("Ejecutar Transferencia"):
                meta_id = metas_df[metas_df['nombre_meta'] == meta_sel]['id'].iloc[0]
                db.update_meta_funds(meta_id, monto_inyeccion)
                # Opcional: registrar como gasto de ahorro
                db.add_transaccion(datetime.now().strftime("%Y-%m-%d"), "Gasto", "Ahorro Activo", monto_inyeccion, f"Inyección a {meta_sel}", meta_id)
                st.success(f"Transferencia de ${monto_inyeccion:,.2f} completada hacia '{meta_sel}'.")
                st.rerun()

elif navegacion == "Configuración de Categorías":
    st.header("🛠️ Configuración de Categorías")
    st.write("Añade o elimina categorías para personalizar tu sistema de clasificación.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Agregar Categoría")
        with st.form("form_add_cat", clear_on_submit=True):
            nueva_cat = st.text_input("Nombre de la Categoría")
            tipo_cat = st.radio("Tipo", ["Ingreso", "Gasto"])
            if st.form_submit_button("Añadir"):
                if nueva_cat.strip() != "":
                    db.add_categoria(nueva_cat.strip(), tipo_cat)
                    st.success(f"Categoría '{nueva_cat}' añadida al sistema.")
                    st.rerun()
                else:
                    st.error("El nombre no puede estar vacío.")
                    
    with col2:
        st.subheader("Eliminar Categoría")
        categorias_df = db.get_categorias()
        if not categorias_df.empty:
            with st.form("form_del_cat"):
                cat_a_borrar = st.selectbox("Selecciona la categoría a eliminar", categorias_df.itertuples(), format_func=lambda x: f"{x.nombre} ({x.tipo})")
                if st.form_submit_button("Eliminar"):
                    db.delete_categoria(cat_a_borrar.id)
                    st.warning(f"Categoría '{cat_a_borrar.nombre}' eliminada del sistema.")
                    st.rerun()

elif navegacion == "Telemetría y Reportes":
    st.header("📡 Telemetría y Análisis de Datos")
    
    df_txns = db.get_transacciones()
    
    if df_txns.empty:
        st.info("Insuficientes datos para generar telemetría válida.")
    else:
        df_txns['fecha'] = pd.to_datetime(df_txns['fecha'])
        df_gastos = df_txns[df_txns['tipo'] == 'Gasto']
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribución de Gastos")
            if not df_gastos.empty:
                gastos_por_cat = df_gastos.groupby('categoria')['monto'].sum().reset_index()
                fig_donut = px.pie(gastos_por_cat, values='monto', names='categoria', hole=0.4, title="Análisis de Salida de Capital")
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.write("No hay gastos registrados.")
                
        with col2:
            st.subheader("Tendencia Financiera")
            balance_diario = df_txns.groupby(['fecha', 'tipo'])['monto'].sum().reset_index()
            fig_lines = px.line(balance_diario, x='fecha', y='monto', color='tipo', title="Flujo Nominal en el Tiempo", markers=True)
            st.plotly_chart(fig_lines, use_container_width=True)
            
        st.markdown("---")
        st.subheader("🧹 Limpieza de Datos y Respaldo")
        csv = df_txns.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar Dataset Completo (CSV)",
            data=csv,
            file_name=f'telemetria_financiera_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
