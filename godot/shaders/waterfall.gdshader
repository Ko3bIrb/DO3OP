shader_type spatial;
render_mode cull_disabled,depth_prepass_alpha;
uniform int mode=1;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.),f.x),f.y);}
void fragment(){
 float streak=n(vec2(UV.x*22.,UV.y*6.-TIME*2.2));
 float fine=n(vec2(UV.x*47.,UV.y*15.-TIME*5.));
 float edge=smoothstep(0.,.16,UV.x)*(1.-smoothstep(.84,1.,UV.x));
 float foam=smoothstep(.42,.90,streak*.7+fine*.45);
 ALBEDO=mix(vec3(.12,.34,.41),vec3(.73,.87,.89),foam);
 ALPHA=edge*mix(.42,.95,foam)*smoothstep(0.,.03,UV.y)*(1.-smoothstep(.94,1.,UV.y));
 ROUGHNESS=.3;METALLIC=.08;EMISSION=vec3(.02,.045,.05);
}
