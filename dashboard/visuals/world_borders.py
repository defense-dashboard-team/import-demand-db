"""세계지도 국가 경계선 (GeoJSON)"""
import gzip
import json

import streamlit as st

from dashboard.common.config import ASSETS_DIR


# 1페이지 평면 세계지도용 국가 경계 (gzip 압축 파일)
WORLD_GEOJSON_PATH = ASSETS_DIR / "world_countries.geojson.gz"


@st.cache_resource
def load_world_geojson():
    geojson = json.loads(
        gzip.decompress(
            WORLD_GEOJSON_PATH.read_bytes()
        ).decode("utf-8")
    )

    # 좌표를 소수점 3자리(약 100m)로 줄여 브라우저 전송량을 절반 이하로
    # (세계지도 크기에서는 눈으로 차이가 없습니다)
    def round_coords(value):
        if isinstance(value, list):
            return [round_coords(item) for item in value]
        return round(value, 3)

    for feature in geojson.get("features", []):
        geometry = feature.get("geometry") or {}
        if "coordinates" in geometry:
            geometry["coordinates"] = round_coords(geometry["coordinates"])

    ids = [
        feature.get("id")
        for feature in geojson.get("features", [])
        if feature.get("id")
    ]

    return geojson, ids


@st.cache_resource
def world_geojson_subset(ids):
    """
    지도 레이어마다 필요한 나라의 국경선만 담은 GeoJSON.
    (레이어 3개가 전체 국경선을 각각 보내면 매번 1MB 넘게 전송됩니다)
    ids : 정렬된 ISO3 튜플
    """
    geojson, _ = load_world_geojson()
    keep = set(ids)

    return {
        "type": "FeatureCollection",
        "features": [
            feature
            for feature in geojson.get("features", [])
            if feature.get("id") in keep
        ],
    }
