shader_type spatial;
render_mode cull_disabled;
uniform int mode = 0; // 0 bay, 1 waterfall, 2 molten rock
varying vec3 world;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p);vec2 f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
void vertex(){world=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;if(mode==0){VERTEX.y+=sin(world.x*1.6+TIME*.7)*.025+cos(world.z*1.2-TIME*.5)*.018;}}
void fragment(){
 if(mode==2){
  vec2 p=world.xz*.19;
  vec2 flow=vec2(noise(p+vec2(TIME*.015,0.)),noise(p+vec2(13.7,-TIME*.012)));
  float broad=noise(p+flow*2.5)*.62+noise(p*2.4+flow)*.26+noise(p*5.+flow)*.12;
  float crust=smoothstep(.48,.69,noise(p*3.3+flow*1.7));
  float heat=smoothstep(.26,.70,broad)*(1.-crust*.91);
  ALBEDO=mix(vec3(.025,.012,.009),vec3(.33,.035,.002),heat);
  EMISSION=vec3(2.8,.27,.008)*heat*heat;ROUGHNESS=mix(.94,.44,heat);
 } else if(mode==1){
  float stream=noise(vec2(world.x*4.,world.z*.6+TIME*4.0))+noise(vec2(world.x*9.,world.y*.3+TIME*5.0))*.5;
  ALBEDO=mix(vec3(.08,.25,.32),vec3(.73,.88,.9),smoothstep(.3,1.2,stream));
  EMISSION=vec3(.035,.065,.07);ROUGHNESS=.2;METALLIC=.15;
 } else {
  vec2 p=world.xz;float wave=sin(p.x*2.+TIME*.9)*cos(p.y*1.7-TIME*.6);
  ALBEDO=mix(vec3(.025,.11,.15),vec3(.055,.27,.32),noise(p*.12));
  NORMAL=normalize(NORMAL+vec3(cos(p.x*2.+TIME*.9)*.08,0.,sin(p.y*1.7-TIME*.6)*.06));
  METALLIC=.3;ROUGHNESS=.16;SPECULAR=.8;EMISSION=vec3(.006,.016,.02);
 }
}
