shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform vec4 tint : source_color = vec4(1.,.27,.025,1.);
void vertex(){MODELVIEW_MATRIX=VIEW_MATRIX*mat4(INV_VIEW_MATRIX[0],INV_VIEW_MATRIX[1],INV_VIEW_MATRIX[2],MODEL_MATRIX[3]);}
void fragment(){
 vec2 p=UV*2.-1.;float t=TIME;float bend=sin(p.y*7.-t*4.)*.12+sin(p.y*13.-t*6.)*.05;
 float shape=UV.y*.75+.05;float edge=1.-smoothstep(shape*.65,shape,abs(p.x-bend));
 float tip=smoothstep(0.,.15,UV.y)*(1.-smoothstep(.8,1.,UV.y));
 ALBEDO=mix(vec3(1.,.8,.3),tint.rgb,1.-UV.y);EMISSION=ALBEDO*1.5;
 ALPHA=edge*tip*.82;
}
