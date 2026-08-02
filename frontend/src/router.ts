import {
  createRouter,
  createWebHistory,
  type LocationQueryValue,
  type RouterHistory,
} from 'vue-router'
import ArcadeHome from './views/ArcadeHome.vue'
import ArcadeRoom from './views/ArcadeRoom.vue'
import GameHall from './views/GameHall.vue'
import { gameCatalogItem } from './gameCatalog'

function firstQueryValue(value: LocationQueryValue | LocationQueryValue[]): string | null {
  return Array.isArray(value) ? value[0] ?? null : value
}

function normalizedRoomCode(value: unknown): string | null {
  if (typeof value !== 'string') return null
  const roomCode = value.trim().toUpperCase()
  return /^[A-Z0-9]{4,8}$/.test(roomCode) ? roomCode : null
}

export function createAppRouter(history: RouterHistory = createWebHistory()) {
  const router = createRouter({
    history,
    routes: [
      { path: '/', name: 'hall', component: GameHall },
      { path: '/games/:gameKey', name: 'game', component: ArcadeHome },
      {
        path: '/games/:gameKey/rooms/:roomCode',
        name: 'room',
        component: ArcadeRoom,
      },
      { path: '/:pathMatch(.*)*', redirect: { name: 'hall' } },
    ],
    scrollBehavior(to, from, savedPosition) {
      if (savedPosition) return savedPosition
      if (to.path !== from.path) return { top: 0 }
      return undefined
    },
  })

  router.beforeEach((to) => {
    if (to.name === 'hall') {
      const legacyRoom = normalizedRoomCode(firstQueryValue(to.query.room))
      const legacyGameKey = firstQueryValue(to.query.game) ?? (legacyRoom ? 'avalon' : null)
      const legacyGame = gameCatalogItem(legacyGameKey)
      if (legacyGame && legacyRoom) {
        return {
          name: 'room',
          params: { gameKey: legacyGame.key, roomCode: legacyRoom },
          hash: to.hash,
          replace: true,
        }
      }
      if (legacyGame) {
        return {
          name: 'game',
          params: { gameKey: legacyGame.key },
          hash: to.hash,
          replace: true,
        }
      }
      return true
    }

    if (to.name !== 'game' && to.name !== 'room') return true
    const game = gameCatalogItem(to.params.gameKey)
    if (!game) return { name: 'hall', replace: true }
    if (to.name === 'game') return true

    const roomCode = normalizedRoomCode(to.params.roomCode)
    if (!roomCode) {
      return {
        name: 'game',
        params: { gameKey: game.key },
        replace: true,
      }
    }
    if (roomCode !== to.params.roomCode) {
      return {
        name: 'room',
        params: { gameKey: game.key, roomCode },
        query: to.query,
        hash: to.hash,
        replace: true,
      }
    }
    return true
  })

  return router
}

export const router = createAppRouter()
