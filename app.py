import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go
from data_loader import load_sqlite_db, get_table_data
from visuals import plot_sales_trend, plot_comparison, plot_pie_chart

st.set_page_config(page_title="판매 데이터 분석 대시보드", layout="wide")
st.title("📊 판매 데이터 시각화 분석기")

# 분석에서 제외할 공통 컬럼 리스트
EXCLUDE_COLS = [
    '날짜', '매출액', '장부금액', '데이터구분', '매출일', '계획년월', '연월',
    'WBS번호', 'SET모품목', '사업부', '부가세사업장', '세무분류', 
    '제품군', '수출신고번호', 'L_C번호', 'B_L번호', 'No', '수익성계획전표번호',
    '계획버전', '공장', '내수_수출', '국가코드', '고객그룹', '수량',
    '환율','판매단가','장부단가','판매금액','송장번호','전표번호','부가세',
    '총금액','매출번호','출고번호','수금예정일','매출유형','영업문서범주코드',
    '헤더비고','매출처','품목','수금처','규격','매출순번','단위',
    '부가세포함단가','품목범주','영업조직','거래처소분류','영업담당자',
    '판매지역','납품처','채권_전표_상태','수주라인비고','수주헤더비고',
    '영업담당자명','수불유형','매출상태','고객자재코드','수주번호',
    '수주순번','납품일정순번','출고순번','출고일','납품지시번호',
    '부가세포함금액','버전','비용센터','WBS명','손익전표번호','비고'
]

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
                st.subheader("1) 시간 흐름에 따른 매출 실적 (판매실적 기준)")
                if not actual_df.empty:
                    st.plotly_chart(plot_sales_trend(actual_df), use_container_width=True)
                else:
                    st.warning("표시할 '판매실적' 데이터가 없습니다.")
            
            with tab2:
                st.subheader("2) 월별 실적 vs 계획 상세 비교")
                
                # 시점 및 항목 기준 선택 레이아웃
                col_y, col_c = st.columns(2)
                available_months = sorted(df['연월'].unique(), reverse=True)
                
                with col_y:
                    selected_month = st.selectbox("비교할 기준 연월을 선택하세요", available_months, key="compare_month_tab2")
                
                with col_c:
                    # '월 전체 합계' 옵션을 포함한 분석 기준 생성
                    category_options = ["월 전체 합계"] + [col for col in actual_df.columns if col not in EXCLUDE_COLS]
                    selected_category = st.selectbox("상세 분석 기준 선택", category_options, key="compare_category_tab2")

                # 데이터 필터링 (선택 월)
                m_actual = actual_df[actual_df['연월'] == selected_month]
                m_plan = plan_df[plan_df['연월'] == selected_month]

                if selected_category == "월 전체 합계":
                    # 기존 방식: 월 전체 합계 수치 및 그래프
                    actual_val = m_actual['매출액'].sum()
                    plan_val = m_plan['매출액'].sum()
                    
                    col1, col2, col3 = st.columns(3)
                    diff = actual_val - plan_val
                    col1.metric(f"{selected_month} 총 실적", f"{actual_val:,.0f}원")
                    col2.metric(f"{selected_month} 총 계획", f"{plan_val:,.0f}원")
                    col3.metric("차이", f"{diff:,.0f}원", delta=float(diff))
                    
                    st.plotly_chart(plot_comparison(df, actual_val, plan_val, f"{selected_month} 실적", f"{selected_month} 계획"), use_container_width=True)
                
                else:
                    # 신규 방식: 선택한 항목별(품목, 매출처 등) 실적 vs 계획 비교
                    act_grouped = m_actual.groupby(selected_category)['매출액'].sum().reset_index()
                    pln_grouped = m_plan.groupby(selected_category)['매출액'].sum().reset_index()
                    
                    # 데이터 통합 (Outer Join을 통해 한쪽에만 있는 데이터도 포함)
                    comp_df = pd.merge(act_grouped, pln_grouped, on=selected_category, how='outer', suffixes=('_실적', '_계획')).fillna(0)
                    comp_df.columns = [selected_category, '실적', '계획']
                    comp_df = comp_df.sort_values('실적', ascending=False).head(15) # 가독성을 위해 상위 15개만 표시
                    
                    # 시각화 차트 생성
                    fig = go.Figure(data=[
                        go.Bar(name='실적', x=comp_df[selected_category], y=comp_df['실적'], marker_color='royalblue', text=comp_df['실적'].apply(lambda x: f"{x:,.0f}"), textposition='outside'),
                        go.Bar(name='계획', x=comp_df[selected_category], y=comp_df['계획'], marker_color='lightslategray', text=comp_df['계획'].apply(lambda x: f"{x:,.0f}"), textposition='outside')
                    ])
                    fig.update_layout(barmode='group', title=f"{selected_month} {selected_category}별 실적 vs 계획 (Top 15)", template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 상세 데이터 테이블
                    with st.expander("항목별 상세 수치 데이터 보기"):
                        st.dataframe(comp_df.style.format({'실적': '{:,.0f}', '계획': '{:,.0f}'}), use_container_width=True)

            with tab3:
                st.subheader("3) 항목별 실적 비중")
                col1, col2 = st.columns(2)
                
                with col1:
                    category_options_pie = [col for col in actual_df.columns if col not in EXCLUDE_COLS]
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
