import streamlit as st
import requests

# =========================
# TMDB 설정
# =========================
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

# =========================
# 1) 답변 분석 -> 장르 결정
# =========================
def analyze_answers_to_genre(q1, q2, q3, q4, q5):
    scores = {g: 0 for g in GENRES.keys()}
    reasons = []

    # Q1. 주말에 하고 싶은 것
    if q1 == "집에서 휴식":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        scores["판타지"] += 1
        reasons.append("휴식을 선호해 감정선이 좋은 영화가 잘 맞아요.")
    elif q1 == "친구와 놀기":
        scores["코미디"] += 2
        scores["액션"] += 1
        reasons.append("사람들과 즐기는 걸 좋아해 유쾌한 영화가 잘 어울려요.")
    elif q1 == "새로운 곳 탐험":
        scores["SF"] += 2
        scores["판타지"] += 1
        scores["액션"] += 1
        reasons.append("새로운 경험을 좋아해 세계관이 큰 영화가 취향일 확률이 높아요.")
    elif q1 == "혼자 취미생활":
        scores["드라마"] += 1
        scores["SF"] += 1
        reasons.append("혼자 몰입하는 시간을 즐겨 서사가 탄탄한 영화가 잘 맞아요.")

    # Q2. 스트레스 해소
    if q2 == "혼자 있기":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        reasons.append("혼자 정리하는 편이라 감정 몰입형 장르가 어울려요.")
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
        reasons.append("일상의 만족을 중시해 공감되는 톤의 영화가 잘 맞아요.")

    # Q3. 영화에서 중요한 것
    if q3 == "감동 스토리":
        scores["드라마"] += 3
        reasons.append("스토리와 감동을 중요하게 여겨 드라마 성향이 강해요.")
    elif q3 == "시각적 영상미":
        scores["SF"] += 2
        scores["판타지"] += 2
        scores["액션"] += 1
        reasons.append("영상미를 중시해 스케일 큰 장르가 잘 맞아요.")
    elif q3 == "깊은 메시지":
        scores["드라마"] += 2
        scores["SF"] += 1
        reasons.append("메시지를 좋아해 생각할 거리 있는 영화가 어울려요.")
    elif q3 == "웃는 재미":
        scores["코미디"] += 3
        reasons.append("웃음을 원해 코미디 성향이 강해요.")

    # Q4. 여행 스타일
    if q4 == "계획적":
        scores["드라마"] += 1
        scores["SF"] += 1
        reasons.append("탄탄한 구성/전개를 선호할 가능성이 있어요.")
    elif q4 == "즉흥적":
        scores["코미디"] += 1
        scores["로맨스"] += 1
        scores["액션"] += 1
        reasons.append("즉흥을 즐겨 템포 좋은 영화가 어울려요.")
    elif q4 == "액티비티":
        scores["액션"] += 2
        scores["SF"] += 1
        reasons.append("액티브한 성향이라 액션/스릴이 잘 맞아요.")
    elif q4 == "힐링":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        scores["판타지"] += 1
        reasons.append("힐링을 원해 따뜻한 감성의 영화가 잘 맞아요.")

    # Q5. 친구 사이에서 나는?
    if q5 == "듣는 역할":
        scores["드라마"] += 2
        scores["로맨스"] += 1
        reasons.append("공감형이라 관계 중심 장르가 잘 어울려요.")
    elif q5 == "주도하기":
        scores["액션"] += 2
        scores["SF"] += 1
        reasons.append("주도적이라 주인공 서사가 강한 영화가 잘 맞아요.")
    elif q5 == "분위기 메이커":
        scores["코미디"] += 2
        scores["판타지"] += 1
        reasons.append("분위기 메이커라 재미/상상력이 있는 영화가 어울려요.")
    elif q5 == "필요할 때 나타남":
        scores["SF"] += 1
        scores["액션"] += 1
        scores["드라마"] += 1
        reasons.append("독립적이면서도 임팩트 있는 전개에 끌릴 수 있어요.")

    # 동점일 때 우선순위(원하면 변경 가능)
    priority = ["드라마", "코미디", "액션", "로맨스", "SF", "판타지"]
    max_score = max(scores.values())
    candidates = [g for g, s in scores.items() if s == max_score]
    candidates.sort(key=lambda g: priority.index(g))
    chosen_genre = candidates[0]

    # 추천 이유는 1~2개만 간단히
    uniq = []
    for r in reasons:
        if r not in uniq:
            uniq.append(r)
        if len(uniq) == 2:
            break

    return chosen_genre, scores, uniq


# =========================
# 2) TMDB 호출
# =========================
def fetch_top_movies(api_key: str, genre_id: int, limit: int = 5, language: str = "ko-KR"):
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


def build_recommendation_reason(chosen_genre: str, base_reasons: list, movie_title: str):
    reason = f"당신의 답변 패턴에서 **{chosen_genre}** 성향이 강하게 나타났어요. "
    if base_reasons:
        reason += base_reasons[0] + " "
    reason += f"그래서 **{movie_title}** 같은 {chosen_genre} 영화가 잘 맞을 확률이 높아요!"
    return reason
