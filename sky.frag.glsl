#version 330

out vec3 fragment_color;

in vec4 position;

#define PI 3.14159

float grid(float altitude, float azimuth) {
    return 1.0 - step(0.4, mod(altitude, 15)) * step(0.4, mod(azimuth, 15));
}

void main(void) {
    vec3 sun_position = normalize(vec3(0.7, 0.7, 0.0));
    vec3 normal_position = normalize(position.xyz);

    float sun = 1.0 - smoothstep(0.01, 0.015, distance(normal_position, sun_position));

    vec3 sky1 = vec3(0.29, 0.74, 0.98);
    vec3 sky2 = vec3(1.0, 1.0, 1.0);

    float altitude = 360.0 * atan(normal_position.y / length(normal_position.xz)) / (2.0 * PI);
    float azimuth = 360.0 * atan(normal_position.z / normal_position.x) / (2.0 * PI);

    fragment_color = mix(sky2, sky1, normal_position.y);
    fragment_color += vec3(sun);
    fragment_color += vec3(0.0, 1.0, 0.0) * grid(altitude, azimuth);
}
