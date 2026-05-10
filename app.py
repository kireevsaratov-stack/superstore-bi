import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import numpy as np

# ============ НАСТРОЙКИ ============
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

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

    # ABC анализ
    try:
        product_profit = df.groupby('Product Name')['Profit'].sum().sort_values(ascending=False)
        product_cumsum = product_profit.cumsum() / product_profit.sum() * 100
        abc = pd.cut(product_cumsum, bins=[0, 50, 80, 100], labels=['A - Золото', 'B - Середняки', 'C - Балласт'])
        df['ABC'] = df['Product Name'].map(abc)
    except:
        df['ABC'] = 'Без категории'

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

    st.subheader("🎨 Оформление")
    dark_mode = st.checkbox("🌙 Тёмная тема")
    if dark_mode:
        st.session_state.dark_mode = True
        plotly_template = 'plotly_dark'
    else:
        st.session_state.dark_mode = False
        plotly_template = 'plotly'

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
                     color_discrete_sequence=px.colors.qualitative.Pastel,
                     template=plotly_template)
        fig.update_traces(textinfo='percent+label+value',
                          texttemplate='%{label}<br>%{percent:.1%}<br>' + currency + '%{value:,.0f}',
                          textfont=dict(size=13))
        fig.update_layout(showlegend=True, legend=dict(orientation='h', y=-0.1))
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Продажи и Прибыль по месяцам")
        monthly = df.groupby([df['Order Date'].dt.to_period('M')]).agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
        monthly['Order Date'] = monthly['Order Date'].astype(str)
        fig = go.Figure(layout=dict(template=plotly_template))
        fig.add_trace(go.Scatter(x=monthly['Order Date'], y=monthly['Sales'], name='Продажи',
                                 fill='tozeroy', line=dict(color='#636EFA'),
                                 hovertemplate=currency + '%{y:,.0f}<extra>Продажи</extra>'))
        fig.add_trace(go.Scatter(x=monthly['Order Date'], y=monthly['Profit'], name='Прибыль',
                                 fill='tozeroy', line=dict(color='#00CC96'),
                                 hovertemplate=currency + '%{y:,.0f}<extra>Прибыль</extra>'))
        fig.update_layout(hovermode='x unified',
                          xaxis=dict(tickformat='%Y-%m', dtick='M3'))
        st.plotly_chart(fig, width='stretch')

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔥 Скидки vs Прибыль")
        df['Discount Level'] = pd.cut(df['Discount'], bins=[-0.01, 0.05, 0.2, 0.5, 1],
                                      labels=['Без скидки', '0-5%', '5-20%', '20%+'])
        disc_profit = df.groupby('Discount Level', observed=False)['Profit'].sum().reset_index()
        colors = ['#00CC96' if x > 0 else '#EF553B' for x in disc_profit['Profit']]
        fig = px.bar(disc_profit, x='Discount Level', y='Profit', color='Discount Level',
                     color_discrete_sequence=colors, text_auto='.2s',
                     template=plotly_template)
        fig.update_traces(texttemplate=currency + '%{value:,.0f}', textfont=dict(size=13), textposition='outside')
        fig.update_layout(showlegend=False,
                          yaxis=dict(title=f'Прибыль ({currency})',
                                     range=[disc_profit['Profit'].min() * 1.1, disc_profit['Profit'].max() * 1.1]))
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("📈 Сезонность продаж")
        heatmap_data = df.pivot_table(values='Sales', index='Month', columns='Year', aggfunc='sum')
        months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                  'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        heatmap_data.index = months[:len(heatmap_data)]

        fig = px.imshow(heatmap_data, aspect='auto', color_continuous_scale='Blues',
                        template=plotly_template)
        fig.update_xaxes(side='top', title='Год', tickformat='d', dtick=1)
        fig.update_yaxes(title='Месяц')
        fig.update_layout(coloraxis_colorbar=dict(title=f'Продажи ({currency})'))
        fig.update_traces(text=[[f"{currency}{val:,.0f}" for val in row] for row in heatmap_data.values],
                          texttemplate="%{text}", textfont=dict(size=11))
        st.plotly_chart(fig, width='stretch')

