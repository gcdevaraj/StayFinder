#!/usr/bin/env python3
"""
StayFinder – scripts/seed.py
Run: python scripts/seed.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import uuid, json
import bcrypt
from database import init_db, db

def h(pw): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(10)).decode()


def seed():
    init_db()
    print("\n[Seed] Seeding StayFinder...\n")

    with db() as conn:

        # ── Amenities ──────────────────────────────────────────────
        amenity_rows = [
            ("WiFi",          "📶", "basic"),
            ("Power Backup",  "🔋", "basic"),
            ("Hot Water",     "🚿", "basic"),
            ("Furnished",     "🪑", "basic"),
            ("AC",            "❄️", "comfort"),
            ("Gym",           "💪", "comfort"),
            ("TV",            "📺", "comfort"),
            ("Balcony",       "🏡", "comfort"),
            ("CCTV",          "📷", "security"),
            ("24x7 Security", "🔒", "security"),
            ("Gated Entry",   "🚪", "security"),
            ("Meals",         "🍽️", "food"),
            ("Kitchen",       "🍳", "food"),
            ("RO Water",      "💧", "food"),
            ("Parking",       "🚗", "transport"),
            ("Laundry",       "👕", "transport"),
            ("Bike Parking",  "🛵", "transport"),
        ]
        amenity_map = {}  # name -> id
        for name, icon, cat in amenity_rows:
            existing = conn.execute("SELECT id FROM amenities WHERE name=?", (name,)).fetchone()
            if existing:
                amenity_map[name] = existing["id"]
            else:
                aid = str(uuid.uuid4())
                conn.execute("INSERT INTO amenities (id,name,icon,category) VALUES (?,?,?,?)",
                             (aid, name, icon, cat))
                amenity_map[name] = aid
        print(f"  [OK] {len(amenity_rows)} amenities")

        # ── Users ──────────────────────────────────────────────────
        def upsert_user(name, email, password, role, phone, verified=True):
            existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if existing:
                return existing["id"]
            uid = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO users (id,name,email,phone,password_hash,role,verified) VALUES (?,?,?,?,?,?,?)",
                (uid, name, email, phone, h(password), role, int(verified))
            )
            return uid

        admin_id = upsert_user("Admin", "admin@stayfinder.in", "Admin@123", "admin", "+919900000000")
        owner_ids = [
            upsert_user("Ramesh Kumar",   "ramesh@owner.com",    "Owner@123", "owner", "+919845012345"),
            upsert_user("Priya Nair",     "priya@owner.com",     "Owner@123", "owner", "+918765432100"),
            upsert_user("Suresh Rao",     "suresh@owner.com",    "Owner@123", "owner", "+919900123456"),
            upsert_user("Anita Sharma",   "anita@owner.com",     "Owner@123", "owner", "+917654321098"),
            upsert_user("Manjunath BS",   "manjunath@owner.com", "Owner@123", "owner", "+918000144444", False),
        ]
        test_id = upsert_user("Test User", "test@user.com", "Test@123", "user", "+919999999999")
        print(f"  [OK] 1 admin, {len(owner_ids)} owners, 1 test user")

        # ── Properties ─────────────────────────────────────────────
        def upsert_property(data):
            existing = conn.execute("SELECT id FROM properties WHERE name=?", (data["name"],)).fetchone()
            if existing:
                return existing["id"]
            pid = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO properties
                   (id,owner_id,name,type,gender,area,address,city,lat,lng,
                    description,nearby_landmarks,price_min,price_max,deposit,
                    verified,available,total_rooms,avail_rooms)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pid, data["owner_id"], data["name"], data["type"], data["gender"],
                 data["area"], data["address"], data.get("city","Bengaluru"),
                 data.get("lat"), data.get("lng"),
                 data["description"], data.get("nearby"),
                 data["price_min"], data["price_max"], data.get("deposit"),
                 int(data.get("verified",True)), int(data.get("available",True)),
                 data.get("total_rooms",20), data.get("avail_rooms",5))
            )
            for aname in data.get("amenities", []):
                if aname in amenity_map:
                    conn.execute(
                        "INSERT OR IGNORE INTO property_amenities (property_id,amenity_id) VALUES (?,?)",
                        (pid, amenity_map[aname])
                    )
            for r in data.get("rooms", []):
                conn.execute(
                    "INSERT INTO rooms (id,property_id,sharing_type,price,count) VALUES (?,?,?,?,?)",
                    (str(uuid.uuid4()), pid, r["sharing_type"], r["price"], r.get("count",1))
                )
            return pid

        props = [
            dict(owner_id=owner_ids[0], name="Koramangala Comfort PG",
                 type="PG", gender="Men", area="Koramangala",
                 address="5th Block, Koramangala, Bengaluru", lat=12.9352, lng=77.6245,
                 description="Well-maintained PG with homely food and 24/7 security. Walking distance to Wipro and other IT companies. Spacious rooms with ample storage.",
                 nearby="Wipro, Infosys (2 km), Forum Mall",
                 price_min=7500, price_max=12000, deposit=15000,
                 total_rooms=20, avail_rooms=5,
                 amenities=["WiFi","Meals","CCTV","Laundry","Hot Water","Power Backup"],
                 rooms=[{"sharing_type":"Single","price":12000,"count":5},
                        {"sharing_type":"Double","price":8500,"count":10},
                        {"sharing_type":"Triple","price":7500,"count":5}]),

            dict(owner_id=owner_ids[1], name="Sakura Women's Hostel",
                 type="Private Hostel", gender="Women", area="Indiranagar",
                 address="12th Main, Indiranagar, Bengaluru", lat=12.9784, lng=77.6408,
                 description="Premium women-only hostel with 24/7 security. Spacious rooms, great food, rooftop common area with city views.",
                 nearby="100 Feet Road, CMH Road, Indiranagar Metro",
                 price_min=9000, price_max=16000, deposit=18000,
                 total_rooms=30, avail_rooms=3,
                 amenities=["WiFi","AC","Meals","Gym","CCTV","24x7 Security","Hot Water","RO Water"],
                 rooms=[{"sharing_type":"Single","price":16000,"count":8},
                        {"sharing_type":"Double","price":11000,"count":14},
                        {"sharing_type":"Triple","price":9000,"count":8}]),

            dict(owner_id=owner_ids[2], name="TechPark Residency",
                 type="PG", gender="Co-ed", area="Whitefield",
                 address="EPIP Zone, Whitefield, Bengaluru", lat=12.9698, lng=77.7500,
                 description="Premium co-living near EPIP Zone and ITPL. High-speed 200 Mbps internet, modern furniture.",
                 nearby="ITPL, EPIP Zone, Mindtree, Phoenix Marketcity",
                 price_min=11000, price_max=18000, deposit=22000,
                 total_rooms=40, avail_rooms=8,
                 amenities=["WiFi","AC","Parking","Power Backup","Laundry","Gym","CCTV"],
                 rooms=[{"sharing_type":"Single","price":18000,"count":10},
                        {"sharing_type":"Double","price":13000,"count":20},
                        {"sharing_type":"Triple","price":11000,"count":10}]),

            dict(owner_id=owner_ids[4], name="Namma PG – BTM",
                 type="PG", gender="Men", area="BTM Layout",
                 address="2nd Stage, BTM Layout, Bengaluru", lat=12.9165, lng=77.6101,
                 description="Budget-friendly PG in BTM with good connectivity to Electronic City and Silk Board.",
                 nearby="Silk Board, Meenakshi Mall, BTM Bus Stand",
                 price_min=5500, price_max=8000, deposit=8000, verified=False,
                 total_rooms=15, avail_rooms=4,
                 amenities=["WiFi","Meals","CCTV","Hot Water"],
                 rooms=[{"sharing_type":"Double","price":6500,"count":8},
                        {"sharing_type":"Triple","price":5500,"count":7}]),

            dict(owner_id=owner_ids[3], name="HSR Cozy Nest",
                 type="PG", gender="Women", area="HSR Layout",
                 address="Sector 6, HSR Layout, Bengaluru", lat=12.9116, lng=77.6474,
                 description="Peaceful women's PG near Agara Lake. Excellent food — North and South Indian options.",
                 nearby="HSR BDA Complex, Agara Lake, Decathlon",
                 price_min=8000, price_max=14000, deposit=16000,
                 total_rooms=18, avail_rooms=2,
                 amenities=["WiFi","Meals","AC","CCTV","Power Backup","Hot Water","Laundry"],
                 rooms=[{"sharing_type":"Single","price":14000,"count":6},
                        {"sharing_type":"Double","price":10000,"count":8},
                        {"sharing_type":"Triple","price":8000,"count":4}]),

            dict(owner_id=owner_ids[2], name="Marathon Stay – Marathahalli",
                 type="Private Hostel", gender="Co-ed", area="Marathahalli",
                 address="Outer Ring Road, Marathahalli, Bengaluru", lat=12.9591, lng=77.6970,
                 description="Modern hostel with dorm and private rooms. Perfect for newcomers on a budget.",
                 nearby="Marathahalli Bridge, Phoenix Mall, Innovative Multiplex",
                 price_min=4000, price_max=9000, deposit=8000,
                 total_rooms=50, avail_rooms=12,
                 amenities=["WiFi","Laundry","Power Backup","CCTV","Hot Water","RO Water"],
                 rooms=[{"sharing_type":"Dorm","price":4000,"count":20},
                        {"sharing_type":"Double","price":6500,"count":20},
                        {"sharing_type":"Single","price":9000,"count":10}]),

            dict(owner_id=owner_ids[4], name="Silicon Valley PG",
                 type="PG", gender="Men", area="Electronic City",
                 address="Phase 1, Electronic City, Bengaluru", lat=12.8399, lng=77.6770,
                 description="Strategic location near Electronics City Phase 1 & 2. Shuttle service on request.",
                 nearby="Infosys, Wipro, HCL (1.5 km), EC Metro",
                 price_min=5500, price_max=9500, deposit=10000, available=False,
                 total_rooms=25, avail_rooms=0,
                 amenities=["WiFi","Meals","Gym","Parking","CCTV","Power Backup"],
                 rooms=[{"sharing_type":"Single","price":9500,"count":5},
                        {"sharing_type":"Double","price":7000,"count":12},
                        {"sharing_type":"Triple","price":5500,"count":8}]),

            dict(owner_id=owner_ids[3], name="Jayanagar Heritage PG",
                 type="PG", gender="Co-ed", area="Jayanagar",
                 address="4th Block, Jayanagar, Bengaluru", lat=12.9259, lng=77.5842,
                 description="Upscale PG in Jayanagar 4th Block. Traditional home-cooked Karnataka cuisine.",
                 nearby="Jayanagar Shopping Complex, NIMHANS, National Games Village",
                 price_min=9500, price_max=16000, deposit=19000,
                 total_rooms=22, avail_rooms=4,
                 amenities=["WiFi","AC","Meals","Laundry","CCTV","24x7 Security","Hot Water"],
                 rooms=[{"sharing_type":"Single","price":16000,"count":8},
                        {"sharing_type":"Double","price":12000,"count":10},
                        {"sharing_type":"Triple","price":9500,"count":4}]),

            dict(owner_id=owner_ids[0], name="Hebbal Connect Hostel",
                 type="Private Hostel", gender="Men", area="Hebbal",
                 address="Hebbal Ring Road, Bengaluru", lat=13.0358, lng=77.5970,
                 description="Well-connected hostel near Hebbal flyover. Easy access to Manyata Tech Park.",
                 nearby="Manyata Tech Park, Hebbal Lake, Airport (22 km)",
                 price_min=6000, price_max=11000, deposit=12000, verified=False,
                 total_rooms=30, avail_rooms=9,
                 amenities=["WiFi","Meals","Power Backup","Parking","CCTV"],
                 rooms=[{"sharing_type":"Single","price":11000,"count":8},
                        {"sharing_type":"Double","price":8000,"count":14},
                        {"sharing_type":"Dorm","price":6000,"count":8}]),

            dict(owner_id=owner_ids[3], name="Bannerghatta Bliss PG",
                 type="PG", gender="Women", area="Bannerghatta Road",
                 address="JP Nagar 7th Phase, Bannerghatta Road, Bengaluru", lat=12.8829, lng=77.5985,
                 description="Peaceful women's PG near Bannerghatta National Park. Strict hygiene standards.",
                 nearby="JP Nagar, Bannerghatta National Park, Arekere Gate",
                 price_min=6500, price_max=13000, deposit=13000,
                 total_rooms=16, avail_rooms=3,
                 amenities=["WiFi","AC","Meals","CCTV","Gym","Hot Water","24x7 Security"],
                 rooms=[{"sharing_type":"Single","price":13000,"count":6},
                        {"sharing_type":"Double","price":9000,"count":7},
                        {"sharing_type":"Triple","price":6500,"count":3}]),
        ]

        prop_ids = [upsert_property(p) for p in props]
        print(f"  [OK] {len(prop_ids)} properties")

        # ── Reviews ────────────────────────────────────────────────
        review_data = [
            (5, "Excellent PG! Food is amazing and the owner is very helpful. Highly recommended."),
            (4, "Good location and facilities. WiFi speed could be better but overall great stay."),
            (5, "Very clean rooms, homely atmosphere. Staying here for 2 years — no complaints."),
            (4, "Decent place with all basic amenities. Cook makes delicious South Indian food."),
            (3, "Average place. Location is good but maintenance needs improvement."),
            (5, "Best PG in the area! Security is top-notch and management is very responsive."),
            (4, "Nice comfortable rooms. Slightly expensive but worth it for AC and cleanliness."),
            (5, "Stayed 8 months. Safe, clean, great food variety. Would stay again!"),
        ]
        rc = 0
        for pid, (rating, comment) in zip(prop_ids, review_data):
            existing = conn.execute("SELECT id FROM reviews WHERE property_id=? AND user_id=?",
                                    (pid, test_id)).fetchone()
            if not existing:
                conn.execute("INSERT INTO reviews (id,property_id,user_id,rating,comment) VALUES (?,?,?,?,?)",
                             (str(uuid.uuid4()), pid, test_id, rating, comment))
                rc += 1
        print(f"  [OK] {rc} reviews")

        # ── Govt Hostels ───────────────────────────────────────────
        govt_data = [
            ("Dr. B.R. Ambedkar SC/ST Boys Hostel", "Dept of Social Welfare, Karnataka",
             "Chamrajpet", '["SC/ST"]', "Free", None, 120, 15,
             "080-2226-0001", "https://sw.kar.nic.in",
             "Govt hostel for SC/ST male students in classes 9-10. Includes food, lodging and scholarship."),

            ("KSWDC Working Women's Hostel", "Dept of Women & Child Development, Karnataka",
             "Sadashivanagar", '["Women"]', "Subsidized", "₹500–₹1,500/month", 80, 8,
             "080-2238-0092", "https://wcd.kar.nic.in",
             "Subsidized hostel for working women earning under ₹50,000/month. Meals and security included."),

            ("OBC Pre-Matric Boys Hostel", "Backward Classes Welfare Dept, Karnataka",
             "Rajajinagar", '["OBC"]', "Free", None, 100, 20,
             "080-2334-5500", "https://bcwd.kar.nic.in",
             "Free accommodation for OBC students with meals, study room, and library access."),

            ("Minorities Welfare Girls Hostel", "Dept for Minorities, Karnataka",
             "Shivajinagar", '["Minority","Women"]', "Free", None, 60, 5,
             "080-2286-1122", "https://minorities.kar.nic.in",
             "Free hostel for minority community girls pursuing higher education in Bengaluru."),

            ("Labour Department Workers Hostel", "Dept of Labour, Karnataka",
             "Peenya", '["Labour"]', "Subsidized", "₹300/month", 200, 35,
             "080-2239-7700", "https://labour.kar.nic.in",
             "Heavily subsidized accommodation for registered industrial workers near Peenya."),

            ("SC/ST Post-Matric Girls Hostel", "Dept of Social Welfare, Karnataka",
             "Yeshwantpur", '["SC/ST","Women"]', "Free", None, 90, 10,
             "080-2347-1200", "https://sw.kar.nic.in",
             "Free hostel for SC/ST girls enrolled in degree, diploma or ITI courses."),

            ("Valmiki Tribal Development Hostel", "Tribal Welfare Dept, Karnataka",
             "Majestic", '["SC/ST"]', "Free", None, 75, 12,
             "080-2220-9900", "https://tribal.kar.nic.in",
             "Dedicated hostel for tribal community students with coaching support and career guidance."),

            ("BBMP Working Men's Hostel", "BBMP, Bengaluru",
             "Multiple locations", '["Labour","OBC"]', "Subsidized", "₹800/month", 350, 50,
             "1800-425-0066", "https://bbmp.gov.in",
             "Municipal hostel across 6 zones. Ideal for migrant workers and daily wage earners."),
        ]
        gc = 0
        for row in govt_data:
            name = row[0]
            existing = conn.execute("SELECT id FROM govt_hostels WHERE name=?", (name,)).fetchone()
            if not existing:
                conn.execute(
                    """INSERT INTO govt_hostels
                       (id,name,organisation,area,eligibility,cost_type,cost_amount,
                        total_seats,avail_seats,contact,apply_url,description)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (str(uuid.uuid4()),) + row
                )
                gc += 1
        print(f"  [OK] {gc} govt hostels")

        # ── Area Guides ────────────────────────────────────────────
        area_data = [
            ("Koramangala","⚡","IT and startup hub with excellent restaurants and cafes.",
             '["Startups","Cafés","Nightlife","IT Hub"]',4.2,"High",4.0,"Good",7000,20000,
             '["Wipro","Infosys","Dell"]','["Christ University","St. Josephs"]'),
            ("Whitefield","💻","ITPL hub with modern amenities and malls.",
             '["IT Park","Metro","Malls"]',4.3,"High",3.8,"Good",8000,22000,
             '["ITPL","EPIP Zone","RMZ Infinity"]','["IIMB","Acharya Institute"]'),
            ("HSR Layout","🌟","Planned, premium residential area. Safe and green.",
             '["Premium","Green","Safe"]',4.7,"Very High",3.9,"Good",8000,18000,
             '["Salarpuria","Prestige Tech Park"]','["IIM Bangalore"]'),
            ("Indiranagar","🎵","Trendy area loved by young professionals.",
             '["Trendy","Metro","Pubs","Restaurants"]',4.1,"High",4.5,"Excellent",9000,25000,
             '["Embassy Golf Links","Bagmane Tech Park"]','["St. Johns Medical College"]'),
            ("Marathahalli","🛣️","Well-connected corridor between IT zones.",
             '["Budget","Connectivity","Tech","ORR"]',3.5,"Medium",3.8,"Good",5500,12000,
             '["RMZ Ecospace","Prestige Shantiniketan"]','["RVCE","Jain University"]'),
            ("Electronic City","🏭","Largest IT SEZ. Budget-friendly but far from city.",
             '["IT Park","Budget","Far","SEZ"]',3.4,"Medium",3.0,"Fair",4500,10000,
             '["Infosys","Wipro","HCL","TCS"]','["BMS College of Engineering"]'),
            ("BTM Layout","🧑‍🎓","Budget-friendly student hub with good bus connectivity.",
             '["Students","Budget","Busy"]',3.3,"Medium",4.0,"Good",4000,9000,
             '["Salarpuria Softzone"]','["Vivekananda College"]'),
            ("Jayanagar","🏛️","Old Bengaluru charm. Peaceful, residential, great food.",
             '["Peaceful","Families","Food","Old Bengaluru"]',4.8,"Very High",4.0,"Good",7000,18000,
             '["National Games Village"]','["NIMHANS","Seshadripuram College"]'),
            ("Hebbal","✈️","Strategic north Bengaluru near Manyata Tech Park.",
             '["Airport","Tech Park","Lake","North"]',4.0,"High",3.9,"Good",6000,14000,
             '["Manyata Tech Park","Kirloskar Business Park"]','["PESIT","Atria Institute"]'),
            ("Bannerghatta Road","🌿","Green corridor near JP Nagar and national park.",
             '["Green","Quiet","Premium","South"]',4.2,"High",3.0,"Fair",6500,16000,
             '["Global Village Tech Park"]','["BMS College","Vijaya College"]'),
            ("Rajajinagar","🏡","Well-established residential area with metro connectivity.",
             '["Residential","Old Blr","Metro","West"]',4.3,"High",4.5,"Excellent",5000,12000,
             '["Peenya Industrial Area"]','["RV College","RVCE"]'),
            ("Yelahanka","🌳","Upcoming north suburb with peaceful surroundings.",
             '["Upcoming","Airport","Peaceful","Suburb"]',4.1,"High",2.8,"Fair",4000,9000,
             '["Aerospace SEZ"]','["CMRIT","Sambhram Academy"]'),
        ]
        ac = 0
        for row in area_data:
            name = row[0]
            existing = conn.execute("SELECT id FROM area_guides WHERE name=?", (name,)).fetchone()
            if not existing:
                conn.execute(
                    """INSERT INTO area_guides
                       (id,name,emoji,description,tags,safety_score,safety_label,
                        transit_score,transit_label,avg_price_min,avg_price_max,
                        nearby_tech_parks,nearby_colleges)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (str(uuid.uuid4()),) + row
                )
                ac += 1
        print(f"  [OK] {ac} area guides")

    print("\n[OK] Seed complete!\n")
    print("--- Test Credentials -------------------------")
    print("  Admin:  admin@stayfinder.in  /  Admin@123")
    print("  Owner:  ramesh@owner.com     /  Owner@123")
    print("  User:   test@user.com        /  Test@123")
    print("---------------------------------------------\n")


if __name__ == "__main__":
    seed()
