import json
import urllib.request
import urllib.error
import time
import os

API_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
BASE_URL = "https://api.notion.com/v1"
PARENT_PAGE = "30e107f0-44d1-8014-abd0-c449748c499e"
NOTION_VERSION = "2022-06-28"

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
        print(f"    Entry added: {result['properties'].get('Name', result['properties'].get('title', {}) ).get('title', [{}])[0].get('plain_text', 'ok') if 'Name' in result.get('properties',{}) else 'ok'}")
    return result

def append_blocks(page_id, children):
    data = {"children": children}
    result = api_call(f"blocks/{page_id}/children", data, "PATCH")
    if result:
        print(f"  Blocks appended: {len(children)} blocks")
    return result

def select_prop(options):
    return {"select": {"options": [{"name": o} for o in options]}}

def multi_select_prop(options):
    return {"multi_select": {"options": [{"name": o} for o in options]}}

def status_prop(options):
    # Status uses groups, we just define it as status type
    return {"status": {}}

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

# Entry helper functions
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

def e_status(val):
    return {"status": {"name": val}}


# ========================================================
# ADVANCED BLOCK HELPERS
# ========================================================

def column_list(columns):
    """Create a column layout. columns is a list of lists of blocks."""
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

def paragraph_rich(rich_texts, **kwargs):
    block = {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_texts}}
    if kwargs.get("color"):
        block["paragraph"]["color"] = kwargs["color"]
    return block

def bullet_rich(rich_texts, children=None):
    block = {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rich_texts}}
    if children:
        block["bulleted_list_item"]["children"] = children
    return block

def numbered_rich(rich_texts, children=None):
    block = {"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": rich_texts}}
    if children:
        block["numbered_list_item"]["children"] = children
    return block

def toggle_rich(rich_texts, children):
    return {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": rich_texts,
            "children": children
        }
    }

def blank_paragraph():
    return paragraph("")

def heading2_colored(content, color="default"):
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [text(content)], "color": color}}

def heading3_colored(content, color="default"):
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": [text(content)], "color": color}}

def bullet_with_children(content, children):
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [text(content)], "children": children}}

def numbered_with_children(content, children):
    return {"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": [text(content)], "children": children}}

def todo_rich(rich_texts, checked=False):
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": rich_texts, "checked": checked}}

def formula_prop(expression):
    return {"formula": {"expression": expression}}

def relation_prop(database_id, single_property=None):
    prop = {"relation": {"database_id": database_id}}
    if single_property:
        prop["relation"]["single_property"] = {}
    return prop

def rollup_prop(relation_name, rollup_name, function="count"):
    return {"rollup": {"relation_property_name": relation_name, "rollup_property_name": rollup_name, "function": function}}


