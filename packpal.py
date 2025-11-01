
"""
PackPal SIMPLE (single-file, beginner-friendly)
-----------------------------------------------
- Single .py file, Python standard library only
- Input: emoji/text activities + climate + days
- Output: terminal text, auto-saved to packpal_output.txt

Examples:
  python packpal.py "🏖️ 📸 3d"
  python packpal.py "hiking ❄️ 4d"
  python packpal.py            # interactive prompt
"""

import sys, re, datetime

# 1) Map emojis to keywords. You can also type plain words:
#    activities: beach/hiking/city/business/photo/camping/flight/train/roadtrip/swim/fishing/amusement_park
#    climates: warm/cold/rain/cloudy/storm
EMOJI_TO_WORD = {
    # activities
    "🏖️": "beach", "🏝️": "beach",
    "🥾": "hiking", "⛰️": "hiking", "🧗": "hiking",
    "🏙️": "city", "🌆": "city",
    "💼": "business", "📊": "business",
    "📸": "photo",
    "⛺": "camping",
    "✈️": "flight", "🛫": "flight", "🛬": "flight",
    "🏊": "swim", "🏊‍♀️": "swim", "🏊‍♂️": "swim",
    "🚄": "train", "🚅": "train", "🚝": "train",
    "🚗": "roadtrip", "🚘": "roadtrip",
    "🎣": "fishing",
    "🎡": "amusement_park", "🎢": "amusement_park",
    # climates (include plain + variation selector forms)
    "☀️": "warm", "🌞": "warm",
    "❄️": "cold", "🥶": "cold",
    "🌧️": "rain", "☔": "rain",
    "⛅️": "cloudy", "⛅": "cloudy",
    "🌩️": "storm", "🌩": "storm"
}

# 2) Base items + add-ons for activities and climates.
#    Rule markers:
#      "(per_day)"     -> quantity = days
#      "(per_2_days)"  -> quantity = ceil(days/2)
#      "(fixed)"       -> always 1
#      "(optional)"    -> label only; quantity unaffected
BASE_ITEMS = {
    "Clothing": ["T-shirt (per_2_days)", "Underwear (per_day)", "Socks (per_day)", "Sleepwear (fixed)"],
    "Toiletries": ["Toothbrush (fixed)", "Toothpaste (fixed)", "Face wash (fixed)"],
    "Electronics": ["Phone + charger (fixed)"],
    "Documents": ["ID / Passport (fixed)"],
    "Misc": ["Water bottle (fixed)"]
}

ACTIVITY_ITEMS = {
    "beach": {
        "Clothing": ["Swimwear (fixed)"],
        "Misc": ["Sunscreen (fixed)", "Sunglasses (fixed)", "Beach towel (fixed)"]
    },
    "hiking": {
        "Clothing": ["Quick-dry T-shirt (per_2_days)", "Hiking socks (per_day)", "Cap/hat (fixed)"],
        "Footwear": ["Hiking shoes (fixed)"],
        "Misc": ["Small first-aid kit (fixed)", "Snacks (fixed)"]
    },
    "city": {
        "Footwear": ["Comfort sneakers (fixed)"],
        "Misc": ["Tote/backpack (fixed)"]
    },
    "business": {
        "Clothing": ["Shirt (per_2_days)"],
        "Documents": ["Laptop (fixed)"]
    },
    "photo": {
        "Electronics": ["Camera (fixed)", "Spare battery (fixed)", "SD card x2 (fixed)"]
    },
    "camping": {
        "Misc": ["Tent (fixed)", "Sleeping bag (fixed)"]
    },
    "flight": {
        "Documents": ["Boarding pass (fixed)"],
        "Misc": ["Neck pillow (optional)"]
    },
    "train": {
        "Documents": ["Rail ticket/QR (fixed)"],
        "Misc": ["Neck pillow (optional)", "Snacks (optional)"]
    },
    "roadtrip": {
        "Documents": ["Driver's license (fixed)"],
        "Electronics": ["Car charger (fixed)"],
        "Misc": ["Phone mount (optional)", "Emergency kit (fixed)"]
    },
    "swim": {
        "Clothing": ["Swimwear (fixed)"]
    },
    "fishing": {
        "Misc": ["Fishing rod (fixed)", "Line & hooks (fixed)", "Bait (fixed)", "Tackle box (fixed)", "Fishing license if required (fixed)"]
    },
    "amusement_park": {
        "Misc": ["Small crossbody bag (fixed)", "Poncho for water rides (optional)"],
        "Electronics": ["Power bank (optional)"]
    }
}

CLIMATE_ITEMS = {
    "warm": {
        "Clothing": ["Shorts (per_2_days)"]
    },
    "cold": {
        "Clothing": ["Warm coat (fixed)", "Thermal top (per_2_days)"],
        "Misc": ["Lip balm (fixed)"]
    },
    "rain": {
        "Clothing": ["Rain jacket (fixed)"],
        "Misc": ["Umbrella (fixed)"]
    },
    "cloudy": {
        "Clothing": ["Light jacket (optional)"]
    },
    "storm": {
        "Clothing": ["Rain jacket (fixed)"],
        "Misc": ["Waterproof phone pouch (optional)", "Umbrella (fixed)"]
    }
}

