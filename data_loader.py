import sqlite3
import pandas as pd
import streamlit as st
import tempfile
import os

def load_sqlite_db(uploaded_file):
    """
    업로드된 SQLite DB 파일을 임시 저장소에 쓰고 연결을 반환합니다.
    """
    try:
        # 1. 임시 파일 생성 (SQLite는 파일 경로가 필요함)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # 2. SQLite 연결
        conn = sqlite3.connect(tmp_path)
        
        # 3. 테이블 목록 가져오기
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql_query(query, conn)
        
        return conn, tables['name'].tolist(), tmp_path
        
    except Exception as e:
        st.error(f"DB 로드 중 오류 발생: {e}")
        return None, [], None

def get_table_data(conn, table_name):
    """
    선택한 테이블의 모든 데이터를 가져와 전처리합니다.
    """
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    
    # 날짜/시간 관련 컬럼 자동 변환 시도
    for col in df.columns:
        if '날짜' in col or 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='ignore')
            
    return df
