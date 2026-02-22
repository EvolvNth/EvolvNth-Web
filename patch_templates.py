"""Patch script to fix Template 2 (missing blocks) and Template 7 (missing Itinerary DB)"""
import json
import urllib.request
import urllib.error
import time
import os

API_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Page IDs from the build output
TEMPLATE_2_PAGE = "30e107f0-44d1-8169-aaa2-c981b28f0405"
TEMPLATE_7_PAGE = "30e107f0-44d1-810a-9342-f974f9e051c3"

def api_call(endpoint, data, method="POST"):
    url = f"{BASE_URL}/{endpoint}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {API_TOKEN}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Notion-Version", NOTION_VERSION)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  ERROR {e.code}: {error_body[:500]}")
        return None

def text(content, **annotations):
    t = {"type": "text", "text": {"content": content}}
    if annotations:
        t["annotations"] = annotations
    return t

def heading2(content):
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [text(content)]}}

def paragraph(content, **annotations):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [text(content, **annotations)]}}

def divider():
    return {"object": "block", "type": "divider", "divider": {}}

def callout_rich(emoji, rich_texts, color="blue_background"):
    return {
        "object": "block", "type": "callout",
        "callout": {"icon": {"type": "emoji", "emoji": emoji}, "color": color, "rich_text": rich_texts}
    }

def toggle(title, children=[]):
    return {
        "object": "block", "type": "toggle",
        "toggle": {"rich_text": [text(title)], "children": children}
    }

def bullet(content):
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [text(content)]}}

def todo_block(content, checked=False):
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": [text(content)], "checked": checked}}

def title_prop():
    return {"title": {}}
def rich_text_prop():
    return {"rich_text": {}}
def select_prop(options):
    return {"select": {"options": [{"name": o} for o in options]}}
def number_prop(fmt=None):
    if fmt: return {"number": {"format": fmt}}
    return {"number": {}}
def date_prop():
    return {"date": {}}
def checkbox_prop():
    return {"checkbox": {}}

def e_title(v):
    return {"title": [{"text": {"content": v}}]}
def e_select(v):
    return {"select": {"name": v}}
def e_rich_text(v):
    return {"rich_text": [{"text": {"content": v}}]}
def e_number(v):
    return {"number": v}
def e_checkbox(v):
    return {"checkbox": v}

def append_blocks(page_id, blocks):
    result = api_call("blocks/" + page_id + "/children", {"children": blocks}, "PATCH")
    if result:
        print(f"  Blocks appended: {len(blocks)} blocks")
    return result

