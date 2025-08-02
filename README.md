# Music Recommendation Telegram Bot 🎵🤖

A Telegram bot that recommends similar songs and provides 30-second previews using AI and Deezer API.

## Features ✨

- **AI-Powered Recommendations**: Gets 5 similar songs based on your input
- **Instant Previews**: Plays 30-second demos of recommended tracks
- **Interactive Interface**: With buttons for easy control
- **Async Implementation**: Fast and responsive user experience
- **Cancellation Support**: Stop recommendations anytime

## How It Works ⚙️

1. User sends a song name
2. Bot queries AI for similar song recommendations
3. For each recommendation, bot finds and sends a 30-second preview from Deezer
4. User can stop the process anytime with the stop button

## Technologies Used 🛠️

- Python 3.x
- `python-telegram-bot` library (v20+)
- AsyncOpenAI (OpenRouter API)
- Deezer API
- `python-dotenv` for environment variables