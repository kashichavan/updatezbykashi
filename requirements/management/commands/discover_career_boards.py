"""
Find employers' official public career boards (Greenhouse, Lever, Ashby,
SmartRecruiters) and add the ones with real India postings to
requirements/job_aggregator/career_boards.json.

    python manage.py discover_career_boards                  # probe the built-in list, print results
    python manage.py discover_career_boards --save           # ...and add qualifying boards
    python manage.py discover_career_boards Zepto Ola "Urban Company" --save

A board qualifies only if it exists, has at least --min-india India postings,
and its postings carry a real job description.
"""
import json
import re

from django.core.management.base import BaseCommand

from requirements.job_aggregator.adapters.indian_startup_adapter import (
    BOARDS_FILE,
    IndianStartupSourceAdapter,
    load_boards,
)

SEED_COMPANIES = [
    "Zepto", "Swiggy", "Zomato", "Blinkit", "Flipkart", "Myntra", "PhonePe", "Paytm", "Razorpay",
    "CRED", "Groww", "Zerodha", "Upstox", "Meesho", "Nykaa", "Lenskart", "Ola", "Rapido",
    "Urban Company", "Dunzo", "BigBasket", "Licious", "ShareChat", "Dream11", "MPL", "Games24x7",
    "Postman", "BrowserStack", "Freshworks", "Zoho", "Chargebee", "Druva", "InMobi", "Glance",
    "Unacademy", "upGrad", "PhysicsWallah", "Scaler", "InterviewBit", "Simplilearn", "Vedantu",
    "Atlan", "SpotDraft", "Sarvam", "Krutrim", "Uniphore", "Hasura", "Setu", "Jupiter", "Fi",
    "Slice", "Jar", "Navi", "Acko", "Digit", "PolicyBazaar", "CARS24", "Spinny", "OYO",
    "MakeMyTrip", "ixigo", "Cleartrip", "Delhivery", "Shiprocket", "Rivigo", "BlackBuck",
    "Mindtickle", "Whatfix", "LeadSquared", "Darwinbox", "Keka", "Zeta", "M2P", "Juspay",
    "Cashfree", "Pine Labs", "BharatPe", "MobiKwik", "HighRadius", "Zenoti", "Innovaccer",
    "Practo", "PharmEasy", "Cult.fit", "HealthifyMe", "Pocket FM", "Kuku FM", "FamPay",
    "NoBroker", "Housing", "Apna", "Pratilipi", "Dailyhunt", "Eruditus", "Leap",
]

ATS_ORDER = ("greenhouse", "lever", "ashby", "smartrecruiters")


def slug_variants(name: str, ats: str):
    base = re.sub(r"[^A-Za-z0-9 ]", "", name).strip()
    tight = base.replace(" ", "")
    variants = {tight.lower(), base.lower().replace(" ", "-"), base.lower().replace(" ", "")}
    if ats == "smartrecruiters":
        variants |= {tight, tight.upper(), base.title().replace(" ", "")}
    return [v for v in variants if v]


class Command(BaseCommand):
    help = "Discover employers' official public career boards with India postings."

    def add_arguments(self, parser):
        parser.add_argument("companies", nargs="*", help="Company names (defaults to a built-in Indian list)")
        parser.add_argument("--save", action="store_true", help="Add qualifying boards to career_boards.json")
        parser.add_argument("--min-india", type=int, default=2)

    def handle(self, *args, **opts):
        adapter = IndianStartupSourceAdapter()
        adapter.max_jobs_per_board = 3  # enough to prove JDs exist without many detail calls
        adapter.rate_limit_delay = 0.3
        existing = {(b["ats"], b["slug"].lower()) for b in load_boards()}
        found = []

        for name in opts["companies"] or SEED_COMPANIES:
            hit = None
            for ats in ATS_ORDER:
                for slug in slug_variants(name, ats):
                    if (ats, slug.lower()) in existing:
                        hit = ("known", ats, slug, None)
                        break
                    board = {"ats": ats, "slug": slug, "company": name}
                    try:
                        jobs = adapter.fetch_board(board)
                    except Exception:
                        jobs = []
                    if len(jobs) >= min(opts["min_india"], adapter.max_jobs_per_board):
                        hit = ("new", ats, slug, len(jobs))
                        found.append(board)
                        break
                if hit:
                    break
            if hit and hit[0] == "known":
                self.stdout.write(f"  already listed  {name:22} {hit[1]}:{hit[2]}")
            elif hit:
                self.stdout.write(self.style.SUCCESS(f"  NEW             {name:22} {hit[1]}:{hit[2]}  (India postings with JD found)"))
            else:
                self.stdout.write(f"  no public board {name}")

        self.stdout.write(f"\n{len(found)} new board(s) found.")
        if opts["save"] and found:
            data = json.loads(BOARDS_FILE.read_text(encoding="utf-8"))
            data["boards"].extend(found)
            BOARDS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Saved to {BOARDS_FILE}"))
