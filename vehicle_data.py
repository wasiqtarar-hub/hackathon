import re
from datetime import date
from functools import lru_cache
from urllib.parse import quote

import requests


VPIC_BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles"
REQUEST_TIMEOUT = 20
YEAR_FLOOR = 1996
SPEC_DISPLAY_ORDER = [
    ("Model", "Variant"),
    ("OL", "Overall Length (cm)"),
    ("OW", "Overall Width (cm)"),
    ("OH", "Overall Height (cm)"),
    ("WB", "Wheelbase (cm)"),
    ("CW", "Curb Weight (kg)"),
    ("WD", "Weight Distribution"),
    ("TWF", "Front Track Width (cm)"),
    ("TWR", "Rear Track Width (cm)"),
    ("A", "Front Bumper to Windshield Base (cm)"),
    ("B", "Rear Body Section Length (cm)"),
    ("C", "Max Side Glass Height (cm)"),
    ("D", "Side Glass to Rocker Panel (cm)"),
    ("E", "Roof or Rail Width (cm)"),
    ("F", "Front Overhang (cm)"),
    ("G", "Rear Overhang (cm)"),
]


def build_years():
    return list(range(date.today().year, YEAR_FLOOR - 1, -1))


def normalize_text(value):
    return re.sub(r"[^A-Z0-9]+", " ", str(value).upper()).strip()


def fetch_vpic_json(endpoint, params=None):
    response = requests.get(
        f"{VPIC_BASE_URL}{endpoint}",
        params=params or {},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def specs_list_to_dict(specs):
    spec_map = {}
    for item in specs:
        name = (item.get("Name") or "").strip()
        value = (item.get("Value") or "").strip()
        if name and value:
            spec_map[name] = value
    return spec_map


def build_display_specs(spec_map):
    display_specs = []
    for raw_key, label in SPEC_DISPLAY_ORDER:
        value = spec_map.get(raw_key)
        if value:
            display_specs.append(
                {
                    "key": raw_key,
                    "label": label,
                    "value": value,
                }
            )
    return display_specs


def build_fallback_profile(year, make, model, variant=None):
    variant_name = variant or f"{model} Standard"
    spec_map = {
        "Model": variant_name,
        "Year": str(year),
        "Make": make,
        "BaseModel": model,
    }
    return {
        "year": year,
        "make": make,
        "model": model,
        "variant": variant_name,
        "has_detailed_specs": False,
        "source": "Fallback profile generated because detailed vPIC specs were unavailable.",
        "raw_specs": spec_map,
        "display_specs": [{"key": "Model", "label": "Variant", "value": variant_name}],
    }


def build_car_profile(year, make, model, spec_map):
    variant_name = spec_map.get("Model") or f"{model} Standard"
    return {
        "year": year,
        "make": make,
        "model": model,
        "variant": variant_name,
        "has_detailed_specs": True,
        "source": "NHTSA vPIC Canadian Vehicle Specifications",
        "raw_specs": spec_map,
        "display_specs": build_display_specs(spec_map),
    }


@lru_cache(maxsize=1)
def get_makes():
    data = fetch_vpic_json("/GetMakesForVehicleType/car", params={"format": "json"})
    makes = {}
    for item in data.get("Results", []):
        name = (item.get("MakeName") or "").strip()
        make_id = item.get("MakeId")
        if name:
            makes[name] = {"id": make_id, "name": name}
    return sorted(makes.values(), key=lambda item: item["name"])


@lru_cache(maxsize=512)
def get_models(year, make):
    data = fetch_vpic_json(
        f"/GetModelsForMakeYear/make/{quote(make)}/modelyear/{int(year)}",
        params={"format": "json"},
    )
    models = {}
    for item in data.get("Results", []):
        name = (item.get("Model_Name") or "").strip()
        model_id = item.get("Model_ID")
        if name:
            models[name] = {"id": model_id, "name": name}
    return sorted(models.values(), key=lambda item: item["name"])


@lru_cache(maxsize=512)
def get_canadian_specs(year, make, model=""):
    params = {
        "year": int(year),
        "make": make,
        "format": "json",
    }
    if model:
        params["model"] = model
    data = fetch_vpic_json("/GetCanadianVehicleSpecifications/", params=params)
    return data.get("Results", [])


def get_variant_profiles(year, make, model):
    candidate_results = get_canadian_specs(year, make, model)
    if not candidate_results:
        broader_results = get_canadian_specs(year, make, "")
        model_key = normalize_text(model)
        candidate_results = [
            item
            for item in broader_results
            if model_key
            and normalize_text(specs_list_to_dict(item.get("Specs", [])).get("Model", "")).startswith(model_key)
        ]

    profiles = []
    seen = set()
    for item in candidate_results:
        spec_map = specs_list_to_dict(item.get("Specs", []))
        variant_name = spec_map.get("Model")
        if not variant_name:
            continue
        normalized_variant = normalize_text(variant_name)
        if normalized_variant in seen:
            continue
        seen.add(normalized_variant)
        profiles.append(build_car_profile(year, make, model, spec_map))

    if not profiles:
        profiles = [build_fallback_profile(year, make, model)]

    return profiles


def get_selected_profile(year, make, model, variant):
    profiles = get_variant_profiles(year, make, model)
    if not variant:
        return profiles[0]

    normalized_variant = normalize_text(variant)
    for profile in profiles:
        if normalize_text(profile["variant"]) == normalized_variant:
            return profile

    return build_fallback_profile(year, make, model, variant=variant)
