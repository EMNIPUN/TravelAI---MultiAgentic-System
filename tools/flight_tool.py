import os
import re
import certifi
import airportsdata
import pycountry
import requests
from dotenv import load_dotenv

# ============================================================
# ENVIRONMENT SETUP
# ============================================================

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

API_KEY = os.getenv("AVIATATIONSTACK_API_KEY")

# Default origin when user specifies only a destination.
# Sri Lanka -> Bandaranaike International Airport (CMB)
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "CMB")

BASE_URL = "https://api.aviationstack.com/v1/flights"

# Load airport database
AIRPORTS = airportsdata.load("IATA")


# ============================================================
# COUNTRY ALIASES
# ============================================================

COUNTRY_ALIASES = {
    "usa": "US",
    "u.s.a": "US",
    "u.s.": "US",
    "america": "US",
    "united states": "US",

    "uk": "GB",
    "u.k.": "GB",
    "britain": "GB",
    "england": "GB",

    "uae": "AE",
    "dubai": "AE",

    "south korea": "KR",
    "korea": "KR",

    "russia": "RU",
    "vietnam": "VN",

    "bangladesh": "BD",

    # Sri Lanka
    "sri lanka": "LK",
    "srilanka": "LK",

    "india": "IN",
    "japan": "JP",
    "china": "CN",
    "singapore": "SG",
    "malaysia": "MY",
    "thailand": "TH",
    "indonesia": "ID",
    "nepal": "NP",
    "qatar": "QA",
    "saudi arabia": "SA",
    "turkey": "TR",
    "canada": "CA",
    "australia": "AU",
    "germany": "DE",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
}


# ============================================================
# PREFERRED MAIN AIRPORT FOR EACH COUNTRY
# ============================================================

COUNTRY_MAIN_AIRPORT = {
    # Sri Lanka
    "LK": "CMB",

    # Bangladesh
    "BD": "DAC",

    # India
    "IN": "DEL",

    # Japan
    "JP": "NRT",

    # USA
    "US": "JFK",

    # United Kingdom
    "GB": "LHR",

    # UAE
    "AE": "DXB",

    # Singapore
    "SG": "SIN",

    # Malaysia
    "MY": "KUL",

    # Thailand
    "TH": "BKK",

    # Indonesia
    "ID": "CGK",

    # China
    "CN": "PEK",

    # South Korea
    "KR": "ICN",

    # Nepal
    "NP": "KTM",

    # Qatar
    "QA": "DOH",

    # Saudi Arabia
    "SA": "JED",

    # Turkey
    "TR": "IST",

    # Canada
    "CA": "YYZ",

    # Australia
    "AU": "SYD",

    # Germany
    "DE": "FRA",

    # France
    "FR": "CDG",

    # Italy
    "IT": "FCO",

    # Spain
    "ES": "MAD",
}


# ============================================================
# CITY -> MAIN AIRPORT
# ============================================================

