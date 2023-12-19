class V2 {
  constructor (x, y) {
    if (typeof x === 'object') {
      this.x = x.x
      this.y = x.y
    } else {
      this.x = x
      this.y = y
    }
  }

  equals (other) {
    return ((this.x === other.x) &&
            (this.y === other.y))
  }

  length () {
    return Math.sqrt(this.dot(this))
  }

  neg () {
    return new V2(-this.x, -this.y)
  }

  add (b) {
    return new V2(this.x + b.x, this.y + b.y)
  }

  sub (b) {
    return new V2(this.x - b.x, this.y - b.y)
  }

  multiply (w) {
    return new V2(this.x * w, this.y * w)
  }

  norm () {
    return this.multiply(1 / this.length())
  }

  dot (b) {
    return this.x * b.x + this.y * b.y
  }
}

export default V2
