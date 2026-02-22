"""
Build Personal CRM — Standalone Notion Template
----------------------------------------------------------
A free giveaway template expanding on the Life OS CRM section.
Full-featured relationship management for personal & professional networks.
"""
import json
import urllib.request
import urllib.error
import time
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
BASE_URL = "https://api.notion.com/v1"
PARENT_PAGE = "30e107f0-44d1-8014-abd0-c449748c499e"
NOTION_VERSION = "2022-06-28"


# ============================================================
# API & BLOCK HELPERS (same as build_templates.py)
# ============================================================

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

def heading1(content):
    return {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [text(content, bold=True)]}}

def heading2(content):
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [text(content)]}}

def heading3(content):
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": [text(content)]}}

def paragraph(content, **annotations):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [text(content, **annotations)]}}

def paragraph_rich(rich_texts, **kwargs):
    block = {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_texts}}
    if kwargs.get("color"):
        block["paragraph"]["color"] = kwargs["color"]
    return block

def divider():
    return {"object": "block", "type": "divider", "divider": {}}

def callout(emoji, content, color="blue_background", children=None):
    block = {
        "object": "block",
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": emoji},
            "color": color,
            "rich_text": [text(content)]
        }
    }
    if children:
        block["callout"]["children"] = children
    return block

def callout_rich(emoji, rich_texts, color="blue_background", children=None):
    block = {
        "object": "block",
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": emoji},
            "color": color,
            "rich_text": rich_texts
        }
    }
    if children:
        block["callout"]["children"] = children
    return block

def toggle(content, children):
    return {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [text(content, bold=True)],
            "children": children
        }
    }

def bullet(content):
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [text(content)]}}

def numbered(content):
    return {"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": [text(content)]}}

def todo_block(content, checked=False):
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": [text(content)], "checked": checked}}

def quote_block(content):
    return {"object": "block", "type": "quote", "quote": {"rich_text": [text(content)]}}

def column_list(columns):
    return {
        "object": "block",
        "type": "column_list",
        "column_list": {
            "children": [
                {"object": "block", "type": "column", "column": {"children": col}}
                for col in columns
            ]
        }
    }

def table_of_contents(color="default"):
    return {"object": "block", "type": "table_of_contents", "table_of_contents": {"color": color}}

# Property schema helpers
def select_prop(options):
    return {"select": {"options": [{"name": o} for o in options]}}

def multi_select_prop(options):
    return {"multi_select": {"options": [{"name": o} for o in options]}}

def number_prop(fmt=None):
    if fmt:
        return {"number": {"format": fmt}}
    return {"number": {}}

def date_prop():
    return {"date": {}}

def rich_text_prop():
    return {"rich_text": {}}

def url_prop():
    return {"url": {}}

def checkbox_prop():
    return {"checkbox": {}}

def title_prop():
    return {"title": {}}

# Entry value helpers
def e_title(val):
    return {"title": [{"text": {"content": val}}]}

def e_select(val):
    return {"select": {"name": val}}

def e_multi_select(vals):
    return {"multi_select": [{"name": v} for v in vals]}

def e_number(val):
    return {"number": val}

def e_date(val, end=None):
    d = {"date": {"start": val}}
    if end:
        d["date"]["end"] = end
    return d

def e_rich_text(val):
    return {"rich_text": [{"text": {"content": val}}]}

def e_url(val):
    return {"url": val}

def e_checkbox(val):
    return {"checkbox": val}

# Page & database creation
def create_page(title, emoji, children):
    data = {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE},
        "icon": {"type": "emoji", "emoji": emoji},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        },
        "children": children
    }
    result = api_call("pages", data)
    if result:
        print(f"  Page created: {result['id']}")
        return result["id"]
    return None

def create_database(parent_id, title, properties):
    data = {
        "parent": {"type": "page_id", "page_id": parent_id},
        "title": [{"text": {"content": title}}],
        "is_inline": True,
        "properties": properties
    }
    result = api_call("databases", data)
    if result:
        print(f"  Database created: {result['id']}")
        return result["id"]
    return None

def add_entry(db_id, properties):
    data = {
        "parent": {"database_id": db_id},
        "properties": properties
    }
    result = api_call("pages", data)
    if result:
        print(f"    Entry added")
    return result

def append_blocks(page_id, children):
    data = {"children": children}
    result = api_call(f"blocks/{page_id}/children", data, "PATCH")
    if result:
        print(f"  Blocks appended: {len(children)} blocks")
    return result


