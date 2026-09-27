"""
CIVI-RESQ Observed Waterlogging Events
-----------------------------------------
Real, independently reported waterlogging/flood locations for Guntur & Vijayawada,
sourced from news coverage of the September 2024 Vijayawada floods (one of the
worst flood events in the region's recorded history) and municipal reports on
chronic drainage issues. This is what the mentor's pitch means by "observed
waterlogging locations" -- as distinct from the synthetic training labels used
to train the ML models.

IMPORTANT METHODOLOGICAL NOTE (be upfront about this in your report/defense):
- These are REAL reported events with REAL locations, but they are not a
  systematic municipal flood-incident database (no such public dataset exists
  for these cities at zone/ward level). They are drawn from credible news
  reporting of a major, well-documented flood event plus one municipal report.
- Sample size is small (11 zones). This is enough for a face-validity /
  independent-corroboration check, NOT a statistically powered validation.
  Be honest about this distinction if asked.

Sources:
  [1] Wikipedia: "2024 Vijayawada floods" (Aug 31 - Sep 9, 2024; 35 deaths,
      ~270,000 people affected; triggered by Budameru Rivulet breach)
  [2] ETV Bharat, Sep 1 2024: "10 Dead in Andhra Pradesh as Heavy Rains Cause
      Landslides, Waterlogging in Vijayawada, Guntur, Other Areas"
  [3] countryandpolitics.in, Aug 31 2024: "Heavy rain in Vijayawada and Guntur..
      Roads facing ponds"
  [4] suryaa.com: "Guntur Municipal Corporation Begins to Tackle Issues" --
      GMC desilting operation in Old Guntur due to chronically clogged drains
"""
import json

OBSERVED_EVENTS = [
    # Matches existing zones in demo_zones.json (zone_code references)
    {
        "zone_code": "VIJ-021", "zone_name": "Bhavanipuram",
        "event_date": "2024-09-01", "event_type": "flood",
        "description": "Reported flooded during Sept 2024 Vijayawada floods.",
        "source": "ETV Bharat, Sep 1 2024",
    },
    {
        "zone_code": "VIJ-025", "zone_name": "Auto Nagar",
        "event_date": "2024-08-31", "event_type": "waterlogging",
        "description": "Areas surrounding Autonagar flooded during heavy rain.",
        "source": "countryandpolitics.in, Aug 31 2024",
    },
    {
        "zone_code": "VIJ-026", "zone_name": "Ajit Singh Nagar",
        "event_date": "2024-09-08", "event_type": "flood",
        "description": "Flood water inundation photographed/reported; area near "
                        "Vijayawada North mandal HQ, among worst-hit in the 2024 floods.",
        "source": "Wikipedia, '2024 Vijayawada floods'",
    },
    {
        "zone_code": "GUN-001", "zone_name": "Old Guntur / One Town",
        "event_date": "2024-recurring", "event_type": "chronic_drainage_failure",
        "description": "Chronically clogged open drains; GMC ran a dedicated "
                        "desilting operation across Old Guntur.",
        "source": "suryaa.com, GMC drainage report",
    },
    # New zones -- real reported locations not previously in the demo dataset
    {
        "zone_code": "VIJ-027", "zone_name": "Vidyadharapuram",
        "event_date": "2024-08-31", "event_type": "waterlogging",
        "description": "Roads turned into ponds; severe waterlogged-road problems reported.",
        "source": "countryandpolitics.in, Aug 31 2024",
    },
    {
        "zone_code": "VIJ-028", "zone_name": "Satyanarayanapuram",
        "event_date": "2024-09-01", "event_type": "flood",
        "description": "Reported flooded during Sept 2024 Vijayawada floods.",
        "source": "ETV Bharat, Sep 1 2024",
    },
    {
        "zone_code": "VIJ-029", "zone_name": "RR Nagar (RR Peta)",
        "event_date": "2024-08-31", "event_type": "waterlogging",
        "description": "Severe waterlogged-road problems during heavy rain.",
        "source": "countryandpolitics.in, Aug 31 2024",
    },
    {
        "zone_code": "VIJ-030", "zone_name": "Krishna Lanka",
        "event_date": "2024-09-02", "event_type": "flood",
        "description": "Residents evacuated as water levels near retaining wall rose to "
                        "historic highs during Prakasam Barrage high-inflow event.",
        "source": "All India Radio (newsonair.gov.in), Sep 2 2024",
    },
    {
        "zone_code": "VIJ-031", "zone_name": "Tadepalli",
        "event_date": "2024-09-02", "event_type": "flood",
        "description": "Residents near the Krishna riverbank evacuated during "
                        "historic-high water inflow at Prakasam Barrage.",
        "source": "All India Radio (newsonair.gov.in), Sep 2 2024",
    },
    {
        "zone_code": "VIJ-032", "zone_name": "Eluru Road",
        "event_date": "2024-09-01", "event_type": "flood",
        "description": "Reported flooded during Sept 2024 Vijayawada floods.",
        "source": "ETV Bharat, Sep 1 2024",
    },
    {
        "zone_code": "VIJ-033", "zone_name": "Poly Clinic Road",
        "event_date": "2024-09-01", "event_type": "flood",
        "description": "Reported flooded during Sept 2024 Vijayawada floods.",
        "source": "ETV Bharat, Sep 1 2024",
    },
]

# New zone geographic + parameter seeds (real coordinates, mandal-grounded).
# Character profiles reuse the same archetypes as generate_demo_data.py so
# ML predictions remain methodologically consistent with the rest of the dataset.
NEW_ZONE_SEEDS = [
    # (zone_code, name, lat, lng, land_use, character)
    ("VIJ-027", "Vidyadharapuram", 16.5135, 80.6355, "residential", "old_dense_low_drainage"),
    ("VIJ-028", "Satyanarayanapuram", 16.5350, 80.6355, "residential", "old_dense_low_drainage"),
    ("VIJ-029", "RR Nagar (RR Peta)", 16.5280, 80.6320, "mixed", "mid_density"),
    ("VIJ-030", "Krishna Lanka", 16.5080, 80.6170, "residential", "old_dense_low_drainage"),
    ("VIJ-031", "Tadepalli", 16.6033, 80.6208, "residential", "mid_density"),
    ("VIJ-032", "Eluru Road", 16.5120, 80.6330, "commercial", "old_dense_low_drainage"),
    ("VIJ-033", "Poly Clinic Road", 16.5130, 80.6340, "commercial", "old_dense_low_drainage"),
]

if __name__ == "__main__":
    with open("backend/data/observed_waterlogging_events.json", "w") as f:
        json.dump({
            "description": "Real, independently reported waterlogging/flood events "
                            "for Guntur & Vijayawada, used for external validation "
                            "(NOT used in model training).",
            "events": OBSERVED_EVENTS,
        }, f, indent=2)
    print(f"Wrote {len(OBSERVED_EVENTS)} observed events -> "
          f"backend/data/observed_waterlogging_events.json")
