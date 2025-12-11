import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ======================== CONFIGURACIÓN GENERAL ========================
st.set_page_config(
    page_title="Analizador COP – Calentador de Agua",
    page_icon="🔥",
    layout="wide"
)

# Tema claro (evitar fondo negro)
st.markdown("""
    <style>
        body { background-color: #ffffff !important; }
        h1, h2, h3 { color: #222222; }
    </style>
""", unsafe_allow_html=True)

st.title("🔥 Analizador de Datos – COP Calentador de Agua (ESP32 + FS300A)")
st.write("Sube tu archivo CSV para analizar temperaturas, caudal y calcular el COP.")

# =========================== SUBIR ARCHIVO =============================
file = st.file_uploader("📤 Sube tu archivo CSV", type=["csv"])

if not file:
    st.info("📄 Esperando que subas un archivo CSV...")
    st.stop()

df = pd.read_csv(file)
st.success("CSV cargado correctamente ✔")

# =========================== PROCESAR TIEMPO ============================
st.subheader("⏰ Hora real de inicio del experimento")

start_time = st.time_input("Selecciona la hora de inicio (ej: 07:56:00)")

# Convertir "mm:ss" a timedelta
df["Tiempo"] = pd.to_timedelta(df["Tiempo"])

# Crear hora sin zona horaria
inicio = pd.to_datetime(str(start_time), format="%H:%M:%S")

# Tiempo real corregido
df["Tiempo_real"] = inicio + df["Tiempo"]

# Crear DeltaT AHORA para evitar errores
df["DeltaT"] = df["T_out"] - df["T_in"]

# ========================== DISEÑO EN PESTAÑAS ==========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 Datos",
    "📈 Gráficas",
    "⚡ Cálculo COP",
    "📥 Descargar",
    "📘 ¿Cómo se calcula el COP?"
])

# =========================== TAB 1: DATOS ==============================
with tab1:
    st.subheader("Vista previa del archivo")
    st.dataframe(df.head())
    st.write("Dimensiones del archivo:", df.shape)

# =========================== TAB 2: GRAFICAS ===========================
with tab2:
    st.subheader("📈 Gráfica de Temperaturas")

    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.plot(df["Tiempo_real"], df["T_in"], label="T_in", linewidth=2)
    ax1.plot(df["Tiempo_real"], df["T_out"], label="T_out", linewidth=2)
    ax1.plot(df["Tiempo_real"], df["T_tank"], label="T_tank", linewidth=2)

    ax1.set_xlabel("Tiempo")
    ax1.set_ylabel("Temperatura (°C)")

    ax1.grid(which="major", alpha=0.3)
    ax1.grid(which="minor", alpha=0.15)
    ax1.minorticks_on()
    ax1.legend()

    st.pyplot(fig1)

    # ---------- ΔT ----------
    st.subheader("📉 ΔT = $T_{out} - T_{in}$")

    fig2, ax2 = plt.subplots(figsize=(12, 4))
    ax2.plot(df["Tiempo_real"], df["DeltaT"], color="purple", linewidth=2)
    ax2.set_xlabel("Tiempo")
    ax2.set_ylabel("ΔT ($T_{out} - T_{in}$) [°C]")

    ax2.grid(which="major", alpha=0.3)
    ax2.grid(which="minor", alpha=0.15)
    ax2.minorticks_on()

    st.pyplot(fig2)

    # ---------- Caudal ----------
    st.subheader("💧 Caudal (L/min)")

    fig3, ax3 = plt.subplots(figsize=(12, 4))
    ax3.plot(df["Tiempo_real"], df["Caudal(L/min)"], color="orange", linewidth=2)
    ax3.set_xlabel("Tiempo")
    ax3.set_ylabel("Caudal (L/min)")

    ax3.grid(which="major", alpha=0.3)
    ax3.grid(which="minor", alpha=0.15)
    ax3.minorticks_on()

    st.pyplot(fig3)

