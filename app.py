import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_loader import load_sqlite_db, get_table_data
from visuals import plot_sales_trend, plot_comparison, plot_pie_chart

# 설정 파일 임포트
import config

st.set_page_config(page_title="판매 데이터 분석 대시보드", layout="wide")
st.title("📊 판매 데이터 시각화 분석기")

# --- 사이드바: 데이터 업로드 및 설정 ---
st.sidebar.header("데이터 업로드")
uploaded_file = st.sidebar.file_uploader("SQLite DB 파일을 업로드하세요", type=['db', 'sqlite', 'sqlite3'])

if uploaded_file:
    conn, table_list, tmp_path = load_sqlite_db(uploaded_file)
    
    if table_list:
        selected_table = st.sidebar.selectbox("분석할 테이블 선택", table_list)
        df = get_table_data(conn, selected_table)
        
        if df is not None and not df.empty:
            st.sidebar.success("데이터 로드 및 표준화 완료!")
            
            # 전처리를 위한 연월 컬럼 생성
            df['연월'] = df['날짜'].dt.to_period('M').astype(str)
            
            # 데이터 분리 (실적 vs 계획)
            actual_df = df[df['데이터구분'] == '판매실적']
            plan_df = df[df['데이터구분'] == '판매계획']
            
            # --- 메인 화면 탭 구성 ---
            tab1, tab2, tab3 = st.tabs(["📈 매출 추이", "📊 실적 vs 계획 비교", "🍕 항목별 비중"])
            
            with tab1:
                st.subheader("1) 시간 흐름에 따른 매출 실적")
                
                # [추가] 상세 분석 기준 선택박스
                t1_options = ["전체 매출 추이"] + [col for col in actual_df.columns if col not in config.TAB1_EXCLUDE]
                selected_t1_cat = st.selectbox("상세 분석 기준 선택", t1_options, key="tab1_category")
                
                if not actual_df.empty:
                    if selected_t1_cat == "전체 매출 추이":
                        # 기존: 전체 실적 합계 추이
                        st.plotly_chart(plot_sales_trend(actual_df), use_container_width=True)
                    else:
                        # 신규: 선택한 항목별 누적 라인 차트
                        # 월별/항목별 매출 합계 계산
                        trend_data = actual_df.groupby(['연월', selected_t1_cat])['매출액'].sum().reset_index()
                        
                        # 가독성을 위해 상위 10개 항목만 필터링
                        top_items = actual_df.groupby(selected_t1_cat)['매출액'].sum().nlargest(10).index
                        trend_data_filtered = trend_data[trend_data[selected_t1_cat].isin(top_items)]
                        
                        fig = px.line(
                            trend_data_filtered, 
                            x='연월', 
                            y='매출액', 
                            color=selected_t1_cat,
                            markers=True,
                            title=f"상위 10개 {selected_t1_cat}별 매출 추이",
                            template='plotly_white'
                        )
                        fig.update_layout(xaxis_title="연월", yaxis_title="매출액 (원)")
                        st.plotly_chart(fig, use_container_width=True)
                        st.info(f"항목이 많을 경우 실적 상위 10개 **{selected_t1_cat}**만 표시됩니다.")
                else:
                    st.warning("표시할 '판매실적' 데이터가 없습니다.")
            
            with tab2:
                st.subheader("2) 월별 실적 vs 계획 상세 비교")
                
                col_y, col_c = st.columns(2)
                available_months = sorted(df['연월'].unique(), reverse=True)
                
                with col_y:
                    selected_month = st.selectbox("비교할 기준 연월을 선택하세요", available_months, key="compare_month_tab2")
                
                with col_c:
                    tab2_options = ["월 전체 합계"] + [col for col in actual_df.columns if col not in config.TAB2_EXCLUDE]
                    selected_category = st.selectbox("상세 분석 기준 선택", tab2_options, key="compare_category_tab2")

                m_actual = actual_df[actual_df['연월'] == selected_month]
                m_plan = plan_df[plan_df['연월'] == selected_month]

                if selected_category == "월 전체 합계":
                    actual_val = m_actual['매출액'].sum()
                    plan_val = m_plan['매출액'].sum()
                    
                    col1, col2, col3 = st.columns(3)
                    diff = actual_val - plan_val
                    col1.metric(f"{selected_month} 총 실적", f"{actual_val:,.0f}원")
                    col2.metric(f"{selected_month} 총 계획", f"{plan_val:,.0f}원")
                    col3.metric("차이", f"{diff:,.0f}원", delta=float(diff))
                    
                    st.plotly_chart(plot_comparison(df, actual_val, plan_val, f"{selected_month} 실적", f"{selected_month} 계획"), use_container_width=True)
                
                else:
                    act_grouped = m_actual.groupby(selected_category)['매출액'].sum().reset_index()
                    pln_grouped = m_plan.groupby(selected_category)['매출액'].sum().reset_index()
                    
                    comp_df = pd.merge(act_grouped, pln_grouped, on=selected_category, how='outer', suffixes=('_실적', '_계획')).fillna(0)
                    comp_df.columns = [selected_category, '실적', '계획']
                    comp_df = comp_df.sort_values('실적', ascending=False).head(15)
                    
                    fig = go.Figure(data=[
                        go.Bar(name='실적', x=comp_df[selected_category], y=comp_df['실적'], marker_color='royalblue', text=comp_df['실적'].apply(lambda x: f"{x:,.0f}"), textposition='outside'),
                        go.Bar(name='계획', x=comp_df[selected_category], y=comp_df['계획'], marker_color='lightslategray', text=comp_df['계획'].apply(lambda x: f"{x:,.0f}"), textposition='outside')
                    ])
                    fig.update_layout(barmode='group', title=f"{selected_month} {selected_category}별 실적 vs 계획 (Top 15)", template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    with st.expander("항목별 상세 수치 데이터 보기"):
                        st.dataframe(comp_df.style.format({'실적': '{:,.0f}', '계획': '{:,.0f}'}), use_container_width=True)

            with tab3:
                st.subheader("3) 항목별 실적 비중")
                col1, col2 = st.columns(2)
                
                with col1:
                    category_options_pie = [col for col in actual_df.columns if col not in config.TAB3_EXCLUDE]
                    category_col = st.selectbox("분석 기준 컬럼 선택", category_options_pie, key="pie_category")

                with col2:
                    pie_months = ["전체 누적"] + sorted(df['연월'].unique(), reverse=True)
                    selected_period = st.selectbox("분석 대상 기간 선택", pie_months, key="pie_period")

                if selected_period == "전체 누적":
                    filtered_pie_df = actual_df
                else:
                    filtered_pie_df = actual_df[actual_df['연월'] == selected_period]
                
                if not filtered_pie_df.empty:
                    st.plotly_chart(plot_pie_chart(filtered_pie_df, category_col), use_container_width=True)
                else:
                    st.warning(f"{selected_period}에 해당하는 실적 데이터가 없습니다.")

            with st.expander("표준화된 데이터 미리보기"):
                st.dataframe(df.head(100))
        
        conn.close()
else:
    st.info("왼쪽 사이드바에서 SQLite DB 파일을 업로드해 주세요.")
