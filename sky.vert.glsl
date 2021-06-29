#version 330

layout(location = 0) in vec3 vertex_position;

out vec4 position;

// uniform mat4 projection_matrix;

uniform mat4 projection_matrix;
uniform mat4 rotation_matrix;

void main(void) {
	gl_Position = vec4(vertex_position.x, vertex_position.y, 0.999999, 1.0);

	position = inverse(rotation_matrix) * inverse(projection_matrix) * vec4(vertex_position, 1.0);
}
