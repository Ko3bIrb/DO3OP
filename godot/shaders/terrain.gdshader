shader_type spatial;
render_mode cull_back;
uniform bool winter=true;
varying vec3 world;
varying vec3 slope;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float n(vec2 p){vec2 a=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(a),hash(a+vec2(1,0)),f.x),mix(hash(a+vec2(0,1)),hash(a+vec2(1,1)),f.x),f.y);}
void vertex(){world=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;slope=normalize(mat3(MODEL_MATRIX)*NORMAL);}
void fragment(){
 float grain=n(world.xz*2.)*.03+n(world.xz*.16)*.08;
 if(winter){
  float coat=smoothstep(.40,.74,normalize(slope).y+(n(world.xz*.24)-.5)*.1)*smoothstep(-1.0,.25,world.y);
  ALBEDO=mix(vec3(.15,.20,.24)+grain,vec3(.58,.68,.74)+grain*.4,coat);
  ROUGHNESS=mix(.75,.96,coat);METALLIC=.03;
 }else{
  float cracks=1.-smoothstep(.01,.045,abs(n(world.xz*.85)-.5));
  float heat=cracks*smoothstep(.60,.82,n(world.xz*.14))*(1.-smoothstep(2.,7.,world.y));
  ALBEDO=mix(vec3(.025,.013,.009),vec3(.09,.045,.025),n(world.xz*.18))+grain*.10;
  EMISSION=vec3(1.6,.16,.008)*heat;
  ROUGHNESS=.83;METALLIC=.1;
 }
}
