import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from pathlib import Path

# Tampilan dashboard
st.set_page_config(
    page_title='Bike Sharing Dashboard',
    layout='wide'
)

sns.set_theme(style='whitegrid', palette='muted')

# Membaca dataset day.csv
BASE_DIR = Path(__file__).resolve().parent
all_df = pd.read_csv(BASE_DIR / 'main_data.csv')

# Menyiapkan DataFrame
all_df['dteday'] = pd.to_datetime(all_df['dteday'])
all_df.sort_values(by='dteday', inplace=True)

# Mengubah kode musim menjadi nama musim
season_mapping = {
    1: 'Musim Semi',
    2: 'Musim Panas',
    3: 'Musim Gugur',
    4: 'Musim Dingin'
}

all_df['season_name'] = all_df['season'].map(season_mapping)

# Mengubah kode cuaca menjadi keterangan
weather_mapping = {
    1: 'Cerah',
    2: 'Berkabut/Berawan',
    3: 'Hujan/Salju Ringan',
    4: 'Cuaca Ekstrem'
}

all_df['weather_name'] = all_df['weathersit'].map(weather_mapping)


# function untuk menyiapkan data visualisasi
def create_seasonal_summary_df(df):
    seasonal_df = df.groupby(
        ['season_name', 'yr'], as_index=False
    )['cnt'].mean()

    seasonal_df['year'] = seasonal_df['yr'].map({
        0: '2011',
        1: '2012'
    })

    return seasonal_df


def create_seasonal_growth_df(df):
    seasonal_df = df.groupby(
        ['season_name', 'yr']
    )['cnt'].mean().unstack()

    if 0 not in seasonal_df.columns or 1 not in seasonal_df.columns:
        return pd.DataFrame()

    seasonal_df['growth_percentage'] = (
        (seasonal_df[1] - seasonal_df[0]) / seasonal_df[0]
    ) * 100

    return seasonal_df.reset_index()


def create_weather_summary_df(df):
    weather_df = df.groupby(
        'weather_name', as_index=False
    ).agg(
        average_rentals=('cnt', 'mean'),
        total_days=('cnt', 'count')
    )

    return weather_df


def create_user_type_df(df):
    user_df = pd.DataFrame({
        'Jenis Pengguna': ['Terdaftar', 'Kasual'],
        'Total Penyewaan': [
            df['registered'].sum(),
            df['casual'].sum()
        ]
    })

    return user_df


# Filter pada sidebar
min_date = all_df['dteday'].min().date()
max_date = all_df['dteday'].max().date()

with st.sidebar:
    st.title('Bike Sharing')
    st.write('Filter data penyewaan sepeda')

    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )

# Filter DataFrame berdasarkan tanggal
main_df = all_df[
    (all_df['dteday'] >= pd.Timestamp(start_date)) &
    (all_df['dteday'] <= pd.Timestamp(end_date))
].copy()

if main_df.empty:
    st.warning('Tidak terdapat data pada rentang tanggal yang dipilih.')
    st.stop()


# Menyiapkan DataFrame untuk visualisasi
seasonal_df = create_seasonal_summary_df(main_df)
growth_df = create_seasonal_growth_df(main_df)
weather_df = create_weather_summary_df(main_df)
user_df = create_user_type_df(main_df)


# Menampilkan header dashboard
st.title('Bike Sharing Dashboard')
st.caption(
    'Analisis penyewaan sepeda di Washington D.C. '
    'berdasarkan data tahun 2011–2012.'
)

st.divider()


# Membuat tab dashboard
tab1, tab2 = st.tabs([
    'Ringkasan',
    'Analisis Penyewaan'
])


with tab1:

    # Metrik utama
    st.subheader('Ringkasan Penyewaan Sepeda')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            'Total Penyewaan',
            value=f"{main_df['cnt'].sum():,.0f}"
        )

    with col2:
        st.metric(
            'Penyewaan Terdaftar',
            value=f"{main_df['registered'].sum():,.0f}"
        )

    with col3:
        st.metric(
            'Penyewaan Kasual',
            value=f"{main_df['casual'].sum():,.0f}"
        )

    st.divider()

    # Komposisi jenis pengguna
    st.subheader('Komposisi Penyewaan Berdasarkan Jenis Pengguna')
    st.caption('Perbandingan total penyewaan pengguna terdaftar dan kasual.')

    fig, ax = plt.subplots(figsize=(7, 5))

    ax.pie(
        user_df['Total Penyewaan'],
        labels=user_df['Jenis Pengguna'],
        autopct='%1.1f%%',
        startangle=90,
        colors=['#65A98F', '#A7C7E7'],
        wedgeprops={
            'width': 0.4,
            'edgecolor': 'white'
        },
        pctdistance=0.8
    )

    ax.text(
        0,
        0,
        'Total\nPenyewaan',
        ha='center',
        va='center',
        fontsize=12,
        fontweight='bold'
    )

    ax.axis('equal')

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


