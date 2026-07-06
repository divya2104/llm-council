"""Configuration constants for the JD Creator wizard."""

# Data directory for JD draft storage
JD_DATA_DIR = "data/jd_drafts"

# Lines of Business
LOB_OPTIONS = ["AMC", "NBFC"]

LOB_LABELS = {
    "AMC": "AMC (ABSLAMC)",
    "NBFC": "NBFC (Lending)",
}

LOB_DESCRIPTIONS = {
    "AMC": "Asset Management Company — Mutual Funds, PMS, Offshore, AIF",
    "NBFC": "Non-Banking Financial Company — Home Loans, LAP, Personal Loans",
}

LOB_BUSINESS_OPTIONS = {
    "AMC": ["ABSLAMC", "Offshore", "PMS", "AIF"],
    "NBFC": ["ABHFL", "ABFL", "ABPFL"],
}

LOB_ORG_CONTEXT_TEMPLATES = {
    "AMC": (
        "Established in 1994, Aditya Birla Sun Life Asset Management Company "
        "(ABSLAMC) is a joint venture between Aditya Birla Group and Sun Life "
        "Financial Inc. ABSLAMC is a leading fund manager with AAUM of "
        "₹3.82 Lakh Cr, offering mutual funds, portfolio management "
        "services, offshore funds, and alternative investment funds."
    ),
    "NBFC": (
        "Aditya Birla Finance Limited group companies are leading "
        "non-banking financial companies (NBFCs) offering home loans, loan "
        "against property, and personal loans across India, backed by the "
        "Aditya Birla Group's diversified financial services franchise."
    ),
}

LOB_CITY_OPTIONS = [
    "Mumbai",
    "Delhi",
    "Bengaluru",
    "Chennai",
    "Kolkata",
    "Hyderabad",
    "Pune",
    "Ahmedabad",
    "Indore",
    "Jaipur",
]

HIERARCHY_LEVELS = [f"JB {i}" for i in range(1, 9)]

RELATIONSHIP_FREQUENCIES = ["Daily", "Weekly", "Monthly", "Quarterly", "Need Basis"]

AMBIGUITY_LEVELS = [
    "Highly Structured",
    "Moderately Structured",
    "Broadly Defined",
    "Abstract",
]

DEPARTMENTS_BY_FUNCTION = {
    "Investments": ["Equity", "Fixed Income", "Alternate Assets", "Research"],
    "Sales": ["Institutional Sales", "Retail Sales", "Channel Partners"],
    "Finance": ["Accounts & Taxation", "Business Planning & Analytics", "Treasury"],
    "Credit": ["Retail Credit", "Corporate Credit", "Credit Policy"],
    "Collections": ["Field Collections", "Tele-Collections", "Legal Recovery"],
    "Legal & Compliance": ["Regulatory Compliance", "Legal Affairs", "Secretarial"],
    "Operations": ["Fund Operations", "Loan Operations", "Customer Service"],
    "Technology": ["IT Infrastructure", "Application Development", "Cybersecurity"],
    "Human Resources": ["Talent Acquisition", "HR Business Partner", "L&D"],
    "Risk": ["Market Risk", "Credit Risk", "Operational Risk"],
}

MINIMUM_QUALIFICATION_OPTIONS = ["CA", "MBA", "CFA", "CS", "LLB", "Engineering", "PhD"]

INDUSTRY_EXPERIENCE_OPTIONS = [
    "Asset Management",
    "Capital Markets",
    "Banking",
    "NBFC / Lending",
    "Insurance",
    "Consulting",
]

# Row/character thresholds (NON-NEGOTIABLE fields unless noted)
MIN_ACCOUNTABILITIES = 5
MAX_ACCOUNTABILITIES = 15
MIN_INTERNAL_RELATIONSHIPS = 3
MIN_EXTERNAL_RELATIONSHIPS = 2
MIN_CHALLENGES = 3
MAX_CHALLENGES = 8
JOB_PURPOSE_MIN_CHARS = 100
JOB_PURPOSE_MAX_CHARS = 2000
JOB_CONTEXT_MIN_CHARS = 200

# Wizard step order (single source of truth for stepper UI + validation)
WIZARD_STEPS = [
    {"key": "basics", "label": "Basics"},
    {"key": "purpose", "label": "Purpose"},
    {"key": "dimensions", "label": "Dims"},
    {"key": "context", "label": "Context"},
    {"key": "accountabilities", "label": "Accts"},
    {"key": "reports_and_relationships", "label": "Reports"},
    {"key": "hay_factors", "label": "Hay"},
    {"key": "sign_off", "label": "Sign-Off"},
]
