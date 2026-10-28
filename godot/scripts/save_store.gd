extends RefCounted

const PATH = "user://progress.json"
var data: Dictionary = {"best_waves": {}, "stars": {}, "total_kills": 0, "total_waves": 0, "audio_enabled": true, "difficulty": {"hell": "easy", "ice": "easy"}, "selected_map": "hell"}

func _init() -> void:
	var source = PATH
	if not FileAccess.file_exists(source):
		source = OS.get_user_data_dir().get_base_dir().path_join("Защитник/progress.json")
	if FileAccess.file_exists(source):
		var loaded = JSON.parse_string(FileAccess.get_file_as_string(source))
		if loaded is Dictionary:
			data.merge(loaded, true)

func save() -> void:
	var file = FileAccess.open(PATH + ".tmp", FileAccess.WRITE)
	if file == null:
		push_warning("Не удалось сохранить прогресс: " + str(FileAccess.get_open_error()))
		return
	file.store_string(JSON.stringify(data))
	file.close()
	DirAccess.rename_absolute(ProjectSettings.globalize_path(PATH + ".tmp"), ProjectSettings.globalize_path(PATH))

func record(map_id: String, wave: int, hp: int, kills: int, won: bool) -> void:
	data.best_waves[map_id] = max(int(data.best_waves.get(map_id, 0)), wave)
	data.total_kills += kills
	data.total_waves += wave
	if won:
		var stars = 3 if hp >= 20 else (2 if hp >= 10 else 1)
		data.stars[map_id] = max(int(data.stars.get(map_id, 0)), stars)
	save()
