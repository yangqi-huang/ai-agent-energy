import json
import math
import re
import time

import requests

from config import (
    MAP_GEOCODE_TIMEOUT_SECONDS,
    MAP_MAX_DEMAND_POINTS,
    MAP_MAX_REFERENCE_POINTS,
    MAP_REQUEST_DELAY_SECONDS,
    OSM_NOMINATIM_URL,
)


_GEOCODE_CACHE: dict[str, dict | None] = {}


def parse_map_targets(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except Exception:
        return {"reference_points": [], "demand_points": []}

    if not isinstance(data, dict):
        return {"reference_points": [], "demand_points": []}

    return {
        "project_context": str(data.get("project_context", "")).strip(),
        "reference_points": _clean_targets(
            data.get("reference_points", []),
            MAP_MAX_REFERENCE_POINTS,
        ),
        "demand_points": _clean_targets(
            data.get("demand_points", []),
            MAP_MAX_DEMAND_POINTS,
        ),
    }


def _clean_targets(items, limit: int) -> list[dict]:
    output = []
    seen = set()

    if not isinstance(items, list):
        return output

    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        query = str(item.get("query", "") or name).strip()
        if not name or not query:
            continue
        key = query.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(
            {
                "name": name,
                "type": str(item.get("type", "")).strip(),
                "query": query,
                "evidence": str(item.get("evidence", "")).strip(),
            }
        )
        if len(output) >= limit:
            break

    return output


def geocode_osm(query: str) -> dict | None:
    cache_key = query.strip().lower()
    if not cache_key:
        return None
    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]

    try:
        response = requests.get(
            OSM_NOMINATIM_URL,
            params={
                "q": query,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 0,
            },
            headers={
                "User-Agent": "JovoEnergyProjectBrief/1.0 local research",
                "Accept-Language": "en,zh-CN;q=0.8",
            },
            timeout=MAP_GEOCODE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            _GEOCODE_CACHE[cache_key] = None
            return None
        first = data[0]
        result = {
            "display_name": first.get("display_name", ""),
            "lat": float(first["lat"]),
            "lon": float(first["lon"]),
            "category": first.get("category", ""),
            "type": first.get("type", ""),
        }
        _GEOCODE_CACHE[cache_key] = result
        time.sleep(MAP_REQUEST_DELAY_SECONDS)
        return result
    except Exception:
        _GEOCODE_CACHE[cache_key] = None
        return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_map_context(targets: dict) -> str:
    reference_points = targets.get("reference_points", [])
    demand_points = targets.get("demand_points", [])
    project_context = str(targets.get("project_context", "")).strip()

    if not reference_points and project_context:
        reference_points = [
            {
                "name": "项目所在地",
                "type": "project area",
                "query": project_context,
                "evidence": "由项目所在地兜底生成，用于粗略直线距离测算",
            }
        ]

    if not reference_points and not demand_points:
        return "【OSM地图定位参考】\n未识别到可用于地图定位的项目参照点或具名需求点。"

    located_refs = []
    for target in reference_points:
        geo = geocode_osm(target["query"])
        located_refs.append({**target, "geo": geo})

    located_demands = []
    for target in demand_points:
        geo = geocode_osm(target["query"])
        located_demands.append({**target, "geo": geo})

    lines = [
        "【OSM地图定位参考】",
        "说明：以下距离为基于OSM/Nominatim定位结果计算的直线距离，仅作项目简报初筛参考；正式尽调应复核坐标和道路/管线路径。",
    ]

    lines.extend([
        "",
        "## 项目参照点定位",
        "| 参照点 | 类型 | 查询词 | OSM定位结果 | 坐标 |",
        "|---|---|---|---|---|",
    ])
    for item in located_refs:
        geo = item["geo"]
        if geo:
            coord = f"{geo['lat']:.5f}, {geo['lon']:.5f}"
            lines.append(
                f"| {item['name']} | {item['type']} | {item['query']} | {geo['display_name']} | {coord} |"
            )
        else:
            lines.append(
                f"| {item['name']} | {item['type']} | {item['query']} | OSM未定位 | - |"
            )

    lines.extend([
        "",
        "## 具名需求点定位与直线距离",
        "| 需求点 | 类型 | 查询词 | OSM定位结果 | 最近项目参照点 | 直线距离 | 定位状态 |",
        "|---|---|---|---|---|---|---|",
    ])

    valid_refs = [item for item in located_refs if item["geo"]]
    for item in located_demands:
        geo = item["geo"]
        if not geo:
            lines.append(
                f"| {item['name']} | {item['type']} | {item['query']} | OSM未定位 | - | - | 未定位，简报可保留文字依据但不要编造距离 |"
            )
            continue

        nearest = None
        for ref in valid_refs:
            distance = haversine_km(
                ref["geo"]["lat"],
                ref["geo"]["lon"],
                geo["lat"],
                geo["lon"],
            )
            if nearest is None or distance < nearest[1]:
                nearest = (ref, distance)

        if nearest:
            nearest_name = nearest[0]["name"]
            distance_text = f"约{nearest[1]:.1f} km"
            status = "OSM已定位，距离为直线距离"
        else:
            nearest_name = "-"
            distance_text = "-"
            status = "需求点已定位，但项目参照点未定位"

        lines.append(
            f"| {item['name']} | {item['type']} | {item['query']} | {geo['display_name']} | {nearest_name} | {distance_text} | {status} |"
        )

    return "\n".join(lines)
