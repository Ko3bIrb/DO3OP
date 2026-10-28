shader_type spatial;
render_mode unshaded,blend_add,cull_disabled,depth_draw_never;
void fragment(){ALBEDO=COLOR.rgb;EMISSION=COLOR.rgb*.7;ALPHA=COLOR.a;}
