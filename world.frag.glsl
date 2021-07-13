#version 330

out vec3 fragment_color;

uniform sampler2DArray texture_array_sampler;
uniform sampler2D shadow_map;

in vec3 local_color;
in vec3 local_normal;
in vec3 interpolated_tex_coords;
in vec3 interpolated_position;
in vec4 frag_pos_light_space;

uniform vec3 camera;
uniform vec3 sun_position;
// in float interpolated_shading_value;

float compute_shadow(vec4 frag_pos_light_space, float bias) {
	vec3 projCoords = frag_pos_light_space.xyz / frag_pos_light_space.w;

	projCoords = projCoords * 0.5 + 0.5;
	if (projCoords.z > 1.0) {
	   return 0.0;
	}

	float currentDepth = projCoords.z;

	float shadow = 0.0;
	vec2 texelSize = 1.0 / textureSize(shadow_map, 0);
	for(int x = -1; x <= 1; ++x)
	{
	    for(int y = -1; y <= 1; ++y)
	    {
		  float pcfDepth = texture(shadow_map, projCoords.xy + vec2(x, y) * texelSize).r; 
		  shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;        
	    }    
	}

	shadow /= 9.0;
	return shadow;
}

void main(void) {
	if (interpolated_tex_coords.z < -1) {
		discard; // Deleted!
	}

	vec4 albedo = interpolated_tex_coords.z >= 0 ? texture(texture_array_sampler, interpolated_tex_coords) : vec4(local_color, 1);

//	fragment_colour = texture_colour * interpolated_shading_value;
//	if (texture_colour.a == 0.0) { // discard if texel's alpha component is 0 (texel is transparent)
//		discard;
//	}

//	float fog = clamp(1 - length(camera - interpolated_position) / 60, 0.5, 1);

	float specular_strength = 0.5;

	vec3 sun_color = vec3(smoothstep(0, 0.1, sun_position.y), smoothstep(0, 0.2, sun_position.y), smoothstep(0, 0.3, sun_position.y)) * vec3(0.6, 0.6, 0.6);

	vec3 view_dir = normalize(camera - interpolated_position);
	vec3 reflect_dir = reflect(-sun_position, local_normal);

	float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 32);
	vec3 specular = specular_strength * spec * sun_color;

	vec3 light_direction = normalize(sun_position);
	vec3 diffuse = sun_color * max(0, dot(local_normal, light_direction));
	vec3 ambient = 0.5 * vec3(0.7, 0.7, 0.9);

	float bias = max(0.008 * (1.0 - dot(local_normal, light_direction)), 0.00005);  
	float shadow = compute_shadow(frag_pos_light_space, bias);

	fragment_color = ((1.0 - shadow) * (diffuse + specular) + ambient) * albedo.rgb;
}
