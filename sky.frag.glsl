#version 330

out vec3 fragment_color;

in vec4 position;

uniform sampler2DArray texture_array_sampler;

uniform mat4 celestial_matrix;
uniform vec3 sun_position;
uniform float current_time;
uniform bool show_grid;


#define PI 3.1415926535

float grid(vec2 position) {
    return 1.0 - step(0.1, mod(position.y, 15)) * step(0.1, mod(position.x, 15));
}

#define iSteps 16
#define jSteps 8

vec2 rsi(vec3 r0, vec3 rd, float sr) {
    // ray-sphere intersection that assumes
    // the sphere is centered at the origin.
    // No intersection when result.x > result.y
    float a = dot(rd, rd);
    float b = 2.0 * dot(rd, r0);
    float c = dot(r0, r0) - (sr * sr);
    float d = (b*b) - 4.0*a*c;
    if (d < 0.0) return vec2(1e5,-1e5);
    return vec2(
        (-b - sqrt(d))/(2.0*a),
        (-b + sqrt(d))/(2.0*a)
    );
}

vec3 atmosphere(vec3 r, vec3 r0, vec3 pSun, float iSun, float rPlanet, float rAtmos, vec3 kRlh, float kMie, float shRlh, float shMie, float g) {
    // Normalize the sun and view directions.
    pSun = normalize(pSun);
    r = normalize(r);

    // Calculate the step size of the primary ray.
    vec2 p = rsi(r0, r, rAtmos);
    if (p.x > p.y) return vec3(0,0,0);
    p.y = min(p.y, rsi(r0, r, rPlanet).x);
    float iStepSize = (p.y - p.x) / float(iSteps);

    // Initialize the primary ray time.
    float iTime = 0.0;

    // Initialize accumulators for Rayleigh and Mie scattering.
    vec3 totalRlh = vec3(0,0,0);
    vec3 totalMie = vec3(0,0,0);

    // Initialize optical depth accumulators for the primary ray.
    float iOdRlh = 0.0;
    float iOdMie = 0.0;

    // Calculate the Rayleigh and Mie phases.
    float mu = dot(r, pSun);
    float mumu = mu * mu;
    float gg = g * g;
    float pRlh = 3.0 / (16.0 * PI) * (1.0 + mumu);
    float pMie = 3.0 / (8.0 * PI) * ((1.0 - gg) * (mumu + 1.0)) / (pow(1.0 + gg - 2.0 * mu * g, 1.5) * (2.0 + gg));

    // Sample the primary ray.
    for (int i = 0; i < iSteps; i++) {

        // Calculate the primary ray sample position.
        vec3 iPos = r0 + r * (iTime + iStepSize * 0.5);

        // Calculate the height of the sample.
        float iHeight = length(iPos) - rPlanet;

        // Calculate the optical depth of the Rayleigh and Mie scattering for this step.
        float odStepRlh = exp(-iHeight / shRlh) * iStepSize;
        float odStepMie = exp(-iHeight / shMie) * iStepSize;

        // Accumulate optical depth.
        iOdRlh += odStepRlh;
        iOdMie += odStepMie;

        // Calculate the step size of the secondary ray.
        float jStepSize = rsi(iPos, pSun, rAtmos).y / float(jSteps);

        // Initialize the secondary ray time.
        float jTime = 0.0;

        // Initialize optical depth accumulators for the secondary ray.
        float jOdRlh = 0.0;
        float jOdMie = 0.0;

        // Sample the secondary ray.
        for (int j = 0; j < jSteps; j++) {

            // Calculate the secondary ray sample position.
            vec3 jPos = iPos + pSun * (jTime + jStepSize * 0.5);

            // Calculate the height of the sample.
            float jHeight = length(jPos) - rPlanet;

            // Accumulate the optical depth.
            jOdRlh += exp(-jHeight / shRlh) * jStepSize;
            jOdMie += exp(-jHeight / shMie) * jStepSize;

            // Increment the secondary ray time.
            jTime += jStepSize;
        }

        // Calculate attenuation.
        vec3 attn = exp(-(kMie * (iOdMie + jOdMie) + kRlh * (iOdRlh + jOdRlh)));

        // Accumulate scattering.
        totalRlh += odStepRlh * attn;
        totalMie += odStepMie * attn;

        // Increment the primary ray time.
        iTime += iStepSize;

    }

    // Calculate and return the final color.
    return iSun * (3.0 * pRlh * kRlh * totalRlh + pMie * kMie * totalMie);
}

vec2 angular_position(vec4 position) {
    float altitude = 360.0 * atan(position.y / length(position.xz)) / (2.0 * PI);
    float azimuth = 90.0 + 360.0 * atan(position.z / position.x) / (2.0 * PI);
    if (position.x < 0) {
        azimuth = 180.0 + azimuth;
    }

    return vec2(azimuth, altitude);
}

void main(void) {
    vec3 normal_position = normalize(position.xyz);

    if (position.y < 0) {
        float d = length(normal_position.xz);
	fragment_color = mix(vec3(0.2, 0.3, 0.1), vec3(0.6,0.6,0.6), d / 2.0 );
	return;
    }

    vec3 normal_sun_position = normalize(sun_position);
    float sun = 1.0 - smoothstep(0.01, 0.020, distance(normal_position, normal_sun_position));

    vec3 sky1 = vec3(0.29, 0.74, 0.98);
    vec3 sky2 = vec3(1.0, 1.0, 1.0);

    vec4 celestial_position = celestial_matrix * vec4(normal_position, 1.0);

    vec2 angular_position = angular_position(celestial_position);

    vec4 starmap_color = texture(texture_array_sampler, vec3(angular_position.x / 360.0, (90.0 + angular_position.y) / 180.0, 0));

    vec3 atmosphere_color = atmosphere(
        normal_position,                // normalized ray direction
        vec3(0,6372e3,0),               // ray origin
        sun_position,                   // position of the sun
        22.0,                           // intensity of the sun
        6371e3,                         // radius of the planet in meters
        6471e3,                         // radius of the atmosphere in meters
        1.5 * vec3(5.5e-6, 13.0e-6, 22.4e-6), // Rayleigh scattering coefficient
        21e-6,                          // Mie scattering coefficient
        8e3,                            // Rayleigh scale height
        1.2e3,                          // Mie scale height
        0.998                           // Mie preferred scattering direction
    );
    atmosphere_color = 1.0 - exp(-1.0 * max(atmosphere_color, 0.7 * starmap_color.rgb));
    fragment_color = atmosphere_color; // mix(sky2, sky1, normal_position.y);
//    fragment_color = vec3(azimuth / 360.0);

    // fragment_color += vec3(sun);
    if (show_grid) {
        fragment_color += vec3(0.3, 0.3, 0.3) * grid(angular_position);
    }
}
