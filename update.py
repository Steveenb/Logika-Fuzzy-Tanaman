import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt
import io
import pandas as pd

# mengatur gaya matplotlib untuk plot yang lebih baik
plt.style.use('seaborn-v0_8')

# --- DEFINISI VARIABEL FUZZY ---
kelembapan = ctrl.Antecedent(np.arange(0, 101, 1), 'Kelembapan')
suhu = ctrl.Antecedent(np.arange(0, 51, 1), 'Suhu')
durasi = ctrl.Consequent(np.arange(0, 11, 1), 'Durasi')

# --- FUZZY MEMBERSHIP FUNCTIONS ---
# Kelembapan tanah dengan distribusi yang lebih realistis
kelembapan['kering'] = fuzz.trapmf(kelembapan.universe, [0, 0, 25, 45])
kelembapan['lembab'] = fuzz.trimf(kelembapan.universe, [35, 55, 75])
kelembapan['basah'] = fuzz.trapmf(kelembapan.universe, [65, 85, 100, 100])

# Suhu udara dengan distribusi yang lebih smooth
suhu['dingin'] = fuzz.trapmf(suhu.universe, [0, 0, 15, 25])
suhu['sedang'] = fuzz.trimf(suhu.universe, [20, 30, 40])
suhu['panas'] = fuzz.trapmf(suhu.universe, [35, 45, 50, 50])

# Durasi penyiraman dengan distribusi yang lebih baik
durasi['sebentar'] = fuzz.trapmf(durasi.universe, [0, 0, 2, 4])
durasi['sedang'] = fuzz.trimf(durasi.universe, [3, 5, 7])
durasi['lama'] = fuzz.trapmf(durasi.universe, [6, 8, 10, 10])

# --- RULE BASE ---
rules = [
    ctrl.Rule(kelembapan['kering'] & suhu['panas'], durasi['lama']),
    ctrl.Rule(kelembapan['kering'] & suhu['sedang'], durasi['sedang']),
    ctrl.Rule(kelembapan['kering'] & suhu['dingin'], durasi['sedang']),
    ctrl.Rule(kelembapan['lembab'] & suhu['panas'], durasi['sedang']),
    ctrl.Rule(kelembapan['lembab'] & suhu['sedang'], durasi['sebentar']),
    ctrl.Rule(kelembapan['lembab'] & suhu['dingin'], durasi['sebentar']),
    ctrl.Rule(kelembapan['basah'], durasi['sebentar'])
]

# --- SISTEM KONTROL ---
penyiram_ctrl = ctrl.ControlSystem(rules)
penyiram = ctrl.ControlSystemSimulation(penyiram_ctrl)

