import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# Include kids voice routes
from kids_voice_routes import router as kids_voice_router
app.include_router(kids_voice_router)

# Serve static files (kids_voice.js)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Test page
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>IRA Kids Voice Test</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Nunito', cursive, sans-serif;
      background: linear-gradient(135deg, #667EEA22, #764BA222);
      min-height: 100vh;
      display: flex; flex-direction: column;
      align-items: center; padding: 40px 20px 200px;
    }
    h1 { font-size: 28px; color: #333; margin-bottom: 8px; }
    p  { color: #666; margin-bottom: 32px; }

    .characters {
      display: flex; gap: 16px; flex-wrap: wrap;
      justify-content: center; margin-bottom: 32px;
    }
    .char-card {
      background: white; border-radius: 20px;
      padding: 20px 28px; text-align: center;
      cursor: pointer; border: 3px solid transparent;
      transition: all 0.2s; box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }
    .char-card:hover   { transform: translateY(-4px); }
    .char-card.active  { border-color: #667EEA; }
    .char-card .emoji  { font-size: 40px; display: block; margin-bottom: 8px; }
    .char-card .name   { font-size: 16px; font-weight: 700; color: #333; }
    .char-card .tagline{ font-size: 12px; color: #999; margin-top: 4px; }
  </style>
</head>
<body>
  <h1>🎙️ IRA Kids Voice Test</h1>
  <p>Select a character and hold the mic button to talk!</p>

  <div class="characters">
    <div class="char-card active" data-character="doro" onclick="selectChar(this)">
      <span class="emoji">🤖</span>
      <div class="name">Doro</div>
      <div class="tagline">Science & Gadgets</div>
    </div>
    <div class="char-card" data-character="chintu" onclick="selectChar(this)">
      <span class="emoji">😄</span>
      <div class="name">Chintu</div>
      <div class="tagline">Fun & Laughter</div>
    </div>
    <div class="char-card" data-character="bheemu" onclick="selectChar(this)">
      <span class="emoji">💪</span>
      <div class="name">Bheemu</div>
      <div class="tagline">Brave & Strong</div>
    </div>
  </div>

  <script>
    function selectChar(el) {
      document.querySelectorAll('.char-card').forEach(c => c.classList.remove('active'));
      el.classList.add('active');
      if (window.kidsVoice) {
        window.kidsVoice.setCharacter(el.dataset.character);
      }
    }
  </script>
  <script src="/static/kids_voice.js"></script>
</body>
</html>
"""