# ========================================================
# TEMPLATE 1: HABIT TRACKER PRO
# ========================================================
def build_template_1():
    print("\n=== TEMPLATE 1: Habit Tracker Pro ===")

    # Page already created, use existing ID
    page_id = "30e107f0-44d1-81cc-bf19-fa857143c946"

    # Create main habits database with expanded properties
    db_id = create_database(page_id, "Habits", {
        "Name": title_prop(),
        "Category": select_prop(["Health", "Productivity", "Mindfulness", "Fitness", "Learning", "Social", "Creative", "Finance"]),
        "Frequency": select_prop(["Daily", "Weekdays", "Weekends", "3x/Week", "Weekly", "Monthly"]),
        "Time of Day": select_prop(["Morning", "Midday", "Afternoon", "Evening", "Anytime"]),
        "Duration": rich_text_prop(),
        "Status": status_prop([]),
        "Current Streak": number_prop(),
        "Best Streak": number_prop(),
        "Start Date": date_prop(),
        "Priority": select_prop(["High", "Medium", "Low"]),
        "Cue / Trigger": rich_text_prop(),
        "Reward": rich_text_prop(),
        "Notes": rich_text_prop()
    })

    if not db_id:
        print("  Failed to create database!")
        return

    # Add comprehensive sample entries
    entries = [
        {"Name": e_title("Morning Meditation"), "Category": e_select("Mindfulness"), "Frequency": e_select("Daily"), "Time of Day": e_select("Morning"), "Duration": e_rich_text("15 min"), "Current Streak": e_number(21), "Best Streak": e_number(35), "Start Date": e_date("2026-01-15"), "Priority": e_select("High"), "Cue / Trigger": e_rich_text("After waking up, sit on meditation cushion"), "Reward": e_rich_text("Calm, focused start to the day"), "Notes": e_rich_text("Using Headspace guided sessions. Progressing to unguided next month.")},
        {"Name": e_title("Read 30 Minutes"), "Category": e_select("Learning"), "Frequency": e_select("Daily"), "Time of Day": e_select("Evening"), "Duration": e_rich_text("30 min"), "Current Streak": e_number(14), "Best Streak": e_number(14), "Start Date": e_date("2026-01-20"), "Priority": e_select("High"), "Cue / Trigger": e_rich_text("After dinner, sit in reading chair with phone away"), "Reward": e_rich_text("Update reading log + note key insights"), "Notes": e_rich_text("Currently: Atomic Habits by James Clear. Next: Deep Work by Cal Newport.")},
        {"Name": e_title("Gym Workout"), "Category": e_select("Fitness"), "Frequency": e_select("Weekdays"), "Time of Day": e_select("Morning"), "Duration": e_rich_text("45 min"), "Current Streak": e_number(8), "Best Streak": e_number(15), "Start Date": e_date("2026-02-01"), "Priority": e_select("High"), "Cue / Trigger": e_rich_text("Gym clothes laid out night before, pre-workout at 6:15 AM"), "Reward": e_rich_text("Post-workout protein shake + energy boost"), "Notes": e_rich_text("Push/Pull/Legs split. Mon: Push, Tue: Pull, Wed: Legs, Thu: Push, Fri: Pull.")},
        {"Name": e_title("Gratitude Journal"), "Category": e_select("Mindfulness"), "Frequency": e_select("Daily"), "Time of Day": e_select("Evening"), "Duration": e_rich_text("5 min"), "Current Streak": e_number(30), "Best Streak": e_number(30), "Start Date": e_date("2026-01-01"), "Priority": e_select("Medium"), "Cue / Trigger": e_rich_text("Part of evening routine, after reading"), "Reward": e_rich_text("Positive mindset before sleep"), "Notes": e_rich_text("Write 3 things I'm grateful for + 1 highlight of the day.")},
        {"Name": e_title("Drink 8 Glasses of Water"), "Category": e_select("Health"), "Frequency": e_select("Daily"), "Time of Day": e_select("Anytime"), "Duration": e_rich_text("Throughout day"), "Current Streak": e_number(12), "Best Streak": e_number(20), "Start Date": e_date("2026-01-10"), "Priority": e_select("Medium"), "Cue / Trigger": e_rich_text("Keep water bottle on desk, refill at every break"), "Reward": e_rich_text("Better energy and clearer skin"), "Notes": e_rich_text("Use tally marks on sticky note. 1 glass = 250ml.")},
        {"Name": e_title("Weekly Meal Prep"), "Category": e_select("Health"), "Frequency": e_select("Weekly"), "Time of Day": e_select("Afternoon"), "Duration": e_rich_text("2 hours"), "Current Streak": e_number(5), "Best Streak": e_number(7), "Start Date": e_date("2026-01-12"), "Priority": e_select("Medium"), "Cue / Trigger": e_rich_text("Every Sunday at 2 PM, put on podcast and start cooking"), "Reward": e_rich_text("Healthy lunches all week + money saved"), "Notes": e_rich_text("Prep 5 lunches + 3 dinners. Rotate between 4 base recipes.")},
        {"Name": e_title("No Phone Before 8 AM"), "Category": e_select("Productivity"), "Frequency": e_select("Daily"), "Time of Day": e_select("Morning"), "Duration": e_rich_text("First hour"), "Current Streak": e_number(4), "Best Streak": e_number(10), "Start Date": e_date("2026-02-10"), "Priority": e_select("High"), "Cue / Trigger": e_rich_text("Phone charges in another room overnight"), "Reward": e_rich_text("Peaceful, intentional morning"), "Notes": e_rich_text("Use an alarm clock instead of phone alarm. Morning routine flows much better without phone distraction.")},
        {"Name": e_title("Practice Spanish"), "Category": e_select("Learning"), "Frequency": e_select("Weekdays"), "Time of Day": e_select("Afternoon"), "Duration": e_rich_text("20 min"), "Current Streak": e_number(9), "Best Streak": e_number(14), "Start Date": e_date("2026-02-05"), "Priority": e_select("Low"), "Cue / Trigger": e_rich_text("After lunch break, open Duolingo before returning to work"), "Reward": e_rich_text("Track XP and maintain league position"), "Notes": e_rich_text("Duolingo + 1 Pimsleur lesson per day. Goal: conversational by year end.")}
    ]

    for entry in entries:
        add_entry(db_id, entry)
        time.sleep(0.35)

    # Append Habit Log database heading
    append_blocks(page_id, [
        divider(),
        heading2("Habit Log"),
        paragraph("Track daily habit completions here. Each entry represents one day. Use this to spot patterns, identify your best days, and calculate your true completion rates.")
    ])
    time.sleep(0.5)

    # Create Habit Log database for daily tracking
    log_db = create_database(page_id, "Daily Habit Log", {
        "Date": title_prop(),
        "Day": select_prop(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
        "Meditation": checkbox_prop(),
        "Reading": checkbox_prop(),
        "Workout": checkbox_prop(),
        "Gratitude": checkbox_prop(),
        "Hydration": checkbox_prop(),
        "No Phone AM": checkbox_prop(),
        "Spanish": checkbox_prop(),
        "Completion Rate": rich_text_prop(),
        "Energy Level": select_prop(["\u26A1 High", "\uD83D\uDD0B Medium", "\uD83E\uDEAB Low"]),
        "Notes": rich_text_prop()
    })

    if log_db:
        log_entries = [
            {"Date": e_title("Feb 17, 2026"), "Day": e_select("Tuesday"), "Meditation": e_checkbox(True), "Reading": e_checkbox(True), "Workout": e_checkbox(True), "Gratitude": e_checkbox(True), "Hydration": e_checkbox(True), "No Phone AM": e_checkbox(True), "Spanish": e_checkbox(True), "Completion Rate": e_rich_text("7/7 = 100%"), "Energy Level": e_select("\u26A1 High"), "Notes": e_rich_text("Perfect day! Morning routine flowed smoothly.")},
            {"Date": e_title("Feb 18, 2026"), "Day": e_select("Wednesday"), "Meditation": e_checkbox(True), "Reading": e_checkbox(True), "Workout": e_checkbox(False), "Gratitude": e_checkbox(True), "Hydration": e_checkbox(True), "No Phone AM": e_checkbox(False), "Spanish": e_checkbox(True), "Completion Rate": e_rich_text("5/7 = 71%"), "Energy Level": e_select("\uD83D\uDD0B Medium"), "Notes": e_rich_text("Skipped workout - sore from yesterday. Checked phone early due to urgent email.")},
            {"Date": e_title("Feb 19, 2026"), "Day": e_select("Thursday"), "Meditation": e_checkbox(True), "Reading": e_checkbox(True), "Workout": e_checkbox(True), "Gratitude": e_checkbox(True), "Hydration": e_checkbox(True), "No Phone AM": e_checkbox(True), "Spanish": e_checkbox(True), "Completion Rate": e_rich_text("7/7 = 100%"), "Energy Level": e_select("\u26A1 High"), "Notes": e_rich_text("Back on track! Great energy after rest day yesterday.")},
            {"Date": e_title("Feb 20, 2026"), "Day": e_select("Friday"), "Meditation": e_checkbox(True), "Reading": e_checkbox(False), "Workout": e_checkbox(True), "Gratitude": e_checkbox(True), "Hydration": e_checkbox(True), "No Phone AM": e_checkbox(True), "Spanish": e_checkbox(False), "Completion Rate": e_rich_text("5/7 = 71%"), "Energy Level": e_select("\uD83D\uDD0B Medium"), "Notes": e_rich_text("Friday social plans cut into evening routine. That's okay - balance matters.")},
            {"Date": e_title("Feb 21, 2026"), "Day": e_select("Saturday"), "Meditation": e_checkbox(True), "Reading": e_checkbox(True), "Workout": e_checkbox(False), "Gratitude": e_checkbox(True), "Hydration": e_checkbox(True), "No Phone AM": e_checkbox(True), "Spanish": e_checkbox(False), "Completion Rate": e_rich_text("5/7 = 71%"), "Energy Level": e_select("\uD83D\uDD0B Medium"), "Notes": e_rich_text("Rest day from gym. Weekends = no Spanish (weekdays only). Solid day overall.")}
        ]
        for entry in log_entries:
            add_entry(log_db, entry)
            time.sleep(0.35)

    # Dashboard, reviews, and advanced sections
    append_blocks(page_id, [
        divider(),

        # Dashboard section with columns
        heading2("Dashboard"),
        column_list([
            [
                callout_rich("\uD83D\uDCC8", [
                    text("Weekly Stats\n", bold=True),
                    text("Completion Rate:  82%\nLongest Streak:   30 days (Gratitude)\nHabits Active:    8\nPerfect Days:     2 of 5\n\nBest Category:    Mindfulness (95%)\nNeeds Work:       Productivity (60%)")
                ], "green_background")
            ],
            [
                callout_rich("\uD83C\uDFAF", [
                    text("This Week's Focus\n", bold=True),
                    text("Priority Habit: No Phone Before 8 AM\nStreak Goal: Get to 10 days\nNew Habit Trial: Evening stretch routine\n\nAffirmation: I am building the person\nI want to become, one habit at a time.")
                ], "blue_background")
            ]
        ]),

        divider(),
        heading2("Weekly Review"),
        toggle("Click to expand your Weekly Review template", [
            paragraph("Part 1: Celebrate Wins", bold=True),
            bullet("What habits did I complete most consistently this week?"),
            bullet("What new personal records or streaks did I achieve?"),
            bullet("What positive changes am I noticing from my habits?"),
            divider(),
            paragraph("Part 2: Analyze & Learn", bold=True),
            bullet("Which habits did I struggle with? Why?"),
            bullet("What obstacles or triggers caused me to miss habits?"),
            bullet("What time of day am I most/least consistent?"),
            bullet("How did my energy levels correlate with habit completion?"),
            divider(),
            paragraph("Part 3: Plan Next Week", bold=True),
            bullet("Top 3 habits to prioritize next week"),
            bullet("One habit to level up (increase duration or difficulty)"),
            bullet("One potential obstacle to plan around"),
            bullet("Reward for hitting 85%+ completion rate")
        ]),

        divider(),
        heading2("Monthly Goals & Milestones"),
        callout_rich("\uD83D\uDCC5", [
            text("February 2026 Targets\n", bold=True),
            text("\u2022 Overall completion rate: 85%+\n\u2022 Meditation streak: reach 30 consecutive days\n\u2022 Gym consistency: 4x/week minimum\n\u2022 Reading: finish current book\n\u2022 No phone AM: build to 14-day streak")
        ], "purple_background"),
        todo_block("Define top 3 habit goals for the month"),
        todo_block("Set target streak counts for each core habit"),
        todo_block("Plan milestone rewards (7-day, 14-day, 30-day)"),
        todo_block("Identify one habit to retire or replace"),
        todo_block("Schedule monthly habit review for last Sunday"),

        divider(),
        heading2("30-Day Challenge"),
        toggle("Start a New 30-Day Habit Challenge", [
            callout_rich("\uD83D\uDD25", [
                text("Challenge Template\n", bold=True),
                text("Habit: _______________\nStart Date: _______________\nWhy: _______________\nMinimum Version (2 min): _______________\nFull Version: _______________\nReward at Day 30: _______________")
            ], "orange_background"),
            divider(),
            paragraph("30-Day Tracker:", bold=True),
            paragraph("Week 1:  \u2610 \u2610 \u2610 \u2610 \u2610 \u2610 \u2610"),
            paragraph("Week 2:  \u2610 \u2610 \u2610 \u2610 \u2610 \u2610 \u2610"),
            paragraph("Week 3:  \u2610 \u2610 \u2610 \u2610 \u2610 \u2610 \u2610"),
            paragraph("Week 4:  \u2610 \u2610 \u2610 \u2610 \u2610 \u2610 \u2610"),
            paragraph("Days 29-30: \u2610 \u2610"),
            divider(),
            paragraph("Rules:", bold=True),
            numbered("Never miss two days in a row"),
            numbered("If you miss a day, do the 2-minute minimum version the next day"),
            numbered("Track completion every evening"),
            numbered("Share your progress with an accountability partner")
        ]),

        divider(),
        heading2("Habit Stacking Planner"),
        toggle("Design Your Habit Stacks", [
            callout_rich("\uD83E\uDDE9", [
                text("Habit Stacking Formula: ", bold=True),
                text("After [CURRENT HABIT], I will [NEW HABIT].")
            ], "blue_background"),
            divider(),
            paragraph("Morning Stack:", bold=True),
            numbered("After I wake up \u2192 I sit on meditation cushion (15 min)"),
            numbered("After meditation \u2192 I put on gym clothes and workout (45 min)"),
            numbered("After workout \u2192 I drink a glass of water and make breakfast"),
            numbered("After breakfast \u2192 I review today's priorities (5 min)"),
            divider(),
            paragraph("Evening Stack:", bold=True),
            numbered("After dinner \u2192 I sit in reading chair and read (30 min)"),
            numbered("After reading \u2192 I write in gratitude journal (5 min)"),
            numbered("After journaling \u2192 I plan tomorrow's top 3 priorities"),
            numbered("After planning \u2192 I start wind-down routine")
        ]),

        divider(),
        heading2("Quit Tracker \u2014 Habits to Break"),
        callout_rich("\uD83D\uDEAB", [
            text("Breaking Bad Habits\n", bold=True),
            text("Track habits you want to eliminate. The key: replace the routine while keeping the cue and reward. Every day without the bad habit is a victory.")
        ], "red_background"),
        toggle("My Quit Tracker", [
            paragraph("Habit to Quit: _______________", bold=True),
            bullet("Trigger/Cue: What makes me do this?"),
            bullet("Replacement Behavior: What will I do instead?"),
            bullet("Days Clean: ___"),
            bullet("Longest Streak: ___"),
            bullet("Reward for 30 days: _______________"),
            divider(),
            paragraph("Common habits to quit:", italic=True),
            bullet("Doom scrolling social media"),
            bullet("Late-night snacking"),
            bullet("Hitting snooze"),
            bullet("Nail biting"),
            bullet("Excessive caffeine"),
            bullet("Impulse online shopping")
        ]),

        divider(),
        heading2("Streak Milestones & Rewards"),
        callout_rich("\uD83C\uDFC6", [
            text("Reward System\n", bold=True),
            text("Set rewards at key milestones to keep motivation high!")
        ], "green_background"),
        toggle("My Reward Milestones", [
            todo_block("7-day streak: _______________  (e.g., favorite coffee drink)"),
            todo_block("14-day streak: _______________ (e.g., new book)"),
            todo_block("30-day streak: _______________ (e.g., nice dinner out)"),
            todo_block("60-day streak: _______________ (e.g., new gear/clothing)"),
            todo_block("90-day streak: _______________ (e.g., experience/trip)"),
            todo_block("365-day streak: _______________ (e.g., major reward!)")
        ]),

        divider(),
        callout_rich("\u2B50", [
            text("The Science of Habit Building\n\n", bold=True),
            text("The Habit Loop: ", bold=True), text("Cue \u2192 Craving \u2192 Response \u2192 Reward\n\n"),
            text("Key Principles:\n"),
            text("\u2022 Make it Obvious \u2014 Design your environment for success\n\u2022 Make it Attractive \u2014 Pair habits with things you enjoy\n\u2022 Make it Easy \u2014 Start with 2-minute versions\n\u2022 Make it Satisfying \u2014 Track streaks and celebrate wins\n\n"),
            text("Remember: You don't rise to the level of your goals. You fall to the level of your systems. Build the system, and the results will follow.", italic=True)
        ], "yellow_background")
    ])

    print("  Template 1 COMPLETE!")
    return page_id


# ========================================================
# TEMPLATE 2: DEBT SNOWBALL CALCULATOR
# ========================================================
def build_template_2():
    print("\n=== TEMPLATE 2: Debt Snowball Calculator ===")

    children = [
        heading1("Debt Snowball Calculator"),
        paragraph("Take control of your finances and crush your debt with the proven Snowball Method. List all your debts from smallest to largest balance, make minimum payments on everything, and throw every extra dollar at the smallest debt. Watch your debts disappear one by one as you build unstoppable momentum.", italic=True, color="gray"),
        divider(),
        toggle("Getting Started \u2014 How to Use This Template", [
            numbered("Replace the sample debts with your real debts (smallest to largest balance)"),
            numbered("Set your total monthly debt budget (all minimum payments + extra snowball amount)"),
            numbered("Direct all extra money at the smallest debt while paying minimums on the rest"),
            numbered("Log every payment in the Payment History database"),
            numbered("When a debt is paid off, roll that payment into the next smallest debt"),
            numbered("Update the Dashboard and Milestones as you progress"),
            numbered("Celebrate every debt you eliminate!"),
            divider(),
            callout_rich("\uD83D\uDCA1", [text("Tip: ", bold=True), text("Duplicate this page to your Notion workspace, then customize the sample data with your own information. All databases are fully editable.")], "yellow_background")
        ]),
        divider(),
        callout_rich("\uD83D\uDCA1", [
            text("How the Snowball Method Works: ", bold=True),
            text("List debts smallest to largest. Pay minimums on all debts except the smallest. Attack the smallest debt with every extra dollar. When it's paid off, roll that payment into the next smallest debt. Repeat until debt-free!")
        ], "blue_background"),

        # Financial snapshot dashboard
        column_list([
            [
                callout_rich("\uD83D\uDCB0", [
                    text("Debt Overview\n", bold=True),
                    text("Total Debt:           $49,750\nTotal Min Payments:   $880/mo\nActual Payments:      $1,305/mo\nExtra Snowball:       $425/mo\n\nHighest Rate:  22.99% (Visa)\nLowest Rate:   0% (Medical)")
                ], "red_background")
            ],
            [
                callout_rich("\uD83D\uDCC5", [
                    text("Payoff Timeline\n", bold=True),
                    text("Medical Bill:    Jul 2026  (5 mo)\nCredit Card:     Jan 2027  (11 mo)\nPersonal Loan:   Sep 2027  (19 mo)\nCar Loan:        Mar 2029  (37 mo)\nStudent Loan:    Nov 2030  (57 mo)\n\nDebt-Free Date:  November 2030")
                ], "green_background")
            ]
        ]),
        heading2("My Debts")
    ]

    page_id = create_page("Debt Snowball Calculator", "\uD83D\uDCB0", children)
    if not page_id:
        return

    db_id = create_database(page_id, "Debts", {
        "Debt Name": title_prop(),
        "Original Balance": number_prop("dollar"),
        "Current Balance": number_prop("dollar"),
        "Minimum Payment": number_prop("dollar"),
        "Interest Rate": number_prop("percent"),
        "Monthly Payment": number_prop("dollar"),
        "Status": status_prop([]),
        "Priority Order": number_prop(),
        "Lender": rich_text_prop(),
        "Account #": rich_text_prop(),
        "Due Date": date_prop(),
        "Payoff Date": date_prop(),
        "Notes": rich_text_prop()
    })

    if not db_id:
        return

    entries = [
        {"Debt Name": e_title("Medical Bill"), "Original Balance": e_number(2500), "Current Balance": e_number(1800), "Minimum Payment": e_number(50), "Interest Rate": e_number(0), "Monthly Payment": e_number(400), "Priority Order": e_number(1), "Lender": e_rich_text("City Hospital"), "Account #": e_rich_text("MED-****-7823"), "Due Date": e_date("2026-03-01"), "Payoff Date": e_date("2026-07-01"), "Notes": e_rich_text("0% interest \u2014 smallest balance, first to attack. $200 extra/mo from snowball.")},
        {"Debt Name": e_title("Credit Card (Visa)"), "Original Balance": e_number(4200), "Current Balance": e_number(2450), "Minimum Payment": e_number(75), "Interest Rate": e_number(22.99), "Monthly Payment": e_number(75), "Priority Order": e_number(2), "Lender": e_rich_text("Chase Bank"), "Account #": e_rich_text("****-****-****-6411"), "Due Date": e_date("2026-03-15"), "Payoff Date": e_date("2027-01-15"), "Notes": e_rich_text("Highest interest rate. After medical is paid, roll $400 here for $475/mo total.")},
        {"Debt Name": e_title("Personal Loan"), "Original Balance": e_number(7500), "Current Balance": e_number(5000), "Minimum Payment": e_number(150), "Interest Rate": e_number(9.5), "Monthly Payment": e_number(150), "Priority Order": e_number(3), "Lender": e_rich_text("SoFi"), "Account #": e_rich_text("SFI-****-4492"), "Due Date": e_date("2026-03-10"), "Payoff Date": e_date("2027-09-10"), "Notes": e_rich_text("After Visa is paid, roll $475 here for $625/mo total attack.")},
        {"Debt Name": e_title("Car Loan"), "Original Balance": e_number(18000), "Current Balance": e_number(12500), "Minimum Payment": e_number(285), "Interest Rate": e_number(5.9), "Monthly Payment": e_number(285), "Priority Order": e_number(4), "Lender": e_rich_text("Capital One Auto"), "Account #": e_rich_text("AUTO-****-3318"), "Due Date": e_date("2026-03-20"), "Payoff Date": e_date("2029-03-20"), "Notes": e_rich_text("48-month term. After personal loan is paid, snowball brings this to $910/mo.")},
        {"Debt Name": e_title("Student Loan"), "Original Balance": e_number(35000), "Current Balance": e_number(28000), "Minimum Payment": e_number(320), "Interest Rate": e_number(4.5), "Monthly Payment": e_number(320), "Priority Order": e_number(5), "Lender": e_rich_text("Navient"), "Account #": e_rich_text("NAV-****-1156"), "Due Date": e_date("2026-03-25"), "Payoff Date": e_date("2030-11-25"), "Notes": e_rich_text("Largest debt, lowest priority in snowball. Final boss. Full $1,305/mo attack once all others are paid.")}
    ]

    for entry in entries:
        add_entry(db_id, entry)
        time.sleep(0.35)

    # Payment History database
    append_blocks(page_id, [
        divider(),
        heading2("Payment History"),
        paragraph("Track every payment you make. Seeing your progress in black and white builds confidence and momentum. Update this after each payment.")
    ])
    time.sleep(0.5)

    payments_db = create_database(page_id, "Payment History", {
        "Payment": title_prop(),
        "Debt": select_prop(["Medical Bill", "Credit Card (Visa)", "Personal Loan", "Car Loan", "Student Loan"]),
        "Amount": number_prop("dollar"),
        "Date": date_prop(),
        "Type": select_prop(["Minimum Payment", "Extra Payment", "Snowball Payment", "Lump Sum"]),
        "Remaining Balance": number_prop("dollar"),
        "Notes": rich_text_prop()
    })

    if payments_db:
        payment_entries = [
            {"Payment": e_title("March Medical Bill Payment"), "Debt": e_select("Medical Bill"), "Amount": e_number(400), "Date": e_date("2026-03-01"), "Type": e_select("Snowball Payment"), "Remaining Balance": e_number(1400), "Notes": e_rich_text("$50 minimum + $350 extra snowball. 4 months to go!")},
            {"Payment": e_title("March Visa Minimum"), "Debt": e_select("Credit Card (Visa)"), "Amount": e_number(75), "Date": e_date("2026-03-15"), "Type": e_select("Minimum Payment"), "Remaining Balance": e_number(2375), "Notes": e_rich_text("Minimum only until medical bill is cleared.")},
            {"Payment": e_title("March Personal Loan"), "Debt": e_select("Personal Loan"), "Amount": e_number(150), "Date": e_date("2026-03-10"), "Type": e_select("Minimum Payment"), "Remaining Balance": e_number(4850), "Notes": e_rich_text("Minimum payment. This debt's turn is coming.")},
            {"Payment": e_title("March Car Payment"), "Debt": e_select("Car Loan"), "Amount": e_number(285), "Date": e_date("2026-03-20"), "Type": e_select("Minimum Payment"), "Remaining Balance": e_number(12215), "Notes": e_rich_text("Regular monthly payment.")},
            {"Payment": e_title("March Student Loan"), "Debt": e_select("Student Loan"), "Amount": e_number(320), "Date": e_date("2026-03-25"), "Type": e_select("Minimum Payment"), "Remaining Balance": e_number(27680), "Notes": e_rich_text("Auto-pay set up. No action needed.")},
            {"Payment": e_title("Tax Refund \u2192 Medical Bill"), "Debt": e_select("Medical Bill"), "Amount": e_number(500), "Date": e_date("2026-03-05"), "Type": e_select("Lump Sum"), "Remaining Balance": e_number(900), "Notes": e_rich_text("Applied tax refund as lump sum! Medical bill almost gone!")}
        ]
        for entry in payment_entries:
            add_entry(payments_db, entry)
            time.sleep(0.35)

    # Strategy, milestones, and advanced sections
    append_blocks(page_id, [
        divider(),
        callout_rich("\uD83D\uDCB3", [
            text("Snowball Payment Strategy\n", bold=True),
            text("Total Monthly Debt Budget: $1,305\nCurrent Target: Medical Bill ($1,800 remaining)\nExtra Snowball Amount: $350/month on target debt\n\nSnowball Progression:\n1. Medical Bill: $400/mo \u2192 Paid off Jul 2026\n2. Credit Card: $400 rolls in \u2192 $475/mo\n3. Personal Loan: $475 rolls in \u2192 $625/mo\n4. Car Loan: $625 rolls in \u2192 $910/mo\n5. Student Loan: $910 rolls in \u2192 $1,305/mo FULL ATTACK")
        ], "green_background"),

        divider(),
        heading2("Monthly Budget Allocation"),
        column_list([
            [
                callout_rich("\uD83D\uDCB5", [
                    text("Income\n", bold=True),
                    text("Primary Salary:      $4,200\nSide Income:         $400\nOther:               $___\n\nTotal Income:        $4,600")
                ], "green_background")
            ],
            [
                callout_rich("\uD83D\uDCE4", [
                    text("Expenses\n", bold=True),
                    text("Rent/Housing:        $1,200\nUtilities:           $150\nGroceries:           $350\nTransportation:      $200\nInsurance:           $180\nOther Essentials:    $215\n\nTotal Expenses:      $2,295")
                ], "yellow_background")
            ]
        ]),
        callout_rich("\uD83C\uDFAF", [
            text("Available for Debt: ", bold=True),
            text("$4,600 - $2,295 = "),
            text("$2,305/month", bold=True),
            text("  |  Currently allocating $1,305 to debt, $500 to savings, $500 discretionary")
        ], "blue_background"),

        divider(),
        heading2("Debt-Free Milestones"),
        callout_rich("\uD83C\uDFC1", [
            text("Track your journey to financial freedom!\n", bold=True),
            text("Each milestone is a victory worth celebrating.")
        ], "purple_background"),
        todo_block("First payment made \u2014 the journey begins!"),
        todo_block("First debt paid off (Medical Bill) \u2014 momentum building!"),
        todo_block("$5,000 total debt eliminated"),
        todo_block("Second debt paid off (Credit Card) \u2014 snowball growing!"),
        todo_block("50% of total debt eliminated ($24,875)"),
        todo_block("Third debt paid off (Personal Loan) \u2014 unstoppable!"),
        todo_block("$40,000 total debt eliminated"),
        todo_block("Fourth debt paid off (Car Loan) \u2014 almost there!"),
        todo_block("Student loan: final payments!"),
        todo_block("DEBT FREE! \u2014 Celebrate BIG! \uD83C\uDF89"),

        divider(),
        heading2("Snowball vs Avalanche Comparison"),
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

    print("  Template 2 COMPLETE!")
    return page_id


# ========================================================
# TEMPLATE 3: STUDENT COMMAND CENTER
# ========================================================
def build_template_3():
    print("\n=== TEMPLATE 3: Student Command Center ===")

    children = [
        heading1("Student Command Center"),
        paragraph("Your all-in-one academic hub. Track courses, manage assignments, calculate your GPA, and stay on top of your semester. Never miss a deadline again.", italic=True, color="gray"),
        divider(),
        toggle("Getting Started \u2014 How to Use This Template", [
            numbered("Add your courses to the Courses database with professor info and schedule"),
            numbered("Enter all upcoming assignments, exams, and projects with due dates"),
            numbered("Use the Exam Schedule to plan study time well in advance"),
            numbered("Update assignment grades as they come back to track your GPA"),
            numbered("Follow the Study Schedule and Pomodoro system for effective studying"),
            numbered("Use the Flashcard system for active recall practice"),
            numbered("Check the Dashboard weekly to stay on top of deadlines"),
            divider(),
            callout_rich("\uD83D\uDCA1", [text("Tip: ", bold=True), text("Duplicate this page to your Notion workspace, then replace the sample data with your actual courses and assignments.")], "yellow_background")
        ]),
        divider(),
        callout_rich("\uD83D\uDCA1", [
            text("Pro Tip: ", bold=True),
            text("Update your assignment statuses daily and check due dates each morning. Use the GPA Calculator section to project your grades and plan study time accordingly.")
        ], "blue_background"),
        heading2("My Courses")
    ]

    page_id = create_page("Student Command Center", "\uD83C\uDF93", children)
    if not page_id:
        return

    # Courses database
    courses_db = create_database(page_id, "Courses", {
        "Course Name": title_prop(),
        "Professor": rich_text_prop(),
        "Schedule": rich_text_prop(),
        "Grade": select_prop(["A", "A-", "B+", "B", "B-", "C+", "C", "D", "F"]),
        "Status": status_prop([]),
        "Credits": number_prop(),
        "Semester": select_prop(["Fall 2026", "Spring 2026", "Summer 2026"])
    })

    if courses_db:
        course_entries = [
            {"Course Name": e_title("Introduction to Computer Science"), "Professor": e_rich_text("Dr. Sarah Chen"), "Schedule": e_rich_text("MWF 9:00-9:50 AM"), "Grade": e_select("A"), "Credits": e_number(4), "Semester": e_select("Spring 2026")},
            {"Course Name": e_title("Calculus II"), "Professor": e_rich_text("Prof. James Miller"), "Schedule": e_rich_text("TTh 11:00-12:15 PM"), "Grade": e_select("B+"), "Credits": e_number(4), "Semester": e_select("Spring 2026")},
            {"Course Name": e_title("English Composition"), "Professor": e_rich_text("Dr. Emily Watson"), "Schedule": e_rich_text("MWF 1:00-1:50 PM"), "Grade": e_select("A-"), "Credits": e_number(3), "Semester": e_select("Spring 2026")},
            {"Course Name": e_title("Physics I"), "Professor": e_rich_text("Prof. Robert Kim"), "Schedule": e_rich_text("TTh 2:00-3:15 PM + Lab F 2:00-4:50 PM"), "Grade": e_select("B"), "Credits": e_number(4), "Semester": e_select("Spring 2026")}
        ]
        for entry in course_entries:
            add_entry(courses_db, entry)
            time.sleep(0.35)

    # Add Assignments heading
    append_blocks(page_id, [
        divider(),
        heading2("My Assignments")
    ])
    time.sleep(0.5)

    # Assignments database
    assignments_db = create_database(page_id, "Assignments", {
        "Assignment": title_prop(),
        "Course": rich_text_prop(),
        "Due Date": date_prop(),
        "Type": select_prop(["Homework", "Quiz", "Exam", "Project", "Essay", "Lab"]),
        "Status": status_prop([]),
        "Grade": number_prop(),
        "Weight": number_prop("percent"),
        "Priority": select_prop(["High", "Medium", "Low"])
    })

    if assignments_db:
        assignment_entries = [
            {"Assignment": e_title("Problem Set 5 - Integration"), "Course": e_rich_text("Calculus II"), "Due Date": e_date("2026-03-05"), "Type": e_select("Homework"), "Grade": e_number(92), "Weight": e_number(10), "Priority": e_select("High")},
            {"Assignment": e_title("Midterm Exam"), "Course": e_rich_text("Physics I"), "Due Date": e_date("2026-03-12"), "Type": e_select("Exam"), "Weight": e_number(25), "Priority": e_select("High")},
            {"Assignment": e_title("Research Essay Draft"), "Course": e_rich_text("English Composition"), "Due Date": e_date("2026-03-08"), "Type": e_select("Essay"), "Weight": e_number(15), "Priority": e_select("Medium")},
            {"Assignment": e_title("Python Programming Project"), "Course": e_rich_text("Intro to CS"), "Due Date": e_date("2026-03-15"), "Type": e_select("Project"), "Weight": e_number(20), "Priority": e_select("High")},
            {"Assignment": e_title("Lab Report 4"), "Course": e_rich_text("Physics I"), "Due Date": e_date("2026-03-03"), "Type": e_select("Lab"), "Grade": e_number(88), "Weight": e_number(5), "Priority": e_select("Low")}
        ]
        for entry in assignment_entries:
            add_entry(assignments_db, entry)
            time.sleep(0.35)

    # Exam Schedule database
    append_blocks(page_id, [
        divider(),
        heading2("Exam Schedule"),
        paragraph("Never be caught off guard. Track all upcoming exams, quizzes, and major deadlines in one place.")
    ])
    time.sleep(0.5)

    exams_db = create_database(page_id, "Exam Schedule", {
        "Exam": title_prop(),
        "Course": rich_text_prop(),
        "Date": date_prop(),
        "Type": select_prop(["Midterm", "Final", "Quiz", "Oral Exam", "Practical"]),
        "Weight": number_prop("percent"),
        "Status": status_prop([]),
        "Study Hours Needed": number_prop(),
        "Study Hours Completed": number_prop(),
        "Topics": rich_text_prop(),
        "Resources": rich_text_prop()
    })

    if exams_db:
        exam_entries = [
            {"Exam": e_title("Physics I Midterm"), "Course": e_rich_text("Physics I"), "Date": e_date("2026-03-12"), "Type": e_select("Midterm"), "Weight": e_number(25), "Study Hours Needed": e_number(20), "Study Hours Completed": e_number(8), "Topics": e_rich_text("Chapters 1-7: Kinematics, Newton's Laws, Work & Energy, Momentum"), "Resources": e_rich_text("Textbook problems Ch 1-7, lecture notes, Physics tutoring center Thu 4-6 PM")},
            {"Exam": e_title("Calculus II Midterm"), "Course": e_rich_text("Calculus II"), "Date": e_date("2026-03-19"), "Type": e_select("Midterm"), "Weight": e_number(30), "Study Hours Needed": e_number(15), "Study Hours Completed": e_number(3), "Topics": e_rich_text("Integration techniques, Series & Sequences, Taylor polynomials"), "Resources": e_rich_text("Stewart Calculus Ch 7-11, Khan Academy videos, Math lab drop-in hours")},
            {"Exam": e_title("CS Quiz 3"), "Course": e_rich_text("Intro to CS"), "Date": e_date("2026-03-07"), "Type": e_select("Quiz"), "Weight": e_number(5), "Study Hours Needed": e_number(4), "Study Hours Completed": e_number(2), "Topics": e_rich_text("Object-Oriented Programming, Classes, Inheritance"), "Resources": e_rich_text("Lecture slides, practice problems on repl.it, study group notes")},
            {"Exam": e_title("English Composition \u2014 Essay Exam"), "Course": e_rich_text("English Composition"), "Date": e_date("2026-04-02"), "Type": e_select("Midterm"), "Weight": e_number(20), "Study Hours Needed": e_number(10), "Study Hours Completed": e_number(0), "Topics": e_rich_text("Rhetorical analysis, argument structure, thesis development, citations"), "Resources": e_rich_text("Writing center appointments, sample essays, Purdue OWL")}
        ]
        for entry in exam_entries:
            add_entry(exams_db, entry)
            time.sleep(0.35)

    # Enhanced remaining sections
    append_blocks(page_id, [
        divider(),

        # Dashboard
        heading2("Semester Dashboard"),
        column_list([
            [
                callout_rich("\uD83D\uDCCA", [
                    text("GPA Calculator\n", bold=True),
                    text("Intro to CS (4 cr):    A   = 4.0\nCalculus II (4 cr):    B+  = 3.3\nEnglish Comp (3 cr):   A-  = 3.7\nPhysics I (4 cr):      B   = 3.0\n\nSemester GPA:  3.49 / 4.00\nTotal Credits: 15\n\nTarget: 3.5+ (Dean's List)")
                ], "purple_background")
            ],
            [
                callout_rich("\u26A0\uFE0F", [
                    text("Upcoming Deadlines\n", bold=True),
                    text("Mar 3  \u2014 Lab Report 4 (Physics)\nMar 5  \u2014 Problem Set 5 (Calc II)\nMar 7  \u2014 CS Quiz 3\nMar 8  \u2014 Research Essay Draft (English)\nMar 12 \u2014 Physics Midterm \u26A0\uFE0F\nMar 15 \u2014 Python Project (CS)\nMar 19 \u2014 Calculus II Midterm \u26A0\uFE0F")
                ], "orange_background")
            ]
        ]),

        divider(),
        heading2("Study Schedule"),
        toggle("Weekly Study Plan", [
            callout_rich("\u23F0", [
                text("Study Hours Target: 18 hours/week\n", bold=True),
                text("Adjust based on upcoming exams and assignment load.")
            ], "blue_background"),
            divider(),
            paragraph("Monday (3 hrs):", bold=True),
            bullet("9:50-10:50 AM \u2014 CS review + homework (after class)"),
            bullet("3:00-4:00 PM \u2014 Calculus problem sets"),
            bullet("7:00-8:00 PM \u2014 English reading/writing"),
            divider(),
            paragraph("Tuesday (2.5 hrs):", bold=True),
            bullet("9:00-10:00 AM \u2014 Physics problem practice"),
            bullet("12:30-1:30 PM \u2014 Calculus review (after class)"),
            bullet("7:00-8:00 PM \u2014 Lab report writing"),
            divider(),
            paragraph("Wednesday (3 hrs):", bold=True),
            bullet("10:00-11:00 AM \u2014 CS lab prep + coding"),
            bullet("2:00-3:00 PM \u2014 English essay drafting"),
            bullet("7:00-8:00 PM \u2014 Physics reading"),
            divider(),
            paragraph("Thursday (2.5 hrs):", bold=True),
            bullet("9:00-10:00 AM \u2014 Calculus practice problems"),
            bullet("12:30-1:30 PM \u2014 Physics review (after class)"),
            bullet("4:00-5:00 PM \u2014 Office hours (rotate by need)"),
            divider(),
            paragraph("Friday (2 hrs):", bold=True),
            bullet("10:00-11:00 AM \u2014 Weekly review + catch-up"),
            bullet("5:00-6:00 PM \u2014 Plan next week's study sessions"),
            divider(),
            paragraph("Weekend (5 hrs):", bold=True),
            bullet("Saturday: Deep work on projects/papers (3 hrs)"),
            bullet("Sunday: Exam prep + weekly review (2 hrs)")
        ]),

        divider(),
        heading2("Course Notes & Resources"),
        toggle("Intro to Computer Science \u2014 Dr. Sarah Chen", [
            paragraph("Key Topics This Semester:", bold=True),
            bullet("Python fundamentals, OOP, Data structures"),
            bullet("Algorithms, Recursion, File I/O"),
            bullet("Final Project: Build a complete application"),
            divider(),
            paragraph("Resources:", bold=True),
            bullet("Textbook: Think Python (2nd Edition)"),
            bullet("Office Hours: MWF 10:00-11:00 AM, Room 305"),
            bullet("TA Hours: TTh 3:00-5:00 PM, CS Lab"),
            bullet("Piazza forum for Q&A")
        ]),
        toggle("Calculus II \u2014 Prof. James Miller", [
            paragraph("Key Topics This Semester:", bold=True),
            bullet("Integration techniques (by parts, partial fractions, trig sub)"),
            bullet("Improper integrals, Arc length, Surface area"),
            bullet("Sequences, Series, Convergence tests"),
            bullet("Taylor and Maclaurin series"),
            divider(),
            paragraph("Resources:", bold=True),
            bullet("Textbook: Stewart Calculus (9th Edition)"),
            bullet("Office Hours: TTh 10:00-11:00 AM, Math Building 201"),
            bullet("Math Tutoring Center: MTRF 1:00-5:00 PM"),
            bullet("Khan Academy: Calculus 2 playlist")
        ]),
        toggle("English Composition \u2014 Dr. Emily Watson", [
            paragraph("Key Topics This Semester:", bold=True),
            bullet("Rhetorical analysis, Argument construction"),
            bullet("Research methods, Source evaluation"),
            bullet("Essay types: Narrative, Analytical, Persuasive"),
            bullet("Final: 10-page research paper"),
            divider(),
            paragraph("Resources:", bold=True),
            bullet("Writing Center: By appointment, Library 2nd floor"),
            bullet("Purdue OWL for citation help"),
            bullet("Office Hours: MWF 2:00-3:00 PM, Humanities 412")
        ]),
        toggle("Physics I \u2014 Prof. Robert Kim", [
            paragraph("Key Topics This Semester:", bold=True),
            bullet("Mechanics: Kinematics, Dynamics, Work/Energy"),
            bullet("Momentum, Rotational motion, Oscillations"),
            bullet("Lab work: 10 experiments with written reports"),
            divider(),
            paragraph("Resources:", bold=True),
            bullet("Textbook: University Physics (15th Edition)"),
            bullet("Office Hours: TTh 4:00-5:00 PM, Physics Building 118"),
            bullet("Physics Tutoring: MWF 3:00-5:00 PM"),
            bullet("Lab Manual + pre-lab prep required")
        ]),

        divider(),
        heading2("Study Tips & Techniques"),
        toggle("Evidence-Based Study Strategies", [
            callout_rich("\uD83E\uDDE0", [
                text("Active Recall & Spaced Repetition\n", bold=True),
                text("The two most effective study techniques, backed by cognitive science. Test yourself frequently rather than re-reading notes. Space your reviews: 1 day, 3 days, 7 days, 14 days after learning.")
            ], "blue_background"),
            divider(),
            bullet_rich([text("Pomodoro Technique: ", bold=True), text("25 min focused study, 5 min break. After 4 rounds, take a 15-30 min break.")]),
            bullet_rich([text("Feynman Method: ", bold=True), text("Explain the concept in simple terms as if teaching someone. Identify gaps in understanding.")]),
            bullet_rich([text("Cornell Notes: ", bold=True), text("Divide notes into cues, notes, and summary sections. Review cues to self-test.")]),
            bullet_rich([text("Interleaving: ", bold=True), text("Mix different problem types and subjects in one study session. Harder but more effective.")]),
            bullet_rich([text("Elaborative Interrogation: ", bold=True), text("Ask 'why?' and 'how?' about every concept. Connect new info to what you already know.")]),
            bullet_rich([text("Practice Testing: ", bold=True), text("Do practice problems without looking at solutions first. Struggle is where learning happens.")])
        ]),

        divider(),
        heading2("Pomodoro Study Timer"),
        callout_rich("\uD83C\uDF45", [
            text("The Pomodoro Technique\n", bold=True),
            text("1. Choose a task to study\n2. Set timer for 25 minutes (1 Pomodoro)\n3. Work with full focus until timer rings\n4. Take a 5-minute break\n5. After 4 Pomodoros, take a 15-30 min break\n\nToday's Pomodoros: \u2610 \u2610 \u2610 \u2610 | \u2610 \u2610 \u2610 \u2610 | \u2610 \u2610 \u2610 \u2610\nTarget: 8-12 Pomodoros per study day")
        ], "red_background"),

        divider(),
        heading2("Flashcard Study System"),
        toggle("Active Flashcard Sets", [
            callout_rich("\uD83D\uDCA1", [
                text("Spaced Repetition Schedule\n", bold=True),
                text("Review new cards: Same day\nReview again: Next day\nReview again: 3 days later\nReview again: 1 week later\nReview again: 2 weeks later\nFinal review: 1 month later\n\nCards you get wrong go back to Day 1!")
            ], "blue_background"),
            divider(),
            paragraph("Active Sets:", bold=True),
            todo_block("Physics I \u2014 Newton's Laws (20 cards) \u2014 Review due: Mar 5"),
            todo_block("Calculus II \u2014 Integration Rules (15 cards) \u2014 Review due: Mar 3"),
            todo_block("CS \u2014 OOP Concepts (25 cards) \u2014 Review due: Mar 7"),
            todo_block("English \u2014 Rhetorical Devices (10 cards) \u2014 Review due: Mar 4")
        ]),

        divider(),
        callout_rich("\uD83C\uDF93", [
            text("Academic Success Mindset\n\n", bold=True),
            text("Your GPA doesn't define you, but your study habits shape your future. Show up to every class. Start assignments early. Ask for help before you're behind. Build relationships with professors \u2014 they're your greatest resource.\n\nConsistency beats cramming every time. 2 hours of focused study daily beats 14 hours of panicked all-nighters.", italic=True)
        ], "yellow_background")
    ])

    print("  Template 3 COMPLETE!")
    return page_id


# ========================================================
# TEMPLATE 4: CONTENT CREATOR HUB
# ========================================================
def build_template_4():
    print("\n=== TEMPLATE 4: Content Creator Hub ===")

    children = [
        heading1("Content Creator Hub"),
        paragraph("Plan, create, and publish content across all your platforms from one central command center. Track your content pipeline, analyze engagement, and maintain consistent brand guidelines.", italic=True, color="gray"),
        divider(),
        toggle("Getting Started \u2014 How to Use This Template", [
            numbered("Add your content ideas to the Content Ideas Bank as they come to you"),
            numbered("Move the best ideas into the Content Pipeline with status tracking"),
            numbered("Track brand deals and sponsorships in the Brand Deals database"),
            numbered("Follow the Content Calendar for consistent posting"),
            numbered("Use the Repurposing System to maximize every piece of content"),
            numbered("Update Analytics Dashboard weekly with platform metrics"),
            numbered("Review Revenue Tracker monthly to optimize income streams"),
            divider(),
            callout_rich("\uD83D\uDCA1", [text("Tip: ", bold=True), text("Set up database views as Board (Kanban) for the Content Pipeline to visually track content through stages: Idea \u2192 In Progress \u2192 Editing \u2192 Scheduled \u2192 Published.")], "yellow_background")
        ]),
        divider(),
        callout_rich("\uD83D\uDE80", [
            text("Creator Workflow: ", bold=True),
            text("Idea \u2192 Script \u2192 Record \u2192 Edit \u2192 Schedule \u2192 Publish \u2192 Analyze. Use the pipeline below to move content through each stage systematically.")
        ], "purple_background"),
        heading2("Content Pipeline")
    ]

    page_id = create_page("Content Creator Hub", "\uD83C\uDFAC", children)
    if not page_id:
        return

    db_id = create_database(page_id, "Content Pipeline", {
        "Content Title": title_prop(),
        "Platform": select_prop(["YouTube", "Instagram", "TikTok", "Twitter", "Blog", "Podcast"]),
        "Status": status_prop([]),
        "Publish Date": date_prop(),
        "Content Type": select_prop(["Video", "Reel", "Story", "Post", "Article", "Episode"]),
        "Engagement": number_prop(),
        "Notes": rich_text_prop()
    })

    if not db_id:
        return

    entries = [
        {"Content Title": e_title("10 Productivity Apps You NEED in 2026"), "Platform": e_select("YouTube"), "Publish Date": e_date("2026-03-01"), "Content Type": e_select("Video"), "Engagement": e_number(15400), "Notes": e_rich_text("12-min video, screen recordings needed. Sponsor: Notion")},
        {"Content Title": e_title("Morning Routine Vlog"), "Platform": e_select("Instagram"), "Publish Date": e_date("2026-03-03"), "Content Type": e_select("Reel"), "Engagement": e_number(8200), "Notes": e_rich_text("60-sec reel, trending audio, shoot at golden hour")},
        {"Content Title": e_title("How I Built a 6-Figure Side Hustle"), "Platform": e_select("Podcast"), "Publish Date": e_date("2026-03-05"), "Content Type": e_select("Episode"), "Engagement": e_number(3200), "Notes": e_rich_text("Interview with guest entrepreneur, 45 min episode")},
        {"Content Title": e_title("5 AI Tools That Changed My Workflow"), "Platform": e_select("Blog"), "Publish Date": e_date("2026-03-07"), "Content Type": e_select("Article"), "Engagement": e_number(1800), "Notes": e_rich_text("SEO keywords: AI tools, productivity, workflow automation")},
        {"Content Title": e_title("Quick Tips: Lighting Setup on a Budget"), "Platform": e_select("TikTok"), "Publish Date": e_date("2026-03-10"), "Content Type": e_select("Video"), "Engagement": e_number(45000), "Notes": e_rich_text("30-sec vertical video, show 3 setups under $50")}
    ]

    for entry in entries:
        add_entry(db_id, entry)
        time.sleep(0.35)

    # Content Ideas database
    append_blocks(page_id, [
        divider(),
        heading2("Content Ideas Bank"),
        paragraph("Never run out of content. Capture every idea instantly, then develop the best ones into your pipeline.")
    ])
    time.sleep(0.5)

    ideas_db = create_database(page_id, "Content Ideas", {
        "Idea": title_prop(),
        "Platform": multi_select_prop(["YouTube", "Instagram", "TikTok", "Twitter", "Blog", "Podcast"]),
        "Category": select_prop(["Tutorial", "Listicle", "Story", "Review", "Behind the Scenes", "Trending", "Evergreen", "Collaboration"]),
        "Priority": select_prop(["Hot \u2014 Do This Week", "High", "Medium", "Backlog"]),
        "Status": status_prop([]),
        "Estimated Effort": select_prop(["Quick (< 2 hrs)", "Medium (2-5 hrs)", "Large (5+ hrs)"]),
        "Source / Inspiration": rich_text_prop(),
        "Notes": rich_text_prop()
    })

    if ideas_db:
        idea_entries = [
            {"Idea": e_title("Day in My Life as a Content Creator"), "Platform": e_multi_select(["YouTube", "Instagram"]), "Category": e_select("Behind the Scenes"), "Priority": e_select("High"), "Estimated Effort": e_select("Medium (2-5 hrs)"), "Source / Inspiration": e_rich_text("Trending format on YouTube, high engagement"), "Notes": e_rich_text("Film over 2-3 days. Show real workflow, editing process, and content planning. End with tips.")},
            {"Idea": e_title("Top 10 Free Tools Every Creator Needs"), "Platform": e_multi_select(["YouTube", "Blog"]), "Category": e_select("Listicle"), "Priority": e_select("Hot \u2014 Do This Week"), "Estimated Effort": e_select("Medium (2-5 hrs)"), "Source / Inspiration": e_rich_text("Always gets searched. Evergreen + high SEO value."), "Notes": e_rich_text("Include Canva, CapCut, Notion, OBS, Unsplash, Descript, etc. Screen record demos.")},
            {"Idea": e_title("How I Edit Videos in Half the Time"), "Platform": e_multi_select(["YouTube", "TikTok"]), "Category": e_select("Tutorial"), "Priority": e_select("High"), "Estimated Effort": e_select("Large (5+ hrs)"), "Source / Inspiration": e_rich_text("Personal workflow optimization, audience frequently asks"), "Notes": e_rich_text("Screen record full editing workflow. Show keyboard shortcuts, templates, batch editing tricks.")},
            {"Idea": e_title("Reacting to My First Video vs Now"), "Platform": e_multi_select(["YouTube", "Instagram", "TikTok"]), "Category": e_select("Story"), "Priority": e_select("Medium"), "Estimated Effort": e_select("Quick (< 2 hrs)"), "Source / Inspiration": e_rich_text("Nostalgia content performs well. Good for audience connection."), "Notes": e_rich_text("Side-by-side comparison. Honest about growth journey. Encourage audience to start creating.")},
            {"Idea": e_title("Collab: Creator Tools Roundtable"), "Platform": e_multi_select(["Podcast", "YouTube"]), "Category": e_select("Collaboration"), "Priority": e_select("Medium"), "Estimated Effort": e_select("Large (5+ hrs)"), "Source / Inspiration": e_rich_text("Cross-promote with 2-3 other creators in niche"), "Notes": e_rich_text("Each creator shares their top 3 tools. 45-min discussion format. Share audiences.")},
            {"Idea": e_title("Viral Hook Formulas That Actually Work"), "Platform": e_multi_select(["TikTok", "Instagram", "Twitter"]), "Category": e_select("Tutorial"), "Priority": e_select("Hot \u2014 Do This Week"), "Estimated Effort": e_select("Quick (< 2 hrs)"), "Source / Inspiration": e_rich_text("Analyzed top-performing hooks from viral videos"), "Notes": e_rich_text("Carousel or short video format. Show 5-7 hook templates with examples. CTA: save for later.")}
        ]
        for entry in idea_entries:
            add_entry(ideas_db, entry)
            time.sleep(0.35)

    # Brand Deals / Sponsorships database
    append_blocks(page_id, [
        divider(),
        heading2("Brand Deals & Sponsorships"),
        paragraph("Track all brand partnerships, sponsorship inquiries, and revenue from collaborations.")
    ])
    time.sleep(0.5)

    deals_db = create_database(page_id, "Brand Deals", {
        "Brand": title_prop(),
        "Status": status_prop([]),
        "Deal Type": select_prop(["Sponsored Video", "Affiliate", "Product Review", "Brand Ambassador", "Gifted", "Ad Read"]),
        "Revenue": number_prop("dollar"),
        "Platform": select_prop(["YouTube", "Instagram", "TikTok", "Podcast", "Blog", "Multi-Platform"]),
        "Deadline": date_prop(),
        "Deliverables": rich_text_prop(),
        "Contact": rich_text_prop(),
        "Contract URL": url_prop(),
        "Notes": rich_text_prop()
    })

    if deals_db:
        deal_entries = [
            {"Brand": e_title("Notion"), "Deal Type": e_select("Sponsored Video"), "Revenue": e_number(2500), "Platform": e_select("YouTube"), "Deadline": e_date("2026-03-01"), "Deliverables": e_rich_text("1 dedicated video (10+ min) + 3 Instagram stories + 1 tweet"), "Contact": e_rich_text("Sarah Kim \u2014 sarah@notion-partners.com"), "Notes": e_rich_text("Repeat sponsor. Great relationship. 30-day exclusivity clause.")},
            {"Brand": e_title("Skillshare"), "Deal Type": e_select("Ad Read"), "Revenue": e_number(800), "Platform": e_select("Podcast"), "Deadline": e_date("2026-03-05"), "Deliverables": e_rich_text("60-sec ad read in 2 podcast episodes"), "Contact": e_rich_text("Mark T. \u2014 creators@skillshare.com"), "Notes": e_rich_text("Standard rate. Unique promo link: skillshare.com/creator123")},
            {"Brand": e_title("Sony (Camera Gear)"), "Deal Type": e_select("Product Review"), "Revenue": e_number(0), "Platform": e_select("YouTube"), "Deadline": e_date("2026-03-20"), "Deliverables": e_rich_text("Honest review video of Sony ZV-E10 II. Keep the camera."), "Contact": e_rich_text("PR Team \u2014 creators@sony.com"), "Notes": e_rich_text("Gifted product (value ~$900). Must disclose. No script approval required.")}
        ]
        for entry in deal_entries:
            add_entry(deals_db, entry)
            time.sleep(0.35)

    # Enhanced remaining sections
    append_blocks(page_id, [
        divider(),
        heading2("Content Calendar"),
        paragraph("Plan your content schedule 2-4 weeks in advance. Maintain a consistent posting cadence across platforms."),
        toggle("Weekly Posting Schedule", [
            callout_rich("\uD83D\uDCC5", [
                text("Optimal Posting Times (based on analytics)\n", bold=True),
                text("YouTube: Tuesday & Thursday 9 AM EST\nInstagram: Mon/Wed/Fri 12 PM & 6 PM EST\nTikTok: Daily 7 PM-9 PM EST\nPodcast: Thursday 6 AM EST\nBlog: Monday 10 AM EST\nTwitter: Weekdays 8 AM & 5 PM EST")
            ], "blue_background"),
            divider(),
            paragraph("Monday:", bold=True), bullet("YouTube video upload (filmed prev week)"), bullet("Blog article publish"),
            paragraph("Tuesday:", bold=True), bullet("Instagram Reel + 3 Stories"), bullet("Twitter thread"),
            paragraph("Wednesday:", bold=True), bullet("TikTok video"), bullet("Instagram carousel post"),
            paragraph("Thursday:", bold=True), bullet("Podcast episode release"), bullet("YouTube Shorts"),
            paragraph("Friday:", bold=True), bullet("TikTok video"), bullet("Instagram Stories (BTS)"),
            paragraph("Weekend:", bold=True), bullet("Batch film next week's content"), bullet("Plan & outline upcoming content"), bullet("Engage with audience comments")
        ]),

        divider(),
        heading2("Analytics Dashboard"),
        column_list([
            [
                callout_rich("\uD83D\uDCCA", [
                    text("Monthly Performance\n", bold=True),
                    text("Total Views:       125,400\nNew Followers:     +2,340\nEngagement Rate:   4.8%\nRevenue:           $3,300\n\nTop Platform:  TikTok (45K views)\nTop Content:   Lighting Setup video")
                ], "green_background")
            ],
            [
                callout_rich("\uD83D\uDCC8", [
                    text("Growth Targets\n", bold=True),
                    text("YouTube Subs:  8,500 \u2192 10,000\nInstagram:     12K \u2192 15K\nTikTok:        22K \u2192 30K\nPodcast:       500 \u2192 1,000 downloads/ep\nBlog:          3K \u2192 5K monthly visitors\n\nMonthly Revenue Target: $5,000")
                ], "purple_background")
            ]
        ]),

        divider(),
        heading2("Brand Guidelines"),
        toggle("Brand Identity & Style Guide", [
            paragraph("Brand Voice:", bold=True),
            bullet("Tone: Educational yet approachable, like talking to a smart friend"),
            bullet("Personality: Curious, helpful, authentic, slightly nerdy"),
            bullet("Avoid: Corporate jargon, clickbait without value, negativity"),
            divider(),
            paragraph("Visual Identity:", bold=True),
            bullet("Primary Color: [Your hex code]"),
            bullet("Secondary: [Your hex code]"),
            bullet("Accent: [Your hex code]"),
            bullet("Heading Font: [Font name]"),
            bullet("Body Font: [Font name]"),
            divider(),
            paragraph("Hashtag Strategy:", bold=True),
            bullet("Core tags: #ContentCreator #CreatorTips #DigitalCreator"),
            bullet("Niche tags: [Add your niche-specific tags]"),
            bullet("Branded tag: #YourBrandName"),
            bullet("Trending: Add 2-3 trending tags per post")
        ]),

        divider(),
        heading2("Revenue & Earnings Tracker"),
        column_list([
            [
                callout_rich("\uD83D\uDCB0", [
                    text("Monthly Revenue\n", bold=True),
                    text("Sponsorships:    $3,300\nAd Revenue:      $450\nAffiliate:       $280\nDigital Products: $150\nMemberships:     $0\n\nTotal:           $4,180\nGoal:            $5,000\nGap:             $820")
                ], "green_background")
            ],
            [
                callout_rich("\uD83D\uDCC8", [
                    text("Revenue by Platform\n", bold=True),
                    text("YouTube:    $2,100 (50%)\nPodcast:    $800 (19%)\nInstagram:  $580 (14%)\nBlog:       $400 (10%)\nTikTok:     $200 (5%)\nOther:      $100 (2%)\n\nBest ROI: YouTube")
                ], "purple_background")
            ]
        ]),

        divider(),
        heading2("Content Repurposing System"),
        callout_rich("\u267B\uFE0F", [
            text("One Piece of Content \u2192 10+ Posts\n", bold=True),
            text("Maximize every piece of content by repurposing across platforms:")
        ], "blue_background"),
        toggle("Repurposing Workflow", [
            paragraph("Start with ONE long-form piece (YouTube video or blog post), then:", bold=True),
            numbered("YouTube Video (10-15 min) \u2014 Original long-form content"),
            numbered("Blog Article \u2014 Written version with SEO keywords"),
            numbered("Podcast Episode \u2014 Audio extracted + commentary"),
            numbered("Instagram Carousel \u2014 Key points as slides"),
            numbered("Instagram Reel \u2014 Best 60-sec clip from video"),
            numbered("TikTok Video \u2014 Vertical edit of best moment"),
            numbered("Twitter/X Thread \u2014 Key insights as numbered tweets"),
            numbered("LinkedIn Post \u2014 Professional angle of the topic"),
            numbered("Email Newsletter \u2014 Summary + exclusive insight"),
            numbered("Pinterest Pin \u2014 Infographic of key takeaways"),
            divider(),
            callout_rich("\uD83D\uDCA1", [
                text("Pro Tip: ", bold=True),
                text("Batch your repurposing! After filming a YouTube video, spend 1 hour creating all derivative content. This turns 1 day of work into 2 weeks of content.")
            ], "yellow_background")
        ]),

        divider(),
        heading2("Audience Growth Log"),
        toggle("Monthly Follower Milestones", [
            paragraph("Track your growth across all platforms:", bold=True),
            bullet("YouTube:   ___ subs (Goal: 10K by Dec 2026)"),
            bullet("Instagram: ___ followers (Goal: 15K)"),
            bullet("TikTok:    ___ followers (Goal: 30K)"),
            bullet("Twitter:   ___ followers (Goal: 5K)"),
            bullet("Podcast:   ___ avg downloads/ep (Goal: 1K)"),
            bullet("Blog:      ___ monthly visitors (Goal: 5K)"),
            bullet("Newsletter: ___ subscribers (Goal: 2K)"),
            divider(),
            paragraph("Growth Levers to Focus On:", bold=True),
            bullet("SEO optimization for evergreen discoverability"),
            bullet("Collaborations for audience cross-pollination"),
            bullet("Consistent posting schedule for algorithm favor"),
            bullet("Engage in comments to boost post visibility"),
            bullet("Trending topics/sounds for viral potential")
        ]),

        divider(),
        callout_rich("\uD83C\uDFAC", [
            text("Creator's Manifesto\n\n", bold=True),
            text("Create for one person, not a million. Consistency compounds. Every piece of content is practice. Your unique perspective is your superpower. Engagement beats vanity metrics. Serve your audience, and growth follows.\n\nThe best content you'll ever make is the content you haven't made yet. Keep creating. \u2728", italic=True)
        ], "yellow_background")
    ])

    print("  Template 4 COMPLETE!")
    return page_id


# ========================================================
# TEMPLATE 5: JOB HUNT DASHBOARD
# ========================================================
def build_template_5():
    print("\n=== TEMPLATE 5: Job Hunt Dashboard ===")

    children = [
        heading1("Job Hunt Dashboard"),
        paragraph("Organize your entire job search in one place. Track applications, prepare for interviews, manage networking contacts, and land your dream role with a systematic approach.", italic=True, color="gray"),
        divider(),
        toggle("Getting Started \u2014 How to Use This Template", [
            numbered("Add target companies and positions to the Applications database"),
            numbered("Build your Networking Contacts list \u2014 anyone who could help your search"),
            numbered("Use the Interview Prep section before every interview"),
            numbered("Update application statuses as you progress through stages"),
            numbered("Prepare your Salary Negotiation numbers before any offer discussion"),
            numbered("Complete the Skills Gap Analysis to focus your preparation"),
            numbered("Follow the Weekly Job Search Routine for consistent momentum"),
            divider(),
            callout_rich("\uD83D\uDCA1", [text("Tip: ", bold=True), text("Set up a Board view on the Applications database grouped by Status to see your pipeline at a glance: Applied \u2192 Screening \u2192 Interview \u2192 Final Round \u2192 Offer.")], "yellow_background")
        ]),
        divider(),
        callout_rich("\uD83D\uDCA1", [
            text("Job Search Strategy: ", bold=True),
            text("Apply to 5-10 targeted positions per week. Customize each resume and cover letter. Follow up within one week of applying. Network actively \u2014 80% of jobs are filled through connections.")
        ], "blue_background"),
        heading2("My Applications")
    ]

    page_id = create_page("Job Hunt Dashboard", "\uD83D\uDCBC", children)
    if not page_id:
        return

    db_id = create_database(page_id, "Applications", {
        "Company": title_prop(),
        "Position": rich_text_prop(),
        "Status": status_prop([]),
        "Salary Range": rich_text_prop(),
        "Location": rich_text_prop(),
        "Applied Date": date_prop(),
        "Contact": rich_text_prop(),
        "URL": url_prop(),
        "Priority": select_prop(["Dream Job", "Strong Match", "Good Fit", "Safety"])
    })

    if not db_id:
        return

    entries = [
        {"Company": e_title("Google"), "Position": e_rich_text("Software Engineer L4"), "Salary Range": e_rich_text("$150K - $200K"), "Location": e_rich_text("Mountain View, CA (Hybrid)"), "Applied Date": e_date("2026-02-10"), "Contact": e_rich_text("Jane Smith - Recruiter"), "URL": e_url("https://careers.google.com"), "Priority": e_select("Dream Job")},
        {"Company": e_title("Stripe"), "Position": e_rich_text("Full Stack Developer"), "Salary Range": e_rich_text("$140K - $180K"), "Location": e_rich_text("San Francisco, CA (Remote OK)"), "Applied Date": e_date("2026-02-12"), "Contact": e_rich_text("Mike Chen - Engineering Manager"), "URL": e_url("https://stripe.com/jobs"), "Priority": e_select("Strong Match")},
        {"Company": e_title("Notion"), "Position": e_rich_text("Product Engineer"), "Salary Range": e_rich_text("$130K - $170K"), "Location": e_rich_text("New York, NY (Hybrid)"), "Applied Date": e_date("2026-02-15"), "Contact": e_rich_text("Sarah Johnson - HR"), "URL": e_url("https://notion.so/careers"), "Priority": e_select("Dream Job")},
        {"Company": e_title("Shopify"), "Position": e_rich_text("Backend Developer"), "Salary Range": e_rich_text("$120K - $160K"), "Location": e_rich_text("Remote"), "Applied Date": e_date("2026-02-18"), "Contact": e_rich_text("Tom Wilson - Tech Lead"), "URL": e_url("https://shopify.com/careers"), "Priority": e_select("Good Fit")},
        {"Company": e_title("Local Startup Inc."), "Position": e_rich_text("Junior Developer"), "Salary Range": e_rich_text("$80K - $100K"), "Location": e_rich_text("Austin, TX (On-site)"), "Applied Date": e_date("2026-02-20"), "Contact": e_rich_text("Lisa Park - CTO"), "URL": e_url("https://localstartup.com/jobs"), "Priority": e_select("Safety")}
    ]

    for entry in entries:
        add_entry(db_id, entry)
        time.sleep(0.35)

    append_blocks(page_id, [
        divider(),
        heading2("Interview Prep"),
        toggle("Interview Preparation Checklist", [
            todo_block("Research company mission, values, and recent news"),
            todo_block("Review the job description and map your experience to requirements"),
            todo_block("Prepare STAR method answers for behavioral questions"),
            todo_block("Practice coding challenges on LeetCode / HackerRank"),
            todo_block("Prepare 5+ thoughtful questions to ask the interviewer"),
            todo_block("Test your video/audio setup for virtual interviews"),
            todo_block("Prepare a 2-minute elevator pitch about yourself"),
            todo_block("Research salary ranges on Glassdoor / Levels.fyi"),
            todo_block("Prepare portfolio / work samples"),
            todo_block("Practice whiteboard / system design scenarios")
        ]),
        toggle("Common Interview Questions & STAR Answers", [
            callout_rich("\uD83D\uDCA1", [
                text("STAR Method: ", bold=True),
                text("Situation \u2192 Task \u2192 Action \u2192 Result. Structure every behavioral answer this way.")
            ], "blue_background"),
            divider(),
            bullet_rich([text("Tell me about yourself ", bold=True), text("\u2014 2-min pitch: who you are, key experience, why this role")]),
            bullet_rich([text("Why this company? ", bold=True), text("\u2014 Research-backed answer about mission/product alignment")]),
            bullet_rich([text("Describe a challenging project ", bold=True), text("\u2014 Use STAR: complexity, your specific contributions, measurable outcome")]),
            bullet_rich([text("Handling disagreements ", bold=True), text("\u2014 Show empathy, data-driven resolution, positive outcome")]),
            bullet_rich([text("Greatest technical achievement ", bold=True), text("\u2014 Quantify impact: performance gains, users served, revenue impact")]),
            bullet_rich([text("Where do you see yourself in 5 years? ", bold=True), text("\u2014 Growth-focused, aligned with company trajectory")]),
            bullet_rich([text("Why are you leaving? ", bold=True), text("\u2014 Positive framing: seeking growth, new challenges, better alignment")]),
            bullet_rich([text("Salary expectations? ", bold=True), text("\u2014 Research range, provide band, express flexibility")])
        ]),

        divider(),
        heading2("Networking Contacts")
    ])
    time.sleep(0.5)

    # Networking Contacts database
    contacts_db = create_database(page_id, "Networking Contacts", {
        "Name": title_prop(),
        "Company": rich_text_prop(),
        "Role": rich_text_prop(),
        "Connection Type": select_prop(["Recruiter", "Hiring Manager", "Referral", "Alumni", "Conference", "LinkedIn", "Friend/Family"]),
        "Status": status_prop([]),
        "Last Contact": date_prop(),
        "Next Follow-Up": date_prop(),
        "LinkedIn": url_prop(),
        "Notes": rich_text_prop()
    })

    if contacts_db:
        contact_entries = [
            {"Name": e_title("Jane Smith"), "Company": e_rich_text("Google"), "Role": e_rich_text("Technical Recruiter"), "Connection Type": e_select("Recruiter"), "Last Contact": e_date("2026-02-18"), "Next Follow-Up": e_date("2026-02-25"), "Notes": e_rich_text("Initial call went well. She's forwarding resume to hiring team. Follow up next week for status update.")},
            {"Name": e_title("Mike Chen"), "Company": e_rich_text("Stripe"), "Role": e_rich_text("Engineering Manager"), "Connection Type": e_select("Hiring Manager"), "Last Contact": e_date("2026-02-15"), "Next Follow-Up": e_date("2026-02-28"), "Notes": e_rich_text("Met at tech meetup. He mentioned open roles on his team. Connected on LinkedIn. Sent follow-up email.")},
            {"Name": e_title("Alex Rivera"), "Company": e_rich_text("Notion"), "Role": e_rich_text("Senior Engineer"), "Connection Type": e_select("Alumni"), "Last Contact": e_date("2026-02-10"), "Next Follow-Up": e_date("2026-02-24"), "Notes": e_rich_text("College alumni, 2 years ahead of me. Offered to refer me internally. Need to send updated resume.")},
            {"Name": e_title("Sarah Johnson"), "Company": e_rich_text("Multiple"), "Role": e_rich_text("Tech Recruiter"), "Connection Type": e_select("LinkedIn"), "Last Contact": e_date("2026-02-20"), "Next Follow-Up": e_date("2026-03-01"), "Notes": e_rich_text("Reached out via LinkedIn. She works with startups and mid-size companies. Scheduling a call.")},
            {"Name": e_title("David Park"), "Company": e_rich_text("Ex-Shopify"), "Role": e_rich_text("Staff Engineer"), "Connection Type": e_select("Conference"), "Last Contact": e_date("2026-02-05"), "Next Follow-Up": e_date("2026-02-26"), "Notes": e_rich_text("Met at ReactConf. Great conversation about backend architecture. He left Shopify and might know of openings.")}
        ]
        for entry in contact_entries:
            add_entry(contacts_db, entry)
            time.sleep(0.35)

    # Enhanced remaining sections
    append_blocks(page_id, [
        divider(),
        heading2("Job Search Dashboard"),
        column_list([
            [
                callout_rich("\uD83D\uDCCA", [
                    text("Application Stats\n", bold=True),
                    text("Total Applied:     12\nScreening Calls:   4\nTechnical Rounds:  2\nFinal Rounds:      1\nOffers:            0\n\nResponse Rate:     33%\nThis Week's Goal:  5 applications")
                ], "blue_background")
            ],
            [
                callout_rich("\uD83D\uDCB0", [
                    text("Salary Research\n", bold=True),
                    text("Target Role: Software Engineer\nExperience: 3-5 years\n\nMarket Range: $120K-$200K\nTarget Base:  $150K-$170K\nTotal Comp:   $180K-$220K\n\nSources: Levels.fyi, Glassdoor,\nBlind, Payscale")
                ], "green_background")
            ]
        ]),

        divider(),
        heading2("Resume & Portfolio"),
        toggle("Resume Versions", [
            callout_rich("\uD83D\uDCDD", [
                text("Resume Strategy: ", bold=True),
                text("Tailor your resume for each application. Lead with impact, not responsibilities. Use numbers to quantify every achievement.")
            ], "blue_background"),
            divider(),
            todo_block("Master Resume \u2014 comprehensive version with all experience"),
            todo_block("Technical Resume \u2014 engineering-focused, highlights projects & tech stack"),
            todo_block("Leadership Resume \u2014 emphasizes team management and project leadership"),
            todo_block("Startup Resume \u2014 highlights versatility, full-stack capabilities, ownership"),
            divider(),
            paragraph("Resume Checklist:", bold=True),
            todo_block("Updated to include latest role and achievements"),
            todo_block("Quantified impact for top 3 bullet points per role"),
            todo_block("Tailored keywords match target job descriptions"),
            todo_block("Reviewed by 2+ people for feedback"),
            todo_block("PDF and DOCX versions ready"),
            todo_block("Portfolio site link included and working")
        ]),

        divider(),
        heading2("Weekly Job Search Routine"),
        toggle("Weekly Action Plan", [
            paragraph("Monday:", bold=True),
            bullet("Search and save 10-15 new relevant positions"),
            bullet("Research 2-3 target companies in depth"),
            paragraph("Tuesday:", bold=True),
            bullet("Submit 2-3 tailored applications"),
            bullet("Send 3 networking outreach messages"),
            paragraph("Wednesday:", bold=True),
            bullet("Submit 2-3 more applications"),
            bullet("Practice coding problems (1 hour)"),
            paragraph("Thursday:", bold=True),
            bullet("Follow up on pending applications"),
            bullet("Attend any scheduled interviews"),
            bullet("Practice system design (1 hour)"),
            paragraph("Friday:", bold=True),
            bullet("Send thank-you notes for any interviews"),
            bullet("Update tracking spreadsheet"),
            bullet("Plan next week's targets"),
            paragraph("Weekend:", bold=True),
            bullet("Deeper interview prep for upcoming rounds"),
            bullet("Portfolio/side project updates"),
            bullet("Self-care and recharge")
        ]),

        divider(),
        heading2("Salary Negotiation Prep"),
        toggle("Negotiation Toolkit", [
            callout_rich("\uD83D\uDCB0", [
                text("Negotiation Framework\n", bold=True),
                text("1. KNOW YOUR NUMBER: Research market rate on Levels.fyi, Glassdoor, Blind\n2. SET YOUR RANGE: Target (ideal) / Minimum (walk-away) / Stretch (ambitious)\n3. QUANTIFY YOUR VALUE: List 3-5 achievements with measurable impact\n4. PRACTICE: Rehearse with a friend. Say your number out loud 10 times.\n5. NEGOTIATE TOTAL COMP: Base + Bonus + Equity + Benefits + PTO + Remote")
            ], "green_background"),
            divider(),
            paragraph("My Negotiation Numbers:", bold=True),
            bullet("Market Rate (median): $___K"),
            bullet("My Minimum (walk-away): $___K"),
            bullet("My Target (ideal): $___K"),
            bullet("My Stretch (ambitious): $___K"),
            divider(),
            paragraph("Script: When They Ask Your Expectations", bold=True),
            quote_block("Based on my research and the value I bring \u2014 specifically [achievement 1] and [achievement 2] \u2014 I'm targeting a total compensation in the range of $X to $Y. I'm flexible and excited about the opportunity, so I'd love to understand the full package you have in mind."),
            divider(),
            paragraph("Non-Salary Items to Negotiate:", bold=True),
            bullet("Signing bonus"),
            bullet("Equity/RSUs (vesting schedule matters)"),
            bullet("Remote work flexibility"),
            bullet("PTO / vacation days"),
            bullet("Professional development budget"),
            bullet("Start date"),
            bullet("Title/level")
        ]),

        divider(),
        heading2("Skills Gap Analysis"),
        toggle("Identify & Close Your Skill Gaps", [
            paragraph("Compare your skills to target job requirements:", bold=True),
            callout_rich("\u2705", [text("Strong Skills (Meeting/Exceeding Requirements):\n", bold=True), text("\u2022 _______________\n\u2022 _______________\n\u2022 _______________")], "green_background"),
            callout_rich("\u26A0\uFE0F", [text("Skills to Strengthen (Partially Meeting):\n", bold=True), text("\u2022 _______________  \u2192 Action: _______________\n\u2022 _______________  \u2192 Action: _______________")], "yellow_background"),
            callout_rich("\u274C", [text("Skills to Develop (Gap):\n", bold=True), text("\u2022 _______________  \u2192 Course/Resource: _______________\n\u2022 _______________  \u2192 Course/Resource: _______________")], "red_background")
        ]),

        divider(),
        callout_rich("\uD83D\uDD25", [
            text("Stay in the Game\n\n", bold=True),
            text("Job searching is emotionally exhausting. Here's what to remember:\n\n\u2022 Every 'no' narrows the path to the right 'yes'\n\u2022 It only takes ONE offer to change everything\n\u2022 Your worth isn't measured by response rates\n\u2022 Take breaks \u2014 burnout doesn't land jobs\n\u2022 Celebrate small wins: every application, every call, every interview\n\u2022 The right role is out there, and you're getting closer every day\n\nYou've got this. Keep going. \uD83D\uDCAA", italic=True)
        ], "orange_background")
    ])

    print("  Template 5 COMPLETE!")
    return page_id


# ========================================================
# TEMPLATE 6: BUDGET & EXPENSE TRACKER
# ========================================================
def build_template_6():
    print("\n=== TEMPLATE 6: Budget & Expense Tracker ===")

    children = [
        heading1("Budget & Expense Tracker"),
        paragraph("Take complete control of your finances. Track every dollar coming in and going out, categorize expenses, monitor spending patterns, and hit your savings goals. Financial freedom starts with awareness.", italic=True, color="gray"),
        divider(),
        toggle("Getting Started \u2014 How to Use This Template", [
            numbered("Replace sample transactions with your actual income and expenses"),
            numbered("Add all recurring subscriptions to the Subscriptions database"),
            numbered("Set your monthly budget limits in the Budget Goals section"),
            numbered("Log every transaction daily (takes 30 seconds!)"),
            numbered("Review the Financial Dashboard weekly to stay on track"),
            numbered("Update Savings Goals and Net Worth monthly"),
            numbered("Do a subscription audit monthly \u2014 cancel what you don't use"),
            divider(),
            callout_rich("\uD83D\uDCA1", [text("Tip: ", bold=True), text("Create a Calendar view on the Transactions database to see spending patterns by date. Use filters to isolate categories and find spending leaks.")], "yellow_background")
        ]),
        divider(),
        callout_rich("\uD83D\uDCA1", [
            text("The 50/30/20 Rule: ", bold=True),
            text("Allocate 50% of income to needs (housing, food, bills), 30% to wants (entertainment, shopping), and 20% to savings and debt repayment. Adjust these percentages to match your goals.")
        ], "blue_background"),
        heading2("Transactions")
    ]

    page_id = create_page("Budget & Expense Tracker", "\uD83D\uDCCA", children)
    if not page_id:
        return

    db_id = create_database(page_id, "Transactions", {
        "Description": title_prop(),
        "Amount": number_prop("dollar"),
        "Category": select_prop(["Housing", "Food", "Transport", "Entertainment", "Shopping", "Bills", "Health", "Savings", "Income"]),
        "Date": date_prop(),
        "Type": select_prop(["Expense", "Income"]),
        "Payment Method": select_prop(["Cash", "Credit Card", "Debit Card", "Transfer"]),
        "Recurring": checkbox_prop()
    })

    if not db_id:
        return

    entries = [
        {"Description": e_title("Monthly Salary"), "Amount": e_number(5200), "Category": e_select("Income"), "Date": e_date("2026-03-01"), "Type": e_select("Income"), "Payment Method": e_select("Transfer"), "Recurring": e_checkbox(True)},
        {"Description": e_title("Rent Payment"), "Amount": e_number(1500), "Category": e_select("Housing"), "Date": e_date("2026-03-01"), "Type": e_select("Expense"), "Payment Method": e_select("Transfer"), "Recurring": e_checkbox(True)},
        {"Description": e_title("Grocery Shopping - Whole Foods"), "Amount": e_number(127.50), "Category": e_select("Food"), "Date": e_date("2026-03-02"), "Type": e_select("Expense"), "Payment Method": e_select("Debit Card"), "Recurring": e_checkbox(False)},
        {"Description": e_title("Electric & Gas Bill"), "Amount": e_number(145), "Category": e_select("Bills"), "Date": e_date("2026-03-03"), "Type": e_select("Expense"), "Payment Method": e_select("Credit Card"), "Recurring": e_checkbox(True)},
        {"Description": e_title("Gym Membership"), "Amount": e_number(49.99), "Category": e_select("Health"), "Date": e_date("2026-03-01"), "Type": e_select("Expense"), "Payment Method": e_select("Credit Card"), "Recurring": e_checkbox(True)},
        {"Description": e_title("Uber Rides"), "Amount": e_number(35.80), "Category": e_select("Transport"), "Date": e_date("2026-03-04"), "Type": e_select("Expense"), "Payment Method": e_select("Credit Card"), "Recurring": e_checkbox(False)},
        {"Description": e_title("Netflix + Spotify"), "Amount": e_number(26.98), "Category": e_select("Entertainment"), "Date": e_date("2026-03-01"), "Type": e_select("Expense"), "Payment Method": e_select("Credit Card"), "Recurring": e_checkbox(True)},
        {"Description": e_title("Savings Transfer"), "Amount": e_number(500), "Category": e_select("Savings"), "Date": e_date("2026-03-01"), "Type": e_select("Expense"), "Payment Method": e_select("Transfer"), "Recurring": e_checkbox(True)}
    ]

    for entry in entries:
        add_entry(db_id, entry)
        time.sleep(0.35)

    # Subscriptions database
    append_blocks(page_id, [
        divider(),
        heading2("Subscriptions & Recurring Expenses"),
        paragraph("Track every recurring charge. Subscription creep is one of the biggest budget leaks. Review monthly and cut what you don't use.")
    ])
    time.sleep(0.5)

    subs_db = create_database(page_id, "Subscriptions", {
        "Service": title_prop(),
        "Cost": number_prop("dollar"),
        "Frequency": select_prop(["Monthly", "Quarterly", "Annual"]),
        "Category": select_prop(["Streaming", "Software", "Fitness", "News/Media", "Cloud Storage", "Food Delivery", "Gaming", "Other"]),
        "Status": select_prop(["Active", "Paused", "Cancelling", "Free Trial"]),
        "Renewal Date": date_prop(),
        "Payment Method": select_prop(["Credit Card", "Debit Card", "PayPal", "Bank Transfer"]),
        "Essential?": checkbox_prop(),
        "Notes": rich_text_prop()
    })

    if subs_db:
        sub_entries = [
            {"Service": e_title("Netflix"), "Cost": e_number(15.49), "Frequency": e_select("Monthly"), "Category": e_select("Streaming"), "Status": e_select("Active"), "Renewal Date": e_date("2026-03-15"), "Payment Method": e_select("Credit Card"), "Essential?": e_checkbox(False), "Notes": e_rich_text("Standard plan. Consider downgrading to Basic if not using 4K.")},
            {"Service": e_title("Spotify Premium"), "Cost": e_number(11.49), "Frequency": e_select("Monthly"), "Category": e_select("Streaming"), "Status": e_select("Active"), "Renewal Date": e_date("2026-03-01"), "Payment Method": e_select("Credit Card"), "Essential?": e_checkbox(True), "Notes": e_rich_text("Use daily for music and podcasts. Worth keeping.")},
            {"Service": e_title("Gym Membership"), "Cost": e_number(49.99), "Frequency": e_select("Monthly"), "Category": e_select("Fitness"), "Status": e_select("Active"), "Renewal Date": e_date("2026-03-01"), "Payment Method": e_select("Debit Card"), "Essential?": e_checkbox(True), "Notes": e_rich_text("Going 4x/week. Great value. Annual plan saves $120/year.")},
            {"Service": e_title("iCloud Storage (200GB)"), "Cost": e_number(2.99), "Frequency": e_select("Monthly"), "Category": e_select("Cloud Storage"), "Status": e_select("Active"), "Renewal Date": e_date("2026-03-10"), "Payment Method": e_select("Credit Card"), "Essential?": e_checkbox(True), "Notes": e_rich_text("Photo backup + device sync. Essential.")},
            {"Service": e_title("Adobe Creative Cloud"), "Cost": e_number(54.99), "Frequency": e_select("Monthly"), "Category": e_select("Software"), "Status": e_select("Active"), "Renewal Date": e_date("2026-03-20"), "Payment Method": e_select("Credit Card"), "Essential?": e_checkbox(True), "Notes": e_rich_text("Need for work. Using Photoshop, Illustrator, Premiere. Annual plan is cheaper.")},
            {"Service": e_title("DoorDash DashPass"), "Cost": e_number(9.99), "Frequency": e_select("Monthly"), "Category": e_select("Food Delivery"), "Status": e_select("Cancelling"), "Renewal Date": e_date("2026-03-05"), "Payment Method": e_select("Credit Card"), "Essential?": e_checkbox(False), "Notes": e_rich_text("Only ordered 2x last month. Cancel and cook more. Saving $120/year + delivery costs.")},
            {"Service": e_title("ChatGPT Plus"), "Cost": e_number(20), "Frequency": e_select("Monthly"), "Category": e_select("Software"), "Status": e_select("Active"), "Renewal Date": e_date("2026-03-12"), "Payment Method": e_select("Credit Card"), "Essential?": e_checkbox(True), "Notes": e_rich_text("Using daily for work productivity. Worth it.")},
            {"Service": e_title("Audible"), "Cost": e_number(14.95), "Frequency": e_select("Monthly"), "Category": e_select("Streaming"), "Status": e_select("Paused"), "Renewal Date": e_date("2026-04-01"), "Payment Method": e_select("Credit Card"), "Essential?": e_checkbox(False), "Notes": e_rich_text("Paused \u2014 have 3 unused credits. Resume when caught up.")}
        ]
        for entry in sub_entries:
            add_entry(subs_db, entry)
            time.sleep(0.35)

    # Enhanced remaining sections
    append_blocks(page_id, [
        divider(),

        # Financial Dashboard
        heading2("Financial Dashboard"),
        column_list([
            [
                callout_rich("\uD83D\uDCB5", [
                    text("March 2026 Summary\n", bold=True),
                    text("Total Income:      $5,200\nTotal Expenses:    $2,385\nSubscriptions:     $179.90\nNet Savings:       $2,635\n\nSavings Rate:      50.7% \uD83C\uDF89\nTarget Rate:       40%+\nStatus:            AHEAD OF TARGET")
                ], "green_background")
            ],
            [
                callout_rich("\uD83C\uDFAF", [
                    text("50/30/20 Check\n", bold=True),
                    text("Needs (50%):    $2,100 of $2,600\nWants (30%):    $285 of $1,560\nSave/Debt (20%): $2,635 of $1,040\n\nNeeds:   \u2705 Under budget\nWants:   \u2705 Well under budget\nSavings: \u2705 Exceeding target!\n\nVerdict: Excellent month!")
                ], "purple_background")
            ]
        ]),

        divider(),
        heading2("Monthly Summary"),
        toggle("March 2026 Detailed Breakdown", [
            paragraph("Income:", bold=True),
            bullet("Primary Salary: $4,800"),
            bullet("Side Income: $400"),
            bullet("Total: $5,200"),
            divider(),
            paragraph("Expenses by Category:", bold=True),
            bullet("Housing: $1,500 (28.8%) \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2591"),
            bullet("Savings: $500 (9.6%) \u2588\u2588\u2588\u2591\u2591\u2591\u2591\u2591\u2591\u2591"),
            bullet("Food & Dining: $285 (5.5%) \u2588\u2588\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591"),
            bullet("Subscriptions: $180 (3.5%) \u2588\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591"),
            bullet("Bills & Utilities: $145 (2.8%) \u2588\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591"),
            bullet("Health & Fitness: $50 (1.0%) \u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591"),
            bullet("Transport: $36 (0.7%) \u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591"),
            bullet("Entertainment: $27 (0.5%) \u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591"),
            divider(),
            callout_rich("\uD83D\uDCA1", [
                text("Insight: ", bold=True),
                text("Subscription costs ($180/mo = $2,160/year) are your 4th largest expense. Cancelling DoorDash saves $120/year. Review Adobe \u2014 can you use free alternatives for any tools?")
            ], "yellow_background")
        ]),

        divider(),
        heading2("Budget Goals & Targets"),
        callout_rich("\uD83C\uDFAF", [
            text("Monthly Budget Limits\n", bold=True),
            text("Housing:        $1,500 max (29%)\nFood & Dining:  $400 max (8%)\nTransportation: $200 max (4%)\nEntertainment:  $150 max (3%)\nShopping:       $200 max (4%)\nSubscriptions:  $150 max (3%)\nSavings:        $500 min (10%)\nInvesting:      $200 min (4%)\nEmergency Fund: $15,000 target")
        ], "green_background"),

        divider(),
        heading2("Savings Goals"),
        callout_rich("\uD83C\uDFE6", [
            text("Savings Progress\n", bold=True),
            text("Emergency Fund:   $8,500 / $15,000  \u2588\u2588\u2588\u2588\u2588\u2588\u2591\u2591\u2591\u2591 57%\nVacation Fund:    $1,200 / $3,000   \u2588\u2588\u2588\u2588\u2591\u2591\u2591\u2591\u2591\u2591 40%\nNew Laptop:       $750 / $2,000     \u2588\u2588\u2588\u2591\u2591\u2591\u2591\u2591\u2591\u2591 38%\nInvestment:       $1,400 / $2,400   \u2588\u2588\u2588\u2588\u2588\u2588\u2591\u2591\u2591\u2591 58%")
        ], "purple_background"),
        todo_block("Emergency Fund: reach $10,000 by June"),
        todo_block("Vacation Fund: reach $2,000 by August"),
        todo_block("New Laptop Fund: fully funded by May"),
        todo_block("Start Roth IRA contributions ($500/month)"),
        todo_block("Increase savings rate to 25% by Q3"),

        divider(),
        heading2("Money Management Tips"),
        toggle("Smart Money Habits", [
            paragraph("Daily:", bold=True),
            bullet("Log every expense (takes 30 seconds)"),
            bullet("Check if purchase aligns with budget goals"),
            bullet("Use the 24-hour rule for purchases over $50"),
            divider(),
            paragraph("Weekly:", bold=True),
            bullet("Review spending vs budget (Sunday evening)"),
            bullet("Check upcoming bills and due dates"),
            bullet("Transfer any surplus to savings"),
            divider(),
            paragraph("Monthly:", bold=True),
            bullet("Full budget review and adjustment"),
            bullet("Subscription audit \u2014 cancel unused services"),
            bullet("Update savings goal progress"),
            bullet("Negotiate one bill (insurance, phone, internet)"),
            divider(),
            paragraph("Annually:", bold=True),
            bullet("Review all insurance policies for better rates"),
            bullet("Rebalance investment allocations"),
            bullet("Set new financial goals"),
            bullet("Tax planning and optimization")
        ]),

        divider(),
        heading2("Bill Calendar & Due Dates"),
        callout_rich("\uD83D\uDCC5", [
            text("Monthly Bill Schedule\n", bold=True),
            text("1st  \u2014 Rent ($1,500), Gym ($50), Spotify ($11), Savings ($500)\n3rd  \u2014 Electric & Gas ($145)\n5th  \u2014 Internet ($65)\n10th \u2014 Car Insurance ($180)\n12th \u2014 ChatGPT ($20)\n15th \u2014 Netflix ($15), Phone ($85)\n20th \u2014 Adobe CC ($55)\n\nTotal Fixed Monthly Bills: $2,626\nRemaining for Variable Spending: $2,574")
        ], "orange_background"),

        divider(),
        heading2("Net Worth Tracker"),
        toggle("Monthly Net Worth Snapshot", [
            paragraph("Track your net worth monthly to see the full financial picture:", bold=True),
            callout_rich("\uD83D\uDCC8", [
                text("Net Worth Calculator\n", bold=True),
                text("ASSETS:\nChecking:     $___\nSavings:      $___\nEmergency:    $8,500\nInvestments:  $___\nRetirement:   $___\nCar Value:    $___\nOther:        $___\nTotal Assets: $___\n\nLIABILITIES:\nCredit Cards: $___\nLoans:        $___\nOther Debt:   $___\nTotal Debt:   $___\n\nNET WORTH = Assets - Liabilities = $___")
            ], "blue_background"),
            divider(),
            paragraph("Monthly Net Worth Log:", bold=True),
            bullet("Jan 2026: $___"),
            bullet("Feb 2026: $___"),
            bullet("Mar 2026: $___")
        ]),

        divider(),
        heading2("Investment Overview"),
        toggle("My Investment Portfolio", [
            paragraph("Track your investment accounts and allocation:", bold=True),
            bullet("401(k) / Employer Retirement: $___  (Target: maximize employer match)"),
            bullet("Roth IRA: $___  (Target: $7,000/year max contribution)"),
            bullet("Brokerage Account: $___  (Index funds + ETFs)"),
            bullet("Crypto/Alternative: $___  (Keep under 5% of portfolio)"),
            divider(),
            callout_rich("\uD83D\uDCA1", [
                text("Investing Rule of Thumb: ", bold=True),
                text("Invest at least 15% of gross income for retirement. Start with employer 401k match (free money!), then max Roth IRA, then back to 401k or brokerage.")
            ], "blue_background")
        ]),

        divider(),
        callout_rich("\uD83D\uDCB0", [
            text("Your Financial Freedom Equation\n\n", bold=True),
            text("Financial freedom = Passive Income > Expenses\n\nEvery dollar you save and invest is a tiny employee working for you 24/7. At a 7% return, $500/month invested today becomes ~$120,000 in 10 years.\n\nYou're not just tracking expenses \u2014 you're building the life you want.", italic=True)
        ], "yellow_background")
    ])

    print("  Template 6 COMPLETE!")
    return page_id


# ========================================================
# TEMPLATE 7: TRAVEL PLANNER
# ========================================================
def build_template_7():
    print("\n=== TEMPLATE 7: Travel Planner ===")

    children = [
        heading1("Travel Planner"),
        paragraph("Plan unforgettable trips from start to finish. Organize destinations, budgets, itineraries, and packing lists all in one place. Whether it's a weekend getaway or an international adventure, travel with confidence.", italic=True, color="gray"),
        divider(),
        toggle("Getting Started \u2014 How to Use This Template", [
            numbered("Add your planned trips to the Trips database with dates and budgets"),
            numbered("Create day-by-day plans in the Itinerary database"),
            numbered("Build your dream destinations in the Bucket List"),
            numbered("Use the Packing Checklist before every trip (customize per trip type)"),
            numbered("Track on-trip spending with the Expense Tracker"),
            numbered("Save restaurant recommendations for each destination"),
            numbered("Check Travel Documents section well before international trips"),
            divider(),
            callout_rich("\uD83D\uDCA1", [text("Tip: ", bold=True), text("Use Gallery view on the Trips database for a beautiful visual layout. Filter the Itinerary by Trip to see day-by-day plans for each destination.")], "yellow_background")
        ]),
        divider(),
        callout_rich("\u2708\uFE0F", [
            text("Travel Planning Checklist: ", bold=True),
            text("Choose destination \u2192 Set budget \u2192 Book flights & hotels \u2192 Plan itinerary \u2192 Pack smart \u2192 Check documents \u2192 Enjoy the journey!")
        ], "blue_background"),
        heading2("My Trips")
    ]

    page_id = create_page("Travel Planner", "\u2708\uFE0F", children)
    if not page_id:
        return

    db_id = create_database(page_id, "Trips", {
        "Destination": title_prop(),
        "Start Date": date_prop(),
        "End Date": date_prop(),
        "Budget": number_prop("dollar"),
        "Status": status_prop([]),
        "Trip Type": select_prop(["Business", "Vacation", "Adventure", "Weekend Getaway"]),
        "Rating": select_prop(["\u2B50", "\u2B50\u2B50", "\u2B50\u2B50\u2B50", "\u2B50\u2B50\u2B50\u2B50", "\u2B50\u2B50\u2B50\u2B50\u2B50"]),
        "Notes": rich_text_prop()
    })

    if not db_id:
        return

    entries = [
        {"Destination": e_title("Tokyo Japan"), "Start Date": e_date("2026-04-10"), "End Date": e_date("2026-04-20"), "Budget": e_number(4500), "Trip Type": e_select("Vacation"), "Notes": e_rich_text("Cherry blossom season! Visit Shibuya, Akihabara, Mount Fuji day trip. Book JR Pass.")},
        {"Destination": e_title("Barcelona Spain"), "Start Date": e_date("2026-06-15"), "End Date": e_date("2026-06-22"), "Budget": e_number(3200), "Trip Type": e_select("Adventure"), "Notes": e_rich_text("Sagrada Familia, La Rambla, beach days. Book Airbnb in Gothic Quarter.")},
        {"Destination": e_title("New York City"), "Start Date": e_date("2026-03-20"), "End Date": e_date("2026-03-23"), "Budget": e_number(1800), "Trip Type": e_select("Weekend Getaway"), "Rating": e_select("\u2B50\u2B50\u2B50\u2B50"), "Notes": e_rich_text("Broadway show, Central Park, MoMA, food tour in Brooklyn.")},
        {"Destination": e_title("San Francisco - Tech Conference"), "Start Date": e_date("2026-05-05"), "End Date": e_date("2026-05-08"), "Budget": e_number(2000), "Trip Type": e_select("Business"), "Notes": e_rich_text("Company-sponsored. Hotel booked at Marriott Union Square. Networking dinner Thursday.")}
    ]

    for entry in entries:
        add_entry(db_id, entry)
        time.sleep(0.35)

    append_blocks(page_id, [
        divider(),
        heading2("Packing List"),
        toggle("Essential Packing Checklist", [
            paragraph("Documents & Tech:", bold=True),
            todo_block("Passport / ID"),
            todo_block("Boarding passes (digital or printed)"),
            todo_block("Hotel confirmation"),
            todo_block("Phone charger & power bank"),
            todo_block("Universal power adapter"),
            todo_block("Headphones"),
            divider(),
            paragraph("Clothing:", bold=True),
            todo_block("Underwear & socks (days + 2 extra)"),
            todo_block("T-shirts / tops"),
            todo_block("Pants / shorts"),
            todo_block("Jacket / layers"),
            todo_block("Comfortable walking shoes"),
            todo_block("Sleepwear"),
            divider(),
            paragraph("Toiletries:", bold=True),
            todo_block("Toothbrush & toothpaste"),
            todo_block("Deodorant"),
            todo_block("Sunscreen"),
            todo_block("Medications"),
            todo_block("First aid kit basics")
        ]),
        divider(),
        heading2("Travel Documents"),
        bullet("Passport (check expiration - must be valid 6+ months)"),
        bullet("Visa requirements (check destination country)"),
        bullet("Travel insurance policy"),
        bullet("Vaccination records / health certificates"),
        bullet("Emergency contact information"),
        bullet("Copies of all documents (digital + physical)")
    ])
    time.sleep(0.5)

    # Itinerary database
    append_blocks(page_id, [
        divider(),
        heading2("Trip Itinerary Planner"),
        paragraph("Plan your day-by-day itinerary. Add activities, reservations, and transportation details for each day of your trip.")
    ])
    time.sleep(0.5)

    itinerary_db = create_database(page_id, "Itinerary", {
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
            {"Activity": e_title("Arrive at Narita Airport + Train to Hotel"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 1"), "Time": e_rich_text("2:00 PM - 5:00 PM"), "Type": e_select("Transport"), "Booked?": e_checkbox(True), "Cost Estimate": e_number(35), "Address / Location": e_rich_text("Narita Express to Shinjuku Station"), "Notes": e_rich_text("JR Pass covers this ride. Activate pass at JR counter in airport. Buy Suica card for local trains.")},
            {"Activity": e_title("Explore Shibuya Crossing & Harajuku"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 2"), "Time": e_rich_text("10:00 AM - 2:00 PM"), "Type": e_select("Sightseeing"), "Booked?": e_checkbox(False), "Cost Estimate": e_number(0), "Address / Location": e_rich_text("Shibuya Station \u2192 Takeshita Street"), "Notes": e_rich_text("Walk through Shibuya Crossing, Hachiko statue, Meiji Shrine, Harajuku street food. Arrive early to beat crowds.")},
            {"Activity": e_title("Tsukiji Outer Market Breakfast"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 3"), "Time": e_rich_text("7:00 AM - 9:00 AM"), "Type": e_select("Food & Dining"), "Booked?": e_checkbox(False), "Cost Estimate": e_number(30), "Address / Location": e_rich_text("Tsukiji Outer Market"), "Notes": e_rich_text("Fresh sushi, tamagoyaki, and street food. Go early for the best experience.")},
            {"Activity": e_title("Mount Fuji Day Trip"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 5"), "Time": e_rich_text("7:00 AM - 6:00 PM"), "Type": e_select("Adventure"), "Booked?": e_checkbox(True), "Cost Estimate": e_number(80), "Address / Location": e_rich_text("Shinjuku Bus Terminal \u2192 Kawaguchiko"), "Notes": e_rich_text("Book bus tickets in advance. Visit Chureito Pagoda for the classic photo. Lake Kawaguchiko boat ride. Bring warm layers.")},
            {"Activity": e_title("Akihabara Electronics & Anime District"), "Trip": e_select("Tokyo Japan"), "Day": e_select("Day 4"), "Time": e_rich_text("1:00 PM - 6:00 PM"), "Type": e_select("Shopping"), "Booked?": e_checkbox(False), "Cost Estimate": e_number(100), "Address / Location": e_rich_text("Akihabara Station area"), "Notes": e_rich_text("Electronics stores, anime shops, themed cafes. Budget for souvenirs. Visit Super Potato for retro games.")}
        ]
        for entry in itinerary_entries:
            add_entry(itinerary_db, entry)
            time.sleep(0.35)

    # Bucket List database
    append_blocks(page_id, [
        divider(),
        heading2("Travel Bucket List"),
        paragraph("Dream destinations and experiences to plan for. Update as you travel and discover new places that inspire you.")
    ])
    time.sleep(0.5)

    bucket_db = create_database(page_id, "Bucket List Destinations", {
        "Destination": title_prop(),
        "Country": rich_text_prop(),
        "Region": select_prop(["Asia", "Europe", "North America", "South America", "Africa", "Oceania", "Middle East"]),
        "Trip Type": select_prop(["City Break", "Beach", "Adventure", "Cultural", "Road Trip", "Cruise", "Backpacking"]),
        "Best Season": select_prop(["Spring", "Summer", "Fall", "Winter", "Year-Round"]),
        "Estimated Budget": number_prop("dollar"),
        "Priority": select_prop(["Must Visit", "High", "Medium", "Someday"]),
        "Status": status_prop([]),
        "Why I Want to Go": rich_text_prop()
    })

    if bucket_db:
        bucket_entries = [
            {"Destination": e_title("Kyoto, Japan"), "Country": e_rich_text("Japan"), "Region": e_select("Asia"), "Trip Type": e_select("Cultural"), "Best Season": e_select("Spring"), "Estimated Budget": e_number(3000), "Priority": e_select("Must Visit"), "Why I Want to Go": e_rich_text("Ancient temples, bamboo forests, tea ceremonies, cherry blossoms. The cultural heart of Japan.")},
            {"Destination": e_title("Santorini, Greece"), "Country": e_rich_text("Greece"), "Region": e_select("Europe"), "Trip Type": e_select("Beach"), "Best Season": e_select("Summer"), "Estimated Budget": e_number(4000), "Priority": e_select("High"), "Why I Want to Go": e_rich_text("White-washed buildings, stunning sunsets, Mediterranean food, crystal clear water. Ultimate relaxation.")},
            {"Destination": e_title("Patagonia, Argentina/Chile"), "Country": e_rich_text("Argentina / Chile"), "Region": e_select("South America"), "Trip Type": e_select("Adventure"), "Best Season": e_select("Spring"), "Estimated Budget": e_number(5000), "Priority": e_select("High"), "Why I Want to Go": e_rich_text("Torres del Paine, glaciers, epic hiking. One of the most dramatic landscapes on Earth.")},
            {"Destination": e_title("Iceland Ring Road"), "Country": e_rich_text("Iceland"), "Region": e_select("Europe"), "Trip Type": e_select("Road Trip"), "Best Season": e_select("Summer"), "Estimated Budget": e_number(4500), "Priority": e_select("Medium"), "Why I Want to Go": e_rich_text("Northern lights, geysers, waterfalls, volcanic landscapes. 10-day ring road drive around the entire island.")},
            {"Destination": e_title("Marrakech, Morocco"), "Country": e_rich_text("Morocco"), "Region": e_select("Africa"), "Trip Type": e_select("Cultural"), "Best Season": e_select("Spring"), "Estimated Budget": e_number(2000), "Priority": e_select("Medium"), "Why I Want to Go": e_rich_text("Vibrant souks, stunning architecture, incredible food, Sahara desert excursion. Affordable luxury.")},
            {"Destination": e_title("New Zealand South Island"), "Country": e_rich_text("New Zealand"), "Region": e_select("Oceania"), "Trip Type": e_select("Adventure"), "Best Season": e_select("Summer"), "Estimated Budget": e_number(6000), "Priority": e_select("Someday"), "Why I Want to Go": e_rich_text("Milford Sound, Queenstown adventure capital, Lord of the Rings landscapes. The ultimate adventure destination.")}
        ]
        for entry in bucket_entries:
            add_entry(bucket_db, entry)
            time.sleep(0.35)

    # Enhanced remaining sections
    append_blocks(page_id, [
        divider(),
        heading2("Travel Dashboard"),
        column_list([
            [
                callout_rich("\u2708\uFE0F", [
                    text("2026 Travel Stats\n", bold=True),
                    text("Trips Planned:     4\nTrips Completed:   0\nCountries Visited: 0 (this year)\nTotal Budget:      $11,500\nSpent So Far:      $2,100 (deposits)\n\nNext Trip: NYC (Mar 20-23)\nBiggest Trip: Tokyo (Apr 10-20)")
                ], "blue_background")
            ],
            [
                callout_rich("\uD83D\uDDFA\uFE0F", [
                    text("Lifetime Travel Goals\n", bold=True),
                    text("Countries Visited:   8 / 30 goal\nContinents:          3 / 7\nBucket List Done:    0 / 6\n\nThis Year's Goal: Visit 3 new countries\n\nDream Trip: 3-week Southeast\nAsia backpacking adventure")
                ], "purple_background")
            ]
        ]),

        divider(),
        callout_rich("\uD83D\uDCB0", [
            text("Travel Budget Tips\n", bold=True),
            text("\u2022 Book flights 6-8 weeks in advance for domestic, 3 months for international\n\u2022 Use Google Flights alerts for price drops\n\u2022 Consider Airbnb for stays over 3 nights\n\u2022 Research free walking tours at your destination\n\u2022 Set a daily spending limit and track with a travel app\n\u2022 Notify your bank before international travel\n\u2022 Get a no-foreign-transaction-fee credit card\n\u2022 Book accommodations with free cancellation when possible\n\u2022 Travel in shoulder season for better prices and fewer crowds")
        ], "green_background"),

        divider(),
        heading2("Trip Expense Tracker"),
        paragraph("Track every expense during your trips. Categorize spending to understand where your travel budget goes and plan better next time."),
        toggle("Expense Tracking Template", [
            callout_rich("\uD83D\uDCB3", [
                text("Trip: _______________\n", bold=True),
                text("Daily Budget: $___  |  Trip Budget: $___\n\nCategories:\n\u2022 Accommodation: $___\n\u2022 Food & Dining: $___\n\u2022 Transportation: $___\n\u2022 Activities & Attractions: $___\n\u2022 Shopping & Souvenirs: $___\n\u2022 Tips & Miscellaneous: $___\n\nTotal Spent: $___\nRemaining Budget: $___\n\nCurrency Conversion Rate: 1 USD = ___")
            ], "blue_background")
        ]),

        divider(),
        heading2("Restaurant & Food Guide"),
        toggle("Must-Try Restaurants & Food Experiences", [
            paragraph("Research and save restaurant recommendations before each trip:", bold=True),
            divider(),
            paragraph("Tokyo Japan:", bold=True),
            bullet("\u2B50 Ichiran Ramen \u2014 Shibuya \u2014 Famous solo-booth ramen ($12)"),
            bullet("\u2B50 Tsukiji Outer Market \u2014 Fresh sushi breakfast ($15-30)"),
            bullet("\u2B50 Gonpachi \u2014 Roppongi \u2014 'Kill Bill' restaurant ($25-40)"),
            bullet("Convenience stores (7-Eleven, Lawson) \u2014 Amazing quality snacks ($3-5)"),
            divider(),
            paragraph("Barcelona Spain:", bold=True),
            bullet("\u2B50 La Boqueria Market \u2014 La Rambla \u2014 Street food paradise ($10-20)"),
            bullet("\u2B50 Cerveceria Catalana \u2014 Eixample \u2014 Best tapas in city ($15-25)"),
            bullet("El Xampanyet \u2014 Born \u2014 Classic cava bar ($10-15)"),
            divider(),
            paragraph("Add your own recommendations:", italic=True),
            bullet("[City]: [Restaurant] \u2014 [Area] \u2014 [Notes] ($___)")
        ]),

        divider(),
        heading2("Trip Countdown"),
        callout_rich("\u23F3", [
            text("Upcoming Trip Countdowns\n", bold=True),
            text("\uD83D\uDDFD NYC Weekend Getaway:  27 days away!\n\u2708\uFE0F San Francisco Tech Conf: 73 days!\n\uD83C\uDF38 Tokyo Japan:          48 days!\n\u2600\uFE0F Barcelona Spain:      114 days!\n\nNext trip to book: _______________ ")
        ], "purple_background"),

        divider(),
        callout_rich("\u2708\uFE0F", [
            text("Travel Philosophy\n\n", bold=True),
            text("Travel is the only thing you buy that makes you richer. Every trip expands your perspective, builds empathy, and creates memories that last a lifetime. Don't wait for the perfect moment \u2014 book the trip, pack light, and embrace the unexpected.\n\nThe world is a book, and those who do not travel read only one page.", italic=True)
        ], "yellow_background")
    ])

    print("  Template 7 COMPLETE!")
    return page_id


# ========================================================
# TEMPLATE 8: SECOND BRAIN / KNOWLEDGE VAULT
# ========================================================
def build_template_8():
    print("\n=== TEMPLATE 8: Second Brain / Knowledge Vault ===")

    children = [
        heading1("Second Brain / Knowledge Vault"),
        paragraph("Capture, organize, and retrieve everything you learn. Build a personal knowledge management system that grows with you. Never lose a brilliant idea, insightful article, or key takeaway again.", italic=True, color="gray"),
        divider(),
        toggle("Getting Started \u2014 How to Use This Template", [
            numbered("Start capturing \u2014 add articles, books, podcasts, and ideas to the Knowledge Base"),
            numbered("Track your reading in the Reading List database"),
            numbered("Use the Quick Capture Inbox for rapid idea capture throughout the day"),
            numbered("Process your inbox during the Weekly Knowledge Review"),
            numbered("Write Permanent Notes for your best insights (Zettelkasten method)"),
            numbered("Tag everything \u2014 connections between topics reveal breakthrough insights"),
            numbered("Turn your best knowledge into content using the Creation Pipeline"),
            divider(),
            callout_rich("\uD83D\uDCA1", [text("Tip: ", bold=True), text("Use the Notion Web Clipper browser extension to save articles directly into your Knowledge Base. Set up Gallery view for a beautiful visual library.")], "yellow_background")
        ]),
        divider(),
        callout_rich("\uD83E\uDDE0", [
            text("The PARA Method: ", bold=True),
            text("Organize information by actionability. Projects (active work), Areas (ongoing responsibilities), Resources (reference material), Archive (completed items). This vault serves as your Resource hub for knowledge capture.")
        ], "purple_background"),
        heading2("Knowledge Base")
    ]

    page_id = create_page("Second Brain / Knowledge Vault", "\uD83E\uDDE0", children)
    if not page_id:
        return

    db_id = create_database(page_id, "Knowledge Base", {
        "Title": title_prop(),
        "Category": select_prop(["Article", "Book", "Video", "Podcast", "Course", "Research", "Idea"]),
        "Source": url_prop(),
        "Tags": multi_select_prop(["AI", "Business", "Health", "Technology", "Science", "Philosophy", "Productivity", "Finance"]),
        "Status": status_prop([]),
        "Rating": select_prop(["\u2B50", "\u2B50\u2B50", "\u2B50\u2B50\u2B50", "\u2B50\u2B50\u2B50\u2B50", "\u2B50\u2B50\u2B50\u2B50\u2B50"]),
        "Date Added": date_prop(),
        "Key Takeaways": rich_text_prop()
    })

    if not db_id:
        return

    entries = [
        {"Title": e_title("Atomic Habits by James Clear"), "Category": e_select("Book"), "Source": e_url("https://jamesclear.com/atomic-habits"), "Tags": e_multi_select(["Productivity", "Health"]), "Rating": e_select("\u2B50\u2B50\u2B50\u2B50\u2B50"), "Date Added": e_date("2026-01-15"), "Key Takeaways": e_rich_text("1% better every day compounds. Systems > Goals. Habit stacking for new behaviors. Environment design matters more than motivation.")},
        {"Title": e_title("The State of AI Report 2026"), "Category": e_select("Research"), "Source": e_url("https://www.stateof.ai"), "Tags": e_multi_select(["AI", "Technology"]), "Rating": e_select("\u2B50\u2B50\u2B50\u2B50"), "Date Added": e_date("2026-02-01"), "Key Takeaways": e_rich_text("Multimodal AI is mainstream. Open source models closing gap. AI regulation accelerating globally. Key players: Anthropic, OpenAI, Google DeepMind.")},
        {"Title": e_title("How to Build a Second Brain - Tiago Forte"), "Category": e_select("Course"), "Source": e_url("https://www.buildingasecondbrain.com"), "Tags": e_multi_select(["Productivity", "Business"]), "Rating": e_select("\u2B50\u2B50\u2B50\u2B50\u2B50"), "Date Added": e_date("2026-01-20"), "Key Takeaways": e_rich_text("CODE method: Capture, Organize, Distill, Express. Progressive summarization for notes. Save only what resonates. Share your knowledge to solidify learning.")},
        {"Title": e_title("The Psychology of Money - Morgan Housel"), "Category": e_select("Book"), "Source": e_url("https://www.collaborativefund.com/blog/the-psychology-of-money/"), "Tags": e_multi_select(["Finance", "Philosophy"]), "Rating": e_select("\u2B50\u2B50\u2B50\u2B50"), "Date Added": e_date("2026-02-10"), "Key Takeaways": e_rich_text("Wealth is what you don't see. Compounding is the 8th wonder. Room for error in financial planning. Savings rate matters more than income.")},
        {"Title": e_title("Huberman Lab: Optimize Sleep"), "Category": e_select("Podcast"), "Source": e_url("https://hubermanlab.com"), "Tags": e_multi_select(["Health", "Science"]), "Rating": e_select("\u2B50\u2B50\u2B50\u2B50\u2B50"), "Date Added": e_date("2026-02-15"), "Key Takeaways": e_rich_text("Morning sunlight exposure critical. Cool room temperature for sleep. No caffeine after 2 PM. Consistent wake time matters most. NSDR protocols for recovery.")}
    ]

    for entry in entries:
        add_entry(db_id, entry)
        time.sleep(0.35)

    # Reading List database
    append_blocks(page_id, [
        divider(),
        heading2("Reading List"),
        paragraph("Track every book you want to read, are reading, or have finished. Build your personal library and never forget a great recommendation.")
    ])
    time.sleep(0.5)

    reading_db = create_database(page_id, "Reading List", {
        "Book Title": title_prop(),
        "Author": rich_text_prop(),
        "Genre": select_prop(["Business", "Self-Help", "Science", "Philosophy", "Biography", "Fiction", "Technology", "Finance", "Psychology", "Health"]),
        "Status": status_prop([]),
        "Rating": select_prop(["\u2B50", "\u2B50\u2B50", "\u2B50\u2B50\u2B50", "\u2B50\u2B50\u2B50\u2B50", "\u2B50\u2B50\u2B50\u2B50\u2B50"]),
        "Date Started": date_prop(),
        "Date Finished": date_prop(),
        "Pages": number_prop(),
        "Format": select_prop(["Physical", "Kindle", "Audiobook", "PDF"]),
        "Key Takeaways": rich_text_prop(),
        "Recommended By": rich_text_prop()
    })

    if reading_db:
        reading_entries = [
            {"Book Title": e_title("Atomic Habits"), "Author": e_rich_text("James Clear"), "Genre": e_select("Self-Help"), "Rating": e_select("\u2B50\u2B50\u2B50\u2B50\u2B50"), "Date Started": e_date("2026-01-10"), "Date Finished": e_date("2026-01-28"), "Pages": e_number(320), "Format": e_select("Physical"), "Key Takeaways": e_rich_text("1% improvement compounds. Systems > Goals. Habit stacking. Identity-based habits. Environment design."), "Recommended By": e_rich_text("Multiple friends + online reviews")},
            {"Book Title": e_title("Deep Work"), "Author": e_rich_text("Cal Newport"), "Genre": e_select("Business"), "Rating": e_select("\u2B50\u2B50\u2B50\u2B50"), "Date Started": e_date("2026-02-01"), "Date Finished": e_date("2026-02-14"), "Pages": e_number(296), "Format": e_select("Kindle"), "Key Takeaways": e_rich_text("Deep work is rare and valuable. Schedule deep work blocks. Quit social media or limit it severely. Embrace boredom."), "Recommended By": e_rich_text("Tim Ferriss podcast")},
            {"Book Title": e_title("The Psychology of Money"), "Author": e_rich_text("Morgan Housel"), "Genre": e_select("Finance"), "Rating": e_select("\u2B50\u2B50\u2B50\u2B50"), "Date Started": e_date("2026-02-15"), "Pages": e_number(256), "Format": e_select("Audiobook"), "Key Takeaways": e_rich_text("Currently reading. Great insights on behavioral finance."), "Recommended By": e_rich_text("Bill Gates reading list")},
            {"Book Title": e_title("Thinking, Fast and Slow"), "Author": e_rich_text("Daniel Kahneman"), "Genre": e_select("Psychology"), "Pages": e_number(499), "Format": e_select("Physical"), "Key Takeaways": e_rich_text("On the reading list. System 1 vs System 2 thinking."), "Recommended By": e_rich_text("Top 100 business books of all time")},
            {"Book Title": e_title("The Almanack of Naval Ravikant"), "Author": e_rich_text("Eric Jorgenson"), "Genre": e_select("Philosophy"), "Pages": e_number(242), "Format": e_select("Kindle"), "Key Takeaways": e_rich_text("On the reading list. Wealth creation, happiness, and life philosophy."), "Recommended By": e_rich_text("Twitter/podcast community")},
            {"Book Title": e_title("Outlive: The Science & Art of Longevity"), "Author": e_rich_text("Peter Attia"), "Genre": e_select("Health"), "Pages": e_number(496), "Format": e_select("Audiobook"), "Key Takeaways": e_rich_text("On the reading list. Proactive health and longevity science."), "Recommended By": e_rich_text("Huberman Lab podcast")}
        ]
        for entry in reading_entries:
            add_entry(reading_db, entry)
            time.sleep(0.35)

    # Enhanced remaining sections
    append_blocks(page_id, [
        divider(),

        # Quick capture
        callout_rich("\u26A1", [
            text("Quick Capture Inbox\n", bold=True),
            text("Drop ideas, links, and notes here instantly.\nProcess during your weekly review.\nDon't worry about organization \u2014 just capture!")
        ], "yellow_background"),
        todo_block(""),
        todo_block(""),
        todo_block(""),

        divider(),

        # Dashboard
        heading2("Knowledge Dashboard"),
        column_list([
            [
                callout_rich("\uD83D\uDCDA", [
                    text("Reading Progress\n", bold=True),
                    text("Books Read (2026):    2\nCurrently Reading:    1\nReading List:         3\nPages This Month:     552\n\nGoal: 24 books this year\nPace: 2/month needed\nStatus: ON TRACK \u2705")
                ], "green_background")
            ],
            [
                callout_rich("\uD83E\uDDE0", [
                    text("Knowledge Stats\n", bold=True),
                    text("Items Captured:       12\nArticles Saved:       4\nBooks Logged:         6\nPodcast Notes:        2\n\nTop Tags: Productivity, AI,\nHealth, Finance\n\nWeekly Input: ~5 items")
                ], "purple_background")
            ]
        ]),

        divider(),
        heading2("Weekly Knowledge Review"),
        paragraph("Every Sunday, spend 30 minutes reviewing and processing your knowledge vault:"),
        toggle("Weekly Review Checklist", [
            todo_block("Process Quick Capture Inbox \u2014 categorize or discard"),
            todo_block("Review all items captured this week"),
            todo_block("Add key takeaways and personal notes to each entry"),
            todo_block("Tag and categorize new entries properly"),
            todo_block("Archive items that are no longer relevant"),
            todo_block("Identify 1-3 ideas to apply this coming week"),
            todo_block("Share one insight with someone (teach to learn)"),
            todo_block("Update Reading List status"),
            divider(),
            callout_rich("\uD83D\uDCA1", [
                text("Progressive Summarization: ", bold=True),
                text("Each time you revisit a note, highlight the most important parts. Layer 1: Save. Layer 2: Bold key passages. Layer 3: Highlight the highlights. Layer 4: Write your own summary.")
            ], "blue_background")
        ]),

        divider(),
        heading2("Learning Goals & Projects"),
        toggle("Current Learning Objectives", [
            callout_rich("\uD83C\uDFAF", [
                text("2026 Learning Goals\n", bold=True),
                text("1. Read 24 books (2/month)\n2. Build expertise in AI/ML fundamentals\n3. Develop financial literacy\n4. Complete BASB course\n5. Write 12 article summaries (1/month)\n6. Listen to 50+ podcast episodes with notes")
            ], "blue_background"),
            divider(),
            todo_block("Complete Building a Second Brain course"),
            todo_block("Read 2 books per month (24 total)"),
            todo_block("Listen to 4 podcast episodes per week with notes"),
            todo_block("Write one summary/reflection per week"),
            todo_block("Build expertise in AI/ML \u2014 3 courses + 5 papers"),
            todo_block("Develop financial literacy \u2014 read 4 finance books"),
            todo_block("Start a personal blog \u2014 publish 1 article/month")
        ]),

        toggle("Knowledge Areas Map", [
            paragraph("Areas I'm actively exploring and building expertise in:", bold=True),
            divider(),
            bullet_rich([text("Artificial Intelligence & ML ", bold=True), text("\u2014 Transformers, LLMs, prompt engineering, AI agents")]),
            bullet_rich([text("Personal Finance & Investing ", bold=True), text("\u2014 Index funds, tax optimization, retirement planning")]),
            bullet_rich([text("Systems Thinking ", bold=True), text("\u2014 Mental models, feedback loops, complex adaptive systems")]),
            bullet_rich([text("Health Optimization ", bold=True), text("\u2014 Sleep science, nutrition, exercise physiology, longevity")]),
            bullet_rich([text("Philosophy & Decision Making ", bold=True), text("\u2014 Stoicism, cognitive biases, probabilistic thinking")]),
            bullet_rich([text("Business & Entrepreneurship ", bold=True), text("\u2014 Product development, marketing, growth, revenue models")]),
            bullet_rich([text("Writing & Communication ", bold=True), text("\u2014 Clear writing, storytelling, public speaking, persuasion")])
        ]),

        divider(),
        heading2("Note-Taking Frameworks"),
        toggle("Methods & Templates for Better Notes", [
            callout_rich("\uD83D\uDCDD", [
                text("CODE Method (Tiago Forte)\n", bold=True),
                text("Capture \u2014 Save what resonates with you\nOrganize \u2014 Place it where it will be useful\nDistill \u2014 Find the essential message\nExpress \u2014 Share your knowledge with others")
            ], "blue_background"),
            divider(),
            callout_rich("\uD83D\uDCA1", [
                text("Zettelkasten Method\n", bold=True),
                text("Write atomic notes (one idea per note)\nLink notes to each other\nBuild a web of interconnected ideas\nLet insights emerge from connections")
            ], "purple_background"),
            divider(),
            paragraph("Book Notes Template:", bold=True),
            bullet("Title, Author, Date Read"),
            bullet("One-sentence summary"),
            bullet("Top 3 key ideas"),
            bullet("Favorite quotes (2-3)"),
            bullet("How I'll apply this"),
            bullet("Who should read this and why")
        ]),

        divider(),
        heading2("Permanent Notes (Zettelkasten)"),
        callout_rich("\uD83D\uDD17", [
            text("Atomic Notes System\n", bold=True),
            text("Write one insight per note. Link notes to each other. Over time, a web of interconnected knowledge emerges \u2014 producing original ideas you'd never have found otherwise.")
        ], "purple_background"),
        toggle("How to Write Permanent Notes", [
            numbered("Capture a fleeting note (quick thought or highlight)"),
            numbered("Rewrite it in your OWN words as a complete thought"),
            numbered("Make it atomic \u2014 one idea per note"),
            numbered("Link it to related permanent notes"),
            numbered("Add it to relevant topic clusters"),
            numbered("Let connections spark new insights over time"),
            divider(),
            paragraph("Example Permanent Note:", bold=True),
            callout_rich("\uD83D\uDCDD", [
                text("Title: ", bold=True), text("Compound Interest Applies to Habits, Not Just Money\n\n"),
                text("Getting 1% better each day = 37x improvement over a year. This mirrors compound interest in finance. Small, consistent actions create exponential results because each improvement builds on the last.\n\n"),
                text("Connected to: ", italic=True), text("Atomic Habits (book), Systems vs Goals, Consistency Principle")
            ], "gray_background")
        ]),

        divider(),
        heading2("Content Creation Pipeline"),
        toggle("Turn Knowledge Into Content", [
            callout_rich("\uD83D\uDE80", [
                text("Knowledge \u2192 Content Pipeline\n", bold=True),
                text("Your second brain is a content goldmine. Turn your best insights into shareable content:")
            ], "blue_background"),
            divider(),
            numbered("Review your top-rated Knowledge Base entries weekly"),
            numbered("Identify 2-3 insights that would help others"),
            numbered("Draft a thread, article, or video outline from your notes"),
            numbered("Publish and share \u2014 teaching solidifies your learning"),
            numbered("Track engagement and iterate on what resonates"),
            divider(),
            paragraph("Content Ideas from My Knowledge Base:", bold=True),
            todo_block("Write about: _______________"),
            todo_block("Create thread on: _______________"),
            todo_block("Record video about: _______________")
        ]),

        divider(),
        callout_rich("\uD83E\uDDE0", [
            text("The Second Brain Philosophy\n\n", bold=True),
            text("Your brain is for having ideas, not storing them. By building a trusted external system, you free your mind for creative thinking, deep work, and making connections.\n\nDon't just collect \u2014 connect. The magic happens when you link ideas across domains and create your own insights. The best second brain is one you actually use every day.\n\nCapture generously. Organize minimally. Share fearlessly.", italic=True)
        ], "blue_background")
    ])

    print("  Template 8 COMPLETE!")
    return page_id


# ========================================================
# TEMPLATE 9: LIFE OS - MASTER DASHBOARD
# ========================================================
def build_template_9():
    print("\n=== TEMPLATE 9: Life OS - Master Dashboard ===")

    children = [
        heading1("Life OS \u2014 Personal Command Center"),
        paragraph("Your all-in-one operating system for designing an intentional life. Set ambitious goals, build powerful habits, manage projects, reflect daily, and continuously evolve. This is mission control for every dimension of your life \u2014 health, career, finances, relationships, growth, and fulfillment.", italic=True, color="gray"),
        divider(),
        table_of_contents("gray"),
        divider(),

        # === QUICK NAVIGATION & INBOX ===
        column_list([
            # Left column: Navigation
            [
                callout_rich("\uD83E\uDDED", [
                    text("Quick Navigation\n", bold=True),
                    text("\u2193 Dashboard & Today's Focus\n\u2193 Goals & Vision Board\n\u2193 Projects Hub\n\u2193 Daily Habits & Routines\n\u2193 Journal & Reflections\n\u2193 Areas of Life\n\u2193 Review System\n\u2193 Resources & Reference")
                ], "purple_background")
            ],
            # Right column: Inbox
            [
                callout_rich("\u26A1", [
                    text("Quick Capture Inbox\n", bold=True),
                    text("Drop ideas, tasks, and notes here instantly.\nProcess during your daily review.")
                ], "yellow_background"),
                todo_block(""),
                todo_block(""),
                todo_block("")
            ]
        ]),

        divider(),

        # === DASHBOARD ===
        heading2("\uD83D\uDCCA Dashboard"),
        column_list([
            # Left: Today's Focus
            [
                callout_rich("\uD83C\uDFAF", [
                    text("Today's Focus\n", bold=True),
                    text("Top 3 Priorities:\n1. _______________\n2. _______________\n3. _______________\n\nDaily Intention: _______________\nKey Deadline: _______________")
                ], "blue_background")
            ],
            # Right: Scorecard
            [
                callout_rich("\uD83D\uDCC8", [
                    text("Weekly Scorecard\n", bold=True),
                    text("Habits Completed:  _ / _\nTasks Completed:   _ / _\nGoals On Track:    _ / _\nEnergy Level:      _ / 10\nMood Average:      _ / 5")
                ], "green_background")
            ]
        ]),

        divider(),

        # === GOALS & VISION ===
        heading2("\uD83C\uDFAF Goals & Vision Board"),
        callout_rich("\uD83D\uDCA1", [
            text("Goal-Setting Framework: ", bold=True),
            text("Define goals using the SMART method (Specific, Measurable, Achievable, Relevant, Time-bound). Break each goal into Key Results \u2014 concrete milestones that prove you're making progress. Review goals weekly and adjust quarterly.")
        ], "blue_background"),
        heading3("Annual Goals")
    ]

    page_id = create_page("Life OS \u2014 Personal Command Center", "\uD83C\uDFE0", children)
    if not page_id:
        return

    # === GOALS DATABASE ===
    goals_db = create_database(page_id, "Goals & OKRs", {
        "Goal": title_prop(),
        "Area": select_prop(["Health & Fitness", "Career & Work", "Finance", "Relationships", "Personal Growth", "Learning", "Creative", "Fun & Adventure"]),
        "Timeline": select_prop(["This Week", "This Month", "This Quarter", "This Year", "Long-term"]),
        "Status": status_prop([]),
        "Priority": select_prop(["Critical", "High", "Medium", "Low"]),
        "Target Date": date_prop(),
        "Progress %": number_prop("percent"),
        "Key Results": rich_text_prop(),
        "Why It Matters": rich_text_prop()
    })

    if goals_db:
        goal_entries = [
            {"Goal": e_title("Run a Half Marathon"), "Area": e_select("Health & Fitness"), "Timeline": e_select("This Quarter"), "Priority": e_select("High"), "Target Date": e_date("2026-06-01"), "Progress %": e_number(35), "Key Results": e_rich_text("1) Run 3x/week consistently  2) Complete 10K under 50 min  3) Follow 12-week training plan  4) Race day: finish under 2:00:00"), "Why It Matters": e_rich_text("Physical health is the foundation of everything else. Completing this proves I can commit to a long-term goal.")},
            {"Goal": e_title("Launch Side Project MVP"), "Area": e_select("Career & Work"), "Timeline": e_select("This Quarter"), "Priority": e_select("Critical"), "Target Date": e_date("2026-04-15"), "Progress %": e_number(60), "Key Results": e_rich_text("1) Core features complete  2) Landing page live  3) 50 beta signups  4) First user feedback round"), "Why It Matters": e_rich_text("Building something of my own develops entrepreneurial skills and creates an additional income stream.")},
            {"Goal": e_title("Build $10K Emergency Fund"), "Area": e_select("Finance"), "Timeline": e_select("This Year"), "Priority": e_select("High"), "Target Date": e_date("2026-12-31"), "Progress %": e_number(65), "Key Results": e_rich_text("1) Save $800/month minimum  2) Reduce discretionary spending by 20%  3) Set up auto-transfer on payday  4) Reach $10K by December"), "Why It Matters": e_rich_text("Financial security reduces stress and creates freedom to take calculated risks in career and life.")},
            {"Goal": e_title("Read 24 Books This Year"), "Area": e_select("Learning"), "Timeline": e_select("This Year"), "Priority": e_select("Medium"), "Target Date": e_date("2026-12-31"), "Progress %": e_number(17), "Key Results": e_rich_text("1) Read 30 min daily minimum  2) Finish 2 books/month  3) Write summary for each book  4) Apply 1 key insight from each"), "Why It Matters": e_rich_text("Continuous learning compounds over time. Reading widely builds mental models for better decision-making.")},
            {"Goal": e_title("Meditate 100 Consecutive Days"), "Area": e_select("Health & Fitness"), "Timeline": e_select("This Quarter"), "Priority": e_select("High"), "Target Date": e_date("2026-05-30"), "Progress %": e_number(42), "Key Results": e_rich_text("1) 15 min morning meditation daily  2) No breaks in streak  3) Try 3 different techniques  4) Notice measurable calm improvement"), "Why It Matters": e_rich_text("Mental clarity and emotional regulation improve every other area of life.")},
            {"Goal": e_title("Get Promoted to Senior Role"), "Area": e_select("Career & Work"), "Timeline": e_select("This Year"), "Priority": e_select("Critical"), "Target Date": e_date("2026-12-31"), "Progress %": e_number(40), "Key Results": e_rich_text("1) Lead 2 major projects successfully  2) Mentor 1 junior team member  3) Get exceeds expectations on review  4) Build visibility with leadership"), "Why It Matters": e_rich_text("Career advancement increases income, impact, and opens doors for the next chapter.")},
            {"Goal": e_title("Learn Conversational Spanish"), "Area": e_select("Learning"), "Timeline": e_select("This Year"), "Priority": e_select("Medium"), "Target Date": e_date("2026-12-31"), "Progress %": e_number(20), "Key Results": e_rich_text("1) Complete Duolingo tree  2) Hold 15-min conversation with native speaker  3) Watch 1 Spanish show/week  4) Practice 20 min daily"), "Why It Matters": e_rich_text("Opens up travel, culture, and connection with Spanish-speaking communities worldwide.")},
            {"Goal": e_title("Plan & Execute Japan Trip"), "Area": e_select("Fun & Adventure"), "Timeline": e_select("This Month"), "Priority": e_select("Low"), "Target Date": e_date("2026-03-15"), "Progress %": e_number(75), "Key Results": e_rich_text("1) Book flights and hotels  2) Create day-by-day itinerary  3) Budget $4,500 saved  4) Learn 20 essential Japanese phrases"), "Why It Matters": e_rich_text("Life isn't just about goals and productivity \u2014 experiencing new cultures creates lasting memories and perspective.")}
        ]
        for entry in goal_entries:
            add_entry(goals_db, entry)
            time.sleep(0.35)

    # === VISION BOARD SECTION ===
    append_blocks(page_id, [
        divider(),
        toggle("My Vision Board \u2014 Where I'm Headed", [
            callout_rich("\uD83C\uDF1F", [
                text("1-Year Vision\n", bold=True),
                text("By February 2027, I will have...\n\u2022 Launched a profitable side project\n\u2022 Achieved peak physical fitness\n\u2022 Built a 6-month financial runway\n\u2022 Developed a daily meditation practice\n\u2022 Traveled to 2 new countries\n\u2022 Read 24+ books and applied key insights")
            ], "purple_background"),
            callout_rich("\uD83D\uDE80", [
                text("5-Year Vision\n", bold=True),
                text("By 2031, I will have...\n\u2022 Built a business generating $XX,XXX/month\n\u2022 Achieved financial independence\n\u2022 Maintained excellent health and energy\n\u2022 Deep, meaningful relationships\n\u2022 Traveled to 15+ countries\n\u2022 Become an expert in my field")
            ], "blue_background"),
            callout_rich("\u2764\uFE0F", [
                text("Core Values\n", bold=True),
                text("\u2022 Growth \u2014 Always be learning and evolving\n\u2022 Health \u2014 Body and mind are the foundation\n\u2022 Impact \u2014 Create value for others\n\u2022 Freedom \u2014 Design life on my own terms\n\u2022 Connection \u2014 Nurture deep relationships\n\u2022 Adventure \u2014 Say yes to new experiences")
            ], "red_background")
        ]),

        divider(),

        # === PROJECTS HUB ===
        heading2("\uD83D\uDE80 Projects Hub"),
        callout_rich("\uD83D\uDCA1", [
            text("Project Management: ", bold=True),
            text("Every goal breaks down into projects. Every project breaks down into tasks. Keep active projects to 3-5 maximum for focused execution. Archive completed projects to maintain clarity.")
        ], "blue_background")
    ])
    time.sleep(0.5)

    # === PROJECTS DATABASE ===
    projects_db = create_database(page_id, "Projects", {
        "Project": title_prop(),
        "Area": select_prop(["Health & Fitness", "Career & Work", "Finance", "Relationships", "Personal Growth", "Learning", "Creative", "Fun & Adventure"]),
        "Status": status_prop([]),
        "Priority": select_prop(["Critical", "High", "Medium", "Low"]),
        "Deadline": date_prop(),
        "Effort": select_prop(["Small (< 1 week)", "Medium (1-4 weeks)", "Large (1-3 months)", "XL (3+ months)"]),
        "Progress %": number_prop("percent"),
        "Next Action": rich_text_prop(),
        "Notes": rich_text_prop(),
        "URL": url_prop()
    })

    if projects_db:
        project_entries = [
            {"Project": e_title("Personal Website Redesign"), "Area": e_select("Creative"), "Priority": e_select("High"), "Deadline": e_date("2026-03-15"), "Effort": e_select("Medium (1-4 weeks)"), "Progress %": e_number(70), "Next Action": e_rich_text("Finalize responsive design and deploy to production"), "Notes": e_rich_text("Using Next.js + Tailwind. Portfolio section needs 3 more case studies. SEO optimization pending.")},
            {"Project": e_title("Expense Tracker App (Side Project)"), "Area": e_select("Career & Work"), "Priority": e_select("Critical"), "Deadline": e_date("2026-04-15"), "Effort": e_select("Large (1-3 months)"), "Progress %": e_number(45), "Next Action": e_rich_text("Build authentication flow and dashboard UI"), "Notes": e_rich_text("React Native + Firebase. MVP features: expense logging, categories, monthly charts, export to CSV.")},
            {"Project": e_title("Half Marathon Training Program"), "Area": e_select("Health & Fitness"), "Priority": e_select("High"), "Deadline": e_date("2026-05-15"), "Effort": e_select("Large (1-3 months)"), "Progress %": e_number(35), "Next Action": e_rich_text("Complete Week 5 long run (8 miles)"), "Notes": e_rich_text("Following Hal Higdon Novice 2 plan. Current pace: 9:15/mile. Target race pace: 8:45/mile.")},
            {"Project": e_title("Q1 Performance Review Prep"), "Area": e_select("Career & Work"), "Priority": e_select("High"), "Deadline": e_date("2026-03-20"), "Effort": e_select("Small (< 1 week)"), "Progress %": e_number(20), "Next Action": e_rich_text("Document key achievements and metrics from Q1"), "Notes": e_rich_text("Gather project impact data, peer feedback, and examples of leadership moments.")},
            {"Project": e_title("Home Office Upgrade"), "Area": e_select("Personal Growth"), "Priority": e_select("Low"), "Deadline": e_date("2026-04-01"), "Effort": e_select("Small (< 1 week)"), "Progress %": e_number(50), "Next Action": e_rich_text("Order standing desk converter and monitor arm"), "Notes": e_rich_text("Budget: $500. Need: standing desk, better lighting, cable management, plant.")},
            {"Project": e_title("Spanish Course \u2014 Module 3"), "Area": e_select("Learning"), "Priority": e_select("Medium"), "Deadline": e_date("2026-03-30"), "Effort": e_select("Medium (1-4 weeks)"), "Progress %": e_number(30), "Next Action": e_rich_text("Complete Unit 7 verb conjugations and practice dialogue"), "Notes": e_rich_text("Using Pimsleur + Duolingo combo. Schedule iTalki conversation practice for next week.")}
        ]
        for entry in project_entries:
            add_entry(projects_db, entry)
            time.sleep(0.35)

    append_blocks(page_id, [
        divider(),

        # === HABITS & ROUTINES ===
        heading2("\uD83D\uDD04 Daily Habits & Routines"),
        callout_rich("\uD83D\uDCA1", [
            text("Habit Architecture: ", bold=True),
            text("Design your habits using the Cue \u2192 Routine \u2192 Reward loop. Stack new habits onto existing ones. Start with 2-minute versions and scale up. Track your streaks \u2014 consistency is the compound interest of self-improvement.")
        ], "blue_background")
    ])
    time.sleep(0.5)

    # === HABITS DATABASE ===
    habits_db = create_database(page_id, "Habits", {
        "Habit": title_prop(),
        "Category": select_prop(["Health", "Productivity", "Mindfulness", "Fitness", "Learning", "Social", "Creative", "Finance"]),
        "Frequency": select_prop(["Daily", "Weekdays", "Weekends", "3x/Week", "Weekly"]),
        "Time of Day": select_prop(["Morning", "Midday", "Afternoon", "Evening", "Anytime"]),
        "Duration": rich_text_prop(),
        "Streak": number_prop(),
        "Status": status_prop([]),
        "Priority": select_prop(["High", "Medium", "Low"]),
        "Cue / Trigger": rich_text_prop(),
        "Reward": rich_text_prop()
    })

    if habits_db:
        habit_entries = [
            {"Habit": e_title("Morning Meditation"), "Category": e_select("Mindfulness"), "Frequency": e_select("Daily"), "Time of Day": e_select("Morning"), "Duration": e_rich_text("15 minutes"), "Streak": e_number(42), "Priority": e_select("High"), "Cue / Trigger": e_rich_text("After waking up, before checking phone"), "Reward": e_rich_text("Feeling of calm clarity to start the day")},
            {"Habit": e_title("Exercise / Workout"), "Category": e_select("Fitness"), "Frequency": e_select("Weekdays"), "Time of Day": e_select("Morning"), "Duration": e_rich_text("45 minutes"), "Streak": e_number(12), "Priority": e_select("High"), "Cue / Trigger": e_rich_text("Put on workout clothes immediately after meditation"), "Reward": e_rich_text("Post-workout smoothie + energy boost")},
            {"Habit": e_title("Read for 30 Minutes"), "Category": e_select("Learning"), "Frequency": e_select("Daily"), "Time of Day": e_select("Evening"), "Duration": e_rich_text("30 minutes"), "Streak": e_number(28), "Priority": e_select("High"), "Cue / Trigger": e_rich_text("After dinner, sit in reading chair"), "Reward": e_rich_text("Track book progress + update reading list")},
            {"Habit": e_title("Daily Journal & Reflection"), "Category": e_select("Mindfulness"), "Frequency": e_select("Daily"), "Time of Day": e_select("Evening"), "Duration": e_rich_text("10 minutes"), "Streak": e_number(35), "Priority": e_select("High"), "Cue / Trigger": e_rich_text("After reading, before bed"), "Reward": e_rich_text("Mental clarity + tracking personal growth")},
            {"Habit": e_title("Drink 8 Glasses of Water"), "Category": e_select("Health"), "Frequency": e_select("Daily"), "Time of Day": e_select("Anytime"), "Duration": e_rich_text("Throughout day"), "Streak": e_number(18), "Priority": e_select("Medium"), "Cue / Trigger": e_rich_text("Keep water bottle visible on desk at all times"), "Reward": e_rich_text("Better energy, clearer skin, fewer headaches")},
            {"Habit": e_title("No Phone First Hour"), "Category": e_select("Productivity"), "Frequency": e_select("Daily"), "Time of Day": e_select("Morning"), "Duration": e_rich_text("60 minutes"), "Streak": e_number(7), "Priority": e_select("Medium"), "Cue / Trigger": e_rich_text("Phone stays in drawer until morning routine complete"), "Reward": e_rich_text("Focused, intentional start to the day")},
            {"Habit": e_title("Practice Spanish"), "Category": e_select("Learning"), "Frequency": e_select("Weekdays"), "Time of Day": e_select("Afternoon"), "Duration": e_rich_text("20 minutes"), "Streak": e_number(14), "Priority": e_select("Medium"), "Cue / Trigger": e_rich_text("After lunch break, open Duolingo"), "Reward": e_rich_text("Track streak + celebrate weekly milestones")},
            {"Habit": e_title("Gratitude Practice"), "Category": e_select("Mindfulness"), "Frequency": e_select("Daily"), "Time of Day": e_select("Morning"), "Duration": e_rich_text("5 minutes"), "Streak": e_number(42), "Priority": e_select("High"), "Cue / Trigger": e_rich_text("Part of morning meditation closing"), "Reward": e_rich_text("Shift to positive mindset for the day")}
        ]
        for entry in habit_entries:
            add_entry(habits_db, entry)
            time.sleep(0.35)

    # Routines section
    append_blocks(page_id, [
        divider(),
        column_list([
            [
                callout_rich("\uD83C\uDF05", [
                    text("Morning Routine (6:00 - 8:30 AM)\n", bold=True),
                    text("6:00 \u2014 Wake up, no snooze\n6:05 \u2014 Gratitude + intention setting (5 min)\n6:10 \u2014 Meditation (15 min)\n6:25 \u2014 Workout / Run (45 min)\n7:10 \u2014 Shower + get ready\n7:30 \u2014 Healthy breakfast\n7:50 \u2014 Review today's goals & calendar\n8:00 \u2014 Deep work block begins")
                ], "yellow_background")
            ],
            [
                callout_rich("\uD83C\uDF19", [
                    text("Evening Routine (8:00 - 10:30 PM)\n", bold=True),
                    text("8:00 \u2014 Devices on Do Not Disturb\n8:10 \u2014 Read (30 min)\n8:40 \u2014 Journal & daily reflection (10 min)\n8:50 \u2014 Plan tomorrow's top 3 priorities\n9:00 \u2014 Prepare for bed (skincare, etc.)\n9:15 \u2014 Wind down (music, stretching)\n9:30 \u2014 Lights out\n\nWeekly: Sunday evening planning session")
                ], "gray_background")
            ]
        ]),

        divider(),

        # === JOURNAL ===
        heading2("\uD83D\uDCD3 Journal & Reflections"),
        callout_rich("\uD83D\uDCA1", [
            text("Journaling Practice: ", bold=True),
            text("Daily journaling builds self-awareness and emotional intelligence. Log your mood, energy, wins, and challenges. Over time, patterns emerge that help you optimize your life. Be honest \u2014 this is your private space for radical self-reflection.")
        ], "blue_background")
    ])
    time.sleep(0.5)

    # === JOURNAL DATABASE ===
    journal_db = create_database(page_id, "Journal Entries", {
        "Entry": title_prop(),
        "Date": date_prop(),
        "Mood": select_prop(["\uD83E\uDD29 Amazing", "\uD83D\uDE0A Good", "\uD83D\uDE10 Okay", "\uD83D\uDE14 Tough", "\uD83D\uDE1E Rough"]),
        "Energy Level": select_prop(["\u26A1 High", "\uD83D\uDD0B Medium", "\uD83E\uDEAB Low"]),
        "Gratitude": rich_text_prop(),
        "Wins": rich_text_prop(),
        "Challenges": rich_text_prop(),
        "Lessons Learned": rich_text_prop(),
        "Tomorrow's Focus": rich_text_prop()
    })

    if journal_db:
        journal_entries = [
            {"Entry": e_title("Monday \u2014 Strong Start to the Week"), "Date": e_date("2026-02-16"), "Mood": e_select("\uD83D\uDE0A Good"), "Energy Level": e_select("\u26A1 High"), "Gratitude": e_rich_text("Grateful for morning sunshine, supportive team at work, and a quiet evening at home"), "Wins": e_rich_text("Completed 3 deep work hours before lunch. Nailed the project presentation. Kept meditation streak alive."), "Challenges": e_rich_text("Got pulled into an unplanned meeting that disrupted afternoon focus block."), "Lessons Learned": e_rich_text("Need to protect calendar blocks more aggressively. Set status to 'busy' during deep work."), "Tomorrow's Focus": e_rich_text("Finish project milestone #3 and schedule Q1 review prep meeting.")},
            {"Entry": e_title("Tuesday \u2014 Creative Flow Day"), "Date": e_date("2026-02-17"), "Mood": e_select("\uD83E\uDD29 Amazing"), "Energy Level": e_select("\u26A1 High"), "Gratitude": e_rich_text("Grateful for creative inspiration, great coffee shop find, and making progress on side project"), "Wins": e_rich_text("Side project UI breakthrough \u2014 dashboard design came together beautifully. Also hit 8-mile training run."), "Challenges": e_rich_text("Skipped Spanish practice. Evening routine started late."), "Lessons Learned": e_rich_text("Creative energy peaks in the afternoon for me. Schedule creative work after 2 PM."), "Tomorrow's Focus": e_rich_text("Spanish practice (double session to catch up) + code the authentication flow.")},
            {"Entry": e_title("Wednesday \u2014 Grinding Through"), "Date": e_date("2026-02-18"), "Mood": e_select("\uD83D\uDE10 Okay"), "Energy Level": e_select("\uD83D\uDD0B Medium"), "Gratitude": e_rich_text("Grateful for a warm meal, progress even when it's slow, and a good podcast episode"), "Wins": e_rich_text("Pushed through low energy to complete all 3 priority tasks. Journaled despite wanting to skip."), "Challenges": e_rich_text("Didn't sleep well. Low motivation during workout. Tempted to skip habits."), "Lessons Learned": e_rich_text("Showing up on hard days matters more than crushing it on easy days. Discipline > motivation."), "Tomorrow's Focus": e_rich_text("Prioritize sleep tonight. Light workout tomorrow. Focus on one big task.")},
            {"Entry": e_title("Thursday \u2014 Breakthrough Moment"), "Date": e_date("2026-02-19"), "Mood": e_select("\uD83E\uDD29 Amazing"), "Energy Level": e_select("\u26A1 High"), "Gratitude": e_rich_text("Grateful for persistence paying off, mentor call, and unexpected good news"), "Wins": e_rich_text("Got positive feedback from director on project. Side project auth flow working. Meditation felt effortless."), "Challenges": e_rich_text("Over-committed for the weekend. Need to learn to say no more."), "Lessons Learned": e_rich_text("Breakthroughs often come right after the hardest days. Trust the process."), "Tomorrow's Focus": e_rich_text("Wrap up weekly tasks. Plan weekend batch cooking. Review goals for next week.")},
            {"Entry": e_title("Friday \u2014 Weekly Wind-Down"), "Date": e_date("2026-02-20"), "Mood": e_select("\uD83D\uDE0A Good"), "Energy Level": e_select("\uD83D\uDD0B Medium"), "Gratitude": e_rich_text("Grateful for a productive week, Friday sunshine, and plans with friends tonight"), "Wins": e_rich_text("All weekly priorities complete. Side project on track. Reading streak at 28 days."), "Challenges": e_rich_text("Spent 30 min on social media during work. Need better digital boundaries."), "Lessons Learned": e_rich_text("Use website blockers during deep work. Schedule social media for specific times only."), "Tomorrow's Focus": e_rich_text("Weekly review session. Meal prep. Long run for training plan. Rest and recharge.")}
        ]
        for entry in journal_entries:
            add_entry(journal_db, entry)
            time.sleep(0.35)

    # === AREAS OF LIFE ===
    append_blocks(page_id, [
        divider(),
        heading2("\uD83E\uDDED Areas of Life"),
        paragraph("Rate each life area from 1-10 to identify where you're thriving and where you need attention. Update monthly to track your overall life balance and growth trajectory."),
    ])
    time.sleep(0.5)

    # === AREAS DATABASE ===
    areas_db = create_database(page_id, "Life Areas", {
        "Area": title_prop(),
        "Category": select_prop(["Health & Body", "Career & Work", "Finances", "Relationships", "Personal Growth", "Fun & Recreation"]),
        "Current Score": number_prop(),
        "Target Score": number_prop(),
        "Status": status_prop([]),
        "Top Priority": rich_text_prop(),
        "Key Habits": rich_text_prop(),
        "90-Day Goal": rich_text_prop(),
        "Notes": rich_text_prop()
    })

    if areas_db:
        area_entries = [
            {"Area": e_title("\uD83C\uDFCB\uFE0F Physical Health & Fitness"), "Category": e_select("Health & Body"), "Current Score": e_number(7), "Target Score": e_number(9), "Top Priority": e_rich_text("Complete half marathon training + maintain workout streak"), "Key Habits": e_rich_text("Morning workout, hydration, 7+ hrs sleep, meal prep Sundays"), "90-Day Goal": e_rich_text("Run 10K under 50 min, lose 5 lbs body fat, 100-day meditation streak"), "Notes": e_rich_text("Energy and focus have improved significantly since starting consistent exercise routine.")},
            {"Area": e_title("\uD83D\uDCBC Career & Professional Growth"), "Category": e_select("Career & Work"), "Current Score": e_number(8), "Target Score": e_number(9), "Top Priority": e_rich_text("Secure promotion + launch side project MVP"), "Key Habits": e_rich_text("3-hour deep work block daily, weekly 1:1 with manager, monthly skill learning"), "90-Day Goal": e_rich_text("Lead Q2 project, ship side project MVP, get 'exceeds expectations' review"), "Notes": e_rich_text("Strong momentum at work. Need to balance side project time without burning out.")},
            {"Area": e_title("\uD83D\uDCB0 Financial Health"), "Category": e_select("Finances"), "Current Score": e_number(6), "Target Score": e_number(8), "Top Priority": e_rich_text("Build emergency fund to $10K + start investing"), "Key Habits": e_rich_text("Track all expenses, auto-save on payday, monthly budget review, no impulse purchases over $50"), "90-Day Goal": e_rich_text("Emergency fund at $8.5K, reduce dining out by 30%, open brokerage account"), "Notes": e_rich_text("Need to address subscription creep. Cancel unused services this week.")},
            {"Area": e_title("\u2764\uFE0F Relationships & Social"), "Category": e_select("Relationships"), "Current Score": e_number(7), "Target Score": e_number(8), "Top Priority": e_rich_text("Quality time with family + deepen close friendships"), "Key Habits": e_rich_text("Weekly family call, monthly friend hangout, daily check-in with partner, no phones at dinner"), "90-Day Goal": e_rich_text("Plan family vacation, reconnect with 3 old friends, join a community group"), "Notes": e_rich_text("Been too focused on work lately. Need to be more intentional about relationships.")},
            {"Area": e_title("\uD83E\uDDE0 Personal Growth & Learning"), "Category": e_select("Personal Growth"), "Current Score": e_number(8), "Target Score": e_number(9), "Top Priority": e_rich_text("Reading habit + Spanish fluency + consistent journaling"), "Key Habits": e_rich_text("Read 30 min daily, journal nightly, practice Spanish weekdays, weekly review"), "90-Day Goal": e_rich_text("12 books read, Spanish A2 level, 100% journal completion rate"), "Notes": e_rich_text("Feeling strong momentum here. The compound effect of daily habits is becoming visible.")},
            {"Area": e_title("\uD83C\uDF89 Fun, Adventure & Creativity"), "Category": e_select("Fun & Recreation"), "Current Score": e_number(5), "Target Score": e_number(7), "Top Priority": e_rich_text("Plan Japan trip + pick up photography hobby"), "Key Habits": e_rich_text("One creative session/week, one new experience/month, plan next trip always"), "90-Day Goal": e_rich_text("Complete Japan trip, buy camera and take photography class, try 3 new restaurants"), "Notes": e_rich_text("This area needs the most attention. All work and no play isn't sustainable.")}
        ]
        for entry in area_entries:
            add_entry(areas_db, entry)
            time.sleep(0.35)

    # === REVIEW SYSTEM & RESOURCES ===
    append_blocks(page_id, [
        divider(),
        column_list([
            [
                callout_rich("\uD83C\uDFAF", [
                    text("Life Balance Snapshot\n", bold=True),
                    text("Health & Fitness:       7 / 10  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2591\u2591\u2591\nCareer & Work:          8 / 10  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2591\u2591\nFinancial Health:       6 / 10  \u2588\u2588\u2588\u2588\u2588\u2588\u2591\u2591\u2591\u2591\nRelationships:          7 / 10  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2591\u2591\u2591\nPersonal Growth:        8 / 10  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2591\u2591\nFun & Adventure:        5 / 10  \u2588\u2588\u2588\u2588\u2588\u2591\u2591\u2591\u2591\u2591\n\nOverall Average:        6.8 / 10")
                ], "purple_background")
            ],
            [
                callout_rich("\u26A0\uFE0F", [
                    text("Areas Needing Attention\n", bold=True),
                    text("\u2022 Fun & Adventure (5/10) \u2014 Schedule more joy\n\u2022 Financial Health (6/10) \u2014 Build savings faster\n\n")
                ], "orange_background"),
                callout_rich("\uD83C\uDFC6", [
                    text("Areas of Strength\n", bold=True),
                    text("\u2022 Career & Work (8/10) \u2014 Strong momentum\n\u2022 Personal Growth (8/10) \u2014 Habits compounding")
                ], "green_background")
            ]
        ]),

        divider(),

        # === PERSONAL CRM ===
        heading2("\uD83D\uDC65 Personal CRM"),
        paragraph("Never lose touch with the people who matter. Track relationships, follow-ups, and important dates for your personal and professional network.")
    ])
    time.sleep(0.5)

    # === CONTACTS DATABASE ===
    contacts_db = create_database(page_id, "Contacts & Network", {
        "Name": title_prop(),
        "Relationship": select_prop(["Family", "Close Friend", "Friend", "Colleague", "Mentor", "Professional Contact", "Acquaintance"]),
        "Company": rich_text_prop(),
        "Last Contact": date_prop(),
        "Next Follow-Up": date_prop(),
        "Birthday": date_prop(),
        "Communication": select_prop(["Text", "Call", "Email", "In-Person", "Social Media"]),
        "Notes": rich_text_prop(),
        "Topics to Discuss": rich_text_prop()
    })

    if contacts_db:
        contact_entries = [
            {"Name": e_title("Mom & Dad"), "Relationship": e_select("Family"), "Last Contact": e_date("2026-02-20"), "Next Follow-Up": e_date("2026-02-27"), "Communication": e_select("Call"), "Notes": e_rich_text("Weekly Sunday call tradition. Ask about dad's golf tournament and mom's book club."), "Topics to Discuss": e_rich_text("Japan trip plans, career update")},
            {"Name": e_title("Jake (Best Friend)"), "Relationship": e_select("Close Friend"), "Last Contact": e_date("2026-02-18"), "Next Follow-Up": e_date("2026-03-01"), "Communication": e_select("In-Person"), "Birthday": e_date("2026-07-15"), "Notes": e_rich_text("Grab dinner monthly. He's starting a new job next month."), "Topics to Discuss": e_rich_text("His new job, weekend hiking plan")},
            {"Name": e_title("Sarah Kim (Manager)"), "Relationship": e_select("Colleague"), "Company": e_rich_text("Current Company"), "Last Contact": e_date("2026-02-19"), "Next Follow-Up": e_date("2026-03-05"), "Communication": e_select("In-Person"), "Notes": e_rich_text("Great relationship. She's supportive of my promotion goals. Schedule monthly 1:1 outside of regular meetings."), "Topics to Discuss": e_rich_text("Q1 review prep, project proposal")},
            {"Name": e_title("Dr. Patel (Mentor)"), "Relationship": e_select("Mentor"), "Company": e_rich_text("University / Advisory"), "Last Contact": e_date("2026-02-01"), "Next Follow-Up": e_date("2026-03-01"), "Communication": e_select("Email"), "Notes": e_rich_text("Monthly check-in. Incredible career advice. Introduced me to two valuable contacts last year."), "Topics to Discuss": e_rich_text("Side project progress, career crossroads decision")}
        ]
        for entry in contact_entries:
            add_entry(contacts_db, entry)
            time.sleep(0.35)

    # === HEALTH & FITNESS SECTION ===
    append_blocks(page_id, [
        divider(),
        heading2("\uD83C\uDFCB\uFE0F Health & Fitness"),
        paragraph("Track your workouts, meals, sleep, and overall wellness. Your body is the vehicle for everything else in life \u2014 treat it accordingly.")
    ])
    time.sleep(0.5)

    # === WORKOUT LOG DATABASE ===
    workout_db = create_database(page_id, "Workout Log", {
        "Workout": title_prop(),
        "Date": date_prop(),
        "Type": select_prop(["Strength \u2014 Push", "Strength \u2014 Pull", "Strength \u2014 Legs", "Cardio \u2014 Run", "Cardio \u2014 Cycling", "HIIT", "Yoga/Stretch", "Sport", "Rest Day"]),
        "Duration": rich_text_prop(),
        "Intensity": select_prop(["\uD83D\uDD25 High", "\uD83D\uDFE1 Medium", "\uD83D\uDFE2 Easy"]),
        "Calories": number_prop(),
        "Exercises": rich_text_prop(),
        "Notes": rich_text_prop()
    })

    if workout_db:
        workout_entries = [
            {"Workout": e_title("Push Day \u2014 Chest, Shoulders, Triceps"), "Date": e_date("2026-02-19"), "Type": e_select("Strength \u2014 Push"), "Duration": e_rich_text("50 min"), "Intensity": e_select("\uD83D\uDD25 High"), "Calories": e_number(420), "Exercises": e_rich_text("Bench Press 4x8, OHP 3x10, Incline DB Press 3x12, Lateral Raises 3x15, Tricep Pushdown 3x12, Dips 3x10"), "Notes": e_rich_text("New PR on bench: 185 lbs x 8! Shoulders felt great. Increase OHP weight next session.")},
            {"Workout": e_title("5K Easy Run"), "Date": e_date("2026-02-20"), "Type": e_select("Cardio \u2014 Run"), "Duration": e_rich_text("28 min"), "Intensity": e_select("\uD83D\uDFE2 Easy"), "Calories": e_number(310), "Exercises": e_rich_text("5K at conversational pace, 5 min warmup walk, 5 min cooldown"), "Notes": e_rich_text("Pace: 9:05/mile. Felt comfortable. Heart rate stayed in Zone 2. Training for half marathon.")},
            {"Workout": e_title("Pull Day \u2014 Back & Biceps"), "Date": e_date("2026-02-21"), "Type": e_select("Strength \u2014 Pull"), "Duration": e_rich_text("45 min"), "Intensity": e_select("\uD83D\uDD25 High"), "Calories": e_number(380), "Exercises": e_rich_text("Deadlift 4x5, Pull-ups 4x8, Barbell Row 3x10, Face Pulls 3x15, Hammer Curls 3x12, Barbell Curl 3x10"), "Notes": e_rich_text("Deadlift form feeling solid at 225 lbs. Grip gave out on last set of pull-ups \u2014 add grip work.")}
        ]
        for entry in workout_entries:
            add_entry(workout_db, entry)
            time.sleep(0.35)

    # Meal Planning and Wellness
    append_blocks(page_id, [
        divider(),
        column_list([
            [
                callout_rich("\uD83C\uDF57", [
                    text("Meal Planning\n", bold=True),
                    text("Monday: Chicken stir-fry + rice\nTuesday: Salmon + roasted veggies\nWednesday: Turkey tacos\nThursday: Pasta primavera\nFriday: Grilled chicken salad\n\nMeal Prep Sunday: Cook protein,\nchop veggies, portion containers\n\nDaily Targets:\nProtein: 150g | Calories: 2,200")
                ], "green_background")
            ],
            [
                callout_rich("\uD83D\uDE34", [
                    text("Sleep & Wellness\n", bold=True),
                    text("Sleep Target: 7-8 hours\nBedtime: 10:00 PM\nWake Time: 6:00 AM\n\nThis Week's Avg: 7.2 hrs \u2705\nQuality Rating: 7/10\n\nWater: 8 glasses/day\nSteps: 8,000/day target\nScreen Cutoff: 9:00 PM")
                ], "blue_background")
            ]
        ]),

        divider(),

        # === REVIEW SYSTEM ===
        heading2("\uD83D\uDD0D Review System"),
        paragraph("Consistent reviews are the secret weapon of high performers. Use these templates to reflect, adjust, and plan at every time scale. Never let autopilot run your life.", italic=True, color="gray"),

        toggle("Daily Review (5 min \u2014 Every Evening)", [
            paragraph("Complete these each evening before bed:", bold=True),
            todo_block("Did I complete my top 3 priorities today?"),
            todo_block("Did I complete all daily habits?"),
            todo_block("What went well today? (Write in journal)"),
            todo_block("What could I improve tomorrow?"),
            todo_block("Set tomorrow's top 3 priorities"),
            todo_block("Process Quick Capture Inbox items"),
            divider(),
            paragraph("Reflection prompts:", italic=True),
            bullet("What am I most proud of today?"),
            bullet("What drained my energy and how can I avoid it?"),
            bullet("Did I live in alignment with my values today?")
        ]),

        toggle("Weekly Review (30 min \u2014 Every Sunday)", [
            paragraph("Part 1: Reflect on the Week", bold=True),
            todo_block("Review all journal entries from the week"),
            todo_block("Calculate habit completion rate (target: 85%+)"),
            todo_block("Review completed vs planned tasks"),
            todo_block("Celebrate wins \u2014 write down at least 3"),
            todo_block("Identify top lesson learned this week"),
            divider(),
            paragraph("Part 2: Plan Next Week", bold=True),
            todo_block("Review upcoming calendar & deadlines"),
            todo_block("Set 3-5 weekly priorities"),
            todo_block("Identify potential blockers and plan around them"),
            todo_block("Schedule deep work blocks"),
            todo_block("Plan meals and exercise for the week"),
            divider(),
            paragraph("Part 3: Systems Check", bold=True),
            todo_block("Clean up inbox and Quick Capture"),
            todo_block("Update project statuses and next actions"),
            todo_block("Check goal progress \u2014 still on track?"),
            todo_block("Archive completed items")
        ]),

        toggle("Monthly Review (1 hour \u2014 Last Sunday of Month)", [
            paragraph("Monthly Assessment:", bold=True),
            todo_block("Score each Area of Life (1-10)"),
            todo_block("Review goal progress \u2014 update percentages"),
            todo_block("Analyze habit streaks and identify drops"),
            todo_block("Review financial summary (income, expenses, savings)"),
            todo_block("Identify top 3 wins of the month"),
            todo_block("Identify top 3 areas for improvement"),
            divider(),
            paragraph("Planning:", bold=True),
            todo_block("Set 3-5 key priorities for next month"),
            todo_block("Adjust any goals that need recalibrating"),
            todo_block("Start or stop any habits based on data"),
            todo_block("Plan any major events, trips, or milestones"),
            todo_block("Update Vision Board if needed")
        ]),

        toggle("Quarterly Review (2 hours \u2014 Every 3 Months)", [
            paragraph("The Big Picture Review:", bold=True),
            todo_block("Am I making meaningful progress toward my annual goals?"),
            todo_block("Review all goal Key Results \u2014 which are on/off track?"),
            todo_block("Analyze trends across 3 months of journal data"),
            todo_block("Life Area scores \u2014 compare to 3 months ago"),
            todo_block("What projects should I start, stop, or continue?"),
            divider(),
            paragraph("Strategic Adjustments:", bold=True),
            todo_block("Retire goals that no longer serve me"),
            todo_block("Set new goals if current ones are achieved"),
            todo_block("Evaluate whether I'm spending time on what matters most"),
            todo_block("Adjust daily/weekly routines based on what's working"),
            todo_block("Plan next quarter's top 3-5 focus areas"),
            divider(),
            callout_rich("\uD83D\uDCA1", [
                text("Quarterly Question: ", bold=True),
                text("If I continued exactly as I am now for 10 years, would I be happy with where I end up? If not, what needs to change today?")
            ], "yellow_background")
        ]),

        toggle("Annual Review (Half Day \u2014 Every December/January)", [
            paragraph("Year in Review:", bold=True),
            todo_block("List all major accomplishments and milestones"),
            todo_block("Review every goal \u2014 achieved, progressed, or abandoned?"),
            todo_block("Calculate key metrics: books read, habits maintained, savings rate"),
            todo_block("Write a letter to your past self about what you've learned"),
            todo_block("Identify the 3 decisions that had the biggest impact"),
            divider(),
            paragraph("Year Ahead Planning:", bold=True),
            todo_block("Define your theme/word for the new year"),
            todo_block("Set 5-8 annual goals using SMART framework"),
            todo_block("Break each goal into quarterly milestones"),
            todo_block("Design your ideal daily routine for the year"),
            todo_block("Create your Vision Board for the year"),
            todo_block("Plan key trips, events, and milestones"),
            divider(),
            callout_rich("\uD83C\uDF1F", [
                text("Annual Reflection: ", bold=True),
                text("The person who reviews their year honestly and plans intentionally will always outperform the person who lets life happen by default. You are the architect of your life.")
            ], "purple_background")
        ]),

        divider(),

        # === RESOURCES ===
        heading2("\uD83D\uDCDA Resources & Reference"),

        toggle("Recommended Books & Reading List", [
            paragraph("Productivity & Habits:", bold=True),
            bullet("Atomic Habits \u2014 James Clear"),
            bullet("Deep Work \u2014 Cal Newport"),
            bullet("The 7 Habits of Highly Effective People \u2014 Stephen Covey"),
            bullet("Getting Things Done \u2014 David Allen"),
            divider(),
            paragraph("Mindset & Personal Growth:", bold=True),
            bullet("Mindset \u2014 Carol Dweck"),
            bullet("Can't Hurt Me \u2014 David Goggins"),
            bullet("The Obstacle Is the Way \u2014 Ryan Holiday"),
            bullet("Man's Search for Meaning \u2014 Viktor Frankl"),
            divider(),
            paragraph("Finance & Wealth:", bold=True),
            bullet("The Psychology of Money \u2014 Morgan Housel"),
            bullet("I Will Teach You to Be Rich \u2014 Ramit Sethi"),
            bullet("The Simple Path to Wealth \u2014 JL Collins"),
            divider(),
            paragraph("Health & Wellness:", bold=True),
            bullet("Why We Sleep \u2014 Matthew Walker"),
            bullet("Outlive \u2014 Peter Attia"),
            bullet("The Body Keeps the Score \u2014 Bessel van der Kolk")
        ]),

        toggle("Useful Tools & Apps", [
            bullet("Notion \u2014 All-in-one workspace (you're here!)"),
            bullet("Todoist / Things 3 \u2014 Task management"),
            bullet("Headspace / Calm \u2014 Meditation"),
            bullet("Strava / Nike Run Club \u2014 Fitness tracking"),
            bullet("YNAB / Copilot \u2014 Budgeting"),
            bullet("Kindle / Audible \u2014 Reading"),
            bullet("Duolingo / Pimsleur \u2014 Language learning"),
            bullet("Obsidian / Readwise \u2014 Note-taking & highlights"),
            bullet("Google Calendar \u2014 Time blocking"),
            bullet("Forest \u2014 Focus timer")
        ]),

        toggle("Mental Models & Frameworks", [
            bullet_rich([text("80/20 Rule (Pareto): ", bold=True), text("20% of inputs produce 80% of results. Find your highest-leverage activities.")]),
            bullet_rich([text("Eisenhower Matrix: ", bold=True), text("Urgent/Important grid for prioritization. Spend most time in Important + Not Urgent.")]),
            bullet_rich([text("First Principles: ", bold=True), text("Break problems down to fundamentals. Don't accept assumptions blindly.")]),
            bullet_rich([text("Compound Effect: ", bold=True), text("Small daily improvements lead to massive long-term results. 1% better daily = 37x better yearly.")]),
            bullet_rich([text("Inversion: ", bold=True), text("Instead of asking 'how do I succeed?', ask 'how would I fail?' Then avoid those things.")]),
            bullet_rich([text("Circle of Competence: ", bold=True), text("Know what you know, know what you don't, and stay focused on your strengths.")]),
            bullet_rich([text("Second-Order Thinking: ", bold=True), text("Don't just consider immediate effects. Ask 'and then what?' for every decision.")])
        ]),

        divider(),

        # === CLOSING ===
        callout_rich("\uD83C\uDF1F", [
            text("Your Life OS Philosophy\n\n", bold=True),
            text("This system works when you work it. Show up daily, review weekly, and adjust quarterly. The goal isn't perfection \u2014 it's consistent, intentional progress. You are the CEO of your own life. Every day is an opportunity to design the future you want.\n\nRemember: Systems beat goals. Consistency beats intensity. Progress beats perfection.\n\nNow go build something extraordinary. \u2728")
        ], "purple_background")
    ])

    print("  Template 9 COMPLETE!")
    return page_id


# ========================================================
# MAIN EXECUTION
# ========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("BUILDING 9 NOTION TEMPLATES")
    print("=" * 60)

    results = {}

    # Template 1 (page already exists, just need DB + extra blocks)
    results["Habit Tracker Pro"] = build_template_1()
    time.sleep(1)

    results["Debt Snowball Calculator"] = build_template_2()
    time.sleep(1)

    results["Student Command Center"] = build_template_3()
    time.sleep(1)

    results["Content Creator Hub"] = build_template_4()
    time.sleep(1)

    results["Job Hunt Dashboard"] = build_template_5()
    time.sleep(1)

    results["Budget & Expense Tracker"] = build_template_6()
    time.sleep(1)

    results["Travel Planner"] = build_template_7()
    time.sleep(1)

    results["Second Brain / Knowledge Vault"] = build_template_8()
    time.sleep(1)

    results["Life OS - Master Dashboard"] = build_template_9()

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for name, pid in results.items():
        status = "SUCCESS" if pid else "FAILED"
        print(f"  {status}: {name} -> {pid}")

    success_count = sum(1 for v in results.values() if v)
    print(f"\n  {success_count}/9 templates built successfully!")
    print("=" * 60)
