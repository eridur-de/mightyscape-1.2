varying vec3 fNormal;
varying vec4 fFrontColor;

vec3 ambientLight = vec3(0.2,0.2,0.2);
vec3 directionnalLight = normalize(vec3(10,5,7));
vec3 directionnalLightFactor = vec3(0.5,0.5,0.5);

uniform sampler2D tex;

void main() {

    vec3 ambientFactor = ambientLight;
    vec3 lambertFactor = max(vec3(0.0,0.0,0.0), dot(directionnalLight, fNormal) * directionnalLightFactor);
    vec4 noTexColor = vec4(ambientFactor + lambertFactor, 1.0);

    vec4 color = texture2D(tex, gl_TexCoord[0].st);

    vec4 fragColor = noTexColor * color;
    gl_FragColor = fragColor * fFrontColor;

}

