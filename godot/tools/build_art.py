"""Blender 4.x: rebuild all native game art. No web assets or runtime dependencies.
blender --background --python godot/tools/build_art.py -- [all|characters|worlds|towers|menu]
Meshes use original gameplay coordinates; maps retain routes and construction spots.
"""
import bpy, bmesh, math, random, json, sys, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
OUT=R/'assets/models'
DATA=json.loads((R/'data/game_data.json').read_text())
random.seed(7814)
S=1.; OFF=Vector((0,0,0)); ROOT=None
FAST_WORLD=False; BATCH={}

def V(p):
 p=Vector(p)*S+OFF
 return Vector((p.x,-p.z,p.y))
def color(h):
 return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))

def material(name,hex,metal=0.,rough=.6,glow=0,detail=True):
 m=bpy.data.materials.new(name);m.use_nodes=True
 b=m.node_tree.nodes.get('Principled BSDF'); c=color(hex)
 b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
 if glow:
  b.inputs['Emission Color'].default_value=(*c,1);b.inputs['Emission Strength'].default_value=glow
 if detail and not glow:
  rng=np.random.default_rng(sum(map(ord,name)));n=256
  white=rng.normal(0,1,(n,n))
  fy=np.fft.fftfreq(n)*n;fx=np.fft.rfftfreq(n)*n
  spectrum=np.power(1+fy[:,None]**2+fx[None,:]**2,-0.68)
  field=np.fft.irfft2(np.fft.rfft2(white)*spectrum,s=(n,n)).real
  field=field/max(field.std(),1e-6)*(.012 if 'snow' in name.lower() else .045)
  rgba=np.ones((n,n,4),np.float32)
  for j in range(3):rgba[:,:,j]=np.clip(c[j]*(.86+field*1.7),0,1)
  image=bpy.data.images.new(name+'_albedo',n,n);image.pixels.foreach_set(rgba.ravel());image.pack()
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;m.node_tree.links.new(tex.outputs['Color'],b.inputs['Base Color'])
  # Tangent-space micro relief, exported as a real normal texture.
  dy,dx=np.gradient(field); normal=np.dstack((-dx*4,-dy*4,np.ones_like(dx)));normal/=np.linalg.norm(normal,axis=2)[:,:,None]
  rgba[:,:,:3]=normal*.5+.5
  image=bpy.data.images.new(name+'_normal',n,n);image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(rgba.ravel());image.pack()
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
  normalnode=m.node_tree.nodes.new('ShaderNodeNormalMap');normalnode.inputs['Strength'].default_value=.32
  m.node_tree.links.new(tex.outputs['Color'],normalnode.inputs['Color']);m.node_tree.links.new(normalnode.outputs['Normal'],b.inputs['Normal'])
 return m
STEEL=material('Weathered blue steel','71818b',.85,.32)
DARK=material('Forged black iron','27313c',.8,.42)
GOLD=material('Antique brass','b59153',.78,.33)
LEATHER=material('Oiled leather','392c25',.05,.78)
WOOD=material('Old oak','61412a',0,.8)
BONE=material('Aged bone','c9c5ab',.05,.66)
SNOW=material('Soft windblown snow','bed2dc',0,.84)
STONE=material('Weathered granite','59626d',.08,.85)
BASALT=material('Basalt','2e303b',.15,.8)
ICE=material('Blue glacial ice','6398b8',.25,.22)
RED=material('Demon hide','6e302b',.05,.65)
FUR=material('White winter fur','9eaeb5',0,.93)
CLOTH=material('Woven midnight wool','253543',0,.96)
CLOTHRED=material('Worn crimson cloth','4f2430',0,.9)
PINE=material('Fir needles','213e3d',0,.9)
EMBER=material('Ember core','ff8939',0,.35,1.6,False)
LAVA=material('Cooling lava','d43814',0,.95,.6,False)
FROST=material('Frost core','78d9e9',0,.2,2,False)
SOUL=material('Soul light','80d6a3',0,.25,2,False)
WARM=material('Lantern flame','ffd39a',0,.4,3,False)
EYE=material('Eye socket','10141a',0,.8,0,False)

def parent_obj(o,parent=None):
 p=parent or ROOT
 if p:
  loc=o.location.copy();o.parent=p;o.location=loc-p.location
 return o

