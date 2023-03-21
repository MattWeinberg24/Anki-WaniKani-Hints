from enum import Enum
import requests

base_url = "https://api.wanikani.com/v2/subjects"

class SubjectType(str, Enum):
    RADICAL = "radical"
    KANJI = "kanji"
    VOCABULARY = "vocabulary"

class SubjectError(Enum):
    INVALID_TOKEN = 1
    INVALID_SLUG = 2
    INVALID_ID = 3
    BAD_CONNECTION = 4

def get_subject_by_slug(subject_type: SubjectType, slug: str, token: str) -> dict | SubjectError:
    """
    Query the WaniKani API for a specific subject via its type and slug

    Args:
        type (SubjectType): subject type
        slug (int): subject slug (i.e. name, characters)
        token (str): WaniKani API token

    Returns:
        subject json (dictionary) on success, or a SubjectError on fail
    """
    print(f"WK API: type={subject_type},slug={slug}")

    params = {
        "types": subject_type.value,
        "slugs": slug
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        r = requests.get(base_url, params=params, headers=headers).json()
    except requests.ConnectionError as e:
        print(e)
        return SubjectError.BAD_CONNECTION
    
    if "code" in r and r["code"] == 401:
        return SubjectError.INVALID_TOKEN
    if r["total_count"] == 0:
        return SubjectError.INVALID_SLUG
    
    return r["data"][0]["data"]


def get_subject_by_id(id: int, token: str) -> dict | SubjectError:
    """
    Query the WaniKani API for a specific subject via its ID

    Args:
        id (int): subject id
        token (str): WaniKani API token

    Returns:
        subject json (dictionary) on success, or a SubjectError on fail
    """
    print(f"WK API: id={id}")

    url = f"{base_url}/{id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        r = requests.get(url, headers=headers)
    except requests.ConnectionError as e:
        print(e)
        return SubjectError.BAD_CONNECTION
    
    if "code" in r:
        error_code = r["code"]
        if error_code == 401:
            return SubjectError.INVALID_TOKEN
        if error_code == 404:
            return SubjectError.INVALID_ID
        
    return r.json()["data"]
