import streamlit as st
from data_loader import load_data
from visuals import plot_sales_trend, plot_comparison, plot_pie_chart

st.set_page_config(page_title="판매 데이터 분석 대시보드", layout="wide")
st.title("📊 판매 데이터 시각화 분석기")

# 사이드바: 데이터 업로드
st.sidebar.header("데이터 업로드")
uploaded_file = st.sidebar.file_uploader("CSV 파일을 선택하세요", type=['csv'])

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        st.sidebar.success("데이터 로드 성공!")
        
        # 탭 구성
        tab1, tab2, tab3 = st.tabs(["매출 추이", "실적 비교", "항목별 비중"])
        
        with tab1:
            st.subheader("1) 시간 흐름에 따른 매출 실적")
            st.plotly_chart(plot_sales_trend(df), use_container_width=True)
            
        with tab2:
            st.subheader("2) 시점 비교 (실적 vs 전월/계획)")
            # 예시를 위한 간단한 선택 UI
            col1, col2 = st.columns(2)
            val1 = col1.number_input("기준 실적", value=1000)
            val2 = col2.number_input("비교 대상(전월/계획)", value=900)
            st.plotly_chart(plot_comparison(df, val1, val2, "현재", "비교"), use_container_width=True)
            
        with tab3:
            st.subheader("3) 품목별/거래처별 비중")
            category_col = st.selectbox("분석 기준 선택", ["품목", "거래처"])
            if category_col in df.columns:
                st.plotly_chart(plot_pie_chart(df, category_col), use_container_width=True)
            else:
                st.warning(f"데이터에 '{category_col}' 컬럼이 없습니다.")
else:
    st.info("왼쪽 사이드바에서 파일을 업로드해 주세요.")
