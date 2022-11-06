import V3 from './V3'

// Quaternion implementation heavily adapted from the Quaternion implementation in THREE.js
// https://github.com/mrdoob/three.js/blob/master/src/math/Quaternion.js

class Quaternion {
  constructor (x, y, z, w) {
    this.x = x
    this.y = y
    this.z = z
    this.w = w
  }

  applyToVec3 (v3) {
    const x = v3.x
    const y = v3.y
    const z = v3.z

    const qx = this.x
    const qy = this.y
    const qz = this.z
    const qw = this.w

    // calculate quat * vector
    const ix = qw * x + qy * z - qz * y
    const iy = qw * y + qz * x - qx * z
    const iz = qw * z + qx * y - qy * x
    const iw = -qx * x - qy * y - qz * z

    // calculate result * inverse quat
    return new V3(
      ix * qw + iw * -qx + iy * -qz - iz * -qy,
      iy * qw + iw * -qy + iz * -qx - ix * -qz,
      iz * qw + iw * -qz + ix * -qy - iy * -qx)
  }
}

Quaternion.fromAxisAngle = (axis, angle) => {
  // http://www.euclideanspace.com/maths/geometry/rotations/conversions/angleToQuaternion/index.htm
  const axisNorm = axis.norm()
  const halfAngle = angle / 2
  const s = Math.sin(halfAngle)
  return new Quaternion(
    axisNorm.x * s,
    axisNorm.y * s,
    axisNorm.z * s,
    Math.cos(halfAngle))
}

export default Quaternion
