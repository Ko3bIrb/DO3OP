shader_type spatial;
render_mode cull_disabled;
uniform int mode = 0; // 0 bay, 1 waterfall, 2 molten rock
varying vec3 world;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p);vec2 f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
void vertex(){world=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;if(mode==0){VERTEX.y+=sin(world.x*1.6+TIME*.7)*.025+cos(world.z*1.2-TIME*.5)*.018;}}
void fragment(){
 if(mode==2){
  vec2 p=world.xz*.12;
  vec2 warp=vec2(noise(p*2.1+vec2(TIME*.012,0.)),noise(p*2.1+vec2(7.3,-TIME*.009)))-.5;
  float channels=sin((p.x+warp.x*1.8)*3.2+(p.y+warp.y)*1.35+sin(p.y*1.7)*1.4);
  float veins=smoothstep(.72,.98,channels*.5+.5);
  float soft=noise(p*1.8+warp*2.0)*.32+noise(p*4.2+warp)*.12;
  float heat=smoothstep(.62,.88,veins+soft*.35);
  float crust=smoothstep(.38,.62,noise(p*2.7+warp*1.5));
  heat*=1.-crust*.72;
  ALBEDO=mix(vec3(.018,.009,.007),vec3(.20,.022,.006),heat);
  EMISSION=vec3(1.35,.12,.006)*heat*heat;ROUGHNESS=mix(.95,.48,heat);
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