# ============================================================
# BUILD PERSONAL CRM TEMPLATE
# ============================================================

print("=" * 60)
print("BUILDING: Personal CRM — Relationship Manager")
print("=" * 60)

# --- Create the page ---
page_id = create_page("Personal CRM — Relationship Manager", "🤝", [
    heading1("🤝 Personal CRM — Relationship Manager"),
    paragraph("Your relationships are your most valuable asset. This template helps you nurture every connection — from family and close friends to mentors, colleagues, and professional contacts — so no one falls through the cracks.", italic=True, color="gray"),

    divider(),

    table_of_contents(),

    divider(),

    # --- Quick Start Guide ---
    callout_rich("🚀", [
        text("Quick Start Guide\n\n", bold=True),
        text("1. Add your key contacts to the "),
        text("Contacts & Network", bold=True),
        text(" database below\n"),
        text("2. Set follow-up dates so you never lose touch\n"),
        text("3. Log interactions in the "),
        text("Interaction Log", bold=True),
        text(" after every meaningful conversation\n"),
        text("4. Check the "),
        text("Relationship Dashboard", bold=True),
        text(" weekly to see who needs attention\n"),
        text("5. Use "),
        text("Important Dates", bold=True),
        text(" to never miss a birthday or anniversary")
    ], "blue_background"),

    divider(),

    # --- Why a Personal CRM? ---
    heading2("💡 Why a Personal CRM?"),
])
time.sleep(0.5)

if not page_id:
    print("FATAL: Could not create page. Exiting.")
    exit(1)

# --- Philosophy section ---
append_blocks(page_id, [
    column_list([
        [
            callout_rich("🔗", [
                text("The Problem\n", bold=True),
                text("You meet amazing people — at work, at events, through friends — and then life gets busy. You forget to follow up. Birthdays slip by. That mentor you promised to email? It's been 4 months. Relationships fade not because you don't care, but because you don't have a system.")
            ], "red_background")
        ],
        [
            callout_rich("✨", [
                text("The Solution\n", bold=True),
                text("A Personal CRM gives you a system for the most important thing in life: your relationships. Track who matters, when you last connected, what you talked about, and when to reach out next. Turn good intentions into consistent action.")
            ], "green_background")
        ]
    ]),

    divider(),

    callout_rich("🌊", [
        text("The Nth-Order Effect\n", bold=True),
        text("Following up consistently → stronger relationships → more opportunities → a richer life. One system for staying in touch cascades into career growth, deeper friendships, and a support network that compounds over years.")
    ], "purple_background"),

    divider(),

    # --- Relationship Dashboard ---
    heading2("📊 Relationship Dashboard"),
    paragraph("Your weekly check-in. Scan this dashboard to see who needs attention, upcoming important dates, and your relationship health at a glance."),
])
time.sleep(0.5)

# --- Dashboard callouts ---
append_blocks(page_id, [
    column_list([
        [
            callout_rich("🔴", [
                text("Overdue Follow-Ups\n", bold=True),
                text("Check the Contacts database below.\nFilter by: Next Follow-Up < Today\n\nThese are relationships at risk.\nReach out today — even a quick text\ncounts more than silence.")
            ], "red_background")
        ],
        [
            callout_rich("🟡", [
                text("This Week's Follow-Ups\n", bold=True),
                text("Filter by: Next Follow-Up = This Week\n\nThese are your priority touchpoints.\nSchedule time to connect.\nReference your last interaction notes\nfor a personal opener.")
            ], "yellow_background")
        ],
        [
            callout_rich("🟢", [
                text("Recently Connected\n", bold=True),
                text("Filter by: Last Contact = Past 7 Days\n\nGreat work staying in touch!\nLog any notes while they're fresh.\nSet the next follow-up date\nbefore you forget.")
            ], "green_background")
        ]
    ]),

    divider(),

    # --- Contacts & Network database header ---
    heading2("👥 Contacts & Network"),
    paragraph("Your complete relationship database. Every person who matters to your personal or professional life belongs here."),
])
time.sleep(0.5)

