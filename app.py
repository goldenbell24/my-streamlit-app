import streamlit as st
import requests

# -----------------------------
# TMDB 설정
# -----------------------------
DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"

GENRES = {
    "액션": 28,
    "코미디": 35,
    "드라마": 18,
    "SF": 878,
    "로맨스": 10749,
    "판타지": 14,
}

# -----------------------------
# 답변 분석 -> 장르 결정(룰 기반 점수)
# -----------------------------
def analyze_answers_to_genre(q1, q2, q3, q4, q5):
    scores = {g: 0 for g in GENRES.keys()}
    reasons = []

    # 1) 주말
    if q1 == "집에서 휴식":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        scores["판타지"] += 1
        reasons.append("휴식을 선호해서 잔잔한 감정선/몰입형 영화가 잘 맞아요.")
    elif q1 == "친구와 놀기":
        scores["코미디"] += 2
        scores["액션"] += 1
        reasons.append("사람들과 에너지 있게 즐기는 타입이라 밝고 유쾌한 장르가 잘 어울려요.")
    elif q1 == "새로운 곳 탐험":
        scores["SF"] += 2
        scores["판타지"] += 1
        scores["액션"] += 1
        reasons.append("새로움과 자극을 좋아해서 세계관/스케일 큰 영화가 잘 맞아요.")
    elif q1 == "혼자 취미생활":
        scores["드라마"] += 1
        scores["SF"] += 1
        reasons.append("혼자 몰입하는 시간을 즐겨 서사가 탄탄한 영화가 잘 맞아요.")

    # 2) 스트레스 해소
    if q2 == "혼자 있기":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        reasons.append("혼자 정리하는 편이라 감정 몰입형 작품이 어울려요.")
    elif q2 == "수다 떨기":
        scores["코미디"] += 2
        scores["로맨스"] += 1
        reasons.append("대화로 푸는 편이라 가볍게 즐길 영화가 잘 맞아요.")
    elif q2 == "운동하기":
        scores["액션"] += 2
        scores["SF"] += 1
        reasons.append("활동적으로 풀어서 텐션 높은 영화가 취향일 가능성이 높아요.")
    elif q2 == "맛있는 거 먹기":
        scores["코미디"] += 1
        scores["드라마"] += 1
        scores["로맨스"] += 1
        reasons.append("일상 만족을 중시해서 공감되는 톤의 영화가 잘 맞아요.")

    # 3) 영화에서 중요한 것
    if q3 == "감동 스토리":
        scores["드라마"] += 3
        reasons.append("감동/서사를 중요하게 여겨 드라마 성향이 강해요.")
    elif q3 == "시각적 영상미":
        scores["SF"] += 2
        scores["판타지"] += 2
        scores["액션"] += 1
        reasons.append("비주얼을 중시해서 SF/판타지/액션 계열이 잘 맞아요.")
    elif q3 == "깊은 메시지":
        scores["드라마"] += 2
        scores["SF"] += 1
        reasons.append("메시지/여운을 좋아해서 생각할 거리 있는 영화가 어울려요.")
    elif q3 == "웃는 재미":
        scores["코미디"] += 3
        reasons.append("웃음이 중요해서 코미디 성향이 강해요.")

    # 4) 여행 스타일
    if q4 == "계획적":
        scores["드라마"] += 1
        scores["SF"] += 1
        reasons.append("구조적인 흐름을 선호해서 전개가 탄탄한 영화가 잘 맞아요.")
    elif q4 == "즉흥적":
        scores["코미디"] += 1
        scores["로맨스"] += 1
        scores["액션"] += 1
        reasons.append("즉흥을 즐겨 템포 좋은 영화가 어울려요.")
    elif q4 == "액티비티":
        scores["액션"] += 2
        scores["SF"] += 1
        reasons.append("액티브한 스타일이라 액션/스릴 쪽이 잘 맞아요.")
    elif q4 == "힐링":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        scores["판타지"] += 1
        reasons.append("힐링을 원해서 따뜻한 감성의 영화가 잘 맞아요.")

    # 5) 친구 사이 역할
    if q5 == "듣는 역할":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        reasons.append("공감형이라 관계 중심 장르가 잘 맞아요.")
    elif q5 == "주도하기":
        scores["액션"] += 2
        scores["SF"] += 1
        reasons.append("주도적인 성향이라 주인공 서사가 강한 영화가 어울려요.")
    elif q5 == "분위기 메이커":
        scores["코미디"] += 2
        scores["판타지"] += 1
        reasons.append("분위기를 띄우는 타입이라 재미/상상력이 있는 영화가 잘 맞아요.")
    elif q5 == "필요할 때 나타남":
        scores["SF"] += 1
        scores["액션"] += 1
        scores["드라마"] += 1
        reasons.append("독립적이면서도 임팩트 있는 전개를 좋아할 가능성이 있어요.")

    # 동점 처리 우선순위(취향에 맞게 바꿔도 됨)
    priority = ["드라마", "코미디", "액션", "로맨스", "SF", "판타지"]
    max_score = max(scores.values())
    top = [g for g, s in scores.items() if s == max_score]
    top.sort(key=lambda g: priority.index(g))
    chosen_genre = top[0]

    # 추천 이유(짧게 1~2개)
    dedup = []
    for r in reasons:
        if r not in dedup:
            dedup.append(r)
        if len(dedup) == 2:
            break

    return chosen_genre, scores, dedup


