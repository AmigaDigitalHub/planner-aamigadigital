import os
import requests
from typing import List, Dict, Optional

TRELLO_API = "https://api.trello.com/1"

class TrelloClient:
    def __init__(self, key: str | None = None, token: str | None = None):
        self.key = key or os.getenv("TRELLO_KEY")
        self.token = token or os.getenv("TRELLO_TOKEN")
        if not self.key or not self.token:
            raise ValueError("TRELLO_KEY e TRELLO_TOKEN são obrigatórios. Define-os nos Secrets da Streamlit Cloud.")

    def _auth(self) -> Dict[str, str]:
        return {"key": self.key, "token": self.token}

    def get_boards(self) -> List[Dict]:
        r = requests.get(f"{TRELLO_API}/members/me/boards", params=self._auth(), timeout=30)
        r.raise_for_status()
        return [b for b in r.json() if not b.get("closed")]

    def get_lists(self, board_id: str) -> List[Dict]:
        r = requests.get(f"{TRELLO_API}/boards/{board_id}/lists", params=self._auth(), timeout=30)
        r.raise_for_status()
        return r.json()

    def create_card(self, list_id: str, name: str, desc: str, due: Optional[str] = None, labels: Optional[list] = None) -> Dict:
        params = {**self._auth(), "idList": list_id, "name": name, "desc": desc}
        if due:
            params["due"] = due  # accept YYYY-MM-DD or ISO8601
        r = requests.post(f"{TRELLO_API}/cards", params=params, timeout=30)
        r.raise_for_status()
        card = r.json()
        # optional labels as plain text (create label objects on the fly without color)
        if labels:
            for label in labels:
                try:
                    requests.post(
                        f"{TRELLO_API}/cards/{card['id']}/labels",
                        params={**self._auth(), "color": "null", "name": label},
                        timeout=20,
                    )
                except Exception:
                    pass
        return card
