"""
Graphics Enhancement Script for EvolvNth Notion Templates
----------------------------------------------------------
Adds cover images, hero banner images, and branded footer callouts
to all 9 template pages for a professional, polished look.
"""
import json
import urllib.request
import urllib.error
import time
import os

API_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
BASE_URL = "https://api.notion.com/v1"
PARENT_PAGE = "30e107f0-44d1-8014-abd0-c449748c499e"
NOTION_VERSION = "2022-06-28"


# ============================================================
# IMAGE LIBRARY — Curated Unsplash photos for each template
# ============================================================
TEMPLATE_IMAGES = {
    "Habit Tracker Pro": {
        "cover": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=1500&h=600&fit=crop&crop=center",
        "banner": "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=1200&h=400&fit=crop&crop=center",
        "icon": "\uD83C\uDFAF",
        "tagline": "Build lasting habits, one day at a time.",
    },
    "Debt Snowball Calculator": {
        "cover": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1500&h=600&fit=crop&crop=center",
        "banner": "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=1200&h=400&fit=crop&crop=center",
        "icon": "\uD83D\uDCB0",
        "tagline": "Crush your debt with momentum and strategy.",
    },
    "Student Command Center": {
        "cover": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1500&h=600&fit=crop&crop=center",
        "banner": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=1200&h=400&fit=crop&crop=center",
        "icon": "\uD83C\uDF93",
        "tagline": "Your academic life, organized and optimized.",
    },
    "Content Creator Hub": {
        "cover": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=1500&h=600&fit=crop&crop=center",
        "banner": "https://images.unsplash.com/photo-1533750516457-a7f992034fec?w=1200&h=400&fit=crop&crop=center",
        "icon": "\uD83C\uDFAC",
        "tagline": "Plan, create, and grow your content empire.",
    },
    "Job Hunt Dashboard": {
        "cover": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1500&h=600&fit=crop&crop=center",
        "banner": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=1200&h=400&fit=crop&crop=center",
        "icon": "\uD83D\uDCBC",
        "tagline": "Land your dream role with a strategic approach.",
    },
    "Budget & Expense Tracker": {
        "cover": "https://images.unsplash.com/photo-1554224154-22dec7ec8818?w=1500&h=600&fit=crop&crop=center",
        "banner": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=1200&h=400&fit=crop&crop=center",
        "icon": "\uD83D\uDCCA",
        "tagline": "Take control of every dollar you earn and spend.",
    },
    "Travel Planner": {
        "cover": "https://images.unsplash.com/photo-1488085061387-422e29b40080?w=1500&h=600&fit=crop&crop=center",
        "banner": "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1200&h=400&fit=crop&crop=center",
        "icon": "\u2708\uFE0F",
        "tagline": "Dream it. Plan it. Explore it.",
    },
    "Second Brain / Knowledge Vault": {
        "cover": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=1500&h=600&fit=crop&crop=center",
        "banner": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=1200&h=400&fit=crop&crop=center",
        "icon": "\uD83E\uDDE0",
        "tagline": "Capture, connect, and recall everything that matters.",
    },
    "Life OS": {
        "cover": "https://images.unsplash.com/photo-1483058712412-4245e9b90334?w=1500&h=600&fit=crop&crop=center",
        "banner": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=400&fit=crop&crop=center",
        "icon": "\uD83C\uDFE0",
        "tagline": "Your entire life, beautifully orchestrated.",
    },
}


# ============================================================
# API HELPERS
# ============================================================
def api_call(endpoint, data=None, method="GET"):
    url = f"{BASE_URL}/{endpoint}"
    body = json.dumps(data).encode("utf-8") if data else None
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


def image_block(url):
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": url}
        }
    }


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def paragraph(content, **annotations):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [text(content, **annotations)]}}


def callout_rich(emoji, rich_texts, color="default"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": emoji},
            "color": color,
            "rich_text": rich_texts
        }
    }


# ============================================================
# STEP 1: DISCOVER ALL TEMPLATE PAGES
# ============================================================
def discover_template_pages():
    """Fetch all child pages of the parent page to get template IDs."""
    print("\n--- Step 1: Discovering template pages ---")
    result = api_call(f"blocks/{PARENT_PAGE}/children?page_size=100")
    if not result:
        print("  FAILED to fetch parent page children!")
        return {}

    pages = {}
    for block in result.get("results", []):
        if block["type"] == "child_page":
            page_id = block["id"]
            title = block["child_page"]["title"]
            pages[title] = page_id
            print(f"  Found: {title} -> {page_id}")

    print(f"  Total: {len(pages)} template pages found")
    return pages


