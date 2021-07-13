#version 330 core
layout (location = 0) in vec3 vertex_position;

out vec2 tex_coords;

void main()
{
        gl_Position = vec4(0.5 * vertex_position + vec3(0.4, 0.4, 0.0), 1.0);
        tex_coords = vec2(vertex_position.x, 1.0 - vertex_position.y);
}