CITY_MAIN_AIRPORT = {

    # --------------------------------------------------------
    # Sri Lanka
    # --------------------------------------------------------

    "colombo": "CMB",
    "negombo": "CMB",
    "katunayake": "CMB",
    "katunayake airport": "CMB",
    "bandaranaike": "CMB",
    "bandaranaike international airport": "CMB",

    "kandy": "CMB",
    "galle": "CMB",

    "jaffna": "JAF",

    "hambantota": "HRI",
    "mattala": "HRI",
    "mattala rajapaksa": "HRI",
    "mattala international airport": "HRI",

    # --------------------------------------------------------
    # Bangladesh
    # --------------------------------------------------------

    "dhaka": "DAC",

    # --------------------------------------------------------
    # India
    # --------------------------------------------------------

    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "kolkata": "CCU",
    "chennai": "MAA",
    "bangalore": "BLR",
    "bengaluru": "BLR",

    # --------------------------------------------------------
    # Japan
    # --------------------------------------------------------

    "tokyo": "NRT",
    "osaka": "KIX",
    "kyoto": "KIX",

    # --------------------------------------------------------
    # USA
    # --------------------------------------------------------

    "new york": "JFK",

    # --------------------------------------------------------
    # United Kingdom
    # --------------------------------------------------------

    "london": "LHR",

    # --------------------------------------------------------
    # UAE
    # --------------------------------------------------------

    "dubai": "DXB",

    # --------------------------------------------------------
    # Singapore
    # --------------------------------------------------------

    "singapore": "SIN",

    # --------------------------------------------------------
    # Malaysia
    # --------------------------------------------------------

    "kuala lumpur": "KUL",

    # --------------------------------------------------------
    # Thailand
    # --------------------------------------------------------

    "bangkok": "BKK",

    # --------------------------------------------------------
    # Qatar
    # --------------------------------------------------------

    "doha": "DOH",

    # --------------------------------------------------------
    # Turkey
    # --------------------------------------------------------

    "istanbul": "IST",

    # --------------------------------------------------------
    # Canada
    # --------------------------------------------------------

    "toronto": "YYZ",

    # --------------------------------------------------------
    # Australia
    # --------------------------------------------------------

    "sydney": "SYD",

    # --------------------------------------------------------
    # France
    # --------------------------------------------------------

    "paris": "CDG",

    # --------------------------------------------------------
    # Italy
    # --------------------------------------------------------

    "rome": "FCO",

    # --------------------------------------------------------
    # Spain
    # --------------------------------------------------------

    "madrid": "MAD",

    # --------------------------------------------------------
    # Germany
    # --------------------------------------------------------

    "frankfurt": "FRA",
}


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text: str) -> str:
    """
    Cleans natural language input.

    Example:
        "Plan a 7 days Japan trip from Sri Lanka"
        ->
        "7 japan from sri lanka"
    """

    text = text.lower().strip()

    # Replace punctuation with spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    stop_words = [
        "flight",
        "flights",
        "ticket",
        "tickets",
        "trip",
        "travel",
        "plan",
        "complete",
        "days",
        "day",
        "including",
        "hotel",
        "hotels",
        "sightseeing",
        "under",
        "budget",
        "info",
        "information",
    ]

    words = [
        word
        for word in text.split()
        if word not in stop_words
    ]

    return " ".join(words).strip()


# ============================================================
# COUNTRY NAME -> COUNTRY CODE
# ============================================================

def country_name_to_code(text: str):
    """
    Converts country name or alias to ISO alpha-2 code.

    Examples:
        Sri Lanka -> LK
        Japan -> JP
        India -> IN
        Bangladesh -> BD
    """

    text = clean_text(text)

    if not text:
        return None

    # Check aliases first
    if text in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[text]

    # Try pycountry
    try:
        country = pycountry.countries.lookup(text)
        return country.alpha_2

    except LookupError:
        pass

    # Detect country name inside longer text
    for country in pycountry.countries:

        country_name = country.name.lower()

        if country_name in text:
            return country.alpha_2

    # Check aliases inside longer text
    for alias, code in COUNTRY_ALIASES.items():

        if alias in text:
            return code

    return None


# ============================================================
# AIRPORT COUNTRY MATCH
# ============================================================

def airport_country_matches(
    airport: dict,
    country_code: str
) -> bool:

    airport_country = str(
        airport.get("country", "")
    ).upper().strip()

    if airport_country == country_code:
        return True

    try:

        country = pycountry.countries.get(
            alpha_2=country_code
        )

        if country:

            if (
                airport_country.lower()
                == country.name.lower()
            ):
                return True

    except Exception:
        pass

    return False


# ============================================================
# FIND BEST AIRPORT FOR COUNTRY
# ============================================================

def get_best_airport_for_country(
    country_code: str
):
    """
    Returns preferred/main airport for a country.

    Example:
        LK -> CMB
        JP -> NRT
        IN -> DEL
    """

    preferred = COUNTRY_MAIN_AIRPORT.get(
        country_code
    )

    if preferred and preferred in AIRPORTS:
        return preferred

    candidates = []

    for iata, airport in AIRPORTS.items():

        if not iata:
            continue

        if airport_country_matches(
            airport,
            country_code
        ):

            name = str(
                airport.get("name", "")
            ).lower()

            city = str(
                airport.get("city", "")
            ).lower()

            score = 0

            if "international" in name:
                score += 50

            if "intl" in name:
                score += 40

            if "capital" in name:
                score += 20

            if city:
                score += 5

            candidates.append(
                (score, iata)
            )

    if not candidates:
        return None

    candidates.sort(
        reverse=True
    )

    return candidates[0][1]


# ============================================================
# LOCATION -> IATA
# ============================================================

