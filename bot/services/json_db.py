import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from bot.config import Settings

class JsonDB:
    def __init__(self, settings: Settings):
        self.s = settings
        self._lock = asyncio.Lock()
        self._ensure_files()

    def _ensure_files(self):
        for p in [
            self.s.db_users_path,
            self.s.db_teams_path,
            self.s.db_rounds_path,
            self.s.db_solutions_path,
            self.s.db_moderators_path,
        ]:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if not os.path.exists(p):
                with open(p, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)

    async def _read(self, path: str) -> list:
        async with self._lock:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    async def _write(self, path: str, data: list) -> None:
        async with self._lock:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------- roles ----------
    # ---------- roles ----------
    async def is_moderator(self, user_id: int) -> bool:
        rows = await self._read(self.s.db_moderators_path)
        return any(int(x["user_id"]) == user_id for x in rows)


    async def add_moderator(self, user_id: int, username: str | None = None) -> None:
        rows = await self._read(self.s.db_moderators_path)

        # обновляем, если уже есть
        for r in rows:
            if int(r["user_id"]) == user_id:
                if username is not None:
                    r["username"] = username
                await self._write(self.s.db_moderators_path, rows)
                return

        rows.append({"user_id": user_id, "username": username})
        await self._write(self.s.db_moderators_path, rows)


    async def remove_moderator(self, user_id: int) -> None:
        rows = await self._read(self.s.db_moderators_path)
        rows = [x for x in rows if int(x["user_id"]) != user_id]
        await self._write(self.s.db_moderators_path, rows)


    async def find_moderator_id_by_username(self, username: str) -> int | None:
        # username ожидаем без "@"
        u = (username or "").lstrip("@").strip().lower()
        if not u:
            return None
        rows = await self._read(self.s.db_moderators_path)
        for r in rows:
            if (r.get("username") or "").lower() == u:
                return int(r["user_id"])
        return None


    async def list_moderators(self) -> List[Dict[str, Any]]:
        return await self._read(self.s.db_moderators_path)


    # ---------- users/teams ----------
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        rows = await self._read(self.s.db_users_path)
        for r in rows:
            if int(r["user_id"]) == user_id:
                return r
        return None


    async def upsert_user(
        self,
        user_id: int,
        captain_name: str | None = None,
        username: str | None = None,
        city: str | None = None,
    ) -> None:
        rows = await self._read(self.s.db_users_path)
        for r in rows:
            if int(r["user_id"]) == user_id:
                if captain_name is not None:
                    r["captain_name"] = captain_name
                if username is not None:
                    r["username"] = username
                if city is not None:
                    r["city"] = city
                await self._write(self.s.db_users_path, rows)
                return

        # если пользователя нет — создаём
        rows.append({
            "user_id": user_id,
            "captain_name": captain_name or "",
            "username": username,
            "city": city,
        })
        await self._write(self.s.db_users_path, rows)


    async def set_user_city(self, user_id: int, city: str) -> None:
        await self.upsert_user(user_id=user_id, city=city)

    async def upsert_team(self, user_id: int, team_name: str) -> None:
        rows = await self._read(self.s.db_teams_path)
        found = False
        for r in rows:
            if int(r["owner_user_id"]) == user_id:
                r["team_name"] = team_name
                found = True
                break
        if not found:
            rows.append({"owner_user_id": user_id, "team_name": team_name})
        await self._write(self.s.db_teams_path, rows)

    async def get_team(self, user_id: int) -> Optional[Dict[str, Any]]:
        rows = await self._read(self.s.db_teams_path)
        for r in rows:
            if int(r["owner_user_id"]) == user_id:
                return r
        return None

    # ---------- rounds ----------
    async def create_round(self, user_id: int, audit: str, product: str, activity: str) -> int:
        rows = await self._read(self.s.db_rounds_path)
        new_id = (max([r["round_id"] for r in rows], default=0) + 1) if rows else 1
        rows.append({
            "round_id": new_id,
            "owner_user_id": user_id,
            "audit": audit,
            "product": product,
            "activity": activity,
            "ogran": None,
        })
        await self._write(self.s.db_rounds_path, rows)
        return new_id

    async def set_round_ogran(self, round_id: int, ogran: str) -> None:
        rows = await self._read(self.s.db_rounds_path)
        for r in rows:
            if int(r["round_id"]) == round_id:
                r["ogran"] = ogran
                break
        await self._write(self.s.db_rounds_path, rows)

    async def get_round(self, round_id: int) -> Optional[Dict[str, Any]]:
        rows = await self._read(self.s.db_rounds_path)
        for r in rows:
            if int(r["round_id"]) == round_id:
                return r
        return None
    
    async def get_round_solutions(self, round_id: int, owner_user_id: int) -> dict:
        rows = await self._read(self.s.db_solutions_path)
        first = None
        constrained = None
        for r in rows:
            if int(r["round_id"]) == round_id and int(r["owner_user_id"]) == owner_user_id:
                if r["stage"] == "first":
                    first = r
                elif r["stage"] == "constrained":
                    constrained = r
        return {"first": first, "constrained": constrained}


    async def get_user_active_round(self, user_id: int) -> Optional[Dict[str, Any]]:
        rows = await self._read(self.s.db_rounds_path)
        # Самый последний раунд пользователя
        candidates = [r for r in rows if int(r["owner_user_id"]) == user_id]
        return max(candidates, key=lambda x: x["round_id"]) if candidates else None

    # ---------- solutions ----------
    async def save_solution(
        self,
        owner_user_id: int,
        round_id: int,
        stage: str,  # "first" | "constrained"
        text: str,
        gigachat_report: str,
        score: int,
    ) -> None:
        rows = await self._read(self.s.db_solutions_path)
        rows.append({
            "owner_user_id": owner_user_id,
            "round_id": round_id,
            "stage": stage,
            "text": text,
            "gigachat_report": gigachat_report,
            "score": score,
        })
        await self._write(self.s.db_solutions_path, rows)

    async def list_my_solutions(self, user_id: int) -> List[Dict[str, Any]]:
        rows = await self._read(self.s.db_solutions_path)
        return [r for r in rows if int(r["owner_user_id"]) == user_id]

    async def list_all_solutions(self) -> List[Dict[str, Any]]:
        return await self._read(self.s.db_solutions_path)
