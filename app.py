import streamlit as st
import requests

# -----------------------------
# Config
# -----------------------------
GENRE_MAP = {
    "액션": 28,
    "코미디": 35,
    "드라마": 18,
    "SF": 878,
    "로맨스": 10749,
    "판타지": 14,
}

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"

# -----------------------------
# Helpers
# -----------------------------
def analyze_answers_to_genre(q1, q2, q3, q4, q5):
    """
    사용자 답변을 점수화해서 최종 장르(1개)를 결정.
    필요하면 이 매핑을 원하는 방식으로 조정하면 됩니다.
    """
    scores = {g: 0 for g in GENRE_MAP.keys()}
    reasons = []

    # Q1. 주말
    if q1 == "집에서 휴식":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        scores["판타지"] += 1
        reasons.append("편안한 휴식을 선호해서 감정선이 좋은 작품이 잘 맞아요.")
    elif q1 == "친구와 놀기":
        scores["코미디"] += 2
        scores["액션"] += 1
        reasons.append("사람들과 즐기는 시간을 좋아해 유쾌한 영화가 잘 어울려요.")
    elif q1 == "새로운 곳 탐험":
        scores["SF"] += 2
        scores["액션"] += 1
        scores["판타지"] += 1
        reasons.append("새로운 경험을 좋아해 세계관이 큰 영화가 취향일 확률이 높아요.")
    elif q1 == "혼자 취미생활":
        scores["드라마"] += 1
        scores["SF"] += 1
        reasons.append("혼자 몰입하는 시간을 즐겨 서사가 탄탄한 영화가 잘 맞아요.")

    # Q2. 스트레스
    if q2 == "혼자 있기":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        reasons.append("혼자 정리하는 스타일이라 감정 몰입형 영화가 좋아요.")
    elif q2 == "수다 떨기":
        scores["코미디"] += 2
        scores["로맨스"] += 1
        reasons.append("대화로 푸는 편이라 가볍게 즐길 영화가 잘 맞아요.")
    elif q2 == "운동하기":
        scores["액션"] += 2
        scores["SF"] += 1
        reasons.append("활동적으로 해소해서 에너지 넘치는 영화가 어울려요.")
    elif q2 == "맛있는 거 먹기":
        scores["코미디"] += 1
        scores["드라마"] += 1
        scores["로맨스"] += 1
        reasons.append("일상의 만족을 중시해서 공감되는 톤의 영화가 좋아요.")

    # Q3. 영화에서 중요한 것
    if q3 == "감동 스토리":
        scores["드라마"] += 3
        reasons.append("스토리와 감동을 중요하게 여겨 드라마가 제격이에요.")
    elif q3 == "시각적 영상미":
        scores["SF"] += 2
        scores["판타지"] += 2
        scores["액션"] += 1
        reasons.append("비주얼을 중시해서 스케일 큰 장르가 잘 맞아요.")
    elif q3 == "깊은 메시지":
        scores["드라마"] += 2
        scores["SF"] += 1
        reasons.append("메시지를 좋아해 생각할 거리 있는 영화가 어울려요.")
    elif q3 == "웃는 재미":
        scores["코미디"] += 3
        reasons.append("웃음을 원해서 코미디가 딱이에요.")

    # Q4. 여행 스타일
    if q4 == "계획적":
        scores["드라마"] += 1
        scores["SF"] += 1
        reasons.append("구조적이고 탄탄한 전개를 선호할 가능성이 있어요.")
    elif q4 == "즉흥적":
        scores["코미디"] += 1
        scores["로맨스"] += 1
        scores["액션"] += 1
        reasons.append("즉흥을 즐겨 템포 좋은 영화가 어울려요.")
    elif q4 == "액티비티":
        scores["액션"] += 2
        scores["SF"] += 1
        reasons.append("활동적인 취향이라 액션/스릴이 잘 맞아요.")
    elif q4 == "힐링":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        scores["판타지"] += 1
        reasons.append("힐링을 원해서 따뜻한 감성의 영화가 잘 맞아요.")

    # Q5. 친구 사이에서
    if q5 == "듣는 역할":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        reasons.append("공감형 성향이라 관계 중심 장르가 어울려요.")
    elif q5 == "주도하기":
        scores["액션"] += 2
        scores["SF"] += 1
        reasons.append("주도적이라 주인공 서사가 강한 영화가 잘 맞아요.")
    elif q5 == "분위기 메이커":
        scores["코미디"] += 2
        scores["판타지"] += 1
        reasons.append("분위기를 띄우는 타입이라 재미/상상력이 있는 영화가 좋아요.")
    elif q5 == "필요할 때 나타남":
        scores["SF"] += 1
        scores["액션"] += 1
        scores["드라마"] += 1
        reasons.append("독립적이면서도 결정적 역할을 하는 캐릭터에 끌릴 수 있어요.")

    # 최고 점수 장르 선택 (동점이면 우선순위로 고정)
    priority = ["드라마", "코미디", "액션", "로맨스", "SF", "판타지"]
    max_score = max(scores.values())
    top_genres = [g for g, s in scores.items() if s == max_score]
    top_genres.sort(key=lambda g: priority.index(g))

    chosen = top_genres[0]
    return chosen, scores, reasons