ALWAYS_INCLUDE = ["Medications (fixed)", "Cash (fixed)"]

def parse_user_input(raw: str):
    """
    Turn a string into: set(activities), days (int), set(climates).
    Supported days: "3", "3d", "⏱️3", "⏰5".
    """
    raw = raw.strip()
    if not raw:
        return set(), 3, set()

    tokens = re.split(r"[,\s]+", raw)
    activities, climates = set(), set()
    days = None

    for t in tokens:
        if not t:
            continue
        # detect days like 3 or 3d
        if re.fullmatch(r"\d+[dD]?", t):
            days = int(re.search(r"\d+", t).group())
            continue
        # detect "⏱️3" / "⏰5"
        if ("⏱" in t or "⏰" in t) and re.search(r"\d+", t):
            days = int(re.search(r"\d+", t).group()); continue

        # emoji → keyword
        mapped = EMOJI_TO_WORD.get(t)
        if mapped:
            if mapped in CLIMATE_ITEMS:
                climates.add(mapped)
            else:
                activities.add(mapped)
            continue

        # plain words allowed
        low = t.lower()
        if low in CLIMATE_ITEMS:
            climates.add(low)
        else:
            activities.add(low)

    if days is None:
        days = 3
    days = max(1, min(days, 60))
    return activities, days, climates

def merge_items(activities, climates):
    """
    Merge base + activities + climates into {category: [items...]}
    """
    merged = {}
    # base
    for cat, items in BASE_ITEMS.items():
        merged.setdefault(cat, [])
        merged[cat].extend(items)
    # activities
    for act in activities:
        if act in ACTIVITY_ITEMS:
            for cat, items in ACTIVITY_ITEMS[act].items():
                merged.setdefault(cat, [])
                merged[cat].extend(items)
    # climates
    for c in climates:
        if c in CLIMATE_ITEMS:
            for cat, items in CLIMATE_ITEMS[c].items():
                merged.setdefault(cat, [])
                merged[cat].extend(items)
    # always include
    merged.setdefault("Misc", [])
    merged["Misc"].extend(ALWAYS_INCLUDE)
    # de-duplicate per category, keep order
    for cat in list(merged.keys()):
        new_items, seen = [], set()
        for x in merged[cat]:
            if x not in seen:
                new_items.append(x); seen.add(x)
        merged[cat] = new_items
    return merged

def scale_by_days(items_by_cat, days):
    """
    Apply quantity rules: per_day / per_2_days / fixed / optional
    """
    out = {}
    for cat, items in items_by_cat.items():
        formatted = []
        for it in items:
            m = re.search(r"\((per_day|per_\d+_days|fixed|optional)\)", it)
            mode = m.group(1) if m else "fixed"
            name = re.sub(r"\s*\((per_day|per_\d+_days|fixed|optional)\)\s*$", "", it)

            if mode == "per_day":
                qty = days
            elif mode.startswith("per_") and mode.endswith("_days"):
                n = int(re.search(r"per_(\d+)_days", mode).group(1))
                qty = (days + n - 1) // n
            else:
                qty = 1

            suffix = "" if mode != "optional" else " (optional)"
            if mode == "per_day" or mode.startswith("per_"):
                formatted.append(f"{name} x{qty}{suffix}")
            else:
                formatted.append(f"{name}{suffix}")
        out[cat] = formatted
    return out

def render_text(activities, climates, days, packed):
    """
    Make a readable multi-line packing list.
    """
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    act = ", ".join(sorted(activities)) if activities else "general"
    clim = ", ".join(sorted(climates)) if climates else "unspecified"
    lines = [
        "PackPal SIMPLE — Packing List",
        f"Generated: {dt}",
        f"Trip length: {days} day(s)",
        f"Activities: {act}",
        f"Climate: {clim}",
        "-"*40
    ]
    for cat in sorted(packed.keys()):
        lines.append("")
        lines.append(f"[{cat}]")
        for item in packed[cat]:
            lines.append(f"• {item}")
    return "\n".join(lines)

def save_to_file(text, filename="packpal_output.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        return filename
    except Exception:
        return None

def main():
    # Read CLI args; if none, fall back to interactive input.
    raw = " ".join(sys.argv[1:]).strip()
    if not raw:
        print("Enter your trip (emoji/words). Example:  '🏖️ 📸 3d'   or   'hiking ❄️ 4d'")
        raw = input("> ").strip()

    activities, days, climates = parse_user_input(raw)
    items = merge_items(activities, climates)
    packed = scale_by_days(items, days)
    text = render_text(activities, climates, days, packed)

    print("\n" + text + "\n")
    saved = save_to_file(text)
    if saved:
        print(f"Saved to: {saved}")

if __name__ == "__main__":
    main()
