import json
from pathlib import Path
from html import escape
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl
import seaborn as sns

# 한글 폰트 세팅 -------------------------------
def set_korean_font():
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

    if not Path(font_path).is_file():
        return fm.FontProperties()
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()

    mpl.rcParams["font.family"] = font_name
    mpl.rcParams["axes.unicode_minus"] = False

    sns.set_theme(style="whitegrid", rc={
        "font.family": font_name,
        "axes.unicode_minus": False
    })

    return fm.FontProperties(fname=font_path)

font_prop = set_korean_font()


# -----------------------------
# 1. 함수, 데이터 준비
# -----------------------------

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--data', default='review_results.csv')
args, _ = parser.parse_known_args()
csv_path = args.data

# json 변환 함수
ALLOWED_ASPECTS = {'보습','가격','향','포장'}
def safe_load_json_list(value):
    import ast
    if isinstance(value,list):
        return value
    if value is None:
        return []
    try:
        parsed = json.loads(str(value))
    except (ValueError,TypeError):
        try:
            parsed = ast.literal_eval(str(value))
        except (ValueError,SyntaxError):
            return []
    return parsed if isinstance(parsed,list) else []

def make_long_df(df):
    rows = []
    for _,row in df.iterrows():
        aspects = safe_load_json_list(row.get('aspect'))
        labels = safe_load_json_list(row.get('label'))
        evidence = safe_load_json_list(row.get('evidence'))
        if len(aspects) != len(labels) or len(set(a for a in aspects if isinstance(a,str))) != len(aspects):
            continue
        if any(not isinstance(a,str) or a not in ALLOWED_ASPECTS for a in aspects):
            continue
        if any(type(v) is not int or v not in (0,1) for v in labels):
            continue
        if row.get('status') in ('needs_review','error'):
            continue
        for i,(aspect,label) in enumerate(zip(aspects,labels)):
            rows.append({'review':row.get('review'),'aspect':aspect,'label':label,
                         'evidence':evidence[i] if len(evidence)==len(aspects) else '',
                         'processed_at':row.get('processed_at','')})
    return pd.DataFrame(rows,columns=['review','aspect','label','evidence','processed_at'])

def load_data():
    if not Path(csv_path).is_file():
        st.info('review_results.csv를 먼저 준비하세요.')
        st.stop()
    return pd.read_csv(csv_path)

df = load_data()
long_df = make_long_df(df)

# -----------------------------
# 2. Streamlit UI
# -----------------------------

st.set_page_config(
    page_title="상품 리뷰 분석 대시보드",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #f5f7fb;
}

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 5px;
}

.sub-title {
    font-size: 20px;
    color: #475569;
    margin-bottom: 40px;
}

