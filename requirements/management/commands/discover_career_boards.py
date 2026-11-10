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
    # More Indian startups and product companies
    "Ather Energy", "Ola Electric", "Rebel Foods", "Swiggy Instamart", "Porter", "Cure.fit",
    "Groww Tech", "Smallcase", "INDmoney", "Kotak Securities", "Jumbotail", "Udaan", "Infra.Market",
    "OfBusiness", "Moglix", "Zetwerk", "Mamaearth", "Honasa", "boAt", "Sugar Cosmetics", "Purplle",
    "FirstCry", "Bewakoof", "Snapdeal", "Paytm Money", "Khatabook", "OkCredit", "Vyapar",
    "Classplus", "Testbook", "Adda247", "Byju's", "Toppr", "Great Learning", "Masai School",
    "Newton School", "AlmaBetter", "Coding Ninjas", "GeeksforGeeks", "HackerEarth", "HackerRank",
    "Hevo Data", "Sprinklr", "Capillary", "Exotel", "Haptik", "Yellow.ai", "Gupshup", "Observe.AI",
    "Locus", "FarEye", "Shipsy", "Signzy", "Perfios", "IDfy", "Credgenics", "Rupeek", "KreditBee",
    "Fibe", "MoneyView", "Lendingkart", "OneCard", "Uni Cards", "Open Financial", "RazorpayX",
    "Plum", "Loop Health", "Even Healthcare", "Pristyn Care", "Tata 1mg", "Medikabazaar",
    "Eka Care", "Nference", "Qure.ai", "SigTuple", "Tricog", "Wysa", "Increff", "Unbxd",
    "Netcore", "MoEngage", "CleverTap", "WebEngage", "Mailmodo", "Rocketlane", "Zluri", "Sprinto",
    "Scrut", "Superops", "Facilio", "Kissflow", "Freshdesk", "Zoho Corp", "Druva Inc", "Icertis",
    "Amagi", "MediaAmp", "Toplyne", "Fyle", "Chargebee Inc", "BrowserStack Inc", "LambdaTest",
    "Testsigma", "DeepSource", "Appsmith", "ToolJet", "Hoppscotch", "SigNoz", "Dyte", "100ms",
    "Ultrahuman", "Ola Krutrim", "Neysa", "Sarvam AI", "Gnani", "Rephrase.ai", "Wadhwani AI",
    # IT services and consulting firms hiring freshers in India
    "Infosys", "TCS", "Wipro", "HCLTech", "Tech Mahindra", "LTIMindtree", "Mphasis", "Persistent",
    "Coforge", "Hexaware", "Zensar", "Birlasoft", "Cyient", "KPIT", "Tata Elxsi", "Sasken",
    "Happiest Minds", "Mastek", "NIIT Technologies", "Sonata Software", "Thoughtworks", "Publicis Sapient",
    "EPAM", "GlobalLogic", "Nagarro", "Sigmoid", "Tiger Analytics", "Fractal", "MathCo",
    "LatentView", "Mu Sigma", "Quantiphi", "Tredence", "Course5", "Ugam", "Kantar",
    # Global companies with large India engineering offices
    "Stripe", "Databricks", "Rubrik", "Nutanix", "Okta", "Twilio", "Cloudflare", "MongoDB",
    "Confluent", "Elastic", "GitLab", "HashiCorp", "Coinbase", "Airbnb", "Uber", "Atlassian",
    "Salesforce", "ServiceNow", "Workday", "Adobe", "Intuit", "PayPal", "Visa", "Mastercard",
    "American Express", "Goldman Sachs", "Morgan Stanley", "JPMorgan", "Deutsche Bank", "Barclays",
    "Walmart Global Tech", "Target", "Lowe's", "Tesco", "Sainsbury's", "IKEA", "H&M",
    "Wayfair", "Expedia", "Booking.com", "Agoda", "Grab", "Gojek", "Shopee", "Rippling", "Deel",
    "Remote", "Gusto", "Brex", "Ramp", "Plaid", "Chime", "Robinhood", "Wise", "Revolut", "Klarna",
    "Canva", "Figma", "Notion", "Miro", "Dropbox", "Box", "Zendesk", "HubSpot", "Freshservice",
    "Docusign", "Zscaler", "CrowdStrike", "Palo Alto Networks", "Fortinet", "Check Point",
    "Commvault", "Veeam", "NetApp", "Pure Storage", "Snowflake", "Datadog", "New Relic",
    "Dynatrace", "Splunk", "PagerDuty", "Grafana Labs", "Sumo Logic", "Harness", "JFrog",
    "CircleCI", "Postman Inc", "Kong", "Celonis", "UiPath", "Automation Anywhere", "Blue Yonder",
    "o9 Solutions", "Sprinklr Inc", "Gainsight", "Amagi Media", "Vymo", "Synopsys", "Cadence",
    "Qualcomm", "NVIDIA", "AMD", "Intel", "Micron", "Western Digital", "Arm", "Texas Instruments",
    "Siemens", "Bosch", "Philips", "GE HealthCare", "Honeywell", "Schneider Electric", "ABB",
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
