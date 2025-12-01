# 🧪 Frankenstein's Forge

A multimodal AI web application that combines images, audio, and text to generate creative, actionable ideas using Google's Gemini 2.0 Flash model. For a Kiro competition.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal)

## ✨ Features

### Core Functionality
- 🖼️ **Image Upload** - Drag & drop or select images (JPEG/PNG)
- 🎤 **Voice Recording** - Record up to 30 seconds with live waveform visualization
- 📝 **Text Input** - Describe your vision in your own words
- 🤖 **AI Generation** - Multimodal idea generation using Gemini 2.0 Flash
- 📋 **Implementation Steps** - Get detailed step-by-step plans for your ideas

### Enhanced UX
- 👁️ **Image Preview** - See your uploaded image before submission
- 🔊 **Audio Playback** - Review your recording before generating
- 📊 **Waveform Visualization** - Real-time audio visualization during recording
- 📚 **History System** - Browse and revisit your previous generations (stored locally)
- 💾 **Export Options** - Download ideas as JSON files
- 🔄 **Regeneration** - Create variations of existing ideas
- 🎨 **Animated Background** - Dynamic Perlin noise canvas

### User Experience
- 🌙 Dark theme optimized for extended use
- 📱 Fully responsive mobile design
- ⚡ Fast and lightweight
- 🔒 Privacy-focused (history stored locally)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google API Key (for Gemini)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd frankensteins-forge
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install fastapi uvicorn python-dotenv google-genai python-multipart
```

4. **Set up environment variables**
Create a `.env` file:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

5. **Run the application**
```bash
python main.py
```

6. **Open your browser**
Navigate to `http://localhost:8000`

## 📖 Usage

1. **Upload an Image** - Click "Choose File" or drag & drop an image
2. **Record Audio** - Click the microphone button and speak for up to 30 seconds
3. **Add Description** - Type your idea or context in the text area
4. **Generate** - Click "⚡ Generate Idea" and wait for AI magic
5. **Review & Export** - Copy, export, or generate implementation steps
6. **Browse History** - Click "📚 History" to see past generations

## 🏗️ Architecture

```
frankensteins-forge/
├── app.py                 # FastAPI backend
├── utils/
│   └── forge.py          # Gemini AI wrapper
├── static/
│   ├── index.html        # Frontend UI
│   ├── script.js         # Client-side logic
│   └── style.css         # Styling
├── .env                  # Environment variables
└── README.md            # Documentation
```

## 🔌 API Endpoints

### `POST /generate`
Generate an idea from multimodal inputs
- **Body**: `multipart/form-data`
  - `image`: Image file (JPEG/PNG)
  - `audio`: Audio file (WAV/MP3/WebM)
  - `text`: Text description
- **Response**: Generated idea with metadata

### `POST /generate-steps`
Generate implementation steps for an idea
- **Body**: `application/json`
  - `idea`: The idea to break down
- **Response**: Detailed step-by-step plan

### `POST /refine-idea`
Refine or create variations of an idea
- **Body**: `application/json`
  - `idea`: Original idea
  - `type`: "variation" | "simpler" | "more_ambitious"
- **Response**: Refined idea

### `GET /health`
Health check endpoint

### `GET /stats`
Get API statistics and features

## 🎨 Customization

### Modify AI Prompts
Edit `utils/forge.py` to customize how ideas are generated:
```python
prompt = f"""Your custom prompt here..."""
```

### Adjust Recording Time
Change `MAX_RECORDING_TIME` in `static/script.js`:
```javascript
const MAX_RECORDING_TIME = 60; // 60 seconds
```

### Theme Colors
Modify CSS variables in `static/style.css`:
```css
:root {
    --primary-bg: #0a0a0a;
    --accent-color: #4ade80;
}
```

## 🔒 Privacy & Security

- All history is stored locally in browser localStorage
- No data is sent to external servers except Google's Gemini API
- API keys are stored securely in `.env` (never commit this file)
- File size limits prevent abuse (10MB images, 20MB audio)

## 🐛 Troubleshooting

**Microphone not working?**
- Check browser permissions
- Ensure HTTPS or localhost
- Try a different browser

**API errors?**
- Verify your `GOOGLE_API_KEY` in `.env`
- Check API quota limits
- Ensure internet connection

**Files not uploading?**
- Check file size limits
- Verify file format (JPEG/PNG for images, WAV/MP3/WebM for audio)

## 🚧 Future Enhancements

- [ ] Multiple image support
- [ ] Idea categories and tagging
- [ ] Collaboration features
- [ ] Cloud history sync
- [ ] Light theme toggle
- [ ] Advanced audio effects
- [ ] PDF export with formatting
- [ ] Social sharing

## 📄 License

MIT License - feel free to use and modify!

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Google Gemini 2.0 Flash](https://deepmind.google/technologies/gemini/)
- Inspired by creative AI applications

---

**Made with ⚡ by [Your Name]**
