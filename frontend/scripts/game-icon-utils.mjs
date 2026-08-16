export const expectedGameIconSize = 768

function readUint24LE(buffer, offset) {
  return buffer[offset] | (buffer[offset + 1] << 8) | (buffer[offset + 2] << 16)
}

export function readWebpDimensions(buffer, filename) {
  if (
    buffer.length < 30
    || buffer.toString('ascii', 0, 4) !== 'RIFF'
    || buffer.toString('ascii', 8, 12) !== 'WEBP'
  ) {
    throw new Error(`${filename} is not a valid WebP file`)
  }

  let chunkOffset = 12
  while (chunkOffset + 8 <= buffer.length) {
    const chunkType = buffer.toString('ascii', chunkOffset, chunkOffset + 4)
    const chunkSize = buffer.readUInt32LE(chunkOffset + 4)
    const dataOffset = chunkOffset + 8

    if (chunkType === 'VP8 ' && dataOffset + 10 <= buffer.length) {
      return {
        width: buffer.readUInt16LE(dataOffset + 6) & 0x3fff,
        height: buffer.readUInt16LE(dataOffset + 8) & 0x3fff,
      }
    }

    if (chunkType === 'VP8L' && dataOffset + 5 <= buffer.length) {
      const bits = buffer.readUInt32LE(dataOffset + 1)
      return {
        width: (bits & 0x3fff) + 1,
        height: ((bits >>> 14) & 0x3fff) + 1,
      }
    }

    if (chunkType === 'VP8X' && dataOffset + 10 <= buffer.length) {
      return {
        width: readUint24LE(buffer, dataOffset + 4) + 1,
        height: readUint24LE(buffer, dataOffset + 7) + 1,
      }
    }

    chunkOffset = dataOffset + chunkSize + (chunkSize % 2)
  }

  throw new Error(`${filename} has no supported WebP image chunk`)
}

export function verifyGameIconBuffer(buffer, filename) {
  const dimensions = readWebpDimensions(buffer, filename)
  if (
    dimensions.width !== expectedGameIconSize
    || dimensions.height !== expectedGameIconSize
  ) {
    throw new Error(
      `${filename} is ${dimensions.width}x${dimensions.height}; `
      + `expected ${expectedGameIconSize}x${expectedGameIconSize}`,
    )
  }
}
