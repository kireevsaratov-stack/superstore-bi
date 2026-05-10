import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# Настройка страницы
st.set_page_config(
    page_title="Superstore BI",
    page_icon="📊",
    layout="wide"
)


# ============ РАБОТА С КУРСОМ ВАЛЮТ ============

@st.cache_data(ttl=86400)
def get_exchange_rates():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    response = requests.get(url)
    current_data = response.json()
    current_rate = current_data['Valute']['USD']['Value']

    rates = {}
    years = [2014, 2015, 2016, 2017]

    for year in years:
        for month in range(1, 13):
            date_str = f"{year}-{month:02d}-01"
            archive_url = f"https://www.cbr-xml-daily.ru/archive/{date_str}/daily_json.js"
            try:
                resp = requests.get(archive_url)
                if resp.status_code == 200:
                    data = resp.json()
                    rate = data['Valute']['USD']['Value']
                    rates[date_str] = rate
            except:
                continue

    return rates


def convert_to_rub(df, rates):
    df = df.copy()
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Month_Key'] = df['Order Date'].dt.strftime('%Y-%m-01')
    df['Rate'] = df['Month_Key'].map(rates)
    avg_rate = sum(rates.values()) / len(rates) if rates else 60
    df['Rate'] = df['Rate'].fillna(avg_rate)
    df['Sales'] = df['Sales'] * df['Rate']
    df['Profit'] = df['Profit'] * df['Rate']
    return df


# ============ ЗАГРУЗКА ДАННЫХ ============

@st.cache_data
def load_data():
    df = pd.read_csv('Sample - Superstore.csv', encoding='latin1')
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.month
    return df


# ============ ЗАГРУЗКА КУРСОВ ============

rates = get_exchange_rates()

# ============ ЗАГРУЗКА ДАННЫХ (ДОЛЖНА БЫТЬ ПЕРЕД ФИЛЬТРАМИ) ============

df_raw = load_data()

# ============ UI ============

st.sidebar.header("🎛️ Фильтры")

show_rub = st.sidebar.toggle("🇷🇺 Показать в рублях", value=False)

if show_rub:
    currency_symbol = "₽"
    st.sidebar.info("Курсы ЦБ РФ загружены (исторические, по месяцам)")
else:
    currency_symbol = "$"

regions = ['Все'] + list(df_raw['Region'].unique())
selected_region = st.sidebar.selectbox("Регион", regions)

years = ['Все'] + sorted(df_raw['Year'].unique().tolist())
selected_year = st.sidebar.selectbox("Год", years)

# ФИЛЬТРАЦИЯ
df_filtered = df_raw.copy()

if selected_region != 'Все':
    df_filtered = df_filtered[df_filtered['Region'] == selected_region]
if selected_year != 'Все':
    df_filtered = df_filtered[df_filtered['Year'] == int(selected_year)]

if show_rub:
    df_filtered = convert_to_rub(df_filtered, rates)

# ============ ГЛАВНАЯ СТРАНИЦА ============

st.title("📊 Superstore BI Dashboard")
st.markdown(
    f"*Данные: {df_filtered['Order Date'].min().strftime('%d.%m.%Y')} — {df_filtered['Order Date'].max().strftime('%d.%m.%Y')}*")

col1, col2, col3, col4 = st.columns(4)

total_sales = df_filtered['Sales'].sum()
total_profit = df_filtered['Profit'].sum()

with col1:
    st.metric(f"💰 Продажи", f"{currency_symbol}{total_sales:,.0f}")
with col2:
    st.metric(f"📈 Прибыль", f"{currency_symbol}{total_profit:,.0f}")
with col3:
    avg_discount = df_filtered['Discount'].mean() * 100
    st.metric("🏷️ Средняя скидка", f"{avg_discount:.1f}%")
with col4:
    customers = df_filtered['Customer ID'].nunique()
    st.metric("👥 Клиентов", f"{customers:,}")

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Продажи по категориям")
    sales_cat = df_filtered.groupby('Category')['Sales'].sum().reset_index()
    fig = px.pie(sales_cat, values='Sales', names='Category', hole=0.3)
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Продажи по месяцам")
    monthly = df_filtered.groupby(['Year', 'Month'])['Sales'].sum().reset_index()
    monthly['Date'] = pd.to_datetime(monthly['Year'].astype(str) + '-' + monthly['Month'].astype(str) + '-01')
    fig = px.line(monthly, x='Date', y='Sales', markers=True)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("🏆 Топ-10 продуктов")
top10 = df_filtered.groupby('Product Name')['Sales'].sum().sort_values(ascending=False).head(10)
fig = px.bar(x=top10.values, y=top10.index, orientation='h')
fig.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("📋 Статистика по регионам")
stats = df_filtered.groupby('Region').agg({'Sales': 'sum', 'Profit': 'sum', 'Order ID': 'nunique'}).round(0)
st.dataframe(stats, use_container_width=True)

st.markdown("---")
st.caption("Курсы валют: ЦБ РФ • Данные обновляются раз в сутки")