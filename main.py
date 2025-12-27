#!/usr/bin/env python3


import os
import json
import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


GROQ_API_KEY = "grok api as open ai is not open source"  
# ============================================


client = Groq(api_key=GROQ_API_KEY)

DB_FILE = "campaigns.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT,
            product_name TEXT,
            product_description TEXT,
            generated_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def scrape_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        title = (soup.find("meta", property="og:title") or soup.find("meta", {"name": "og:title"}))
        title = title.get("content", "") if title else soup.find("title").text if soup.find("title") else "Product"
        
        desc = (soup.find("meta", property="og:description") or soup.find("meta", {"name": "description"}))
        desc = desc.get("content", "") if desc else ""
        
        text = soup.get_text()[:500].strip() if soup.get_text() else ""
        
        return {"title": title, "description": desc, "text": text}
    except:
        return {"title": "Product", "description": "", "text": ""}

def generate_campaign(url):
    try:
        scraped = scrape_url(url)
        
        prompt = f"""You are an expert digital marketer creating a D2C landing page.
URL: {url}
Title: {scraped['title']}
Description: {scraped['description']}

Generate compelling D2C ad content in JSON format. Make sure all text is properly escaped for JSON.
{{
    "productName": "product name",
    "productDescription": "2-3 sentences",
    "adCopy": "3 compelling paragraphs about the product",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "celebrityEndorsement": "A celebrity quote endorsement",
    "features": ["feature1", "feature2", "feature3", "feature4"]
}}

IMPORTANT: Return ONLY valid JSON with no newlines in strings, no control characters, and proper escaping."""
        
        # Using Groq with Llama model
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Fast and capable Llama model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1].replace("json", "").strip()
        
        # Clean up control characters that might break JSON parsing
        import re
        # Remove control characters except newline, tab, and carriage return
        content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', content)
        
        data = json.loads(content)
        return {
            "originalUrl": url,
            "productName": data.get("productName", "Product"),
            "productDescription": data.get("productDescription", ""),
            "generatedContent": {
                "adCopy": data.get("adCopy", ""),
                "keywords": data.get("keywords", []),
                "celebrityEndorsement": data.get("celebrityEndorsement", ""),
                "features": data.get("features", [])
            }
        }
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Content received: {content[:500]}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def save_campaign(campaign):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO campaigns (original_url, product_name, product_description, generated_content)
            VALUES (?, ?, ?, ?)
        """, (campaign["originalUrl"], campaign["productName"], campaign["productDescription"], 
              json.dumps(campaign["generatedContent"])))
        conn.commit()
        cid = c.lastrowid
        conn.close()
        return cid
    except Exception as e:
        print(f"DB Error: {e}")
        return None

def get_campaign(cid):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM campaigns WHERE id = ?", (cid,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0], "originalUrl": row[1], "productName": row[2],
            "productDescription": row[3], "generatedContent": json.loads(row[4]),
            "createdAt": row[5]
        }
    except:
        return None

def get_campaigns():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM campaigns ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return [{
            "id": row[0], "originalUrl": row[1], "productName": row[2],
            "productDescription": row[3], "generatedContent": json.loads(row[4]),
            "createdAt": row[5]
        } for row in rows]
    except:
        return []

HOME_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ad Campaign Generator</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Outfit', sans-serif; 
            background: #f7f6f3;
            color: #1a1a1a;
            line-height: 1.6;
        }
        .container { max-width: 1280px; margin: 0 auto; padding: 0 20px; }
        
        /* Hero Section */
        .hero {
            padding: 100px 20px;
            text-align: center;
            background: linear-gradient(135deg, #f7f6f3 0%, #eeebe5 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .hero h1 {
            font-family: 'Playfair Display', serif;
            font-size: 72px;
            font-weight: 700;
            margin-bottom: 20px;
            color: #1a1a1a;
            letter-spacing: -2px;
        }
        
        .hero .subtitle {
            font-size: 20px;
            color: #666;
            margin-bottom: 40px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .form-group {
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }
        
        .form-group input {
            flex: 1;
            min-width: 300px;
            padding: 18px 24px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: white;
            font-family: 'Outfit', sans-serif;
            transition: all 0.3s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #1a1a1a;
            box-shadow: 0 0 0 3px rgba(26,26,26,0.1);
        }
        
        .form-group button {
            padding: 18px 40px;
            background: #1a1a1a;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Outfit', sans-serif;
            transition: all 0.3s;
            white-space: nowrap;
        }
        
        .form-group button:hover {
            background: #333;
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .form-group button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Recent Campaigns Section */
        .campaigns-section {
            padding: 80px 20px;
            background: white;
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 50px;
        }
        
        .section-header h2 {
            font-family: 'Playfair Display', serif;
            font-size: 48px;
            font-weight: 700;
            color: #1a1a1a;
        }
        
        .campaigns-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 30px;
        }
        
        .campaign-card {
            background: #f7f6f3;
            border-radius: 12px;
            padding: 30px;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            color: inherit;
        }
        
        .campaign-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            background: #eeebe5;
        }
        
        .campaign-card h3 {
            font-family: 'Playfair Display', serif;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #1a1a1a;
        }
        
        .campaign-card p {
            color: #666;
            font-size: 14px;
            margin-bottom: 15px;
            line-height: 1.5;
        }
        
        .campaign-card .meta {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #999;
        }
        
        .empty-state {
            grid-column: 1 / -1;
            padding: 60px 20px;
            text-align: center;
            background: #f7f6f3;
            border-radius: 12px;
            border: 2px dashed #ddd;
        }
        
        .empty-state p {
            font-size: 18px;
            color: #999;
        }
        
        .message {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        .message.success {
            background: #e8f5e9;
            color: #2e7d32;
            border-left: 4px solid #2e7d32;
        }
        
        .message.error {
            background: #ffebee;
            color: #c62828;
            border-left: 4px solid #c62828;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 30px;
            color: #1a1a1a;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="hero">
        <div class="container">
            <h1>Turn Social Links into<br>High-Converting Pages</h1>
            <p class="subtitle">Paste a social media product link and our AI will generate a personalized, story-driven landing page instantly.</p>
            
            <div id="message"></div>
            <div class="loading" id="loading">⏳ Generating your campaign...</div>
            
            <form id="form" class="form-group">
                <input 
                    type="text" 
                    id="url" 
                    name="url"
                    placeholder="https://instagram.com/p/..." 
                    value="https://www.instagram.com/p/DQKaZtVDx-6/?img_index=1"
                    required
                />
                <button type="submit">Generate</button>
            </form>
        </div>
    </div>

    <div class="campaigns-section">
        <div class="container">
            <div class="section-header">
                <h2>Recent Campaigns</h2>
            </div>
            
            <div class="campaigns-grid" id="campaigns">
                <div class="empty-state"><p>No campaigns yet. Create your first one!</p></div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = document.getElementById('url').value;
            const msg = document.getElementById('message');
            const loading = document.getElementById('loading');
            
            msg.innerHTML = '';
            loading.style.display = 'block';
            
            try {
                const res = await fetch('/api/campaigns/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                const data = await res.json();
                loading.style.display = 'none';
                
                if (!res.ok) {
                    msg.innerHTML = `<div class="message error">❌ ${data.message || 'Failed to generate'}</div>`;
                    return;
                }
                
                msg.innerHTML = '<div class="message success">✓ Campaign generated! Redirecting...</div>';
                setTimeout(() => window.location.href = `/campaign/${data.id}`, 1500);
            } catch (err) {
                loading.style.display = 'none';
                msg.innerHTML = `<div class="message error">Error: ${err.message}</div>`;
            }
        });
        
        async function loadCampaigns() {
            try {
                const res = await fetch('/api/campaigns');
                const campaigns = await res.json();
                const grid = document.getElementById('campaigns');
                
                if (campaigns.length === 0) {
                    grid.innerHTML = '<div class="empty-state"><p>No campaigns yet. Create your first one!</p></div>';
                    return;
                }
                
                grid.innerHTML = campaigns.slice(0, 6).map(c => `
                    <a href="/campaign/${c.id}" class="campaign-card">
                        <h3>${c.productName}</h3>
                        <p>${c.productDescription.substring(0, 100)}...</p>
                        <div class="meta">
                            <span>${new Date(c.createdAt).toLocaleDateString()}</span>
                            <span>View →</span>
                        </div>
                    </a>
                `).join('');
            } catch (err) {
                console.error('Failed to load campaigns:', err);
            }
        }
        
        loadCampaigns();
    </script>
</body>
</html>"""