# =========================== TAB 3: COP ================================
with tab3:
    st.subheader("⚡ Cálculo del COP")

    modo = st.radio(
        "Selecciona el modo de cálculo del COP:",
        ("Caudalímetro (flujo abierto)", "Volumen fijo (tanque cerrado)")
    )

    voltaje = st.number_input("Voltaje (V)", value=208.0)
    corriente = st.number_input("Corriente promedio (A)", value=8.0)
    P_el = voltaje * corriente

    st.write(f"**Potencia eléctrica consumida:** {P_el:.1f} W")

    rho = 1       # kg/L
    cp = 4180     # J/kgK

    # ------- MODO 1: Flujo Abierto -------
    if modo == "Caudalímetro (flujo abierto)":
        st.subheader("🔄 Modo flujo abierto")

        volumen = 0
        for i in range(1, len(df)):
            caudal = df.loc[i, "Caudal(L/min)"]
            if caudal < 0.5:
                continue
            dt = (df.loc[i, "Tiempo_real"] - df.loc[i-1, "Tiempo_real"]).total_seconds() / 60
            volumen += caudal * dt

        st.write(f"**Volumen calentado:** {volumen:.2f} L")

        deltaT_tank = df["T_tank"].iloc[-1] - df["T_tank"].iloc[0]
        Q = volumen * rho * cp * deltaT_tank

        tiempo_total_s = (df["Tiempo_real"].iloc[-1] - df["Tiempo_real"].iloc[0]).total_seconds()
        Q_dot = Q / tiempo_total_s
        COP = Q_dot / P_el

        st.write(f"🔺 ΔT tanque: **{deltaT_tank:.2f} °C**")
        st.write(f"🔥 Transferencia térmica útil: **{Q_dot:.2f} W**")
        st.write(f"# ⭐ COP estimado (flujo abierto): **{COP:.2f}**")

    # ------- MODO 2: Tanque Cerrado -------
    else:
        st.subheader("🔒 Modo tanque cerrado (volumen fijo)")

        volumen_fijo = st.number_input("Volumen de agua dentro del tanque (L)", value=140.0)

        T_inicial = df["T_tank"].iloc[0]
        T_final = df["T_tank"].iloc[-1]
        deltaT = T_final - T_inicial

        st.write(f"Temperatura inicial: **{T_inicial:.2f} °C**")
        st.write(f"Temperatura final: **{T_final:.2f} °C**")
        st.write(f"ΔT total del tanque: **{deltaT:.2f} °C**")

        Q = volumen_fijo * rho * cp * deltaT

        tiempo_total_s = (df["Tiempo_real"].iloc[-1] - df["Tiempo_real"].iloc[0]).total_seconds()
        Q_dot = Q / tiempo_total_s
        COP = Q_dot / P_el

        st.write(f"🔥 Transferencia térmica útil: **{Q_dot:.2f} W**")
        st.write(f"# ⭐ COP estimado (tanque cerrado): **{COP:.2f}**")

# =========================== TAB 4: DESCARGAS ==========================
with tab4:
    st.subheader("📥 Descargar CSV corregido")

    df_csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Descargar archivo corregido",
        df_csv,
        "datos_corregidos.csv",
        mime="text/csv"
    )

with tab5:
    st.subheader("📘 ¿Cómo se calcula el COP?")

    st.markdown(r"""
El **Coeficiente de Desempeño (COP)** mide qué tan eficiente es un sistema de calefacción.

## 🔷 Definición general

$$
COP = \frac{\dot{Q}}{P_{el}}
$$

---

# 🔵 1. Modo Flujo Abierto (Caudalímetro)

Cuando el agua fluye a través del tanque:

$$
Q = m\, c_p\, (T_{out} - T_{in})
$$

El volumen calentado se obtiene integrando el caudal:

$$
m = \rho \int \dot{V}(t)\, dt
$$

Luego, la potencia térmica útil es:

$$
\dot{Q} = \frac{Q}{\Delta t}
$$

---

# 🔵 2. Modo Tanque Cerrado (Volumen fijo)

Cuando cierras la llave, el volumen del tanque es fijo:

$$
Q = m\, c_p\, (T_{final} - T_{inicial})
$$

con

$$
m = \rho\, V_{tanque}
$$

Y el COP se calcula igual:

$$
COP = \frac{\dot{Q}}{P_{el}}
$$

---

# 🔧 Supuestos utilizados

- Agua con densidad aproximada:  
  $$ \rho \approx 1\ \text{kg/L} $$
- Calor específico del agua:  
  $$ c_p = 4180\ \text{J/(kg·K)} $$
- No se consideran pérdidas térmicas del tanque.  
- El tiempo se toma desde la hora corregida ingresada por el usuario.

---
""")
