from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "weather.db"

STATIONS = {
    "54511099999": {"city": "北京", "province": "北京"},
    "58367099999": {"city": "上海", "province": "上海"},
    "59287099999": {"city": "广州", "province": "广东"},
    "56294099999": {"city": "成都", "province": "四川"},
    "57494099999": {"city": "武汉", "province": "湖北"},
    "50953099999": {"city": "哈尔滨", "province": "黑龙江"},
    "51463099999": {"city": "乌鲁木齐", "province": "新疆"},
    "56778099999": {"city": "昆明", "province": "云南"},
}

SOURCE = "NOAA/NCEI Global Summary of the Day"