# --- Contacts & Network Database ---
contacts_db = create_database(page_id, "Contacts & Network", {
    "Name": title_prop(),
    "Relationship": select_prop([
        "Family",
        "Close Friend",
        "Friend",
        "Colleague",
        "Mentor",
        "Mentee",
        "Professional Contact",
        "Client",
        "Acquaintance"
    ]),
    "Circle": select_prop([
        "🔴 Inner Circle (Weekly)",
        "🟠 Close (Bi-weekly)",
        "🟡 Regular (Monthly)",
        "🟢 Casual (Quarterly)",
        "🔵 Distant (Yearly)"
    ]),
    "Company / Context": rich_text_prop(),
    "How We Met": rich_text_prop(),
    "Last Contact": date_prop(),
    "Next Follow-Up": date_prop(),
    "Birthday": date_prop(),
    "Preferred Channel": select_prop([
        "Text",
        "Call",
        "Email",
        "In-Person",
        "Social Media (DM)",
        "Video Call"
    ]),
    "Interests & Topics": rich_text_prop(),
    "Notes": rich_text_prop(),
    "LinkedIn / Social": url_prop()
})

if contacts_db:
    contact_entries = [
        {
            "Name": e_title("Mom & Dad"),
            "Relationship": e_select("Family"),
            "Circle": e_select("🔴 Inner Circle (Weekly)"),
            "Last Contact": e_date("2026-02-20"),
            "Next Follow-Up": e_date("2026-02-27"),
            "Preferred Channel": e_select("Call"),
            "Interests & Topics": e_rich_text("Dad: golf, home improvement, retirement planning. Mom: book club, gardening, grandkids updates."),
            "Notes": e_rich_text("Weekly Sunday call tradition. Ask about dad's golf tournament and mom's book club. They're planning a trip to Italy this summer — send them that restaurant list.")
        },
        {
            "Name": e_title("Jake — Best Friend"),
            "Relationship": e_select("Close Friend"),
            "Circle": e_select("🔴 Inner Circle (Weekly)"),
            "Last Contact": e_date("2026-02-18"),
            "Next Follow-Up": e_date("2026-03-01"),
            "Birthday": e_date("2026-07-15"),
            "Preferred Channel": e_select("In-Person"),
            "How We Met": e_rich_text("College roommate, freshman year 2018"),
            "Interests & Topics": e_rich_text("Hiking, craft beer, fantasy football, career moves"),
            "Notes": e_rich_text("Starting a new job at Stripe next month — congratulate him! Planning a weekend hiking trip to Shenandoah. Owes me dinner from our bet.")
        },
        {
            "Name": e_title("Sarah Kim — Manager"),
            "Relationship": e_select("Colleague"),
            "Circle": e_select("🟠 Close (Bi-weekly)"),
            "Company / Context": e_rich_text("Current Company — Engineering"),
            "Last Contact": e_date("2026-02-19"),
            "Next Follow-Up": e_date("2026-03-05"),
            "Preferred Channel": e_select("In-Person"),
            "How We Met": e_rich_text("She became my manager when I joined the platform team in 2024"),
            "Interests & Topics": e_rich_text("Leadership, team culture, hiking, her daughter's soccer"),
            "Notes": e_rich_text("Incredibly supportive of my promotion goals. Schedule monthly 1:1 outside of regular meetings. She mentioned wanting book recommendations on systems thinking — send her 'Thinking in Systems' by Meadows.")
        },
        {
            "Name": e_title("Dr. Patel — Mentor"),
            "Relationship": e_select("Mentor"),
            "Circle": e_select("🟡 Regular (Monthly)"),
            "Company / Context": e_rich_text("University / Advisory — CS Department"),
            "Last Contact": e_date("2026-02-01"),
            "Next Follow-Up": e_date("2026-03-01"),
            "Preferred Channel": e_select("Email"),
            "How We Met": e_rich_text("Graduate advisor, introduced through Prof. Williams in 2020"),
            "Interests & Topics": e_rich_text("AI/ML research, career strategy, academic publishing, Indian classical music"),
            "Notes": e_rich_text("Monthly check-in. Incredible career advice — introduced me to two valuable contacts last year. Discuss: side project progress, whether to pursue management vs. IC track. His birthday is April 12 — send a thoughtful note.")
        },
        {
            "Name": e_title("Lisa Chen — Conference Contact"),
            "Relationship": e_select("Professional Contact"),
            "Circle": e_select("🟢 Casual (Quarterly)"),
            "Company / Context": e_rich_text("VP of Product at TechCorp"),
            "Last Contact": e_date("2026-01-15"),
            "Next Follow-Up": e_date("2026-04-15"),
            "Preferred Channel": e_select("Email"),
            "How We Met": e_rich_text("Met at React Summit 2025 — great conversation about developer tools"),
            "Interests & Topics": e_rich_text("Developer experience, product strategy, startup ecosystem, running"),
            "Notes": e_rich_text("She's hiring for a senior PM role — could be a future opportunity. Offered to introduce me to their CTO. Send her that article about developer productivity I mentioned."),
            "LinkedIn / Social": e_url("https://linkedin.com/in/example")
        },
        {
            "Name": e_title("Marcus — Gym Buddy"),
            "Relationship": e_select("Friend"),
            "Circle": e_select("🟠 Close (Bi-weekly)"),
            "Last Contact": e_date("2026-02-21"),
            "Next Follow-Up": e_date("2026-03-07"),
            "Birthday": e_date("2026-11-03"),
            "Preferred Channel": e_select("Text"),
            "How We Met": e_rich_text("Met at the gym, started spotting each other in 2025"),
            "Interests & Topics": e_rich_text("Powerlifting, nutrition, motorcycles, real estate investing"),
            "Notes": e_rich_text("Training for a powerlifting meet in April — ask about his prep. He recommended a great protein powder brand. Considering buying a rental property — share that podcast episode about first-time landlords.")
        },
        {
            "Name": e_title("Aunt Rosa"),
            "Relationship": e_select("Family"),
            "Circle": e_select("🟡 Regular (Monthly)"),
            "Last Contact": e_date("2026-02-10"),
            "Next Follow-Up": e_date("2026-03-10"),
            "Birthday": e_date("2026-08-22"),
            "Preferred Channel": e_select("Call"),
            "Interests & Topics": e_rich_text("Cooking, family history, her grandchildren, church events"),
            "Notes": e_rich_text("She's the family historian — ask about grandpa's story from the war. Always sends the best birthday cards. Her famous tamale recipe is still unmatched. Visit her next time I'm in town.")
        },
        {
            "Name": e_title("Alex Rivera — Co-founder Idea Partner"),
            "Relationship": e_select("Professional Contact"),
            "Circle": e_select("🟡 Regular (Monthly)"),
            "Company / Context": e_rich_text("Freelance designer / potential co-founder"),
            "Last Contact": e_date("2026-02-05"),
            "Next Follow-Up": e_date("2026-03-05"),
            "Preferred Channel": e_select("Video Call"),
            "How We Met": e_rich_text("Twitter/X — connected over a thread about design systems in 2025"),
            "Interests & Topics": e_rich_text("UI/UX design, SaaS, indie hacking, side projects, design systems"),
            "Notes": e_rich_text("We've been brainstorming a SaaS idea for developer onboarding. He's incredibly talented with product design. Schedule a monthly brainstorm call. He's also looking for freelance UI work if anyone asks.")
        }
    ]
    for entry in contact_entries:
        add_entry(contacts_db, entry)
        time.sleep(0.35)

