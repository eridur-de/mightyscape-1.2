import V3 from './V3'

const dist = (a, b) => {
  return Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2) + Math.pow(a.z - b.z, 2))
}

class Line3 {
  constructor (a, b) {
    if ((typeof a !== 'object') || (a.x === undefined) || (a.y === undefined) || (a.z === undefined)) {
      throw Error('expected first argument to have x, y and z properties')
    }
    if ((typeof b !== 'object') || (b.x === undefined) || (b.y === undefined) || (b.y === undefined)) {
      throw Error('expected second argument to have x, y and z properties')
    }
    this.a = new V3(a)
    this.b = new V3(b)
  }

  length () {
    return this.a.sub(this.b).length()
  }

  containsPoint (point, eps = 1e-12) {
    return Math.abs(
      dist(this.a, this.b) - dist(point, this.a) - dist(point, this.b)) < eps
  }
}

export default Line3
