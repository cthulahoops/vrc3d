#version 330 core
out vec3 FragColor;
  
in vec2 tex_coords;

uniform sampler2D depthMap;

void main()
{             
    float depthValue = texture(depthMap, tex_coords).r;
    FragColor = depthValue * vec3(0.0, 1.0, 0.0);
}  