.dashboard-box {
    background-color: white;
    padding: 38px;
    border-radius: 24px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.section-title {
    font-size: 28px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 30px;
}

.metric-card {
    background-color: white;
    padding: 26px 28px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.metric-label {
    font-size: 16px;
    color: #64748b;
}

.metric-value {
    font-size: 30px;
    font-weight: 800;
    color: #020617;
}

.chart-title {
    font-size: 22px;
    font-weight: 800;
    color: #020617;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 수치 계산
# -----------------------------
total_reviews = len(df)

positive_count = (long_df["label"] == 1).sum()
negative_count = (long_df["label"] == 0).sum()
total_labels = positive_count + negative_count

positive_ratio = round((positive_count / total_labels) * 100) if total_labels > 0 else 0
negative_ratio = round((negative_count / total_labels) * 100) if total_labels > 0 else 0

top_aspect = long_df["aspect"].value_counts().idxmax() if not long_df.empty else "-"


# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="main-title">상품 리뷰 분석 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI 기반 리뷰 감성 및 Aspect 분석 결과</div>', unsafe_allow_html=True)


# -----------------------------
# Main Box
# -----------------------------
with st.container(border=True):

    st.markdown('<div class="section-title">📈 상품 리뷰 결과 분석</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">총 리뷰 수</div>
            <div class="metric-value">{total_reviews:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">긍정 속성 비율</div>
            <div class="metric-value">{positive_ratio}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">부정 속성 비율</div>
            <div class="metric-value">{negative_ratio}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">최다 언급 Aspect</div>
            <div class="metric-value">{escape(str(top_aspect))}</div>
        </div>
        """, unsafe_allow_html=True)


    # -----------------------------
    # Charts
    # -----------------------------

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        with st.container():
            st.markdown('<div class="chart-title">속성별 감성 판정 분포</div>', unsafe_allow_html=True)

            values = [positive_count, negative_count]
            labels = ["긍정", "부정"]
            colors = ["#1557B0", "#EF4438"]

            fig, ax = plt.subplots(figsize=(7, 6))

            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")

            if sum(values) > 0:
                wedges, texts, autotexts = ax.pie(
                    values,
                    labels=labels,
                    colors=colors,
                    startangle=90,
                    counterclock=False,
                    wedgeprops={"width": 0.38, "edgecolor": "white", "linewidth": 4},
                    autopct="%1.0f%%",
                    pctdistance=0.58,
                    labeldistance=0.68,
                    textprops={"fontproperties": font_prop, "fontsize": 11}
                )

                for t in autotexts:
                    t.set_fontsize(12)

                ax.legend(
                    labels,
                    loc="lower center",
                    bbox_to_anchor=(0.5, -0.12),
                    ncol=2,
                    prop=font_prop
                )

                ax.set_aspect("equal")
                st.pyplot(fig)

            else:
                st.warning("분석된 긍정/부정 데이터가 없어서 원형 그래프를 표시할 수 없습니다.")


    with chart_col2:
        with st.container():
            st.markdown('<div class="chart-title">Aspect별 감성 분석</div>', unsafe_allow_html=True)

            aspect_sentiment = (
                long_df
                .groupby(["aspect", "label"])
                .size()
                .reset_index(name="count")
            )

            fig2, ax2 = plt.subplots(figsize=(7, 5))

            fig2.patch.set_facecolor("white")
            ax2.set_facecolor("white")

            sns.barplot(
                data=aspect_sentiment,
                x="aspect",
                y="count",
                hue="label",
                hue_order=[1, 0],
                palette={1: "#1557B0", 0: "#EF4438"},
                ax=ax2
            )

            if not aspect_sentiment.empty:
                ax2.set_ylim(0, aspect_sentiment["count"].max() + 10)

            handles, _ = ax2.get_legend_handles_labels()

            ax2.legend(
                handles,
                [{"1":"긍정","0":"부정"}.get(label,label) for label in _],
                loc="lower center",
                bbox_to_anchor=(0.5, -0.32),
                ncol=2,
                prop=font_prop
            )

            fig2.subplots_adjust(bottom=0.3)
            st.pyplot(fig2)


    st.markdown("## 💬 리뷰 분석 결과 건별 조회")

    # 검색 + 필터 영역
    col1, col2, col3 = st.columns([6, 1.5, 2])

    with col1:
        search_text = st.text_input(
            "리뷰 검색",
            placeholder="리뷰 검색...",
            label_visibility="collapsed"
        )

    with col2:
        label_filter = st.selectbox(
            "감성",
            ["전체", "긍정", "부정"],
            label_visibility="collapsed"
        )

    with col3:
        st.write("")


    # 데이터 준비
    table_df = long_df.copy()

    table_df["감성"] = table_df["label"].map({
        1: "긍정",
        0: "부정"
    })

    table_df["처리 시각 (UTC)"] = table_df["processed_at"].fillna("")


    # 검색 필터
    if search_text:
        table_df = table_df[
            table_df["review"].str.contains(search_text, case=False, na=False, regex=False)
        ]

    # 감성 필터
    if label_filter != "전체":
        table_df = table_df[
            table_df["감성"] == label_filter
        ]


    # 컬럼명 변경
    table_df = table_df.rename(columns={
        "review": "리뷰 원문",
        "aspect": "Aspect",
        "감성": "Label",
        "evidence": "Evidence"
    })


    # 필요한 컬럼만
    show_df = table_df[
        ["리뷰 원문", "Aspect", "Label", "Evidence", "처리 시각 (UTC)"]
    ]


    # 테이블 출력
    st.dataframe(
        show_df,
        use_container_width=True,
        hide_index=True
    )