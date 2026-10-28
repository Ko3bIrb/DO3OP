shader_type spatial;
render_mode unshaded,blend_mix,cull_disabled,depth_draw_never;
varying vec4 tint;
void vertex(){
 tint=COLOR;vec3 s=vec3(length(MODEL_MATRIX[0].xyz),length(MODEL_MATRIX[1].xyz),length(MODEL_MATRIX[2].xyz));
 MODELVIEW_MATRIX=VIEW_MATRIX*mat4(INV_VIEW_MATRIX[0]*s.x,INV_VIEW_MATRIX[1]*s.y,INV_VIEW_MATRIX[2]*s.z,MODEL_MATRIX[3]);
}
void fragment(){float d=length(UV*2.-1.);float soft=1.-smoothstep(.15,1.,d);ALBEDO=tint.rgb;ALPHA=soft*soft*tint.a;}