print("  Contacts database populated!")
time.sleep(0.5)

# --- Interaction Log section ---
append_blocks(page_id, [
    divider(),
    heading2("📝 Interaction Log"),
    paragraph("Log every meaningful interaction. This is your relationship memory — never wonder 'what did we talk about last time?' again."),
])
time.sleep(0.5)

# --- Interaction Log Database ---
interaction_db = create_database(page_id, "Interaction Log", {
    "Summary": title_prop(),
    "Contact": rich_text_prop(),
    "Date": date_prop(),
    "Type": select_prop([
        "☕ Coffee / Meal",
        "📞 Phone Call",
        "💬 Text / Chat",
        "📧 Email",
        "🤝 In-Person Meeting",
        "🎉 Event / Party",
        "💻 Video Call",
        "📱 Social Media"
    ]),
    "Key Takeaways": rich_text_prop(),
    "Follow-Up Actions": rich_text_prop(),
    "Mood / Energy": select_prop([
        "🟢 Great — energizing",
        "🟡 Good — pleasant",
        "🟠 Neutral",
        "🔴 Draining — set boundaries"
    ])
})

if interaction_db:
    interaction_entries = [
        {
            "Summary": e_title("Sunday call with Mom & Dad"),
            "Contact": e_rich_text("Mom & Dad"),
            "Date": e_date("2026-02-20"),
            "Type": e_select("📞 Phone Call"),
            "Key Takeaways": e_rich_text("Dad won his golf tournament! Mom finished her book club pick and loved it. They're booking flights to Italy for June. Asked about my job — told them about the promotion timeline."),
            "Follow-Up Actions": e_rich_text("Send them the Italy restaurant list from that travel blog. Call next Sunday as usual."),
            "Mood / Energy": e_select("🟢 Great — energizing")
        },
        {
            "Summary": e_title("Dinner with Jake — caught up on everything"),
            "Contact": e_rich_text("Jake"),
            "Date": e_date("2026-02-18"),
            "Type": e_select("☕ Coffee / Meal"),
            "Key Takeaways": e_rich_text("He's excited about Stripe but nervous about the learning curve. Wants to do more hiking this spring. He broke up with Emma — be supportive but don't pry. Fantasy football trophy is still at his place."),
            "Follow-Up Actions": e_rich_text("Send him that 'First 90 Days' article. Plan the Shenandoah trip for March. Text him Wednesday to check in."),
            "Mood / Energy": e_select("🟢 Great — energizing")
        },
        {
            "Summary": e_title("1:1 with Sarah — promotion discussion"),
            "Contact": e_rich_text("Sarah Kim"),
            "Date": e_date("2026-02-19"),
            "Type": e_select("🤝 In-Person Meeting"),
            "Key Takeaways": e_rich_text("She's advocating for my promotion in the next cycle. Needs me to lead the API migration project as a visible leadership signal. Mentioned her daughter's soccer team made playoffs."),
            "Follow-Up Actions": e_rich_text("Draft API migration proposal by Friday. Send her 'Thinking in Systems' book recommendation. Congratulate her on her daughter's soccer win next time."),
            "Mood / Energy": e_select("🟢 Great — energizing")
        },
        {
            "Summary": e_title("Email exchange with Dr. Patel"),
            "Contact": e_rich_text("Dr. Patel"),
            "Date": e_date("2026-02-01"),
            "Type": e_select("📧 Email"),
            "Key Takeaways": e_rich_text("He thinks the IC track is underrated and to not rush into management. Suggested I publish a technical blog post to build visibility. Shared a contact at Google DeepMind who might be interesting to connect with."),
            "Follow-Up Actions": e_rich_text("Write that blog post draft. Email the DeepMind contact with Dr. Patel's introduction. Schedule next monthly check-in for March 1."),
            "Mood / Energy": e_select("🟢 Great — energizing")
        },
        {
            "Summary": e_title("Quick text check-in with Marcus about gym"),
            "Contact": e_rich_text("Marcus"),
            "Date": e_date("2026-02-21"),
            "Type": e_select("💬 Text / Chat"),
            "Key Takeaways": e_rich_text("He hit a 405 lb deadlift PR! Powerlifting meet is April 12. He's doing a 4-week cut starting March. Asked about the rental property — still researching neighborhoods."),
            "Follow-Up Actions": e_rich_text("Send him the landlord podcast episode. Plan to go to his powerlifting meet to support him."),
            "Mood / Energy": e_select("🟡 Good — pleasant")
        }
    ]
    for entry in interaction_entries:
        add_entry(interaction_db, entry)
        time.sleep(0.35)

