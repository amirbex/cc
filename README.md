# CaReMa - Cafe Restaurant Manager (Accounting Version)

**CaReMa** (Cafe Restaurant Manager) is a Telegram bot designed to assist cafe and restaurant managers with financial and operational data analysis. This accounting version focuses on analyzing purchase, sales, waste, expenses, and material usage data using the Gemini AI API.

## Features
- Upload Excel files for various data categories.
- Generate textual and visual (charts) analyses.
- Review past data and analyses.
- User-friendly menu and natural conversation flow.

## Setup
1. Clone the repository: `git clone https://github.com/amirbex/cc.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` (see `.env` example).
4. Run the bot locally: `python src/telegram_bot.py`

## Deployment
Deployed on Railway. Configure environment variables in Railway and use the `Procfile` for setup.

## Project Structure
- `src/`: Python modules for data processing, Gemini API, visualization, and Telegram bot.
- `temp_data/`: Temporary storage for uploaded Excel files.
- `results/`: Stores analysis reports and visualizations.
