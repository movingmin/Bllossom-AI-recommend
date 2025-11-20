from django.shortcuts import render
from .kis import get_stock_price
from .services.llm import ask_invest_ai


def main(request):
    # 세션에 저장된 예산 불러오기 (없으면 0)
    budget = request.session.get("budget", 0)

    # 템플릿으로 넘길 기본 값
    context = {
        "budget": budget,
        "api_error": False,
        "api_message": "",
        "stock_name": "",
        "stock_code": "",
        "price": "",
        "change": "",
        "change_rate": "",
        # 추가 정보
        "open_price": "",
        "high_price": "",
        "low_price": "",
        "volume": "",
        # 차트 데이터
        "chart_labels": [],
        "chart_prices": [],
        # LLM 답변
        "ai_answer": "",
    }

    if request.method == "POST":

        # 1) 예산 설정 버튼 눌렀을 때
        if "budget_submit" in request.POST:
            raw = request.POST.get("budget_amount", "").replace(",", "").strip()
            if raw.isdigit():
                budget = int(raw)
                request.session["budget"] = budget
                context["budget"] = budget
            else:
                context["api_error"] = True
                context["api_message"] = "예산은 숫자만 입력해 주세요."

        # 2) 주식 검색 버튼 눌렀을 때
        if "stock_search" in request.POST:
            keyword = request.POST.get("stock_keyword", "").strip()
            if keyword:
                result = get_stock_price(keyword)
                if result["error"]:
                    context["api_error"] = True
                    context["api_message"] = result["message"]
                else:
                    context["stock_name"] = result["stock_name"]
                    context["stock_code"] = result["stock_code"]
                    context["price"] = result["price"]
                    context["change"] = result["change"]
                    context["change_rate"] = result["change_rate"]
                    # 추가 정보
                    context["open_price"] = result.get("open", "")
                    context["high_price"] = result.get("high", "")
                    context["low_price"] = result.get("low", "")
                    context["volume"] = result.get("volume", "")
                    # 차트 데이터
                    context["chart_labels"] = result.get("chart_labels", [])
                    context["chart_prices"] = result.get("chart_prices", [])
            else:
                context["api_error"] = True
                context["api_message"] = "종목 코드 또는 이름을 입력해 주세요."

        # 3) LLM 질문하기 눌렀을 때
        if "llm_question" in request.POST:
            # ⭐ 여기부터 전부 if 안으로 들여쓰기 되어 있어야 함 (공백 4칸)
            question = request.POST.get("llm_question", "").strip()
            stock_name = context.get("stock_name") or ""  # 직전에 검색한 종목명

            if question:
                context["ai_answer"] = ask_invest_ai(question, stock_name=stock_name)
            else:
                context["api_error"] = True
                context["api_message"] = "AI에게 물어볼 내용을 입력해 주세요."

    return render(request, "recommend/main.html", context)
