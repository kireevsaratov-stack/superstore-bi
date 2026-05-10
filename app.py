# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# import requests
#
# # Настройка страницы
# st.set_page_config(
#     page_title="Superstore BI",
#     page_icon="📊",
#     layout="wide"
# )
#
#
# # ============ РАБОТА С КУРСОМ ВАЛЮТ ============
#
# @st.cache_data(ttl=86400)
# def get_exchange_rates():
#     url = "https://www.cbr-xml-daily.ru/daily_json.js"
#     response = requests.get(url)
#     current_data = response.json()
#     current_rate = current_data['Valute']['USD']['Value']
#
#     rates = {}
#     years = [2014, 2015, 2016, 2017]
#
#     for year in years:
#         for month in range(1, 13):
#             date_str = f"{year}-{month:02d}-01"
#             archive_url = f"https://www.cbr-xml-daily.ru/archive/{date_str}/daily_json.js"
#             try:
#                 resp = requests.get(archive_url)
#                 if resp.status_code == 200:
#                     data = resp.json()
#                     rate = data['Valute']['USD']['Value']
#                     rates[date_str] = rate
#             except:
#                 continue
#
#     return rates
#
#
# def convert_to_rub(df, rates):
#     df = df.copy()
#     df['Order Date'] = pd.to_datetime(df['Order Date'])
#     df['Month_Key'] = df['Order Date'].dt.strftime('%Y-%m-01')
#     df['Rate'] = df['Month_Key'].map(rates)
#     avg_rate = sum(rates.values()) / len(rates) if rates else 60
#     df['Rate'] = df['Rate'].fillna(avg_rate)
#     df['Sales'] = df['Sales'] * df['Rate']
#     df['Profit'] = df['Profit'] * df['Rate']
#     return df
#
#
# # ============ ЗАГРУЗКА ДАННЫХ ============
#
# @st.cache_data
# def load_data():
#     df = pd.read_csv('Sample - Superstore.csv', encoding='latin1')
#     df['Order Date'] = pd.to_datetime(df['Order Date'])
#     df['Year'] = df['Order Date'].dt.year
#     df['Month'] = df['Order Date'].dt.month
#     return df
#
#
# # ============ ЗАГРУЗКА КУРСОВ ============
#
# rates = get_exchange_rates()
#
# # ============ ЗАГРУЗКА ДАННЫХ (ДОЛЖНА БЫТЬ ПЕРЕД ФИЛЬТРАМИ) ============
#
# df_raw = load_data()
#
# # ============ UI ============
#
# st.sidebar.header("🎛️ Фильтры")
#
# show_rub = st.sidebar.toggle("🇷🇺 Показать в рублях", value=False)
#
# if show_rub:
#     currency_symbol = "₽"
#     st.sidebar.info("Курсы ЦБ РФ загружены (исторические, по месяцам)")
# else:
#     currency_symbol = "$"
#
# regions = ['Все'] + list(df_raw['Region'].unique())
# selected_region = st.sidebar.selectbox("Регион", regions)
#
# years = ['Все'] + sorted(df_raw['Year'].unique().tolist())
# selected_year = st.sidebar.selectbox("Год", years)
#
# # ФИЛЬТРАЦИЯ
# df_filtered = df_raw.copy()
#
# if selected_region != 'Все':
#     df_filtered = df_filtered[df_filtered['Region'] == selected_region]
# if selected_year != 'Все':
#     df_filtered = df_filtered[df_filtered['Year'] == int(selected_year)]
#
# if show_rub:
#     df_filtered = convert_to_rub(df_filtered, rates)
#
# # ============ ГЛАВНАЯ СТРАНИЦА ============
#
# st.title("📊 Superstore BI Dashboard")
# st.markdown(
#     f"*Данные: {df_filtered['Order Date'].min().strftime('%d.%m.%Y')} — {df_filtered['Order Date'].max().strftime('%d.%m.%Y')}*")
#
# col1, col2, col3, col4 = st.columns(4)
#
# total_sales = df_filtered['Sales'].sum()
# total_profit = df_filtered['Profit'].sum()
#
# with col1:
#     st.metric(f"💰 Продажи", f"{currency_symbol}{total_sales:,.0f}")
# with col2:
#     st.metric(f"📈 Прибыль", f"{currency_symbol}{total_profit:,.0f}")
# with col3:
#     avg_discount = df_filtered['Discount'].mean() * 100
#     st.metric("🏷️ Средняя скидка", f"{avg_discount:.1f}%")
# with col4:
#     customers = df_filtered['Customer ID'].nunique()
#     st.metric("👥 Клиентов", f"{customers:,}")
#
# st.markdown("---")
# col1, col2 = st.columns(2)
#
# with col1:
#     st.subheader("Продажи по категориям")
#     sales_cat = df_filtered.groupby('Category')['Sales'].sum().reset_index()
#     fig = px.pie(sales_cat, values='Sales', names='Category', hole=0.3)
#     fig.update_traces(textinfo='percent+label')
#     st.plotly_chart(fig, use_container_width=True)
#
# with col2:
#     st.subheader("Продажи по месяцам")
#     monthly = df_filtered.groupby(['Year', 'Month'])['Sales'].sum().reset_index()
#     monthly['Date'] = pd.to_datetime(monthly['Year'].astype(str) + '-' + monthly['Month'].astype(str) + '-01')
#     fig = px.line(monthly, x='Date', y='Sales', markers=True)
#     st.plotly_chart(fig, use_container_width=True)
#
# st.markdown("---")
# st.subheader("🏆 Топ-10 продуктов")
# top10 = df_filtered.groupby('Product Name')['Sales'].sum().sort_values(ascending=False).head(10)
# fig = px.bar(x=top10.values, y=top10.index, orientation='h')
# fig.update_layout(yaxis={'categoryorder': 'total ascending'})
# st.plotly_chart(fig, use_container_width=True)
#
# st.markdown("---")
# st.subheader("📋 Статистика по регионам")
# stats = df_filtered.groupby('Region').agg({'Sales': 'sum', 'Profit': 'sum', 'Order ID': 'nunique'}).round(0)
# st.dataframe(stats, use_container_width=True)
#
# st.markdown("---")
# st.caption("Курсы валют: ЦБ РФ • Данные обновляются раз в сутки")

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

    # RFM
    ref_date = df['Order Date'].max() + timedelta(days=1)
    rfm = df.groupby('Customer ID').agg({
        'Order Date': lambda x: (ref_date - x.max()).days,
        'Order ID': 'nunique',
        'Sales': 'sum'
    }).rename(columns={'Order Date': 'Recency', 'Order ID': 'Frequency', 'Sales': 'Monetary'})
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1])
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4])
    rfm['RFM_Score'] = rfm['R_Score'].astype(int) + rfm['F_Score'].astype(int) + rfm['M_Score'].astype(int)

    conditions = [
        (rfm['RFM_Score'] >= 10),
        (rfm['RFM_Score'] >= 7) & (rfm['RFM_Score'] < 10),
        (rfm['RFM_Score'] >= 4) & (rfm['RFM_Score'] < 7),
        (rfm['RFM_Score'] < 4)
    ]
    choices = ['VIP', 'Лояльные', 'Спящие', 'Потерянные']
    rfm['Segment'] = np.select(conditions, choices)

    df = df.merge(rfm[['Segment']], left_on='Customer ID', right_index=True, how='left')

    # ABC-анализ
    product_profit = df.groupby('Product Name')['Profit'].sum().sort_values(ascending=False)
    product_cumsum = product_profit.cumsum() / product_profit.sum() * 100
    conditions_abc = [
        (product_cumsum <= 50),
        (product_cumsum <= 80) & (product_cumsum > 50),
        (product_cumsum > 80)
    ]
    choices_abc = ['A - Золото', 'B - Середняки', 'C - Балласт']
    abc = pd.Series(np.select(conditions_abc, choices_abc), index=product_profit.index)
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

    segments = ['Все'] + sorted(df_raw['Segment'].dropna().unique().tolist())
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
    segments_display = [
        ('👑 VIP', 'Sales', '#FFD700'),
        ('💚 Лояльные', 'Sales', '#00CC96'),
        ('💤 Спящие', 'Sales', '#FFA15A'),
        ('👻 Потерянные', 'Sales', '#EF553B')
    ]

    for col, (name, metric, color) in zip([col1, col2, col3, col4], segments_display):
        with col:
            segment_name = name.split()[-1] if ' ' in name else name[2:]
            if segment_name in rfm_data.index:
                val = rfm_data.loc[segment_name, 'Customers']
                sales = rfm_data.loc[segment_name, 'Sales']
                st.metric(name, f"{val:,} чел.", f"Продажи: {currency}{sales:,.0f}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Распределение клиентов")
        fig = px.pie(rfm_data, values='Customers', names=rfm_data.index, hole=0.4,
                     color_discrete_sequence=['#FFD700', '#00CC96', '#FFA15A', '#EF553B'])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Продажи по сегментам")
        fig = px.bar(rfm_data, x=rfm_data.index, y='Sales', color=rfm_data.index,
                     color_discrete_sequence=['#FFD700', '#00CC96', '#FFA15A', '#EF553B'])
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

    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Скачать CSV", csv, "superstore_filtered.csv", "text/csv",
                           help="Скачать отфильтрованные данные в формате CSV")

    with col2:
        # Excel export via tmp file
        from io import BytesIO

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Superstore', index=False)
        excel_data = output.getvalue()
        st.download_button("📥 Скачать Excel", excel_data, "superstore_filtered.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           help="Скачать отфильтрованные данные в формате Excel")

    st.markdown("---")
    st.subheader("📋 Все данные")
    st.dataframe(df, use_container_width=True, height=600)