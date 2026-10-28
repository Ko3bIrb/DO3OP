extends RefCounted

const Data = preload("res://scripts/game_data.gd")
signal changed
signal tower_changed(tower: Dictionary, action: String)
signal enemy_spawned(enemy: Dictionary)
signal enemy_removed(enemy: Dictionary, rewarded: bool)
signal effect(event: Dictionary)
signal wave_started
signal completed(won: bool)

var map_id = "hell"
var map: Dictionary
var difficulty: Dictionary
var hp = 20
var max_hp = 20
var coins = 200
var wave = 0
var phase = "prep"
var prep_timer = 10.0
var speed = 1.0
var paused = false
var game_time = 0.0
var wave_start = 0.0
var wave_leaked = 0
var kills = 0
var spots: Array = []
var waypoints: Array[Vector3] = []
var towers: Array = []
var enemies: Array = []
var projectiles: Array = []
var queue: Array = []
var spawn_index = 0
var _next_id = 0
var _recorded = false

func setup(id: String, difficulty_id: String) -> void:
	map_id = id
	map = Data.all().maps[id]
	difficulty = Data.all().difficulty[difficulty_id]
	max_hp = int(difficulty.hp)
	hp = max_hp
	coins = int(difficulty.coins)
	for point in map.waypoints:
		waypoints.append(Data.vector(point))
	for item in map.spots:
		spots.append({"position": Data.vector(item.position), "restricted_to": item.restricted_to, "tower": null})

# Road half-width 1.75, terrace radius 1.4, with a safety gap.
func can_build_at(index: int) -> bool:
	if index < 0 or index >= spots.size(): return false
	var p = Vector2(spots[index].position.x, spots[index].position.z)
	for i in range(waypoints.size() - 1):
		var a = Vector2(waypoints[i].x, waypoints[i].z)
		var b = Vector2(waypoints[i+1].x, waypoints[i+1].z)
		if p.distance_to(Geometry2D.get_closest_point_to_segment(p, a, b)) < 3.4:
			return false
	return true

func build(type: String, index: int) -> Dictionary:
	if phase in ["win", "lose"] or not Data.all().towers.has(type) or index < 0 or index >= spots.size():
		return {}
	var spot = spots[index]
	var restricted = spot.restricted_to
	if not can_build_at(index) or spot.tower != null or (restricted != "" and restricted != type) or (restricted == "" and type == "sniper"):
		return {}
	var cost = int(Data.all().towers[type].baseCost)
	if coins < cost:
		return {}
	coins -= cost
	_next_id += 1
	var tower = {"id": _next_id, "type": type, "level": 1, "position": spot.position, "spot": index, "stats": Data.stats(type, 1), "cooldown": 0.0, "buff": 0.0, "shots": 0, "pulse": 0.0, "alive": true, "angle": 0.0}
	towers.append(tower)
	spot.tower = tower
	tower_changed.emit(tower, "build")
	changed.emit()
	return tower

func upgrade(tower: Dictionary) -> bool:
	if tower.is_empty() or not tower.alive or tower.level >= 3:
		return false
	var cost = Data.upgrade_cost(tower.type, tower.level)
	if coins < cost:
		return false
	coins -= cost
	tower.level += 1
	tower.stats = Data.stats(tower.type, tower.level)
	tower_changed.emit(tower, "upgrade")
	changed.emit()
	return true

func sell(tower: Dictionary) -> bool:
	if tower.is_empty() or not tower.alive:
		return false
	coins += Data.sell_price(tower.type, tower.level)
	tower.alive = false
	spots[tower.spot].tower = null
	towers.erase(tower)
	tower_changed.emit(tower, "sell")
	changed.emit()
	return true

func start_wave() -> void:
	if phase != "prep":
		return
	wave += 1
	phase = "wave"
	wave_start = game_time
	wave_leaked = 0
	queue.clear()
	spawn_index = 0
	var time = 0.0
	for group in map.waves[wave - 1].groups:
		for i in range(int(group.count)):
			queue.append({"type": group.type, "time": time})
			time += float(map.gaps.get(group.type, 1.0))
		time += float(map.group_gap)
	wave_started.emit()
	changed.emit()

