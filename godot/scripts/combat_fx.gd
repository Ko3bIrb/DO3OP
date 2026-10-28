extends Node3D
# Bounded shared geometry. Hits and deaths never create meshes/materials/nodes.
const CAPACITY = 768
var batches: Dictionary = {}
var particles: Array = []
var shots: Array = []
var random = RandomNumberGenerator.new()
var dropped = 0
var emitted = 0

func _ready() -> void:
 random.seed=81729
 var sphere=SphereMesh.new()
 sphere.radius=.5;sphere.height=1;sphere.radial_segments=8;sphere.rings=4
 var cylinder=CylinderMesh.new()
 cylinder.top_radius=.5;cylinder.bottom_radius=.5;cylinder.height=1;cylinder.radial_segments=6
 var ring=TorusMesh.new()
 ring.inner_radius=.94;ring.outer_radius=1.0;ring.rings=24;ring.ring_segments=4
 var quad=QuadMesh.new();quad.size=Vector2.ONE
 for name in ["hot","line","ring","smoke"]:
  var material=ShaderMaterial.new()
  material.shader=preload("res://shaders/smoke.gdshader") if name=="smoke" else preload("res://shaders/combat.gdshader")
  var mesh=quad if name=="smoke" else cylinder if name=="line" else ring if name=="ring" else sphere
  mesh.material=material
  var mm=MultiMesh.new()
  mm.transform_format=MultiMesh.TRANSFORM_3D
  mm.use_colors=true
  mm.mesh=mesh
  mm.instance_count=CAPACITY
  mm.visible_instance_count=0
  var node=MultiMeshInstance3D.new()
  node.name="Pooled_"+name
  node.multimesh=mm
  node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  add_child(node)
  batches[name]={"mesh":mm,"count":0}

func _particle(kind: String,position: Vector3,velocity: Vector3,color: Color,size: float,life: float,growth: float=0.0,gravity: float=0.0) -> void:
 if particles.size()>=CAPACITY:
  dropped+=1;return
 particles.append({"kind":kind,"p":position,"v":velocity,"color":color,"size":size,"life":life,"total":life,"growth":growth,"gravity":gravity})
 emitted+=1

func _radial(radius: float) -> Vector3:
 var angle=random.randf()*TAU
 return Vector3(cos(angle),random.randf_range(.2,1.1),sin(angle))*radius

func track(event: Dictionary) -> void:
 shots.append({"state":event,"previous":event.start})
 muzzle(event.start,event.end,event.get("tower",{}).get("type","gun"))

func muzzle(at: Vector3,to: Vector3,type: String) -> void:
 var color=Color("ffad5e") if type!="sniper" else Color("bde4ff")
 _particle("hot",at,Vector3.ZERO,color,.36 if type=="mortar" else .25,.075,.5)
 for i in range(4 if type=="mortar" else 2):
  _particle("smoke",at,_radial(.5)+Vector3.UP*.7,Color(.4,.39,.37,.20),.25,.55,.9)
 for i in range(4):
  _particle("hot",at,(to-at).normalized()*random.randf_range(2,5)+_radial(.6),color,.035,.12,0,3)

func impact(at: Vector3,color: Color,large: bool=false,radius: float=1.0) -> void:
 _particle("hot",at,Vector3.ZERO,color,.65 if large else .16,.09,1.0)
 for i in range(18 if large else 5):
  var velocity=_radial(random.randf_range(1.5,6.0) if large else random.randf_range(.5,2.2))
  _particle("hot",at,velocity,color,.06 if large else .03,random.randf_range(.18,.5),-.02,9)
 for i in range(8 if large else 2):
  _particle("smoke",at+Vector3.UP*.2,_radial(.4)+Vector3.UP*.9,Color(.24,.25,.28,.26),.45 if large else .14,.85 if large else .4,1.6 if large else .5)
 if large:
  _particle("ring",Vector3(at.x,.20,at.z),Vector3.ZERO,Color(.65,.48,.3,.3),.2,.45,maxf(1,radius)*4)

func streak(start: Vector3,end: Vector3,color: Color) -> void:
 if particles.size()>=CAPACITY:return
 particles.append({"kind":"line","p":start,"v":Vector3.ZERO,"color":color,"size":.045,"life":.10,"total":.10,"growth":0.0,"gravity":0.0,"start":start,"end":end})
 impact(end,color)

