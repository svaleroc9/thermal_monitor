import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="Analizador COP – Calentador de Agua", layout="wide")

st.title("🔥 Analizador de Datos – COP Calentador de Agua (ESP32 + FS300A)")

st.write("""
Sube tu archivo CSV con columnas:

**Tiempo, T_in, T_out, T_tank, Caudal(L/min)**  
y la app generará automáticamente:

- Temperaturas vs tiempo  
- ΔT = T_out – T_in  
- Caudal vs tiempo  
- Cálculo del COP  
- Integración del volumen ignorando caudal < 0.5  
""")

# =========================== UPLOAD CSV ===========================
file = st.file_uploader("📤 Sube tu archivo CSV", type=["csv"])

if file:
    # Leer CSV
    df = pd.read_csv(file)

    st.success("CSV cargado correctamente ✔")

    st.write("### Vista previa de los datos:")
    st.dataframe(df.head())

    # ======================= HORA DE INICIO =======================
    st.write("## ⏰ Hora real de inicio de la toma de datos")
    start_time = st.time_input("Selecciona la hora (ejemplo: 07:56:00)")

    # Convertir los tiempos de "mm:ss" a tiempo real
    df["Tiempo"] = pd.to_timedelta(df["Tiempo"])

    # Sumar la hora real
    df["Tiempo_real"] = pd.to_datetime(start_time.strftime("%H:%M:%S")) + df["Tiempo"]

    # ======================= GRAFICAS =======================
    st.write("## 📈 Gráfica de Temperaturas")

    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.plot(df["Tiempo_real"], df["T_in"], label="T_in")
    ax1.plot(df["Tiempo_real"], df["T_out"], label="T_out")
    ax1.plot(df["Tiempo_real"], df["T_tank"], label="T_tank")
    ax1.set_xlabel("Tiempo")
    ax1.set_ylabel("Temperatura (°C)")
    ax1.legend()
    ax1.grid()
    st.pyplot(fig1)

    # ======================= DELTA T =======================
    st.write("## 📉 ΔT = T_out – T_in")

    df["DeltaT"] = df["T_out"] - df["T_in"]

    fig2, ax2 = plt.subplots(figsize=(12, 4))
    ax2.plot(df["Tiempo_real"], df["DeltaT"], color="purple")
    ax2.set_xlabel("Tiempo")
    ax2.set_ylabel("ΔT (°C)")
    ax2.grid()
    st.pyplot(fig2)

    # ======================= CAUDAL =======================
    st.write("## 💧 Caudal (L/min)")

    fig3, ax3 = plt.subplots(figsize=(12, 4))
    ax3.plot(df["Tiempo_real"], df["Caudal(L/min)"], color="orange")
    ax3.set_xlabel("Tiempo")
    ax3.set_ylabel("Caudal (L/min)")
    ax3.grid()
    st.pyplot(fig3)

    # ======================= CÁLCULO DEL COP =======================
    st.write("## ⚡ Cálculo del COP")

    voltaje = st.number_input("Voltaje (V)", value=208.0)
    corriente = st.number_input("Corriente promedio (A)", value=8.0)

    P_el = voltaje * corriente  # Potencia eléctrica
    st.write(f"**Potencia eléctrica:** {P_el:.1f} W")

    # ===== Integración del volumen ignorando caudal < 0.5 L/min =====
    volumen = 0
    for i in range(1, len(df)):
        caudal = df.loc[i, "Caudal(L/min)"]
        if caudal < 0.5:
            continue

        t1 = df.loc[i-1, "Tiempo_real"]
        t2 = df.loc[i, "Tiempo_real"]
        dt = (t2 - t1).total_seconds() / 60  # minutos

        volumen += caudal * dt

    st.write(f"**Volumen calentado:** {volumen:.2f} L")

    # ===== Calor aportado m·cp·ΔT =====
    rho = 1  # kg/L
    cp = 4180  # J/kgK
    deltaT_tank = df["T_tank"].iloc[-1] - df["T_tank"].iloc[0]

    Q = volumen * rho * cp * deltaT_tank  # Joules

    tiempo_total_s = (df["Tiempo_real"].iloc[-1] - df["Tiempo_real"].iloc[0]).total_seconds()
    Q_dot = Q / tiempo_total_s  # W

    COP = Q_dot / P_el

    st.write(f"**ΔT del tanque:** {deltaT_tank:.2f} °C")
    st.write(f"**Transferencia de calor útil (W):** {Q_dot:.2f}")
    st.write(f"# ⭐ COP estimado: **{COP:.2f}**")

    # ======================= DESCARGAR RESULTADOS =======================
    st.write("## 📥 Descargar datos corregidos")

    df_export = df.copy()
    df_csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button("Descargar CSV corregido", df_csv, "datos_corregidos.csv")
