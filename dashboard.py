import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Olist Business Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# Fix Teks Putih agar tetap Hitam dan Terlihat Jelas
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #000000 !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv('all_data.csv')
    rfm = pd.read_csv('rfm_data.csv')
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df, rfm

try:
    df, rfm = load_data()
except Exception as e:
    st.error("Pastikan file 'all_data.csv' dan 'rfm_data.csv' ada di folder yang sama!")
    st.stop()

# --- SIDEBAR CONTROL ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Olist_logo.svg/1200px-Olist_logo.svg.png", width=150)
st.sidebar.title("Dashboard Control")

# FITUR GESER-GESER (Slider Rentang Waktu)
st.sidebar.subheader("Pilih Rentang Waktu")
# Membuat daftar bulan-tahun unik untuk slider agar tidak terlalu rapat
df['month_year'] = df['order_purchase_timestamp'].dt.strftime('%b %Y')
unique_months = df.sort_values('order_purchase_timestamp')['month_year'].unique().tolist()

# Slider Geser untuk milih Bulan
start_m, end_m = st.sidebar.select_slider(
    'Geser untuk mengatur periode:',
    options=unique_months,
    value=(unique_months[0], unique_months[-1])
)

# Filter Wilayah
states = st.sidebar.multiselect("Pilih Wilayah (State):", options=sorted(df["customer_state"].unique()), default=df["customer_state"].unique())

# --- PROSES FILTER DATA ---
# Konversi kembali pilihan slider ke format datetime untuk filtering
main_df = df[(df['month_year'].isin(unique_months[unique_months.index(start_m):unique_months.index(end_m)+1])) & 
             (df["customer_state"].isin(states))]

# --- HEADER ---
st.title("🛍️ Olist Executive Business Overview")
st.markdown(f"Menampilkan performa bisnis dari periode **{start_m}** hingga **{end_m}**.")

# --- KPI METRICS ---
col1, col2, col3, col4 = st.columns(4)
total_orders = main_df['order_id'].nunique()
total_revenue = main_df['total_price'].sum()
avg_order = total_revenue / total_orders if total_orders > 0 else 0
unique_cust = main_df['customer_unique_id'].nunique()

col1.metric("Total Orders", f"{total_orders:,}")
col2.metric("Total Revenue", f"R$ {total_revenue:,.2f}")
col3.metric("Avg. Ticket Size", f"R$ {avg_order:.2f}")
col4.metric("Unique Customers", f"{unique_cust:,}")

st.divider()

# --- MAIN ANALYSIS TABS ---
tab1, tab2, tab3 = st.tabs(["📈 Analisis Penjualan", "👥 Segmentasi Pelanggan", "📍 Produk & Wilayah"])

with tab1:
    st.subheader("Tren Pertumbuhan Pendapatan")
    monthly_sales = main_df.resample('M', on='order_purchase_timestamp')['total_price'].sum().reset_index()
    fig_sales = px.area(monthly_sales, x='order_purchase_timestamp', y='total_price', 
                        labels={'total_price': 'Revenue (R$)'}, template="plotly_white", color_discrete_sequence=['#0083B8'])
    st.plotly_chart(fig_sales, use_container_width=True)

with tab2:
    col_rfm1, col_rfm2 = st.columns([1, 1])
    with col_rfm1:
        st.subheader("Distribusi Segmen")
        segment_counts = rfm['Segment'].value_counts().reset_index()
        fig_rfm = px.pie(segment_counts, values='count', names='Segment', hole=0.5,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_rfm, use_container_width=True)
    with col_rfm2:
        st.subheader("Detail Angka Segmentasi")
        st.dataframe(segment_counts, use_container_width=True)

with tab3:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("10 Kategori Produk Teratas")
        top_cats = main_df.groupby('product_category_name_english')['total_price'].sum().nlargest(10).reset_index()
        fig_cat = px.bar(top_cats, y='product_category_name_english', x='total_price', orientation='h', 
                         color='total_price', color_continuous_scale='GnBu')
        st.plotly_chart(fig_cat, use_container_width=True)
    with col_p2:
        st.subheader("Penjualan per Negara Bagian")
        state_sales = main_df.groupby('customer_state')['total_price'].sum().reset_index().sort_values('total_price', ascending=False)
        fig_state = px.bar(state_sales.head(10), x='customer_state', y='total_price', color='total_price', color_continuous_scale='Blues')
        st.plotly_chart(fig_state, use_container_width=True)

# --- REKOMENDASI STRATEGIS ---
st.divider()
st.header("🚀 Rencana Aksi Bisnis")
champions = rfm[rfm['Segment'] == 'Champions (VIP)'].shape[0]
at_risk = rfm[rfm['Segment'] == 'At Risk / Hibernating'].shape[0]
top_prod = top_cats.iloc[0]['product_category_name_english'] if not top_cats.empty else "N/A"

c1, c2, c3 = st.columns(3)
c1.info(f"**Pertahankan VIP:** Manjakan **{champions:,} pelanggan VIP** dengan promo eksklusif.")
c2.warning(f"**Ajak Balik At Risk:** Segera sapa **{at_risk:,} pelanggan lama** sebelum mereka churn.")
c3.success(f"**Stok Barang:** Pastikan kategori **{top_prod}** selalu tersedia karena peminatnya tinggi.")

st.caption(f"© {datetime.now().year} Fathan Rezah | Data Science Freelance Portfolio")