with tab2:

    # Pertumbuhan penyewaan berdasarkan musim
    st.subheader('Pertumbuhan Penyewaan Berdasarkan Musim')
    st.caption('Perbandingan persentase pertumbuhan rata-rata penyewaan harian tahun 2011 dan 2012.')

    if not growth_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))

        growth_df = growth_df.sort_values(
            by='growth_percentage',
            ascending=True
        )

        colors = [
            '#A8CDB8' if value != growth_df['growth_percentage'].max()
            else '#2E8B57'
            for value in growth_df['growth_percentage']
        ]

        bars = ax.barh(
            growth_df['season_name'],
            growth_df['growth_percentage'],
            color=colors
        )

        for bar in bars:
            ax.text(
                bar.get_width() + 2,
                bar.get_y() + bar.get_height() / 2,
                f'{bar.get_width():.2f}%',
                va='center',
                fontsize=10
            )

        ax.set_xlabel('Pertumbuhan (%)')
        ax.set_ylabel('Musim')
        ax.set_xlim(0, growth_df['growth_percentage'].max() * 1.2)
        ax.grid(axis='x', linestyle='--', alpha=0.3)
        ax.grid(axis='y', visible=False)

        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    else:
        st.info('Pilih rentang tanggal yang mencakup tahun 2011 dan 2012 untuk melihat pertumbuhan.')

    st.divider()

    # Rata-rata penyewaan berdasarkan cuaca
    st.subheader('Penyewaan Berdasarkan Kondisi Cuaca')
    st.caption('Perbandingan rata-rata penyewaan sepeda harian pada setiap kondisi cuaca.')

    fig, ax = plt.subplots(figsize=(10, 5))

    weather_order = [
        'Cerah',
        'Berkabut/Berawan',
        'Hujan/Salju Ringan',
        'Cuaca Ekstrem'
    ]

    weather_df['weather_name'] = pd.Categorical(
        weather_df['weather_name'],
        categories=weather_order,
        ordered=True
    )

    weather_df = weather_df.sort_values('weather_name')

    sns.barplot(
        data=weather_df,
        x='weather_name',
        y='average_rentals',
        color='#83B6A0',
        ax=ax
    )

    for bar in ax.patches:
        ax.annotate(
            f'{bar.get_height():,.0f}',
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            ha='center',
            va='bottom',
            fontsize=10,
            xytext=(0, 5),
            textcoords='offset points'
        )

    ax.set_xlabel('Kondisi Cuaca')
    ax.set_ylabel('Rata-rata Penyewaan Harian')
    ax.set_ylim(bottom=0)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.grid(axis='x', visible=False)

    plt.xticks(rotation=15)
    plt.tight_layout()

    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.divider()

    # Perbandingan penyewaan berdasarkan musim dan tahun
    st.subheader('Perbandingan Penyewaan Berdasarkan Musim')
    st.caption('Rata-rata penyewaan harian pada setiap musim tahun 2011 dan 2012.')

    fig, ax = plt.subplots(figsize=(10, 5))

    season_order = [
        'Musim Semi',
        'Musim Panas',
        'Musim Gugur',
        'Musim Dingin'
    ]

    sns.barplot(
        data=seasonal_df,
        x='season_name',
        y='cnt',
        hue='year',
        order=season_order,
        palette=['#A7C7E7', '#65A98F'],
        errorbar=None,
        ax=ax
    )

    ax.set_xlabel('Musim')
    ax.set_ylabel('Rata-rata Penyewaan Harian')
    ax.legend(title='Tahun')
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.grid(axis='x', visible=False)

    plt.xticks(rotation=10)
    plt.tight_layout()

    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


st.divider()

st.caption(
    'Sumber data: Bike Sharing Dataset. '
    'Seluruh metrik dan visualisasi mengikuti rentang tanggal yang dipilih.'
)
