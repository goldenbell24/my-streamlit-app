import streamlit as st
import requests
from collections import Counter

st.set_page_config(page_title="🎬 나와 어울리는 영화는?", page_icon="🎬", layout="centered")

# ----------------------------
# TMDB 설정
# ----------------------------
TMDB_DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_POSTER_BASE = "https://image.tmdb.org/t/p/w500"

GENRES = {
    "액션": 28,
    "코미디": 35,
    "드라마": 18,
    "SF": 878,
    "로맨스": 10749,
    "판타지": 14,
}

# ----------------------------
# 유틸 함수들
# ----------------------------
def decide_genre(answers: dict) -> tuple[str, str]:
    """
    사용자의 답변을 바탕으로 장르를 점수화해서 1개 장르를 결정.
    반환: (genre_name, explanation_text)
    """
    scores = {g: 0 for g in GENRES.keys()}

    # Q1. 주말
    q1 = answers["q1"]
    if q1 == "집에서 휴식":
        scores["드라마"] += 2
        scores["로맨스"] += 1
    elif q1 == "친구와 놀기":
        scores["코미디"] += 2
        scores["액션"] += 1
    elif q1 == "새로운 곳 탐험":
        scores["판타지"] += 2
        scores["SF"] += 1
        scores["액션"] += 1
    elif q1 == "혼자 취미생활":
        scores["드라마"] += 1
        scores["SF"] += 1
        scores["판타지"] += 1

    # Q2. 스트레스 해소
    q2 = answers["q2"]
    if q2 == "혼자 있기":
        scores["드라마"] += 2
        scores["SF"] += 1
    elif q2 == "수다 떨기":
        scores["코미디"] += 2
        scores["로맨스"] += 1
    elif q2 == "운동하기":
        scores["액션"] += 2
        scores["SF"] += 1
    elif q2 == "맛있는 거 먹기":
        scores["코미디"] += 1
        scores["드라마"] += 1
        scores["로맨스"] += 1

    # Q3. 영화에서 중요한 것
    q3 = answers["q3"]
    if q3 == "감동 스토리":
        scores["드라마"] += 3
        scores["로맨스"] += 1
    elif q3 == "시각적 영상미":
        scores["SF"] += 2
        scores["판타지"] += 2
        scores["액션"] += 1
    elif q3 == "깊은 메시지":
        scores["드라마"] += 2
        scores["SF"] += 1
    elif q3 == "웃는 재미":
        scores["코미디"] += 3

    # Q4. 여행 스타일
    q4 = answers["q4"]
    if q4 == "계획적":
        scores["드라마"] += 1
    elif q4 == "즉흥적":
        scores["코미디"] += 1
        scores["로맨스"] += 1
    elif q4 == "액티비티":
        scores["액션"] += 2
        scores["SF"] += 1
    elif q4 == "힐링":
        scores["로맨스"] += 2
        scores["드라마"] += 1

    # Q5. 친구 사이의 역할
    q5 = answers["q5"]
    if q5 == "듣는 역할":
        scores["드라마"] += 1
        scores["로맨스"] += 1
    elif q5 == "주도하기":
        scores["액션"] += 1
        scores["SF"] += 1
    elif q5 == "분위기 메이커":
        scores["코미디"] += 2
    elif q5 == "필요할 때 나타남":
        scores["SF"] += 1
        scores["판타지"] += 1
        scores["액션"] += 1

    # 최고 점수 장르 선택 (동점이면 안정적으로 정렬 기준 적용)
    max_score = max(scores.values())
    top_genres = [g for g, s in scores.items() if s == max_score]
    top_genres.sort(key=lambda x: list(GENRES.keys()).index(x))  # 고정된 우선순위
    chosen = top_genres[0]

    # 설명 문구 만들기
    # (가장 크게 영향을 준 답변 키워드도 같이 보여주면 설득력 ↑)
    keywords = []
    if answers["q3"] in ["감동 스토리", "깊은 메시지"] and chosen in ["드라마", "SF"]:
        keywords.append("스토리/메시지")
    if answers["q3"] == "시각적 영상미" and chosen in ["SF", "판타지", "액션"]:
        keywords.append("영상미")
    if answers["q3"] == "웃는 재미" and chosen == "코미디":
        keywords.append("유쾌함")
    if answers["q4"] == "힐링" and chosen in ["로맨스", "드라마"]:
        keywords.append("힐링")
    if answers["q4"] == "액티비티" and chosen in ["액션", "SF"]:
        keywords.append("활동성")

    kw_text = " / ".join(keywords) if keywords else "전반적인 성향"
    explanation = f"당신의 답변을 종합해보면 **{kw_text}**을(를) 특히 중요하게 생각하는 편이라 **{chosen}** 장르가 잘 어울려요!"

    return chosen, explanation


@st.cache_data(show_spinner=False)
def fetch_popular_movies_by_genre(api_key: str, genre_id: int, limit: int = 5) -> list[dict]:
    """
    TMDB discover API로 해당 장르 인기 영화 가져오기
    """
    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "language": "ko-KR",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "include_video": "false",
        "page": 1,
    }
    r = requests.get(TMDB_DISCOVER_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])[:limit]
    return results


