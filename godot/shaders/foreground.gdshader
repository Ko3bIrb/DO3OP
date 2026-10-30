shader_type spatial;
render_mode cull_disabled,depth_draw_never,depth_test_disabled;
uniform vec4 tint : source_color = vec4(1.0);

void fragment(){
 ALBEDO=tint.rgb;
 ROUGHNESS=.78;
 METALLIC=.04;
 EMISSION=tint.rgb*.035;
}
