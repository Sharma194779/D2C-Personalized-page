Introduction:
A simple web app that turns social media product links into professional landing pages using AI. Built with Flask and powered by Groq's Llama models.

Paste a link to a product post from Instagram, Twitter, or any social platform. The app scrapes basic info from the page and uses AI to generate a complete marketing landing page with product descriptions, key features, and ad copy.
Features:

Automatic content scraping from URLs
AI-generated marketing copy using Llama 3.3
Clean, modern landing page design
Campaign history and storage
Simple SQLite database for persistence

Setup
Install dependencies:
bashpip install flask groq beautifulsoup4 requests python-dotenv
Get a free API key from Groq at https://console.groq.com/keys
Add your API key to main.py on line 19:
pythonGROQ_API_KEY = "your_groq_api_key_here"
Run the app:
bashpython main.py
Open your browser to http://127.0.0.1:5000
How it works:
The app scrapes metadata from the URL you provide, sends it to Groq's Llama model with a marketing-focused prompt, and generates structured content. The generated campaign is saved to a local SQLite database and rendered as a full landing page.
Tech stack:

Backend: Flask (Python)
AI: Groq API with Llama 3.3 70B
Database: SQLite
Frontend: HTML, CSS, vanilla JavaScript
Web scraping: BeautifulSoup4