# -----------------------------
# TMDB에서 장르별 인기 영화 가져오기
# -----------------------------
def fetch_movies_by_genre(api_key: str, genre_id: int, limit: int = 5, language: str = "ko-KR"):
    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "language": language,
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "page": 1,
    }
    r = requests.get(DISCOVER_URL, params=params, timeout=15)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[:limit]


def build_movie_reason(chosen_genre: str, base_reasons: list[str], movie_title: str):
    # 영화별 이유는 “선택한 장르 + 사용자 성향 요약”으로 간단히
    reason = f"당신은 **{chosen_genre}** 성향이 강해서 "
    if base_reasons:
        reason += f"{base_reasons[0]} "
    reason += f"그래서 **{movie_title}** 같은 {chosen_genre} 영화가 잘 맞을 확률이 높아요."
    return reason


# -----------------------------
# Streamlit App
# -----------------------------
def main():
    st.set_page_config(
        page_title="나와 어울리는 영화는?",
        page_icon="🎬",
        layout="centered"
    )

    # ✅ 사이드바: TMDB API Key 입력
    with st.sidebar:
        st.header("🔑 TMDB API 설정")
        tmdb_api_key = st.text_input(
            "TMDB API Key",
            type="password",
            placeholder="여기에 TMDB API Key를 입력하세요",
            help="TMDB에서 영화 데이터를 가져오는 데 사용됩니다."
        )
        st.caption("※ 키를 입력해야 추천 결과가 표시됩니다.")

    st.title("🎬 나와 어울리는 영화는?")
    st.write("간단한 질문 5개로, 당신의 성향과 어울리는 영화 장르를 고르고 인기 영화 5편을 추천해줄게요! 👀")

    st.divider()

    q1 = st.radio(
        "1. 주말에 가장 하고 싶은 것은?",
        ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"],
        index=None,
        key="q1"
    )

    q2 = st.radio(
        "2. 스트레스 받으면?",
        ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"],
        index=None,
        key="q2"
    )

    q3 = st.radio(
        "3. 영화에서 중요한 것은?",
        ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"],
        index=None,
        key="q3"
    )

    q4 = st.radio(
        "4. 여행 스타일?",
        ["계획적", "즉흥적", "액티비티", "힐링"],
        index=None,
        key="q4"
    )

    q5 = st.radio(
        "5. 친구 사이에서 나는?",
        ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"],
        index=None,
        key="q5"
    )

    st.divider()

    if st.button("결과 보기", type="primary"):
        # 1) 입력 검증
        if not tmdb_api_key:
            st.error("사이드바에 TMDB API Key를 먼저 입력해줘!")
            st.stop()

        if None in [q1, q2, q3, q4, q5]:
            st.warning("모든 질문에 답해주세요!")
            st.stop()

        # 2) 답변 분석 -> 장르 결정
        chosen_genre, scores, base_reasons = analyze_answers_to_genre(q1, q2, q3, q4, q5)
        genre_id = GENRES[chosen_genre]

        st.subheader("🧠 분석 결과")
        st.write(f"당신에게 어울리는 장르: **{chosen_genre}**")
        with st.expander("점수 상세 보기"):
            st.json(scores)

        # 3) TMDB로 영화 5개 가져오기
        try:
            movies = fetch_movies_by_genre(tmdb_api_key, genre_id, limit=5, language="ko-KR")
        except requests.HTTPError as e:
            st.error("TMDB 요청에 실패했어요. API Key가 맞는지 확인해줘!")
            st.caption(f"에러: {e}")
            st.stop()
        except requests.RequestException as e:
            st.error("네트워크 오류가 발생했어요. 잠시 후 다시 시도해줘!")
            st.caption(f"에러: {e}")
            st.stop()

        if not movies:
            st.info("해당 장르의 영화를 찾지 못했어요. 다른 답변 조합으로 다시 시도해봐!")
            st.stop()

        # 4) 포스터/제목/평점/줄거리 + 5) 추천 이유 표시
        st.subheader("🍿 추천 영화 TOP 5")

        for m in movies:
            title = m.get("title") or "제목 없음"
            vote = m.get("vote_average", 0)
            overview = m.get("overview") or "줄거리 정보가 없어요."
            poster_path = m.get("poster_path")
            poster_url = f"{POSTER_BASE_URL}{poster_path}" if poster_path else No_
