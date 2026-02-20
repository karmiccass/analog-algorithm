# Analog Algorithm

**A solar calendar encoded in a standard 52-card deck.**

Built from the original 1893 mathematics: 52 weeks, 4 seasons, Julian leap-year correction via the Joker (5/4 = 1.25), and a fixed permutation that generates 90 unique yearly spreads in a helical pattern.

### Features

- **Live Web Calculator** — instant personal year or personal week reading (no backend)
- **Monthly Letter Engine** — generates beautiful one-page print-ready PDFs
- **Batch + Email** — send all letters automatically
- Pure math. No databases. No lookup tables.

### Quick Start

```bash
# 1. Clone
git clone https://github.com/YOURUSERNAME/analog-algorithm.git
cd analog-algorithm

# 2. Install
pip install -r requirements.txt

# 3. Add your email credentials (Gmail app password recommended)
cp .env.example .env
# edit .env with your SMTP details

# 4. Run single test
python generate_letter.py

# 5. Run full batch + email
python generate_letter.py --csv subscribers.csv --send-emails