import pandas as pd
import streamlit as st

def load_data(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file) # 혹은 pd.read_excel
        # 날짜 컬럼이 있다면 datetime 객체로 변환
        if '날짜' in df.columns:
            df['날짜'] = pd.to_datetime(df['날짜'])
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return None