def resolve_location_to_iata(
    location: str
):
    """
    Converts country/city/airport/IATA
    into an IATA airport code.

    Examples:

        Sri Lanka -> CMB
        Colombo -> CMB
        Negombo -> CMB
        Japan -> NRT
        Tokyo -> NRT
        Dhaka -> DAC
        CMB -> CMB
    """

    if not location:
        return None

    raw_location = location.strip()

    # --------------------------------------------------------
    # Direct IATA code
    # --------------------------------------------------------

    if re.fullmatch(
        r"[A-Za-z]{3}",
        raw_location
    ):

        code = raw_location.upper()

        if code in AIRPORTS:
            return code

    # --------------------------------------------------------
    # Clean location
    # --------------------------------------------------------

    location_clean = clean_text(
        raw_location
    )

    if not location_clean:
        return None

    # --------------------------------------------------------
    # City preferred airport
    # --------------------------------------------------------

    if location_clean in CITY_MAIN_AIRPORT:

        return CITY_MAIN_AIRPORT[
            location_clean
        ]

    # --------------------------------------------------------
    # Country preferred airport
    # --------------------------------------------------------

    country_code = country_name_to_code(
        location_clean
    )

    if country_code:

        airport = get_best_airport_for_country(
            country_code
        )

        if airport:
            return airport

    # --------------------------------------------------------
    # Search airport database
    # --------------------------------------------------------

    city_matches = []

    for iata, airport in AIRPORTS.items():

        city = str(
            airport.get("city", "")
        ).lower().strip()

        name = str(
            airport.get("name", "")
        ).lower().strip()

        score = 0

        if city == location_clean:
            score += 100

        elif location_clean in city:
            score += 70

        if location_clean in name:
            score += 50

        if "international" in name:
            score += 10

        if score > 0:

            city_matches.append(
                (score, iata)
            )

    if city_matches:

        city_matches.sort(
            reverse=True
        )

        return city_matches[0][1]

    return None


# ============================================================
# FIND LOCATION MENTIONS
# ============================================================

def find_location_mentions(
    query: str
):
    """
    Finds country or city names
    inside a natural language query.
    """

    q = query.lower()

    mentions = []

    # --------------------------------------------------------
    # Country aliases
    # --------------------------------------------------------

    for alias in COUNTRY_ALIASES:

        if re.search(
            rf"\b{re.escape(alias)}\b",
            q
        ):

            mentions.append(alias)

    # --------------------------------------------------------
    # Country names from pycountry
    # --------------------------------------------------------

    for country in pycountry.countries:

        name = country.name.lower()

        if (
            len(name) >= 4
            and re.search(
                rf"\b{re.escape(name)}\b",
                q
            )
        ):

            mentions.append(name)

    # --------------------------------------------------------
    # City names
    # --------------------------------------------------------

    for city in CITY_MAIN_AIRPORT:

        if re.search(
            rf"\b{re.escape(city)}\b",
            q
        ):

            mentions.append(city)

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    unique_mentions = []

    for item in mentions:

        if item not in unique_mentions:
            unique_mentions.append(item)

    return unique_mentions


# ============================================================
# PARSE ROUTE
# ============================================================

