import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Настройка страницы
st.set_page_config(
    page_title="Superstore BI",
    page_icon="📊",
    layout="wide"
)

# Загрузка данных с кэшированием
@st.cache_data
def load_data():
    df = pd.read_csv('Sample - Superstore.csv', encoding='latin1')
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.month
    return df

df = load_data()

# Боковая панель с фильтрами
st.sidebar.header("🎛️ Фильтры")

# Фильтр по региону
regions = ['Все'] + list(df['Region'].unique())
selected_region = st.sidebar.selectbox("Регион", regions)

# Фильтр по году
years = ['Все'] + sorted(df['Year'].unique().tolist())
selected_year = st.sidebar.selectbox("Год", years)

# Фильтрация данных
df_filtered = df.copy()
if selected_region != 'Все':
    df_filtered = df_filtered[df_filtered['Region'] == selected_region]
if selected_year != 'Все':
    df_filtered = df_filtered[df_filtered['Year'] == int(selected_year)]

# Главная страница
st.title("📊 Superstore BI Dashboard")
st.markdown(f"*Данные за период: {df_filtered['Order Date'].min().strftime('%d.%m.%Y')} - {df_filtered['Order Date'].max().strftime('%d.%m.%Y')}*")

# KPI метрики
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sales = df_filtered['Sales'].sum()
    st.metric(
        label="💰 Общие продажи",
        value=f"${total_sales:,.0f}",
        delta=f"{len(df_filtered):,} заказов"
    )

with col2:
    total_profit = df_filtered['Profit'].sum()
    st.metric(
        label="📈 Прибыль",
        value=f"${total_profit:,.0f}",
        delta=f"Рентабельность: {(total_profit/total_sales*100):.1f}%"
    )

with col3:
    avg_discount = df_filtered['Discount'].mean() * 100
    st.metric(
        label="🏷️ Средняя скидка",
        value=f"{avg_discount:.1f}%"
    )

with col4:
    unique_customers = df_filtered['Customer ID'].nunique()
    st.metric(
        label="👥 Клиентов",
        value=f"{unique_customers:,}"
    )

# Графики
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Продажи по категориям")
    sales_by_cat = df_filtered.groupby('Category')['Sales'].sum().reset_index()
    fig = px.pie(
        sales_by_cat,
        values='Sales',
        names='Category',
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Продажи по месяцам")
    sales_by_month = df_filtered.groupby(['Year', 'Month'])['Sales'].sum().reset_index()
    sales_by_month['Date'] = pd.to_datetime(
        sales_by_month['Year'].astype(str) + '-' +
        sales_by_month['Month'].astype(str) + '-01'
    )
    fig = px.line(
        sales_by_month,
        x='Date',
        y='Sales',
        markers=True,
        labels={'Sales': 'Продажи ($)', 'Date': 'Дата'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Топ продуктов
st.markdown("---")
st.subheader("🏆 Топ-10 продуктов")

top_products = df_filtered.groupby('Product Name')['Sales'].sum().sort_values(ascending=False).head(10)
fig = px.bar(
    x=top_products.values,
    y=top_products.index,
    orientation='h',
    labels={'x': 'Продажи ($)', 'y': 'Товар'},
    color=top_products.values,
    color_continuous_scale='Viridis'
)
fig.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig, use_container_width=True)

# Детальная статистика
st.markdown("---")
st.subheader("📋 Детальная статистика по регионам")

stats_by_region = df_filtered.groupby('Region').agg({
    'Sales': ['sum', 'mean'],
    'Profit': 'sum',
    'Order ID': 'nunique'
}).round(2)

stats_by_region.columns = ['Продажи (всего)', 'Средний чек', 'Прибыль', 'Кол-во заказов']
stats_by_region = stats_by_region.sort_values('Продажи (всего)', ascending=False)

st.dataframe(stats_by_region, use_container_width=True)

# Подвал
st.markdown("---")
st.markdown("📊 **Superstore BI Dashboard** | Создано с помощью Streamlit")