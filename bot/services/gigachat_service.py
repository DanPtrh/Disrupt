import re
from typing import Tuple
from langchain_gigachat.chat_models import GigaChat

from bot.prompts import FINAL_EVAL_PROMPT


class GigaChatService:
    def __init__(self, credentials: str, scope: str, verify_ssl: bool):
        self.llm = GigaChat(credentials=credentials, scope=scope, verify_ssl_certs=verify_ssl)

    async def evaluate_final(
        self,
        team_name: str,
        audit: str,
        product: str,
        activity: str,
        ogran: str,
        solution_first: str,
        solution_constrained: str,
    ) -> Tuple[float, str]:
        prompt = FINAL_EVAL_PROMPT.format(
            team_name=team_name,
            audit=audit,
            product=product,
            activity=activity,
            ogran=ogran,
            solution_first=solution_first,
            solution_constrained=solution_constrained,
        )

        resp = self.llm.invoke(prompt)
        text = getattr(resp, "content", str(resp))
        score = self._extract_final_score(text)
        return score, text

    def _extract_final_score(self, text: str) -> float:
        # ловим "Итоговая оценка: 7,5" или "Итоговая оценка: 7.5"
        m = re.search(r"Итоговая оценка\s*:\s*(\d{1,2}(?:[.,]\d+)?)", text, flags=re.IGNORECASE)
        if m:
            raw = m.group(1).replace(",", ".")
            try:
                val = float(raw)
                return max(0.0, min(10.0, val))
            except ValueError:
                pass

        # запасной вариант: "7/10"
        m2 = re.search(r"(\d{1,2})\s*/\s*10", text)
        if m2:
            return float(max(0, min(10, int(m2.group(1)))))

        return 0.0
