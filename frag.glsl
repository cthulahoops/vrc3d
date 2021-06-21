#version 330

out vec3 fragment_color;

uniform sampler2DArray texture_array_sampler;

in vec3 local_color;
in vec3 local_normal;
in vec3 interpolated_tex_coords;
in float fog;

// in float interpolated_shading_value;

void main(void) {
	vec4 texture_color = texture(texture_array_sampler, interpolated_tex_coords);

//	fragment_colour = texture_colour * interpolated_shading_value;
//	if (texture_colour.a == 0.0) { // discard if texel's alpha component is 0 (texel is transparent)
//		discard;
//	}

	vec3 light_direction = normalize(vec3(0.3, 0.5, 0.2));
	vec3 diffuse = vec3(0.3, 0.3, 0.2) * max(0, dot(local_normal, light_direction));
	vec3 ambient = vec3(0.7, 0.7, 0.9);
	fragment_color = (diffuse + ambient) * (texture_color.a > 0 ? texture_color.xyz : local_color);
}
