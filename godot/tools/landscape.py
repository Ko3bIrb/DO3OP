"""Authored terrain composition for Night Watch. Routes/placements stay playable.
Static architecture is exported by Blender; repeated forest/rock props are instanced
by Godot from the scene manifest rather than duplicated into a giant world mesh.
"""
import math,random,json
from mathutils import Vector

def build_props(c):
 for i in range(3):
  random.seed(720+i);c['start']();c['fir']((0,0,0),[5.8,7.1,4.6][i],True);c['export']('prop_fir_'+str(i))
 for ice in [True,False]:
  for i in range(3):
   random.seed(460+i);c['start']();c['rock']((0,0,0),[1.0,1.5,.7][i],ice);c['export']('prop_'+('snowrock_' if ice else 'basalt_')+str(i))

def build_landscape(c,mapid):
 c['start']();c['FAST_WORLD']=True;random.seed(2109 if mapid=='ice' else 914)
 ice=mapid=='ice';data=c['DATA']['maps'][mapid];route=data['waypoints'];spots=data['spots']
 mesh,box,tube,curve,ring=c['mesh'],c['box'],c['tube'],c['curve'],c['ring']
 stone,snow,basalt,wood,bone,gold=[c[k] for k in ['STONE','SNOW','BASALT','WOOD','BONE','GOLD']]
 water=c['material']('Bay water','16485d',.28,.15,0,False)
 cascade=c['material']('Waterfall','7da5b7',.1,.22,0,False)
 magma=c['material']('Living lava','db4310',0,.65,1.2,False)
 terrainmat=c['material']('Mountain ground','71808a' if ice else '24130f',.03,.9)
 roadmat=c['material']('Old road stones','58616a' if ice else '31251d',.02,.9)
 slate=c['material']('Wet cliff stone','3b5362' if ice else '3d3238',.13,.7)
 meta={'instances':[],'fires':[],'mist':[],'waterfall':ice,'landmarks':[]}
 if ice:
  peaks=[(-49,-62,31,22,21),(-17,-64,40,15,17),(3,-53,30,13,13),(29,-67,45,23,18),(67,-55,26,18,22),(-66,-17,14,10,17),(64,20,11,16,18)]
 else:
  peaks=[(-12,-53,34,21,22),(-47,-63,26,19,16),(26,-65,31,16,22),(58,-47,24,17,14),(-65,12,12,10,14),(62,23,13,13,17)]
 def bay(x,z):
  if ice:
   q=(x/(13.8+1.0*math.sin(z*.21)))**2+((z+19)/20.5)**2
   outlet=(x/1.8)**2+((z-10)/16)**2
   return min(q,outlet)
  return ((x+3)/13.2)**2+((z-3)/11.5)**2
 def river_distance(x,z):
  center=(-4+2.0*math.sin(z*.15)) if not ice else .4*math.sin(z*.3)
  return abs(x-center)
 def height(x,z):
  h=(.25 if ice else -4.6)+1.2*math.sin(x*.105+math.sin(z*.08))+.7*math.cos(z*.13+x*.045)
  for px,pz,hh,rx,rz in peaks:
   q=((x-px)/rx)**2+((z-pz)/rz)**2
   ridge=1+.05*math.sin(x*.43+z*.19)+.03*math.sin(z*.58-x*.27)
   h+=hh*math.exp(-q*1.7)*ridge
  if not ice:
   crater=((x+12)/6)**2+((z+53)/5.5)**2
   h-=9*math.exp(-crater*2)
  q=bay(x,z)
  if q<1.18:h=min(h,-4.2+4.1*max(0,q-.57)/.61)
  if -48<z<-10 and river_distance(x,z)<(2.6 if ice else 3.4):
   if ice:h=min(h,-1+18*max(0,(-z-34)/13)**1.65)
   else:h=min(h,-2.7+max(0,(-z-25))*1.0)
  d=c['near_route'](x,z,route)
  ds=min(math.hypot(x-s['position'][0],z-s['position'][2]) for s in spots)
  safe=max(max(0,1-(d/4.5)**4),max(0,1-(ds/3.4)**4))
  if d<2.2 or ds<1.65:safe=1
  # Stable rock terraces carry the military road and every construction platform.
  return h*(1-safe)
 meta['landmarks']=['central bay','mountain waterfall','shore road','outlet bridge','fishing hamlet','watch camp'] if ice else ['volcano','lava basin','lava river','dragon ribs','broken gate','fortress causeway']
 # Continuous asymmetric massifs with exposed cliffs and windblown snow.
 n,m=193,137;verts=[];faces_by={};minx,maxx,minz,maxz=-105,105,-89,60
 for j in range(m):
  z=minz+j*(maxz-minz)/(m-1)
  for i in range(n):
   x=minx+i*(maxx-minx)/(n-1);verts.append((x,height(x,z),z))
 terrain_faces=[]
 for j in range(m-1):
  for i in range(n-1):
   a=j*n+i;terrain_faces.append((a,a+n,a+n+1,a+1))
 mesh('Carved landscape',verts,terrain_faces,terrainmat,smooth=True)
 # Visible water/lava basins. Holes retain the sniper islands and shore ledges.
 def basin_surface():
  vv=[];ff=[];nx,nz=(65,121) if ice else (151,121)
  for j in range(nz):
   z=(-43+j*67/(nz-1)) if ice else (-78+j*133/(nz-1))
   for i in range(nx):vv.append(((-20+i*40/(nx-1)) if ice else (-96+i*192/(nx-1)),-1.05,z))
  for j in range(nz-1):
   for i in range(nx-1):
    k=j*nx+i;ids=(k,k+nx,k+nx+1,k+1)
    if not ice or min(bay(vv[v][0],vv[v][2]) for v in ids)<1.5:ff.append(ids)
  mesh('Central bay' if ice else 'Molten basin',vv,ff,water if ice else magma,smooth=True)
 basin_surface()
 # A stepped rock lip breaks the waterfall into several unequal falling streams.
 if ice:
  # Start well above the camera framing. The upper source is deliberately
  # outside the game view so the streams enter from the mountain instead of
  # exposing an artificial, floating beginning.
  for strand,(cx,width,top,bottom,phase) in enumerate([(-1.2,1.05,-56.5,-33.2,.0),(.9,.7,-55.6,-32.4,1.5),(2.0,.38,-54.4,-33.8,3.2)]):
   vv=[];ff=[];steps=74
   for i in range(steps+1):
    t=i/steps;z=top+(bottom-top)*t
    x=cx+.28*math.sin(t*9+phase)+.18*math.sin(t*23+phase)
    w=width*(.62+.25*math.sin(t*17+phase)+.45*t)
    y=-.75+18*max(0,(-z-34)/13)**1.65
    for j in range(5):
     u=j/4;vv.append((x+(u*2-1)*w,y+.15+.12*math.sin(t*29+u*8+phase),z))
   for i in range(steps):
    for j in range(4):
     k=i*5+j;ff.append((k,k+5,k+6,k+1))
   # UV.y is one at the hidden top and zero at the pool. The waterfall
   # shader advances this coordinate toward zero, matching the fall direction.
   c['emit']([tuple(c['V'](v)) for v in vv],ff,cascade,uv=[(j/4,1.0-i/steps) for i in range(steps+1) for j in range(5)],smooth=True)
  meta['mist'] += [[-1,-.3,-33],[1,-.3,-33.8]]
 else:
  # Several molten tributaries crawl down the volcano instead of a straight stripe.
  for offset,width in [(-1.2,1.4),(1.6,.8),(5.2,.5)]:
   vv=[];ff=[]
   for i in range(100):
    z=-54+i*45/99;x=-8+offset+3.5*math.sin(z*.13)+1.1*math.sin(z*.4)
    y=max(-.98,height(x,z)+.12)
    w=width*(1+.3*math.sin(z))
    vv.extend([(x-w,y,z),(x+w,y,z)])
   for i in range(99):ff.append((i*2,i*2+2,i*2+3,i*2+1))
   mesh('Volcanic tributary',vv,ff,magma,smooth=True)
 # Rounded corners retain the original route within the walkable ribbon.
 controls=[Vector(route[0])+Vector((-3,0,0))]+[Vector(v) for v in route]+[Vector(route[-1])+Vector((3,0,0))]
 samples=[controls[0]]
 def append_line(a,b):
  for j in range(1,max(2,int((b-a).length/.55))+1):
   samples.append(a.lerp(b,j/max(2,int((b-a).length/.55))))
 for i in range(1,len(controls)-1):
  a,b,d=controls[i-1:i+2];radius=min(1.6,(b-a).length*.25,(d-b).length*.25)
  before=b+(a-b).normalized()*radius;after=b+(d-b).normalized()*radius
  append_line(samples[-1],before)
  for j in range(1,9):
   t=j/8;samples.append(before*(1-t)**2+b*2*(1-t)*t+after*t*t)
 append_line(samples[-1],controls[-1])
 # Small, even paving stones leave narrow joints in both directions. Each
 # segment has five mirrored rows, so the route reads as a path of tiles rather
 # than one continuous slab. Snow buries individual stones at random while the
 # bridge stays clear of both paving and drifts.
 tile_v=[];tile_f=[];snow_v=[];snow_f=[]
 row_centers=[-1.28,-.64,0,.64,1.28]
 for i in range(len(samples)-1):
  p=samples[i];nxt=samples[i+1]
  midpoint=(p+nxt)*.5
  if ice and abs(midpoint.x)<5.5 and 13<midpoint.z<17:continue
  tangent=(nxt-p).normalized();normal=Vector((-tangent.z,0,tangent.x))
  seg_len=(nxt-p).length
  half_len=min(.235,seg_len*.39)
  for u in row_centers:
   center=midpoint+normal*u
   half_width=.265
   y=center.y+.105+random.uniform(-.006,.008)
   base=len(tile_v)
   tile_v.extend([
    center-tangent*half_len-normal*half_width+Vector((0,y,0)),
    center+tangent*half_len-normal*half_width+Vector((0,y+.008,0)),
    center+tangent*half_len+normal*half_width+Vector((0,y+.006,0)),
    center-tangent*half_len+normal*half_width+Vector((0,y,0))
   ])
   tile_f.append((base,base+1,base+2,base+3))
   # Snow covers complete small tiles, leaving an irregular but readable route.
   if random.random()<.39:
    snow_base=len(snow_v);snow_y=y+.045
    snow_v.extend([
     center-tangent*(half_len*.98)-normal*(half_width*.96)+Vector((0,snow_y,0)),
     center+tangent*(half_len*.98)-normal*(half_width*.96)+Vector((0,snow_y+.008,0)),
     center+tangent*(half_len*.98)+normal*(half_width*.96)+Vector((0,snow_y+.006,0)),
     center-tangent*(half_len*.98)+normal*(half_width*.96)+Vector((0,snow_y,0))
    ])
    snow_f.append((snow_base,snow_base+1,snow_base+2,snow_base+3))
 mesh('Small symmetric route tiles',tile_v,tile_f,roadmat,smooth=True)
 mesh('Snow covered route tiles',snow_v,snow_f,snow,smooth=True)
 # Lanterns mark key bends; loose paving blocks along every segment created
 # the chain of dark route points visible from the game camera.
 for i in range(0,len(samples),42):
  p=samples[i]
  if ice and abs(p.x)<6 and p.z>12:continue
  tangent=(samples[min(i+1,len(samples)-1)]-samples[max(0,i-1)]).normalized();normal=Vector((-tangent.z,0,tangent.x))
  at=p+normal*2.6;c['lantern'](at,ice)
  meta.setdefault('lanterns',[]).append([at.x,at.y+2.25,at.z])
 # Construction platforms are separate from the route markers and remain
 # visible so players can tell where a tower may be placed.
 for s in spots:
  x,y,z=s['position'];tube('Rock tower terrace',(x,-.4,z),(x,.14,z),1.40,stone,r2=1.16,verts=24)
  ring('Terrace inlay',(x,.16,z),1.02,.033,c['ICE'] if s['restricted_to'] else gold)
 def camp(x,z):
  y=height(x,z)
  for dx,dz,sc in [(-3,-1,1.1),(2,2,.8)]:
   xx,zz=x+dx,z+dz;yy=height(xx,zz);w=2.3*sc;h=2.1*sc
   mesh('Watch camp tent',[(xx-w,yy,zz-2),(xx+w,yy,zz-2),(xx,yy+h,zz-2),(xx-w,yy,zz+2),(xx+w,yy,zz+2),(xx,yy+h,zz+2)],[(0,2,5,3),(2,1,4,5),(0,1,2)],c['CLOTH'],smooth=False)
   tube('Tent ridge',(xx,yy+h+.03,zz-2.3),(xx,yy+h+.03,zz+2.3),.05,wood)
  for i in range(6):
   a=i*math.tau/6;tube('Campfire log',(x+math.cos(a),y+.12,z+math.sin(a)),(x-math.cos(a)*.6,y+.17,z-math.sin(a)*.6),.10,wood)
  meta['fires'].append([x,y+.25,z]);meta.setdefault('camps',[]).append([x,y,z])
 def house(x,z,scale):
  y=height(x,z);w=1.8*scale;d=2.2*scale;h=2.5*scale
  box('Village stone footing',(x,y+.2,z),(w*2.1,.4,d*2.1),stone,bevel=.1)
  box('Timber cottage',(x,y+h/2,z),(w*2,h,d*2),wood,bevel=.06)
  roof=[(x-w-.3,y+h,z-d-.3),(x+w+.3,y+h,z-d-.3),(x,y+h+1.8*scale,z-d-.3),(x-w-.3,y+h,z+d+.3),(x+w+.3,y+h,z+d+.3),(x,y+h+1.8*scale,z+d+.3)]
  mesh('Cottage pitched roof',roof,[(0,2,5,3),(2,1,4,5),(0,1,2),(3,5,4)],snow if ice else c['DARK'])
  for side in [-1,1]:
   box('Warm cottage window',(x+side*w*.55,y+h*.64,z+d+.025),(.55*scale,.65*scale,.04),c['WARM'],bevel=.06)
   tube('Window cross',(x+side*w*.55,y+h*.40,z+d+.055),(x+side*w*.55,y+h*.87,z+d+.055),.025,wood)
  box('Cottage door',(x,y+.72*scale,z+d+.035),(.65*scale,1.45*scale,.06),c['DARK'],bevel=.04)
  tube('Chimney',(x+w*.65,y+h,z-.7),(x+w*.65,y+h+2.1*scale,z-.7),.28,stone,verts=8)
  meta.setdefault('homes',[]).append([x,y+1,z])
 def ruin(x,z,scale=1.0):
  y=height(x,z)
  # The ruin is a snow-buried landmark: its visible stonework is white all
  # the way through, so no detached caps can float above the walls.
  for dx,dz,h in [(-2.4,0,4.2),(2.1,.35,3.0),(.0,1.9,3.5)]:
   box('Snow buried ruin wall',(x+dx*scale,y+h*.5,z+dz*scale),(1.35*scale,h,.62*scale),snow,bevel=.10)
  for side in [-1,1]:
   box('Snow buried ruin arch pillar',(x+side*.9*scale,y+2.0*scale,z-1.15*scale),(.72*scale,4.0*scale,.72*scale),snow,bevel=.08)
  curve('Snow buried ruin arch',[(x-.95*scale,y+3.8*scale,z-1.15*scale),(x,y+5.0*scale,z-1.15*scale),(x+.95*scale,y+3.8*scale,z-1.15*scale)],.22*scale,snow)
  for step in range(4):
   box('Snow buried ruin stair',(x,y+.12*scale+step*.18*scale,z-2.3*scale+step*.32*scale),(1.5*scale,.22*scale,.62*scale),snow,bevel=.05)
  tube('Snow buried collapsed beam',(x-2.3*scale,y+1.8*scale,z-.5*scale),(x+2.1*scale,y+.45*scale,z+1.0*scale),.17*scale,snow,r2=.10*scale,verts=8)
  c['ell']('Snow mound on ruin',(x+.1*scale,y+4.9*scale,z-1.15*scale),(1.55*scale,.22*scale,.75*scale),snow,seg=12)
 def gargoyle(x,z,scale=1.0):
  y=height(x,z)
  # A squat dragon statue: haunches, muzzle, horns, wings and a tail read as
  # a creature instead of a rounded vessel when seen from the game camera.
  c['ell']('Snow dragon torso',(x,y+1.25*scale,z),(.95*scale,1.25*scale,.72*scale),stone,seg=14)
  for side in [-1,1]:
   c['ell']('Snow dragon haunch',(x+side*.62*scale,y+.85*scale,z+.38*scale),(.50*scale,.72*scale,.58*scale),stone,seg=12)
   tube('Snow dragon foreleg',(x+side*.42*scale,y+1.0*scale,z-.35*scale),(x+side*.55*scale,y+.18*scale,z-.75*scale),.16*scale,stone,r2=.09*scale,verts=8)
   c['ell']('Snow dragon paw',(x+side*.55*scale,y+.13*scale,z-.86*scale),(.30*scale,.14*scale,.42*scale),snow,seg=10)
  c['ell']('Snow dragon neck',(x,y+2.0*scale,z-.18*scale),(.48*scale,.85*scale,.45*scale),stone,seg=12)
  c['ell']('Snow dragon head',(x,y+2.65*scale,z-.42*scale),(.62*scale,.52*scale,.58*scale),stone,seg=14)
  c['ell']('Snow dragon muzzle',(x,y+2.52*scale,z-.88*scale),(.40*scale,.26*scale,.40*scale),snow,seg=12)
  for side in [-1,1]:
   curve('Snow dragon wing',[(x+side*.35*scale,y+1.55*scale,z),(x+side*1.45*scale,y+3.0*scale,z+.15*scale),(x+side*2.2*scale,y+1.75*scale,z+.45*scale),(x+side*1.6*scale,y+1.0*scale,z+.55*scale)],.16*scale,stone)
   tube('Snow dragon horn',(x+side*.25*scale,y+2.95*scale,z-.35*scale),(x+side*.58*scale,y+3.45*scale,z-.25*scale),.10*scale,stone,r2=.02*scale,verts=8)
  curve('Snow dragon tail',[(x,y+.9*scale,z+.45*scale),(x,y+.45*scale,z+1.5*scale),(x,y+.3*scale,z+2.2*scale)],.16*scale,stone)
  c['ell']('Snow dragon crown',(x,y+3.15*scale,z-.35*scale),(.62*scale,.14*scale,.44*scale),snow,seg=12)
 def windmill(x,z,scale=1.0):
  y=height(x,z)
  # A tapered wooden tower and four broad lattice sails match the traditional
  # windmill silhouette and face the elevated camera on the positive-Z side.
  sides=12;base_r=2.10*scale;top_r=1.15*scale;bottom=y+.08*scale;top=y+4.85*scale
  vv=[];ff=[]
  for yy,rr in [(bottom,base_r),(top,top_r)]:
   for i in range(sides):
    a=math.tau*i/sides;vv.append((x+math.cos(a)*rr,yy,z+math.sin(a)*rr))
  for i in range(sides):
   n=(i+1)%sides;ff.append((i,n,sides+n,sides+i))
  ff.append(tuple(range(sides-1,-1,-1)));ff.append(tuple(range(sides,2*sides)))
  mesh('Tapered mill tower',vv,ff,wood,smooth=True)
  for i in range(4):
   a=i*math.pi*.5+math.pi*.25
   tube('Mill tower timber rib',(x+math.cos(a)*base_r*.98,bottom,z+math.sin(a)*base_r*.98),(x+math.cos(a)*top_r,top,z+math.sin(a)*top_r),.075*scale,c['DARK'],r2=.045*scale,verts=6)
  # Snow cap over the small roof, kept seated directly on the tower rim.
  roof=[(x+math.cos(math.tau*i/sides)*top_r,top,z+math.sin(math.tau*i/sides)*top_r) for i in range(sides)]
  roof.append((x,top+.72*scale,z))
  mesh('Snow cap on mill',roof,[(i,(i+1)%sides,sides) for i in range(sides)],snow,smooth=True)
  box('Mill dark doorway',(x,y+1.0*scale,z+base_r*.98),(.72*scale,1.65*scale,.08),c['DARK'],bevel=.04)
  hub=Vector((x,top-.05*scale,z+top_r*1.32))
  for blade in range(4):
   angle=blade*math.pi*.5+math.pi*.25;direction=Vector((math.cos(angle),math.sin(angle),0));across=Vector((-math.sin(angle),math.cos(angle),0))
   root=hub+direction*.30*scale;tip=hub+direction*3.15*scale
   root_w=.25*scale;tip_w=.62*scale
   for side in [-1,1]:
    tube('Mill lattice sail rail',root+across*root_w*side,tip+across*tip_w*side,.075*scale,wood,r2=.045*scale,verts=6)
   tube('Mill lattice sail spine',root,tip,.07*scale,wood,r2=.04*scale,verts=6)
   for fraction in [.25,.5,.75]:
    center=root.lerp(tip,fraction);half= root_w+(tip_w-root_w)*fraction
    tube('Mill lattice sail brace',center-across*half,center+across*half,.045*scale,wood,r2=.025*scale,verts=6)
  c['ell']('Mill axle',tuple(hub),(.22*scale,.22*scale,.13*scale),stone,seg=12)
 def frozen_mine(x,z,scale=1.0):
  y=height(x,z)
  box('Frozen mine darkness',(x,y+1.05*scale,z),(2.5*scale,2.0*scale,.30*scale),c['EYE'],bevel=.10)
  for side in [-1,1]:
   tube('Mine timber support',(x+side*.9*scale,y+.15*scale,z-1.0*scale),(x+side*.9*scale,y+2.0*scale,z-1.0*scale),.14*scale,wood,r2=.10*scale,verts=8)
  tube('Mine timber lintel',(x-.95*scale,y+2.0*scale,z-1.0*scale),(x+.95*scale,y+2.0*scale,z-1.0*scale),.16*scale,wood,r2=.11*scale,verts=8)
  c['crystal']((x-1.3*scale,y+.35*scale,z+.15*scale),1.4*scale,c['ICE'])
  c['crystal']((x+1.25*scale,y+.28*scale,z+.25*scale),1.0*scale,c['ICE'])
  c['ell']('Mine snow bank',(x,y+.15*scale,z+1.15*scale),(1.55*scale,.28*scale,.58*scale),snow,seg=14)
 def logging_site(x,z,scale=1.0):
  y=height(x,z)
  # A dropped axe, boot prints, rough sawhorse and fresh-cut timber make the
  # settlement feel inhabited even though the workers are gone.
  tube('Dropped axe handle',(x,y+.10*scale,z),(x+.95*scale,y+.68*scale,z+.25*scale),.055*scale,wood,r2=.035*scale,verts=8)
  box('Dropped axe head',(x+.98*scale,y+.72*scale,z+.26*scale),(.34*scale,.20*scale,.08*scale),c['DARK'],bevel=.03)
  box('Small sawmill frame',(x+2.1*scale,y+.65*scale,z),(2.2*scale,1.2*scale,1.4*scale),wood,bevel=.06)
  for side in [-1,1]:tube('Sawmill support',(x+(1.3+side*.7)*scale,y+.08*scale,z-1.0*scale),(x+(1.3+side*.7)*scale,y+1.55*scale,z-1.0*scale),.07*scale,wood,verts=8)
  for i in range(6):
   px=x+(.1+(i%3)*.7)*scale;pz=z+(.7+(i//3)*.65)*scale
   box('Boot print',(px,y+.035*scale,pz),(.16*scale,.025*scale,.34*scale),c['DARK'],bevel=.02)
  for i in range(4):
   xx=x-1.4*scale+i*.42*scale
   tube('Fallen tree log',(xx,y+.22*scale,z+2.0*scale),(xx+.25*scale,y+.36*scale,z+3.65*scale),.16*scale,wood,r2=.13*scale,verts=10)
  c['ell']('Small timber pile',(x-1.0*scale,y+.55*scale,z+3.5*scale),(1.25*scale,.55*scale,.75*scale),wood,seg=12)
  c['ell']('Snow on timber pile',(x-1.0*scale,y+1.02*scale,z+3.5*scale),(1.18*scale,.12*scale,.70*scale),snow,seg=12)
 # Human landmarks make the road's destination and defensive purpose legible.
 if ice:
  # The old camp was isolated on the left. Move the active-looking settlement
  # up beside the allied fortress and give it a broken mill and a frozen mine.
  camp(48,-34)
  windmill(58,-35,1.90)
  frozen_mine(68,-49,2.10)
  # The western shoulder keeps the history of the old pass: snow-buried ruins
  # and two gargoyles watching the enemy gate.
  for rx,rz,rs in [(-39,-28,2.4),(-40,18,2.0)]:ruin(rx,rz,rs)
  # Replace the road-blocking third ruin with a raised snow-rock cluster.
  for rx,rz,rs in [(-47,-25,2.1),(-42,-23,1.45),(-45,-30,1.0)]:
   c['rock']((rx,height(rx,rz),rz),rs,True)
  logging_site(27,27,1.2)
  for x,z,sc in [(31,6,.75),(36,10,1.05),(41,7,.9),(45,13,.65),(32,14,.65)]:house(x,z,sc)
  # Stone crossing extends into both banks; paving disappears below the abutments.
  for x in [-5.8,5.8]:
   box('Bridge abutment',(x,-.35,15),(2.3,1.1,4.25),stone,bevel=.25)
   for z in [12.75,17.25]:
    tube('Bridge watch turret',(x,-.1,z),(x,2.9,z),.65,stone,verts=16)
    ring('Watch turret crown',(x,2.9,z),.70,.13,stone)
    for k in range(6):
     a=k*math.tau/6;box('Watch crenel',(x+math.cos(a)*.52,3.15,z+math.sin(a)*.52),(.28,.4,.28),stone,bevel=.035)
    meta.setdefault('lanterns',[]).append([x,2,z])
  for i in range(25):
   x=-6.0+i*.5;box('Bridge paving',(x,.055,15),(.51,.19,3.8),stone,bevel=.04)
  for side in [-1,1]:
   curve('Bridge arch',[(-6,0,15+side*1.8),(-3,-1.2,15+side*1.8),(0,-1.8,15+side*1.8),(3,-1.2,15+side*1.8),(6,0,15+side*1.8)],.38,stone)
   box('Bridge parapet',(0,.6,15+side*1.94),(12.8,.8,.35),stone,bevel=.1)
  # Timber fences, stone walls and supplies tie the settlement to the military road.
  for x,z,sc in [(29,20,.65),(36,21,.85),(43,23,.7),(46,3,.6),(29,9,.55)]:house(x,z,sc)
  # A lookout island with a short footbridge to the east shore.
  for x in range(2,11):box('Lookout footbridge',(x,-.05,-20),(.94,.18,1.6),wood,bevel=.04)
  # Dock and moored fishing boat on the sheltered shore.
  for j in range(10):box('Jetty planks',(-7+j*.4,-.7,-4),(.38,.15,2.5),wood,bevel=.025)
  for x in [-7,-5,-3]:tube('Dock piling',(x,-3,-4.9),(x,-.45,-4.9),.10,wood)
  c['ell']('Fishing hull',(-5,-.8,-6.5),(.7,.26,1.7),wood)
 else:
  # Ruined arch over a historic basalt pass.
  for side in [-1,1]:
   for j in range(5):box('Broken gate stone',(-33,-.1+j*.8,-15+side*2.7),(1.1,.72,.95),stone,bevel=.12)
  curve('Broken gate arch',[(-33,3.6,-17.7),(-33,5,-17),(-33,5.7,-15.7)],.36,stone)
  # Dragon remains and a shrine on the basin rim, not evenly spaced scenery.
  for i in range(6):
   z=-3+i*2.0;w=4.2-i*.32;h=3.7-i*.22
   for side in [-1,1]:curve('Ancient dragon rib',[(-5+side*w,-.6,z),(-5+side*w*.85,h*.65,z),(-5+side*w*.3,h,z+.2)],.17,bone)
  for j in range(6):tube('Dragon vertebra',(-5,j*.03+2.7,-3+j*2),(-5,2.7,-2+j*2),.20,bone)
  for x,z in [(-28,6),(-9,20),(20,-27),(36,10),(-47,-6),(-5,-28)]:
   if c['near_route'](x,z,route)>3.5:meta['fires'].append([x,height(x,z)+.25,z])
  for x,z,sc in [(37,8,.8),(43,11,1.05),(31,13,.65)]:house(x,z,sc)
  # A crater and tributary pools make the volcano recognisable at game-camera scale.
  vv=[(-12,26,-53)]
  for i in range(65):
   a=i*math.tau/64;vv.append((-12+math.cos(a)*4.5,26+math.sin(a*5)*.15,-53+math.sin(a)*3.4))
  mesh('Glowing volcanic crater',vv,[(0,i+2,i+1) for i in range(64)],magma)
  meta['fires'].append([-12,27,-53])
 c['fortress'](route[-1],ice)
 # The enemy source is a fortress with an open, illuminated gate facing the road.
 x,y,z=route[0];wall=c['ICE'] if ice else basalt;glow=c['FROST'] if ice else c['EMBER']
 for dx,dz,h,r in [(-3,-5,12,2),(-3,5,14,2.3),(-11,-6,17,2.5),(-11,6,15,2.2)]:
  tube('Enemy castle tower',(x+dx,-.4,z+dz),(x+dx,h,z+dz),r,wall,verts=20)
  for yy in [2.5,5.5,8.5]:ring('Castle tower stone band',(x+dx,yy,z+dz),r+.08,.14,stone if ice else basalt)
  tube('Castle spire',(x+dx,h,z+dz),(x+dx,h+5,z+dz),r*1.35,c['ICE'] if ice else c['DARK'],r2=.05,verts=16)
  for yy in [4,7,10]:box('Castle burning slit',(x+dx+r*.9,yy,z+dz),(.12,1.35,.38),glow,bevel=.07)
  if not ice:meta['fires'].append([x+dx,h,z+dz])
 box('Enemy citadel keep',(x-10,5.5,z),(8,11,10),wall,bevel=.2)
 for dz in [-1,1]:
  box('Castle gatehouse side',(x-1,3.7,z+dz*3.5),(4,7.5,2),wall,bevel=.18)
  box('Citadel flank',(x-8,4,z+dz*7),(9,8,1.5),wall,bevel=.18)
 curve('Gate pointed vault',[(x+.9,4,z-2.5),(x+.9,6,z-1.4),(x+.9,7.2,z),(x+.9,6,z+1.4),(x+.9,4,z+2.5)],.65,wall)
 for dz in [-2.2,2.2]:tube('Gate luminous arch',(x+1.05,0,z+dz),(x+1.05,4.3,z+dz),.065,glow)
 # Darkness behind the opening gives emerging monsters an architectural origin.
 box('Gate depth',(x-4,2.5,z),(.12,5,4.7),c['EYE'],bevel=.2)
 for i in range(8):
  box('Gatehouse crenel',(x-2+(i%2)*3,7.8,z-3.9+(i//2)*2.6),(1,.7,.8),wall,bevel=.07)
 if ice:
  for j in range(28):
   xx=x+random.uniform(-15,1);zz=z+random.choice([-1,1])*random.uniform(7,10)
   c['crystal']((xx,height(xx,zz),zz),random.uniform(.8,2.0),c['ICE'])
 meta['enemy_castle']=[x-7,0,z]

 # Clustered, varied vegetation/stone props, instanced by the runtime. Keep
 # landmark clearings reserved so foliage and rocks never grow through them.
 reserved=[
  (48,-34,9), (58,-35,9), (68,-49,10), (27,27,10), (-30,-34,5),
  (-39,-28,9), (-45,-26,8), (-40,18,8),
  (31,6,5), (36,10,6), (41,7,5), (45,13,5), (32,14,5),
  (-6,15,8), (0,-20,4), (-5,-4,5), (route[0][0],route[0][2],14),
  (route[-1][0],route[-1][2],14), (route[0][0]-10,route[0][2],8)
 ] if ice else [(36,10,10),(-5,3,7),(route[0][0],route[0][2],14),(route[-1][0],route[-1][2],14)]
 occupied=[(x,z,r) for x,z,r in reserved]
 def clear_of_props(x,z,radius):
  return all(math.hypot(x-px,z-pz) >= radius+pr for px,pz,pr in occupied)
 def allowed(x,z,margin=4):
  if c['near_route'](x,z,route)<margin:return False
  if min(math.hypot(x-s['position'][0],z-s['position'][2]) for s in spots)<3.1:return False
  if any(math.hypot(x-a,z-b)<r for a,b,r in reserved):return False
  if min(math.hypot(x-route[k][0],z-route[k][2]) for k in [0,-1])<8:return False
  # The central cascade is a visible landmark; keep every instanced rock and
  # tree outside its water channel so nothing appears to float in the fall.
  if ice and -50<z<-30 and river_distance(x,z)<4.8:return False
  return height(x,z)>(-.75 if ice else -1.0)
 def add_snow_rock(x,z,sc):
  clearance=max(1.0,sc*.80)
  if not allowed(x,z,7.5) or not clear_of_props(x,z,clearance):return False
  meta['instances'].append({'key':'prop_snowrock_'+str(random.randrange(3)),'position':[x,height(x,z)-.15,z],'scale':[sc*random.uniform(.7,1.7),sc*random.uniform(.7,1.7),sc*random.uniform(.8,1.4)],'yaw':random.uniform(0,math.tau)})
  occupied.append((x,z,clearance));return True
 if ice:
  # Deliberate empty clearings around the enemy gate and on both road corners
  # receive additional boulders. The same route/landmark tests keep these
  # pockets off the walkable tiles and out of every existing prop.
  for cx,cz,radius,count in [(-73,-14,8,26),(-73,14,8,26),(-31,-42,8,28),(31,-42,8,28)]:
   placed=0
   for _ in range(count*8):
    if placed>=count:break
    a=random.uniform(0,math.tau);r=radius*math.sqrt(random.random());x=cx+math.cos(a)*r;z=cz+math.sin(a)*r
    if add_snow_rock(x,z,random.uniform(.75,2.1)):placed+=1
  clusters=[(-48,12,9,60),(-36,-3,7,19),(28,-3,8,22),(48,18,10,32),(-54,-35,8,22),(57,-37,9,25),(-35,-48,8,21),(37,-46,7,19),(-23,29,9,23),(23,29,9,24)]
  for cx,cz,radius,count in clusters:
   for _ in range(count*4):
    if count<=0:break
    a=random.uniform(0,math.tau);r=radius*math.sqrt(random.random());x=cx+math.cos(a)*r;z=cz+math.sin(a)*r
    sc=random.uniform(.55,1.35);clearance=max(1.45,sc*1.65)
    if not allowed(x,z) or not clear_of_props(x,z,clearance):continue
    meta['instances'].append({'key':'prop_fir_'+str(random.randrange(3)),'position':[x,height(x,z),z],'scale':[sc*random.uniform(.85,1.05),sc*random.uniform(.9,1.35),sc*random.uniform(.85,1.1)],'yaw':random.uniform(0,math.tau)})
    occupied.append((x,z,clearance))
    count-=1
 # Continuous forest across the valley shoulders; small clearings remain around play.
 if ice:
  tree_count=sum(1 for item in meta['instances'] if item['key'].startswith('prop_fir_'))
  for _ in range(10000):
   if tree_count>=900:break
   x=random.uniform(-87,87);z=random.uniform(-69,43)
   if not allowed(x,z,5.2):continue
   density=.38+.22*math.sin(x*.15+math.sin(z*.2))
   if random.random()>density:continue
   if height(x,z)>23:continue
   sc=random.uniform(.5,1.25);clearance=max(1.35,sc*1.55)
   if not clear_of_props(x,z,clearance):continue
   meta['instances'].append({'key':'prop_fir_'+str(random.randrange(3)),'position':[x,height(x,z)-.1,z],'scale':[sc,sc*random.uniform(.85,1.3),sc],'yaw':random.uniform(0,math.tau)})
   occupied.append((x,z,clearance));tree_count+=1
 # Shoulder cliff groups, rather than loose isolated boulders on empty plains.
 for side in [-1,1]:
  for j in range(30):
   z=-40+j*2.4;x=side*(15.5+2.2*math.sin(z*.19))
   if not allowed(x,z,7.5):continue
   sc=random.uniform(1.2,3.8)
   if not clear_of_props(x,z,max(1.0,sc*.75)):continue
   meta['instances'].append({'key':('prop_snowrock_' if ice else 'prop_basalt_')+str(j%3),'position':[x,height(x,z)-sc*.25,z],'scale':[sc,sc*random.uniform(1,2),sc*.8],'yaw':random.uniform(0,math.tau)})
   occupied.append((x,z,max(1.0,sc*.75)))
 if not ice:
  # Jagged basalt stacks and ruined towers emerge from the lava sea.
  for _ in range(210):
   x=random.uniform(-82,82);z=random.uniform(-65,43)
   if c['near_route'](x,z,route)<5.5:continue
   if min(math.hypot(x-a['position'][0],z-a['position'][2]) for a in spots)<4:continue
   y=height(x,z);h=random.uniform(2,10);r=random.uniform(.6,2.3)
   tube('Basalt needle',(x,y-.8,z),(x+random.uniform(-.8,.8),y+h,z),r,basalt,r2=r*.08,verts=random.choice([5,6,7]))
   if random.random()<.25:meta['fires'].append([x,y+h*.3,z])
  for x,z in [(-44,-30),(-27,26),(20,27),(41,-31)]:
   y=max(-1,height(x,z));tube('Ruined sentinel tower',(x,y-1,z),(x,y+5,z),1.5,basalt,verts=12)
   for j in range(5):box('Ruined crenel',(x+math.cos(j*math.tau/5)*1.3,y+5,z+math.sin(j*math.tau/5)*1.3),(.5,1,.5),basalt)
 for _ in range(2600):
  x=random.uniform(-69,69);z=random.uniform(-53,35)
  if not allowed(x,z,7.5):continue
  sc=random.uniform(.55,2.2);clearance=max(1.0,sc*.80)
  if not clear_of_props(x,z,clearance):continue
  meta['instances'].append({'key':('prop_snowrock_' if ice else 'prop_basalt_')+str(random.randrange(3)),'position':[x,height(x,z)-.15,z],'scale':[sc*random.uniform(.7,1.7),sc*random.uniform(.7,1.7),sc*random.uniform(.8,1.4)],'yaw':random.uniform(0,math.tau)})
  occupied.append((x,z,clearance))
  if not ice and sc>1.7:
   tube('Charred crooked tree',(x,height(x,z),z),(x+.3,height(x,z)+3.2,z-.2),.13,wood,r2=.025)
   tube('Broken limb',(x+.2,height(x,z)+1.8,z),(x+1.1,height(x,z)+2.4,z+.4),.06,wood,r2=.01)
 c['FAST_WORLD']=False;c['flush_world']();c['export']('world_'+mapid)
 path=c['R']/'data/landscapes.json';existing=json.loads(path.read_text()) if path.exists() else {};existing[mapid]=meta
 path.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n')
