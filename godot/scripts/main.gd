extends Node3D

const Data = preload("res://scripts/game_data.gd")
const Simulation = preload("res://scripts/simulation.gd")
const SaveStore = preload("res://scripts/save_store.gd")
const Sound = preload("res://scripts/sound.gd")
const CombatFX = preload("res://scripts/combat_fx.gd")
const Landscape = preload("res://scripts/landscape.gd")
const Atmosphere = preload("res://scripts/atmosphere.gd")
const MAP_IMAGES = {"hell":preload("res://assets/map_hell.png"),"ice":preload("res://assets/map_ice.png")}
const TYPES = ["gun", "sniper", "mortar", "slow", "skyguard", "amp"]

var save_store = SaveStore.new()
var sound: Node
var sim: RefCounted
var world: Node3D
var camera: Camera3D
var ui: Control
var canvas: CanvasLayer
var menu: Control
var dialog_layer: Control
var navigation: VBoxContainer
var dock: PanelContainer
var speed_bar: HBoxContainer
var wave_label: Label
var coins_label: Label
var health_label: Label
var tower_panel: PanelContainer
var tower_title: Label
var tower_stars: Label
var tower_stats: Label
var upgrade_button: Button
var sell_button: Button
var audio_button: Button
var speed_slider: HSlider
var speed_value: Label
var tactical_button: Button
var _hud_visibility: Dictionary = {}
var _spatial_overlay_visibility: Dictionary = {}
var _pause_menu_open = false
var _return_to_pause = false
var shop_buttons: Dictionary = {}
var selected: Dictionary = {}
var hovered: Dictionary = {}
var building = ""
var ghost: Node3D
var range_mesh: MeshInstance3D
var spot_nodes: Array = []
var tower_nodes: Dictionary = {}
var enemy_nodes: Dictionary = {}
var projectile_nodes: Array = []
var deaths: Array = []
var effects: Array = []
var _models: Dictionary = {}
var _gesture_start = Vector2.ZERO
var _gesture_time = 0
var _gesture_moved = false
var _touches: Dictionary = {}
var _multitouch = false
var _dialog_pause = false
var _active_dialog: Control
var accent = Color("c99d62")
var panel_color = Color("181410")
var muted = Color("b9aa95")
var _last_time = 0.0
var fx: Node3D
var _actor_pool: Dictionary = {}
var _recoil: Dictionary = {}
var _loading = false
var _loading_overlay: ColorRect
var _bar_background: QuadMesh
var _bar_fill: QuadMesh
var _bar_dark: StandardMaterial3D
var _bar_green: StandardMaterial3D
var pool_growth = 0
var _ghost_material: StandardMaterial3D
var _unit_range: ImmediateMesh
var _screenshot_path = ""
var _screenshot_timer = 0.0

func _ready() -> void:
	get_window().mode = Window.MODE_FULLSCREEN
	get_window().content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	get_tree().auto_accept_quit = false
	sound = Sound.new()
	add_child(sound)
	sound.enabled = save_store.data.audio_enabled
	canvas = CanvasLayer.new()
	add_child(canvas)
	ui = Control.new()
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(ui)
	dialog_layer = Control.new()
	dialog_layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dialog_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(dialog_layer)
	get_viewport().size_changed.connect(_layout)
	for arg in OS.get_cmdline_user_args():
		if arg == "--windowed":
			get_window().mode = Window.MODE_WINDOWED
			DisplayServer.window_set_size(Vector2i(1440, 900))
	show_menu()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--map="):
			start_game(arg.trim_prefix("--map="), "easy")
		elif arg.begins_with("--screenshot="):
			_screenshot_path = arg.trim_prefix("--screenshot=")
			_screenshot_timer = 3.0
		elif arg == "--demo":
			call_deferred("_demo")

func _demo() -> void:
	while _loading: await get_tree().process_frame
	if sim == null:
		await start_game("hell", "easy")
	sim.coins = 3000
	for i in range(min(8, sim.spots.size())):
		sim.build("sniper" if sim.spots[i].restricted_to != "" else TYPES[i % 6] if TYPES[i % 6] != "sniper" else "gun", i)
	if not sim.towers.is_empty():
		select_tower(sim.towers[int(sim.towers.size() / 2)])
	sim.start_wave()

func _style(background: Color, border: Color, padding: int = 8) -> StyleBoxFlat:
	var box = StyleBoxFlat.new()
	box.bg_color = background
	box.border_color = border
	box.set_border_width_all(1)
	box.set_corner_radius_all(4)
	box.content_margin_left = padding
	box.content_margin_right = padding
	box.content_margin_top = padding
	box.content_margin_bottom = padding
	return box

func _theme() -> Theme:
	var theme = Theme.new()
	theme.default_font_size = 14
	theme.default_font = preload("res://assets/fonts/Interface.ttf")
	theme.set_color("font_color", "Label", Color("e8e1d3") if accent.r > accent.b else Color("d4e6ed"))
	theme.set_color("font_color", "Button", muted)
	theme.set_color("font_hover_color", "Button", accent)
	theme.set_color("font_pressed_color", "Button", accent)
	theme.set_stylebox("normal", "Button", _style(panel_color.lightened(0.04), Color(accent, 0.28), 8))
	theme.set_stylebox("hover", "Button", _style(panel_color.lightened(0.10), accent, 8))
	theme.set_stylebox("pressed", "Button", _style(panel_color.lightened(0.16), accent, 8))
	theme.set_stylebox("disabled", "Button", _style(panel_color, Color(accent, 0.12), 8))
	theme.set_stylebox("panel", "PanelContainer", _style(Color(panel_color, 0.96), Color(accent, 0.45), 10))
	return theme

func _button(text: String, callback: Callable, parent: Node, minimum: Vector2 = Vector2(0, 40)) -> Button:
	var button = Button.new()
	button.text = text
	button.focus_mode = Control.FOCUS_NONE
	button.custom_minimum_size = minimum
	button.pressed.connect(callback)
	parent.add_child(button)
	return button

func _label(text: String, parent: Node, font_size: int = 14) -> Label:
	var label = Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", font_size)
	parent.add_child(label)
	return label

func _remove_game_ui() -> void:
	for child in ui.get_children():
		if child != dialog_layer:
			ui.remove_child(child)
			child.queue_free()
	shop_buttons.clear()
	speed_slider = null
	speed_value = null
	tower_panel = null

