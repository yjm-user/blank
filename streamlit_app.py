#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="Titanic Passenger Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

/* ✅ Metric 카드 배경을 흰색으로 변경 */
[data-testid="stMetric"] {
    background-color: #ffffff;
    text-align: center;
    padding: 15px 0;
    border: 1px solid #E6E6E6;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)


#######################
# Load data
df_reshaped = pd.read_csv('titanic.csv') ## 분석 데이터 넣기


#######################
# Sidebar
with st.sidebar:
    st.title("Titanic Passenger Dashboard")
    st.caption("필터를 선택하면 모든 차트가 동기화됩니다.")

    st.markdown("---")

    # --- 기본 값/옵션 준비
    df = df_reshaped.copy()

    # 숫자 범위(결측 제외)
    age_min = int(df["Age"].dropna().min()) if df["Age"].notna().any() else 0
    age_max = int(df["Age"].dropna().max()) if df["Age"].notna().any() else 80
    fare_min = float(df["Fare"].dropna().min()) if df["Fare"].notna().any() else 0.0
    fare_max = float(df["Fare"].dropna().max()) if df["Fare"].notna().any() else 600.0

    # 필터 위젯
    sex_sel = st.multiselect(
        "성별 (Sex)",
        options=sorted(df["Sex"].dropna().unique().tolist()),
        default=sorted(df["Sex"].dropna().unique().tolist()),
    )

    pclass_sel = st.multiselect(
        "탑승 클래스 (Pclass)",
        options=sorted(df["Pclass"].dropna().unique().tolist()),
        default=sorted(df["Pclass"].dropna().unique().tolist()),
        help="1=1등석, 2=2등석, 3=3등석",
    )

    embarked_sel = st.multiselect(
        "출항지 (Embarked)",
        options=sorted(df["Embarked"].dropna().unique().tolist()),
        default=sorted(df["Embarked"].dropna().unique().tolist()),
        help="C=Cherbourg, Q=Queenstown, S=Southampton",
    )

    age_range = st.slider(
        "연령대 (Age)",
        min_value=age_min,
        max_value=age_max,
        value=(age_min, age_max),
        step=1,
    )
    include_age_nan = st.checkbox("나이 결측치 포함", value=True)

    fare_range = st.slider(
        "운임 범위 (Fare)",
        min_value=float(fare_min),
        max_value=float(fare_max),
        value=(float(fare_min), float(min(fare_max, 150.0))),
        step=0.5,
    )
    include_fare_nan = st.checkbox("운임 결측치 포함", value=True)

    st.markdown("---")
    reset = st.button("필터 초기화")

    # --- 필터 적용
    if reset:
        st.session_state.clear()
        st.rerun()

    filt = pd.Series([True] * len(df))

    if sex_sel:
        filt &= df["Sex"].isin(sex_sel)

    if pclass_sel:
        filt &= df["Pclass"].isin(pclass_sel)

    if embarked_sel:
        filt &= df["Embarked"].isin(embarked_sel)

    # Age 필터 (결측 포함 여부)
    age_ok = df["Age"].between(age_range[0], age_range[1])
    if include_age_nan:
        age_ok = age_ok | df["Age"].isna()
    filt &= age_ok

    # Fare 필터 (결측 포함 여부)
    fare_ok = df["Fare"].between(fare_range[0], fare_range[1])
    if include_fare_nan:
        fare_ok = fare_ok | df["Fare"].isna()
    filt &= fare_ok

    filtered_df = df.loc[filt].copy()

    # 다운스트림에서 사용하도록 저장
    st.session_state["filtered_df"] = filtered_df
    st.caption(f"현재 필터링된 승객 수: **{len(filtered_df):,} 명**")



#######################
# Plots



#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.subheader("생존 요약 (Summary)")

    df = st.session_state["filtered_df"]

    # --- 전체 생존자/사망자 수
    total_passengers = len(df)
    total_survived = df["Survived"].sum()
    total_dead = total_passengers - total_survived
    survival_rate = (total_survived / total_passengers * 100) if total_passengers > 0 else 0

    st.metric(
        label="총 승객 수",
        value=f"{total_passengers:,}"
    )
    st.metric(
        label="생존자 수",
        value=f"{total_survived:,}",
        delta=f"{survival_rate:.1f}% 생존률",
        delta_color="normal"
    )
    st.metric(
        label="사망자 수",
        value=f"{total_dead:,}"
    )

    st.markdown("---")

    # --- 탑승 클래스별 생존률
    st.caption("탑승 클래스별 생존률 (%)")
    pclass_survival = (
        df.groupby("Pclass")["Survived"]
        .mean()
        .reset_index()
        .sort_values("Pclass")
    )
    pclass_survival["Survived"] *= 100

    chart = alt.Chart(pclass_survival).mark_bar().encode(
        x=alt.X("Pclass:O", title="탑승 클래스"),
        y=alt.Y("Survived:Q", title="생존률 (%)"),
        tooltip=["Pclass", alt.Tooltip("Survived", format=".1f")]
    ).properties(
        height=250
    )
    st.altair_chart(chart, use_container_width=True)



with col[1]:
    st.subheader("메인 시각화")

    df = st.session_state["filtered_df"]

    if len(df) == 0:
        st.warning("필터 결과가 없습니다. 사이드바에서 조건을 완화해 주세요.")
    else:
        # -----------------------------
        # 1) 연령 × 클래스별 생존률 히트맵
        # -----------------------------
        st.markdown("#### 연령 × 탑승 클래스별 생존률 (Heatmap)")
        heatmap = (
            alt.Chart(df)
            .mark_rect()
            .encode(
                x=alt.X("Pclass:O", title="탑승 클래스"),
                y=alt.Y("Age:Q", bin=alt.Bin(step=5), title="연령대 (5세 구간)"),
                color=alt.Color("mean(Survived):Q", title="생존률", scale=alt.Scale(scheme="blues")),
                tooltip=[
                    alt.Tooltip("Pclass:O", title="클래스"),
                    alt.Tooltip("Age:Q", bin=alt.Bin(step=5), title="연령대"),
                    alt.Tooltip("mean(Survived):Q", title="평균 생존률", format=".1%"),
                    alt.Tooltip("count():Q", title="표본 수"),
                ],
            )
            .properties(height=360)
        )
        st.altair_chart(heatmap, use_container_width=True)

        st.markdown("---")

        # -----------------------------
        # 2) 운임(Fare) 분포: 생존/사망 비교 (Box Plot)
        # -----------------------------
        st.markdown("#### 운임 분포와 생존 여부 (Box Plot)")
        boxfig = px.box(
            df,
            x="Survived",
            y="Fare",
            points="outliers",
            labels={"Survived": "생존 여부 (0=사망, 1=생존)", "Fare": "운임"},
        )
        boxfig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(boxfig, use_container_width=True)

        st.markdown("---")

        # -----------------------------
        # 3) 연령대별 생존률 곡선 (라인)
        # -----------------------------
        st.markdown("#### 연령대별 생존률 (Line)")
        tmp = df.dropna(subset=["Age"]).copy()
        bins = list(range(int(tmp["Age"].min()) // 5 * 5, int(tmp["Age"].max()) + 6, 5))
        tmp["age_bin"] = pd.cut(tmp["Age"], bins=bins, include_lowest=True)
        rate_by_age = (
            tmp.groupby("age_bin")["Survived"].mean().reset_index()
        )
        rate_by_age["age_mid"] = rate_by_age["age_bin"].apply(lambda iv: iv.mid if hasattr(iv, "mid") else None)
        line = (
            alt.Chart(rate_by_age)
            .mark_line(point=True)
            .encode(
                x=alt.X("age_mid:Q", title="연령(구간 중심)"),
                y=alt.Y("Survived:Q", title="생존률"),
                tooltip=[
                    alt.Tooltip("age_bin:N", title="연령 구간"),
                    alt.Tooltip("Survived:Q", title="생존률", format=".1%"),
                ],
            )
            .properties(height=300)
        )
        st.altair_chart(line, use_container_width=True)



with col[2]:
    st.subheader("세부 분석")

    df = st.session_state["filtered_df"]

    if len(df) == 0:
        st.info("필터 결과가 없습니다. 사이드바 조건을 확인하세요.")
    else:
        # -----------------------------
        # 1) Top Groups by Survival
        # -----------------------------
        st.markdown("#### 생존률이 높은 그룹 (Top Groups)")

        # 그룹 정의: 성별 + 클래스
        group_stats = (
            df.groupby(["Sex", "Pclass"])["Survived"]
            .mean()
            .reset_index()
            .sort_values("Survived", ascending=False)
        )
        group_stats["Survived"] *= 100  # 퍼센트 변환

        top_chart = (
            alt.Chart(group_stats.head(6))
            .mark_bar()
            .encode(
                x=alt.X("Survived:Q", title="생존률 (%)"),
                y=alt.Y("Sex:N", title="성별", sort="-x"),
                color=alt.Color("Pclass:O", title="탑승 클래스"),
                tooltip=["Sex", "Pclass", alt.Tooltip("Survived", format=".1f")],
            )
            .properties(height=300)
        )
        st.altair_chart(top_chart, use_container_width=True)

        st.markdown("---")

        # -----------------------------
        # 2) 상위운임 승객 리스트
        # -----------------------------
        st.markdown("#### 상위운임 승객 (Top Fare Passengers)")
        top_n = 10  # 표시 개수
        cols_to_show = ["Name", "Pclass", "Sex", "Age", "Fare", "Embarked", "Survived"]
        show_df = (
            df[cols_to_show]
            .dropna(subset=["Fare"])
            .sort_values("Fare", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        show_df["Survived"] = show_df["Survived"].map({0: "사망", 1: "생존"})
        st.dataframe(show_df, use_container_width=True)
