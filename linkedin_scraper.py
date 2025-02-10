import os
import asyncio
import json
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import google.generativeai as genai

# Load environment variables securely
load_dotenv()
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD or not GEMINI_API_KEY:
    raise ValueError("Missing environment variables. Set LINKEDIN_EMAIL, LINKEDIN_PASSWORD, and GEMINI_API_KEY in .env file.")

# Setup Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.0-pro")

async def login_to_linkedin(page):
    """Logs into LinkedIn and verifies successful login using cookies."""
    print("🔐 Logging into LinkedIn...")
    await page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded')
    
    await page.fill('input[name="session_key"]', LINKEDIN_EMAIL)
    await page.fill('input[name="session_password"]', LINKEDIN_PASSWORD)
    await page.click('button[type="submit"]')

    # Wait for feed identity module as success indicator
    print("Waiting for login to complete...")
    await page.wait_for_selector('div.feed-identity-module', timeout=15000)
    print("✅ Successfully logged in!")
    await asyncio.sleep(3)  # Wait a bit for the page to settle

async def scrape_jobs(page, job_limit=10):
    """Scrapes LinkedIn job postings and extracts job details."""
    print("🔍 Fetching job listings for Software Engineers in Singapore...")
    jobs_url = "https://www.linkedin.com/jobs/search/?keywords=Software%20Engineer&location=Singapore"
    await page.goto(jobs_url, wait_until='domcontentloaded')
    
    await asyncio.sleep(3)  # Allow dynamic content to load

    # Get all job cards
    job_cards = await page.query_selector_all('.job-card-container, .jobs-search-results__list-item')
    print(f"📄 Found {len(job_cards)} job listings.")

    jobs = []
    
    for i, card in enumerate(job_cards[:job_limit]):  # Limit to `job_limit`
        print(f"\n✨ Processing job {i+1}/{job_limit}...")

        # Click job card to load details
        await card.click()
        await asyncio.sleep(2)  # Allow job description to load

        # Extract job details using proper selector methods
        title_elem = await card.query_selector('.job-card-container__link, h3.job-card-list__title')
        title = await title_elem.inner_text() if title_elem else "Unknown Title"
        
        company_elem = await card.query_selector('.job-card-container__company-name')
        company = await company_elem.inner_text() if company_elem else "Unknown Company"
        
        # Extract job description
        desc_elem = await page.query_selector('div.jobs-box__html-content[id="job-details"]')
        description = await desc_elem.inner_text() if desc_elem else ""

        if description.strip():  # Only add jobs with descriptions
            jobs.append({"title": title.strip(), "company": company.strip(), "description": description.strip()})
            print(f"✅ Added: {title} at {company}")

    return jobs

def extract_skills(description):
    """Uses Gemini AI to extract required skills from job description."""
    prompt = f"""
    Extract required technical and soft skills from this job description.
    Return only a JSON list: ["Skill1", "Skill2", "Skill3"]
    
    Job Description:
    {description}
    """

    try:
        response = gemini_model.generate_content(prompt)
        skills = json.loads(response.text.strip())  # Ensure JSON format
        return skills if isinstance(skills, list) else ["Error: Invalid skills format"]
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return ["Error: Could not extract skills"]

async def main():
    """Main function to run the scraper and extract skills."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Run in headless mode for efficiency
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Log in and scrape jobs
            await login_to_linkedin(page)
            job_postings = await scrape_jobs(page, job_limit=10)

            # Process job descriptions and extract skills
            print("Extracting skills from job descriptions...")
            processed_jobs = [{"title": job["title"], "company": job["company"], "skills": extract_skills(job["description"])} for job in job_postings]

            # Save results
            output_file = "linkedin_jobs.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(processed_jobs, f, indent=2, ensure_ascii=False)

            print(f"Process completed. Results saved to {output_file}.")

        finally:
            await browser.close()

# Run the script
if __name__ == "__main__":
    asyncio.run(main())