func show_menu() -> void:
	_close_dialog()
	_return_to_pause = false
	if world != null:
		world.queue_free()
		world = null
	if camera != null:
		camera.queue_free()
		camera = null
	sim = null
	selected = {}
	hovered = {}
	building = ""
	tower_nodes.clear()
	enemy_nodes.clear()
	deaths.clear()
	effects.clear()
	projectile_nodes.clear()
	spot_nodes.clear()
	_remove_game_ui()
	accent = Color("88ccff")
	panel_color = Color("0b1729")
	muted = Color("bbd6e8")
	ui.theme = _theme()
	menu = Control.new()
	menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.add_child(menu)
	_menu_backdrop(menu)
	var box = PanelContainer.new()
	box.name = "MenuBox"
	box.add_theme_stylebox_override("panel", _style(Color(0.025, 0.045, 0.075, 0.65), Color(0.72, 0.80, 0.85, 0.15), 28))
	menu.add_child(box)
	var rows = VBoxContainer.new()
	rows.add_theme_constant_override("separation", 14)
	box.add_child(rows)
	_menu_contents(rows, false)
	_layout()
	ui.move_child(dialog_layer, ui.get_child_count() - 1)
	call_deferred("_layout")

func _menu_backdrop(parent: Control) -> void:
	var image = TextureRect.new()
	image.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	image.texture = load("res://assets/winter_watch.png")
	image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(image)
	parent.move_child(image, 0)
	var snow = CPUParticles2D.new()
	snow.name = "MenuSnow"
	snow.amount = 100
	snow.lifetime = 18.0
	snow.preprocess = 10.0
	snow.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	snow.emission_rect_extents = Vector2(900, 50)
	snow.position = Vector2(720, -40)
	snow.direction = Vector2(0.15, 1)
	snow.spread = 15
	snow.gravity = Vector2.ZERO
	snow.initial_velocity_min = 25
	snow.initial_velocity_max = 65
	snow.scale_amount_min = 0.6
	snow.scale_amount_max = 1.8
	snow.color = Color(0.8, 0.9, 1, 0.4)
	parent.add_child(snow)
	parent.move_child(snow, 1)

func _menu_contents(rows: VBoxContainer, paused: bool) -> void:
	var caption = _label("ПОСЛЕДНИЙ БАСТИОН  /  ЗИМНЯЯ СТРАЖА", rows, 11)
	caption.modulate = Color("b6c4cf")
	var title = _label("НОЧНОЙ ДОЗОР", rows, 35)
	title.add_theme_font_override("font", preload("res://assets/fonts/Title.ttf"))
	title.modulate = Color("f1e5d1")
	var subtitle = _label("Пока горит огонь — надежда жива.", rows, 12)
	subtitle.modulate = Color("b6c4cf")
	_label("ИГРА ПРИОСТАНОВЛЕНА" if paused else "", rows, 10).modulate = Color("dfb878")
	_button("Продолжить" if paused else "Начать защиту", _close_dialog if paused else func(): _choose_difficulty(save_store.data.selected_map), rows, Vector2(355, 52))
	_button("Выбрать карту", func(): _open_menu_dialog(_show_maps, paused), rows, Vector2(355, 46))
	_button("Как играть", func(): _open_menu_dialog(_show_rules, paused), rows, Vector2(355, 46))
	var audio = _button("Звук: " + ("включён" if sound.enabled else "выключен"), func(): _toggle_audio(), rows, Vector2(355, 46))
	audio.pressed.connect(func(): audio.text = "Звук: " + ("включён" if sound.enabled else "выключен"))
	if paused:
		_button("Начать заново", func(): _open_menu_dialog(_confirm_restart, true), rows, Vector2(355, 46))
		_button("В главное меню", func(): _open_menu_dialog(_confirm_exit, true), rows, Vector2(355, 46))
	_button("Выйти из игры", _quit_game, rows, Vector2(355, 46))
	if paused:
		_label("ESC — ВЕРНУТЬСЯ К ОБОРОНЕ", rows, 10).modulate = Color("8b9da8")

func _open_menu_dialog(callback: Callable, from_pause: bool) -> void:
	callback.call()
	_return_to_pause = from_pause

func _show_pause_menu() -> void:
	if sim == null or _loading:
		return
	_return_to_pause = false
	var rows = _dialog("", 435)
	rows.get_child(0).queue_free()
	_menu_contents(rows, true)
	_pause_menu_open = true

func _back_dialog() -> void:
	if _return_to_pause:
		_return_to_pause = false
		_show_pause_menu()
	else:
		_close_dialog()

func _dialog(title: String, width: float = 600.0) -> VBoxContainer:
	_close_dialog()
	if sim != null:
		_dialog_pause = sim.paused
		sim.paused = true
		_hide_game_hud()
	_active_dialog = ColorRect.new()
	_active_dialog.color = Color(0.01, 0.02, 0.04, 0.46)
	_active_dialog.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dialog_layer.add_child(_active_dialog)
	var center = CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_active_dialog.add_child(center)
	var panel = PanelContainer.new()
	panel.custom_minimum_size.x = width
	center.add_child(panel)
	var rows = VBoxContainer.new()
	rows.add_theme_constant_override("separation", 12)
	panel.add_child(rows)
	var label = _label(title, rows, 26)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return rows

func _hide_game_hud() -> void:
	for overlay in [range_mesh, ghost] + spot_nodes:
		if is_instance_valid(overlay):
			_spatial_overlay_visibility[overlay] = overlay.visible
			overlay.hide()
	for child in ui.get_children():
		if child != dialog_layer and child is CanvasItem:
			_hud_visibility[child] = child.visible
			child.hide()

func _restore_game_hud() -> void:
	for overlay in _spatial_overlay_visibility:
		if is_instance_valid(overlay): overlay.visible = _spatial_overlay_visibility[overlay]
	_spatial_overlay_visibility.clear()
	for child in _hud_visibility:
		if is_instance_valid(child): child.visible = _hud_visibility[child]
	_hud_visibility.clear()

func _close_dialog() -> void:
	_restore_game_hud()
	_pause_menu_open = false
	if is_instance_valid(world):
		world.show()
	if _active_dialog != null:
		_active_dialog.queue_free()
		_active_dialog = null
		if sim != null:
			sim.paused = _dialog_pause
			_refresh()

