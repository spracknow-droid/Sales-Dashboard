import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# 1) 시간 흐름에 따른 매출 추이 (월별 합계 버전)
def plot_sales_trend(df):
    if df.empty:
        return go.Figure().update_layout(title="데이터가 없습니다.")
    
    # 데이터 복사 및 정렬
    df_plot = df.copy().sort_values('날짜')
    
    # 날짜에서 '연-월' 추출하여 그룹화
    df_plot['연월'] = df_plot['날짜'].dt.to_period('M').astype(str)
    df_monthly = df_plot.groupby('연월')['매출액'].sum().reset_index()
    
    # 차트 생성
    fig = px.line(df_monthly, 
                  x='연월', 
                  y='매출액', 
                  title='월별 매출 실적 추이 (판매실적 기준)',
                  markers=True, 
                  template='plotly_white')
    
    # 포인트 위에 금액 표시
    fig.update_traces(text=df_monthly['매출액'].apply(lambda x: f'{x:,.0f}'),
                      textposition="top center",
                      mode='lines+markers+text')
    
    fig.update_xaxes(title_text='연월')
    fig.update_yaxes(title_text='매출액 합계')
    
    return fig

# 2) 기준 시점 비교 막대 그래프 (실적 vs 계획 등)
def plot_comparison(df, val1, val2, label1, label2):
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
        title=f'{label1} vs {label2} 전체 합계 비교',
        barmode='group',
        template='plotly_white',
        yaxis=dict(title='금액')
    )
    return fig

# 3) 비중 파이 그래프 (5% 미만 항목 기타 처리)
def plot_pie_chart(df, column):
    if df.empty or column not in df.columns:
        return go.Figure().update_layout(title="데이터가 없거나 컬럼이 존재하지 않습니다.")
    
    # 항목별 매출 합산
    df_pie = df.groupby(column)['매출액'].sum().reset_index()
    
    # 전체 매출액 대비 비중 계산
    total_sales = df_pie['매출액'].sum()
    df_pie['percent'] = (df_pie['매출액'] / total_sales) * 100
    
    # [수정] 5% 미만 항목을 '기타(Etc)'로 통합하는 로직
    major_items = df_pie[df_pie['percent'] >= 5].copy()
    minor_items = df_pie[df_pie['percent'] < 5]
    
    if not minor_items.empty:
        etc_value = minor_items['매출액'].sum()
        etc_row = pd.DataFrame({
            column: ['기타(Etc)'], 
            '매출액': [etc_value], 
            'percent': [(etc_value / total_sales) * 100]
        })
        df_final = pd.concat([major_items, etc_row], ignore_index=True)
    else:
        df_final = major_items
    
    # 내림차순 정렬 (기타 항목 유무와 관계없이 금액순)
    df_final = df_final.sort_values('매출액', ascending=False)
    
    fig = px.pie(df_final, 
                 values='매출액', 
                 names=column, 
                 title=f'{column}별 매출 비중 (5% 미만 기타 처리)',
                 hole=0.4) 
    
    fig.update_traces(textinfo='percent+label', pull=[0.02] * len(df_final))
    fig.update_layout(showlegend=True)
    
    return fig
