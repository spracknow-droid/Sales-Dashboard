import plotly.express as px
import plotly.graph_objects as go

# 1) 시간 흐름에 따른 매출 추이
def plot_sales_trend(df):
    fig = px.line(df, x='날짜', y='매출액', title='시간별 매출 추이')
    return fig

# 2) 기준 시점 비교 막대 그래프
def plot_comparison(df, period1, period2, label1, label2):
    # 실제 데이터에서는 필터링 로직이 추가되어야 함
    fig = go.Figure(data=[
        go.Bar(name=label1, x=['실적'], y=[period1]),
        go.Bar(name=label2, x=['비교값'], y=[period2])
    ])
    fig.update_layout(title='기준 시점 비교', barmode='group')
    return fig

# 3) 비중 파이 그래프
def plot_pie_chart(df, column):
    fig = px.pie(df, values='매출액', names=column, title=f'{column}별 매출 비중')
    return fig