func _show_maps() -> void:
	var rows = _dialog("ВЫБОР КАРТЫ", 880)
	var cards = HBoxContainer.new()
	cards.add_theme_constant_override("separation", 16)
	rows.add_child(cards)
	for id in ["hell", "ice"]:
		var button = _button("", func(): save_store.data.selected_map = id; save_store.save(); _choose_difficulty(id), cards, Vector2(410, 310))
		button.tooltip_text = "Выбрать карту"
		var content = VBoxContainer.new()
		content.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		content.offset_left = 12
		content.offset_right = -12
		content.offset_top = 12
		content.offset_bottom = -12
		content.mouse_filter = Control.MOUSE_FILTER_IGNORE
		button.add_child(content)
		var preview = TextureRect.new()
		preview.texture = MAP_IMAGES[id]
		preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		preview.custom_minimum_size = Vector2(386, 196)
		preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
		content.add_child(preview)
		_label("ПЕПЕЛЬНЫЙ РАЗЛОМ" if id == "hell" else "ЗИМНЯЯ БУХТА", content, 19).mouse_filter = Control.MOUSE_FILTER_IGNORE
		var description = _label("Лава, огненные уступы и дорога сквозь руины" if id == "hell" else "Водопад, береговые уступы и узкий мост", content, 12)
		description.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var record = _label("20 волн · Рекорд: %d · %s" % [save_store.data.best_waves.get(id, 0), "★".repeat(int(save_store.data.stars.get(id, 0)))], content, 12)
		record.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_button("Назад", _back_dialog, rows)

func _choose_difficulty(id: String) -> void:
	var rows = _dialog("СЛОЖНОСТЬ · " + Data.all().maps[id].name, 640)
	for key in ["easy", "medium", "hard"]:
		var data = Data.all().difficulty[key]
		var text = "%s\nЗдоровье: %d · Монеты: %d" % [data.name, data.hp, data.coins]
		_button(text, func(): start_game(id, key), rows, Vector2(590, 76))
	_button("Назад", _back_dialog, rows)

func _show_rules() -> void:
	var rows = _dialog("ПРАВИЛА", 760)
	var scroll = ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(710, 430)
	rows.add_child(scroll)
	var content = VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(content)
	var intro = _label("Отбейте 20 волн. Враги, дошедшие до крепости, отнимают здоровье.\nВыберите башню внизу и свободную площадку на карте.\nСнайпер строится только на специальных синих площадках.\nEsc — меню · Пробел — тактическая пауза для строительства.\nПолзунок ТЕМП — от 0.25× до 5×; стрелки меняют темп.\nРестарт — начать текущую карту заново.\nПодготовка следующей волны начинается автоматически.", content, 15)
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	for type in TYPES:
		var data = Data.all().towers[type]
		_label("\n%s · %d монет" % [data.name, data.baseCost], content, 19)
		var label = _label(data.details, content, 14)
		label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		for level in [2, 3]:
			var stats = Data.stats(type, level)
			_label("%d уровень: %s · дальность %.1f · урон %.1f" % [level, data.upgrades[str(level)], stats.range, stats.damage], content, 12)
	_button("Понятно", _back_dialog, rows)

func start_game(id: String, difficulty_id: String) -> void:
	if _loading:
		return
	_loading = true
	_loading_overlay = ColorRect.new()
	_loading_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_loading_overlay.color = Color("0b131f")
	dialog_layer.add_child(_loading_overlay)
	var center = CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_loading_overlay.add_child(center)
	var label = _label("НОЧНОЙ ДОЗОР\n\nПодготовка карты…", center, 28)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	await get_tree().process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
	_close_dialog()
	_return_to_pause = false
	if world != null:
		world.queue_free()
	if camera != null:
		camera.queue_free()
	_remove_game_ui()
	_actor_pool.clear()
	_recoil.clear()
	tower_nodes.clear()
	enemy_nodes.clear()
	spot_nodes.clear()
	projectile_nodes.clear()
	deaths.clear()
	effects.clear()
	selected = {}
	hovered = {}
	building = ""
	ghost = null
	range_mesh = null
	save_store.data.selected_map = id
	save_store.data.difficulty[id] = difficulty_id
	save_store.save()
	sim = Simulation.new()
	sim.setup(id, difficulty_id)
	_last_time = 0.0
	sim.tower_changed.connect(_tower_changed)
	sim.enemy_spawned.connect(_enemy_spawned)
	sim.enemy_removed.connect(_enemy_removed)
	sim.effect.connect(_effect)
	sim.changed.connect(_refresh)
	sim.wave_started.connect(func(): sound.wave_start())
	sim.completed.connect(_completed)
	accent = Color("c99d62") if id == "hell" else Color("99c3d2")
	panel_color = Color("181410") if id == "hell" else Color("10212b")
	muted = Color("b9aa95") if id == "hell" else Color("a6c0ca")
	ui.theme = _theme()
	world = Node3D.new()
	add_child(world)
	world.add_child(_model("world_" + id))
	var landscape = Landscape.new()
	world.add_child(landscape)
	landscape.configure(world, id)
	fx = CombatFX.new()
	world.add_child(fx)
	_lighting(id)
	camera = Camera3D.new()
	camera.fov = 45.0
	camera.far = 1600.0
	add_child(camera)
	camera.current = true
	for i in range(sim.spots.size()):
		var spot = sim.spots[i]
		var mesh = _mesh(CylinderMesh.new(), Color("a4c5d5") if spot.restricted_to != "" else accent, true)
		mesh.mesh.top_radius = 1.12
		mesh.mesh.bottom_radius = 1.18
		mesh.mesh.height = 0.10
		mesh.mesh.radial_segments = 16
		mesh.position = spot.position + Vector3.UP * 0.27
		mesh.visible = false
		world.add_child(mesh)
		spot_nodes.append(mesh)
	_build_hud()
	_refresh()
	_layout()
	call_deferred("_layout")
	ui.move_child(dialog_layer, ui.get_child_count() - 1)
	await _prepare_combat()
	_loading = false
	_loading_overlay.queue_free()

