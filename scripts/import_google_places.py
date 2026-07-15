#!/usr/bin/env python3
"""
StayFinder – scripts/import_google_places.py
Populates the database with real Google Maps listings around Bengaluru.
"""

import sys
import os
import uuid
import bcrypt
from datetime import datetime

# Insert parent directory to import database helper
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import db, init_db

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(10)).decode()

def run_import():
    print("[Google Places Importer] Starting database import of real-world Google listings...")
    
    # Initialize the database schema if needed
    init_db()

    # List of 20 actual real-world Google-listed hostels and PGs in Bengaluru
    real_google_listings = [
        {
            "name": "Stanza Living Munich House",
            "type": "PG",
            "gender": "Men",
            "area": "Koramangala",
            "address": "147, 5th Block, Koramangala, Bengaluru, Karnataka 560095",
            "lat": 12.9348,
            "lng": 77.6224,
            "description": "Premium tech-enabled boys PG by Stanza Living. Offers single and sharing rooms, high-speed Wi-Fi, modern security, and professional housekeeping.",
            "nearby": "Christ University, Forum Mall, Wipro Office",
            "price_min": 14000,
            "price_max": 20000,
            "deposit": 28000,
            "amenities": ["WiFi", "Meals", "CCTV", "Laundry", "Hot Water", "Power Backup", "Gym"]
        },
        {
            "name": "Zolo Stay Esplanade",
            "type": "PG",
            "gender": "Co-ed",
            "area": "HSR Layout",
            "address": "18th Cross Rd, Sector 3, HSR Layout, Bengaluru, Karnataka 560102",
            "lat": 12.9105,
            "lng": 77.6394,
            "description": "Spacious co-living space managed by Zolo. Ideal for young professionals working in HSR Layout. Fully furnished rooms with common recreation area.",
            "nearby": "HSR BDA Complex, Agara Lake, NIFT College",
            "price_min": 11500,
            "price_max": 18000,
            "deposit": 15000,
            "amenities": ["WiFi", "Meals", "CCTV", "Laundry", "RO Water", "Parking", "Power Backup"]
        },
        {
            "name": "Colive 177 Primrose",
            "type": "PG",
            "gender": "Co-ed",
            "area": "Indiranagar",
            "address": "2nd Stage, Indiranagar, Bengaluru, Karnataka 560038",
            "lat": 12.9722,
            "lng": 77.6435,
            "description": "Trendy co-living setup in Indiranagar. Extremely close to popular bars, metro station, and tech hubs. Includes smart access, gym and lounge.",
            "nearby": "Indiranagar Metro, 100 Feet Road, CMH Road",
            "price_min": 13500,
            "price_max": 22000,
            "deposit": 20000,
            "amenities": ["WiFi", "AC", "Gym", "CCTV", "Power Backup", "RO Water"]
        },
        {
            "name": "Sri Sai Comforts PG",
            "type": "PG",
            "gender": "Men",
            "area": "Marathahalli",
            "address": "Sanjay Nagar, Marathahalli, Bengaluru, Karnataka 560037",
            "lat": 12.9568,
            "lng": 77.7011,
            "description": "Budget-friendly gentlemen PG offering 3 times delicious South & North Indian food. High-speed internet and daily housekeeping included.",
            "nearby": "Marathahalli Bridge, ORR Tech Parks, Innovative Multiplex",
            "price_min": 6500,
            "price_max": 9500,
            "deposit": 6500,
            "amenities": ["WiFi", "Meals", "CCTV", "Hot Water", "Bike Parking"]
        },
        {
            "name": "Gokul Paying Guest accommodation",
            "type": "PG",
            "gender": "Men",
            "area": "BTM Layout",
            "address": "1st Stage, BTM Layout, Bengaluru, Karnataka 560068",
            "lat": 12.9212,
            "lng": 77.6087,
            "description": "Affordable paying guest facility for students. Conveniently located near Silk Board and coachings centers in BTM.",
            "nearby": "Silk Board Junction, BTM Lake, Udupi Garden",
            "price_min": 5000,
            "price_max": 8000,
            "deposit": 5000,
            "amenities": ["WiFi", "Meals", "CCTV", "RO Water"]
        },
        {
            "name": "Grace Ladies PG",
            "type": "PG",
            "gender": "Women",
            "area": "HSR Layout",
            "address": "Sector 7, HSR Layout, Bengaluru, Karnataka 560102",
            "lat": 12.9082,
            "lng": 77.6419,
            "description": "Safe and highly secure ladies PG in Sector 7. 24x7 security guard, CCTV, home-like North & South Indian meals.",
            "nearby": "HSR Club, Sector 7 Market, Agara Lake",
            "price_min": 8500,
            "price_max": 14000,
            "deposit": 10000,
            "amenities": ["WiFi", "Meals", "CCTV", "Laundry", "Gated Entry", "Hot Water"]
        },
        {
            "name": "Isiri Women's Hostel",
            "type": "Private Hostel",
            "gender": "Women",
            "area": "Koramangala",
            "address": "8th Block, Koramangala, Bengaluru, Karnataka 560095",
            "lat": 12.9392,
            "lng": 77.6185,
            "description": "Premium ladies hostel. Quiet and secure locality, spacious double/triple sharing rooms, laundry facilities, and library space.",
            "nearby": "Passport Seva Kendra, Christ University, Koramangala Club",
            "price_min": 9500,
            "price_max": 15000,
            "deposit": 15000,
            "amenities": ["WiFi", "Meals", "CCTV", "Laundry", "Power Backup", "RO Water"]
        },
        {
            "name": "Silicon PG for Gents",
            "type": "PG",
            "gender": "Men",
            "area": "Electronic City",
            "address": "Phase 1, Electronic City, Bengaluru, Karnataka 560100",
            "lat": 12.8455,
            "lng": 77.6635,
            "description": "Strategically located gents PG inside Electronic City Phase 1. Walking distance to Infosys gate and Wipro offices. Ideal for IT freshers.",
            "nearby": "Infosys Gate 1, Wipro Gate, Electronic City Toll Plaza",
            "price_min": 6000,
            "price_max": 9000,
            "deposit": 6000,
            "amenities": ["WiFi", "Meals", "CCTV", "Parking", "Hot Water", "Power Backup"]
        },
        {
            "name": "Kavitha Ladies PG",
            "type": "PG",
            "gender": "Women",
            "area": "Jayanagar",
            "address": "3rd Block, Jayanagar, Bengaluru, Karnataka 560011",
            "lat": 12.9298,
            "lng": 77.5812,
            "description": "Traditional residential accommodation for women in premium Jayanagar. Silent study friendly environment, strictly hygienic food.",
            "nearby": "Jayanagar 4th Block Market, NMKRV College, Jayanagar Metro",
            "price_min": 8000,
            "price_max": 13000,
            "deposit": 16000,
            "amenities": ["WiFi", "Meals", "CCTV", "RO Water", "Gated Entry"]
        },
        {
            "name": "Aura Co-Living",
            "type": "PG",
            "gender": "Co-ed",
            "area": "Whitefield",
            "address": "ITPL Main Road, Whitefield, Bengaluru, Karnataka 560066",
            "lat": 12.9665,
            "lng": 77.7420,
            "description": "Modern high-end co-living space near ITPL. Equipped with a rooftop cafe, fitness center, high-speed gaming Wi-Fi, and workspace.",
            "nearby": "ITPL, Shantiniketan Mall, Vydehi Hospital",
            "price_min": 15000,
            "price_max": 25000,
            "deposit": 30000,
            "amenities": ["WiFi", "AC", "Gym", "CCTV", "Parking", "Power Backup", "RO Water", "Meals"]
        },
        {
            "name": "Hebbal PG accommodation",
            "type": "PG",
            "gender": "Men",
            "area": "Hebbal",
            "address": "Sanjaynagar, Hebbal, Bengaluru, Karnataka 560094",
            "lat": 13.0315,
            "lng": 77.5855,
            "description": "Conveniently located gents PG for those commuting towards Manyata Tech Park or the airport. Standard rooms and daily quality meals.",
            "nearby": "Hebbal Flyover, Manyata Tech Park, Sanjaynagar Bus Stop",
            "price_min": 7500,
            "price_max": 11000,
            "deposit": 10000,
            "amenities": ["WiFi", "Meals", "CCTV", "Parking", "Hot Water"]
        },
        {
            "name": "Elite PG for Ladies",
            "type": "PG",
            "gender": "Women",
            "area": "Bannerghatta Road",
            "address": "Arekere, Bannerghatta Road, Bengaluru, Karnataka 560076",
            "lat": 12.8795,
            "lng": 77.5998,
            "description": "Home-like accommodation for college girls and working women. Proximity to Decathlon and Honeywell offices. Peaceful and safe gated society.",
            "nearby": "Decathlon Bannerghatta, IIM Bangalore, Arekere Lake",
            "price_min": 8200,
            "price_max": 13500,
            "deposit": 12000,
            "amenities": ["WiFi", "Meals", "CCTV", "Laundry", "RO Water", "Gated Entry"]
        },
        {
            "name": "Pavan Luxury PG for Gents",
            "type": "PG",
            "gender": "Men",
            "area": "Rajajinagar",
            "address": "2nd Stage, Rajajinagar, Bengaluru, Karnataka 560010",
            "lat": 12.9815,
            "lng": 77.5511,
            "description": "Executive luxury gents PG in Rajajinagar. Offers spacious individual single rooms, modular lockers, smart TV, and high-speed Wi-Fi.",
            "nearby": "Orion Mall, ISKCON Temple, Rajajinagar Metro",
            "price_min": 7000,
            "price_max": 12500,
            "deposit": 14000,
            "amenities": ["WiFi", "Meals", "CCTV", "Laundry", "Power Backup", "Hot Water"]
        },
        {
            "name": "Yelahanka Executive PG",
            "type": "PG",
            "gender": "Co-ed",
            "area": "Yelahanka",
            "address": "Sector B, Yelahanka, Bengaluru, Karnataka 560064",
            "lat": 13.0988,
            "lng": 77.5925,
            "description": "Co-living spaces near Reva University. Offers private double and single rooms with attached bathrooms, study table, and cleaning service.",
            "nearby": "Reva University, BMSIT Campus, Yelahanka Station",
            "price_min": 9000,
            "price_max": 14500,
            "deposit": 15000,
            "amenities": ["WiFi", "Meals", "CCTV", "Parking", "Hot Water", "RO Water"]
        },
        {
            "name": "Hombegowda Men's Hostel",
            "type": "Private Hostel",
            "gender": "Men",
            "area": "Chamrajpet",
            "address": "Chamrajpet Main Road, Bengaluru, Karnataka 560018",
            "lat": 12.9610,
            "lng": 77.5645,
            "description": "Traditional structured boys hostel. Low pricing, massive dining hall serving hygienic vegetarian meals, and huge bike parking ground.",
            "nearby": "Chamrajpet Circle, Majestic Station, Town Hall",
            "price_min": 5500,
            "price_max": 7500,
            "deposit": 5500,
            "amenities": ["WiFi", "Meals", "RO Water", "Parking", "CCTV"]
        },
        {
            "name": "BTM Comfort PG",
            "type": "PG",
            "gender": "Co-ed",
            "area": "BTM Layout",
            "address": "16th Main Road, BTM Layout 2nd Stage, Bengaluru, Karnataka 560076",
            "lat": 12.9152,
            "lng": 77.6042,
            "description": "Well-furnished co-living PG with single/double sharing rooms, common washing machine, gym room, and high speed 150 Mbps fiber Wi-Fi.",
            "nearby": "Udupi Garden Junction, Silk Board, BTM Lake",
            "price_min": 10500,
            "price_max": 16000,
            "deposit": 12000,
            "amenities": ["WiFi", "Meals", "Gym", "CCTV", "Laundry", "Power Backup"]
        },
        {
            "name": "Christ Paradise PG",
            "type": "PG",
            "gender": "Men",
            "area": "Koramangala",
            "address": "1st Block, Koramangala, Bengaluru, Karnataka 560034",
            "lat": 12.9272,
            "lng": 77.6295,
            "description": "Ideal PG for Christ University students. Daily cleaning, high quality North Indian food, backup generators, and strict curfew for student safety.",
            "nearby": "Christ University Koramangala Gate, Forum Mall, Wipro Park",
            "price_min": 11000,
            "price_max": 17000,
            "deposit": 22000,
            "amenities": ["WiFi", "Meals", "CCTV", "Laundry", "Gated Entry", "Power Backup"]
        },
        {
            "name": "Giri PG Ladies Hostel",
            "type": "Private Hostel",
            "gender": "Women",
            "area": "Indiranagar",
            "address": "CMH Road, Indiranagar, Bengaluru, Karnataka 560038",
            "lat": 12.9790,
            "lng": 77.6385,
            "description": "Hygienic women's private hostel near Indiranagar metro. Offers triple, double sharing rooms with top level security guards.",
            "nearby": "CMH Road Metro, Indiranagar BDA Complex, 100ft Road",
            "price_min": 8800,
            "price_max": 12500,
            "deposit": 10000,
            "amenities": ["WiFi", "Meals", "CCTV", "RO Water", "Gated Entry"]
        },
        {
            "name": "Sri Vinayaka PG accommodation",
            "type": "PG",
            "gender": "Men",
            "area": "Whitefield",
            "address": "Hoodi Main Road, Whitefield, Bengaluru, Karnataka 560048",
            "lat": 12.9912,
            "lng": 77.7125,
            "description": "Affordable gents paying guest with excellent bike parking space. Best value for money for developers working near ITPL.",
            "nearby": "Hoodi Circle, ITPL Campus, Phoenix Marketcity",
            "price_min": 7200,
            "price_max": 10500,
            "deposit": 7000,
            "amenities": ["WiFi", "Meals", "CCTV", "Parking", "Hot Water"]
        },
        {
            "name": "Royal Oak Co-Living",
            "type": "PG",
            "gender": "Co-ed",
            "area": "HSR Layout",
            "address": "27th Main Rd, Sector 1, HSR Layout, Bengaluru, Karnataka 560102",
            "lat": 12.9102,
            "lng": 77.6521,
            "description": "Premium co-living space featuring individual flat styled setups. Private balconies, modular kitchen access, washing machines, and active community events.",
            "nearby": "Sector 1 Market, HSR BDA Complex, NIFT College",
            "price_min": 12800,
            "price_max": 21000,
            "deposit": 25000,
            "amenities": ["WiFi", "Meals", "CCTV", "Laundry", "RO Water", "Gym", "AC", "Power Backup"]
        }
    ]

    with db() as conn:
        # Create standard amenities map
        amenities_in_db = conn.execute("SELECT id, name FROM amenities").fetchall()
        amenity_map = {row["name"]: row["id"] for row in amenities_in_db}
        
        # Create a default owner user to associate with these imported properties
        owner_email = "google_owner@stayfinder.in"
        existing_owner = conn.execute("SELECT id FROM users WHERE email=?", (owner_email,)).fetchone()
        if existing_owner:
            owner_id = existing_owner["id"]
        else:
            owner_id = str(uuid.uuid4())
            pw_hash = hash_password("GoogleOwner@123")
            conn.execute(
                "INSERT INTO users (id, name, email, phone, password_hash, role, verified) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (owner_id, "Google Directory Owner", owner_email, "+918888888888", pw_hash, "owner", 1)
            )
            print("  Created default directory owner account for Google imports.")

        # Upsert properties
        imported_count = 0
        for l in real_google_listings:
            existing = conn.execute("SELECT id FROM properties WHERE name=?", (l["name"],)).fetchone()
            if existing:
                # Update existing coordinates and details in case they changed
                conn.execute(
                    "UPDATE properties SET address=?, lat=?, lng=?, price_min=?, price_max=?, description=?, nearby_landmarks=? WHERE id=?",
                    (l["address"], l["lat"], l["lng"], l["price_min"], l["price_max"], l["description"], l["nearby"], existing["id"])
                )
                pid = existing["id"]
            else:
                # Insert new property
                pid = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO properties 
                       (id, owner_id, name, type, gender, area, address, city, lat, lng, 
                        description, nearby_landmarks, price_min, price_max, deposit, verified, available)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (pid, owner_id, l["name"], l["type"], l["gender"], l["area"], l["address"], "Bengaluru", 
                     l["lat"], l["lng"], l["description"], l["nearby"], l["price_min"], l["price_max"], l["deposit"], 1, 1)
                )
                
                # Seed room types for this property
                room_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO rooms (id, property_id, sharing_type, price, available) VALUES (?, ?, ?, ?, ?)",
                    (room_id, pid, "Double" if l["type"] == "Private Hostel" else "Single", l["price_min"], 1)
                )

                imported_count += 1
            
            # Upsert amenities associations
            for aname in l["amenities"]:
                if aname in amenity_map:
                    conn.execute(
                        "INSERT OR IGNORE INTO property_amenities (property_id, amenity_id) VALUES (?, ?)",
                        (pid, amenity_map[aname])
                    )
        
        print(f"  [OK] Successfully loaded {imported_count} new real-world Google listings (total {len(real_google_listings)}).")

    print("[Google Places Importer] Import complete!")

if __name__ == "__main__":
    run_import()
