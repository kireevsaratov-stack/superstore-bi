import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import numpy as np

# ============ НАСТРОЙКИ ============
st.set_page_config(page_title="Superstore BI Pro", page_icon="📊", layout="wide")


# ============ КУРСЫ ВАЛЮТ ============
@st.cache_data(ttl=86400)
def get_exchange_rates():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    response = requests.get(url)
    current_data = response.json()
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
    df['Ship Date'] = pd.to_datetime(df['Ship Date'])
    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.month
    df['Quarter'] = df['Order Date'].dt.quarter
    df['Processing Days'] = (df['Ship Date'] - df['Order Date']).dt.days
    df['Margin %'] = (df['Profit'] / df['Sales'] * 100).round(1)

    # RFM анализ
    ref_date = df['Order Date'].max() + timedelta(days=1)
    rfm = df.groupby('Customer ID').agg({
        'Order Date': lambda x: (ref_date - x.max()).days,
        'Order ID': 'nunique',
        'Sales': 'sum'
    }).rename(columns={'Order Date': 'Recency', 'Order ID': 'Frequency', 'Sales': 'Monetary'})

    rfm['R'] = pd.qcut(rfm['Recency'], 3, labels=['Высокая', 'Средняя', 'Низкая'])
    rfm['F'] = pd.qcut(rfm['Frequency'].rank(method='first'), 3, labels=['Низкая', 'Средняя', 'Высокая'])
    rfm['M'] = pd.qcut(rfm['Monetary'], 3, labels=['Низкая', 'Средняя', 'Высокая'])

    def get_segment(row):
        if row['R'] == 'Высокая' and row['F'] == 'Высокая':
            return 'VIP'
        elif row['R'] in ['Высокая', 'Средняя'] and row['F'] in ['Высокая', 'Средняя']:
            return 'Лояльные'
        elif row['R'] == 'Низкая':
            return 'Потерянные'
        else:
            return 'Спящие'

    rfm['Segment'] = rfm.apply(get_segment, axis=1)

    df = df.merge(rfm[['Segment']], left_on='Customer ID', right_index=True, how='left')

    # ABC анализ
    product_profit = df.groupby('Product Name')['Profit'].sum().sort_values(ascending=False)
    product_cumsum = product_profit.cumsum() / product_profit.sum() * 100

    def get_abc(cumsum):
        if cumsum <= 50:
            return 'A - Золото'
        elif cumsum <= 80:
            return 'B - Середняки'
        else:
            return 'C - Балласт'

    abc = product_cumsum.apply(get_abc)
    df['ABC'] = df['Product Name'].map(abc)

    return df


# ============ ЗАГРУЗКА ============
rates = get_exchange_rates()
df_raw = load_data()

