varying vec3 fNormal;
varying vec4 fTexCoord;
varying vec4 fFrontColor;

void main() {

    fNormal = gl_Normal;
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_TexCoord[0] = gl_TextureMatrix[0] * gl_MultiTexCoord0;
    fFrontColor = gl_Color;

}