def create_database(page_id, title, properties):
    data = {
        "parent": {"type": "page_id", "page_id": page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": properties
    }
    result = api_call("databases", data)
    if result:
        db_id = result["id"]
        print(f"  Database created: {db_id}")
        return db_id
    return None

def add_entry(db_id, properties):
    data = {"parent": {"database_id": db_id}, "properties": properties}
    result = api_call("pages", data)
    if result:
        print(f"    Entry added: ok")
    return result


print("=" * 60)
print("PATCHING TEMPLATES 2 AND 7")
print("=" * 60)

# ============================================================
# PATCH TEMPLATE 2: Append missing blocks (from toggle onwards)
# ============================================================
print("\n--- Patching Template 2: Debt Snowball Calculator ---")
print("  Appending missing Snowball vs Avalanche section and beyond...")

append_blocks(TEMPLATE_2_PAGE, [
    toggle("Which Method is Right for You?", [
        callout_rich("\u2744\uFE0F", [
            text("Snowball Method\n", bold=True),
            text("Pay smallest balance first\n\nPros:\n\u2022 Quick wins build motivation\n\u2022 Psychological momentum\n\u2022 Easier to stick with\n\nCons:\n\u2022 May pay more interest overall\n\nBest for: People who need motivation and quick wins")
        ], "blue_background"),
        callout_rich("\uD83C\uDF0B", [
            text("Avalanche Method\n", bold=True),
            text("Pay highest interest first\n\nPros:\n\u2022 Saves the most money\n\u2022 Mathematically optimal\n\u2022 Less total interest paid\n\nCons:\n\u2022 Slower initial wins\n\nBest for: People motivated by math and long-term savings")
        ], "red_background"),
        callout_rich("\u2705", [
            text("This template uses the Snowball Method ", bold=True),
            text("because research shows that the psychological boost from quick wins makes people 14% more likely to pay off all their debt. The best plan is the one you stick with!")
        ], "green_background")
    ]),

    divider(),
    heading2("Extra Income Ideas"),
    toggle("Ways to Accelerate Your Debt Payoff", [
        paragraph("Every extra dollar goes straight to your target debt!", bold=True),
        bullet("Sell unused items (clothes, electronics, furniture)"),
        bullet("Freelance your professional skills on weekends"),
        bullet("Drive for a rideshare service"),
        bullet("Tutor students in your area of expertise"),
        bullet("Take on overtime at work"),
        bullet("Start a small side business"),
        bullet("Cancel subscriptions and redirect those payments"),
        bullet("Negotiate bills (phone, internet, insurance)"),
        bullet("Apply all windfalls (tax refunds, bonuses, gifts) to debt"),
        divider(),
        callout_rich("\uD83D\uDCB8", [
            text("Quick Math: ", bold=True),
            text("An extra $200/month would cut your payoff timeline by approximately 8 months and save you over $1,200 in interest!")
        ], "yellow_background")
    ]),

    divider(),
    heading2("Net Worth Tracker"),
    paragraph("Your net worth = Assets - Liabilities. Track monthly to see the full picture of your financial health improving as debts decrease."),
    toggle("Monthly Net Worth Log", [
        callout_rich("\uD83D\uDCCA", [
            text("Net Worth Snapshot Template\n", bold=True),
            text("Date: _______________\n\nASSETS:\n\u2022 Checking Account: $___\n\u2022 Savings Account: $___\n\u2022 Investments/401k: $___\n\u2022 Car Value: $___\n\u2022 Other Assets: $___\nTotal Assets: $___\n\nLIABILITIES:\n\u2022 Medical Bill: $___\n\u2022 Credit Card: $___\n\u2022 Personal Loan: $___\n\u2022 Car Loan: $___\n\u2022 Student Loan: $___\nTotal Liabilities: $___\n\nNET WORTH: $___")
        ], "blue_background"),
        divider(),
        paragraph("Monthly Progress:", bold=True),
        bullet("January 2026: Net Worth = $___"),
        bullet("February 2026: Net Worth = $___"),
        bullet("March 2026: Net Worth = $___")
    ]),

    divider(),
    heading2("Debt-Free Countdown"),
    callout_rich("\u23F3", [
        text("Debt-Free Target Date: November 2030\n", bold=True),
        text("Days Remaining: ~1,710 days\nMonths Remaining: ~57 months\nTotal Debt Remaining: $49,750\nTotal Paid Off So Far: $17,250 (25.7%)\n\nAt current pace, you'll be completely debt-free in under 5 years. Every extra dollar accelerates this timeline!")
    ], "green_background"),

    divider(),
    callout_rich("\uD83C\uDFC6", [
        text("Stay the Course\n\n", bold=True),
        text("Debt payoff is a marathon, not a sprint. Every single payment \u2014 big or small \u2014 brings you closer to financial freedom. The snowball method works because it builds unstoppable psychological momentum.\n\nWhen you feel discouraged, look at your Payment History. Look at how far you've come. You're doing something most people never have the courage to start.\n\nYour future self will thank you for every sacrifice you make today. Keep going. \uD83D\uDCAA", italic=True)
    ], "yellow_background")
])

print("  Template 2 patch COMPLETE!")

# ============================================================
# PATCH TEMPLATE 7: Create Itinerary DB with entries
# ============================================================
print("\n--- Patching Template 7: Travel Planner ---")
print("  Creating Itinerary database and adding entries...")

time.sleep(1)

itinerary_db = create_database(TEMPLATE_7_PAGE, "Itinerary", {
    "Activity": title_prop(),
    "Trip": select_prop(["Tokyo Japan", "Barcelona Spain", "New York City", "San Francisco"]),
    "Day": select_prop(["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "Day 8", "Day 9", "Day 10"]),
    "Time": rich_text_prop(),
    "Type": select_prop(["Sightseeing", "Food & Dining", "Transport", "Accommodation", "Shopping", "Adventure", "Relaxation", "Culture"]),
    "Booked?": checkbox_prop(),
    "Cost Estimate": number_prop("dollar"),
    "Address / Location": rich_text_prop(),
    "Notes": rich_text_prop()
})

if itinerary_db:
    itinerary_entries = [
        {"Activity": e_title("Arrive at Narita Airport + Train to Hotel"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 1"), "Time": e_rich_text("2:00 PM - 5:00 PM"), "Type": e_select("Transport"), "Booked?": e_checkbox(True), "Cost Estimate": e_number(35), "Address / Location": e_rich_text("Narita Express to Shinjuku Station"), "Notes": e_rich_text("JR Pass covers this ride. Activate pass at JR counter in airport.")},
        {"Activity": e_title("Explore Shibuya Crossing & Harajuku"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 2"), "Time": e_rich_text("10:00 AM - 2:00 PM"), "Type": e_select("Sightseeing"), "Booked?": e_checkbox(False), "Cost Estimate": e_number(0), "Address / Location": e_rich_text("Shibuya Station to Takeshita Street"), "Notes": e_rich_text("Walk through Shibuya Crossing, Hachiko statue, Meiji Shrine, Harajuku street food.")},
        {"Activity": e_title("Tsukiji Outer Market Breakfast"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 3"), "Time": e_rich_text("7:00 AM - 9:00 AM"), "Type": e_select("Food & Dining"), "Booked?": e_checkbox(False), "Cost Estimate": e_number(30), "Address / Location": e_rich_text("Tsukiji Outer Market"), "Notes": e_rich_text("Fresh sushi, tamagoyaki, and street food. Go early for the best experience.")},
        {"Activity": e_title("Mount Fuji Day Trip"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 5"), "Time": e_rich_text("7:00 AM - 6:00 PM"), "Type": e_select("Adventure"), "Booked?": e_checkbox(True), "Cost Estimate": e_number(80), "Address / Location": e_rich_text("Shinjuku Bus Terminal to Kawaguchiko"), "Notes": e_rich_text("Book bus tickets in advance. Visit Chureito Pagoda for the classic photo.")},
        {"Activity": e_title("Akihabara Electronics & Anime District"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 4"), "Time": e_rich_text("1:00 PM - 6:00 PM"), "Type": e_select("Shopping"), "Booked?": e_checkbox(False), "Cost Estimate": e_number(100), "Address / Location": e_rich_text("Akihabara Station area"), "Notes": e_rich_text("Electronics stores, anime shops, themed cafes. Visit Super Potato for retro games.")}
    ]
    for entry in itinerary_entries:
        add_entry(itinerary_db, entry)
        time.sleep(0.35)
else:
    print("  ERROR: Could not create Itinerary database!")

print("  Template 7 patch COMPLETE!")

print("\n" + "=" * 60)
print("PATCHING COMPLETE!")
print("=" * 60)
