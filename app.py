import streamlit as st
import os
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
            
            # 데이터 분리 (실적 vs 계획)
            actual_df = df[df['데이터구분'] == '판매실적']
            plan_df = df[df['데이터구분'] == '판매계획']
            
            # --- 메인 화면 탭 구성 ---
            tab1, tab2, tab3 = st.tabs(["📈 매출 추이", "📊 실적 vs 계획 비교", "🍕 항목별 비중"])
            
            with tab1:
                st.subheader("1) 시간 흐름에 따른 매출 실적 (판매실적 기준)")
                if not actual_df.empty:
                    # visuals.py의 plot_sales_trend 호출
                    st.plotly_chart(plot_sales_trend(actual_df), use_container_width=True)
                else:
                    st.warning("표시할 '판매실적' 데이터가 없습니다.")
            
            with tab2:
                st.subheader("2) 실적 vs 계획 비교 (막대 그래프)")
                
                # 비교를 위한 데이터 집계 (전체 합계 기준 예시)
                total_actual = actual_df['매출액'].sum()
                total_plan = plan_df['매출액'].sum()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("총 실적 합계", f"{total_actual:,.0f}원")
                with col2:
                    st.metric("총 계획 합계", f"{total_plan:,.0f}원")
                
                # visuals.py의 plot_comparison 호출
                st.plotly_chart(plot_comparison(df, total_actual, total_plan, "판매실적", "판매계획"), use_container_width=True)
                
            with tab3:
                st.subheader("3) 항목별 실적 비중")
                # 비중은 보통 실적(actual_df)을 기준으로 분석합니다.
                category_options = [col for col in actual_df.columns if col not in ['날짜', '매출액', '장부금액', '데이터구분', '매출일', '계획년월']]
                category_col = st.selectbox("분석 기준 컬럼 선택", category_options if category_options else actual_df.columns)
                
                if not actual_df.empty:
                    st.plotly_chart(plot_pie_chart(actual_df, category_col), use_container_width=True)
                else:
                    st.warning("비중을 계산할 실적 데이터가 없습니다.")

            # 데이터 테이블 확인
            with st.expander("표준화된 데이터 미리보기"):
                st.dataframe(df.head(100))
        
        # DB 연결 종료
        conn.close()
else:
    st.info("왼쪽 사이드바에서 SQLite DB 파일을 업로드해 주세요.")
