from enum import Enum
import requests

base_url = "https://api.wanikani.com/v2/subjects"

class SubjectType(str, Enum):
    RADICAL = "radical"
    KANJI = "kanji"
    VOCABULARY = "vocabulary"

class SubjectError(Enum):
    INVALID_TOKEN = -1
    INVALID_SLUG = -2
    INVALID_ID = -3

class ImageSize(str, Enum):
    SMALL = "32x32"
    MEDIUM = "64x64"
    LARGE = "128x128"

def get_subject_by_slug(type: SubjectType, slug: str, token: str) -> dict | SubjectError:
    """
    Query the WaniKani API for a specific subject via its type and slug

    Args:
        type (SubjectType): subject type
        slug (int): subject slug (i.e. name, characters)
        token (str): WaniKani API token

    Returns:
        subject json (dictionary) on success, or a SubjectError on fail
    """

    params = {
        "types": type.value,
        "slugs": slug
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(base_url, params=params, headers=headers).json()
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

    url = f"{base_url}/{id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(url, headers=headers)
    if "code" in r:
        error_code = r["code"]
        if error_code == 401:
            return SubjectError.INVALID_TOKEN
        if error_code == 404:
            return SubjectError.INVALID_ID
        
    return r.json()["data"]


def get_radicals_from_kanji(kanji: str, token: str, image_size: ImageSize = ImageSize.SMALL) -> list | SubjectError:
    """
    Given a kanji character string, return a list of radicals it is made up of (name and image)

    Args:
        kanji (str): kanji character
        token (str): WaniKani API token
        image_size (ImageSize, optional): Size of the image. Defaults to ImageSize.SMALL.

    Returns:
        a list of (<radical name>,<radical image url>) tuples on success, or a SubjectError on fail
    """

    kanji_r = get_subject_by_slug(SubjectType.KANJI, kanji, token)
    if isinstance(kanji_r, SubjectError):
        return kanji_r

    radical_ids = kanji_r["component_subject_ids"]

    result = []
    for id in radical_ids:
        radical_r = get_subject_by_id(id, token)

        slug = radical_r["slug"]

        images = radical_r["character_images"]
        image_urls = [img["url"] for img in images if img["content_type"] == "image/png" and img["metadata"]["dimensions"] == image_size.value]
        
        result.append((slug, image_urls[0]))

    return result
