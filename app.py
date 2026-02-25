import streamlit as st
import pandas as pd
import io
import data_loader
import visuals

# 1. 페이지 초기 설정
st.set_page_config(page_title="매출 분석 대시보드", layout="wide")
st.title("📊 매출 분석 대시보드")

if 'current_df' not in st.session_state:
    st.session_state.current_df = pd.DataFrame()

# 2. 사이드바 구성
with st.sidebar:
    st.header("파일 업로드")
    sales_file = st.file_uploader("1. 매출 리스트 파일 (xlsx)", type=["xlsx"])
    master_file = st.file_uploader("2. 마스터 파일 (xlsx)", type=["xlsx"])

    if sales_file and master_file:
        df, error = data_loader.process_data(sales_file, master_file)
        if error:
            st.error(f"오류: {error}")
        else:
            st.session_state.current_df = df
            st.success("데이터 병합 완료!")

df = st.session_state.current_df

# 3. 메인 분석 영역
if not df.empty:
    unique_dates = sorted(df['매출일'].dt.to_period('M').unique())
    date_options = [str(d) for d in unique_dates]

    with st.sidebar:
        selected_base = st.selectbox("기준 연월 선택", options=date_options)
        selected_comp = st.selectbox("비교 연월 선택", options=date_options)
        
        # 다운로드 버튼
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        st.download_button("최종 데이터 다운로드", data=output.getvalue(), 
                           file_name="분석데이터.xlsx", mime="application/vnd.ms-excel")

    col1, col2, col3 = st.columns([1, 2, 2])

    # --- Column 1: 주요 지표 ---
    with col1:
        st.header("주요 지표")
        base_val = df[df['매출일'].dt.to_period('M') == selected_base]['장부금액'].sum()
        comp_val = df[df['매출일'].dt.to_period('M') == selected_comp]['장부금액'].sum()
        
        st.metric(f"{selected_base} 매출액", f"{base_val/1e6:,.0f}M", f"{(base_val-comp_val)/1e6:,.0f}M")
        
        # USD 지표
        base_usd = df[(df['매출일'].dt.to_period('M') == selected_base) & (df['거래통화'] == 'USD')]['판매금액'].sum()
        st.metric(f"{selected_base} USD 매출", f"${base_usd/1e6:,.2f}M")

    # --- Column 2: 추이 및 지도 ---
    with col2:
        st.plotly_chart(visuals.get_monthly_sales_fig(df), use_container_width=True)
        st.plotly_chart(visuals.get_item_trend_fig(df), use_container_width=True)
        st.plotly_chart(visuals.get_geo_map_fig(df), use_container_width=True)

    # --- Column 3: Top 5 및 비중 ---
    with col3:
        st.header("상세 분석")
        base_df = df[df['매출일'].dt.to_period('M') == selected_base].copy()
        base_df['기간'] = selected_base
        comp_df = df[df['매출일'].dt.to_period('M') == selected_comp].copy()
        comp_df['기간'] = selected_comp
        combined = pd.concat([base_df, comp_df])
        
        color_map = {selected_base: '#004488', selected_comp: '#C8C8C8'}
        
        st.plotly_chart(visuals.get_top5_bar_fig(combined, '거래처구분(PPT_보고용)', selected_base, color_map, "거래처 Top 5"), use_container_width=True)
        st.plotly_chart(visuals.get_top5_bar_fig(combined, 'Subject(PPT_보고용)', selected_base, color_map, "품목 Top 5"), use_container_width=True)
        
        # 국가별 비중 파이차트
        country_pie = px.pie(base_df.groupby('국가구분')['장부금액'].sum().reset_index(), 
                             values='장부금액', names='국가구분', title=f"{selected_base} 국가비중", hole=0.5)
    st.plotly_chart(country_pie, use_container_width=True)

else:
    st.info("파일을 업로드하면 분석이 시작됩니다.")
