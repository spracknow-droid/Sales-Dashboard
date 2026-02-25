import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# 1) 시간 흐름에 따른 매출 추이 (거미줄 현상 해결 버전)
def plot_sales_trend(df):
    if df.empty:
        return go.Figure().update_layout(title="데이터가 없습니다.")
    
    # [핵심] 날짜 순으로 정렬하고, 같은 날짜의 매출은 합산합니다.
    df_sorted = df.sort_values('날짜')
    df_daily = df_sorted.groupby('날짜')['매출액'].sum().reset_index()
    
    fig = px.line(df_daily, x='날짜', y='매출액', 
                  title='시간별 매출 추이 (일별 합계)',
                  markers=True, # 데이터 포인트를 점으로 표시
                  template='plotly_white')
    
    fig.update_xaxes(title_text='날짜')
    fig.update_yaxes(title_text='매출액 (장부금액)')
    
    return fig

# 2) 기준 시점 비교 막대 그래프 (실적 vs 계획 등)
def plot_comparison(df, val1, val2, label1, label2):
    # 막대 그래프 색상을 다르게 하여 가독성을 높입니다.
    fig = go.Figure(data=[
        go.Bar(
            name=label1, 
            x=[label1], 
            y=[val1], 
            text=f"{val1:,.0f}", 
            textposition='outside',
            marker_color='royalblue'
        ),
        go.Bar(
            name=label2, 
            x=[label2], 
            y=[val2], 
            text=f"{val2:,.0f}", 
            textposition='outside',
            marker_color='lightslategray'
        )
    ])
    
    fig.update_layout(
        title=f'{label1} vs {label2} 비교',
        barmode='group',
        template='plotly_white',
        yaxis=dict(title='금액')
    )
    return fig

# 3) 비중 파이 그래프
def plot_pie_chart(df, column):
    if df.empty:
        return go.Figure().update_layout(title="데이터가 없습니다.")
    
    # 항목별로 매출액을 합산하여 비중을 계산합니다.
    df_pie = df.groupby(column)['매출액'].sum().reset_index()
    
    # 데이터가 너무 많으면 상위 10개만 보여주고 나머지는 '기타'로 묶는 것이 좋지만, 
    # 일단은 전체를 보여주되 가독성을 위해 텍스트 정보를 조정합니다.
    fig = px.pie(df_pie, 
                 values='매출액', 
                 names=column, 
                 title=f'{column}별 매출 비중',
                 hole=0.3) # 도넛 모양으로 만들어 세련미 추가
    
    fig.update_traces(textinfo='percent+label')
    return fig
