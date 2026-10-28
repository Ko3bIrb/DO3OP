extends Node

var enabled = true
var _players: Array[AudioStreamPlayer] = []
var _files = {"roar": preload("res://assets/audio/the_monster_roar.wav"), "exit": preload("res://assets/audio/the_monsters_exit.wav"), "scream": preload("res://assets/audio/scream.wav")}
var _last_shoot = -10000
var _last_death = -10000
var _last_roar = -10000
var _last_scream = -10000
var _shot: AudioStreamWAV
var _death: AudioStreamWAV
var _weapons: Dictionary = {}

func _ready() -> void:
	for key in ["gun","sniper","mortar","skyguard"]: _weapons[key] = _weapon(key)
	_shot = _weapons.gun
	_death = _weapon("death")
	for i in range(12):
		var player = AudioStreamPlayer.new()
		add_child(player)
		_players.append(player)

func _weapon(kind: String) -> AudioStreamWAV:
	var stream = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 22050
	var duration = .30 if kind == "mortar" else .18 if kind == "sniper" else .11
	var random = RandomNumberGenerator.new()
	random.seed = kind.hash()
	var bytes = PackedByteArray()
	var low = 0.0
	for i in range(int(22050*duration)):
		var t = float(i)/22050.0
		var noise = random.randf_range(-1,1)
		low = lerpf(low,noise,.12 if kind == "mortar" else .35)
		var decay = exp(-t*(15 if kind == "mortar" else 35 if kind == "sniper" else 50))
		var thump = sin(TAU*(65 if kind == "mortar" else 130)*t)*exp(-t*28)
		var value = (low*.6+noise*.14+thump*.28)*decay
		if kind == "skyguard": value = noise*.23*exp(-t*45)+sin(t*TAU*1800)*.06*exp(-t*70)
		if kind == "death": value = low*.35*exp(-t*32)+sin(t*TAU*80)*.12*exp(-t*35)
		var sample = int(clampf(value,-1,1)*12000)
		bytes.append(sample&255)
		bytes.append((sample>>8)&255)
	stream.data = bytes
	return stream

func _play(stream: AudioStream, volume: float, pitch: float = 1.0) -> void:
	if not enabled:
		return
	for player in _players:
		if not player.playing:
			player.stream = stream
			player.volume_db = linear_to_db(max(0.0001, volume))
			player.pitch_scale = pitch
			player.play()
			return

func shoot(type: String = "gun") -> void:
	var now = Time.get_ticks_msec()
	if now - _last_shoot >= 150:
		_last_shoot = now
		_play(_weapons.get(type,_shot), 1.0, randf_range(0.94, 1.06))

func death() -> void:
	var now = Time.get_ticks_msec()
	if now - _last_death >= 100:
		_last_death = now
		_play(_death, 1.0)

func wave_start() -> void:
	_play(_files.exit, 0.3)

func growl(boss: bool = false) -> void:
	var now = Time.get_ticks_msec()
	if boss or now - _last_roar >= 6000:
		_last_roar = now
		_play(_files.roar, 0.42 if boss else 0.12, 0.75 if boss else 0.92)

func scream() -> void:
	var now = Time.get_ticks_msec()
	if now - _last_scream >= 2000:
		_last_scream = now
		_play(_files.scream, 0.24)

func set_enabled(value: bool) -> void:
	enabled = value
	if not value:
		for player in _players:
			player.stop()
			player.stream = null

func _exit_tree() -> void:
	for player in _players:
		player.stop()
		player.stream = null
	_players.clear()
