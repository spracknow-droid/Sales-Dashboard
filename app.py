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
            tab1, tab2, tab4, tab3 = st.tabs(["📈 매출 추이", "📊 실적 vs 계획 비교", "🔄 실적 vs 실적 비교", "🍕 항목별 비중"])
            
            # --- 탭 1: 매출 추이 (유지) ---
            with tab1:
                st.subheader("1) 시간 흐름에 따른 매출 실적")
                t1_options = ["전체 매출 추이"] + [col for col in actual_df.columns if col not in config.TAB1_EXCLUDE]
                selected_t1_cat = st.selectbox("상세 분석 기준 선택", t1_options, key="tab1_category")
                
                if not actual_df.empty:
                    if selected_t1_cat == "전체 매출 추이":
                        st.plotly_chart(plot_sales_trend(actual_df), use_container_width=True)
                    else:
                        trend_data = actual_df.groupby(['연월', selected_t1_cat])['매출액'].sum().reset_index()
                        top_items = actual_df.groupby(selected_t1_cat)['매출액'].sum().nlargest(10).index
                        trend_data_filtered = trend_data[trend_data[selected_t1_cat].isin(top_items)]
                        
                        fig = px.line(trend_data_filtered, x='연월', y='매출액', color=selected_t1_cat, markers=True,
                                      title=f"상위 10개 {selected_t1_cat}별 매출 추이", template='plotly_white')
                        fig.update_layout(xaxis_title="연월", yaxis_title="매출액 (원)")
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("표시할 '판매실적' 데이터가 없습니다.")

            # --- 탭 2: 실적 vs 계획 비교 (탭 4 레이아웃으로 수정!) ---
            with tab2:
                st.subheader("2) 월별 실적 vs 계획 상세 비교")
                
                # 탭 4 스타일의 3열 레이아웃 적용
                col_y2, col_target2, col_c2 = st.columns(3)
                available_months = sorted(df['연월'].unique(), reverse=True)
                
                with col_y2:
                    selected_month = st.selectbox("분석 연월 선택", available_months, key="t2_month")
                with col_target2:
                    # 탭 4와의 통일감을 위해 비교 대상을 명시 (수정 불가 텍스트박스 형태)
                    st.text_input("비교 대상", value="판매실적 vs 판매계획", disabled=True, key="t2_target")
                with col_c2:
                    tab2_options = ["월 전체 합계"] + [col for col in actual_df.columns if col not in config.TAB2_EXCLUDE]
                    selected_category = st.selectbox("상세 분석 기준 선택", tab2_options, key="t2_cat")

                m_actual = actual_df[actual_df['연월'] == selected_month]
                m_plan = plan_df[plan_df['연월'] == selected_month]

                if selected_category == "월 전체 합계":
                    actual_val = m_actual['매출액'].sum()
                    plan_val = m_plan['매출액'].sum()
                    diff = actual_val - plan_val
                    pct = (diff / plan_val * 100) if plan_val != 0 else 0
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"{selected_month} 실적", f"{actual_val:,.0f}원")
                    c2.metric(f"{selected_month} 계획", f"{plan_val:,.0f}원")
                    c3.metric("차이(달성률)", f"{diff:,.0f}원", delta=f"{pct:.1f}%")
                    st.plotly_chart(plot_comparison(df, actual_val, plan_val, "실적", "계획"), use_container_width=True)
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
                    fig.update_layout(barmode='group', title=f"{selected_month} {selected_category}별 실적 vs 계획", template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("상세 수치 데이터 보기"):
                        st.dataframe(comp_df.style.format({'실적': '{:,.0f}', '계획': '{:,.0f}'}), use_container_width=True)

            # --- 탭 4: 실적 vs 실적 비교 (기존 3열 레이아웃 유지) ---
            with tab4:
                st.subheader("3) 기간별 실적 비교 (실적 vs 실적)")
                col_m1, col_m2, col_cat_4 = st.columns(3)
                act_months = sorted(actual_df['연월'].unique(), reverse=True)
                
                with col_m1:
                    base_month = st.selectbox("기준 연월 (A)", act_months, key="t4_base")
                with col_m2:
                    comp_month = st.selectbox("비교 대상 연월 (B)", act_months, index=min(1, len(act_months)-1), key="t4_comp")
                with col_cat_4:
                    t4_options = ["전체 합계"] + [col for col in actual_df.columns if col not in config.TAB4_EXCLUDE]
                    selected_t4_cat = st.selectbox("비교 기준 선택", t4_options, key="t4_cat")

                df_a = actual_df[actual_df['연월'] == base_month]
                df_b = actual_df[actual_df['연월'] == comp_month]

                if selected_t4_cat == "전체 합계":
                    val_a = df_a['매출액'].sum()
                    val_b = df_b['매출액'].sum()
                    diff = val_a - val_b
                    pct = (diff / val_b * 100) if val_b != 0 else 0
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"{base_month} 실적 (A)", f"{val_a:,.0f}원")
                    c2.metric(f"{comp_month} 실적 (B)", f"{val_b:,.0f}원")
                    c3.metric("증감액 (A-B)", f"{diff:,.0f}원", delta=f"{pct:.1f}%")
                    st.plotly_chart(plot_comparison(df, val_a, val_b, base_month, comp_month), use_container_width=True)
                else:
                    grp_a = df_a.groupby(selected_t4_cat)['매출액'].sum().reset_index()
                    grp_b = df_b.groupby(selected_t4_cat)['매출액'].sum().reset_index()
                    comp_act_df = pd.merge(grp_a, grp_b, on=selected_t4_cat, how='outer', suffixes=(f'_{base_month}', f'_{comp_month}')).fillna(0)
                    col_a, col_b = f'매출액_{base_month}', f'매출액_{comp_month}'
                    comp_act_df = comp_act_df.sort_values(col_a, ascending=False).head(15)

                    fig = go.Figure(data=[
                        go.Bar(name=base_month, x=comp_act_df[selected_t4_cat], y=comp_act_df[col_a], marker_color='indianred', text=comp_act_df[col_a].apply(lambda x: f"{x:,.0f}"), textposition='outside'),
                        go.Bar(name=comp_month, x=comp_act_df[selected_t4_cat], y=comp_act_df[col_b], marker_color='lightsalmon', text=comp_act_df[col_b].apply(lambda x: f"{x:,.0f}"), textposition='outside')
                    ])
                    fig.update_layout(barmode='group', title=f"{base_month} vs {comp_month} {selected_t4_cat}별 실적 비교", template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("증감 상세 데이터 보기"):
                        comp_act_df['증감액'] = comp_act_df[col_a] - comp_act_df[col_b]
                        st.dataframe(comp_act_df.style.format({col_a: '{:,.0f}', col_b: '{:,.0f}', '증감액': '{:,.0f}'}), use_container_width=True)

            # --- 탭 3: 항목별 비중 (유지) ---
            with tab3:
                st.subheader("4) 항목별 실적 비중")
                col1, col2 = st.columns(2)
                with col1:
                    category_options_pie = [col for col in actual_df.columns if col not in config.TAB3_EXCLUDE]
                    category_col = st.selectbox("분석 기준 컬럼 선택", category_options_pie, key="pie_category")
                with col2:
                    pie_months = ["전체 누적"] + sorted(df['연월'].unique(), reverse=True)
                    selected_period = st.selectbox("분석 대상 기간 선택", pie_months, key="pie_period")

                filtered_pie_df = actual_df if selected_period == "전체 누적" else actual_df[actual_df['연월'] == selected_period]
                if not filtered_pie_df.empty:
                    st.plotly_chart(plot_pie_chart(filtered_pie_df, category_col), use_container_width=True)
                else:
                    st.warning(f"{selected_period}에 해당하는 실적 데이터가 없습니다.")

            with st.expander("표준화된 데이터 미리보기"):
                st.dataframe(df.head(100))
        
        conn.close()
else:
    st.info("왼쪽 사이드바에서 SQLite DB 파일을 업로드해 주세요.")
