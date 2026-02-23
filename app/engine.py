import datetime
import math

# ====================== DATA CONSTANTS ======================
# Standard "Life Spread" (Year 0)
YEAR_0 = [
    '7♥','6♥','5♥','4♥','3♥','2♥','A♥',  # Row 0: Mercury (Indices 0-6)
    'A♣','K♥','Q♥','J♥','10♥','9♥','8♥', # Row 1: Venus
    '8♣','7♣','6♣','5♣','4♣','3♣','2♣',  # Row 2: Mars
    '2♦','A♦','K♣','Q♣','J♣','10♣','9♣', # Row 3: Jupiter
    '9♦','8♦','7♦','6♦','5♦','4♦','3♦',  # Row 4: Saturn
    '3♠','2♠','A♠','K♦','Q♦','J♦','10♦', # Row 5: Uranus
    '10♠','9♠','8♠','7♠','6♠','5♠','4♠', # Row 6: Neptune
    'K♠','Q♠','J♠'                       # Crown (Indices 49-51)
]

# Quadration Permutation (Standard 52-card shuffle)
P = [
    37,34,17,42,24,7,4,   # 0-6
    5,43,27,10,47,30,0,   # 7-13
    14,51,21,18,1,38,8,   # 14-20
    22,6,44,41,11,48,31,  # 21-27
    32,15,12,35,19,2,39,  # 28-34
    40,23,20,45,28,25,50, # 35-41
    9,46,16,13,36,33,3,   # 42-48
    49,29,26              # 49-51 (Crown)
]

ROWS = ['Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune']
NO_DISP_ENV = {'K♠', 'J♥', '8♣', 'A♣', '2♥', '7♦', '9♥'}

# ====================== CORE LOGIC ======================

def get_birth_card(month: int, day: int):
    """Calculates birth card from month/day using Solar Value."""
    sv = 55 - (month * 2 + day)
    if sv <= 0: return "Joker", 0
    suits = ['♥','♣','♦','♠']
    ranks = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    # sv 1 = A♥, sv 52 = K♠
    return f"{ranks[(sv-1)%13]}{suits[(sv-1)//13]}", sv

def get_spread_year(birth_month: int, birth_day: int, birth_year: int, target_date: datetime.date):
    """Calculates the Spread Year (Age + 1) and day of year."""
    try:
        last_bday = datetime.date(target_date.year, birth_month, birth_day)
    except ValueError: # Leap year case (Feb 29)
        last_bday = datetime.date(target_date.year, 3, 1) # Treat as Mar 1 for non-leap years

    if last_bday > target_date:
        try:
            last_bday = datetime.date(target_date.year - 1, birth_month, birth_day)
        except ValueError:
            last_bday = datetime.date(target_date.year - 1, 3, 1)

    age = last_bday.year - birth_year
    days_since = (target_date - last_bday).days + 1
    spread_year = min(max(age + 1, 1), 90)
    return age, days_since, spread_year, last_bday

