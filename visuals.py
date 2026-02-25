import plotly.express as px
import numpy as np

def get_monthly_sales_fig(df):
    monthly_sales = df.groupby(df['매출일'].dt.to_period('M'))['장부금액'].sum().reset_index()
    monthly_sales['매출일'] = monthly_sales['매출일'].astype(str)
    return px.bar(monthly_sales, x='매출일', y='장부금액', title="월별 매출액 변화 추이(전체)", color_discrete_sequence=['red'])

def get_item_trend_fig(df, target_items=['PCpZr', 'CpHf', 'CpZr', 'HCDS']):
    filtered_df = df[df['Subject(PPT_보고용)'].isin(target_items)].copy()
    item_monthly_sales = filtered_df.groupby([filtered_df['매출일'].dt.to_period('M'), 'Subject(PPT_보고용)'])['장부금액'].sum().reset_index()
    item_monthly_sales['매출일'] = item_monthly_sales['매출일'].astype(str)
    return px.line(item_monthly_sales, x='매출일', y='장부금액', color='Subject(PPT_보고용)', title="주요 품목 월별 매출액 변화 추이")

def get_geo_map_fig(df):
    country_iso_map = {
        '대한민국': 'KOR', '미국': 'USA', '중국': 'CHN', '일본': 'JPN', '호주': 'AUS',
        '태국': 'THA', '말레이시아': 'MYS', '인도네시아': 'IDN', '인도': 'IND', '필리핀': 'PHL',
        '베트남': 'VNM', '캐나다': 'CAN', '멕시코': 'MEX', '브라질': 'BRA', '영국': 'GBR',
        '독일': 'DEU', '프랑스': 'FRA', '이탈리아': 'ITA', '스페인': 'ESP', '러시아': 'RUS',
        '싱가포르': 'SGP', '대만': 'TWN', '벨기에': 'BEL', '핀란드': 'FIN'
    }
    country_sales = df.groupby('국가구분')['장부금액'].sum().reset_index()
    country_sales['iso_alpha'] = country_sales['국가구분'].map(country_iso_map)
    country_sales.dropna(subset=['iso_alpha'], inplace=True)
    country_sales['size_scaled'] = np.log1p(country_sales['장부금액'])
    
    fig = px.scatter_geo(country_sales, locations="iso_alpha", size="size_scaled", color="장부금액",
                         hover_name="국가구분", projection="natural earth", title="국가별 매출액 지도",
                         color_continuous_scale=px.colors.sequential.Plasma, size_max=60)
    fig.update_layout(geo={'resolution': 50})
    return fig

def get_top5_bar_fig(combined_df, category_col, base_month, color_map, title):
    base_df = combined_df[combined_df['기간'] == base_month]
    top_5_indices = base_df.groupby(category_col)['장부금액'].sum().nlargest(5).index
    
    chart_data = combined_df[combined_df[category_col].isin(top_5_indices)]
    chart_data = chart_data.groupby(['기간', category_col])['장부금액'].sum().reset_index()
    
    # 정렬 순서
    order = chart_data[chart_data['기간'] == base_month].sort_values(by='장부금액', ascending=False)[category_col]
    
    return px.bar(chart_data, x='장부금액', y=category_col, color='기간', barmode='group',
                  orientation='h', category_orders={category_col: list(order)},
                  color_discrete_map=color_map, title=title)
