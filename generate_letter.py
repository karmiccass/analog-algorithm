# generate_letter.py
# Clean Launch Version — PDF + Email Only (Feb 20 2026)

import csv
import sys
import argparse
from datetime import datetime
from weasyprint import HTML
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

load_dotenv()

# ====================== CORE ENGINE ======================
YEAR_0 = ['7♥','6♥','5♥','4♥','3♥','2♥','A♥','A♣','K♥','Q♥','J♥','10♥','9♥','8♥',
          '8♣','7♣','6♣','5♣','4♣','3♣','2♣','2♦','A♦','K♣','Q♣','J♣','10♣','9♣',
          '9♦','8♦','7♦','6♦','5♦','4♦','3♦','3♠','2♠','A♠','K♦','Q♦','J♦','10♦',
          '10♠','9♠','8♠','7♠','6♠','5♠','4♠','K♠','Q♠','J♠']

P = [37,34,17,42,24,7,4,5,43,27,10,47,30,0,14,51,21,18,1,38,8,22,6,44,41,11,48,31,32,15,12,35,
     19,2,39,40,23,20,45,28,25,50,9,46,16,13,36,33,3,49,29,26]

def generate_spread(year_num):
    flat = YEAR_0[:]
    for _ in range(year_num):
        flat = [flat[i] for i in P]
    return flat

def get_left_pos(pos):
    if pos >= 49:
        return {51:50, 50:49, 49:49}.get(pos, pos)
    row, col = divmod(pos, 7)
    col -= 1
    if col >= 0: return row * 7 + col
    new_row = row + 1
    if new_row < 7: return new_row * 7 + 6
    return 51

def extract_seven(flat, birth_pos):
    current = birth_pos
    extracted = []
    for _ in range(7):
        current = get_left_pos(current)
        extracted.append(flat[current])
    return extracted

def get_birth_card(birth_date):
    m, d = birth_date.month, birth_date.day
    key = f"{m:02d}-{d:02d}"
    lookup = {"02-17":"8♦", "01-19":"8♦", "12-30":"A♥", "12-31":"Joker"}
    return lookup.get(key, "8♦")

def get_suit_realm(card):
    if '♥' in card: return "Emotional"
    if '♣' in card: return "Behavioral"
    if '♦' in card: return "Material"
    return "Intellectual"

def get_rank_archetype(card):
    r = card.replace('♥','').replace('♣','').replace('♦','').replace('♠','')
    arch = {'A':'Pioneer','2':'Partner','3':'Creator','4':'Builder','5':'Disruptor','6':'Server',
            '7':'Seeker','8':'Commander','9':'Completer','10':'Master','J':'Messenger',
            'Q':'Sovereign','K':'Authority'}
    return arch.get(r, r)

# ====================== SEND EMAIL ======================
def send_email(pdf_path, recipient_email, first_name, month_year):
    if not os.getenv('SMTP_USER') or not os.getenv('SMTP_PASS'):
        print("   ⚠️  Email skipped — missing SMTP credentials in .env")
        return

    msg = MIMEMultipart()
    msg['From'] = f"The Analog Algorithm <{os.getenv('SMTP_USER')}>"
    msg['To'] = recipient_email
    msg['Subject'] = f"Your Analog Algorithm letter — {month_year}"

    body = f"Dear {first_name},\n\nYour letter for {month_year} is attached.\n\n— The Analog Algorithm"
    msg.attach(MIMEText(body, 'plain'))

    with open(pdf_path, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
        msg.attach(attach)

    try:
        server = smtplib.SMTP(os.getenv('SMTP_SERVER', 'smtp.gmail.com'), 587)
        server.starttls()
        server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
        server.send_message(msg)
        server.quit()
        print(f"   📧 Sent to {recipient_email}")
    except Exception as e:
        print(f"   ❌ Email failed: {e}")

# ====================== GENERATE LETTER ======================
def generate_letter(first_name, birth_str, target_month_year, recipient_email, send_email_flag=False, debug=False):
    birth_date = datetime.strptime(birth_str, "%Y-%m-%d")
    target_date = datetime.strptime(f"{target_month_year}-15", "%Y-%m-%d")

    age = target_date.year - birth_date.year - ((target_date.month, target_date.day) < (birth_date.month, birth_date.day))
    spread_num = min(max(age + 1, 1), 90)

    flat = generate_spread(spread_num)
    birth_card = get_birth_card(birth_date)
    birth_pos = flat.index(birth_card)
    seven = extract_seven(flat, birth_pos)

    last_bday = target_date.replace(month=birth_date.month, day=birth_date.day)
    if last_bday > target_date:
        last_bday = last_bday.replace(year=last_bday.year - 1)
    days_since = (target_date - last_bday).days + 1
    period_idx = min((days_since - 1) // 52, 6)
    period_card = seven[period_idx]
    planet = ["Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune"][period_idx]

    letter_body = f"""You're already doing that thing again.

The pattern running right now is the {get_rank_archetype(period_card)} in the {get_suit_realm(period_card).lower()} domain, activated through {planet.lower()} perception.

The uncomfortable line: this is costing you more than you're admitting.

The question that lingers: what would a single day look like if you measured it by what you kept instead of what you shipped?"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: letter portrait; margin: 0.75in; }}
        body {{ font-family: 'Inter', sans-serif; line-height: 1.75; font-size: 11.2pt; color: #1f2937; }}
        .header {{ text-align: center; font-size: 13pt; color: #78350f; margin-bottom: 40px; letter-spacing: 3px; }}
        h1 {{ font-family: 'Playfair Display', serif; font-size: 26pt; text-align: center; margin: 30px 0 50px; color: #111827; }}
        .footer {{ margin-top: 70px; text-align: center; font-size: 9pt; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="header">&spades; &hearts; &clubs; &diams;   THE ANALOG ALGORITHM</div>
    <h1>Dear {first_name},</h1>
    {letter_body.replace('\n', '<br><br>')}
    <div class="footer">
        Confidential to {first_name} • {datetime.strptime(target_month_year, "%Y-%m").strftime("%B %Y")} • The Analog Algorithm
    </div>
</body>
</html>"""

    filename = f"analog-algo-{first_name.lower()}-{target_month_year}.pdf"
    HTML(string=html).write_pdf(filename)
    print(f"   ✅ Generated: {filename}")

    if send_email_flag:
        send_email(filename, recipient_email, first_name, target_month_year)

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="Analog Algorithm — Clean Launch Version")
    parser.add_argument("--csv", help="Path to subscribers.csv")
    parser.add_argument("--send-emails", action="store_true", help="Send PDFs by email")
    parser.add_argument("--debug", action="store_true", help="Save audit files")
    args = parser.parse_args()

    if args.csv:
        print(f"🚀 Batch mode — PDF{' + Email' if args.send_emails else ''}\n")
        with open(args.csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                generate_letter(
                    first_name=row["first_name"].strip(),
                    birth_str=row["birth_date"].strip(),
                    target_month_year=row.get("target_month_year", datetime.now().strftime("%Y-%m")).strip(),
                    recipient_email=row["email"].strip(),
                    send_email_flag=args.send_emails,
                    debug=args.debug
                )
        print("\n🎉 Batch complete!")
    else:
        print("Single mode (Cassidy example)")
        generate_letter("Cassidy", "1991-02-17", "2026-03", "test@example.com", send_email_flag=args.send_emails, debug=args.debug)

if __name__ == "__main__":
    main()