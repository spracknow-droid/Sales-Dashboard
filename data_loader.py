import pandas as pd
import numpy as np

def process_data(sales_file, master_file):
    """매출 파일과 마스터 파일을 병합하고 전처리합니다."""
    try:
        sales_df = pd.read_excel(sales_file)
        vendor_master = pd.read_excel(master_file, sheet_name='매출처')
        item_master = pd.read_excel(master_file, sheet_name='품목')

        if '매출일' not in sales_df.columns:
            return None, "매출 리스트 파일에 '매출일' 컬럼이 없습니다."

        # 날짜 변환
        sales_df['매출일'] = pd.to_datetime(sales_df['매출일'])

        # 병합
        merged_df = pd.merge(sales_df, vendor_master, on='매출처', how='left')
        merged_df = pd.merge(merged_df, item_master, on='품목', how='left')

        # 마지막 합계 행 등 제거
        merged_df = merged_df.iloc[:-1]

        # 삭제할 컬럼 리스트
        unnecessary_cols = [
            '제품군','송장번호','헤더비고','규격','부가세포함단가','영업담당자','영업담당자명','WBS명',
            '거래처소분류','부가세포함금액','수주헤더비고','수주라인비고','B/L번호','L/C번호','수출신고번호',
            '매출유형','매출상태','영업문서범주코드','판매단위','영업조직','사업부','수주순번','납품일정순번',
            '출고순번','비용센터','채권 전표 상태','세무분류','부가세사업장','납품처','납품처명','공장',
            '비고','수금처','수금처명','결제조건','수금예정일','고객자재코드','고객자재코드명', 'SET모품목', 
            'WBS번호','수주번호','출고일','손익전표번호','납품지시번호','품목범주','출고번호','매출순번', 
            'No','매출번호','캔수량', '캔 별 금액', '캔 별 장부금액', '품목제품군','세무구분', '대분류', 
            '중분류', '소분류', '유통경로', '수불유형', '품목계정', '수주유형', '고객그룹', '해외거래처구분',
            '매출처명_x', '매출처명_y', '품목명_x', '품목명_y'
        ]
        merged_df = merged_df.drop(columns=unnecessary_cols, errors='ignore')
        
        return merged_df, None
    except Exception as e:
        return None, str(e)