print("  Interaction Log populated!")
time.sleep(0.5)

# --- Important Dates section ---
append_blocks(page_id, [
    divider(),
    heading2("🎂 Important Dates"),
    paragraph("Never miss a birthday, anniversary, or milestone. Set reminders and show people you care."),
])
time.sleep(0.5)

# --- Important Dates Database ---
dates_db = create_database(page_id, "Important Dates", {
    "Event": title_prop(),
    "Contact": rich_text_prop(),
    "Date": date_prop(),
    "Type": select_prop([
        "🎂 Birthday",
        "💍 Anniversary",
        "🎓 Milestone",
        "🏠 Life Event",
        "🎄 Holiday Tradition",
        "📅 Recurring"
    ]),
    "Gift Ideas / Plans": rich_text_prop(),
    "Reminder Set": checkbox_prop()
})

if dates_db:
    date_entries = [
        {
            "Event": e_title("Jake's Birthday"),
            "Contact": e_rich_text("Jake"),
            "Date": e_date("2026-07-15"),
            "Type": e_select("🎂 Birthday"),
            "Gift Ideas / Plans": e_rich_text("He mentioned wanting a new hiking daypack. REI has the Osprey Daylite on sale. Or get him a craft beer subscription box."),
            "Reminder Set": e_checkbox(True)
        },
        {
            "Event": e_title("Marcus's Birthday"),
            "Contact": e_rich_text("Marcus"),
            "Date": e_date("2026-11-03"),
            "Type": e_select("🎂 Birthday"),
            "Gift Ideas / Plans": e_rich_text("Gym-related gift: lifting straps, gym bag, or a guest pass to that new powerlifting gym downtown."),
            "Reminder Set": e_checkbox(True)
        },
        {
            "Event": e_title("Aunt Rosa's Birthday"),
            "Contact": e_rich_text("Aunt Rosa"),
            "Date": e_date("2026-08-22"),
            "Type": e_select("🎂 Birthday"),
            "Gift Ideas / Plans": e_rich_text("She loves handwritten cards. Include a recipe I tried that she inspired. Maybe a nice cookbook — 'Salt Fat Acid Heat' by Nosrat."),
            "Reminder Set": e_checkbox(True)
        },
        {
            "Event": e_title("Dr. Patel's Birthday"),
            "Contact": e_rich_text("Dr. Patel"),
            "Date": e_date("2026-04-12"),
            "Type": e_select("🎂 Birthday"),
            "Gift Ideas / Plans": e_rich_text("A thoughtful email with genuine thanks for his mentorship. Mention a specific piece of advice that made a difference."),
            "Reminder Set": e_checkbox(True)
        },
        {
            "Event": e_title("Mom & Dad's Anniversary"),
            "Contact": e_rich_text("Mom & Dad"),
            "Date": e_date("2026-06-15"),
            "Type": e_select("💍 Anniversary"),
            "Gift Ideas / Plans": e_rich_text("35th anniversary! Coordinate with siblings to plan a dinner or send flowers. They love that Italian restaurant downtown."),
            "Reminder Set": e_checkbox(True)
        },
        {
            "Event": e_title("Marcus's Powerlifting Meet"),
            "Contact": e_rich_text("Marcus"),
            "Date": e_date("2026-04-12"),
            "Type": e_select("🎓 Milestone"),
            "Gift Ideas / Plans": e_rich_text("Show up to support him! Bring a sign or at least text good luck the night before."),
            "Reminder Set": e_checkbox(True)
        },
        {
            "Event": e_title("Jake starts at Stripe"),
            "Contact": e_rich_text("Jake"),
            "Date": e_date("2026-03-15"),
            "Type": e_select("🏠 Life Event"),
            "Gift Ideas / Plans": e_rich_text("Send a congratulations text on his first day. Maybe a small gift — a nice notebook for his new desk or a funny card."),
            "Reminder Set": e_checkbox(True)
        }
    ]
    for entry in date_entries:
        add_entry(dates_db, entry)
        time.sleep(0.35)