func spawn(type: String, hp_override: float = -1.0) -> Dictionary:
	var data = map.enemies[type]
	_next_id += 1
	var health = float(Data.js_round(data.baseHp * pow(1.15, max(0, wave - 1)) * difficulty.enemyHpMul)) if hp_override < 0 else hp_override
	var enemy = {"id": _next_id, "type": type, "hp": health, "max_hp": health, "speed": data.speed * difficulty.enemySpeedMul, "armor": data.armor, "flying": data.flying, "position": waypoints[0], "path_index": 0, "progress": 0.0, "base_y": 1.6 if data.flying else max(0.6, data.size * 0.75), "alive": true, "slow_factor": 0.0, "slow_until": 0.0, "stun_until": 0.0, "summon_at": 0.0, "step_at": 0.0, "buff_at": 0.0, "siege_at": 0.0, "buff_until": 0.0, "walk_phase": randf() * TAU}
	enemies.append(enemy)
	enemy_spawned.emit(enemy)
	return enemy

func remove_enemy(enemy: Dictionary, rewarded: bool) -> void:
	if not enemy.alive:
		return
	enemy.alive = false
	var data = map.enemies[enemy.type]
	if rewarded:
		coins += Data.js_round(data.reward * difficulty.rewardMul)
		kills += 1
		if data.has("healOnDeath"):
			for other in enemies:
				if other.alive and other.position.distance_to(enemy.position) <= data.healOnDeath.radius:
					other.hp = min(other.max_hp, other.hp + data.healOnDeath.amount)
	if data.has("lavaOnDeath"):
		effect.emit({"kind": "lava", "position": enemy.position, "radius": data.lavaOnDeath.radius, "duration": data.lavaOnDeath.duration})
	if data.has("explosionOnDeath"):
		effect.emit({"kind": "explosion", "position": enemy.position, "color": Color("ff3bff") if map_id == "hell" else Color("88ccff"), "radius": 1.5})
	enemies.erase(enemy)
	enemy_removed.emit(enemy, rewarded)
	changed.emit()

func tick(real_delta: float) -> void:
	if paused or phase in ["win", "lose"]:
		return
	step(real_delta * float(speed) * 3.0)

func step(delta: float) -> void:
	if phase in ["win", "lose"]:
		return
	game_time += delta
	if phase == "prep":
		prep_timer -= delta
		if prep_timer <= 0:
			start_wave()
	elif phase == "wave":
		while spawn_index < queue.size() and queue[spawn_index].time <= game_time - wave_start:
			spawn(queue[spawn_index].type)
			spawn_index += 1
		if spawn_index >= queue.size() and enemies.is_empty():
			coins += Data.js_round((30 + 5 * wave) * difficulty.waveBonusMul)
			if wave_leaked == 0:
				coins += Data.js_round(20 * difficulty.waveBonusMul)
			if wave >= 20:
				_finish(true)
			else:
				phase = "prep"
				prep_timer = 15.0 if wave % 10 == 0 else 10.0
			changed.emit()
	_update_enemies(delta)
	_update_towers(delta)
	_update_projectiles(delta)

func _finish(won: bool) -> void:
	phase = "win" if won else "lose"
	if not _recorded:
		_recorded = true
		completed.emit(won)
	changed.emit()

func _nearest_tower(position: Vector3, radius: float) -> Dictionary:
	var nearest: Dictionary = {}
	var distance = radius
	for tower in towers:
		var d = tower.position.distance_to(position)
		if d < distance:
			distance = d
			nearest = tower
	return nearest