func lightning(start: Vector3,end: Vector3,color: Color) -> void:
 var previous=start
 for i in range(1,7):
  if particles.size()>=CAPACITY:break
  var at=start.lerp(end,float(i)/6)
  if i<6:at+=_radial(.25)
  particles.append({"kind":"line","p":(previous+at)*.5,"v":Vector3.ZERO,"color":color,"size":.045,"life":.13,"total":.13,"growth":0.0,"gravity":0.0,"end":at,"start":previous})
  previous=at
 impact(end,color)

func ring_at(at: Vector3,radius: float,color: Color,life: float=.6) -> void:
 _particle("ring",at+Vector3.UP*.16,Vector3.ZERO,Color(color,.5),radius,life,.4)

func death(at: Vector3,type: String,size: float,flying: bool) -> void:
 var ice=type.begins_with("ice_") or type in ["snow_witch","blizzard_spirit","blizzard_lord","frost_guardian","snow_devourer"]
 var color=Color("a4d9ec") if ice else Color("c27848")
 var spectral=type in ["soul_eater","blizzard_spirit","blizzard_lord","spire"]
 for i in range(14 if spectral else 8):
  var velocity=_radial(random.randf_range(.7,2.1))
  _particle("hot",at,velocity,color,.06 if ice else .035,.55,0,1 if spectral else 8)
 for i in range(5):
  _particle("smoke",at,_radial(.4)+Vector3.UP*(1.0 if spectral else .25),Color(.25,.4,.46,.20) if ice else Color(.24,.20,.18,.22),size*.32,.8,size*.7)

func reward(at: Vector3,boss: bool) -> void:
 for i in range(8 if boss else 3):
  _particle("hot",at,_radial(1.8)+Vector3.UP*1.4,Color("e1bf75"),.07,.65,-.03,7)

func warmup(at: Vector3) -> void:
 for kind in batches:
  _particle(kind,at,Vector3.ZERO,Color(.1,.1,.1,.01),.1,.03)
  if kind=="line":
   particles[-1].start=at
   particles[-1].end=at+Vector3.UP*.1
 render(0)

func render(delta: float,interpolation: float=1.0) -> void:
 for key in batches:batches[key].count=0
 var index=0
 while index<shots.size():
  var shot=shots[index];var state=shot.state
  if not state.get("active",false):
   _line(shot.previous,state.end,.025,state.color)
   shots.remove_at(index);continue
  var visual_position=state.get("previous_position",state.position).lerp(state.position,interpolation)
  var direction=visual_position-shot.previous
  if direction.length_squared()<.0001:direction=state.end-visual_position
  var tail=visual_position-direction.normalized()*(.7 if state.kind=="mortar" else 1.2)
  if state.kind=="mortar":
   _draw("hot",Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*.25),visual_position),Color("b79969"))
  else:
   _line(tail,visual_position,.035,state.color)
  shot.previous=visual_position
  index+=1
 index=0
 while index<particles.size():
  var p=particles[index]
  p.life-=delta
  if p.life<=0:
   particles.remove_at(index);continue
  p.v.y-=p.gravity*delta
  p.p+=p.v*delta
  p.size=maxf(.001,p.size+p.growth*delta)
  var color=Color(p.color,p.color.a*minf(1,p.life/p.total*1.6))
  if p.kind=="line":
   _line(p.start,p.end,p.size,color)
  else:
   var scale=Vector3.ONE*p.size
   if p.kind=="ring":scale.y=.07
   _draw(p.kind,Transform3D(Basis.IDENTITY.scaled(scale),p.p),color)
  index+=1
 for key in batches:batches[key].mesh.visible_instance_count=batches[key].count

func _line(start: Vector3,end: Vector3,width: float,color: Color) -> void:
 var direction=end-start
 if direction.length_squared()<.00001:return
 _draw("line",_line_transform(start,end,width),color)

func _line_transform(start: Vector3,end: Vector3,width: float) -> Transform3D:
 var direction=end-start
 var basis=Basis(Quaternion(Vector3.UP,direction.normalized())) * Basis.from_scale(Vector3(width,direction.length(),width))
 return Transform3D(basis,(start+end)*.5)

func _draw(kind: String,transform: Transform3D,color: Color) -> void:
 var batch=batches[kind]
 if batch.count>=CAPACITY:return
 batch.mesh.set_instance_transform(batch.count,transform)
 batch.mesh.set_instance_color(batch.count,color)
 batch.count+=1
