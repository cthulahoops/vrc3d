#version 330

out vec3 fragment_color;

uniform sampler2DArray texture_array_sampler;

in vec3 local_color;
in vec3 local_normal;
in vec3 interpolated_tex_coords;
in vec3 interpolated_position;

uniform vec3 camera;
uniform vec3 sun_position;
// in float interpolated_shading_value;

void main(void) {
	if (interpolated_tex_coords.z < -1) {
		discard; // Deleted!
	}

	vec4 texture_color = interpolated_tex_coords.z >= 0 ? texture(texture_array_sampler, interpolated_tex_coords) : vec4(local_color, 1);


//	fragment_colour = texture_colour * interpolated_shading_value;
//	if (texture_colour.a == 0.0) { // discard if texel's alpha component is 0 (texel is transparent)
//		discard;
//	}

	float fog = clamp(1 - length(camera - interpolated_position) / 60, 0.5, 1);

	vec3 light_direction = normalize(sun_position);
	vec3 diffuse = vec3(0.3, 0.3, 0.2) * max(0, dot(local_normal, light_direction));
	vec3 ambient = vec3(0.7, 0.7, 0.9);

	fragment_color = fog * (diffuse + ambient) * texture_color.rgb + vec3(0.5, 0.5, 0.5) * (1 - fog);
}
