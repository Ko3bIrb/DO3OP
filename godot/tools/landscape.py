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
  for strand,(cx,width,top,bottom,phase) in enumerate([(-1.2,1.05,-46.8,-33.2,.0),(.9,.7,-46.1,-32.4,1.5),(2.0,.38,-44.8,-33.8,3.2)]):
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
   c['emit']([tuple(c['V'](v)) for v in vv],ff,cascade,uv=[(j/4,i/steps) for i in range(steps+1) for j in range(5)],smooth=True)
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
 # Three strips provide a broken, slightly sunken edge and a crowned paving surface.
 vv=[]
 for i,p in enumerate(samples):
  tangent=(samples[min(i+1,len(samples)-1)]-samples[max(0,i-1)]).normalized();normal=Vector((-tangent.z,0,tangent.x))
  width=1.73+.12*math.sin(i*.61)+.06*math.sin(i*1.8)
  for u in [-1,-.82,0,.82,1]:
   vv.append(p+normal*width*u+Vector((0,.095-.065*abs(u),0)))
 ff=[]
 for i in range(len(samples)-1):
  if ice and abs((samples[i].x+samples[i+1].x)*.5)<5.5 and 13<samples[i].z<17:continue
  for j in range(4):
   k=i*5+j;ff.append((k,k+5,k+6,k+1))
 mesh('Worn connected causeway',vv,ff,roadmat,smooth=True)
 for i in range(0,len(samples),6):
  p=samples[i]
  if ice and abs(p.x)<6 and p.z>12:continue
  tangent=(samples[min(i+1,len(samples)-1)]-samples[max(0,i-1)]).normalized();normal=Vector((-tangent.z,0,tangent.x))
  for side in [-1,1]:
   at=p+normal*side*1.78
   if random.random()<.22:continue
   size=random.uniform(.23,.40);box('Chipped paving edge',(at.x,.1,at.z),(size,.20,random.uniform(.3,.60)),stone if ice else basalt,bevel=.075)
  if i%42==0:
   at=p+normal*2.6;c['lantern'](at,ice)
   meta.setdefault('lanterns',[]).append([at.x,at.y+2.25,at.z])
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
 # Human landmarks make the road's destination and defensive purpose legible.
 if ice:
  camp(-32,1)
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
  for x,z in [(27,5),(30,17),(-30,4),(-34,3)]:
   y=height(x,z)
   for k in range(3):box('Camp supply crate',(x+k*.65,y+.3,z),(.6,.6,.6),wood,bevel=.05)
  for side in [-1,1]:
   for z in range(3,20,2):
    x=side*28;y=height(x,z)
    tube('Settlement fence post',(x,y,z),(x,y+1,z),.08,wood)
    tube('Settlement fence rail',(x,y+.65,z),(x,height(x,z+2)+.65,z+2),.065,wood)
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

 # Clustered, varied vegetation/stone props, instanced by the runtime.
 reserved=[(-32,1,6),(36,10,11)] if ice else [(36,10,10),(-5,3,7)]
 def allowed(x,z,margin=4):
  if c['near_route'](x,z,route)<margin:return False
  if min(math.hypot(x-s['position'][0],z-s['position'][2]) for s in spots)<3.1:return False
  if any(math.hypot(x-a,z-b)<r for a,b,r in reserved):return False
  if min(math.hypot(x-route[k][0],z-route[k][2]) for k in [0,-1])<8:return False
  return height(x,z)>(-.75 if ice else -1.0)
 if ice:
  clusters=[(-48,12,9,60),(-36,-3,7,19),(28,-3,8,22),(48,18,10,32),(-54,-35,8,22),(57,-37,9,25),(-35,-48,8,21),(37,-46,7,19),(-23,29,9,23),(23,29,9,24)]
  for cx,cz,radius,count in clusters:
   for _ in range(count*4):
    if count<=0:break
    a=random.uniform(0,math.tau);r=radius*math.sqrt(random.random());x=cx+math.cos(a)*r;z=cz+math.sin(a)*r
    if not allowed(x,z):continue
    sc=random.uniform(.55,1.35);meta['instances'].append({'key':'prop_fir_'+str(random.randrange(3)),'position':[x,height(x,z),z],'scale':[sc*random.uniform(.85,1.05),sc*random.uniform(.9,1.35),sc*random.uniform(.85,1.1)],'yaw':random.uniform(0,math.tau)})
    count-=1
 # Continuous forest across the valley shoulders; small clearings remain around play.
 if ice:
  for _ in range(3000):
   x=random.uniform(-87,87);z=random.uniform(-69,43)
   if not allowed(x,z,4.6):continue
   density=.52+.30*math.sin(x*.15+math.sin(z*.2))
   if random.random()>density:continue
   if height(x,z)>23:continue
   sc=random.uniform(.5,1.25)
   meta['instances'].append({'key':'prop_fir_'+str(random.randrange(3)),'position':[x,height(x,z)-.1,z],'scale':[sc,sc*random.uniform(.85,1.3),sc],'yaw':random.uniform(0,math.tau)})
 # Shoulder cliff groups, rather than loose isolated boulders on empty plains.
 for side in [-1,1]:
  for j in range(30):
   z=-40+j*2.4;x=side*(15.5+2.2*math.sin(z*.19))
   if not allowed(x,z,5.2):continue
   sc=random.uniform(1.2,3.8)
   meta['instances'].append({'key':('prop_snowrock_' if ice else 'prop_basalt_')+str(j%3),'position':[x,height(x,z)-sc*.25,z],'scale':[sc,sc*random.uniform(1,2),sc*.8],'yaw':random.uniform(0,math.tau)})
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
 for _ in range(650):
  x=random.uniform(-69,69);z=random.uniform(-53,35)
  if not allowed(x,z,5.5):continue
  sc=random.uniform(.55,2.2)
  meta['instances'].append({'key':('prop_snowrock_' if ice else 'prop_basalt_')+str(random.randrange(3)),'position':[x,height(x,z)-.15,z],'scale':[sc*random.uniform(.7,1.7),sc*random.uniform(.7,1.7),sc*random.uniform(.8,1.4)],'yaw':random.uniform(0,math.tau)})
  if not ice and sc>1.7:
   tube('Charred crooked tree',(x,height(x,z),z),(x+.3,height(x,z)+3.2,z-.2),.13,wood,r2=.025)
   tube('Broken limb',(x+.2,height(x,z)+1.8,z),(x+1.1,height(x,z)+2.4,z+.4),.06,wood,r2=.01)
 c['FAST_WORLD']=False;c['flush_world']();c['export']('world_'+mapid)
 path=c['R']/'data/landscapes.json';existing=json.loads(path.read_text()) if path.exists() else {};existing[mapid]=meta
 path.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n')