func _prepare_combat() -> void:
	_bar_background = QuadMesh.new()
	_bar_background.size = Vector2(2, .15)
	_bar_fill = QuadMesh.new()
	_bar_fill.size = Vector2(2, .13)
	_bar_dark = StandardMaterial3D.new()
	_bar_dark.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_bar_dark.albedo_color = Color("160f18")
	_bar_green = StandardMaterial3D.new()
	_bar_green.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_bar_green.albedo_color = Color("a9da77")
	var warm_nodes: Array = []
	for type in sim.map.enemies:
		var capacity = 2
		for wave in sim.map.waves:
			var count = 0
			for group in wave.groups:
				if group.type == type: count += int(group.count)
			capacity = maxi(capacity, count)
		_actor_pool[type] = []
		for i in range(mini(32, capacity)):
			_actor_pool[type].append(_new_actor(type))
		var entry = _actor_pool[type][0]
		entry.node.position = Vector3(0, 2, 0)
		entry.node.show()
		entry.bar.position = Vector3(0,4,0)
		entry.bar.show()
		warm_nodes.append(entry.node)
		warm_nodes.append(entry.bar)
	for type in TYPES:
		for level in [1,2,3]:
			var node = _model("tower_%s_%d" % [type,level])
			world.add_child(node)
			warm_nodes.append(node)
	_ghost_material = StandardMaterial3D.new()
	_ghost_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_ghost_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_ghost_material.albedo_color = Color(.25,.8,.6,.35)
	for type in TYPES:
		var preview = _model("tower_%s_1" % type)
		world.add_child(preview)
		_ghost_style(preview)
		warm_nodes.append(preview)
	_draw_range(Vector3.ZERO,1,Color("88bbcc"))
	fx.warmup(Vector3(0,2,0))
	for i in range(2):
		await get_tree().process_frame
		if DisplayServer.get_name() != "headless": await RenderingServer.frame_post_draw
	for node in warm_nodes: node.hide()
	for node in warm_nodes:
		if node not in _actor_nodes(): node.queue_free()
	fx.particles.clear()
	fx.render(0)
	_hide_range()

func _actor_nodes() -> Array:
	var nodes: Array = []
	for type in _actor_pool:
		for entry in _actor_pool[type]:
			nodes.append(entry.node)
			nodes.append(entry.bar)
	return nodes

func _new_actor(type: String) -> Dictionary:
	var node = _model("enemy_" + type)
	world.add_child(node)
	node.hide()
	var bar = Node3D.new()
	world.add_child(bar)
	bar.hide()
	var background = MeshInstance3D.new()
	background.mesh = _bar_background
	background.material_override = _bar_dark
	bar.add_child(background)
	var fill = MeshInstance3D.new()
	fill.mesh = _bar_fill
	fill.material_override = _bar_green
	fill.position.z = .01
	bar.add_child(fill)
	var joints: Array = []
	for joint in node.find_children("motion_*", "Node3D", true, false):
		var key = str(joint.name)
		var role = 0 if "leg" in key else 1 if "arm" in key else 2 if "wing" in key else 3 if "head" in key else 4
		joints.append({"node":joint,"role":role,"sign":-1.0 if key.ends_with("L") or "-1" in key else 1.0,"rest":joint.transform})
	return {"node":node,"bar":bar,"fill":fill,"joints":joints,"type":type}

func _release_actor(entry: Dictionary) -> void:
	entry.node.hide()
	entry.bar.hide()
	entry.node.transform = Transform3D.IDENTITY
	for joint in entry.joints: joint.node.transform = joint.rest
	_actor_pool[entry.type].append(entry)

func _model(key: String) -> Node3D:
	if not _models.has(key):
		_models[key] = load("res://assets/models/" + key + ".glb")
	var result = _models[key].instantiate()
	_prepare_materials(result)
	return result

func _prepare_materials(node: Node) -> void:
	if node is MeshInstance3D and node.name.begins_with("billboard"):
		for i in range(node.mesh.get_surface_count()):
			var material = node.get_active_material(i)
			if material is StandardMaterial3D:
				material = material.duplicate()
				material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
				material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				material.no_depth_test = false
				node.set_surface_override_material(i, material)
	for child in node.get_children():
		_prepare_materials(child)

func _mesh(mesh: Mesh, color: Color, unshaded: bool = false) -> MeshInstance3D:
	var instance = MeshInstance3D.new()
	instance.mesh = mesh
	var material = StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.8
	if unshaded:
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	instance.material_override = material
	return instance

func _lighting(id: String) -> void:
	Atmosphere.setup(world, id)

func _build_hud() -> void:
	navigation = VBoxContainer.new()
	ui.add_child(navigation)
	_label(sim.map.name.to_upper(), navigation, 11).modulate = muted
	var nav_panel = PanelContainer.new()
	navigation.add_child(nav_panel)
	var nav = HBoxContainer.new()
	nav_panel.add_child(nav)
	_button("Меню · Esc", _show_pause_menu, nav)
	_button("Рестарт", _confirm_restart, nav)
	_button("Карты", _show_maps, nav)
	_button("Правила", _show_rules, nav)
	_button("Сложность", func(): _choose_difficulty(sim.map_id), nav)
	speed_bar = HBoxContainer.new()
	ui.add_child(speed_bar)
	tactical_button = _button("Ⅱ Пауза", _toggle_tactical_pause, speed_bar, Vector2(130, 44))
	tactical_button.tooltip_text = "Пробел · Можно строить, улучшать и продавать башни"
	var tempo = VBoxContainer.new()
	tempo.add_theme_constant_override("separation", 3)
	speed_bar.add_child(tempo)
	speed_value = _label("ТЕМП  ·  1.00×", tempo, 11)
	speed_value.modulate = muted
	speed_slider = HSlider.new()
	speed_slider.focus_mode = Control.FOCUS_NONE
	speed_slider.custom_minimum_size = Vector2(220, 30)
	speed_slider.min_value = 0.25
	speed_slider.max_value = 5.0
	speed_slider.step = 0.05
	speed_slider.value = 1.0
	speed_slider.tooltip_text = "Темп боя · 0.25× — 5× · Двойной щелчок: обычная скорость"
	speed_slider.value_changed.connect(func(value): sim.speed = value; _refresh())
	speed_slider.gui_input.connect(func(event):
		if event is InputEventMouseButton and event.double_click:
			speed_slider.value = 1.0)
	tempo.add_child(speed_slider)
	audio_button = null
	wave_label = _label("", ui, 15)
	dock = PanelContainer.new()
	ui.add_child(dock)
	var shop = HBoxContainer.new()
	shop.add_theme_constant_override("separation", 5)
	dock.add_child(shop)
	var balance = VBoxContainer.new()
	balance.custom_minimum_size.x = 100
	shop.add_child(balance)
	_label("КАЗНА", balance, 10).modulate = muted
	coins_label = _label("", balance, 24)
	coins_label.modulate = accent
	for type in TYPES:
		var data = Data.all().towers[type]
		var text = "%s\n%d" % [data.name, data.baseCost]
		var button = _button(text, func(): enter_build(type), shop, Vector2(116, 64))
		_shop_icon(type, button)
		button.add_theme_font_size_override("font_size", 12)
		button.tooltip_text = data.role + "\n" + data.details
		shop_buttons[type] = button
	health_label = _label("", ui, 24)
	health_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tower_panel = PanelContainer.new()
	tower_panel.custom_minimum_size.x = 234
	ui.add_child(tower_panel)
	var rows = VBoxContainer.new()
	tower_panel.add_child(rows)
	var header = HBoxContainer.new()
	rows.add_child(header)
	var titles = VBoxContainer.new()
	titles.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(titles)
	tower_title = _label("", titles, 15)
	tower_stars = _label("", titles, 12)
	tower_stars.modulate = accent
	_button("×", deselect, header, Vector2(44, 44))
	tower_stats = _label("", rows, 13)
	var actions = HBoxContainer.new()
	rows.add_child(actions)
	upgrade_button = _button("", _upgrade, actions, Vector2(132, 44))
	upgrade_button.add_theme_font_size_override("font_size", 12)
	sell_button = _button("", _sell, actions, Vector2(132, 44))
	sell_button.add_theme_font_size_override("font_size", 12)
	tower_panel.hide()