print("  Important Dates populated!")
time.sleep(0.5)

# --- Relationship Health & Tips section ---
append_blocks(page_id, [
    divider(),
    heading2("🎯 Relationship Playbook"),
    paragraph("Frameworks and reminders for being a great connector, friend, and human."),
])
time.sleep(0.5)

append_blocks(page_id, [
    toggle("🔄 The Follow-Up Framework", [
        callout_rich("📋", [
            text("The 3-Touch System\n\n", bold=True),
            text("After meeting someone new or having a meaningful interaction:\n\n"),
            text("Touch 1 (Within 24 hours):", bold=True),
            text(" Send a quick message referencing something specific from your conversation.\n"),
            text("Touch 2 (Within 1 week):", bold=True),
            text(" Share something valuable — an article, introduction, or resource related to what you discussed.\n"),
            text("Touch 3 (Within 1 month):", bold=True),
            text(" Check in genuinely. Ask about something they mentioned. Suggest meeting up.\n\n"),
            text("After 3 touches, the relationship has momentum. Set a recurring follow-up cadence based on their Circle tier.")
        ], "blue_background")
    ]),

    toggle("💬 Conversation Starters by Relationship Type", [
        callout_rich("👨‍👩‍👧‍👦", [
            text("Family\n", bold=True),
            text("• What's been the highlight of your week?\n• How's [specific thing they care about]?\n• I was thinking about that time we [shared memory]...\n• What are you looking forward to this month?")
        ], "green_background"),
        callout_rich("🧑‍🤝‍🧑", [
            text("Friends\n", bold=True),
            text("• I saw [thing] and it reminded me of you\n• Are you still into [interest they mentioned]?\n• We need to [activity you've been planning] — when works?\n• How's [project/goal they're working on] going?")
        ], "blue_background"),
        callout_rich("💼", [
            text("Professional Contacts\n", bold=True),
            text("• I read an article about [their industry/interest] and thought of you\n• How's the [project they mentioned] coming along?\n• I'd love to get your take on [relevant topic]\n• I met someone who [connection opportunity] — want an intro?")
        ], "purple_background")
    ]),

    toggle("📊 Monthly Relationship Review (10 min)", [
        paragraph("Do this on the first Sunday of each month:", bold=True),
        todo_block("Review overdue follow-ups — reach out to anyone past due"),
        todo_block("Check upcoming birthdays/events for the next 30 days"),
        todo_block("Move anyone to a different Circle tier if the relationship has changed"),
        todo_block("Add any new people you've met this month"),
        todo_block("Review interaction log — is there anyone you've been meaning to reconnect with?"),
        todo_block("Send at least one 'thinking of you' message to someone unexpected"),
        divider(),
        callout("💡", "Tip: The best time to strengthen a relationship is when you don't need anything. Reach out just to give — share an article, a compliment, or a memory.", "yellow_background")
    ]),

    toggle("🏆 Relationship Investment Tiers — How Often to Connect", [
        callout_rich("🔴", [
            text("Inner Circle — Weekly\n", bold=True),
            text("5-7 people max. Your ride-or-dies. Family, best friends, partner.\nThese people get your time, energy, and vulnerability.\nFormat: Calls, in-person, real conversation.")
        ], "red_background"),
        callout_rich("🟠", [
            text("Close — Every 2 Weeks\n", bold=True),
            text("10-15 people. Good friends, close colleagues, active mentors.\nThese people know your real life.\nFormat: Texts, meals, phone calls.")
        ], "orange_background"),
        callout_rich("🟡", [
            text("Regular — Monthly\n", bold=True),
            text("15-30 people. Friends, mentors, professional contacts you actively invest in.\nThese relationships grow with consistent attention.\nFormat: Emails, DMs, occasional coffee.")
        ], "yellow_background"),
        callout_rich("🟢", [
            text("Casual — Quarterly\n", bold=True),
            text("30-50 people. Conference contacts, old classmates, distant colleagues.\nLow-effort, high-leverage. Stay on their radar.\nFormat: LinkedIn comments, holiday messages, sharing articles.")
        ], "green_background"),
        callout_rich("🔵", [
            text("Distant — Yearly\n", bold=True),
            text("Everyone else worth remembering.\nAnnual touchpoint — holiday card, birthday message, or a 'how have you been?'\nFormat: Holiday emails, annual check-ins, social media engagement.")
        ], "blue_background")
    ]),
])
time.sleep(0.5)