# ============ САЙДБАР ============
with st.sidebar:
    st.header("🎛️ Фильтры")

    st.subheader("💱 Валюта")
    show_rub = st.toggle("🇷🇺 Рубли", value=False)
    currency = "₽" if show_rub else "$"

    st.subheader("📅 Период")
    min_date = df_raw['Order Date'].min().date()
    max_date = df_raw['Order Date'].max().date()
    date_range = st.date_input("Выберите даты", [min_date, max_date], min_value=min_date, max_value=max_date)

    st.subheader("🌍 География")
    regions = ['Все'] + sorted(df_raw['Region'].unique().tolist())
    selected_region = st.selectbox("Регион", regions)

    if selected_region != 'Все':
        states = ['Все'] + sorted(df_raw[df_raw['Region'] == selected_region]['State'].unique().tolist())
        selected_state = st.selectbox("Штат", states)
    else:
        selected_state = 'Все'

    st.subheader("🏷️ Сегменты")
    categories = ['Все'] + sorted(df_raw['Category'].unique().tolist())
    selected_category = st.selectbox("Категория", categories)

    segments = ['Все']
    if 'Segment' in df_raw.columns:
    segments += sorted(df_raw['Segment'].dropna().unique().tolist())
    selected_segment = st.selectbox("RFM Сегмент", segments)

    st.subheader("🎨 Оформление")
    dark_mode = st.toggle("🌙 Тёмная тема", value=False)

    st.markdown("---")
    st.caption(f"Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

# ============ ФИЛЬТРАЦИЯ ============
df = df_raw.copy()
if len(date_range) == 2:
    df = df[(df['Order Date'].dt.date >= date_range[0]) & (df['Order Date'].dt.date <= date_range[1])]
if selected_region != 'Все':
    df = df[df['Region'] == selected_region]
if selected_state != 'Все':
    df = df[df['State'] == selected_state]
if selected_category != 'Все':
    df = df[df['Category'] == selected_category]
if selected_segment != 'Все':
    df = df[df['Segment'] == selected_segment]

if show_rub and len(df) > 0:
    df = convert_to_rub(df, rates)

# ============ ВКЛАДКИ ============
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Обзор", "📦 Продукты", "👥 Клиенты", "🌍 Гео", "💾 Экспорт"])

# ============ TAB 1: ОБЗОР ============
with tab1:
    st.title("📊 Общий обзор")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric(f"💰 Продажи", f"{currency}{df['Sales'].sum():,.0f}")
    with col2:
        profit = df['Profit'].sum()
        st.metric(f"📈 Прибыль", f"{currency}{profit:,.0f}", delta=f"{profit / df['Sales'].sum() * 100:.1f}%")
    with col3:
        st.metric("📦 Заказов", f"{df['Order ID'].nunique():,}")
    with col4:
        st.metric("👥 Клиентов", f"{df['Customer ID'].nunique():,}")
    with col5:
        st.metric("🏷️ Средняя скидка", f"{df['Discount'].mean() * 100:.1f}%")
    with col6:
        st.metric("🚚 Доставка (дни)", f"{df['Processing Days'].mean():.1f}")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Продажи по категориям")
        sales_cat = df.groupby('Category')['Sales'].sum().reset_index()
        fig = px.pie(sales_cat, values='Sales', names='Category', hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textinfo='percent+label+value', texttemplate='%{label}<br>%{percent}<br>%{value:,.0f}')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Прибыль по месяцам")
        monthly = df.groupby([df['Order Date'].dt.to_period('M')]).agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
        monthly['Order Date'] = monthly['Order Date'].astype(str)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly['Order Date'], y=monthly['Sales'], name='Продажи',
                                 fill='tozeroy', line=dict(color='#636EFA')))
        fig.add_trace(go.Scatter(x=monthly['Order Date'], y=monthly['Profit'], name='Прибыль',
                                 fill='tozeroy', line=dict(color='#00CC96')))
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔥 Скидки vs Прибыль")
        df['Discount Level'] = pd.cut(df['Discount'], bins=[-0.01, 0.05, 0.2, 0.5, 1],
                                      labels=['Без скидки', '0-5%', '5-20%', '20%+'])
        disc_profit = df.groupby('Discount Level', observed=False)['Profit'].sum().reset_index()
        colors = ['#00CC96' if x > 0 else '#EF553B' for x in disc_profit['Profit']]
        fig = px.bar(disc_profit, x='Discount Level', y='Profit', color='Discount Level',
                     color_discrete_sequence=colors, text_auto='.0f')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📈 Сезонность продаж")
        heatmap_data = df.pivot_table(values='Sales', index='Month', columns='Year', aggfunc='sum')
        fig = px.imshow(heatmap_data, text_auto='.0f', aspect='auto',
                        color_continuous_scale='Blues')
        fig.update_xaxes(side='top')
        st.plotly_chart(fig, use_container_width=True)