def parse_route(query: str):
    """
    Returns:

        dep_iata, arr_iata

    Possible results:

        None, None
            -> global live flights

        CMB, NRT
            -> Sri Lanka to Japan

        CMB, None
            -> all flights from Sri Lanka

        None, NRT
            -> all flights to Japan
    """

    q = query.strip()
    q_lower = q.lower()

    # ========================================================
    # GLOBAL / ALL COUNTRY QUERY
    # ========================================================

    global_keywords = [
        "all country",
        "all countries",
        "global flight",
        "global flights",
        "all flight",
        "all flights",
        "worldwide flight",
        "worldwide flights",
    ]

    if any(
        keyword in q_lower
        for keyword in global_keywords
    ):

        return None, None

    # ========================================================
    # DIRECT IATA ROUTE
    #
    # Example:
    # CMB to NRT
    # DAC to CMB
    # ========================================================

    codes = re.findall(
        r"\b[A-Z]{3}\b",
        q
    )

    valid_codes = [
        code.upper()
        for code in codes
        if code.upper() in AIRPORTS
    ]

    if len(valid_codes) >= 2:

        dep = valid_codes[0]
        arr = valid_codes[1]

        return dep, arr

    # ========================================================
    # FROM X TO Y
    #
    # Example:
    # Flights from Sri Lanka to Japan
    # Flights from Colombo to Tokyo
    # ========================================================

    match = re.search(
        r"\bfrom\s+(.+?)\s+\bto\s+(.+?)"
        r"(?:\s+(?:on|for|under|including|with|in|at)\b"
        r"|[.!?]|$)",
        q_lower,
    )

    if match:

        origin_text = match.group(1)
        dest_text = match.group(2)

        dep_iata = resolve_location_to_iata(
            origin_text
        )

        arr_iata = resolve_location_to_iata(
            dest_text
        )

        return dep_iata, arr_iata

    # ========================================================
    # TO X FROM Y
    #
    # Example:
    # Flights to Japan from Sri Lanka
    # ========================================================

    match = re.search(
        r"\bto\s+(.+?)\s+\bfrom\s+(.+?)"
        r"(?:\s+(?:on|for|under|including|with|in|at)\b"
        r"|[.!?]|$)",
        q_lower,
    )

    if match:

        dest_text = match.group(1)
        origin_text = match.group(2)

        dep_iata = resolve_location_to_iata(
            origin_text
        )

        arr_iata = resolve_location_to_iata(
            dest_text
        )

        return dep_iata, arr_iata

    # ========================================================
    # FLIGHTS FROM X
    # ========================================================

    match = re.search(
        r"\bfrom\s+(.+?)(?:[.!?]|$)",
        q_lower
    )

    if match:

        origin_text = match.group(1)

        dep_iata = resolve_location_to_iata(
            origin_text
        )

        return dep_iata, None

    # ========================================================
    # FLIGHTS TO X
    # ========================================================

    match = re.search(
        r"\bto\s+(.+?)(?:[.!?]|$)",
        q_lower
    )

    if match:

        dest_text = match.group(1)

        arr_iata = resolve_location_to_iata(
            dest_text
        )

        return None, arr_iata

    # ========================================================
    # FALLBACK: FIND LOCATION MENTIONS
    # ========================================================

    mentions = find_location_mentions(q)

    # --------------------------------------------------------
    # Two locations
    # --------------------------------------------------------

    if len(mentions) >= 2:

        dep_iata = resolve_location_to_iata(
            mentions[0]
        )

        arr_iata = resolve_location_to_iata(
            mentions[1]
        )

        return dep_iata, arr_iata

    # --------------------------------------------------------
    # One location
    #
    # Example:
    # "Japan trip"
    #
    # Automatically:
    # CMB -> NRT
    # --------------------------------------------------------

    if len(mentions) == 1:

        arr_iata = resolve_location_to_iata(
            mentions[0]
        )

        return DEFAULT_ORIGIN_IATA, arr_iata

    # ========================================================
    # NOTHING FOUND
    # ========================================================

    return None, None


# ============================================================
# FORMAT FLIGHT
# ============================================================

def format_flight(
    flight: dict
):

    airline = (
        flight.get("airline", {}).get("name")
        or "Unknown airline"
    )

    flight_number = (
        flight.get("flight", {}).get("iata")
        or "Unknown flight number"
    )

    status = (
        flight.get("flight_status")
        or "Unknown"
    )

    dep = flight.get(
        "departure",
        {}
    ) or {}

    arr = flight.get(
        "arrival",
        {}
    ) or {}

    # --------------------------------------------------------
    # Departure
    # --------------------------------------------------------

    dep_airport = (
        dep.get("airport")
        or "Unknown departure airport"
    )

    dep_iata = (
        dep.get("iata")
        or "Unknown"
    )

    dep_terminal = (
        dep.get("terminal")
        or "N/A"
    )

    dep_gate = (
        dep.get("gate")
        or "N/A"
    )

    dep_scheduled = (
        dep.get("scheduled")
        or "Unknown"
    )

    dep_delay = dep.get(
        "delay"
    )

    dep_delay_text = (
        f"{dep_delay} minutes"
        if dep_delay is not None
        else "N/A"
    )

    # --------------------------------------------------------
    # Arrival
    # --------------------------------------------------------

    arr_airport = (
        arr.get("airport")
        or "Unknown arrival airport"
    )

    arr_iata = (
        arr.get("iata")
        or "Unknown"
    )

    arr_terminal = (
        arr.get("terminal")
        or "N/A"
    )

    arr_gate = (
        arr.get("gate")
        or "N/A"
    )

    arr_scheduled = (
        arr.get("scheduled")
        or "Unknown"
    )

    arr_delay = arr.get(
        "delay"
    )

    arr_delay_text = (
        f"{arr_delay} minutes"
        if arr_delay is not None
        else "N/A"
    )

    # --------------------------------------------------------
    # Return formatted information
    # --------------------------------------------------------

    return f"""
Airline: {airline}
Flight: {flight_number}
Status: {status}

Departure:
- Airport: {dep_airport}
- IATA: {dep_iata}
- Terminal: {dep_terminal}
- Gate: {dep_gate}
- Scheduled: {dep_scheduled}
- Delay: {dep_delay_text}

Arrival:
- Airport: {arr_airport}
- IATA: {arr_iata}
- Terminal: {arr_terminal}
- Gate: {arr_gate}
- Scheduled: {arr_scheduled}
- Delay: {arr_delay_text}
""".strip()