def finish(o,name,mat,parent=None,smooth=False):
 if FAST_WORLD:
  matrix=Matrix.Translation(o.location) @ o.rotation_euler.to_matrix().to_4x4() @ Matrix.Diagonal((*o.scale,1))
  emit([tuple(matrix @ v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],mat,smooth=smooth)
  bpy.data.objects.remove(o,do_unlink=True);return None
 o.name=name;o.data.materials.append(mat)
 if smooth:
  for poly in o.data.polygons:poly.use_smooth=True
 return parent_obj(o,parent)

def emit(verts,faces,mat,uv=None,smooth=True):
 g=BATCH.setdefault(mat.name,{'mat':mat,'verts':[],'faces':[],'smooth':[],'uv':[]})
 offset=len(g['verts']);g['verts'].extend(verts)
 for face in faces:
  g['faces'].append(tuple(i+offset for i in face));g['smooth'].append(smooth)
  for i in face:
   co=verts[i];g['uv'].append(uv[i] if uv else (co[0]*.045,co[1]*.045))

def flush_world():
 for g in BATCH.values():
  data=bpy.data.meshes.new(g['mat'].name);data.from_pydata(g['verts'],[],g['faces']);data.update()
  layer=data.uv_layers.new(name='SurfaceUV')
  # Fast bulk assignment avoids per-object dependency-graph updates.
  layer.data.foreach_set('uv',np.asarray(g['uv'],dtype=np.float32).ravel())
  for i,poly in enumerate(data.polygons):poly.use_smooth=g['smooth'][i]
  o=bpy.data.objects.new(g['mat'].name,data);bpy.context.collection.objects.link(o);o.parent=ROOT;data.materials.append(g['mat'])
 BATCH.clear()

def primitive(name,verts,faces,mat,p=(0,0,0),scale=(1,1,1),parent=None,smooth=False):
 if FAST_WORLD:
  pos=V(p);scale=Vector(scale)*S
  emit([tuple(pos+Vector((v[0]*scale.x,v[1]*scale.y,v[2]*scale.z))) for v in verts],faces,mat,smooth=smooth)
  return None
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
 uv=data.uv_layers.new(name='SurfaceUV')
 for loop in data.loops:
  co=data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(co.x*.5+.5,co.z*.5+.5)
 o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=V(p);o.scale=Vector(scale)*S
 return finish(o,name,mat,parent,smooth)

def box(name,p,d,mat,parent=None,bevel=.04):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:v.co.x*=d[0]*S;v.co.y*=d[2]*S;v.co.z*=d[1]*S
 if bevel:
  bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel*S,min(d)*S*.22),segments=2,affect='EDGES')
 if FAST_WORLD:
  bm.verts.ensure_lookup_table();bm.verts.index_update();verts=[tuple(v.co+V(p)) for v in bm.verts];faces=[tuple(v.index for v in f.verts) for f in bm.faces];emit(verts,faces,mat,smooth=False);bm.free();return None
 data=bpy.data.meshes.new(name);bm.to_mesh(data);bm.free();data.update()
 uv=data.uv_layers.new(name='SurfaceUV')
 for loop in data.loops:
  co=data.vertices[loop.vertex_index].co;normal=data.polygons[0].normal;uv.data[loop.index].uv=(co.x*.25,co.y*.25)
 o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=V(p)
 return finish(o,name,mat,parent)

def ell(name,p,d,mat,parent=None,seg=20):
 rings=max(8,seg//2);verts=[];faces=[]
 for j in range(rings+1):
  t=math.pi*j/rings
  for i in range(seg):
   a=math.tau*i/seg;verts.append((math.sin(t)*math.cos(a),math.sin(t)*math.sin(a),math.cos(t)))
 for j in range(rings):
  for i in range(seg):
   k=j*seg+i;n=j*seg+(i+1)%seg;faces.append((k,k+seg,n+seg,n))
 return primitive(name,verts,faces,mat,p,(d[0],d[2],d[1]),parent,True)

def tube(name,a,b,r,mat,parent=None,r2=None,verts=16):
 aa,bb=V(a),V(b);delta=bb-aa;points=[];faces=[];rr=r if r2 is None else r2
 for z,rad in [(-.5,r),(.5,rr)]:
  for i in range(verts):
   theta=i*math.tau/verts;points.append((math.cos(theta)*rad,math.sin(theta)*rad,z))
 for i in range(verts):
  n=(i+1)%verts;faces.append((i,n,n+verts,i+verts))
 faces.extend([tuple(reversed(range(verts))),tuple(range(verts,verts*2))])
 if FAST_WORLD:
  rotation=delta.to_track_quat('Z','Y');mid=(aa+bb)*.5
  emit([tuple(mid+rotation @ Vector((v[0]*S,v[1]*S,v[2]*delta.length))) for v in points],faces,mat,smooth=True)
  return None
 data=bpy.data.meshes.new(name);data.from_pydata(points,[],faces);data.update()
 uv=data.uv_layers.new(name='SurfaceUV')
 for loop in data.loops:
  co=data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(math.atan2(co.y,co.x)/math.tau+.5,co.z+.5)
 o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=(aa+bb)*.5;o.scale=(S,S,delta.length)
 o.rotation_mode='QUATERNION';o.rotation_quaternion=delta.to_track_quat('Z','Y')
 return finish(o,name,mat,parent,True)

def ring(name,p,r,t,mat,parent=None,axis='Y'):
 verts=[];faces=[];n,m=32,8
 for j in range(n):
  a=j*math.tau/n
  for k in range(m):
   b=k*math.tau/m;verts.append(((r+t*math.cos(b))*math.cos(a),(r+t*math.cos(b))*math.sin(a),t*math.sin(b)))
 for j in range(n):
  for k in range(m):faces.append((j*m+k,((j+1)%n)*m+k,((j+1)%n)*m+(k+1)%m,j*m+(k+1)%m))
 if FAST_WORLD:
  rotation=Matrix.Rotation(math.pi/2,3,'X') if axis=='Z' else Matrix.Rotation(math.pi/2,3,'Y') if axis=='X' else Matrix.Identity(3)
  emit([tuple(V(p)+rotation @ (Vector(v)*S)) for v in verts],faces,mat,smooth=True);return None
 o=primitive(name,verts,faces,mat,p,parent=parent,smooth=True)
 if axis=='Z':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 return o

def curve(name,points,r,mat,parent=None):
 if FAST_WORLD:
  for a,b in zip(points,points[1:]):tube(name,a,b,r,mat,parent,verts=8)
  return None
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=r*S;cu.bevel_resolution=2
 sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 pp=parent or ROOT
 for point,co in zip(sp.points,points):point.co=(*(V(co)-(pp.location if pp else Vector())),1)
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.data.materials.append(mat);o.parent=pp
 return o

def mesh(name,vertices,faces,mat,parent=None,smooth=False):
 if FAST_WORLD:
  emit([tuple(V(v)) for v in vertices],faces,mat,smooth=smooth);return None
 pp=parent or ROOT;data=bpy.data.meshes.new(name)
 data.from_pydata([V(v)-(pp.location if pp else Vector()) for v in vertices],[],faces);data.update()
 uv=data.uv_layers.new(name='SurfaceUV')
 for loop in data.loops:
  point=data.vertices[loop.vertex_index].co
  uv.data[loop.index].uv=(point.x*.045,point.y*.045)
 ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.parent=pp;data.materials.append(mat)
 for p in data.polygons:p.use_smooth=smooth
 return ob

def empty(name,p=(0,0,0)):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=V(p)
 if ROOT and name!='asset':o.parent=ROOT
 return o

def start(scale=1,offset=(0,0,0)):
 global ROOT,S,OFF
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 S=scale;OFF=Vector(offset);ROOT=None;ROOT=empty('asset')
 # Geometry helpers use world coordinates; keep the asset root at origin.
 ROOT.location=(0,0,0)

def export(name):
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();groups={};original=[]
 for o in list(bpy.context.scene.objects):
  if o.type not in ['MESH','CURVE']:continue
  ev=o.evaluated_get(deps);data=ev.to_mesh();parent=o.parent
  matrix=parent.matrix_world.inverted() @ o.matrix_world if parent else o.matrix_world
  key=(parent.name if parent else '',o.data.materials[0].name)
  g=groups.setdefault(key,{'parent':parent,'mat':o.data.materials[0],'verts':[],'faces':[],'uv':[],'smooth':[]})
  offset=len(g['verts']);g['verts'].extend([matrix @ v.co for v in data.vertices])
  for poly in data.polygons:
   g['faces'].append(tuple(offset+i for i in poly.vertices));g['smooth'].append(poly.use_smooth)
   for li in poly.loop_indices:g['uv'].append(tuple(data.uv_layers.active.data[li].uv) if data.uv_layers.active else (0,0))
  ev.to_mesh_clear();original.append(o)
 for o in original:bpy.data.objects.remove(o,do_unlink=True)
 for g in groups.values():
  data=bpy.data.meshes.new(g['mat'].name);data.from_pydata(g['verts'],[],g['faces']);data.update()
  uv=data.uv_layers.new(name='SurfaceUV')
  for i,pair in enumerate(g['uv']):uv.data[i].uv=pair
  for i,poly in enumerate(data.polygons):poly.use_smooth=g['smooth'][i]
  o=bpy.data.objects.new(g['mat'].name.replace(' ','_'),data);bpy.context.collection.objects.link(o);o.parent=g['parent'];data.materials.append(g['mat'])
 bpy.ops.object.select_all(action='SELECT')
 bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_yup=True)
 print('ART_EXPORTED',name,flush=True)
 for data in list(bpy.data.meshes):
  if not data.users:bpy.data.meshes.remove(data)

