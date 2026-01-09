# services/youtube_search.py

from yt_dlp import YoutubeDL


def search_youtube(query: str, limit: int = 5) -> list[dict]:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
    }

    search_query = f"ytsearch{limit}:{query}"
    results = []

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)

        if not info or "entries" not in info:
            return results

        for entry in info["entries"]:
            results.append(
                {
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                }
            )

    return results
