import json
from logging import getLogger

import requests

from pkuphysu_wechat.config import settings

logger = getLogger(__name__)


class SituationPuzzleAIError(RuntimeError):
    pass


class SituationPuzzleAI:
    @staticmethod
    def complete(messages):
        config = settings.situation_puzzle_ai
        headers = {"Content-Type": "application/json"}
        if config.API_KEY:
            headers["Authorization"] = "Bearer " + config.API_KEY

        try:
            response = requests.post(
                config.API_URL,
                headers=headers,
                json={
                    "model": config.MODEL,
                    "messages": messages,
                    "temperature": config.TEMPERATURE,
                    "max_tokens": config.MAX_TOKENS,
                },
                timeout=config.TIMEOUT,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("AI content is not text")
            result = json.loads(content)
            if not isinstance(result, dict) or set(result) != {"verdict"}:
                raise ValueError("AI verdict has an invalid shape")
            verdict = result["verdict"]
            if verdict not in ("yes", "no", "irrelevant", "unknown", "solved"):
                raise ValueError("AI verdict is invalid")
        except (
            requests.RequestException,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ) as error:
            logger.warning("Situation-puzzle AI request failed: %s", error)
            raise SituationPuzzleAIError("The AI provider did not return a reply")

        return verdict
