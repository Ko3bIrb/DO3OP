extends Node3D

var _asset_cache: Dictionary = {}
var _materials: Dictionary = {}
var _emitters: Array = []

func configure(scene: Node3D, id: String) -> void:
 var all = JSON.parse_string(FileAccess.get_file_as_string("res://data/landscapes.json"))
 var data = all[id]
 name = "LandscapeLife"
 for part in scene.find_children("*", "MeshInstance3D", true, false):
  for index in range(part.mesh.get_surface_count()):
   var mat = part.get_active_material(index)
   if mat == null: continue
   var key = str(mat.resource_name).replace("_"," ").to_lower()
   if "mountain ground" in key:
    var ground=ShaderMaterial.new()
    ground.shader=preload("res://shaders/terrain.gdshader")
    ground.set_shader_parameter("winter",id=="ice")
    part.set_surface_override_material(index,ground)
    continue
   if "old road stones" in key:
    var paving=ShaderMaterial.new()
    paving.shader=preload("res://shaders/road.gdshader")
    paving.set_shader_parameter("winter",id=="ice")
    part.set_surface_override_material(index,paving)
    continue
   var mode = 0 if "bay water" in key else 1 if "waterfall" in key else 2 if "living lava" in key else -1
   if mode < 0: continue
   if not _materials.has(mode):
    var water = ShaderMaterial.new()
    water.shader = preload("res://shaders/waterfall.gdshader") if mode==1 else preload("res://shaders/landscape.gdshader")
    water.set_shader_parameter("mode",mode)
    _materials[mode] = water
   part.set_surface_override_material(index,_materials[mode])
 var groups: Dictionary = {}
 for item in data.instances:
  if not groups.has(item.key):groups[item.key]=[]
  groups[item.key].append(item)
 for key in groups:
  var source=load("res://assets/models/"+key+".glb").instantiate()
  for part in source.find_children("*","MeshInstance3D",true,false):
   var mm=MultiMesh.new()
   mm.transform_format=MultiMesh.TRANSFORM_3D
   mm.mesh=part.mesh
   mm.instance_count=groups[key].size()
   for i in range(groups[key].size()):
    var prop=groups[key][i]
    var scale=Vector3(prop.scale[0],prop.scale[1],prop.scale[2])
    var basis=Basis(Vector3.UP,float(prop.yaw)).scaled(scale)
    mm.set_instance_transform(i,Transform3D(basis,Vector3(prop.position[0],prop.position[1],prop.position[2]))*part.transform)
   var instance=MultiMeshInstance3D.new()
   instance.name="Instanced_"+key
   instance.multimesh=mm
   instance.visibility_range_end=280
   add_child(instance)
  source.free()
 var flame_material=ShaderMaterial.new()
 flame_material.shader=preload("res://shaders/flame.gdshader")
 for p in data.fires:
  var fire=MeshInstance3D.new()
  fire.mesh=QuadMesh.new()
  fire.mesh.size=Vector2(1.8,2.8) if id=="hell" else Vector2(.9,1.4)
  fire.material_override=flame_material
  fire.position=Vector3(p[0],p[1]+fire.mesh.size.y*.43,p[2])
  fire.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  add_child(fire)
 for p in data.mist:
  _mist(Vector3(p[0],p[1],p[2]))

func _mist(at: Vector3) -> void:
 var mist=GPUParticles3D.new()
 mist.name="WaterfallMist"
 mist.amount=120
 mist.lifetime=3.0
 mist.preprocess=3
 mist.position=at
 mist.visibility_aabb=AABB(Vector3(-10,-3,-10),Vector3(20,15,20))
 var process=ParticleProcessMaterial.new()
 process.emission_shape=ParticleProcessMaterial.EMISSION_SHAPE_BOX
 process.emission_box_extents=Vector3(2,.2,1)
 process.direction=Vector3(0,1,1)
 process.initial_velocity_min=.3
 process.initial_velocity_max=1.1
 process.gravity=Vector3.ZERO
 process.scale_min=.2
 process.scale_max=.8
 mist.process_material=process
 var material=StandardMaterial3D.new()
 material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
 material.billboard_mode=BaseMaterial3D.BILLBOARD_ENABLED
 material.billboard_keep_scale=true
 material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
 material.albedo_color=Color(.55,.72,.8,.10)
 var texture=GradientTexture2D.new()
 texture.width=64;texture.height=64
 texture.fill=GradientTexture2D.FILL_RADIAL
 texture.fill_from=Vector2(.5,.5);texture.fill_to=Vector2(1,.5)
 texture.gradient=Gradient.new()
 texture.gradient.set_color(0,Color(1,1,1,.5))
 texture.gradient.set_color(1,Color(1,1,1,0))
 material.albedo_texture=texture
 var quad=QuadMesh.new()
 quad.size=Vector2.ONE
 quad.material=material
 mist.draw_pass_1=quad
 add_child(mist)