def generate_yearly_spread_data(spread_year: int):
    """Generates the grid and crown for a specific spread year."""
    # Start with Year 0
    flat = YEAR_0[:]
    
    # Shuffle N times
    # Note: spread_year 0 = Life Spread. spread_year 1 = First shuffle.
    # The spec implies `data[str(spread_year)]` where 0 is base.
    # If spread_year is 1 (Age 0), is it Year 0 or Year 1?
    # Spec: "Spread Year = age + 1". So Age 0 = Spread Year 1.
    # Usually Age 0 lives in the Life Spread (Year 0). 
    # But let's follow the logic: "Extract exactly spread_year cards".
    # If spread_year = 1, we extract 1 card.
    # The spread we LOOK AT depends on the system.
    # Spec says: "yearly = data[str(spread_year)]". 
    # This implies there IS a spread for Year 36.
    # I will assume we shuffle `spread_year` times from Year 0.
    
    for _ in range(spread_year):
        flat = [flat[i] for i in P]
        
    # Map to Grid and Crown
    # Grid: 7 rows of 7 (indices 0-48)
    grid = {}
    for r_idx, row_name in enumerate(ROWS):
        start = r_idx * 7
        end = start + 7
        # Python lists are left-to-right, but spec says Col 0 is Neptune (Left) -> Col 6 Mercury (Right)?
        # Spec: "Cols (left→right, index 0→6): Neptune...Mercury"
        # YEAR_0 list: Index 0 is 7♥ (Mercury/Mercury). 
        # Usually Merc/Merc is Top Right.
        # If Col 6 is Mercury (Right), then Index 0 should be at Col 6?
        # Let's look at `extract_chain`:
        # "In grid, col == 0 (Left), row < 6: row += 1, col = 6 (Right)"
        # This scans rows Right-to-Left (6->0), Top-to-Bottom.
        # So Index 0 should be at Col 6 (Right).
        # Index 1 at Col 5... Index 6 at Col 0.
        row_cards = flat[start:end]
        # Reverse the row to map indices 0..6 to Cols 6..0? 
        # Or does grid[row][0] mean Col 0?
        # Spec: "grid[row_name][col_index]"
        # If I want Index 0 to be Col 6:
        # grid[row][6] = flat[start]
        # grid[row][0] = flat[end-1]
        # Let's construct it so grid[row_name] is a list where index = col.
        # So we need to REVERSE the slice from flat if flat is sorted Right-to-Left.
        # YEAR_0: 7♥ is Merc/Merc.
        # If Merc/Merc is Col 6, then flat[0] -> Col 6.
        # flat[6] -> Col 0.
        # So grid row list should be flat[start:end] REVERSED.
        # UPDATE: Reversed logic was incorrect for index mapping. 
        # Col 0 = Mercury (Right), Col 6 = Neptune (Left).
        grid[row_name] = row_cards

    # Crown: Indices 49-51.
    # Spec: "crown = [Saturn_card(0), Jupiter_card(1), Mars_card(2)]"
    # YEAR_0: K♠(49), Q♠(50), J♠(51).
    # Usually K♠ is Saturn(0)? Q♠ Jupiter? J♠ Mars?
    # Let's assume order is preserved: crown[0] = flat[49].
    crown = flat[49:52]
    
    return grid, crown

def extract_chain(grid, crown, birth_card, spread_year):
    """Extracts the planetary period chain."""
    r = c = None
    in_crown_anchor = False
    anchor_cidx = None

    # Find Anchor
    for ri, rn in enumerate(ROWS):
        if birth_card in grid[rn]:
            r = ri
            c = grid[rn].index(birth_card)
            break
            
    if r is None:
        if birth_card in crown:
            in_crown_anchor = True
            anchor_cidx = crown.index(birth_card)

    results = []
    in_crown = in_crown_anchor
    
    # State variables for traversal
    curr_r, curr_c = r, c
    curr_cidx = anchor_cidx

    # Logic from spec
    # "Starting immediately left of the anchor"
    # We simulate steps.
    
    # Helper to move one step left
    def move_step(loc_in_crown, loc_r, loc_c, loc_cidx):
        if loc_in_crown:
            if loc_cidx > 0:
                return True, None, None, loc_cidx - 1 # Stay in crown, move left
            else:
                return False, 0, 6, None # Exit crown to Merc(0) Col 6
        else:
            if loc_c > 0:
                return False, loc_r, loc_c - 1, None # Grid move left
            elif loc_r < 6:
                return False, loc_r + 1, 6, None # Grid drop row, reset to right
            else:
                return True, None, None, 2 # Enter crown at index 2 (Mars)

    # Initial move (Start immediately left)
    in_crown, curr_r, curr_c, curr_cidx = move_step(in_crown, curr_r, curr_c, curr_cidx)

    while len(results) < spread_year:
        # Collect card at current position
        if in_crown:
            results.append(crown[curr_cidx])
        else:
            results.append(grid[ROWS[curr_r]][curr_c])
            
        # Move to next for next iteration? 
        # Wait, loop condition is len < spread_year.
        # We collect, THEN move? Or Move THEN collect?
        # Spec: "Starting immediately left... collect cards... extract spread_year cards total"
        # So we collect the one we just moved to.
        # Then we need to move AGAIN for the next one?
        # Yes.
        if len(results) < spread_year:
             in_crown, curr_r, curr_c, curr_cidx = move_step(in_crown, curr_r, curr_c, curr_cidx)

    return results