CAMPAIGN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ campaign.productName }} - Ad Campaign</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Outfit', sans-serif; background: white; color: #1a1a1a; }
        
        /* Navigation */
        nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: rgba(255,255,255,0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid #f0f0f0;
            padding: 0 20px;
        }
        
        nav .container {
            max-width: 1280px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 80px;
        }
        
        nav a { text-decoration: none; color: inherit; }
        nav button {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            font-family: 'Outfit', sans-serif;
            padding: 8px 16px;
            color: #1a1a1a;
            border-radius: 6px;
            transition: all 0.3s;
        }
        
        nav button:hover { background: #f0f0f0; }
        
        /* Hero Section */
        .hero {
            margin-top: 80px;
            height: 600px;
            background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
            color: white;
            display: flex;
            align-items: center;
            overflow: hidden;
            position: relative;
        }
        
        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('https://placehold.co/1920x600/1a1a1a/fff?text=Product') center/cover;
            opacity: 0.3;
        }
        
        .hero .container {
            position: relative;
            z-index: 10;
            max-width: 1280px;
            width: 100%;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .hero h1 {
            font-family: 'Playfair Display', serif;
            font-size: 64px;
            font-weight: 700;
            margin-bottom: 20px;
            max-width: 800px;
        }
        
        .hero p {
            font-size: 18px;
            color: #ddd;
            margin-bottom: 30px;
            max-width: 600px;
            line-height: 1.6;
        }
        
        .hero .cta {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 15px 32px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-family: 'Outfit', sans-serif;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: white;
            color: #1a1a1a;
        }
        
        .btn-primary:hover {
            background: #f0f0f0;
            transform: translateY(-2px);
        }
        
        .btn-outline {
            background: transparent;
            color: white;
            border: 2px solid white;
        }
        
        .btn-outline:hover {
            background: white;
            color: #1a1a1a;
        }
        
        /* Sections */
        section {
            padding: 80px 20px;
        }
        
        section .container {
            max-width: 1280px;
            margin: 0 auto;
        }
        
        .story {
            background: white;
        }
        
        .story h2 {
            font-family: 'Playfair Display', serif;
            font-size: 44px;
            text-align: center;
            margin-bottom: 40px;
        }
        
        .story .content {
            max-width: 800px;
            margin: 0 auto;
            font-size: 16px;
            line-height: 1.8;
            color: #333;
            white-space: pre-wrap;
        }
        
        /* Features */
        .features {
            background: #f7f6f3;
        }
        
        .features h2 {
            font-family: 'Playfair Display', serif;
            font-size: 44px;
            text-align: center;
            margin-bottom: 50px;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
        }
        
        .feature-item {
            background: white;
            padding: 30px;
            border-radius: 12px;
            border-left: 4px solid #1a1a1a;
            transition: all 0.3s;
        }
        
        .feature-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .feature-item p {
            font-size: 16px;
            line-height: 1.6;
        }
        
        /* Endorsement */
        .endorsement {
            background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
            color: white;
            text-align: center;
        }
        
        .endorsement blockquote {
            font-family: 'Playfair Display', serif;
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 30px;
            line-height: 1.4;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .endorsement .credit {
            font-size: 14px;
            color: #999;
            font-style: italic;
        }
        
        /* Gallery */
        .gallery {
            background: white;
        }
        
        .gallery-grid {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 20px;
            height: 500px;
        }
        
        .gallery-item {
            background: #f0f0f0;
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            transition: all 0.3s;
        }
        
        .gallery-item:hover {
            transform: scale(1.02);
        }
        
        .gallery-item:nth-child(2),
        .gallery-item:nth-child(3) {
            grid-column: span 1;
        }
        
        @media (max-width: 768px) {
            .hero h1 { font-size: 42px; }
            .story h2 { font-size: 32px; }
            .features h2 { font-size: 32px; }
            .endorsement blockquote { font-size: 24px; }
            .gallery-grid {
                grid-template-columns: 1fr;
                height: auto;
            }
        }
    </style>
</head>
<body>
    <nav>
        <div class="container">
            <a href="/" style="font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700;">← Back</a>
            <span style="font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700;">{{ campaign.productName }}</span>
            <button onclick="alert('Share functionality coming soon!')">Share →</button>
        </div>
    </nav>

    <!-- Hero -->
    <section class="hero">
        <div class="container">
            <div style="margin-bottom: 20px; display: inline-block; background: rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.2);">
                ⭐ Trending on Social
            </div>
            <h1>{{ campaign.productName }}</h1>
            <p>{{ campaign.productDescription }}</p>
            <div class="cta">
                <button class="btn btn-primary">Shop Now</button>
                <a href="{{ campaign.originalUrl }}" target="_blank" class="btn btn-outline">View Original Post</a>
            </div>
        </div>
    </section>

    <!-- Story -->
    <section class="story">
        <div class="container">
            <h2>Why everyone is talking about {{ campaign.productName }}</h2>
            <div class="content">{{ campaign.generatedContent.adCopy }}</div>
        </div>
    </section>

    <!-- Features -->
    <section class="features">
        <div class="container">
            <h2>Key Features</h2>
            <div class="features-grid">
                {% for feature in campaign.generatedContent.features %}
                <div class="feature-item">
                    <p>✓ {{ feature }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>

    <!-- Endorsement -->
    <section class="endorsement">
        <div class="container">
            <blockquote>"{{ campaign.generatedContent.celebrityEndorsement }}"</blockquote>
            <p class="credit">Endorsed By Top Influencers</p>
        </div>
    </section>

    <!-- Gallery -->
    <section class="gallery">
        <div class="container">
            <div class="gallery-grid">
                <div class="gallery-item">Image 1</div>
                <div class="gallery-item">Image 2</div>
                <div class="gallery-item">Image 3</div>
            </div>
        </div>
    </section>
</body>
</html>"""

@app.route("/")
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route("/campaign/<int:cid>")
def campaign(cid):
    campaign_data = get_campaign(cid)
    if not campaign_data:
        return "Campaign not found", 404
    
    html = CAMPAIGN_TEMPLATE.replace("{{ campaign.productName }}", campaign_data["productName"])
    html = html.replace("{{ campaign.productDescription }}", campaign_data["productDescription"])
    html = html.replace("{{ campaign.originalUrl }}", campaign_data["originalUrl"])
    html = html.replace("{{ campaign.generatedContent.adCopy }}", campaign_data["generatedContent"]["adCopy"])
    html = html.replace("{{ campaign.generatedContent.celebrityEndorsement }}", campaign_data["generatedContent"]["celebrityEndorsement"])
    
    features_html = "".join([f'<div class="feature-item"><p>✓ {f}</p></div>' for f in campaign_data["generatedContent"]["features"]])
    html = html.replace('{% for feature in campaign.generatedContent.features %}<div class="feature-item"><p>✓ {{ feature }}</p></div>{% endfor %}', features_html)
    
    return html

@app.route("/api/campaigns/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        url = data.get("url", "").strip()
        
        if not url:
            return jsonify({"message": "URL required"}), 400
        
        campaign_data = generate_campaign(url)
        if not campaign_data:
            return jsonify({"message": "Failed to generate campaign"}), 500
        
        cid = save_campaign(campaign_data)
        if not cid:
            return jsonify({"message": "Failed to save"}), 500
        
        campaign_data["id"] = cid
        campaign_data["createdAt"] = datetime.now().isoformat()
        return jsonify(campaign_data), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/campaigns")
def list_campaigns():
    return jsonify(get_campaigns()), 200

@app.route("/api/campaigns/<int:cid>")
def get_one(cid):
    campaign_data = get_campaign(cid)
    return jsonify(campaign_data) if campaign_data else ("Not found", 404)

if __name__ == "__main__":
    init_db()
    print("\n Ad Campaign Generator (Groq + Llama)")
    print(" http://127.0.0.1:5000")
    print(" Open your browser!\n")
    app.run(debug=True, port=5000)