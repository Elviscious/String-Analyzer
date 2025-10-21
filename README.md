# 🧠 String Analyzer API

A **FastAPI-based application** that analyzes and manages strings with advanced filtering and natural language interpretation.  
It supports CRUD operations, filtering by string properties, and intelligent natural language queries.

---

## 🚀 Features

- ✅ **Create a new string** and analyze its properties
- 🔍 **Get specific strings** using the string value
- ⚙️ **Filter strings** using query parameters (e.g., min length, palindrome, etc.)
- 🗣️ **Filter using Natural Language (NLP)** (e.g., “show me palindromic strings longer than 5 characters”)
- ❌ **Delete strings** from the in-memory database
- 🔒 Includes proper **error handling** and **status codes**

---

## 🧩 Tech Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Database:** In-memory dictionary (for simplicity)
- **Hashing:** SHA-256 for unique string identification
- **Natural Language Parsing:** Regex & string-based rules (extendable with spaCy)

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/string-analyzer.git
cd string-analyzer
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn
```

### 3. Run the Application

```bash
uvicorn main:app --reload
```

### 4. Access the Documentation

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📍 API Endpoints

### 🧾 1. **Create a String**

**POST** `/strings/`

```json
{
	"value": "madam"
}
```

**Response (201):**

```json
{
	"id": "09b9c392dc1f6e914cea287cb6be34b0...",
	"value": "madam",
	"properties": {
		"length": 5,
		"is_palindrome": true,
		"unique_characters": 3,
		"word_count": 1,
		"sha256_hash": "09b9c392dc1f6e914cea287cb6be34b0...",
		"character_frequency_map": {
			"m": 2,
			"a": 2,
			"d": 1
		},
		"created_at": "2025-10-17T09:32:10.123Z"
	}
}
```

---

### 🔍 2. **Get a Specific String**

**GET** `/strings/{string_value}`
Returns the analyzed data for that exact string.

**Example:**
`GET /strings/madam`

---

### 🧮 3. **Filter Strings (Query Parameters)**

**GET** `/strings/`

**Available filters:**

| Parameter            | Type | Description                             |
| -------------------- | ---- | --------------------------------------- |
| `is_palindrome`      | bool | Filter palindromic strings              |
| `min_length`         | int  | Minimum string length                   |
| `max_length`         | int  | Maximum string length                   |
| `word_count`         | int  | Exact number of words                   |
| `contains_character` | str  | Strings containing a specific character |

**Example:**
`/strings/?is_palindrome=true&min_length=4`

---

### 🗣️ 4. **Filter by Natural Language Query**

**GET** `/strings/filter-by-natural-language?query={query}`

**Example Queries:**

```
show me palindromic strings longer than 5 characters
find strings with the letter "a"
list strings that are not palindrome and have more than one word
```

**Response:**

```json
{
  "data": [...],
  "count": 2,
  "interpreted_query": {
    "original": "show me palindromic strings longer than 5 characters",
    "parsed_filters": {
      "is_palindrome": true,
      "min_length": 5
    }
  }
}
```

---

### 🗑️ 5. **Delete a String**

**DELETE** `/strings/{string_value}`
Deletes a specific string by its SHA-256 ID or value.

---

## ⚠️ Error Handling

| Status Code                  | Description                            | Example Cause                            |
| ---------------------------- | -------------------------------------- | ---------------------------------------- |
| **400 Bad Request**          | Unable to parse natural language query | Invalid or empty natural language input  |
| **409 Conflict**             | String already exists                  | Same string submitted twice              |
| **404 Not Found**            | String not found in database           | Fetching or deleting a missing string    |
| **422 Unprocessable Entity** | Conflicting filters in query           | Example: “palindrome and not palindrome” |

---

## 🧠 NLP Logic (Simplified)

The NLP filter uses keyword and regex matching to interpret human-like queries:

| Phrase Example       | Parsed Filter              |
| -------------------- | -------------------------- |
| “palindrome”         | `is_palindrome = True`     |
| “not palindrome”     | `is_palindrome = False`    |
| “longer than 5”      | `min_length = 5`           |
| “less than 10”       | `max_length = 10`          |
| “contains letter a”  | `contains_character = "a"` |
| “more than one word” | `word_count > 1`           |

---

## 💡 Future Improvements

- Integrate **spaCy** for more accurate NLP query understanding
- Add **persistent storage** (SQLite or PostgreSQL)
- Add **authentication** for data management
- Deploy to **Render / Railway / Vercel**

---

## 👨‍💻 Author

**David Ihegaranya**
Computer Engineering Student • Graphics Designer • Developer
Passionate about building tools that simplify complex problems.
