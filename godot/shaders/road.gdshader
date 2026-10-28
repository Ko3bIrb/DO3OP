shader_type spatial;
uniform bool winter=true;
varying vec3 world;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void vertex(){world=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){
 vec2 p=world.xz*1.65;p.x+=mod(floor(p.y),2.)*.5;
 vec2 f=fract(p),id=floor(p);
 float joint=min(min(f.x,1.-f.x),min(f.y,1.-f.y));
 float slab=smoothstep(.035,.11,joint);
 float variation=hash(id);
 vec3 stone=winter?vec3(.25,.30,.33):vec3(.10,.065,.048);
 ALBEDO=mix(stone*.28,stone*(.78+variation*.45),slab);
 if(winter){float frost=step(.87,hash(floor(world.xz*3.)))*.2;ALBEDO+=vec3(.30,.38,.43)*frost;}
 ROUGHNESS=.87;METALLIC=.03;
}
