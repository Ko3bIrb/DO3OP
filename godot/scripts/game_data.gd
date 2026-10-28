extends RefCounted

static var _data: Dictionary = {}

static func all() -> Dictionary:
	if _data.is_empty():
		_data = JSON.parse_string(FileAccess.get_file_as_string("res://data/game_data.json"))
	return _data

static func vector(values: Array) -> Vector3:
	return Vector3(values[0], values[1], values[2])

static func js_round(value: float) -> int:
	return int(floor(value + 0.5))

static func stats(type: String, level: int) -> Dictionary:
	return all().towers[type].levels[level - 1].duplicate(true)

static func upgrade_cost(type: String, level: int) -> int:
	if level >= 3:
		return -1
	return int(all().towers[type].upgrade_costs[level - 1])

static func sell_price(type: String, level: int) -> int:
	var base = float(all().towers[type].baseCost)
	return js_round((base + (base * 0.75 if level >= 2 else 0.0) + (base if level >= 3 else 0.0)) * 0.5)