func _toggle_tactical_pause() -> void:
	if sim == null or _active_dialog != null:
		return
	sim.paused = not sim.paused
	_refresh()

func _confirm_restart() -> void:
	if sim == null or _loading: return
	var id = sim.map_id
	var difficulty_id = save_store.data.difficulty[id]
	var rows = _dialog("Начать карту заново?", 500)
	_label("Волны, казна и башни начнутся с исходного состояния.", rows)
	_button("Отмена", _back_dialog, rows)
	_button("Начать заново", func(): start_game(id, difficulty_id), rows)

func _confirm_exit() -> void:
	var rows = _dialog("Выйти в меню?", 500)
	_label("Текущий прогресс забега будет потерян.", rows)
	_button("Остаться", _back_dialog, rows)
	_button("Выйти", show_menu, rows)

func _toggle_audio() -> void:
	sound.set_enabled(not sound.enabled)
	save_store.data.audio_enabled = sound.enabled
	save_store.save()
	_refresh()

func _refresh() -> void:
	if sim == null or coins_label == null:
		return
	tactical_button.text = "▶ Продолжить" if sim.paused else "Ⅱ Пауза"
	coins_label.text = str(sim.coins)
	wave_label.text = "ВОЛНА  %d / 20" % sim.wave
	health_label.text = str(sim.hp)
	health_label.modulate = Color("f3897e") if sim.hp < sim.max_hp * 0.3 else Color("f0eee4")
	if is_instance_valid(speed_value):
		speed_value.text = "ТЕМП  ·  %.2f×" % sim.speed
	if is_instance_valid(speed_slider):
		speed_slider.set_value_no_signal(sim.speed)
	for type in shop_buttons:
		shop_buttons[type].disabled = sim.coins < Data.all().towers[type].baseCost
		shop_buttons[type].modulate = accent if building == type else Color.WHITE
	if not selected.is_empty() and selected.alive:
		var data = Data.all().towers[selected.type]
		var stats = selected.stats
		tower_title.text = data.name
		tower_stars.text = "★".repeat(selected.level) + "☆".repeat(3 - selected.level)
		var text = ""
		if stats.damage > 0:
			text += "Урон: %d\nСкорость: %.2f/сек\n" % [round(stats.damage), stats.fireRate]
		text += "Дальность: %.1f м" % stats.range
		if stats.get("slowPercent", 0) > 0:
			text += "\nЗамедление: −%d%%" % stats.slowPercent
		if stats.get("buffPercent", 0) > 0:
			text += "\nУсиление: +%d%%" % stats.buffPercent
		tower_stats.text = text
		var cost = Data.upgrade_cost(selected.type, selected.level)
		upgrade_button.text = "Макс.\nуровень" if cost < 0 else "Улучшить (%d)" % cost
		upgrade_button.disabled = cost < 0 or sim.coins < cost
		sell_button.text = "Продать +%d" % Data.sell_price(selected.type, selected.level)
		tower_panel.show()
	else:
		tower_panel.hide()

	if not _hud_visibility.is_empty():
		for child in _hud_visibility:
			if is_instance_valid(child): child.hide()

func _layout() -> void:
	var view = get_viewport().get_visible_rect().size
	if sim == null:
		if is_instance_valid(menu):
			var box = menu.get_node_or_null("MenuBox")
			if box != null:
				box.position = Vector2(view.x * 0.075, maxf(24, (view.y - box.get_combined_minimum_size().y) * 0.5))
		return
	navigation.position = Vector2(18, 14)
	speed_bar.position = Vector2(view.x - speed_bar.get_combined_minimum_size().x - 18, 32)
	wave_label.position = Vector2((view.x - 150) * 0.5, 44)
	dock.position = Vector2((view.x - dock.get_combined_minimum_size().x) * 0.5, view.y - dock.get_combined_minimum_size().y - 14)
	_fit_camera()
	_position_tower_panel()

func _fit_camera() -> void:
	if camera == null or sim == null:
		return
	var view = get_viewport().get_visible_rect().size
	var top = navigation.position.y + navigation.get_combined_minimum_size().y + 10
	var bottom = view.y - dock.position.y + 18
	var usable = max(view.y * 0.35, view.y - top - bottom)
	var tangent = tan(deg_to_rad(45.0) / 2.0)
	var tilt = deg_to_rad(50.0)
	var forward = Vector3(0, -cos(tilt), -sin(tilt))
	var up = Vector3(0, sin(tilt), -cos(tilt))
	var corners: Array[Vector3] = []
	for x in [-55.0, 55.0]:
		for z in [-15.0, 15.0]:
			for y in [0.0, 2.0]:
				corners.append(Vector3(x, y, z))
	for point in sim.waypoints:
		corners.append(point + Vector3.UP * 2.0)
	for spot in sim.spots:
		corners.append(spot.position + Vector3.UP * 2.0)
	corners.append(sim.waypoints[0] + Vector3(-15,22,-7))
	corners.append(sim.waypoints[-1] + Vector3.UP * 18)
	var distance = 20.0
	for point in corners:
		var depth = point.dot(forward)
		distance = max(distance, abs(point.x) / (tangent * view.x / view.y) - depth)
		distance = max(distance, abs(point.dot(up)) / (tangent * usable / view.y) - depth)
	distance /= 0.98
	camera.position = -forward * distance
	camera.look_at(Vector3.ZERO, Vector3.UP)
	camera.v_offset = (top - bottom) / view.y * distance * tangent

