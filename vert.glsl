#version 330

layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec3 color;
layout(location = 2) in vec3 normal;
layout(location = 3) in vec3 tex_coords;

// layout(location = 2) in float shading_value;

out vec3 local_color;
out vec3 local_normal;
out vec3 interpolated_tex_coords;
out vec3 interpolated_position;

// out float interpolated_shading_value;

uniform mat4 matrix;

void main(void) {
	local_color = color;
	local_normal = normal;

	interpolated_tex_coords = tex_coords;

//	interpolated_shading_value = shading_value;

	interpolated_position = vertex_position;

	gl_Position = matrix * vec4(vertex_position, 1.0);

}
