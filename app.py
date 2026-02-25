import streamlit as st
import os
# 수정된 data_loader에서 함수들을 가져옵니다.
from data_loader import load_sqlite_db, get_table_data
from visuals import plot_sales_trend, plot_comparison, plot_pie_chart

st.set_page_config(page_title="판매 데이터 분석 대시보드", layout="wide")
st.title("📊 판매 데이터 시각화 분석기 (SQLite)")

# --- 사이드바: 데이터 업로드 및 테이블 선택 ---
st.sidebar.header("데이터 업로드")
# SQLite 확장자 지원
uploaded_file = st.sidebar.file_uploader("SQLite DB 파일을 업로드하세요", type=['db', 'sqlite', 'sqlite3'])

if uploaded_file:
    # 1. DB 연결 및 테이블 목록 가져오기
    conn, table_list, tmp_path = load_sqlite_db(uploaded_file)
    
    if table_list:
        st.sidebar.success("DB 로드 성공!")
        # 2. 분석할 테이블 선택
        selected_table = st.sidebar.selectbox("분석할 테이블을 선택하세요", table_list)
        
        # 3. 데이터 로드 (DataFrame 변환)
        df = get_table_data(conn, selected_table)
        
        # --- 메인 화면: 데이터 시각화 ---
        if df is not None and not df.empty:
            # 탭 구성
            tab1, tab2, tab3 = st.tabs(["📈 매출 추이", "📊 실적 비교", "🍕 항목별 비중"])
            
            with tab1:
                st.subheader("1) 시간 흐름에 따른 매출 실적")
                # 날짜 컬럼 자동 감지 로직이 data_loader에 있지만, 여기서 확인
                date_cols = [col for col in df.columns if '날짜' in col or 'date' in col.lower()]
                if date_cols and '매출액' in df.columns:
                    st.plotly_chart(plot_sales_trend(df), use_container_width=True)
                else:
                    st.warning("데이터에 '날짜'와 '매출액' 컬럼이 필요합니다.")
                
            with tab2:
                st.subheader("2) 시점 비교 (실적 vs 전월/계획)")
                col1, col2 = st.columns(2)
                # 실제 데이터에서 값을 추출하거나 사용자가 입력
                val1 = col1.number_input("기준 실적", value=float(df['매출액'].sum()) if '매출액' in df.columns else 1000.0)
                val2 = col2.number_input("비교 대상(전월/계획)", value=val1 * 0.9) # 예시로 90% 설정
                st.plotly_chart(plot_comparison(df, val1, val2, "현재", "비교"), use_container_width=True)
                
            with tab3:
                st.subheader("3) 품목별/거래처별 비중")
                # DB 테이블의 실제 컬럼명 중 선택하게 함
                available_cols = df.columns.tolist()
                category_col = st.selectbox("비중을 확인할 컬럼 선택", available_cols)
                
                if '매출액' in df.columns:
                    st.plotly_chart(plot_pie_chart(df, category_col), use_container_width=True)
                else:
                    st.error("비중을 계산할 '매출액' 컬럼이 데이터에 없습니다.")
            
            # (옵션) 데이터 미리보기
            with st.expander("데이터 원본 보기"):
                st.dataframe(df)
        else:
            st.warning("선택한 테이블에 데이터가 없습니다.")
            
        # 작업 종료 후 DB 연결 닫기 (Streamlit 세션 특성상 필요시)
        conn.close()
        # 임시 파일 삭제 (선택 사항)
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass

else:
    st.info("왼쪽 사이드바에서 SQLite DB(.db, .sqlite) 파일을 업로드해 주세요.")
