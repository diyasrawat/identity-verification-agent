import re

ADDRESS_KNOWLEDGE_GRAPH = {
    "LINKING ROAD": {
        "aliases": ["LINKING RD", "LK ROAD", "LINKNG ROAD"],
        "cities": ["MUMBAI"],
        "areas": ["BANDRA", "BANDRA WEST", "KHAR", "SANTACRUZ"],
        "pincodes": ["400050", "400052", "400054"]
    },
    "MARINE DRIVE": {
        "aliases": ["MARINE DR", "NETAJI SUBHASH CHANDRA BOSE ROAD", "QUEEN NECKLACE ROAD"],
        "cities": ["MUMBAI"],
        "areas": ["CHURCHGATE", "NARIMAN POINT", "COLABA"],
        "pincodes": ["400020", "400021"]
    },
    "LBS MARG": {
        "aliases": ["LALA BAHADUR SHASTRI MARG", "LBS ROAD", "L B S MARG"],
        "cities": ["MUMBAI"],
        "areas": ["KURLA", "GHATKOPAR", "VIKHROLI"],
        "pincodes": ["400070", "400075", "400079", "400083"]
    },
    "CONNAUGHT PLACE": {
        "aliases": ["CP", "RAJIV CHOWK", "CONNAUGHT CIRCUS", "C PLACE"],
        "cities": ["DELHI", "NEW DELHI"],
        "areas": ["CENTRAL DELHI"],
        "pincodes": ["110001"]
    },
    "CHANDNI CHOWK": {
        "aliases": ["CHANDNI CHAWK", "CC ROAD"],
        "cities": ["DELHI", "NEW DELHI"],
        "areas": ["OLD DELHI", "NORTH DELHI"],
        "pincodes": ["110006"]
    },
    "OUTER RING ROAD": {
        "aliases": ["ORR", "RING ROAD", "OUTER RING RD"],
        "cities": ["DELHI", "NEW DELHI"],
        "areas": ["SOUTH DELHI", "EAST DELHI"],
        "pincodes": ["110077", "110096", "110095"]
    },
    "MG ROAD PUNE": {
        "aliases": [
            "MAHATMA GANDHI ROAD PUNE", "M G ROAD PUNE", "MG RD PUNE",
            "MG ROAD SHIVAJI NAGAR", "MAHATMA GANDHI ROAD SHIVAJI NAGAR",
            "MAHATMA GANDHI ROAD CAMP", "MG ROAD CAMP"
        ],
        "cities": ["PUNE"],
        "areas": ["CAMP", "SHIVAJI NAGAR", "DECCAN", "CANTONMENT"],
        "pincodes": ["411001"]
    },
    "FC ROAD": {
        "aliases": ["FERGUSSON COLLEGE ROAD", "FERGUSSON RD", "F C ROAD"],
        "cities": ["PUNE"],
        "areas": ["DECCAN", "SHIVAJI NAGAR"],
        "pincodes": ["411004", "411005"]
    },
    "JM ROAD": {
        "aliases": ["JANGLI MAHARAJ ROAD", "J M ROAD", "JM RD"],
        "cities": ["PUNE"],
        "areas": ["DECCAN"],
        "pincodes": ["411004"]
    },
    "MG ROAD BANGALORE": {
        "aliases": ["MAHATMA GANDHI ROAD BANGALORE", "MG RD BANGALORE", "MG ROAD BLR"],
        "cities": ["BANGALORE", "BENGALURU"],
        "areas": ["CENTRAL BANGALORE"],
        "pincodes": ["560001"]
    },
    "BRIGADE ROAD": {
        "aliases": ["BRIGADE RD", "BRIGADES ROAD"],
        "cities": ["BANGALORE", "BENGALURU"],
        "areas": ["CENTRAL BANGALORE"],
        "pincodes": ["560001", "560025"]
    },
    "KORAMANGALA": {
        "aliases": ["KORAMANGALA ROAD", "KORMANGALA", "KORAMANGLA"],
        "cities": ["BANGALORE", "BENGALURU"],
        "areas": ["SOUTH BANGALORE"],
        "pincodes": ["560034", "560095"]
    },
    "ANNA SALAI": {
        "aliases": ["MOUNT ROAD", "MT ROAD", "ANNA SALAI ROAD"],
        "cities": ["CHENNAI"],
        "areas": ["CENTRAL CHENNAI", "TEYNAMPET"],
        "pincodes": ["600002", "600006"]
    },
    "ECR": {
        "aliases": ["EAST COAST ROAD", "EAST COAST RD", "E C ROAD"],
        "cities": ["CHENNAI"],
        "areas": ["THIRUVANMIYUR", "BESANT NAGAR", "SHOLINGANALLUR"],
        "pincodes": ["600041", "600090", "600119"]
    },
    "BANJARA HILLS ROAD": {
        "aliases": ["BANJARA HILLS", "BH ROAD", "BANJARA RD"],
        "cities": ["HYDERABAD"],
        "areas": ["BANJARA HILLS"],
        "pincodes": ["500034"]
    },
}


