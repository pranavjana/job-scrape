# LinkedIn Job Skills Extractor

This project scrapes Software Engineer job descriptions from LinkedIn and uses Google's Gemini AI to extract required skills from each posting.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root and add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

You can get a Gemini API key from: https://makersuite.google.com/app/apikey

## Usage

Run the script:
```bash
python linkedin_scraper.py
```

The script will:
1. Scrape 10 Software Engineer job postings from LinkedIn
2. Extract required skills using Gemini AI
3. Save the results in `linkedin_jobs.json`

## Output Format

The script generates a JSON file (`linkedin_jobs.json`) with the following structure:

```json
[
  {
    "title": "Software Engineer",
    "company": "Example Company",
    "description": "Full job description...",
    "skills": ["Python", "Java", "Problem Solving", "Communication"]
  }
]
```

## Notes
- The script is limited to scraping 10 job postings to avoid overwhelming LinkedIn's servers
- Make sure you have a stable internet connection when running the script
- The skill extraction uses AI and may require adjustments based on the job descriptions 
