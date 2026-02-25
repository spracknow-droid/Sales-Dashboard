import sqlite3
import pandas as pd
import streamlit as st
import tempfile
import os

def load_sqlite_db(uploaded_file):
    """
    업로드된 SQLite DB 파일을 임시 파일로 저장하고 연결을 생성합니다.
    """
    try:
        # 1. 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # 2. SQLite 연결
        conn = sqlite3.connect(tmp_path)
        
        # 3. DB 내의 모든 테이블 목록 가져오기
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql_query(query, conn)
        
        return conn, tables['name'].tolist(), tmp_path
        
    except Exception as e:
        st.error(f"DB를 불러오는 중 오류가 발생했습니다: {e}")
        return None, [], None

def get_table_data(conn, table_name):
    """
    선택된 테이블의 데이터를 가져와서 사용자의 요구사항에 맞게 컬럼을 표준화합니다.
    """
    try:
        # 전체 데이터 로드
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        if df.empty:
            return df

        # --- 요구사항 반영: 컬럼 표준화 로직 ---
        
        # 1. 매출액 표준화: '장부금액'을 공통 '매출액' 컬럼으로 복사
        if '장부금액' in df.columns:
            df['매출액'] = pd.to_numeric(df['장부금액'], errors='coerce').fillna(0)
        
        # 2. 날짜 표준화: '데이터구분'에 따라 '매출일' 또는 '계획년월'을 '날짜' 컬럼으로 통합
        if '데이터구분' in df.columns:
            def map_date(row):
                if row['데이터구분'] == '판매실적':
                    return row.get('매출일')
                elif row['데이터구분'] == '판매계획':
                    return row.get('계획년월')
                return None

            df['날짜'] = df.apply(map_date, axis=1)
            
            # 날짜 형식 변환 (문자열 -> datetime)
            df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        
        return df

    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
        return None