func _update_enemies(delta: float) -> void:
	var current = enemies.duplicate()
	current.reverse()
	for enemy in current:
		if not enemy.alive:
			continue
		var data = map.enemies[enemy.type]
		if data.has("aura"):
			for other in enemies:
				if other != enemy and other.alive and other.position.distance_to(enemy.position) <= data.aura.radius:
					other.hp = min(other.max_hp, other.hp + data.aura.healPerSec * delta)
		if data.has("summon") and game_time >= enemy.summon_at:
			for i in range(int(data.summon.count)):
				var child = spawn(data.summon.type)
				child.path_index = enemy.path_index
				child.progress = max(0, enemy.progress - 0.02 * i)
				child.position = enemy.position
			enemy.summon_at = game_time + data.summon.cooldown
		if data.has("stepDamage") and game_time >= enemy.step_at:
			var near = _nearest_tower(enemy.position, data.stepDamage.radius)
			if not near.is_empty():
				near.cooldown = max(near.cooldown, game_time + data.stepDamage.towerStun)
				effect.emit({"kind": "explosion", "position": enemy.position, "color": Color("ff3b3b") if map_id == "hell" else Color("88ccff"), "radius": 1.5})
			enemy.step_at = game_time + data.stepDamage.cooldown
		if data.has("buffSpeed") and game_time >= enemy.buff_at:
			for other in enemies:
				if other != enemy and other.alive and other.flying == data.buffSpeed.targetFlying and other.position.distance_to(enemy.position) <= data.buffSpeed.radius:
					other.speed *= data.buffSpeed.mul
					other.buff_until = game_time + 3.0
			enemy.buff_at = game_time + 4.0
		if enemy.buff_until > 0 and game_time > enemy.buff_until:
			enemy.speed = data.speed * difficulty.enemySpeedMul
			enemy.buff_until = 0.0
		var velocity = enemy.speed
		if game_time < enemy.slow_until and not data.get("slowImmune", false):
			velocity *= 1.0 - enemy.slow_factor
		if game_time < enemy.stun_until:
			velocity = 0.0
		if data.has("siege"):
			var near = _nearest_tower(enemy.position, data.siege.stopRange)
			if not near.is_empty() and game_time >= enemy.siege_at:
				near.cooldown = max(near.cooldown, game_time + data.siege.towerStun)
				enemy.siege_at = game_time + 1.0 / data.siege.fireRate
				effect.emit({"kind": "beam", "start": enemy.position + Vector3.UP * enemy.base_y, "end": near.position + Vector3.UP * 1.6, "color": Color("ff3b3b") if map_id == "hell" else Color("88ccff")})
		if velocity > 0:
			var length = waypoints[enemy.path_index].distance_to(waypoints[enemy.path_index + 1])
			enemy.progress += velocity * delta / length
			while enemy.progress >= 1.0:
				enemy.progress -= 1.0
				enemy.path_index += 1
				if enemy.path_index >= waypoints.size() - 1:
					wave_leaked += 1
					hp = max(0, hp - int(data.damage))
					effect.emit({"kind": "base_damage"})
					remove_enemy(enemy, false)
					if hp == 0:
						_finish(false)
					break
		if not enemy.alive:
			continue
		enemy.position = waypoints[enemy.path_index].lerp(waypoints[enemy.path_index + 1], enemy.progress)
		enemy.walk_phase += delta * (2.2 if data.flying else float(data.walk.bobFreq) * clampf(velocity / data.speed, 0.15, 1.5))

func target_for(tower: Dictionary) -> Dictionary:
	var best: Dictionary = {}
	var score = -INF
	var data = Data.all().towers[tower.type]
	for enemy in enemies:
		if not enemy.alive or (enemy.flying and not data.canHitAir):
			continue
		if data.get("priority", "progress") == "air" and not enemy.flying:
			continue
		var distance = enemy.position.distance_squared_to(tower.position)
		if distance > pow(tower.stats.range, 2) or distance < pow(tower.stats.get("minRange", 0), 2):
			continue
		var candidate = (enemy.path_index + enemy.progress) * 1000000 + enemy.hp
		if candidate > score:
			score = candidate
			best = enemy
	return best

func _armor(damage: float, enemy: Dictionary, pierce: float = 0.0) -> float:
	return damage * (1.0 - max(0.0, enemy.armor * (1.0 - pierce)))