def make_reason(chosen_genre: str, answers: dict, movie: dict) -> str:
    """
    '이 영화를 추천하는 이유'를 간단한 템플릿으로 생성
    (다음 시간에 LLM/API로 고도화 가능)
    """
    q3 = answers["q3"]
    q4 = answers["q4"]

    # 영화 정보 약간 활용
    rating = movie.get("vote_average", 0)
    title = movie.get("title", "이 작품")

    base = f"**{chosen_genre}** 감성과 잘 맞는 인기 작품이라 추천해요."
    if q3 == "감동 스토리":
        base = f"스토리 몰입을 좋아하는 당신에게, **{title}**는 감정선을 따라가기 좋은 작품이에요."
    elif q3 == "시각적 영상미":
        base = f"영상미를 중요하게 생각한다면 **{title}** 같은 작품이 만족도가 높아요."
    elif q3 == "깊은 메시지":
        base = f"여운/메시지를 선호하는 당신에게 **{title}**는 생각할 거리를 주는 편이에요."
    elif q3 == "웃는 재미":
        base = f"웃는 재미를 찾는다면 **{title}**는 가볍게 즐기기 좋아요."

    # 여행 스타일로 한 줄 추가
    if q4 == "힐링" and chosen_genre in ["로맨스", "드라마"]:
        base += " 게다가 편안하게 힐링하며 보기 좋아요."
    elif q4 == "액티비티" and chosen_genre in ["액션", "SF"]:
        base += " 템포가 살아있어 스트레스 해소에 딱이에요."
    elif q4 == "즉흥적" and chosen_genre in ["코미디", "로맨스"]:
        base += " 즉흥적인 기분 전환용으로도 잘 맞아요."

    # 평점 기반(아주 짧게)
    if isinstance(rating, (int, float)) and rating >= 7.5:
        base += " 평점도 높은 편이라 실패 확률이 낮아요."

    return base


# ----------------------------
# UI
# ----------------------------
st.sidebar.header("🔑 TMDB 설정")
api_key = st.sidebar.text_input("TMDB API Key", type="password", placeholder="여기에 키를 입력하세요")

st.title("🎬 나와 어울리는 영화는?")
st.write("간단한 질문 5개로 당신의 성향을 알아보고, 어울리는 영화 장르와 인기 영화를 추천해드려요! 🍿")
st.divider()

q1 = st.radio(
    "1. 주말에 가장 하고 싶은 것은?",
    ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"],
    index=None
)

q2 = st.radio(
    "2. 스트레스 받으면?",
    ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"],
    index=None
)

q3 = st.radio(
    "3. 영화에서 중요한 것은?",
    ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"],
    index=None
)

q4 = st.radio(
    "4. 여행 스타일?",
    ["계획적", "즉흥적", "액티비티", "힐링"],
    index=None
)

q5 = st.radio(
    "5. 친구 사이에서 나는?",
    ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"],
    index=None
)

st.divider()

# ----------------------------
# 결과 보기
# ----------------------------
if st.button("결과 보기", type="primary"):
    # 입력 검증
    if not api_key:
        st.error("사이드바에 TMDB API Key를 입력해 주세요.")
        st.stop()

    if None in [q1, q2, q3, q4, q5]:
        st.warning("모든 질문에 답해 주세요!")
        st.stop()

    answers = {"q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5}

    chosen_genre, explanation = decide_genre(answers)
    genre_id = GENRES[chosen_genre]

    with st.spinner("분석 중..."):
        try:
            movies = fetch_popular_movies_by_genre(api_key, genre_id, limit=5)
        except requests.HTTPError as e:
            st.error("TMDB API 호출에 실패했어요. API Key가 올바른지 확인해 주세요.")
            st.caption(f"에러 상세: {e}")
            st.stop()
        except requests.RequestException as e:
            st.error("네트워크 문제로 TMDB API 호출에 실패했어요. 잠시 후 다시 시도해 주세요.")
            st.caption(f"에러 상세: {e}")
            st.stop()

    st.subheader("🧠 당신에게 어울리는 장르")
    st.markdown(f"### **{chosen_genre}**")
    st.write(explanation)
    st.divider()

    st.subheader("🎞️ 인기 영화 추천 TOP 5")

    if not movies:
        st.info("해당 장르에서 추천할 영화를 찾지 못했어요. (결과가 비어있음)")
        st.stop()

    for m in movies:
        title = m.get("title") or m.get("name") or "제목 없음"
        overview = m.get("overview") or "줄거리 정보가 없어요."
        rating = m.get("vote_average", 0)
        poster_path = m.get("poster_path")

        poster_url = f"{TMDB_POSTER_BASE}{poster_path}" if poster_path else None
        reason = make_reason(chosen_genre, answers, m)

        with st.container(border=True):
            col1, col2 = st.columns([1, 2], gap="large")

            with col1:
                if poster_url:
                    st.image(poster_url, use_container_width=True)
                else:
                    st.info("포스터 없음")

            with col2:
                st.markdown(f"### {title}")
                st.write(f"⭐ 평점: **{rating:.1f}**" if isinstance(rating, (int, float)) else "⭐ 평점 정보 없음")
                st.markdown("**줄거리**")
                st.write(overview)

                st.markdown("**이 영화를 추천하는 이유**")
                st.write(reason)
