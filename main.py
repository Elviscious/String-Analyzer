from fastapi import Body, FastAPI, Query
import re
from datetime import datetime
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
import hashlib

from fastapi.responses import JSONResponse

app = FastAPI()

database: Dict[str, dict] = {}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/strings")
def create_string(body: dict = Body(...)):

    if "value" not in body:
        raise HTTPException(
            status_code=400, detail="Missing 'value' in request body")

    if not isinstance(body.get("value"), str):
        raise HTTPException(
            status_code=422, detail="'value' must be a string"
        )

    value = body["value"]
    hash_id = hashlib.sha256(value.encode()).hexdigest()

    if hash_id in database:
        raise HTTPException(
            status_code=409, detail="String already exists"
        )

    info = {
        "id": hash_id,
        "value": value,
        "properties": {
            "length": len(value),
            "is_palindrome": value.lower() == value[::-1].lower(),
            "unique_characters": len(set(value)),
            "word_count": len(value.split()),
            "sha256_hash": hash_id,
            "character_frequency_map": {
                char: value.count(char) for char in set(value)
            },
        },
        "created_at": datetime.now().isoformat()
    }

    database[hash_id] = info

    return JSONResponse(status_code=201, content=info)


@app.get("/strings/filter-by-natural-language")
def filter_by_natural_language(query: str = Query(...)):
    parsed_filters = {}
    text = query.lower()

    # Detect palindrome
    if "palindrome" in text and "not palindrome" in text:
        raise HTTPException(
            status_code=422,
            detail="Conflicting query: both 'palindrome' and 'not palindrome' found."
        )

    if "palindrome" in text or "palindromic" in text:
        parsed_filters["is_palindrome"] = True
    elif "not palindrome" in text or "not palindromic" in text:
        parsed_filters["is_palindrome"] = False

    # Detect word count filters
    if "single word" in text or "one word" in text:
        parsed_filters["word_count"] = 1

    if "multiple words" in text:
        parsed_filters["min_word_count"] = 2

    more_than_word_match = re.search(r"more than\s+(\d+)\s+words?", text)
    if more_than_word_match:
        parsed_filters["min_word_count"] = int(
            more_than_word_match.group(1)) + 1

    # Detect length filters
    longer_match = re.search(r"longer\s+than\s+(\d+)", text)
    if longer_match:
        parsed_filters["min_length"] = int(longer_match.group(1)) + 1

    shorter_match = re.search(r"shorter\s+than\s+(\d+)", text)
    if shorter_match:
        parsed_filters["max_length"] = int(shorter_match.group(1)) - 1

    at_least_match = re.search(r"at\s+least\s+(\d+)", text)
    if at_least_match:
        parsed_filters["min_length"] = int(at_least_match.group(1))

    less_than_match = re.search(r"less\s+than\s+(\d+)", text)
    if less_than_match:
        parsed_filters["max_length"] = int(less_than_match.group(1)) - 1

    min_length_match = re.search(
        r"minimum\s+(?:length\s+(?:of\s+)?)?(\d+)", text)
    if min_length_match:
        parsed_filters["min_length"] = int(min_length_match.group(1))

    max_length_match = re.search(
        r"maximum\s+(?:length\s+(?:of\s+)?)?(\d+)", text)
    if max_length_match:
        parsed_filters["max_length"] = int(max_length_match.group(1))

    # Detect contains_character
    contains_match = re.search(
        r"(?:contain|containing|contains|that contain|with|has)\s+(?:the\s+)?(?:letter|character)?\s*['\"]?(\w)['\"]?",
        text
    )
    if contains_match:
        parsed_filters["contains_character"] = contains_match.group(1)

    if "first vowel" in text:
        parsed_filters["contains_character"] = "a"

    # Check for conflicts
    if "min_length" in parsed_filters and "max_length" in parsed_filters:
        if parsed_filters["min_length"] > parsed_filters["max_length"]:
            raise HTTPException(
                status_code=422,
                detail=f"Conflicting query: min_length ({parsed_filters['min_length']}) > max_length ({parsed_filters['max_length']})."
            )

    if "word_count" in parsed_filters and "min_word_count" in parsed_filters:
        raise HTTPException(
            status_code=422,
            detail="Conflicting query: exact word_count and min_word_count cannot both be set."
        )

    # 400 if no valid filters parsed
    if not parsed_filters:
        raise HTTPException(
            status_code=400,
            detail="Unable to parse natural language query — no valid filters found."
        )

    # Apply filters
    results = list(database.values())

    if "is_palindrome" in parsed_filters:
        results = [item for item in results if item["properties"]
                   ["is_palindrome"] == parsed_filters["is_palindrome"]]

    if "min_length" in parsed_filters:
        results = [item for item in results if item["properties"]
                   ["length"] >= parsed_filters["min_length"]]

    if "max_length" in parsed_filters:
        results = [item for item in results if item["properties"]
                   ["length"] <= parsed_filters["max_length"]]

    if "word_count" in parsed_filters:
        results = [item for item in results if item["properties"]
                   ["word_count"] == parsed_filters["word_count"]]

    if "min_word_count" in parsed_filters:
        results = [item for item in results if item["properties"]
                   ["word_count"] >= parsed_filters["min_word_count"]]

    if "contains_character" in parsed_filters:
        results = [
            item for item in results if parsed_filters["contains_character"] in item["value"]]

    return {
        "data": results,
        "count": len(results),
        "interpreted_query": {
            "original": query,
            "parsed_filters": parsed_filters
        }
    }

@app.get("/strings/{string_value}")
def get_string(string_value: str):
    hash_id = hashlib.sha256(string_value.encode()).hexdigest()

    if hash_id not in database:
        raise HTTPException(
            status_code=404, detail="String not found"
        )

    return database[hash_id]


@app.get("/strings")
def get_strings(
    is_palindrome: Optional[bool] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    word_count: Optional[int] = None,
    contains_character: Optional[str] = None
):
    results = list(database.values())

    if is_palindrome is not None:
        results = [item for item in results if item["properties"]
                   ["is_palindrome"] == is_palindrome]

    if min_length is not None:
        results = [item for item in results if item["properties"]
                   ["length"] >= min_length]

    if max_length is not None:
        results = [item for item in results if item["properties"]
                   ["length"] <= max_length]

    if word_count is not None:
        results = [item for item in results if item["properties"]
                   ["word_count"] == word_count]

    if contains_character is not None:
        results = [
            item for item in results if contains_character in item["value"]]

    filter_applied = {
        "is_palindrome": is_palindrome,
        "min_length": min_length,
        "max_length": max_length,
        "word_count": word_count,
        "contains_character": contains_character
    }

    return {
        "data": results,
        "count": len(results),
        "filters_applied": {k: v for k, v in filter_applied.items() if v is not None}
    }


@app.delete("/strings/{string_value}", status_code=204)
def delete_string(string_value: str):
    hash_id = hashlib.sha256(string_value.encode()).hexdigest()

    if hash_id not in database:
        raise HTTPException(
            status_code=404, detail="String not found"
        )

    del database[hash_id]

    return None