func _position_tower_panel() -> void:
	if sim == null or camera == null:
		return
	var base = camera.unproject_position(sim.waypoints[-1] + Vector3.UP * 17)
	health_label.position = base - Vector2(health_label.size.x / 2, health_label.size.y)
	if selected.is_empty() or not selected.alive or not tower_panel.visible:
		return
	var point = camera.unproject_position(selected.position + Vector3.UP * 2)
	var size = tower_panel.get_combined_minimum_size()
	var viewport = get_viewport().get_visible_rect().size
	var top = navigation.position.y + navigation.get_combined_minimum_size().y + 8
	var bottom = dock.position.y - 8
	var best = Vector2.ZERO
	var score = INF
	for candidate in [point + Vector2(24, -size.y / 2), point - Vector2(size.x + 24, size.y / 2), point - Vector2(size.x / 2, size.y + 24), point + Vector2(-size.x / 2, 24)]:
		var pos = Vector2(clampf(candidate.x, 8, viewport.x - size.x - 8), clampf(candidate.y, top, bottom - size.y))
		var distance = Vector2(maxf(maxf(pos.x - point.x, 0), point.x - pos.x - size.x), maxf(maxf(pos.y - point.y, 0), point.y - pos.y - size.y))
		var current = distance.length() + (10000 if distance.x < 18 and distance.y < 18 else 0)
		if current < score:
			score = current
			best = pos
	tower_panel.position = best

func enter_build(type: String) -> void:
	if sim == null or sim.coins < Data.all().towers[type].baseCost:
		return
	if building == type:
		cancel_build()
		return
	cancel_build()
	deselect()
	building = type
	ghost = _model("tower_%s_1" % type)
	world.add_child(ghost)
	_ghost_style(ghost)
	ghost.hide()
	for i in range(spot_nodes.size()):
		var spot = sim.spots[i]
		var valid = _spot_allows(i, type)
		spot_nodes[i].visible = valid
		spot_nodes[i].material_override.albedo_color = Color("44ff66")
	_refresh()

func cancel_build() -> void:
	building = ""
	if is_instance_valid(ghost):
		ghost.queue_free()
	ghost = null
	for i in range(spot_nodes.size()):
		spot_nodes[i].hide()
		spot_nodes[i].material_override.albedo_color = Color("a4c5d5") if sim.spots[i].restricted_to != "" else accent
	_update_range()
	_refresh()

func select_tower(tower: Dictionary) -> void:
	selected = tower
	_update_range()
	_refresh()
	call_deferred("_position_tower_panel")

func deselect() -> void:
	selected = {}
	_update_range()
	_refresh()

func _upgrade() -> void:
	if not selected.is_empty():
		sim.upgrade(selected)
		_update_range()

func _sell() -> void:
	if not selected.is_empty():
		sim.sell(selected)
		deselect()

func _tower_changed(tower: Dictionary, action: String) -> void:
	if tower_nodes.has(tower.id):
		tower_nodes[tower.id].queue_free()
		tower_nodes.erase(tower.id)
	if action != "sell":
		var node = _model("tower_%s_%d" % [tower.type, tower.level])
		node.position = tower.position
		world.add_child(node)
		node.set_meta("turret", node.find_child("turret", true, false))
		tower_nodes[tower.id] = node
	spot_nodes[tower.spot].visible = building != "" and _spot_allows(tower.spot, building)

func _enemy_spawned(enemy: Dictionary) -> void:
	var entry: Dictionary
	if _actor_pool[enemy.type].is_empty():
		entry = _new_actor(enemy.type)
		pool_growth += 1
	else:
		entry = _actor_pool[enemy.type].pop_back()
	entry.node.position = enemy.position + Vector3.UP * enemy.base_y
	entry.node.show()
	entry.bar.show()
	entry.fill.scale.x = 1
	entry.fill.position.x = 0
	entry.previous = enemy.position
	entry.previous_phase = enemy.walk_phase
	enemy_nodes[enemy.id] = entry
	sound.growl(sim.map.enemies[enemy.type].get("isBoss", false))

func _enemy_removed(enemy: Dictionary, rewarded: bool) -> void:
	if not enemy_nodes.has(enemy.id): return
	var entry = enemy_nodes[enemy.id]
	enemy_nodes.erase(enemy.id)
	entry.bar.hide()
	if not rewarded:
		_release_actor(entry)
		return
	var data = sim.map.enemies[enemy.type]
	var spectral = enemy.type in ["soul_eater","blizzard_spirit","blizzard_lord","spire"]
	deaths.append({"entry":entry,"time":0.0,"start":entry.node.position,"rotation":entry.node.rotation,"spectral":spectral,"machine":"ballista" in enemy.type,"flying":data.flying,"base":enemy.base_y,"size":data.size})
	if deaths.size() > 40:
		_release_actor(deaths[0].entry)
		deaths.pop_front()
	fx.death(enemy.position + Vector3.UP * enemy.base_y,enemy.type,data.size,data.flying)
	fx.reward(enemy.position + Vector3.UP * enemy.base_y,data.get("isBoss",false))
	sound.death()

func _transparency(node: Node, value: float) -> void:
	if node is GeometryInstance3D:
		node.transparency = clampf(value, 0.0, 1.0)
	for child in node.get_children():
		_transparency(child, value)

func _spot_allows(index: int, type: String) -> bool:
	var spot = sim.spots[index]
	return sim.can_build_at(index) and spot.tower == null and ((spot.restricted_to == "" and type != "sniper") or spot.restricted_to == type)

func _floor_point(screen: Vector2):
	return Plane(Vector3.UP, 0).intersects_ray(camera.project_ray_origin(screen), camera.project_ray_normal(screen))

func _tower_at(screen: Vector2) -> Dictionary:
	var best: Dictionary = {}
	var distance = 24.0
	for tower in sim.towers:
		var point = camera.unproject_position(tower.position + Vector3.UP * 2.0)
		var current = screen.distance_to(point)
		if current < distance:
			distance = current
			best = tower
	return best

