import { createMemoryHistory } from 'vue-router'
import { createAppRouter } from './router'

describe('application routes', () => {
  it('opens the board-game collection with a stable path', async () => {
    const router = createAppRouter(createMemoryHistory())

    await router.push('/collections/board-games')

    expect(router.currentRoute.value.name).toBe('board-games')
    expect(router.currentRoute.value.fullPath).toBe('/collections/board-games')
  })

  it('opens a game with a stable path', async () => {
    const router = createAppRouter(createMemoryHistory())

    await router.push('/games/junqi')

    expect(router.currentRoute.value.name).toBe('game')
    expect(router.currentRoute.value.params.gameKey).toBe('junqi')
  })

  it('normalizes room codes in invitation paths', async () => {
    const router = createAppRouter(createMemoryHistory())

    await router.push('/games/xiangqi/rooms/a1b2')

    expect(router.currentRoute.value.name).toBe('room')
    expect(router.currentRoute.value.fullPath).toBe('/games/xiangqi/rooms/A1B2')
  })

  it('redirects legacy query invitations to the room route', async () => {
    const router = createAppRouter(createMemoryHistory())

    await router.push('/?game=avalon&room=h76x')

    expect(router.currentRoute.value.fullPath).toBe('/games/avalon/rooms/H76X')
  })

  it('keeps room-only legacy Avalon invitations working', async () => {
    const router = createAppRouter(createMemoryHistory())

    await router.push('/?room=test')

    expect(router.currentRoute.value.fullPath).toBe('/games/avalon/rooms/TEST')
  })

  it('returns invalid games and room codes to a valid page', async () => {
    const router = createAppRouter(createMemoryHistory())

    await router.push('/games/not-a-game')
    expect(router.currentRoute.value.fullPath).toBe('/')

    await router.push('/games/go/rooms/XX')
    expect(router.currentRoute.value.fullPath).toBe('/games/go')
  })
})
