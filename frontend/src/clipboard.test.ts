import { copyText } from './clipboard'

describe('copyText', () => {
  it('uses the synchronous fallback on an insecure LAN page', async () => {
    const execCommand = vi.fn(() => true)
    Object.defineProperty(window, 'isSecureContext', {
      configurable: true,
      value: false,
    })
    Object.defineProperty(document, 'execCommand', {
      configurable: true,
      value: execCommand,
    })

    await expect(copyText('http://192.168.0.104:8800/?room=TEST')).resolves.toBe(true)
    expect(execCommand).toHaveBeenCalledWith('copy')
    expect(document.querySelector('textarea')).toBeNull()
  })

  it('reports failure when the browser blocks both copy methods', async () => {
    Object.defineProperty(window, 'isSecureContext', {
      configurable: true,
      value: false,
    })
    Object.defineProperty(document, 'execCommand', {
      configurable: true,
      value: vi.fn(() => {
        throw new Error('copy blocked')
      }),
    })

    await expect(copyText('invite')).resolves.toBe(false)
    expect(document.querySelector('textarea')).toBeNull()
  })
})
