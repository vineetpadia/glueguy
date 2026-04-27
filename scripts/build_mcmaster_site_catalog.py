#!/usr/bin/env python3
"""Build site-ready Glueguy catalog artifacts from the raw McMaster crawl."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "mcmaster-glues.json"
DETAILS_PATH = ROOT / "data" / "mcmaster-product-details.json"
TDS_PATH = ROOT / "data" / "mcmaster-tds-links.json"
JS_OUTPUT = ROOT / "data" / "mcmaster-site-catalog.js"
SUMMARY_OUTPUT = ROOT / "data" / "mcmaster-site-summary.json"


CANONICAL_MAKERS = {
    "Loctite": ["loctite"],
    "3M Scotch-Weld": ["3m scotch-weld", "scotch-weld"],
    "3M": ["3m"],
    "Permabond": ["permabond"],
    "Devcon": ["devcon"],
    "J-B Weld": ["j-b weld", "jb weld", "kwikweld"],
    "Gorilla": ["gorilla"],
    "Dow Corning": ["dow corning"],
    "Momentive": ["momentive", "ge silicone"],
    "Sika": ["sika", "sikaflex"],
    "Plexus": ["plexus"],
    "LORD": ["lord"],
    "SciGrip": ["scigrip", "weld-on"],
    "Elmer's": ["elmer"],
    "Liquid Nails": ["liquid nails"],
    "Infinity Bond": ["infinity bond"],
    "Vibra-Tite": ["vibra-tite"],
    "Permatex": ["permatex"],
    "Pliobond": ["pliobond"],
}

SELECTOR_CATEGORY_HINTS = (
    "instant-bond",
    "structural adhesive",
    "threadlocker",
    "retaining compound",
    "contact adhesive",
    "hot glue",
    "construction adhesive",
    "sealant",
    "gasket maker",
    "potting compound",
    "conductive adhesive",
    "electrically insulating adhesive",
    "anchoring adhesive",
)

SKIP_SELECTOR_HINTS = (
    "tape",
    "rope",
    "strip",
    "patch",
    "dispens",
    "nozzle",
    "plunger",
    "brush",
    "beads",
    "gun ",
    "holder",
)

PROFILE_CATEGORY_KEYWORDS = {
    "anaerobicThreadlocker": ("threadlocker",),
    "anaerobicRetainer": ("retaining compound",),
    "hotMelt": ("hot glue", "glue stick"),
    "constructionAdhesive": ("construction adhesive", "anchoring adhesive", "concrete bonding construction adhesive"),
    "contactCement": ("contact adhesive", "cement for abrasive grains"),
    "rtvSilicone": ("gasket maker", "silicone sealant"),
    "polyurethaneSealant": ("structural sealant", "sealants", "roof joint sealant", "concrete joint sealant", "hvac sealant"),
    "thermalEpoxy": ("potting compound", "conductive adhesive", "electrically insulating adhesive"),
}

PROFILE_APPLICATION_TAGS = {
    "toughenedEpoxy": ["structural-bonding"],
    "flexibleEpoxy": ["structural-bonding"],
    "clearEpoxy": ["structural-bonding"],
    "structuralAcrylic": ["structural-bonding"],
    "structuralPolyurethane": ["structural-bonding"],
    "mmaPlasticWelder": ["plastic-repair", "structural-bonding"],
    "thinCA": ["instant-bonding"],
    "gelCA": ["instant-bonding"],
    "hybridCA": ["instant-bonding", "plastic-repair"],
    "uvOptical": ["optical-bonding"],
    "uvAcrylate": ["optical-bonding"],
    "rtvSilicone": ["sealing-gasketing"],
    "siliconeRubberAdhesive": ["sealing-gasketing"],
    "polyurethaneSealant": ["sealing-gasketing"],
    "anaerobicThreadlocker": ["threadlocking"],
    "anaerobicRetainer": ["retaining"],
    "foamTape": ["structural-bonding"],
    "contactCement": ["contact-lamination"],
    "pvaWood": ["wood-paper-fabric"],
    "hotMelt": ["hot-melt-assembly"],
    "sprayAdhesive": ["spray-mounting"],
    "thermalEpoxy": ["potting-thermal"],
    "solventAcrylic": ["solvent-welding"],
    "solventPVC": ["solvent-welding"],
    "constructionAdhesive": ["construction"],
    "industrialClear": ["general-repair"],
    "fabricAdhesive": ["wood-paper-fabric"],
    "craftPva": ["wood-paper-fabric"],
}

MATERIAL_TOKEN_MAP = {
    "metal": {"aluminum": 8.0, "steel": 8.0, "copper": 7.0},
    "aluminum": {"aluminum": 10.0},
    "steel": {"steel": 10.0},
    "stainless steel": {"steel": 9.0},
    "copper": {"copper": 10.0},
    "glass": {"glass": 10.0},
    "ceramic": {"ceramic": 10.0},
    "wood": {"wood": 10.0, "mdf": 8.5},
    "paper": {"paper": 10.0},
    "cardboard": {"paper": 9.0},
    "fabric": {"fabric": 10.0},
    "leather": {"leather": 10.0},
    "plastic": {
        "abs": 7.0,
        "pvc": 7.0,
        "acrylic": 7.0,
        "polycarbonate": 7.0,
        "petg": 7.0,
    },
    "abs": {"abs": 10.0},
    "pvc": {"pvc": 10.0},
    "acrylic": {"acrylic": 10.0},
    "polycarbonate": {"polycarbonate": 10.0},
    "petg": {"petg": 10.0},
    "rubber": {"rubber": 10.0},
    "silicone": {"siliconeRubber": 9.5},
    "composite": {"carbonFiber": 8.5},
    "carbon fiber": {"carbonFiber": 10.0},
    "fiberglass": {"carbonFiber": 7.5},
    "frp": {"carbonFiber": 7.5},
    "smc": {"carbonFiber": 7.5},
    "concrete": {"concrete": 10.0},
    "masonry": {"concrete": 9.5},
    "cement": {"concrete": 9.0},
    "brick": {"concrete": 8.5},
    "stone": {"concrete": 8.0},
    "hard-to-bond materials": {"hdpe": 8.0},
    "polyethylene": {"hdpe": 9.0},
    "polypropylene": {"hdpe": 9.0},
    "garolite": {"fr4": 8.0},
    "fr-4": {"fr4": 10.0},
    "circuit board": {"fr4": 9.0},
}

PSI_TO_MPA = 0.00689476
F_TO_C_SCALE = 5 / 9


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def clean_brand_text(value: str | None) -> str:
    text = normalize_space(value)
    text = text.replace("®", "").replace("™", "").replace("©", "")
    return normalize_space(text)


def first_number(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"-?\d+(?:,\d{3})*(?:\.\d+)?", value)
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def f_to_c(value_f: float | None) -> int | None:
    if value_f is None:
        return None
    return round((value_f - 32) * F_TO_C_SCALE)


def psi_to_mpa(value_psi: float | None) -> float | None:
    if value_psi is None:
        return None
    return round(value_psi * PSI_TO_MPA, 1)


def inch_to_mm(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value * 25.4, 2)


def parse_gap_mm(raw: str | None) -> float | None:
    if not raw:
        return None
    match = re.search(r'(\d+(?:\.\d+)?)"', raw)
    if match:
        return inch_to_mm(float(match.group(1)))
    return None


def parse_minutes(offer: dict) -> tuple[float | None, float | None]:
    fields = offer.get("fields", {})
    if fields.get("begins_to_harden_min"):
        value = first_number(fields["begins_to_harden_min"])
        return value, value
    if fields.get("begins_to_harden_sec"):
        value = first_number(fields["begins_to_harden_sec"])
        if value is not None:
            minutes = round(value / 60, 2)
            return minutes, minutes
    if fields.get("begins_to_harden"):
        text = fields["begins_to_harden"].lower()
        value = first_number(text)
        if value is not None:
            minutes = value / 60 if "sec" in text else value
            return round(minutes, 2), round(minutes, 2)
    return None, None


def choose_representative_offer(offers: list[dict]) -> dict:
    return sorted(
        offers,
        key=lambda offer: (
            offer.get("price_usd") is None,
            offer.get("package_ml") is None,
            offer.get("package_ml") or 10**9,
            offer.get("price_usd") or 10**9,
        ),
    )[0]


def load_detail_lookup() -> tuple[dict[str, dict], dict]:
    if not DETAILS_PATH.exists():
        return {}, {}
    payload = json.loads(DETAILS_PATH.read_text())
    return payload.get("detailsByPartNo", {}), payload.get("stats", {})


def load_tds_lookup() -> tuple[dict[str, dict], dict]:
    if not TDS_PATH.exists():
        return {}, {}
    payload = json.loads(TDS_PATH.read_text())
    return payload.get("entriesByFamilyKey", {}), payload.get("stats", {})


def offer_part_no(offer: dict) -> str | None:
    return normalize_space(offer.get("fields", {}).get("mcmaster_part_no")) or None


def offer_direct_url(offer: dict) -> str | None:
    row_links = offer.get("row_links") or []
    for link in row_links:
        href = normalize_space(link.get("href"))
        if href.startswith("https://www.mcmaster.com/"):
            return href
    part_no = offer_part_no(offer)
    if part_no:
        return f"https://www.mcmaster.com/{part_no}/"
    return None


def detail_field(detail: dict | None, key: str) -> str | None:
    if not detail:
        return None
    return normalize_space(detail.get("fields", {}).get(key)) or None


def format_offer_size_text(offer: dict) -> str | None:
    size_value = offer.get("size_value")
    size_unit = offer.get("size_unit")
    if size_value is None or not size_unit:
        return None

    unit_labels = {
        "fl_oz": "fl. oz.",
        "ml": "mL",
        "qt": "qt",
        "pt": "pt",
        "gal": "gal",
    }
    unit_label = unit_labels.get(size_unit)
    if not unit_label:
        return None
    return f"{size_value:g} {unit_label}"


def package_label(package_size: str | None, package_type: str | None) -> str | None:
    parts = [part for part in (package_size, package_type) if part]
    if not parts:
        return None
    return " ".join(parts)


def normalize_detail_clarity(value: str | None) -> str | None:
    text = normalize_space(value).lower()
    if not text:
        return None
    if "optically clear" in text:
        return "optically-clear"
    if any(token in text for token in ("clear", "transparent")):
        return "transparent"
    if "translucent" in text:
        return "translucent"
    if "opaque" in text:
        return "opaque"
    return None


def build_mcmaster_meta(offer: dict, detail: dict | None) -> dict | None:
    part_no = offer_part_no(offer)
    spec_url = (detail or {}).get("url") or offer_direct_url(offer)
    package_size = detail_field(detail, "size") or format_offer_size_text(offer)
    package_type = detail_field(detail, "container_type") or normalize_space(
        offer.get("fields", {}).get("type")
    )
    mix_ratio = detail_field(detail, "mix_ratio") or normalize_space(offer.get("fields", {}).get("mix_ratio"))
    color = detail_field(detail, "color") or normalize_space(offer.get("fields", {}).get("color"))
    consistency = detail_field(detail, "consistency_viscosity") or offer.get("consistency")
    for_joining = detail_field(detail, "for_joining") or normalize_space(
        offer.get("fields", {}).get("for_joining")
    )
    peel_strength = detail_field(detail, "peel")
    if not peel_strength:
        raw_peel = normalize_space(offer.get("fields", {}).get("peel_lb_per_in"))
        if raw_peel:
            peel_strength = f"{raw_peel} lb/in"

    meta = {
        "partNo": part_no,
        "packageSize": package_size,
        "packageType": package_type,
        "packageLabel": package_label(package_size, package_type),
        "specUrl": spec_url,
        "coverage": detail_field(detail, "approximate_coverage"),
        "mixRatio": mix_ratio,
        "color": color,
        "peelStrength": peel_strength,
        "consistency": consistency,
        "forJoining": for_joining,
        "forUseOn": detail_field(detail, "for_use_on"),
        "cureType": detail_field(detail, "cure_type") or normalize_space(
            offer.get("fields", {}).get("cure_type")
        ),
        "fullStrength": detail_field(detail, "reaches_full_strength") or normalize_space(
            offer.get("fields", {}).get("reaches_full_strength")
        ),
        "clarity": detail_field(detail, "clarity"),
        "certificate": detail_field(detail, "certificate"),
        "rohs": detail_field(detail, "rohs"),
        "reach": detail_field(detail, "reach"),
    }
    compact = {key: value for key, value in meta.items() if value}
    if part_no:
        compact["sourceLabel"] = f"McMaster {part_no}"
    return compact or None


def choose_primary_category(categories: list[str]) -> str:
    if not categories:
        return "McMaster reference family"

    generic_tokens = {
        "sealants",
        "threadlockers",
        "instant-bond adhesives",
        "retaining compounds",
        "glue",
    }

    ranked = sorted(
        categories,
        key=lambda item: (
            item.lower() in generic_tokens,
            len(item.split()),
            item,
        ),
    )
    return ranked[0]


def canonical_maker(raw_maker: str | None, family_name: str) -> str | None:
    candidates = [clean_brand_text(raw_maker), clean_brand_text(family_name)]
    for candidate in candidates:
        lowered = candidate.lower()
        for canonical, aliases in CANONICAL_MAKERS.items():
            if any(alias in lowered for alias in aliases):
                return canonical
    for candidate in candidates:
        if not candidate or re.fullmatch(r"[0-9]{3,}[A-Z]?[0-9A-Z]*|__", candidate):
            continue
        if re.search(r"[A-Za-z]", candidate):
            return candidate
    return None


def clean_family_name(family_name: str | None, maker: str | None, detail: dict | None = None) -> str:
    detail_model_name = clean_brand_text(detail_field(detail, "manufacturer_model_name"))
    detail_model_number = clean_brand_text(detail_field(detail, "manufacturer_model_number"))
    detail_name = clean_brand_text((detail or {}).get("name"))

    if detail_model_name or detail_model_number:
        parts: list[str] = []
        if maker:
            parts.append(maker)
        if detail_model_name and (not maker or detail_model_name.lower() not in maker.lower()):
            parts.append(detail_model_name)
        if detail_model_number:
            parts.append(detail_model_number)
        detail_composed = normalize_space(" ".join(parts))
        if detail_composed:
            return detail_composed

    name = clean_brand_text(family_name) or detail_name
    if not name:
        return ""

    name = name.split("Product Detail")[0].strip()
    name = re.sub(r"\s*QuantityEach.*$", "", name)
    name = re.sub(r",\s*\d+(?:\.\d+)?\s*FL\.\s*oz.*$", "", name, flags=re.IGNORECASE)

    model_number_match = re.search(
        r"Model Number ([A-Za-z0-9-]+).*?\.\s*([A-Za-z0-9-]+)$",
        name,
    )
    if model_number_match:
        name = model_number_match.group(2)
    elif "—" in name:
        tail = name.split("—", 1)[1].strip()
        tail_token = tail.split()[-1] if tail else ""
        if re.fullmatch(r"[A-Za-z0-9-]{2,}", tail_token):
            name = tail_token

    if len(name.split()) > 8:
        trailing_code = re.search(r"\b([A-Za-z0-9-]{4,})$", name)
        if trailing_code:
            name = trailing_code.group(1)

    name = name.rstrip(" -—.")

    if maker == "Gorilla" and name.lower() == "gorilla glue gorilla glue":
        return "Gorilla Glue"

    if name == "__":
        return ""

    if maker and name.lower().startswith(maker.lower()):
        return name

    if maker and not name.lower().startswith(maker.lower()):
        return f"{maker} {name}"

    return name


def should_skip_selector_family(name: str, primary_category: str) -> bool:
    lowered = f"{name} {primary_category}".lower()
    if not name or name == "__":
        return True
    if any(token in lowered for token in SKIP_SELECTOR_HINTS):
        return True
    if not any(token in lowered for token in SELECTOR_CATEGORY_HINTS):
        return True
    return False


def infer_profile(family_name: str, maker: str | None, primary_category: str, offer: dict) -> str | None:
    text = " ".join(
        part
        for part in (
            family_name,
            maker or "",
            primary_category,
            " ".join(offer.get("fields", {}).values()),
        )
        if part
    ).lower()

    for profile, keywords in PROFILE_CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            if profile in {"contactCement", "polyurethaneSealant", "thermalEpoxy"}:
                break
            return profile

    if "instant-bond" in text:
        if any(token in text for token in ("light-activated", "uv light", "visible light")):
            return "uvOptical" if "optically clear" in text else "uvAcrylate"
        if any(token in text for token in ("hy4090", "hy 4090", "hy4070", "hy 4070", "3092")):
            return "hybridCA"
        if any(token in text for token in ("gel", "gap-filling", "impact-resistant", "flexible", "low-odor")):
            return "gelCA"
        return "thinCA"

    if "structural adhesive" in text:
        if "urethane" in text:
            return "structuralPolyurethane"
        if any(token in text for token in ("acrylic", "methacrylate", "mma", "plexus")):
            return "structuralAcrylic"
        if "optically clear" in text:
            return "clearEpoxy"
        return "toughenedEpoxy"

    if "contact adhesive" in text or "cement for abrasive grains" in text:
        offer_type = normalize_space(offer.get("fields", {}).get("type", "")).lower()
        if any(token in offer_type for token in ("aerosol", "canister")):
            return "sprayAdhesive"
        return "contactCement"

    if "hot glue" in text or "glue stick" in text:
        return "hotMelt"

    if "construction adhesive" in text or "anchoring adhesive" in text:
        return "constructionAdhesive"

    if any(token in text for token in ("gasket maker", "silicone sealant", "noncorrosive silicone", "rtv")):
        return "rtvSilicone"

    if "sealant" in text:
        if "silicone" in text:
            return "rtvSilicone"
        return "polyurethaneSealant"

    if any(token in text for token in ("potting compound", "conductive adhesive", "electrically insulating adhesive")):
        if any(token in text for token in ("conductive", "silver", "thermal")):
            return "thermalEpoxy"
        if "silicone" in text:
            return "rtvSilicone"
        return "toughenedEpoxy"

    return None


def infer_viscosity_class(offer: dict, primary_category: str, profile: str) -> str | None:
    consistency = normalize_space(offer.get("consistency") or offer.get("fields", {}).get("consistency", "")).lower()
    viscosity = offer.get("viscosity_cp")
    context = f"{primary_category} {consistency}".lower()

    if "wicking" in context:
        return "wicking"
    if "thin" in consistency:
        return "low"
    if "gel" in consistency or "paste" in consistency or "putty" in consistency:
        if viscosity and viscosity > 50000:
            return "very-high"
        return "high"
    if "thick" in consistency:
        if viscosity and viscosity > 10000:
            return "high"
        return "medium"
    if viscosity is not None:
        if viscosity < 30:
            return "wicking"
        if viscosity < 500:
            return "low"
        if viscosity < 5000:
            return "medium"
        if viscosity < 50000:
            return "high"
        return "very-high"
    if profile == "hotMelt":
        return "very-high"
    if profile in {"sprayAdhesive", "thinCA", "anaerobicThreadlocker"}:
        return "low"
    return None


def infer_clarity(family_name: str, primary_category: str, offer: dict) -> str | None:
    text = " ".join(
        part
        for part in (
            family_name,
            primary_category,
            offer.get("fields", {}).get("color", ""),
        )
        if part
    ).lower()

    if "optically clear" in text:
        return "optically-clear"
    if "clear" in text or "translucent" in text:
        return "transparent"
    return None


def infer_thixotropic(offer: dict, primary_category: str) -> bool | None:
    text = " ".join(
        part
        for part in (
            primary_category,
            offer.get("consistency", ""),
            offer.get("fields", {}).get("type", ""),
        )
        if part
    ).lower()
    if any(token in text for token in ("gel", "paste", "putty", "non-sag", "cartridge", "stick")):
        return True
    if "thin liquid" in text or "wicking" in text or "aerosol" in text:
        return False
    return None


def build_substrate_overrides(primary_category: str, offer: dict, detail: dict | None = None) -> dict:
    ratings: dict[str, float] = {}
    text_bits = [
        primary_category,
        offer.get("fields", {}).get("for_joining", ""),
        detail_field(detail, "for_joining"),
        detail_field(detail, "for_use_on"),
    ]
    joined = " ".join(bit for bit in text_bits if bit)
    lowered = joined.lower()

    for token, mapping in MATERIAL_TOKEN_MAP.items():
        if token in lowered:
            for material, score in mapping.items():
                ratings[material] = max(ratings.get(material, 0), score)

    if any(token in lowered for token in ("hard-to-bond materials", "polyethylene", "polypropylene")):
        ratings["hdpe"] = max(ratings.get("hdpe", 0), 9.0)

    if "electronics" in lowered or "circuit" in lowered:
        ratings["fr4"] = max(ratings.get("fr4", 0), 9.0)

    return ratings


def build_environment_overrides(primary_category: str) -> dict:
    lowered = primary_category.lower()
    overrides: dict[str, float] = {}
    if any(token in lowered for token in ("waterproof", "submersible", "immersion", "moisture-resistant")):
        overrides["humidity"] = 0.92
        overrides["immersion"] = 0.88
    if any(token in lowered for token in ("oil", "fuel", "chemical", "harsh environments")):
        overrides["fuel"] = 0.86
    if "outgassing" in lowered:
        overrides["humidity"] = 0.82
    return overrides


def build_stress_overrides(primary_category: str) -> dict:
    lowered = primary_category.lower()
    overrides: dict[str, float] = {}
    if any(token in lowered for token in ("impact-resistant", "toughened", "fatigue-resistant")):
        overrides["impact"] = 9.2
        overrides["peel"] = 7.8
    if any(token in lowered for token in ("high-strength", "structural")):
        overrides["shear"] = 8.8
    if "flexible" in lowered:
        overrides["peel"] = 9.0
        overrides["impact"] = 8.4
    return overrides


def build_pricing_entry(family: dict, offer: dict, detail: dict | None) -> dict | None:
    source_url = (detail or {}).get("url") or offer_direct_url(offer) or offer.get("source_url")
    if offer.get("price_per_ml") is not None:
        size_text = detail_field(detail, "size") or format_offer_size_text(offer) or ""
        container = detail_field(detail, "container_type") or normalize_space(
            offer.get("fields", {}).get("type")
        )
        example = f"{size_text} {container} from McMaster".strip()
        return {
            "basis": "observed",
            "unit": "mL",
            "unitPrice": round(offer["price_per_ml"], 4),
            "example": example,
            "sourceUrl": source_url,
        }
    if family.get("lowest_price_usd") is not None:
        return {
            "basis": "observed",
            "unit": "each",
            "unitPrice": round(family["lowest_price_usd"], 2),
            "example": "Lowest observed McMaster package price",
            "sourceUrl": source_url or (family["source_urls"][0] if family.get("source_urls") else None),
        }
    return None


def build_summary(primary_category: str, offer: dict) -> str:
    consistency = normalize_space(offer.get("consistency")) or normalize_space(offer.get("fields", {}).get("type"))
    joining = normalize_space(offer.get("fields", {}).get("for_joining"))
    bits = [primary_category]
    if consistency:
        bits.append(consistency.lower())
    if joining:
        short_joining = joining.split(",")
        bits.append(f"for {', '.join(short_joining[:3]).lower()}")
    return ", ".join(bits).rstrip(".") + "."


def infer_application_tags(
    family_name: str,
    primary_category: str,
    profile: str | None,
    offer: dict,
) -> list[str]:
    text = " ".join(
        part
        for part in (
            family_name,
            primary_category,
            offer.get("fields", {}).get("type", ""),
            offer.get("fields", {}).get("for_joining", ""),
            offer.get("fields", {}).get("consistency", ""),
        )
        if part
    ).lower()

    tags: list[str] = list(PROFILE_APPLICATION_TAGS.get(profile or "", []))

    def add(tag: str) -> None:
        if tag not in tags:
            tags.append(tag)

    if any(token in text for token in ("structural adhesive", "bonding epoxy", "bonding acrylic", "structural polyurethane")):
        add("structural-bonding")
    if any(token in text for token in ("instant-bond", "cyanoacrylate", "super glue")):
        add("instant-bonding")
    if any(token in text for token in ("optically clear", "glass bonding", "uv light", "visible light", "light-activated")):
        add("optical-bonding")
    if any(token in text for token in ("threadlocker", "studlock", "screwlock")):
        add("threadlocking")
    if any(token in text for token in ("retaining compound", "bearing mount", "sleeve retainer")):
        add("retaining")
    if any(token in text for token in ("gasket maker", "sealant", "joint sealant", "seam sealer", "rtv")):
        add("sealing-gasketing")
    if any(token in text for token in ("potting compound", "conductive adhesive", "electrically insulating adhesive", "thermal")):
        add("potting-thermal")
    if any(token in text for token in ("contact adhesive", "laminating")):
        add("contact-lamination")
    if any(token in text for token in ("construction adhesive", "anchoring adhesive", "masonry", "concrete bonding")):
        add("construction")
    if any(token in text for token in ("spray adhesive", "aerosol")):
        add("spray-mounting")
    if any(token in text for token in ("hot glue", "glue stick", "hot melt")):
        add("hot-melt-assembly")
    if any(token in text for token in ("solvent cement", "solvent weld")):
        add("solvent-welding")
    if any(token in text for token in ("wood glue", "paper", "cardboard", "fabric", "leather", "felt")):
        add("wood-paper-fabric")
    if any(token in text for token in ("hard-to-bond materials", "polyolefin", "polyethylene", "polypropylene", "plastic welder", "plastic bonder")):
        add("plastic-repair")

    if not tags:
        add("general-repair")

    return tags


def build_reference_entry(
    family: dict,
    offer: dict,
    detail: dict | None,
    tds_entry: dict | None,
    maker: str | None,
    family_name: str,
    primary_category: str,
    application_tags: list[str],
) -> dict:
    mcmaster = build_mcmaster_meta(offer, detail) or {}
    spec_url = (detail or {}).get("url") or offer_direct_url(offer) or (
        family["source_urls"][0] if family.get("source_urls") else offer.get("source_url")
    )
    tds_url = normalize_space((tds_entry or {}).get("tdsUrl"))
    product_url = normalize_space((tds_entry or {}).get("productUrl"))
    source_url = tds_url or product_url or spec_url
    source_label = "TDS" if tds_url else (mcmaster.get("sourceLabel") or "McMaster")
    return {
        "id": family["family_key"],
        "familyName": family_name,
        "manufacturer": maker,
        "primaryCategory": primary_category,
        "applicationTags": application_tags,
        "categories": family["category_headings"],
        "offerCount": family["offer_count"],
        "lowestPriceUsd": family["lowest_price_usd"],
        "bestPricePerMl": family["best_price_per_ml"],
        "tempMinC": f_to_c(family.get("temp_min_f")),
        "tempMaxC": f_to_c(family.get("temp_max_f")),
        "sampleType": mcmaster.get("packageType") or family.get("sample_type"),
        "samplePartNo": mcmaster.get("partNo"),
        "samplePackage": mcmaster.get("packageLabel"),
        "sampleMixRatio": mcmaster.get("mixRatio") or family.get("sample_mix_ratio"),
        "sampleColor": mcmaster.get("color"),
        "sampleCoverage": mcmaster.get("coverage"),
        "sampleCureType": mcmaster.get("cureType"),
        "sampleConsistency": mcmaster.get("consistency") or family.get("sample_consistency"),
        "sampleForJoining": mcmaster.get("forJoining") or family.get("sample_for_joining"),
        "sampleForUseOn": mcmaster.get("forUseOn"),
        "sourceLabel": source_label,
        "sourceUrl": source_url,
        "specUrl": spec_url,
        "tdsUrl": tds_url,
    }


def build_selector_product(
    family: dict,
    offer: dict,
    detail: dict | None,
    tds_entry: dict | None,
    maker: str | None,
    family_name: str,
    primary_category: str,
) -> dict | None:
    if not maker or should_skip_selector_family(family_name, primary_category):
        return None

    profile = infer_profile(family_name, maker, primary_category, offer)
    if not profile:
        return None

    service_min_c = f_to_c(family.get("temp_min_f"))
    service_max_c = f_to_c(family.get("temp_max_f"))
    lap_shear = psi_to_mpa(first_number(offer.get("fields", {}).get("shear_psi")))
    gap_fill = parse_gap_mm(offer.get("fields", {}).get("max_gap_filled"))
    pot_life, fixture_time = parse_minutes(offer)
    clarity = normalize_detail_clarity(detail_field(detail, "clarity")) or infer_clarity(
        family_name, primary_category, offer
    )
    viscosity_class = infer_viscosity_class(offer, primary_category, profile)
    thixotropic = infer_thixotropic(offer, primary_category)
    application_tags = infer_application_tags(family_name, primary_category, profile, offer)
    mcmaster = build_mcmaster_meta(offer, detail)
    spec_url = (detail or {}).get("url") or offer_direct_url(offer) or (
        family["source_urls"][0] if family.get("source_urls") else offer.get("source_url")
    )
    tds_url = normalize_space((tds_entry or {}).get("tdsUrl"))
    product_url = normalize_space((tds_entry or {}).get("productUrl"))
    source_url = tds_url or product_url or spec_url

    payload = {
        "id": f"mc-{family['family_key']}",
        "profile": profile,
        "maker": maker,
        "name": family_name,
        "summary": build_summary(primary_category, offer),
        "applicationTags": application_tags,
        "referenceUrl": source_url,
        "specUrl": spec_url,
    }

    if service_min_c is not None:
        payload["serviceMin"] = service_min_c
    if service_max_c is not None:
        payload["serviceMax"] = service_max_c
    if lap_shear is not None:
        payload["lapShear"] = lap_shear
    if gap_fill is not None:
        payload["gapFill"] = gap_fill
    if pot_life is not None:
        payload["potLife"] = max(0.25, round(pot_life, 2))
    if fixture_time is not None:
        payload["fixtureTime"] = max(0.25, round(fixture_time, 2))
    if clarity is not None:
        payload["clarity"] = clarity
    if viscosity_class is not None:
        payload["viscosityClass"] = viscosity_class
    if thixotropic is not None:
        payload["thixotropic"] = thixotropic
    if mcmaster:
        payload["mcmaster"] = mcmaster
    if tds_url:
        payload["tdsUrl"] = tds_url
        payload["sourceLabel"] = "TDS"
    elif mcmaster and mcmaster.get("sourceLabel"):
        payload["sourceLabel"] = mcmaster["sourceLabel"]

    substrates = build_substrate_overrides(primary_category, offer, detail)
    if substrates:
        payload["substrates"] = substrates

    environment = build_environment_overrides(primary_category)
    if environment:
        payload["environment"] = environment

    stress = build_stress_overrides(primary_category)
    if stress:
        payload["stress"] = stress

    pricing = build_pricing_entry(family, offer, detail)
    if pricing:
        payload["pricing"] = pricing

    cautions = []
    if "each" == pricing.get("unit") if pricing else False:
        cautions.append("Observed cost is per package because McMaster did not expose a normalizable volume.")
    if cautions:
        payload["cautions"] = cautions

    return payload


def build_catalog() -> tuple[list[dict], list[dict], dict]:
    raw = json.loads(RAW_PATH.read_text())
    detail_lookup, detail_stats = load_detail_lookup()
    tds_lookup, tds_stats = load_tds_lookup()
    families = raw["families"]
    raw_stats = raw.get("stats", {})
    offers_by_family: dict[str, list[dict]] = defaultdict(list)
    for offer in raw["offers"]:
        offers_by_family[offer["family_key"]].append(offer)

    reference_families: list[dict] = []
    selector_products: list[dict] = []

    for family in families:
        offers = offers_by_family.get(family["family_key"], [])
        if not offers:
            continue
        representative = choose_representative_offer(offers)
        representative_detail = detail_lookup.get(offer_part_no(representative) or "")
        tds_entry = tds_lookup.get(family["family_key"])
        maker = canonical_maker(family.get("manufacturer"), family.get("family_name") or "")
        maker = canonical_maker(detail_field(representative_detail, "manufacturer"), maker or family.get("family_name") or "")
        family_name = clean_family_name(family.get("family_name") or "", maker, representative_detail)
        primary_category = choose_primary_category(family.get("category_headings") or [])
        profile = infer_profile(family_name, maker, primary_category, representative)
        application_tags = infer_application_tags(family_name, primary_category, profile, representative)

        if family_name:
            reference_families.append(
                build_reference_entry(
                    family,
                    representative,
                    representative_detail,
                    tds_entry,
                    maker,
                    family_name,
                    primary_category,
                    application_tags,
                )
            )

        product = build_selector_product(
            family,
            representative,
            representative_detail,
            tds_entry,
            maker,
            family_name,
            primary_category,
        )
        if product is not None:
            selector_products.append(product)

    reference_families.sort(
        key=lambda item: (
            item["manufacturer"] or "zzz",
            item["familyName"] or "",
        )
    )
    selector_products.sort(key=lambda item: (item["maker"], item["name"]))

    stats = {
        "rawFamilies": len(reference_families),
        "selectorProducts": len(selector_products),
        "offers": raw_stats.get("offers", len(raw.get("offers", []))),
        "pagesCrawled": raw_stats.get("pages_crawled"),
        "leafPages": raw_stats.get("leaf_pages"),
        "detailPages": detail_stats.get("detail_pages"),
        "tdsFamilies": tds_stats.get("found"),
    }
    return selector_products, reference_families, stats


def write_outputs(selector_products: list[dict], reference_families: list[dict], stats: dict) -> None:
    payload = {
        "selectorProducts": selector_products,
        "referenceFamilies": reference_families,
        "stats": stats,
    }
    SUMMARY_OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    js = (
        "window.MCMASTER_SITE_PRODUCTS = "
        + json.dumps(selector_products, indent=2)
        + ";\n\nwindow.MCMASTER_REFERENCE_FAMILIES = "
        + json.dumps(reference_families, indent=2)
        + ";\n\nwindow.MCMASTER_PIPELINE_STATS = "
        + json.dumps(stats, indent=2)
        + ";\n"
    )
    JS_OUTPUT.write_text(js, encoding="utf-8")


def main() -> int:
    selector_products, reference_families, stats = build_catalog()
    write_outputs(selector_products, reference_families, stats)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