func _spot_at(screen: Vector2) -> int:
	var floor_point = _floor_point(screen)
	if floor_point == null:
		return -1
	var best = -1
	var distance = 6.0
	for i in range(sim.spots.size()):
		if not _spot_allows(i, building):
			continue
		var current = sim.spots[i].position.distance_to(floor_point)
		if current < distance:
			distance = current
			best = i
	return best

func _canvas_click(screen: Vector2) -> void:
	if building != "":
		var spot = _spot_at(screen)
		if spot >= 0:
			var built = sim.build(building, spot)
			if not built.is_empty():
				cancel_build()
				select_tower(built)
				return
	var tower = _tower_at(screen)
	if not tower.is_empty():
		cancel_build()
		select_tower(tower)
		return
	if building != "":
		cancel_build()
	deselect()

func _pointer_move(screen: Vector2) -> void:
	if building != "" and is_instance_valid(ghost):
		var index = _spot_at(screen)
		ghost.visible = index >= 0
		if index >= 0:
			ghost.position = sim.spots[index].position
			_draw_range(ghost.position, Data.stats(building, 1).range, Color("64d8b1"))
		else:
			_hide_range()
		return
	var tower = _tower_at(screen)
	if tower != hovered:
		hovered = tower
		_update_range()

func _unhandled_input(event: InputEvent) -> void:
	if sim == null or _active_dialog != null or _loading:
		return
	if event is InputEventMouseMotion:
		if event.position.distance_to(_gesture_start) > 20:
			_gesture_moved = true
		_pointer_move(event.position)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_gesture_start = event.position
			_gesture_moved = false
		else:
			if not _gesture_moved and event.position.distance_to(_gesture_start) <= 20:
				_canvas_click(event.position)
	elif event is InputEventScreenTouch:
		if event.pressed:
			_touches[event.index] = event.position
			if _touches.size() > 1:
				_multitouch = true
			else:
				_multitouch = false
				_gesture_start = event.position
				_gesture_time = Time.get_ticks_msec()
				_gesture_moved = false
		else:
			_touches.erase(event.index)
			if not event.canceled and not _multitouch and not _gesture_moved and Time.get_ticks_msec() - _gesture_time < 500 and event.position.distance_to(_gesture_start) <= 20:
				_canvas_click(event.position)
	elif event is InputEventScreenDrag:
		if event.position.distance_to(_gesture_start) > 20:
			_gesture_moved = true
		_pointer_move(event.position)

func _input(event: InputEvent) -> void:
	if _loading: return
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode in [KEY_ESCAPE, KEY_SPACE, KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]:
		get_viewport().set_input_as_handled()
	if event.keycode == KEY_ESCAPE:
		if _active_dialog != null:
			_back_dialog()
		elif sim != null:
			_show_pause_menu()
		return
	if event.keycode == KEY_SPACE:
		_toggle_tactical_pause()
	elif event.keycode in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN] and sim != null and _active_dialog == null:
		speed_slider.value += .25 if event.keycode in [KEY_RIGHT, KEY_UP] else -.25

func _ghost_style(node: Node) -> void:
	if node is MeshInstance3D: node.material_override = _ghost_material
	for child in node.get_children(): _ghost_style(child)

func _hide_range() -> void:
	if is_instance_valid(range_mesh): range_mesh.hide()

func _update_range() -> void:
	if sim == null:
		return
	var tower = selected if not selected.is_empty() else hovered
	if building == "" and not tower.is_empty() and tower.alive:
		_draw_range(tower.position, tower.stats.range, Color("66a4cc"))
	elif building == "":
		_hide_range()

func _draw_range(position: Vector3, radius: float, color: Color) -> void:
	if not is_instance_valid(range_mesh):
		if _unit_range == null:
			_unit_range = ImmediateMesh.new()
			_unit_range.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
			for i in range(97):
				var angle = float(i)/96.0*TAU
				_unit_range.surface_add_vertex(Vector3(cos(angle),.15,sin(angle)))
			_unit_range.surface_end()
		range_mesh = _mesh(_unit_range,color,true)
		range_mesh.material_override.no_depth_test = true
		world.add_child(range_mesh)
	range_mesh.position = position
	range_mesh.scale = Vector3(radius,1,radius)
	range_mesh.material_override.albedo_color = color
	range_mesh.show()

func _beam(start: Vector3, end: Vector3, color: Color, _duration: float = .15) -> void:
	fx.lightning(start,end,color)

func _effect(event: Dictionary) -> void:
	match event.kind:
		"base_damage": sound.scream()
		"bullet", "mortar":
			sound.shoot(event.tower.type)
			fx.track(event)
			_recoil[event.tower.id] = .24 if event.kind == "mortar" else .10
		"beam":
			if event.has("tower"):
				sound.shoot("skyguard")
				fx.lightning(event.start,event.end,event.color)
			else:
				sound.shoot("sniper")
				fx.streak(event.start,event.end,event.color)
		"karma": fx.lightning(event.position + Vector3.UP*8,event.position,Color("ffe4a8"))
		"impact": fx.impact(event.position,event.color)
		"explosion": fx.impact(event.position,event.get("color",Color("ffaa54")),true,event.get("radius",1.4))
		"lava", "ring": fx.ring_at(event.position,event.get("radius",1.0),event.get("color",Color("b85931")),event.get("duration",.6))

func _coin_burst(position: Vector3, count: int) -> void:
	fx.reward(position,count>8)

func _completed(won: bool) -> void:
	save_store.record(sim.map_id, sim.wave, sim.hp, sim.kills, won)
	var rows = _dialog("ПОБЕДА!" if won else "ПОРАЖЕНИЕ", 540)
	if won:
		_label("★".repeat(3 if sim.hp >= 20 else (2 if sim.hp >= 10 else 1)), rows, 36)
	_label("Волны: %d / 20 · Убийств: %d · Здоровье: %d" % [sim.wave, sim.kills, sim.hp], rows)
	_button("Ещё раз", func(): start_game(sim.map_id, sim.difficulty.key), rows)
	_button("Выбрать карту", _show_maps, rows)
	_button("Главное меню", show_menu, rows)

