import V3 from './V3'

class Box3 {
  constructor (min, max) {
    if (typeof min === 'object' && typeof max === 'object' &&
        min.x !== undefined && min.y !== undefined && min.z !== undefined &&
        max.x !== undefined && max.y !== undefined && max.z !== undefined) {
      this.min = new V3(min)
      this.max = new V3(max)
      this.valid = true
    } else if (min === undefined && max === undefined) {
      this.min = new V3(Infinity, Infinity, Infinity)
      this.max = new V3(-Infinity, -Infinity, -Infinity)
      this.valid = false
    } else {
      throw Error('Illegal construction - must use { x, y, z } objects')
    }
  }

  equals (other) {
    if (!this.valid) {
      throw Error('Box3 is invalid')
    }
    return ((this.min.equals(other.min)) &&
            (this.max.equals(other.max)))
  }

  get width () {
    if (!this.valid) {
      throw Error('Box3 is invalid')
    }
    return this.max.x - this.min.x
  }

  get depth () {
    if (!this.valid) {
      throw Error('Box3 is invalid')
    }
    return this.max.y - this.min.y
  }

  get height () {
    if (!this.valid) {
      throw Error('Box3 is invalid')
    }
    return this.max.z - this.min.z
  }

  expandByPoint (p) {
    this.min = new V3(
      Math.min(this.min.x, p.x),
      Math.min(this.min.y, p.y),
      Math.min(this.min.z, p.z)
    )
    this.max = new V3(
      Math.max(this.max.x, p.x),
      Math.max(this.max.y, p.y),
      Math.max(this.max.z, p.z)
    )
    this.valid = true
    return this
  }

  expandByPoints (points) {
    points.forEach(point => {
      this.expandByPoint(point)
    }, this)
    return this
  }

  isPointInside (p) {
    return (
      (p.x >= this.min.x) &&
      (p.y >= this.min.y) &&
      (p.z >= this.min.z) &&
      (p.x <= this.max.x) &&
      (p.y <= this.max.y) &&
      (p.z <= this.max.z))
  }
}

Box3.fromPoints = (points) => {
  return new Box3().expandByPoints(points)
}

export default Box3