def extract_pincode(address: str) -> str:
    match = re.search(r'\b\d{6}\b', address)
    return match.group(0) if match else ""


def graph_lookup(address: str) -> dict:
    address_upper = address.upper().strip()

    for road_name, data in ADDRESS_KNOWLEDGE_GRAPH.items():
        all_names = [road_name] + data["aliases"]
        for name in all_names:
            if name in address_upper:
                return {
                    "found": True,
                    "canonical_road": road_name,
                    "matched_via": name,
                    "cities": data["cities"],
                    "known_pincodes": data["pincodes"],
                    "known_areas": data["areas"]
                }

    return {"found": False}


def graph_address_match(addr_a: str, addr_b: str) -> dict:
    node_a = graph_lookup(addr_a)
    node_b = graph_lookup(addr_b)

    if node_a["found"] and node_b["found"]:
        road_a = node_a["canonical_road"]
        road_b = node_b["canonical_road"]

        if road_a == road_b:
            pin_a = extract_pincode(addr_a)
            pin_b = extract_pincode(addr_b)

            if pin_a and pin_b and pin_a == pin_b:
                return {
                    "result": "GRAPH_CONFIRMED_MATCH",
                    "confidence": "HIGH",
                    "reasoning": (
                        f"Graph confirms both addresses are on "
                        f"{road_a} with matching pincode {pin_a}"
                    )
                }
            elif pin_a and pin_b and pin_a != pin_b:
                known_pins = node_a["known_pincodes"]
                if pin_a in known_pins and pin_b in known_pins:
                    return {
                        "result": "GRAPH_CONFIRMED_MATCH",
                        "confidence": "MEDIUM",
                        "reasoning": (
                            f"Graph confirms both pincodes "
                            f"({pin_a}, {pin_b}) are known areas of {road_a}"
                        )
                    }
            else:
                return {
                    "result": "GRAPH_CONFIRMED_MATCH",
                    "confidence": "MEDIUM",
                    "reasoning": (
                        f"Graph identifies both as {road_a} — "
                        f"'{node_a['matched_via']}' and "
                        f"'{node_b['matched_via']}' are aliases"
                    )
                }

        cities_a = set(node_a["cities"])
        cities_b = set(node_b["cities"])

        if not cities_a.intersection(cities_b):
            return {
                "result": "GRAPH_CONFIRMED_DIFFERENT",
                "confidence": "HIGH",
                "reasoning": (
                    f"Graph confirms different cities: "
                    f"{road_a} is in {', '.join(node_a['cities'])} but "
                    f"{road_b} is in {', '.join(node_b['cities'])}"
                )
            }
        else:
            return {
                "result": "GRAPH_CONFIRMED_DIFFERENT",
                "confidence": "HIGH",
                "reasoning": (
                    f"Graph confirms different roads in same city: "
                    f"{road_a} vs {road_b}"
                )
            }

    if node_a["found"] or node_b["found"]:
        return {
            "result": "GRAPH_PARTIAL",
            "confidence": "LOW",
            "reasoning": "One address found in graph, other unknown — falling back to fuzzy matching"
        }

    return {
        "result": "GRAPH_UNKNOWN",
        "confidence": "NONE",
        "reasoning": "Neither address in knowledge graph — using fuzzy matching"
    }