def get_displacement_environment(life_grid, life_crown, yearly_grid, yearly_crown, birth_card):
    # Displacement: Year 0 card at birth card's current position
    disp = None
    env = None
    
    # Find current position of birth card
    curr_r = curr_c = curr_cidx = None
    is_crown = False
    
    for ri, rn in enumerate(ROWS):
        if birth_card in yearly_grid[rn]:
            curr_r = ri
            curr_c = yearly_grid[rn].index(birth_card)
            break
    if curr_r is None:
        if birth_card in yearly_crown:
            is_crown = True
            curr_cidx = yearly_crown.index(birth_card)
            
    if is_crown:
        disp = life_crown[curr_cidx]
    elif curr_r is not None:
        disp = life_grid[ROWS[curr_r]][curr_c]
        
    # Environment: Yearly card at birth card's Year 0 position
    # Find Year 0 position
    y0_r = y0_c = y0_cidx = None
    y0_is_crown = False
    
    for ri, rn in enumerate(ROWS):
        if birth_card in life_grid[rn]:
            y0_r = ri
            y0_c = life_grid[rn].index(birth_card)
            break
    if y0_r is None:
        if birth_card in life_crown:
            y0_is_crown = True
            y0_cidx = life_crown.index(birth_card)
            
    if y0_is_crown:
        env = yearly_crown[y0_cidx]
    elif y0_r is not None:
        env = yearly_grid[ROWS[y0_r]][y0_c]
        
    return disp, env

# ====================== INTERPRETATION HELPERS ======================

def get_suit_realm(card: str):
    if not card: return "Unknown"
    if '♥' in card: return "Emotional"
    if '♣' in card: return "Behavioral"
    if '♦' in card: return "Material"
    return "Intellectual"

def get_rank_archetype(card: str):
    if not card: return "Unknown"
    r = card.replace('♥','').replace('♣','').replace('♦','').replace('♠','')
    arch = {
        'A':'Pioneer','2':'Partner','3':'Creator','4':'Builder','5':'Disruptor',
        '6':'Server','7':'Seeker','8':'Commander','9':'Completer','10':'Master',
        'J':'Messenger','Q':'Sovereign','K':'Authority'
    }
    return arch.get(r, r)

# ====================== API ENTRY POINT ======================

def calculate_letter_data(first_name, birth_year, birth_month, birth_day, target_date_str="2026-03-15"):
    target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
    
    # 1. Birth Card
    bc, sv = get_birth_card(birth_month, birth_day)
    if bc == "Joker":
        return {"error": "Joker cannot receive a spread."}
        
    # 2. Spread Year
    age, days_since, spread_year, last_bday = get_spread_year(birth_month, birth_day, birth_year, target_date)
    
    # 3. Load Spreads (Life and Current)
    life_grid, life_crown = generate_yearly_spread_data(0)
    yearly_grid, yearly_crown = generate_yearly_spread_data(spread_year)
    
    # 4. Extract Chain
    chain = extract_chain(yearly_grid, yearly_crown, bc, spread_year)
    
    # 5. Assign Cards
    # Active period
    # Days 1-52: Mercury (idx 0), 53-104: Venus (idx 1)...
    # Use days_since to find index
    period_idx = min((days_since - 1) // 52, 6)
    period_card = chain[period_idx]
    planet = ROWS[period_idx]
    
    # Year Long
    long_range = chain[spread_year - 1] # Last card extracted
    pluto = chain[7] if spread_year >= 8 else None
    result = chain[8] if spread_year >= 9 else None
    
    # Disp/Env
    disp, env = get_displacement_environment(life_grid, life_crown, yearly_grid, yearly_crown, bc)
    if bc in NO_DISP_ENV:
        disp = env = None
        
    return {
        "subscriber": first_name,
        "birth_card": bc,
        "age": age,
        "spread_year": spread_year,
        "period": {
            "card": period_card,
            "planet": planet,
            "days_since": days_since
        },
        "year_long": {
            "long_range": long_range,
            "pluto": pluto,
            "result": result,
            "displacement": disp,
            "environment": env
        }
    }

if __name__ == "__main__":
    # Test Case 1: 8♦ (Feb 17 1991), effective Feb 21 2026
    # Expect: Spread Year 36. Period 7♦ (Mercury). LR 4♦. Pluto 3♦. Result K♦. Disp 6♦. Env 8♠.
    data = calculate_letter_data("Cassidy", 1991, 2, 17, "2026-02-21")
    print("Test Case 1 (8♦):", data)
