import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from linkedin_api import Linkedin

# Load environment variables
load_dotenv()
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD or not GEMINI_API_KEY:
    raise ValueError("Missing environment variables. Set LINKEDIN_EMAIL, LINKEDIN_PASSWORD, and GEMINI_API_KEY in .env file.")

# Setup Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.0-pro")

def get_jobs(api, job_limit=10):
    """Gets LinkedIn job postings using the API."""
    print("🔍 Fetching job listings for Software Engineers in Singapore...")
    
    # Search for jobs
    jobs = api.search_jobs(
        keywords="Software Engineer",
        location="Singapore",
        limit=job_limit
    )
    
    print(f"📄 Found {len(jobs)} job listings.")
    processed_jobs = []
    
    for i, job in enumerate(jobs[:job_limit]):
        print(f"\n✨ Processing job {i+1}/{job_limit}...")
        
        try:
            # Get detailed job info
            job_detail = api.get_job(job['entityUrn'].split(':')[-1])
            
            # Extract description, handling both string and dict cases
            description = job_detail.get('description', '')
            if isinstance(description, dict):
                # If description is a dict, try to get the text content
                description = description.get('text', '') or description.get('content', '') or str(description)
            
            if description:
                job_info = {
                    "title": job_detail.get('title', 'Unknown Title'),
                    "company": job_detail.get('companyDetails', {}).get('company', 'Unknown Company'),
                    "description": description.strip() if isinstance(description, str) else str(description).strip()
                }
                processed_jobs.append(job_info)
                print(f"✅ Added: {job_info['title']} at {job_info['company']}")
            else:
                print("⚠️ Skipped: No description found")
            
        except Exception as e:
            print(f"❌ Error processing job: {str(e)}")
            print(f"Job detail structure: {type(job_detail)}")
            if job_detail and 'description' in job_detail:
                print(f"Description type: {type(job_detail['description'])}")
            continue
            
    return processed_jobs

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
        skills = json.loads(response.text.strip())
        return skills if isinstance(skills, list) else ["Error: Invalid skills format"]
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return ["Error: Could not extract skills"]

def main():
    """Main function to run the scraper and extract skills."""
    try:
        # Authenticate using LinkedIn API
        print("🔐 Logging into LinkedIn...")
        api = Linkedin(LINKEDIN_EMAIL, LINKEDIN_PASSWORD)
        print("✅ Successfully logged in!")

        # Get jobs
        job_postings = get_jobs(api, job_limit=10)

        if not job_postings:
            print("❌ No jobs were collected. Something went wrong.")
            return

        # Process job descriptions and extract skills
        print("Extracting skills from job descriptions...")
        processed_jobs = [{
            "title": job["title"],
            "company": job["company"],
            "skills": extract_skills(job["description"])
        } for job in job_postings]

        # Save results
        output_file = "linkedin_jobs.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(processed_jobs, f, indent=2, ensure_ascii=False)

        print(f"Process completed. Results saved to {output_file}.")

    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