# ============ TAB 2: ПРОДУКТЫ ============
with tab2:
    st.title("📦 Продуктовая аналитика")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Топ-10 продуктов")
        top10 = df.groupby('Product Name')['Sales'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(x=top10.values, y=top10.index, orientation='h',
                     labels={'x': f'Продажи ({currency})', 'y': ''},
                     text_auto='.2s', color=top10.values, color_continuous_scale='Blues',
                     template=plotly_template)
        fig.update_traces(texttemplate=currency + '%{value:,.0f}', textfont=dict(size=12), textposition='outside')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False,
                          xaxis=dict(range=[0, top10.values.max() * 1.1]))
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("💀 Топ-10 убыточных")
        loss10 = df.groupby('Product Name')['Profit'].sum().sort_values().head(10)
        fig = px.bar(x=loss10.values, y=loss10.index, orientation='h',
                     labels={'x': f'Убыток ({currency})', 'y': ''},
                     text_auto='.2s', color_discrete_sequence=['#EF553B'] * 10,
                     template=plotly_template)
        fig.update_traces(texttemplate=currency + '%{value:,.0f}', textfont=dict(size=12), textposition='outside')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False,
                          xaxis=dict(range=[loss10.values.min() * 1.1, 0]))
        st.plotly_chart(fig, width='stretch')

    st.markdown("---")
    st.subheader("📊 ABC-анализ продуктов")

    col1, col2, col3 = st.columns(3)
    abc_data = df.groupby('ABC').agg(
        Products=('Product Name', 'nunique'),
        Sales=('Sales', 'sum'),
        Profit=('Profit', 'sum')
    )

    for seg in ['A - Золото', 'B - Середняки', 'C - Балласт']:
        if seg not in abc_data.index:
            abc_data.loc[seg] = [0, 0, 0]

    abc_data = abc_data.reindex(['A - Золото', 'B - Середняки', 'C - Балласт'])

    with col1:
        val = abc_data.loc['A - Золото', 'Products']
        profit_val = abc_data.loc['A - Золото', 'Profit']
        st.metric("🥇 A - Золото", f"{val:,} продуктов",
                  delta=f"Прибыль: {currency}{profit_val:,.0f}")
    with col2:
        val = abc_data.loc['B - Середняки', 'Products']
        profit_val = abc_data.loc['B - Середняки', 'Profit']
        st.metric("🥈 B - Середняки", f"{val:,} продуктов",
                  delta=f"Прибыль: {currency}{profit_val:,.0f}")
    with col3:
        val = abc_data.loc['C - Балласт', 'Products']
        profit_val = abc_data.loc['C - Балласт', 'Profit']
        st.metric("🥉 C - Балласт", f"{val:,} продуктов",
                  delta=f"Убыток: {currency}{profit_val:,.0f}",
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
    st.dataframe(product_table, use_container_width=True, height=400,
                 column_config={
                     'Sales': st.column_config.NumberColumn('Продажи', format=f'{currency}%.0f'),
                     'Profit': st.column_config.NumberColumn('Прибыль', format=f'{currency}%.0f'),
                 })

# ============ TAB 3: КЛИЕНТЫ ============
with tab3:
    st.title("👥 Клиентская аналитика")

    customer_stats = df.groupby('Customer ID').agg(
        Customer_Name=('Customer Name', 'first'),
        Total_Sales=('Sales', 'sum'),
        Total_Profit=('Profit', 'sum'),
        Orders=('Order ID', 'nunique'),
        Avg_Check=('Sales', 'mean'),
        Last_Order=('Order Date', 'max'),
    ).reset_index()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Всего клиентов", f"{len(customer_stats):,}")
    with col2:
        st.metric("💰 Средний чек", f"{currency}{customer_stats['Avg_Check'].mean():,.0f}")
    with col3:
        st.metric("📦 Среднее заказов", f"{customer_stats['Orders'].mean():.1f}")
    with col4:
        st.metric("💎 Средние продажи на клиента", f"{currency}{customer_stats['Total_Sales'].mean():,.0f}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Топ-10 клиентов по продажам")
        top_customers = customer_stats.nlargest(10, 'Total_Sales')[['Customer_Name', 'Total_Sales', 'Orders']]
        fig = px.bar(top_customers, x='Total_Sales', y='Customer_Name', orientation='h',
                     labels={'Total_Sales': f'Продажи ({currency})', 'Customer_Name': 'Клиент'},
                     text_auto='.2s', color='Total_Sales', color_continuous_scale='Blues',
                     template=plotly_template)
        fig.update_traces(texttemplate=currency + '%{value:,.0f}', textfont=dict(size=12), textposition='outside')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False,
                          xaxis=dict(range=[0, top_customers['Total_Sales'].max() * 1.1]))
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("📊 Распределение клиентов по заказам")
        orders_dist = customer_stats['Orders'].value_counts().sort_index()
        fig = px.bar(x=orders_dist.index, y=orders_dist.values,
                     labels={'x': 'Количество заказов', 'y': 'Количество клиентов'},
                     color_discrete_sequence=['#636EFA'],
                     template=plotly_template)
        fig.update_traces(texttemplate='%{value:,}', textfont=dict(size=12), textposition='outside')
        fig.update_layout(yaxis=dict(range=[0, orders_dist.values.max() * 1.1]))
        st.plotly_chart(fig, width='stretch')

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💎 Клиенты с максимальной прибылью")
        top_profit = customer_stats.nlargest(10, 'Total_Profit')[['Customer_Name', 'Total_Profit', 'Total_Sales']]
        fig = px.bar(top_profit, x='Total_Profit', y='Customer_Name', orientation='h',
                     labels={'Total_Profit': f'Прибыль ({currency})', 'Customer_Name': 'Клиент'},
                     text_auto='.2s', color='Total_Profit', color_continuous_scale='Greens',
                     template=plotly_template)
        fig.update_traces(texttemplate=currency + '%{value:,.0f}', textfont=dict(size=12), textposition='outside')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False,
                          xaxis=dict(range=[0, top_profit['Total_Profit'].max() * 1.1]))
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("📅 Активность клиентов (дни с последнего заказа)")
        ref_date = df['Order Date'].max()
        customer_stats['Days_Since_Last'] = (ref_date - customer_stats['Last_Order']).dt.days
        fig = px.histogram(customer_stats, x='Days_Since_Last', nbins=30,
                           labels={'Days_Since_Last': 'Дней с последнего заказа', 'count': 'Клиентов'},
                           color_discrete_sequence=['#AB63FA'],
                           template=plotly_template)
        st.plotly_chart(fig, width='stretch')

    st.markdown("---")
    st.subheader("📋 Все клиенты")
    st.dataframe(customer_stats.sort_values('Total_Sales', ascending=False),
                 use_container_width=True, height=400,
                 column_config={
                     'Total_Sales': st.column_config.NumberColumn('Продажи', format=f'{currency}%.0f'),
                     'Total_Profit': st.column_config.NumberColumn('Прибыль', format=f'{currency}%.0f'),
                     'Avg_Check': st.column_config.NumberColumn('Средний чек', format=f'{currency}%.0f'),
                 })

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
                     text_auto='.2s',
                     labels={'Sales': f'Продажи ({currency})', 'State': 'Штат'},
                     template=plotly_template)
        fig.update_traces(texttemplate=currency + '%{value:,.0f}', textfont=dict(size=11), textposition='outside')
        fig.update_layout(coloraxis_colorbar=dict(title='Прибыль'),
                          yaxis=dict(range=[0, state_data['Sales'].max() * 1.1]))
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("🏘️ Топ-10 городов")
        city_data = df.groupby('City').agg({'Sales': 'sum', 'Profit': 'sum'}).sort_values('Sales',
                                                                                          ascending=False).head(10)
        fig = px.bar(city_data, x=city_data.index, y='Sales', color='Profit',
                     color_continuous_scale=['red', 'yellow', 'green'],
                     text_auto='.2s',
                     labels={'Sales': f'Продажи ({currency})', 'City': 'Город'},
                     template=plotly_template)
        fig.update_traces(texttemplate=currency + '%{value:,.0f}', textfont=dict(size=11), textposition='outside')
        fig.update_layout(coloraxis_colorbar=dict(title='Прибыль'),
                          yaxis=dict(range=[0, city_data['Sales'].max() * 1.1]))
        st.plotly_chart(fig, width='stretch')

# ============ TAB 5: ЭКСПОРТ ============
with tab5:
    st.title("💾 Экспорт данных")

    st.info("Скачайте отфильтрованные данные для дальнейшего анализа.")

    from io import BytesIO

    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Скачать CSV", csv, "superstore_filtered.csv", "text/csv")

    with col2:
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Superstore', index=False)
            excel_data = output.getvalue()
            st.download_button("📥 Скачать Excel", excel_data, "superstore_filtered.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except:
            st.warning("Excel экспорт временно недоступен. Скачайте CSV.")

    st.markdown("---")
    st.subheader("📋 Все данные")
    st.dataframe(df, use_container_width=True, height=600,
                 column_config={
                     'Sales': st.column_config.NumberColumn('Продажи', format=f'{currency}%.2f'),
                     'Profit': st.column_config.NumberColumn('Прибыль', format=f'{currency}%.2f'),
                 })