def bolts(y,r,n=12,parent=None):
 for i in range(n):
  a=i*math.tau/n;tube('Hex bolt',(math.cos(a)*r,y,math.sin(a)*r),(math.cos(a)*r,y+.065,math.sin(a)*r),.065,STEEL,parent,verts=6)

def crystal(p,size,mat=FROST,parent=None):
 x,y,z=p
 tube('Crystal', (x,y-size*.5,z),(x,y+size*.48,z),size*.22,ICE,parent,r2=size*.13,verts=6)
 tube('Crystal crown',(x,y+size*.48,z),(x,y+size*.85,z),size*.13,mat,parent,r2=0,verts=6)

def tower(kind,level):
 start();base=empty('base');turret=empty('turret')
 tube('Foundation',(0,.02,0),(0,.28,0),1.35,STONE,base,r2=1.25,verts=40)
 ring('Brass trim',(0,.29,0),1.16,.065,GOLD,base);tube('Bearing',(0,.3,0),(0,.62,0),.82,DARK,base,verts=32);bolts(.31,1.03,12,base)
 for i in range(level):ring('Level ring',(0,.45+i*.13,0),.83,.04,GOLD,base)
 if kind in ['gun','sniper','mortar']:
  height=3.7 if kind=='sniper' else .85
  tube('Pedestal',(0,.62,0),(0,height,0),.46,DARK,base,r2=.33,verts=24)
  if kind=='sniper':
   for y in [1,1.7,2.4,3.1]:ring('Elevation bracing',(0,y,0),.50,.07,STEEL,base)
   for side in [-1,1]:tube('Structural strut',(side*.8,.45,0),(side*.25,3.7,0),.10,STEEL,base)
  box('Breech',(0,height+.3,-.15),(.85,.55,1.4),DARK,turret,.09)
  ell('Armored mantlet',(0,height+.2,.35),(.6,.45,.38),STEEL,turret)
  if kind=='gun':
   # Six distinct open barrels around a rotating central axle.
   for i in range(4+level*2):
    a=math.tau*i/(4+level*2);x=math.cos(a)*.24;y=1.34+math.sin(a)*.24
    tube('Gatling barrel',(x,y,.35),(x,y,2),.085,DARK,turret,verts=16)
    tube('Open muzzle',(x,y,2.005),(x,y,2.025),.057,EYE,turret)
   for z in [.55,1.15,1.78]:ring('Barrel collar',(0,1.34,z),.34,.07,STEEL,turret,axis='Z')
   box('Ammunition box',(-.8,1,-.15),(.55,.65,.9),GOLD,turret)
   for i in range(9):tube('Ammunition belt',(-.59+i*.11,1.12,-.77),(-.59+i*.11,1.12,-.45),.065,GOLD,turret)
  elif kind=='sniper':
   tube('Long precision barrel',(0,4.34,.35),(0,4.34,3.7),.105,DARK,turret)
   for z in [1,2.1,3.4]:ring('Barrel sleeve',(0,4.34,z),.12,.035,STEEL,turret,'Z')
   box('Muzzle brake',(0,4.34,3.65),(.28,.23,.45),STEEL,turret)
   tube('Muzzle bore',(0,4.34,3.88),(0,4.34,3.9),.073,EYE,turret)
   tube('Scope',(0,4.8,-.4),(0,4.8,.7),.15,DARK,turret)
   tube('Scope lens',(0,4.8,.705),(0,4.8,.72),.12,FROST,turret)
   box('Stock',(0,4.25,-1.13),(.30,.50,.75),WOOD,turret)
   for side in [-1,1]:tube('Bipod',(side*.12,4.2,1),(side*.6,3.7,1.4),.05,STEEL,turret)
  else:
   a=(0,1.1,-.45);b=(0,4.24,.7)
   tube('Mortar barrel',a,b,.44,DARK,turret,r2=.53,verts=32)
   direction=(Vector(b)-Vector(a)).normalized()
   for t in [.18,.48,.82]:
    q=Vector(a).lerp(Vector(b),t);tube('Reinforcement sleeve',q-direction*.12,q+direction*.12,.53,STEEL,turret,verts=32)
   tube('Mortar bore',Vector(b)+direction*.012,Vector(b)+direction*.028,.42,EYE,turret,verts=32)
   for side in [-1,1]:
    tube('Recoil piston',(side*.7,.6,-.2),(side*.55,2.5,.1),.13,STEEL,turret)
    tube('Hydraulic ram',(side*.7,.65,-.2),(side*.56,1.6,0),.18,DARK,turret)
   for i in range(level+1):ell('Mortar shell',(.85, .6,-.7+i*.4),(.17,.17,.32),GOLD,base)
 else:
  tube('Carved support',(0,.6,0),(0,2.25,0),.55,STONE,base,r2=.36,verts=12)
  for a in range(4):
   theta=a*math.tau/4;x,z=math.cos(theta)*.52,math.sin(theta)*.52
   tube('Conduit',(x,.65,z),(x,2.3,z),.055,GOLD,base)
  if kind=='slow':
   for y in [1.1,1.5,1.9,2.3]:ring('Cryogenic coil',(0,y,0),.65,.09,STEEL,base)
   crystal((0,2.95,0),.9+level*.13,FROST,turret)
   for i in range(4):
    a=i*math.tau/4; x,z=math.cos(a),math.sin(a)
    tube('Cryo prong',(x*.7,.75,z*.7),(x*.85,2.7,z*.85),.10,DARK,turret,r2=.06)
    ell('Cryo emitter',(x*.85,2.7,z*.85),(.13,.20,.13),FROST,turret)
  elif kind=='amp':
   crystal((0,2.8,0),1.1,SOUL,turret)
   for y in [2.45,3.25]:ring('Gyroscope',(0,y,0),.75,.055,GOLD,turret)
   ring('Gyroscope upright',(0,2.85,0),.95,.055,GOLD,turret,'X')
   for side in [-1,1]:tube('Pylon',(side*.9,.5,0),(side*.7,3.8,0),.13,DARK,turret,r2=.055)
  else:
   ell('Celestial core',(0,3.08,0),(.34,.46,.34),WARM,turret)
   ring('Halo',(0,3.9,0),.55,.06,GOLD,turret)
   for side in [-1,1]:
    for i in range(6):
     a=(side*(.35+i*.17),2.5+i*.15,0)
     tube('Guardian wing',a,(side*(.9+i*.18),3.05+i*.19,-.12),.12,STEEL,turret,r2=.025)
   tube('Lightning conductor',(0,2.3,0),(0,3.74,.6),.12,GOLD,turret,r2=.05)
   ell('Sky emitter',(0,3.74,.6),(.14,.14,.14),WARM,turret)
 for i in range(level-1):
  for sign in [-1,1]:box('Upgrade armor',(sign*(.72+i*.12),.82,-.15),(.16,.55,.85),STEEL,base)
 export('tower_%s_%d'%(kind,level))

