from china_cars.paths import CONFIG_DIR, DATA_DIR, DOCS_DIR, OPS_DIR, SQL_DIR


def test_core_directories_exist():
    assert CONFIG_DIR.exists()
    assert DATA_DIR.exists()
    assert DOCS_DIR.exists()
    assert OPS_DIR.exists()
    assert SQL_DIR.exists()
