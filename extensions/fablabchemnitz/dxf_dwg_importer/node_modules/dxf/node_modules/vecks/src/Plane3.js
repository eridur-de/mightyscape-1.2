class Plane3 {
  constructor (a, b, c, d) {
    this.a = a
    this.b = b
    this.c = c
    this.d = d
  }

  // Distance to a point
  // http://mathworld.wolfram.com/Point-PlaneDistance.html eq 10
  distanceToPoint (p0) {
    const dd = (this.a * p0.x + this.b * p0.y + this.c * p0.z + this.d) /
      Math.sqrt(this.a * this.a + this.b * this.b + this.c * this.c)
    return dd
  }

  equals (other) {
    return ((this.a === other.a) &&
            (this.b === other.b) &&
            (this.c === other.c) &&
            (this.d === other.d))
  }

  coPlanar (other) {
    const coPlanarAndSameNormal =
      ((this.a === other.a) &&
       (this.b === other.b) &&
       (this.c === other.c) &&
       (this.d === other.d))
    const coPlanarAndReversedNormal =
      ((this.a === -other.a) &&
       (this.b === -other.b) &&
       (this.c === -other.c) &&
       (this.d === -other.d))
    return coPlanarAndSameNormal || coPlanarAndReversedNormal
  }
}

// From point and normal
Plane3.fromPointAndNormal = (p, n) => {
  const a = n.x
  const b = n.y
  const c = n.z
  const d = -(p.x * a + p.y * b + p.z * c)
  return new Plane3(n.x, n.y, n.z, d)
}

Plane3.fromPoints = (points) => {
  let firstCross
  for (let i = 0, il = points.length; i < il; ++i) {
    const ab = points[(i + 1) % il].sub(points[i])
    const bc = points[(i + 2) % il].sub(points[(i + 1) % il])
    const cross = ab.cross(bc)
    if (!(isNaN(cross.length()) || (cross.length() === 0))) {
      if (!firstCross) {
        firstCross = cross.norm()
      } else {
        const same = cross.norm().equals(firstCross, 1e-6)
        const opposite = cross.neg().norm().equals(firstCross, 1e-6)
        if (!(same || opposite)) {
          throw Error('points not on a plane')
        }
      }
    }
  }
  if (!firstCross) {
    throw Error('points not on a plane')
  }
  return Plane3.fromPointAndNormal(points[0], firstCross.norm())
}

export default Plane3
