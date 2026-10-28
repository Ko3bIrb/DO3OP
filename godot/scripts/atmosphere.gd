extends Node3D

var _time = 0.0
var _flames: Array = []
var _breathing: Array = []
var _menu = false

static func setup(scene: Node3D, id: String) -> void:
 var atmosphere = load("res://scripts/atmosphere.gd").new()
 scene.add_child(atmosphere)
 atmosphere.configure(scene, id)

func _light(parent: Node3D, at: Vector3, color: Color, energy: float, radius: float, shadows: bool = false) -> void:
 var light = OmniLight3D.new()
 light.position = at
 light.light_color = color
 light.light_energy = energy
 light.omni_range = radius
 light.omni_attenuation = 1.3
 light.light_size = 0.35
 light.shadow_enabled = shadows
 light.shadow_bias = 0.08
 parent.add_child(light)
 _flames.append({"light": light, "energy": energy, "phase": at.x + at.z})

func configure(scene: Node3D, id: String) -> void:
 _menu = id == "menu"
 var winter = id != "hell"
 var environment = WorldEnvironment.new()
 var settings = Environment.new()
 settings.background_mode = Environment.BG_SKY
 var sky = Sky.new()
 var sky_material = ProceduralSkyMaterial.new()
 sky_material.sky_top_color = Color("101e37") if winter else Color("180d14")
 sky_material.sky_horizon_color = Color("3e4d68") if winter else Color("5b261d")
 sky_material.ground_bottom_color = Color("101925")
 sky_material.ground_horizon_color = sky_material.sky_horizon_color
 sky_material.sky_curve = 0.20
 sky_material.sun_angle_max = 2.0
 sky.sky_material = sky_material
 settings.sky = sky
 settings.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
 settings.ambient_light_color = Color("8197b9") if winter else Color("bd5731")
 settings.ambient_light_energy = 0.30 if winter else 0.24
 settings.reflected_light_source = 1
 settings.tonemap_mode = Environment.TONE_MAPPER_AGX
 settings.tonemap_exposure = 0.95
 settings.ssao_enabled = true
 settings.ssao_radius = 2.5
 settings.ssao_intensity = 1.5
 settings.ssil_enabled = true
 settings.ssil_intensity = 0.6
 settings.glow_enabled = true
 settings.glow_intensity = 0.65
 settings.glow_bloom = 0.03
 settings.glow_hdr_threshold = 1.5
 settings.fog_enabled = true
 settings.fog_light_color = Color("465c7b") if winter else Color("63301c")
 settings.fog_density = 0.0009 if not _menu else 0.007
 settings.fog_sun_scatter = 0.12
 settings.volumetric_fog_enabled = true
 settings.volumetric_fog_density = 0.006 if _menu else 0.0008
 settings.volumetric_fog_albedo = Color("b6c4d2") if winter else Color("9c4a27")
 settings.volumetric_fog_sky_affect = 0.3
 environment.environment = settings
 scene.add_child(environment)
 var moon = DirectionalLight3D.new()
 moon.name = "Moonlight"
 moon.light_color = Color("bfd6f3") if winter else Color("e78c54")
 moon.light_energy = 0.46 if winter else 0.34
 moon.rotation_degrees = Vector3(-38, -32, 0)
 moon.shadow_enabled = true
 moon.light_angular_distance = 2.0
 moon.directional_shadow_max_distance = 300.0
 moon.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
 scene.add_child(moon)
 var rim = DirectionalLight3D.new()
 rim.rotation_degrees = Vector3(-23, 145, 0)
 rim.light_color = Color("d4ad92") if winter else Color("ee4822")
 rim.light_energy = 0.14
 scene.add_child(rim)
 if _menu:
  _light(scene, Vector3(3.4, 1.0, 1.8), Color("ffb367"), 5.0, 9, true)
  _light(scene, Vector3(4.3, 2.25, 0.9), Color("ffdb9b"), 2.3, 7, true)
  _light(scene, Vector3(0, 3, -4), Color("7babc9"), 3.2, 12)
  _breathing = scene.find_children("motion_torso", "Node3D", true, false)
  _snow(scene, true)
 else:
  var data = JSON.parse_string(FileAccess.get_file_as_string("res://data/game_data.json")).maps[id]
  var route = data.waypoints
  var scenery = JSON.parse_string(FileAccess.get_file_as_string("res://data/landscapes.json"))[id]
  for i in range(scenery.get("lanterns",[]).size()):
   var p = scenery.lanterns[i]
   _light(scene,Vector3(p[0],p[1],p[2]),Color("ffca8b"),3.2,10,i%4==0)
  for p in scenery.get("homes",[]):
   _light(scene,Vector3(p[0],p[1],p[2]),Color("ffd39a"),1.8,7)
  for i in range(mini(14,scenery.fires.size())):
   var p=scenery.fires[i]
   _light(scene,Vector3(p[0],p[1]+1,p[2]),Color("ff9b4c"),4.5,12,i<4)
  if winter:
   _light(scene,Vector3(0,2,-25),Color("6eabbc"),2.5,23)
   settings.ssr_enabled = true
  else:
   for at in [Vector3(-3,1,3),Vector3(-4,1,-21),Vector3(-10,25,-52)]:
    _light(scene,at,Color("ff6a24"),5.0,24)
  var castle = Vector3(route[-1][0], 0, route[-1][2])
  for offset in [Vector3(-4,3,-3), Vector3(-4,3,3), Vector3(1,6,0)]:
   _light(scene, castle + offset, Color("ffd3a0"), 4.0, 13, true)
  var portal = Vector3(route[0][0], 3.5, route[0][2])
  _light(scene, portal, Color("82c6dd") if winter else Color("e8885b"), 5, 16)
  if not winter:
   for at in [Vector3(-26, 1, 25), Vector3(25,1,-29), Vector3(0,1,-16)]:
    _light(scene, at, Color("f09a68"), 3.2, 16)
  _snow(scene, winter)

