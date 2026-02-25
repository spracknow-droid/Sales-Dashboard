import streamlit as st
import os
import pandas as pd
from data_loader import load_sqlite_db, get_table_data
from visuals import plot_sales_trend, plot_comparison, plot_pie_chart

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
                st.subheader("1) 시간 흐름에 따른 매출 실적 (판매실적 기준)")
                if not actual_df.empty:
                    st.plotly_chart(plot_sales_trend(actual_df), use_container_width=True)
                else:
                    st.warning("표시할 '판매실적' 데이터가 없습니다.")
            
            with tab2:
                st.subheader("2) 월별 실적 vs 계획 상세 비교")
                
                # 데이터에 존재하는 연월 리스트 추출 (최신순 정렬)
                available_months = sorted(df['연월'].unique(), reverse=True)
                
                if available_months:
                    # 사용자로부터 비교할 기준 월 선택 받기
                    selected_month = st.selectbox("비교할 기준 연월을 선택하세요", available_months)
                    
                    # 선택된 월에 해당하는 데이터 필터링
                    m_actual = actual_df[actual_df['연월'] == selected_month]
                    m_plan = plan_df[plan_df['연월'] == selected_month]
                    
                    # 해당 월의 합계 계산
                    actual_val = m_actual['매출액'].sum()
                    plan_val = m_plan['매출액'].sum()
                    
                    # 대시보드 상단 수치 요약 (Metric)
                    col1, col2, col3 = st.columns(3)
                    diff = actual_val - plan_val
                    
                    col1.metric(f"{selected_month} 실적", f"{actual_val:,.0f}원")
                    col2.metric(f"{selected_month} 계획", f"{plan_val:,.0f}원")
                    col3.metric("차이 (실적-계획)", f"{diff:,.0f}원", delta=float(diff))
                    
                    # 시각화 함수 호출 (선택된 월 정보 전달)
                    st.plotly_chart(plot_comparison(df, actual_val, plan_val, f"{selected_month} 실적", f"{selected_month} 계획"), use_container_width=True)
                else:
                    st.info("비교할 월별 데이터가 없습니다.")
                
            with tab3:
                st.subheader("3) 항목별 실적 비중")
                
                # 분석에서 제외할 컬럼 리스트 (기술적 항목 및 불필요한 항목)
                exclude_cols = [
                    '날짜', '매출액', '장부금액', '데이터구분', '매출일', '계획년월', '연월',
                    'WBS번호', 'SET모품목', '사업부', '부가세사업장', '세무분류', 
                    '제품군', '수출신고번호', 'L_C번호', 'B_L번호', 'No', '수익성계획전표번호',
                    '계획버전', '공장', '내수_수출', '국가코드', '고객그룹', '수량',
                    '환율','판매단가','장부단가','판매금액','송장번호','전표번호','부가세',
                    '총금액','매출번호','출고번호','수금예정일','매출유형','영업문서범주코드',
                    '헤더비고','매출처','품목','수금처','규격'
                ]
                
                # 제외 목록을 뺀 나머지 컬럼만 필터링
                category_options = [col for col in actual_df.columns if col not in exclude_cols]
                
                if category_options:
                    category_col = st.selectbox("분석 기준 컬럼 선택", category_options)
                    
                    if not actual_df.empty:
                        st.plotly_chart(plot_pie_chart(actual_df, category_col), use_container_width=True)
                    else:
                        st.warning("비중을 계산할 실적 데이터가 없습니다.")
                else:
                    st.info("분석 가능한 항목 컬럼이 없습니다.")

            # 데이터 테이블 확인
            with st.expander("표준화된 데이터 미리보기"):
                st.dataframe(df.head(100))
        
        # DB 연결 종료
        conn.close()
else:
    st.info("왼쪽 사이드바에서 SQLite DB 파일을 업로드해 주세요.")