# ============================================================
# SEARCH FLIGHTS
# ============================================================

def search_flights(
    query: str,
    limit: int = 10
):

    # ========================================================
    # CHECK API KEY
    # ========================================================

    if not API_KEY:

        return (
            "Flight API error: "
            "AVIATIONSTACK_API_KEY is missing.\n\n"
            "Please add this to your .env file:\n\n"
            "AVIATIONSTACK_API_KEY=your_api_key_here"
        )

    # ========================================================
    # PARSE ROUTE
    # ========================================================

    dep_iata, arr_iata = parse_route(
        query
    )

    # ========================================================
    # API PARAMETERS
    # ========================================================

    params = {
        "access_key": API_KEY,
        "limit": min(limit, 100),
    }

    if dep_iata:
        params["dep_iata"] = dep_iata

    if arr_iata:
        params["arr_iata"] = arr_iata

    # ========================================================
    # API REQUEST
    # ========================================================

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        data = response.json()

    except requests.exceptions.RequestException as e:

        return (
            f"Flight API request failed: {e}"
        )

    except ValueError:

        return (
            "Flight API returned invalid JSON."
        )

    # ========================================================
    # API ERROR
    # ========================================================

    if "error" in data:

        error = data["error"]

        return (
            "Flight API error:\n"
            f"Code: {error.get('code', 'Unknown')}\n"
            f"Message: "
            f"{error.get('message', 'Unknown error')}"
        )

    # ========================================================
    # FLIGHT DATA
    # ========================================================

    flight_data = data.get(
        "data",
        []
    )

    # ========================================================
    # NO DATA
    # ========================================================

    if not flight_data:

        route_text = ""

        if dep_iata and arr_iata:

            route_text = (
                f" for route "
                f"{dep_iata} to {arr_iata}"
            )

        elif dep_iata:

            route_text = (
                f" from {dep_iata}"
            )

        elif arr_iata:

            route_text = (
                f" to {arr_iata}"
            )

        return (
            f"No live flight data found"
            f"{route_text}.\n\n"
            "Note: AviationStack provides "
            "live/status flight data, not "
            "ticket prices.\n"
            "For actual fare prices, use a "
            "flight-pricing API such as Amadeus."
        )

    # ========================================================
    # ROUTE INFORMATION
    # ========================================================

    route_info = "Global live flights"

    if dep_iata and arr_iata:

        route_info = (
            f"Live flights from "
            f"{dep_iata} to {arr_iata}"
        )

    elif dep_iata:

        route_info = (
            f"Live flights from {dep_iata}"
        )

    elif arr_iata:

        route_info = (
            f"Live flights to {arr_iata}"
        )

    # ========================================================
    # FORMAT RESULTS
    # ========================================================

    formatted_flights = [
        format_flight(flight)
        for flight in flight_data[:limit]
    ]

    return (
        f"{route_info}\n\n"
        + "\n\n---\n\n".join(
            formatted_flights
        )
    )


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("TEST 1: Japan trip")
    print("=" * 80)

    print(
        search_flights(
            "Plan a 7 days Japan trip"
        )
    )

    print("\n" + "=" * 80)
    print("TEST 2: Japan trip from Sri Lanka")
    print("=" * 80)

    print(
        search_flights(
            "Plan a Japan trip from Sri Lanka"
        )
    )

    print("\n" + "=" * 80)
    print("TEST 3: Colombo to Tokyo")
    print("=" * 80)

    print(
        search_flights(
            "Flights from Colombo to Tokyo"
        )
    )

    print("\n" + "=" * 80)
    print("TEST 4: Sri Lanka to Japan")
    print("=" * 80)

    print(
        search_flights(
            "Flights from Sri Lanka to Japan"
        )
    )

    print("\n" + "=" * 80)
    print("TEST 5: CMB to NRT")
    print("=" * 80)

    print(
        search_flights(
            "CMB to NRT"
        )
    )

    print("\n" + "=" * 80)
    print("TEST 6: Flights from Sri Lanka")
    print("=" * 80)

    print(
        search_flights(
            "Flights from Sri Lanka"
        )
    )

    print("\n" + "=" * 80)
    print("TEST 7: Flights to Japan")
    print("=" * 80)

    print(
        search_flights(
            "Flights to Japan"
        )
    )

    print("\n" + "=" * 80)
    print("TEST 8: All country flights")
    print("=" * 80)

    print(
        search_flights(
            "all country flight info"
        )
    )