func _snow(scene: Node3D, winter: bool) -> void:
 var particles = GPUParticles3D.new()
 particles.name = "Drifting snow" if winter else "Floating ash"
 particles.amount = 900 if _menu else 1300 if winter else 350
 particles.lifetime = 18
 particles.preprocess = 5
 particles.visibility_aabb = AABB(Vector3(-120,-20,-100), Vector3(240,100,200))
 var process = ParticleProcessMaterial.new()
 process.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
 process.emission_box_extents = Vector3(22,12,22) if _menu else Vector3(90,16,55)
 process.direction = Vector3(0.2,-1,0.12) if winter else Vector3(.12,1,.07)
 process.spread = 18
 process.gravity = Vector3(0,-0.02,0) if winter else Vector3(0,.015,0)
 process.initial_velocity_min = 0.6 if winter else 0.15
 process.initial_velocity_max = 1.1 if winter else 0.35
 process.scale_min = 0.015 if _menu else 0.025
 process.scale_max = 0.045 if _menu else .07 if winter else .035
 process.color = Color("bfccd6") if winter else Color("ff6f18")
 particles.process_material = process
 particles.position.y = 12
 var quad = QuadMesh.new()
 quad.size = Vector2.ONE
 var material = StandardMaterial3D.new()
 material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
 material.billboard_keep_scale = true
 material.vertex_color_use_as_albedo = true
 material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
 material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
 material.albedo_color = Color(1,1,1,0.55) if winter else Color(1,.32,.04,.65)
 # Rounded flakes with soft, transparent edges.
 var image = Image.create(32,32,false,Image.FORMAT_RGBA8)
 for y in range(32):
  for x in range(32):
   var distance = Vector2(x-15.5,y-15.5).length() / 15.5
   image.set_pixel(x,y,Color(1,1,1,clampf(1-distance,0,1)*0.7))
 material.albedo_texture = ImageTexture.create_from_image(image)
 quad.material = material
 particles.draw_pass_1 = quad
 scene.add_child(particles)

func _process(delta: float) -> void:
 _time += delta
 for entry in _flames:
  entry.light.light_energy = entry.energy * (1 + sin(_time * 1.7 + entry.phase) * 0.025 + sin(_time * 4.1) * 0.012)
 for torso in _breathing:
  torso.rotation.z = sin(_time * 0.7) * 0.008
  torso.scale.y = 1.0 + sin(_time * 1.6) * 0.006
