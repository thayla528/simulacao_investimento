def parse_float(val):
    if val is None or val == "":
        return 0.0
    return float(str(val).replace(",", "."))