func _physics_process(delta: float) -> void:
	if sim != null and _active_dialog == null and not _loading:
		for enemy in sim.enemies:
			if enemy_nodes.has(enemy.id):
				enemy_nodes[enemy.id].previous = enemy.position
				enemy_nodes[enemy.id].previous_phase = enemy.walk_phase
		sim.tick(min(delta, 0.1))

func _process(delta: float) -> void:
	if sim != null and camera != null and not _loading:
		var game_delta = max(0.0, sim.game_time - _last_time)
		_last_time = sim.game_time
		var interpolation = 1.0 if sim.paused or _active_dialog != null else Engine.get_physics_interpolation_fraction()
		for enemy in sim.enemies:
			if not enemy_nodes.has(enemy.id):
				continue
			var entry = enemy_nodes[enemy.id]
			var data = sim.map.enemies[enemy.type]
			var phase = lerpf(entry.get("previous_phase",enemy.walk_phase),enemy.walk_phase,interpolation)
			for joint in entry.joints:
				if joint.role == 0: joint.node.rotation.x = sin(phase)*.32*joint.sign
				elif joint.role == 1: joint.node.rotation.x = -sin(phase)*.20*joint.sign
				elif joint.role == 2: joint.node.rotation.z = sin(phase)*.32*joint.sign
				elif joint.role == 3: joint.node.rotation.y = sin(phase*.35)*.06
				elif joint.role == 4: joint.node.scale.y = 1+sin(phase*.5)*.012
			var visual_position = entry.get("previous",enemy.position).lerp(enemy.position,interpolation)
			entry.node.position = visual_position + Vector3.UP * (enemy.base_y + (sin(phase) if data.flying else abs(sin(phase))) * data.walk.bobAmp * data.size)
			var direction = sim.waypoints[enemy.path_index + 1] - sim.waypoints[enemy.path_index]
			entry.node.rotation = Vector3(cos(phase * 2) * data.walk.get("leanAmp", 0.02), atan2(direction.x, direction.z), sin(phase) * data.walk.swayAmp * data.size)
			var body_height = 1.9 if enemy.type == "hound" else 1.75 if "ballista" in enemy.type else 3.4
			entry.bar.position = visual_position + Vector3.UP * (body_height * data.size * data.get("visualScale",1.0) + 0.45 + (enemy.base_y - data.size * 0.35 if data.flying else 0.0))
			entry.bar.quaternion = camera.quaternion
			var ratio = clampf(enemy.hp / enemy.max_hp, 0.001, 1.0)
			entry.fill.scale.x = ratio
			entry.fill.position.x = -(1.0 - ratio)
		for tower in sim.towers:
			if not tower_nodes.has(tower.id):
				continue
			var turret = tower_nodes[tower.id].get_meta("turret", null)
			if turret != null and tower.has("target") and not tower.target.is_empty() and tower.target.alive:
				turret.rotation.y = tower.angle
			if turret != null and tower.type == "amp":
				turret.rotation.y += game_delta * 1.5
		for tower in sim.towers:
			if not _recoil.has(tower.id): continue
			_recoil[tower.id] = move_toward(_recoil[tower.id],0,game_delta*.8)
			var turret = tower_nodes[tower.id].get_meta("turret",null)
			if turret != null:
				turret.position = -Vector3(sin(tower.angle),0,cos(tower.angle))*_recoil[tower.id]
		var index = 0
		while index < deaths.size():
			var death = deaths[index]
			death.time += minf(game_delta,.15)
			var t = death.time
			var node = death.entry.node
			if death.spectral:
				node.scale = Vector3.ONE*maxf(.01,1-t/.9)
				node.position = death.start + Vector3.UP*t*1.5
			else:
				var collapse = smoothstep(0,.75,t)
				node.rotation.x = death.rotation.x + collapse*(.12 if death.machine else 1.40)
				node.rotation.z = death.rotation.z + collapse*(.27 if death.machine else .10)
				node.position.y = lerpf(death.start.y,death.base*.24,collapse)
				for joint in death.entry.joints:
					if joint.role == 1: joint.node.rotation.x = collapse*.65
					elif joint.role == 0: joint.node.rotation.x = collapse*-.35
					elif joint.role == 3: joint.node.rotation.x = collapse*.35
				if t > 5.0: node.position.y -= smoothstep(5,7,t)*death.size*3.2
			if t >= (.9 if death.spectral else 7.0):
				_release_actor(death.entry)
				deaths.remove_at(index)
			else: index += 1
		fx.render(0 if sim.paused or _active_dialog != null else minf(delta,.05),interpolation)
		_position_tower_panel()
		if Engine.get_process_frames() < 8:
			_layout()
	if _screenshot_path != "" and not _loading:
		_screenshot_timer -= delta
		if _screenshot_timer <= 0:
			var destination = _screenshot_path
			_screenshot_path = ""
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(destination)
			_quit_game()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		_quit_game()

func _quit_game() -> void:
	if sound != null:
		sound.set_enabled(false)
	await get_tree().create_timer(.12).timeout
	get_tree().quit()

func _shop_icon(type: String, button: Button) -> void:
	button.text = ""
	var row = HBoxContainer.new()
	row.position = Vector2(4, 6)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	button.add_child(row)
	var container = SubViewportContainer.new()
	container.custom_minimum_size = Vector2(30, 48)
	container.stretch = true
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(container)
	var viewport = SubViewport.new()
	viewport.size = Vector2i(60, 96)
	viewport.transparent_bg = true
	viewport.own_world_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ONCE
	container.add_child(viewport)
	var model = _model("tower_%s_1" % type)
	viewport.add_child(model)
	var icon_camera = Camera3D.new()
	icon_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	icon_camera.size = 5.8
	icon_camera.position = Vector3(5, 5, 7)
	viewport.add_child(icon_camera)
	icon_camera.look_at(Vector3(0, 1.6, 0))
	var light = DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-45, -35, 0)
	light.light_energy = 1.8
	viewport.add_child(light)
	var environment = WorldEnvironment.new()
	var settings = Environment.new()
	settings.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	settings.ambient_light_color = Color.WHITE
	settings.ambient_light_energy = 0.8
	environment.environment = settings
	viewport.add_child(environment)
	var labels = VBoxContainer.new()
	labels.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(labels)
	var data = Data.all().towers[type]
	var name_label = _label(data.name.replace("Небесный страж", "Небесный\nстраж"), labels, 10)
	name_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var cost = _label(str(int(data.baseCost)), labels, 13)
	cost.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cost.modulate = accent