def clawed_hand(p,mat,parent):
 ell('Hand',p,(.13,.19,.10),mat,parent)
 x,y,z=p
 for i in range(4):tube('Claw',(x+(i-1.5)*.052,y-.08,z+.03),(x+(i-1.5)*.065,y-.32,z+.13),.032,mat if mat in [STEEL,DARK] else BONE,parent,r2=.005,verts=8)

def skull(p,scale=1,mat=BONE,eyes=FROST,parent=None,human=False):
 x,y,z=p
 ell('Cranium',(x,y+.08*scale,z),(.22*scale,.28*scale,.20*scale),mat,parent,24)
 ell('Jaw',(x,y-.16*scale,z+.065*scale),(.16*scale,.11*scale,.17*scale),mat,parent)
 for side in [-1,1]:
  ell('Eye socket',(x+side*.09*scale,y+.06*scale,z+.172*scale),(.068*scale,.06*scale,.045*scale),EYE,parent)
  ell('Living eye',(x+side*.09*scale,y+.06*scale,z+.207*scale),(.027*scale,.023*scale,.016*scale),eyes,parent)
  tube('Brow',(x+side*.035*scale,y+.14*scale,z+.18*scale),(x+side*.18*scale,y+.13*scale,z+.14*scale),.025*scale,mat,parent)
 if not human:
  for i in range(7):box('Tooth',(x+(i-3)*.038*scale,y-.11*scale,z+.20*scale),(.027*scale,.052*scale,.03*scale),BONE,parent,.005)
 tube('Nose',(x,y+.03*scale,z+.19*scale),(x,y-.035*scale,z+.25*scale),.035*scale,mat,parent,r2=.018*scale)

def horns(p,parent=None,length=1):
 x,y,z=p
 for sign in [-1,1]:
  points=[(x+sign*.17,y,z),(x+sign*.30,y+.15*length,z-.06),(x+sign*.37,y+.36*length,z-.10),(x+sign*.30,y+.58*length,z-.03)]
  for i in range(3):tube('Horn',points[i],points[i+1],.075*(1-i*.28),BONE,parent,r2=max(.005,.075*(1-(i+1)*.31)),verts=12)

