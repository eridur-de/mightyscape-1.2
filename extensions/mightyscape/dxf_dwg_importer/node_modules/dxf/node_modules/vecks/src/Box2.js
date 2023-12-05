import V2 from './V2'

class Box2 {
  constructor (min, max) {
    if (typeof min === 'object' && typeof max === 'object' &&
        min.x !== undefined && min.y !== undefined &&
        max.x !== undefined && max.y !== undefined) {
      this.min = new V2(min)
      this.max = new V2(max)
      this.valid = true
    } else if (min === undefined && max === undefined) {
      this.min = new V2(Infinity, Infinity)
      this.max = new V2(-Infinity, -Infinity)
      this.valid = false
    } else {
      throw Error('Illegal construction - must use { x, y } objects')
    }
  }

  equals (other) {
    if (!this.valid) {
      throw Error('Box2 is invalid')
    }
    return ((this.min.equals(other.min)) &&
            (this.max.equals(other.max)))
  }

  get width () {
    if (!this.valid) {
      throw Error('Box2 is invalid')
    }
    return this.max.x - this.min.x
  }

  get height () {
    if (!this.valid) {
      throw Error('Box2 is invalid')
    }
    return this.max.y - this.min.y
  }

  expandByPoint (p) {
    this.min = new V2(
      Math.min(this.min.x, p.x),
      Math.min(this.min.y, p.y))
    this.max = new V2(
      Math.max(this.max.x, p.x),
      Math.max(this.max.y, p.y))
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
      (p.x <= this.max.x) &&
      (p.y <= this.max.y))
  }
}

Box2.fromPoints = (points) => {
  return new Box2().expandByPoints(points)
}

export default Box2