# ============================================================
# STEP 2: SET COVER IMAGES
# ============================================================
def set_cover_image(page_id, cover_url, title):
    """Set the cover image for a page."""
    data = {
        "cover": {
            "type": "external",
            "external": {"url": cover_url}
        }
    }
    result = api_call(f"pages/{page_id}", data, method="PATCH")
    if result:
        print(f"  Cover set: {title}")
        return True
    else:
        print(f"  FAILED to set cover: {title}")
        return False


# ============================================================
# STEP 3: INSERT HERO BANNER + BRANDED FOOTER
# ============================================================
def get_first_blocks(page_id, limit=5):
    """Get the first few blocks of a page to find insertion point."""
    result = api_call(f"blocks/{page_id}/children?page_size={limit}")
    if result:
        return result.get("results", [])
    return []


def prepend_banner_after_first_block(page_id, banner_url, first_block_id):
    """Insert a banner image after the first block (heading)."""
    data = {
        "children": [image_block(banner_url)],
        "after": first_block_id
    }
    result = api_call(f"blocks/{page_id}/children", data, method="PATCH")
    if result:
        print(f"  Banner inserted after heading")
        return True
    else:
        print(f"  FAILED to insert banner")
        return False


def append_branded_footer(page_id, template_name, tagline):
    """Append a branded EvolvNth footer callout to the page."""
    footer_blocks = [
        divider(),
        callout_rich("\u2728", [
            text("Made with ", color="gray"),
            text("EvolvNth", bold=True, color="blue"),
            text(" \u2014 ", color="gray"),
            text(tagline, italic=True, color="gray"),
        ], "gray_background"),
    ]

    data = {"children": footer_blocks}
    result = api_call(f"blocks/{page_id}/children", data, method="PATCH")
    if result:
        print(f"  Branded footer appended")
        return True
    else:
        print(f"  FAILED to append footer")
        return False


# ============================================================
# STEP 4: MATCH PAGES TO TEMPLATE CONFIG
# ============================================================
def match_template(page_title):
    """Match a Notion page title to our template config (fuzzy)."""
    title_lower = page_title.lower()
    for template_name, config in TEMPLATE_IMAGES.items():
        # Check if the template name keywords appear in the page title
        name_lower = template_name.lower()
        # Try exact match first
        if name_lower == title_lower:
            return template_name, config
        # Try keyword matching
        keywords = name_lower.split()
        # Match if first major keyword is in the title
        if keywords[0] in title_lower:
            return template_name, config
    # Special cases
    if "life os" in title_lower or "command center" in title_lower and "personal" in title_lower:
        return "Life OS", TEMPLATE_IMAGES["Life OS"]
    return None, None


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("EVOLVNTH GRAPHICS ENHANCEMENT")
    print("Adding covers, banners, and branding to all 9 templates")
    print("=" * 60)

    # Step 1: Discover pages
    pages = discover_template_pages()
    if not pages:
        print("\nABORT: No template pages found!")
        exit(1)

    # Step 2 & 3: Process each template
    cover_ok = 0
    banner_ok = 0
    footer_ok = 0
    matched = 0
    skipped = []

    for page_title, page_id in pages.items():
        template_name, config = match_template(page_title)
        if not config:
            print(f"\n--- SKIPPING: {page_title} (no matching template config) ---")
            skipped.append(page_title)
            continue

        matched += 1
        print(f"\n--- Enhancing: {page_title} ---")
        print(f"  Matched to: {template_name}")

        # 2a: Set cover image
        if set_cover_image(page_id, config["cover"], page_title):
            cover_ok += 1
        time.sleep(0.4)

        # 2b: Insert banner image after first block
        blocks = get_first_blocks(page_id, limit=3)
        time.sleep(0.4)

        if blocks:
            # Find the first heading_1 or use the very first block
            target_block_id = None
            for b in blocks:
                if b["type"] in ("heading_1", "heading_2"):
                    target_block_id = b["id"]
                    break
            if not target_block_id:
                target_block_id = blocks[0]["id"]

            if prepend_banner_after_first_block(page_id, config["banner"], target_block_id):
                banner_ok += 1
        else:
            print(f"  WARN: No blocks found, skipping banner")

        time.sleep(0.4)

        # 2c: Append branded footer
        if append_branded_footer(page_id, template_name, config["tagline"]):
            footer_ok += 1

        time.sleep(0.5)

    # Summary
    print("\n" + "=" * 60)
    print("GRAPHICS ENHANCEMENT COMPLETE")
    print("=" * 60)
    print(f"  Templates matched:  {matched} / {len(pages)}")
    print(f"  Covers set:         {cover_ok} / {matched}")
    print(f"  Banners inserted:   {banner_ok} / {matched}")
    print(f"  Footers appended:   {footer_ok} / {matched}")
    if skipped:
        print(f"  Skipped pages:      {', '.join(skipped)}")
    print("=" * 60)