# --- CUSTOM PLOTTING FUNCTION ---
def plot_membership_function(variable, title, colors=None):
    """Custom function to plot membership functions with better styling"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Default colors
    if colors is None:
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    # Plot each membership function
    for i, (label, mf) in enumerate(variable.terms.items()):
        ax.plot(variable.universe, mf.mf, 
                linewidth=3, 
                label=label.capitalize(), 
                color=colors[i % len(colors)],
                alpha=0.8)
        ax.fill_between(variable.universe, 0, mf.mf, 
                       alpha=0.3, 
                       color=colors[i % len(colors)])
    
    ax.set_title(f'Fungsi Keanggotaan {title}', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel(f'{title} ({variable.label})', fontsize=12)
    ax.set_ylabel('Derajat Keanggotaan', fontsize=12)
    ax.legend(loc='upper right', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)
    
    # Add subtle background
    ax.set_facecolor('#F8F9FA')
    
    plt.tight_layout()
    return fig

# --- STREAMLIT UI ---
st.set_page_config(page_title="Smart Fuzzy Irrigation", page_icon="🌿")
st.title("🌿 Smart Fuzzy Irrigation System")
st.markdown("## Masukkan Kondisi Lingkungan Tanaman")
st.markdown("Masukkan nilai suhu udara dan kelembapan tanah untuk menentukan durasi penyiraman tanaman.")

# Enhanced information section
with st.expander("ℹ️ Informasi Sistem"):
    st.markdown("""
    ### Cara Kerja Sistem Fuzzy Logic:
    
    **Input Variables:**
    - **Kelembapan Tanah (0-100%)**: Kering, Lembab, Basah
    - **Suhu Udara (0-50°C)**: Dingin, Sedang, Panas
    
    **Output Variable:**
    - **Durasi Penyiraman (0-10 menit)**: Sebentar, Sedang, Lama
    
    **Aturan Fuzzy:**
    1. Jika tanah kering dan suhu panas → Siram lama
    2. Jika tanah kering dan suhu sedang → Siram sedang
    3. Jika tanah kering dan suhu dingin → Siram sedang
    4. Jika tanah lembab dan suhu panas → Siram sedang
    5. Jika tanah lembab dan suhu sedang → Siram sebentar
    6. Jika tanah lembab dan suhu dingin → Siram sebentar
    7. Jika tanah basah → Siram sebentar
    """)

# masukkan input pengguna
suhu_input = st.slider("🌡️ Suhu Udara (°C)", 0, 50, 25)
kelembapan_input = st.slider("💧 Kelembapan Tanah (%)", 0, 100, 50)

# instalasi session state
if 'history' not in st.session_state:
    st.session_state.history = []

# tombol hitung
if st.button("🔍 Hitung Durasi Penyiraman"):
    try:
        # setting input values
        penyiram.input['Suhu'] = suhu_input
        penyiram.input['Kelembapan'] = kelembapan_input
        
        # menghitung hasil
        penyiram.compute()
        hasil = penyiram.output['Durasi']
        
        # Display result with better formatting
        st.success(f"### Durasi penyiraman yang disarankan: {hasil:.2f} menit")
        
        # Narasi AI yang Disempurnakan
        if hasil < 3:
            st.info("🌱 **Penyiraman Sebentar**: Tanah cukup basah. Penyiraman sebentar saja sudah cukup untuk menjaga kondisi optimal.")
        elif hasil < 6:
            st.info("🌿 **Penyiraman Sedang**: Tanah agak kering. Penyiraman sedang disarankan untuk menjaga kelembapan yang tepat.")
        else:
            st.warning("🔥 **Penyiraman Lama**: Tanah sangat kering dan suhu tinggi. Butuh penyiraman lebih lama untuk mengembalikan kelembapan optimal.")
        
        # buat dan tampilkan grafik durasi
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # plot semua fungsi keanggotaan untuk durasi
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
            for i, (label, mf) in enumerate(durasi.terms.items()):
                ax.plot(durasi.universe, mf.mf, 
                       linewidth=2, 
                       label=f'Durasi {label.capitalize()}', 
                       color=colors[i],
                       alpha=0.7)
                ax.fill_between(durasi.universe, 0, mf.mf, 
                               alpha=0.2, 
                               color=colors[i])
            
            # lihat hasil 
            ax.axvline(x=hasil, color='red', linestyle='--', linewidth=3, 
                      label=f'Hasil: {hasil:.2f} menit')
            ax.scatter([hasil], [0.05], color='red', s=100, zorder=5)
            
            ax.set_title('Grafik Durasi Penyiraman dengan Hasil Perhitungan', 
                        fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Durasi (menit)', fontsize=12)
            ax.set_ylabel('Derajat Keanggotaan', fontsize=12)
            ax.legend(loc='upper right', frameon=True, shadow=True)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 1.1)
            ax.set_facecolor('#F8F9FA')
            
            plt.tight_layout()
            
            # pindahkan plot ke image
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=150, bbox_inches='tight')
            buf.seek(0)
            st.image(buf, caption="Grafik Hasil Fuzzy Logic dengan Indikator Hasil")
            plt.close(fig)  # tutup untuk membebaskan memori
            
        except Exception as e:
            st.error(f"Gagal menampilkan grafik durasi: {e}")
        
        # simpan ke riwayat
        st.session_state.history.append({
            'Suhu (°C)': suhu_input,
            'Kelembapan (%)': kelembapan_input,
            'Durasi (menit)': round(hasil, 2)
        })
        
    except Exception as e:
        st.error(f"Terjadi kesalahan dalam perhitungan: {e}")

# buat tab untuk grafik fungsi keanggotaan
with st.expander("📊 Lihat Grafik Fungsi Keanggotaan"):
    st.markdown("### Fungsi Keanggotaan untuk Setiap Variabel")
    
    # buat tab untuk setiap variabel
    tab1, tab2, tab3 = st.tabs(["💧 Kelembapan Tanah", "🌡️ Suhu Udara", "⏱️ Durasi Penyiraman"])
    
    with tab1:
        try:
            fig1 = plot_membership_function(kelembapan, "Kelembapan Tanah (%)", 
                                          ['#3498DB', '#2ECC71', '#E74C3C'])
            st.pyplot(fig1)
            plt.close(fig1)
            
            st.markdown("""
            **Interpretasi Kelembapan Tanah:**
            - 🔴 **Kering (0-45%)**: Tanah membutuhkan penyiraman
            - 🟢 **Lembab (35-75%)**: Kondisi kelembapan optimal
            - 🔵 **Basah (65-100%)**: Tanah sudah cukup basah
            """)
        except Exception as e:
            st.error(f"Gagal menampilkan grafik kelembapan: {e}")
    
    with tab2:
        try:
            fig2 = plot_membership_function(suhu, "Suhu Udara (°C)", 
                                          ['#3498DB', '#F39C12', '#E74C3C'])
            st.pyplot(fig2)
            plt.close(fig2)
            
            st.markdown("""
            **Interpretasi Suhu Udara:**
            - 🔵 **Dingin (0-25°C)**: Suhu rendah, evaporasi minimal
            - 🟠 **Sedang (20-40°C)**: Suhu normal, evaporasi sedang
            - 🔴 **Panas (35-50°C)**: Suhu tinggi, evaporasi tinggi
            """)
        except Exception as e:
            st.error(f"Gagal menampilkan grafik suhu: {e}")
    
    with tab3:
        try:
            fig3 = plot_membership_function(durasi, "Durasi Penyiraman (menit)", 
                                          ['#2ECC71', '#F39C12', '#E74C3C'])
            st.pyplot(fig3)
            plt.close(fig3)
            
            st.markdown("""
            **Interpretasi Durasi Penyiraman:**
            - 🟢 **Sebentar (0-4 menit)**: Penyiraman ringan
            - 🟠 **Sedang (3-7 menit)**: Penyiraman normal
            - 🔴 **Lama (6-10 menit)**: Penyiraman intensif
            """)
        except Exception as e:
            st.error(f"Gagal menampilkan grafik durasi: {e}")

# Tingkat riwayat simulasi
if st.session_state.history:
    st.subheader("📋 Riwayat Simulasi")
    df_history = pd.DataFrame(st.session_state.history)
    
    # tambah statistik
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Simulasi", len(df_history))
    with col2:
        st.metric("Rata-rata Durasi", f"{df_history['Durasi (menit)'].mean():.2f} menit")
    with col3:
        st.metric("Durasi Max", f"{df_history['Durasi (menit)'].max():.2f} menit")
    
    st.dataframe(df_history, use_container_width=True)
    
    # tingkat grafik riwayat
    if len(df_history) > 1:
        st.subheader("📈 Grafik Riwayat Durasi")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(range(len(df_history)), df_history['Durasi (menit)'], 
               marker='o', linewidth=2, markersize=8, color='#3498DB')
        ax.set_title('Tren Durasi Penyiraman', fontsize=14, fontweight='bold')
        ax.set_xlabel('Simulasi ke-')
        ax.set_ylabel('Durasi (menit)')
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#F8F9FA')
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    
    # Pilihan untuk mengunduh riwayat
    csv = df_history.to_csv(index=False)
    st.download_button(
        label="📥 Download Riwayat CSV",
        data=csv,
        file_name="riwayat_penyiraman.csv",
        mime="text/csv"
    )

# Tombol untuk menghapus riwayat
if st.session_state.history:
    if st.button("🗑️ Hapus Riwayat"):
        st.session_state.history = []
        st.rerun()

st.markdown("---")
st.caption("Dibuat dengan cinta dan kasih sayang • © 2025")