func _update_towers(delta: float) -> void:
	for tower in towers:
		tower.buff = 0.0
		if tower.type != "amp":
			for other in towers:
				if other.type == "amp" and tower.position.distance_squared_to(other.position) <= pow(other.stats.range, 2):
					tower.buff += other.stats.buffPercent / 100.0
	for tower in towers:
		if tower.type == "slow":
			var active = false
			for enemy in enemies:
				if enemy.alive and not enemy.flying and not map.enemies[enemy.type].get("slowImmune", false) and enemy.position.distance_squared_to(tower.position) <= pow(tower.stats.range, 2):
					enemy.slow_factor = max(enemy.slow_factor, tower.stats.slowPercent / 100.0)
					enemy.slow_until = game_time + 0.3
					active = true
			if active and game_time >= tower.pulse:
				effect.emit({"kind": "ring", "position": tower.position, "radius": tower.stats.range, "color": Color.CYAN})
				tower.pulse = game_time + 2.5
			continue
		if tower.type == "amp":
			continue
		var target = target_for(tower)
		tower.target = target
		if not target.is_empty():
			var direction = target.position - tower.position
			tower.angle = rotate_toward(tower.angle, atan2(direction.x, direction.z), delta * 12.0)
		if target.is_empty() or game_time < tower.cooldown:
			continue
		var damage = float(tower.stats.damage) * (1.0 + tower.buff)
		var muzzle = Data.vector(Data.all().towers[tower.type].muzzles[tower.level - 1]).rotated(Vector3.UP, tower.angle)
		var start = tower.position + muzzle
		if tower.position.distance_to(target.position) < tower.position.distance_to(start):
			start = tower.position + Vector3.UP * muzzle.y
		var shot = {"kind": "bullet", "active": true, "tower": tower, "target": target, "position": start, "start": start, "end": target.position + Vector3.UP * target.base_y, "color": Color("ffbb33"), "speed": 90.0, "damage": _armor(damage, target), "ttl": 5.0, "progress": 0.0}
		match tower.type:
			"gun":
				projectiles.append(shot)
			"sniper":
				shot.speed = 160.0
				shot.color = Color("44ddff")
				if randf() * 100 < tower.stats.critChance:
					shot.damage *= tower.stats.critMul
					shot.color = Color("ffe070")
				projectiles.append(shot)
			"mortar":
				shot.kind = "mortar"
				shot.destination = target.position
				shot.color = Color("ffaa22")
				projectiles.append(shot)
			"skyguard":
				target.hp -= _armor(damage * (tower.stats.airMul if target.flying else tower.stats.groundMul), target)
				shot.kind = "beam"
				shot.color = Color("ffe070")
				tower.shots += 1
				if tower.shots >= int(tower.stats.karma):
					tower.shots = 0
					for enemy in enemies.duplicate():
						if enemy.alive and enemy.flying and enemy.position.distance_squared_to(tower.position) <= pow(tower.stats.range, 2):
							enemy.hp -= tower.stats.karmaDmg * (1.0 + tower.buff)
							effect.emit({"kind": "karma", "position": enemy.position})
				if target.hp <= 0:
					remove_enemy(target, true)
		effect.emit(shot)
		tower.cooldown = game_time + 1.0 / float(tower.stats.fireRate)

func _discard_projectile(projectile: Dictionary) -> void:
	projectile.active = false
	projectiles.erase(projectile)

func _update_projectiles(delta: float) -> void:
	var bullets = projectiles.filter(func(p): return p.kind == "bullet")
	var mortars = projectiles.filter(func(p): return p.kind == "mortar")
	bullets.reverse()
	mortars.reverse()
	for projectile in bullets + mortars:
		projectile.previous_position = projectile.position
		projectile.ttl -= delta
		if projectile.kind == "mortar":
			projectile.progress += delta * 1.2
			var t = min(1.0, projectile.progress)
			projectile.position = projectile.start.lerp(projectile.end, t) + Vector3.UP * sin(t * PI) * 4.0
			if t >= 1.0:
				var tower = projectile.tower
				# Match the source loop: removing a killed enemy advances past
				# the next array entry during this particular mortar impact.
				var index = 0
				while index < enemies.size():
					var enemy = enemies[index]
					if enemy.alive and not enemy.flying and enemy.position.distance_squared_to(projectile.destination) <= pow(tower.stats.aoe, 2):
						enemy.hp -= _armor(tower.stats.damage * (1.0 + tower.buff), enemy, tower.stats.armorPierce)
						if enemy.hp <= 0:
							remove_enemy(enemy, true)
					index += 1
				effect.emit({"kind": "explosion", "position": projectile.end, "radius": 1.4, "color": Color("ffaa22")})
				_discard_projectile(projectile)
		else:
			if not projectile.target.alive:
				_discard_projectile(projectile)
				continue
			var destination = projectile.target.position + Vector3.UP * projectile.target.base_y
			projectile.end = destination
			if projectile.position.distance_to(destination) <= projectile.speed * delta:
				effect.emit({"kind":"impact", "position":destination, "color":projectile.color})
				projectile.target.hp -= projectile.damage
				if projectile.target.hp <= 0:
					remove_enemy(projectile.target, true)
				_discard_projectile(projectile)
			else:
				projectile.position = projectile.position.move_toward(destination, projectile.speed * delta)
		if projectile.ttl <= 0:
			_discard_projectile(projectile)