def cloak(parent,mat=CLOTH,width=.6,height=1.8,y=2.1,z=-.23):
 verts=[];faces=[];cols=18;rows=16
 for j in range(rows):
  t=j/(rows-1)
  for i in range(cols):
   u=i/(cols-1);verts.append(((u-.5)*width*(.5+t),y-t*height,z-.25*t+math.sin(u*math.tau*6)*.065*t))
 for j in range(rows-1):
  for i in range(cols-1):
   k=j*cols+i;faces.append((k,k+1,k+cols+1,k+cols))
 o=mesh('Layered woven cloak',verts,faces,mat,parent,True)
 mod=o.modifiers.new('Cloth thickness','SOLIDIFY');mod.thickness=.015

def humanoid(kind,ice=False):
 armored=kind in ['knight','ice_knight','baron','frost_guardian','colossus','menu_knight']
 skeletal=kind in ['ice_skeleton','soul_eater','trumpeter']
 mage=kind in ['snow_witch','blizzard_lord','blizzard_spirit','spire','soul_eater']
 core=FROST if ice else EMBER
 if kind in ['soul_eater','spire']:core=SOUL
 skin=BONE if skeletal else FUR if kind=='snow_devourer' else ICE if ice else RED
 if kind=='menu_knight':core=WARM
 body=STEEL if armored else skin
 torso=empty('motion_torso',(0,1.45,0))
 if not skeletal:
  ell('Chest',(0,1.72,0),(.42,.55,.24),body,torso,28)
  ell('Abdomen',(0,1.28,0),(.29,.29,.20),LEATHER if armored else skin,torso)
  ell('Pelvis',(0,1.05,0),(.31,.23,.22),body,torso)
 else:
  ring('Pelvic girdle',(0,1.05,0),.23,.045,BONE,torso)
  tube('Sternum',(0,1.45,.20),(0,2.02,.18),.025,BONE,torso)

 for side in [-1,1]:
  suffix='L' if side<0 else 'R'
  leg=empty('motion_leg_'+suffix,(side*.22,1.05,0))
  hip=(side*.22,1.05,0);knee=(side*.25,.57,.09);ankle=(side*.25,.13,0)
  tube('Thigh',hip,knee,.055 if skeletal else .15,LEATHER if armored else skin,leg,r2=.035 if skeletal else .105)
  ell('Knee',knee,(.065,.07,.06) if skeletal else (.14,.15,.13),body,leg)
  tube('Shin',knee,ankle,.04 if skeletal else .11,body,leg,r2=.025 if skeletal else .08)
  ell('Foot',(side*.25,.09,.13),(.13,.12,.28),DARK if armored else skin,leg)
  arm=empty('motion_arm_'+suffix,(side*.48,2.0,0))
  shoulder=(side*.47,1.98,0);elbow=(side*.67,1.56,.03);wrist=(side*.65,1.2,.10)
  ell('Deltoid',shoulder,(.085,.085,.085) if skeletal else (.21,.24,.22),body,arm)
  tube('Upper arm',shoulder,elbow,.045 if skeletal else .13,LEATHER if armored else skin,arm,r2=.03 if skeletal else .105)
  ell('Elbow',elbow,(.055,.055,.055) if skeletal else (.12,.12,.12),body,arm)
  tube('Forearm',elbow,wrist,.035 if skeletal else .12,body,arm,r2=.022 if skeletal else .08)
  clawed_hand(wrist,body,arm)
  if armored:
   for j in range(3):ell('Articulated pauldron',(side*(.43+j*.055),2.08-j*.05,-.015),(.22,.085,.25),STEEL,arm)
   for j in range(4):ell('Laminated armor',(side*.22,1.0-j*.09,.08),(.23,.075,.24),DARK,leg)
   for y in [1.5,1.75,1.95]:ell('Armor rivet',(side*.28,y,.205),(.025,.025,.015),GOLD,torso)
 if skeletal:
  for i in range(7):
   y=1.42+i*.085
   curve('Rib',[(math.cos(a)*(.33-(i*.015)),y,math.sin(a)*.22) for a in np.linspace(.05,math.pi-.05,16)],.022,BONE,torso)
  for i in range(11):ell('Vertebra',(0,1.15+i*.085,-.18),(.07,.045,.065),BONE,torso)
 head=empty('motion_head',(0,2.4,0))
 tube('Neck',(0,2.02,0),(0,2.40,0),.13,skin,head)
 if armored:
  ell('Helmet',(0,2.43,0),(.25,.30,.24),DARK,head,28)
  ell('Face plate',(0,2.39,.16),(.205,.19,.12),STEEL,head)
  box('Visor slit',(0,2.46,.267),(.34,.035,.025),EYE,head,.008)
  for sign in [-1,1]:box('Visor glint',(sign*.085,2.46,.284),(.10,.018,.008),core,head,.003)
  tube('Nasal guard',(0,2.59,.25),(0,2.23,.27),.024,GOLD,head)
  for j in range(5):box('Helmet vent',((j-2)*.045,2.28,.266),(.014,.055,.012),EYE,head,.003)
  cloak(torso,CLOTH if ice or kind=='menu_knight' else CLOTHRED,width=1.15)
  # Embossed breastplate and waist belts.
  tube('Breastplate ridge',(0,1.4,.255),(0,2.05,.255),.035,GOLD,torso)
  for y in [1.09,1.20]:ring('Leather belt',(0,y,0),.29,.045,LEATHER,torso)
  if kind!='menu_knight':horns((0,2.59,0),head,1.2 if kind=='baron' else .65)
 else:
  skull((0,2.4,0),1,skin,core,head,kind in ['snow_witch','succubus'])
  if kind not in ['ice_skeleton','snow_witch','blizzard_spirit']:horns((0,2.58,0),head,.75)
 if mage:
  cloak(torso,CLOTH if ice else CLOTHRED,width=1.4,height=2.3,y=2.15,z=.07)
  tube('Staff',(.76,.1,.2),(.76,2.95,.2),.055,WOOD)
  ring('Staff setting',(.76,2.85,.2),.22,.045,GOLD,axis='Z');crystal((.76,3.08,.2),.35,FROST if ice else SOUL)
  if kind=='snow_witch':
   tube('Fur hood brim',(0,2.44,0),(0,2.55,0),.35,FUR,head,r2=.28,verts=24)
   tube('Witch crown',(0,2.55,0),(.13,3.05,-.1),.28,CLOTH,head,r2=.01)
 if kind in ['knight','ice_knight','baron','frost_guardian','menu_knight']:
  # Crossguard, pommel, fuller, blade and shield clearly read as knight equipment.
  for x in [(-.78 if kind=='menu_knight' else -.9)]:
   box('Sword blade',(x,.70,.28),(.12,1.25,.035),STEEL,bevel=.015)
   tube('Blade fuller',(x,.13,.305),(x,1.25,.305),.012,GOLD)
   box('Crossguard',(x,1.37,.28),(.45,.07,.07),GOLD)
   tube('Sword grip',(x,1.40,.28),(x,1.66,.28),.052,LEATHER)
   ell('Sword pommel',(x,1.7,.28),(.075,.075,.075),GOLD)
  ell('Shield',(.81,1.38,.18),(.38,.55,.09),DARK)
  ring('Shield boss',(.81,1.38,.29),.16,.035,GOLD,axis='Z')
  box('Shield cross',(.81,1.38,.29),(.05,.77,.018),GOLD)
 if kind in ['colossus','ice_golem','snow_devourer']:
  for sign in [-1,1]:
   ell('Massive shoulder',(sign*.55,1.91,0),(.35,.37,.33),body)
   for i in range(5):tube('Shoulder spike',(sign*(.38+i*.1),2.08,-.1),(sign*(.45+i*.15),2.5+random.random()*.2,-.15),.075,ICE if ice else BASALT,r2=.005)
  for i in range(8):crystal(((i%3-1)*.22,1.35+(i//3)*.25,.23),.15,FROST if ice else EMBER)
 if kind=='bes':
  curve('Barbed tail',[(0,1.0,-.15),(.2,.6,-.55),(.6,.7,-.8),(.65,1.0,-.7)],.055,RED)
  tube('Tail barb',(.65,1.,-.7),(.7,1.22,-.6),.12,BONE,r2=0)
 if kind in ['succubus','ice_harpy','trumpeter','blizzard_lord']:
  wings(kind,ice)
 if kind=='trumpeter':
  curve('Ceremonial trumpet',[(.15,2.4,.24),(.45,2.3,.5),(.65,2.25,.85),(.65,2.25,1.4)],.075,GOLD)
  tube('Trumpet bell',(.65,2.25,1.1),(.65,2.25,1.6),.08,GOLD,r2=.35)
  tube('Bell shadow',(.65,2.25,1.605),(.65,2.25,1.615),.29,EYE)
 if kind=='spire':
  for i in range(5):
   a=i*math.tau/5;tube('Floating spire',(.38*math.cos(a),1.4,.38*math.sin(a)),(.62*math.cos(a),3.3,.62*math.sin(a)),.12,BASALT,r2=.01)
  crystal((0,2.9,0),.7,SOUL)
 if kind=='snow_devourer':
  ell('Devouring muzzle',(0,2.3,.27),(.26,.21,.29),FUR,head)
  for sign in [-1,1]:tube('Tusk',(sign*.17,2.2,.43),(sign*.24,2.63,.48),.08,BONE,head,r2=.005)
  for i in range(50):
   a=random.uniform(0,math.tau);y=random.uniform(1.05,2.2);x=math.cos(a)*.43;z=math.sin(a)*.25
   tube('Fur strand',(x,y,z),(x*1.17,y-.16,z*1.17),.05,FUR,r2=.008,verts=6)

def wings(kind,ice):
 for side in [-1,1]:
  parent=empty('motion_wing_'+('L' if side<0 else 'R'),(side*.35,1.9,-.12))
  a=(side*.32,1.95,-.1);b=(side*.98,2.8,-.1);c=(side*1.9,2.95,.05)
  tube('Wing humerus',a,b,.065,BONE,parent);tube('Wing tip',b,c,.045,BONE,parent,r2=.01)
  for i in range(8):
   t=i/7;top=Vector(b).lerp(Vector(c),t);end=(side*(.5+t*1.35),1.45+t*.45,-.20)
   if kind in ['ice_harpy','trumpeter','blizzard_lord']:
    tube('Flight feather',top,end,.10,ICE if ice else BONE,parent,r2=.008,verts=10)
   else:
    mesh('Wing membrane',[a,b,c,end],[(0,1,2),(0,2,3)],CLOTHRED,parent,True)
    tube('Wing finger',top,end,.025,BONE,parent,r2=.008)

def hound():
 body=empty('motion_torso',(0,.8,0))
 ell('Lean ribcage',(0,.92,0),(.32,.40,.65),RED,body,28)
 ell('Withers',(0,1.13,.35),(.35,.40,.32),BASALT,body)
 for side in [-1,1]:
  for front in [-1,1]:
   x=side*.26;z=front*.44;p=empty('motion_leg_'+str(side)+'_'+str(front),(x,.85,z))
   tube('Dog thigh',(x,.85,z),(x*1.15,.45,z-.10),.11,RED,p,r2=.08)
   tube('Dog shin',(x*1.15,.45,z-.10),(x,.1,z+.12),.065,RED,p,r2=.045)
   ell('Paw',(x,.1,z+.19),(.105,.10,.19),BASALT,p)
   for i in range(3):tube('Dog claw',(x+(i-1)*.06,.08,z+.30),(x+(i-1)*.06,.07,z+.40),.025,BONE,p,r2=0)
 head=empty('motion_head',(0,1.15,.67))
 ell('Canine skull',(0,1.18,.68),(.26,.27,.30),RED,head)
 ell('Snout',(0,1.10,.99),(.18,.15,.30),BASALT,head)
 for sign in [-1,1]:
  ell('Dog eye',(sign*.18,1.25,.84),(.048,.038,.04),EMBER,head)
  tube('Fang',(sign*.12,1.03,1.17),(sign*.12,.86,1.18),.04,BONE,head,r2=.005)
  tube('Ear',(sign*.16,1.37,.61),(sign*.22,1.73,.52),.12,RED,head,r2=0)
 for z in np.linspace(-.5,.3,6):tube('Spinal spine',(0,1.22,z),(0,1.62,z-.1),.07,BONE,body,r2=0)
 curve('Hound tail',[(0,.95,-.6),(.15,.8,-1),(.25,1.,-1.3)],.055,RED)

def ballista(ice):
 box('Oak chassis',(0,.46,0),(1.05,.25,1.65),WOOD)
 for side in [-1,1]:
  for z in [-.65,.65]:
   ring('Iron wheel',(side*.68,.45,z),.43,.09,DARK,axis='X')
   for j in range(8):
    a=j*math.tau/8;tube('Wheel spoke',(side*.68,.45,z),(side*.68,.45+math.cos(a)*.39,z+math.sin(a)*.39),.035,WOOD)
   tube('Axle',(side*.71,.45,z),(-side*.71,.45,z),.075,STEEL)
 box('Ballista stock',(0,.96,.2),(.28,.24,1.85),WOOD)
 for side in [-1,1]:
  curve('Laminated bow',[(0,1.05,.75),(side*.65,1.05,.65),(side*1.25,1.1,.28)],.09,ICE if ice else WOOD)
 curve('Taut bowstring',[(-1.25,1.1,.28),(0,1.08,-.45),(1.25,1.1,.28)],.013,LEATHER)
 tube('Siege bolt',(0,1.14,-.7),(0,1.14,1.55),.035,WOOD)
 tube('Bolt point',(0,1.14,1.4),(0,1.14,1.72),.10,ICE if ice else STEEL,r2=0)
 for x in [-.36,.36]:tube('Torsion winch',(x,.65,-.4),(x,1.12,-.4),.12,GOLD)
 if ice:
  for i in range(6):crystal((random.uniform(-.5,.5),.7,random.uniform(-.7,.7)),.25,FROST)

def enemy(kind,d):
 size=d['size']*d.get('visualScale',1.0);base=max(.6,d['size']*.75) if not d['flying'] else d['size']*.35
 start(size,(0,-base,0));ice=kind in DATA['maps']['ice']['enemies']
 if 'ballista' in kind:ballista(ice)
 elif kind=='hound':hound()
 elif kind=='spire':
  for i in range(4):
   tube('Infernal spire',(0,i*.62,0),(0,(i+1)*.62,0),.54-i*.085,BASALT,r2=.46-i*.085,verts=8)
   ring('Spire binding',(0,i*.62,0),.55-i*.085,.055,GOLD)
  crystal((0,2.6,0),.5,SOUL)
  skull((0,1.5,.39),1.4,BONE,SOUL)
  for sign in [-1,1]:
   tube('Spire buttress',(sign*.6,.15,0),(sign*.40,1.8,0),.16,DARK,r2=.045)
   curve('Hanging chain',[(sign*.48,1.6,0),(sign*.65,.9,0),(sign*.5,.1,0)],.035,GOLD)
 else:humanoid(kind,ice)
 export('enemy_'+kind)

def fir(p,height=6,snow=True):
 x,y,z=p;tube('Fir trunk',(x,y,z),(x,y+height,z),height*.035,WOOD,r2=.015,verts=10)
 for layer in range(8):
  yy=y+height*(.16+layer*.098);radius=height*(.30-layer*.035)
  for branch in range(6):
   angle=branch*math.tau/6+layer*.43+random.uniform(-.15,.15)
   forward=Vector((math.cos(angle),0,math.sin(angle)))
   across=Vector((-forward.z,0,forward.x))
   origin=Vector((x,yy,z));tip=origin+forward*radius+Vector((0,-height*.065,0))
   tube('Natural fir bough',origin,tip,height*.010,WOOD,r2=.004,verts=6)
   for segment in range(1,5):
    t=segment/5;at=origin.lerp(tip,t);w=radius*.22*(1-t*.7)
    for side in [-1,1]:
     end=at+forward*radius*.24+across*w*side+Vector((0,-height*.025,0))
     # Serrated needle fronds with visible gaps and irregular snowy shoulders.
     verts=[at];faces=[]
     for j in range(7):
      u=j/6;point=at.lerp(end,u);width=height*.035*math.sin(math.pi*u)*(1+random.uniform(-.15,.15))
      verts.extend([point+across*width,point-across*width])
     for j in range(6):faces.append((1+j*2,1+(j+1)*2,2+(j+1)*2,2+j*2))
     mesh('Fir needles',verts,faces,PINE,smooth=True)
     if snow and segment%2==0:
      curve('Snow on bough',[at+Vector((0,height*.012,0)),at.lerp(end,.55)+Vector((0,height*.016,0)),end],height*.015,SNOW)
 tube('Fir leader',(x,y+height*.84,z),(x,y+height*1.02,z),height*.035,PINE,r2=0,verts=8)

def rock(p,size=2,ice=False):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=V(p));o=bpy.context.object
 for vert in o.data.vertices:
  co=vert.co;co*=random.uniform(.86,1.14)
 o.scale=(size*S,size*.72*S,size*.65*S)
 finish(o,'Eroded boulder',STONE if ice else BASALT,smooth=True)
 if ice:ell('Snow drift',(p[0],p[1]+size*.46,p[2]),(size*.78,size*.18,size*.5),SNOW,seg=20)

def lantern(p,ice=True):
 x,y,z=p;tube('Lamp post',(x,y,z),(x,y+2.2,z),.07,DARK)
 tube('Lamp base',(x,y,z),(x,y+.3,z),.18,STONE,r2=.12)
 box('Lantern',(x,y+2.25,z),(.34,.46,.34),GOLD,bevel=.04)
 ell('Lantern glass',(x,y+2.25,z+.18),(.12,.17,.025),WARM)
 tube('Lantern roof',(x,y+2.48,z),(x,y+2.67,z),.28,DARK,r2=.05,verts=4)

def fortress(p,ice=True):
 x,y,z=p;stone=STONE if ice else BASALT
 box('Fortress foundation',(x,y+.4,z),(10,.8,8),stone,.0 if False else None,bevel=.18)
 box('Keep',(x,y+3.4,z),(6,6,5),stone,bevel=.12)
 for yy in [1.1,2.3,3.5,4.7,5.9]:
  for side in [-1,1]:box('Masonry course',(x,y+yy,z+side*2.54),(6.1,.12,.11),STEEL,bevel=.025)
 for dx in [-3.5,3.5]:
  for dz in [-2.8,2.8]:
   tube('Fortress tower',(x+dx,y+.3,z+dz),(x+dx,y+7.3,z+dz),1.2,stone,verts=32)
   for h in [1.4,4.0,6.6]:ring('Tower masonry',(x+dx,y+h,z+dz),1.23,.09,STONE)
   tube('Turret roof',(x+dx,y+7.3,z+dz),(x+dx,y+10,z+dz),1.7,STEEL,r2=.05,verts=24)
   if ice:tube('Snow roof',(x+dx,y+7.45,z+dz),(x+dx,y+10.1,z+dz),1.48,SNOW,r2=.02,verts=24)
   for sign in [-1,1]:box('Tower window',(x+dx+sign*.60,y+5.9,z+dz+1.04),(.24,.75,.055),WARM,bevel=.10)
 for i in range(8):box('Battlement',(x-3.1+i*.88,y+6.8,z+2.6),(.52,.65,.65),stone)
 box('Gate shadow',(x-3.06,y+1.6,z),(0.13,3.0,2.3),EYE,bevel=.20)
 for k in range(6):box('Iron portcullis',(x-3.15,y+1.6,z-1+k*.4),(.15,2.9,.055),DARK)
 for side in [-1,1]:lantern((x-3.5,y,z+side*2),ice)

def portal(p,ice=True):
 x,y,z=p;mat=ICE if ice else BASALT
 for side in [-1,1]:
  for h in range(6):box('Portal masonry',(x,y+.5+h*.8,z+side*2.7),(.95,.75,1.0),mat,bevel=.12)
  tube('Portal finial',(x,y+5.0,z+side*2.7),(x,y+7.2,z+side*2.7),.55,DARK,r2=.03)
 ring('Portal ring',(x,y+3.3,z),2.6,.35,DARK,axis='X')
 ring('Runic portal',(x+.04,y+3.3,z),2.15,.065,FROST if ice else EMBER,axis='X')
 for i in range(12):
  a=i*math.tau/12;ell('Portal rune',(x+.25,y+3.3+math.sin(a)*2.5,z+math.cos(a)*2.5),(.08,.15,.11),FROST if ice else EMBER)

def near_route(x,z,route):
 p=Vector((x,z));best=1e6
 for a,b in zip(route,route[1:]):
  a=Vector((a[0],a[2]));b=Vector((b[0],b[2]));ab=b-a;t=max(0,min(1,(p-a).dot(ab)/ab.length_squared));best=min(best,(p-(a+ab*t)).length)
 return best

def world(mapid):
 from landscape import build_landscape
 build_landscape(globals(),mapid)

def menu():
 start();random.seed(420)
 box('Winter ground',(0,-.2,0),(90,.4,90),SNOW,bevel=.1)
 for p in [(-5,0,-7),(4,0,-8),(8,0,-11),(-8,0,-15),(12,0,-20),(-15,0,-22),(-3,0,-18),(1,0,-25)]:fir(p,random.uniform(7,12),True)
 for i in range(16):rock((random.uniform(-17,17),0,random.uniform(-18,2)),random.uniform(.4,1.6),True)
 # Hand-built knight is shared with the equipment vocabulary used in game.
 global S,OFF
 S=1.35;OFF=Vector((2.4,0,.0));humanoid('menu_knight',True)
 S=1;OFF=Vector((0,0,0))
 lantern((4.3,0,.9),True)
 # Small campfire, charred logs, iron bowl and luminous coals.
 tube('Fire bowl',(3.4,.05,1.8),(3.4,.28,1.8),.60,DARK,r2=.52,verts=32)
 for i in range(8):
  a=i*math.tau/8;tube('Charred log',(3.4+math.cos(a)*.5,.3,1.8+math.sin(a)*.5),(3.4-math.cos(a)*.3,.4,1.8-math.sin(a)*.3),.09,WOOD)
 for i in range(9):
  x=3.4+random.uniform(-.25,.25);z=1.8+random.uniform(-.25,.25)
  ell('Coal',(x,.35,z),(.12,.09,.1),EMBER)
  tube('Flame',(x,.38,z),(x+random.uniform(-.1,.1),random.uniform(.65,1),z),.11,EMBER,r2=.012,verts=8)
 export('menu_winter')

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv and len(sys.argv)>sys.argv.index('--')+1 else 'all'
if mode in ['all','towers']:
 for kind in DATA['towers']:
  for level in [1,2,3]:tower(kind,level)
if mode in ['all','characters']:
 for mapdata in DATA['maps'].values():
  for kind,d in mapdata['enemies'].items():enemy(kind,d)
if mode in ['all','worlds','terrain']:
 from landscape import build_props
 if mode!='terrain':build_props(globals())
 for mapid in ['ice','hell']:world(mapid)
if mode in ['all','menu']:menu()
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.glb'))}
(R/'data/asset_manifest.json').write_text(json.dumps({'generator':'Blender build_art.py','files':manifest},indent=2)+'\n')