# --- Networking Goals ---
append_blocks(page_id, [
    divider(),
    heading2("🎯 Networking Goals"),
    paragraph("Intentional relationship building. Set quarterly goals and track your progress."),
])
time.sleep(0.5)

append_blocks(page_id, [
    column_list([
        [
            callout_rich("📅", [
                text("Q1 2026 Goals\n\n", bold=True),
                text("✅ Reconnect with 3 old friends\n"),
                text("⬜ Attend 2 networking events\n"),
                text("⬜ Get 1 warm introduction to someone in product management\n"),
                text("⬜ Schedule monthly mentor check-ins with Dr. Patel\n"),
                text("✅ Start logging all interactions consistently")
            ], "blue_background")
        ],
        [
            callout_rich("🎯", [
                text("Annual Goals — 2026\n\n", bold=True),
                text("• Grow professional network by 20 meaningful contacts\n"),
                text("• Never miss a close friend's birthday\n"),
                text("• Have monthly calls with all Inner Circle people\n"),
                text("• Attend 6+ networking events or conferences\n"),
                text("• Introduce at least 10 people who should know each other\n"),
                text("• Strengthen 3 weak ties into real relationships")
            ], "purple_background")
        ]
    ]),

    divider(),

    # --- Footer branding ---
    callout_rich("🤝", [
        text("Made with EvolvNth\n", bold=True),
        text("Your relationships are a compounding asset. Invest consistently, and the returns will surprise you.\n"),
        text("evolvnth.com", italic=True, color="gray")
    ], "gray_background")
])
time.sleep(0.5)

print("\n" + "=" * 60)
print(f"PERSONAL CRM TEMPLATE COMPLETE!")
print(f"Page ID: {page_id}")
print("=" * 60)