# ============ TAB 2: ПРОДУКТЫ ============
with tab2:
    st.title("📦 Продуктовая аналитика")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Топ-10 продуктов")
        top10 = df.groupby('Product Name')['Sales'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(x=top10.values, y=top10.index, orientation='h',
                     labels={'x': f'Продажи ({currency})', 'y': ''},
                     color=top10.values, color_continuous_scale='Blues')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💀 Топ-10 убыточных")
        loss10 = df.groupby('Product Name')['Profit'].sum().sort_values().head(10)
        fig = px.bar(x=loss10.values, y=loss10.index, orientation='h',
                     labels={'x': f'Убыток ({currency})', 'y': ''},
                     color_discrete_sequence=['#EF553B'] * 10)
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 ABC-анализ продуктов")

    col1, col2, col3 = st.columns(3)
    abc_data = df.groupby('ABC').agg(
        Products=('Product Name', 'nunique'),
        Sales=('Sales', 'sum'),
        Profit=('Profit', 'sum')
    ).reindex(['A - Золото', 'B - Середняки', 'C - Балласт'])

    with col1:
        st.metric("🥇 A - Золото", f"{abc_data.loc['A - Золото', 'Products']:,} продуктов",
                  delta=f"Прибыль: {currency}{abc_data.loc['A - Золото', 'Profit']:,.0f}")
    with col2:
        st.metric("🥈 B - Середняки", f"{abc_data.loc['B - Середняки', 'Products']:,} продуктов",
                  delta=f"Прибыль: {currency}{abc_data.loc['B - Середняки', 'Profit']:,.0f}")
    with col3:
        st.metric("🥉 C - Балласт", f"{abc_data.loc['C - Балласт', 'Products']:,} продуктов",
                  delta=f"Убыток: {currency}{abc_data.loc['C - Балласт', 'Profit']:,.0f}",
                  delta_color="inverse")

    st.subheader("Детальная таблица продуктов")
    product_table = df.groupby('Product Name').agg(
        Category=('Category', 'first'),
        Sales=('Sales', 'sum'),
        Profit=('Profit', 'sum'),
        Quantity=('Quantity', 'sum'),
        Discount=('Discount', 'mean'),
        ABC=('ABC', 'first')
    ).round(2).sort_values('Sales', ascending=False)
    st.dataframe(product_table, use_container_width=True, height=400)

# ============ TAB 3: КЛИЕНТЫ ============
with tab3:
    st.title("👥 Клиентская аналитика")

    st.subheader("📊 RFM Сегментация")
    rfm_data = df.groupby('Segment').agg(
        Customers=('Customer ID', 'nunique'),
        Sales=('Sales', 'sum'),
        Profit=('Profit', 'sum')
    ).reindex(['VIP', 'Лояльные', 'Спящие', 'Потерянные'])

    col1, col2, col3, col4 = st.columns(4)
    segment_names = ['VIP', 'Лояльные', 'Спящие', 'Потерянные']
    segment_colors = ['#FFD700', '#00CC96', '#FFA15A', '#EF553B']

    for col, seg_name, color in zip([col1, col2, col3, col4], segment_names, segment_colors):
        with col:
            if seg_name in rfm_data.index:
                val = rfm_data.loc[seg_name, 'Customers']
                sales = rfm_data.loc[seg_name, 'Sales']
                st.metric(seg_name, f"{val:,} чел.", f"Продажи: {currency}{sales:,.0f}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Распределение клиентов")
        fig = px.pie(rfm_data, values='Customers', names=rfm_data.index, hole=0.4,
                     color_discrete_sequence=segment_colors)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Продажи по сегментам")
        fig = px.bar(rfm_data, x=rfm_data.index, y='Sales', color=rfm_data.index,
                     color_discrete_sequence=segment_colors)
        st.plotly_chart(fig, use_container_width=True)

# ============ TAB 4: ГЕО ============
with tab4:
    st.title("🌍 Географическая аналитика")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏙️ Топ-10 штатов")
        state_data = df.groupby('State').agg({'Sales': 'sum', 'Profit': 'sum'}).sort_values('Sales',
                                                                                            ascending=False).head(10)
        fig = px.bar(state_data, x=state_data.index, y='Sales', color='Profit',
                     color_continuous_scale=['red', 'yellow', 'green'],
                     labels={'Sales': f'Продажи ({currency})', 'State': 'Штат'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🏘️ Топ-10 городов")
        city_data = df.groupby('City').agg({'Sales': 'sum', 'Profit': 'sum'}).sort_values('Sales',
                                                                                          ascending=False).head(10)
        fig = px.bar(city_data, x=city_data.index, y='Sales', color='Profit',
                     color_continuous_scale=['red', 'yellow', 'green'],
                     labels={'Sales': f'Продажи ({currency})', 'City': 'Город'})
        st.plotly_chart(fig, use_container_width=True)

# ============ TAB 5: ЭКСПОРТ ============
with tab5:
    st.title("💾 Экспорт данных")

    st.info("Здесь вы можете скачать отфильтрованные данные для дальнейшего анализа.")

    from io import BytesIO

    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Скачать CSV", csv, "superstore_filtered.csv", "text/csv")

    with col2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Superstore', index=False)
        excel_data = output.getvalue()
        st.download_button("📥 Скачать Excel", excel_data, "superstore_filtered.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("---")
    st.subheader("📋 Все данные")
    st.dataframe(df, use_container_width=True, height=600)