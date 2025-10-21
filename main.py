from pydoc import text
from fastapi import FastAPI, Query
import re
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
import hashlib

app = FastAPI()

database = {}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/strings/")
def create_string(body: dict[str, str]):

    if "value" not in body:
        raise HTTPException(
            status_code=400, detail="Missing 'value' in request body")

    if not isinstance(body["value"], str):
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
            "created_at": datetime.now().isoformat()
        }
    }

    database[hash_id] = info

    return info


@app.get("/strings/{string_value}")
def get_string(string_value: str):
    hash_id = hashlib.sha256(string_value.encode()).hexdigest()

    if hash_id not in database:
        raise HTTPException(
            status_code=404, detail="String not found"
        )

    return database[hash_id]


@app.get("/strings/")
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


@app.get("/strings/filter-by-natural-language/")
def filter_by_natural_language(query: str = Query(...)):
    parsed_filters = {}
    text = query.lower()

    # Detect filters

    if "palindrome" in text and "not palindrome" in text:
        raise HTTPException(
            status_code=422,
            detail="Conflicting query: both 'palindrome' and 'not palindrome' found."
        )

    if "palindrome" in text or "palindromic" in text:
        parsed_filters["is_palindrome"] = True
    elif "not palindrome" in text or "not palindromic" in text:
        parsed_filters["is_palindrome"] = False

    # Detect phrases that mean "more than one word"
    if "multiple words" in text or "more than one word" in text or "more than 2 words" in text:
        parsed_filters["min_word_count"] = 2  # more than 1 or 2 words

    # Detect phrases that mean "exactly one word"
    elif "single word" in text or "one word" in text:
        parsed_filters["word_count"] = 1

    # Regex-based parsing
    match = re.search(r"(?:longer|at least|minimum length of)\s+(\d+)", text)
    if match:
        parsed_filters["min_length"] = int(match.group(1))

    match = re.search(r"(?:shorter|less than|maximum length of)\s+(\d+)", text)
    if match:
        parsed_filters["max_length"] = int(match.group(1))

    match = re.search(r"(?:letter|character)\s+['\"]?(\w)['\"]?", text)
    if match:
        parsed_filters["contains_character"] = match.group(1)

        # 🔴 Check for unprocessable (422) conflicts dynamically
    if "min_length" in parsed_filters and "max_length" in parsed_filters:
        if parsed_filters["min_length"] > parsed_filters["max_length"]:
            raise HTTPException(
                status_code=422,
                detail=f"Conflicting query: min_length ({parsed_filters['min_length']}) is greater than max_length ({parsed_filters['max_length']})."
            )

    if "word_count" in parsed_filters and "min_word_count" in parsed_filters:
        raise HTTPException(
            status_code=422,
            detail="Conflicting query: 'single word' and 'more than one word' cannot both be true."
        )

    # 400 Bad Request: no valid filters
    if not parsed_filters:
        raise HTTPException(
            status_code=400,
            detail="Unable to parse natural language query — no valid filters found."
        )

    # Start filtering
    results = list(database.values())

    if parsed_filters.get("is_palindrome") is not None:
        results = [item for item in results if item["properties"]
                   ["is_palindrome"] == parsed_filters["is_palindrome"]]

    if parsed_filters.get("min_length") is not None:
        results = [item for item in results if item["properties"]
                   ["length"] >= parsed_filters["min_length"]]

    if parsed_filters.get("max_length") is not None:
        results = [item for item in results if item["properties"]
                   ["length"] <= parsed_filters["max_length"]]

    if parsed_filters.get("word_count") is not None:
        results = [item for item in results if item["properties"]
                   ["word_count"] == parsed_filters["word_count"]]

    if parsed_filters.get("min_word_count") is not None:
        results = [item for item in results if item["properties"]
                   ["word_count"] >= parsed_filters["min_word_count"]]

    if parsed_filters.get("contains_character") is not None:
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


@app.delete("/strings/{string_value}", status_code=204)
def delete_string(string_value: str):
    hash_id = hashlib.sha256(string_value.encode()).hexdigest()

    if hash_id not in database:
        raise HTTPException(
            status_code=404, detail="String not found"
        )

    del database[hash_id]

    return {"detail": "String deleted successfully"}
