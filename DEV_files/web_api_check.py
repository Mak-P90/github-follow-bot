"""Development-only helper API for manual GitHub follower checks.

This module is intentionally excluded from production deploy flows.
Set DEV_WEB_API_CHECK_ENABLED=true only in local development.
"""

import asyncio
import os
from typing import List

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

if os.getenv("DEV_WEB_API_CHECK_ENABLED", "false").lower() != "true":
    raise RuntimeError(
        "DEV_files/web_api_check.py is disabled by default. "
        "Set DEV_WEB_API_CHECK_ENABLED=true for local development only."
    )

# Configuration Constants
GITHUB_USER = os.getenv("GITHUB_USER")
PERSONAL_GITHUB_TOKEN = os.getenv("PERSONAL_GITHUB_TOKEN")

if not GITHUB_USER or not PERSONAL_GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_USER or PERSONAL_GITHUB_TOKEN is not set in the environment.")

FOLLOWER_URL = f"https://api.github.com/users/{GITHUB_USER}/followers"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)

# GitHub API Headers
HEADERS = {
    "Authorization": f"token {PERSONAL_GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": f"{GITHUB_USER}-FollowBack-Bot-WebAPI",
}

app = FastAPI(title="GitHub Followers API", description="API to fetch GitHub followers.", version="1.0")


class Follower(BaseModel):
    login: str
    id: int
    avatar_url: str
    html_url: str


@app.get("/followers", response_model=List[Follower])
async def get_followers():
    followers = []
    page = 1
    per_page = 100

    async with aiohttp.ClientSession(headers=HEADERS, timeout=REQUEST_TIMEOUT) as session:
        while True:
            params = {"page": page, "per_page": per_page}
            try:
                async with session.get(FOLLOWER_URL, params=params) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=response.status, detail="GitHub API request failed")
                    data = await response.json()
                    if not data:
                        break
                    for follower in data:
                        followers.append(
                            Follower(
                                login=follower.get("login"),
                                id=follower.get("id"),
                                avatar_url=follower.get("avatar_url"),
                                html_url=follower.get("html_url"),
                            )
                        )
                    page += 1
            except aiohttp.ClientError:
                raise HTTPException(status_code=502, detail="Unable to reach GitHub API")
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="GitHub API request timed out")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(status_code=500, detail="Unexpected server error")

    return followers