def fetch_top_movies(api_key, genre_id, language="ko-KR", page=1):
    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "language": language,
        "sort_by": "popularity.desc",
        "page": page,
        "include_adult": "false",
    }
    r = requests.get(DISCOVER_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("results", [])


def build_recommendation_reason(chosen_genre, scores, base_reasons, movie_title):
    # 점수 근거 + 장르 근거를 짧게 요약
    top3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    top3_txt = ", ".join([f"{g}({s})" for g, s in top3])

    # base_reasons 중 1~2개만 사용
    short_reasons = []
    for r in base_reasons:
        if r not in short_reasons:
            short_reasons.append(r)
        if len(short_reasons) == 2:
            break

    reason = (
        f"당신의 선택 패턴에서 **{chosen_genre}** 성향이 가장 강하게 나타났어요 "
        f"(점수 상위: {top3_txt}). "
    )
    if short_reasons:
        reason += " ".join(short_reasons) + " "
    reason += f"그래서 **{movie_title}** 같은 {chosen_genre} 영화가 잘 맞을 확률이 높아요!"
    return reason


# -----------------------------
# App
# -----------------------------
def main():
    st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬", layout="centered")

    st.title("🎬 나와 어울리는 영화는?")
    st.write("간단한 질문 5개로, 당신의 성향과 어울리는 영화 장르를 고르고 인기 영화 5편을 추천해줄게요!")
    st.caption("TMDB API를 사용해 추천 영화를 가져옵니다.")

    with st.sidebar:
        st.header("🔑 TMDB API Key")
        api_key = st.text_input("API Key", type="password", placeholder="여기에 API Key를 입력하세요")
        st.caption("예: f85e7c405ff8244ad88d677b7ce78f5d")

    st.divider()

    q1 = st.radio(
        "1. 주말에 가장 하고 싶은 것은?",
        ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"],
        index=None,
        key="q1",
    )
    q2 = st.radio(
        "2. 스트레스 받으면?",
        ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"],
        index=None,
        key="q2",
    )
    q3 = st.radio(
        "3. 영화에서 중요한 것은?",
        ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"],
        index=None,
        key="q3",
    )
    q4 = st.radio(
        "4. 여행 스타일?",
        ["계획적", "즉흥적", "액티비티", "힐링"],
        index=None,
        key="q4",
    )
    q5 = st.radio(
        "5. 친구 사이에서 나는?",
        ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"],
        index=None,
        key="q5",
    )

    st.divider()

    if st.button("결과 보기", type="primary"):
        # 입력 검증
        if not api_key:
            st.error("사이드바에 TMDB API Key를 입력해주세요.")
            st.stop()

        if None in [q1, q2, q3, q4, q5]:
            st.warning("모든 질문에 답해주세요!")
            st.stop()

        # 1) 답변 분석 -> 장르 결정
        chosen_genre, scores, reasons = analyze_answers_to_genre(q1, q2, q3, q4, q5)
        genre_id = GENRE_M
