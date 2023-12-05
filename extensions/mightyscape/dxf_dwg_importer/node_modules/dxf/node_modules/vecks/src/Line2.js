import V2 from './V2'

const turn = (p1, p2, p3) => {
  const a = p1.x
  const b = p1.y
  const c = p2.x
  const d = p2.y
  const e = p3.x
  const f = p3.y
  const m = (f - b) * (c - a)
  const n = (d - b) * (e - a)
  return (m > n + Number.EPSILON) ? 1 : (m + Number.EPSILON < n) ? -1 : 0
}

// http://stackoverflow.com/a/16725715/35448
const isIntersect = (e1, e2) => {
  const p1 = e1.a
  const p2 = e1.b
  const p3 = e2.a
  const p4 = e2.b
  return (turn(p1, p3, p4) !== turn(p2, p3, p4)) && (turn(p1, p2, p3) !== turn(p1, p2, p4))
}

const getIntersection = (m, n) => {
  // https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection
  const x1 = m.a.x
  const x2 = m.b.x
  const y1 = m.a.y
  const y2 = m.b.y

  const x3 = n.a.x
  const x4 = n.b.x
  const y3 = n.a.y
  const y4 = n.b.y

  const x12 = x1 - x2
  const x34 = x3 - x4
  const y12 = y1 - y2
  const y34 = y3 - y4
  const c = x12 * y34 - y12 * x34

  const px = ((x1 * y2 - y1 * x2) * (x34) - (x12) * (x3 * y4 - y3 * x4)) / c
  const py = ((x1 * y2 - y1 * x2) * (y34) - (y12) * (x3 * y4 - y3 * x4)) / c

  if (isNaN(px) || isNaN(py)) {
    return null
  } else {
    return new V2(px, py)
  }
}

const dist = (a, b) => {
  return Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2))
}

class Line2 {
  constructor (a, b) {
    if ((typeof a !== 'object') || (a.x === undefined) || (a.y === undefined)) {
      throw Error('expected first argument to have x and y properties')
    }
    if ((typeof b !== 'object') || (b.x === undefined) || (b.y === undefined)) {
      throw Error('expected second argument to have x and y properties')
    }
    this.a = new V2(a)
    this.b = new V2(b)
  }

  length () {
    return this.a.sub(this.b).length()
  }

  intersects (other) {
    if (!(other instanceof Line2)) {
      throw new Error('expected argument to be an instance of vecks.Line2')
    }
    return isIntersect(this, other)
  }

  getIntersection (other) {
    if (this.intersects(other)) {
      return getIntersection(this, other)
    } else {
      return null
    }
  }

  containsPoint (point, eps = 1e-12) {
    return Math.abs(
      dist(this.a, this.b) - dist(point, this.a) - dist(point, this.b)) < eps
  }
}

export default Line2
