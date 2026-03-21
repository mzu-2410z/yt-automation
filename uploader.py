"""
uploader.py
Uploads the final video to YouTube using the YouTube Data API v3.
First run: opens browser for OAuth. Token is cached for all future runs.
"""

import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_credentials():
    token_path = Path(config.YOUTUBE_TOKEN_FILE)
    creds_path = Path(config.YOUTUBE_CREDS_FILE)
    creds = None

    if token_path.exists():
        with open(token_path, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    "\n[!] client_secrets.json not found.\n"
                    "    1. Go to https://console.cloud.google.com/\n"
                    "    2. Create project → Enable 'YouTube Data API v3'\n"
                    "    3. Credentials → OAuth 2.0 Client → Desktop App\n"
                    "    4. Download JSON → rename to client_secrets.json\n"
                    "    5. Place it in this project folder\n"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "wb") as f:
            pickle.dump(creds, f)

    return creds


def upload_to_youtube(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
) -> str:
    creds   = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": config.YOUTUBE_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": config.YOUTUBE_PRIVACY,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=4 * 1024 * 1024,
    )

    req = youtube.videos().insert(
        part=",".join(body.keys()), body=body, media_body=media
    )

    print("  Uploading", end="", flush=True)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"\r  Uploading... {int(status.progress() * 100)}%", end="", flush=True)

    print()
    return f"https://www.youtube.com/watch?v={response['id']}"
