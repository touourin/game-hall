import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadePhase, ArcadeSnapshot } from '../../types/arcade'
import OneNightWerewolfTable from './OneNightWerewolfTable.vue'

const role = (code: string, label: string, alignment = 'village') => ({
  code,
  label,
  alignment,
  description: `${label}的身份说明`,
})

function snapshot(phase: ArcadePhase = 'role_reveal'): ArcadeSnapshot {
  const players = ['甲', '乙', '丙'].map((name, seat) => ({
    id: `p${seat + 1}`,
    name,
    seat,
    connected: true,
    isHost: seat === 0,
  }))
  return {
    revision: 1,
    roomCode: 'MOON',
    gameKey: 'one_night_werewolf',
    gameName: '一夜狼人',
    phase,
    options: { rolePreset: 'standard', discussionSeconds: 300, allowSpectators: false },
    hostId: 'p1',
    self: { id: 'p1', name: '甲', seat: 0 },
    players,
    requiredPlayers: 10,
    minimumPlayers: 3,
    roundNumber: 1,
    winner: phase === 'finished' ? 'village' : null,
    winnerPlayerIds: phase === 'finished' ? ['p1', 'p3'] : [],
    winReason: phase === 'finished' ? '村庄成功处决了狼人' : null,
    actions: {
      canStart: false,
      canRestart: phase === 'finished',
      canAct: phase !== 'finished',
      canKickPlayers: false,
      canDissolve: false,
      canEditRules: false,
      canRequestUndo: false,
      canRequestDraw: false,
      canResolveRequest: false,
    },
    rematchReadyPlayerIds: [],
    request: null,
    chat: { maxLength: 300, messages: [] },
    game: {
      roleDeck: [role('werewolf', '狼人', 'werewolf'), role('seer', '预言家')],
      presetLabel: '标准疑云',
      self: {
        initialRole: role('seer', '预言家'),
        finalRole: phase === 'finished' ? role('villager', '村民') : null,
        nightResults: phase === 'discussion' ? [{ kind: 'seer', text: '乙的牌是狼人' }] : [],
      },
      roleConfirmedCount: 1,
      night: { isMyTurn: false, prompt: null },
      discussionEndsAt: phase === 'discussion' ? new Date(Date.now() + 120_000).toISOString() : null,
      votesSubmitted: phase === 'voting' ? 1 : 0,
      hasVoted: false,
      resolution: phase === 'finished' ? {
        players: players.map((player, index) => ({
          playerId: player.id,
          initialRole: index === 1 ? role('werewolf', '狼人', 'werewolf') : role('villager', '村民'),
          finalRole: index === 1 ? role('werewolf', '狼人', 'werewolf') : role('villager', '村民'),
          votedForId: index === 1 ? 'p1' : 'p2',
          voteCount: index === 1 ? 2 : index === 0 ? 1 : 0,
          eliminated: index === 1,
          won: index !== 1,
        })),
        centerRoles: [role('seer', '预言家'), role('tanner', '皮匠', 'tanner'), role('robber', '强盗')],
      } : null,
      legal: {
        canConfirmRole: phase === 'role_reveal',
        canStartVote: phase === 'discussion',
        voteTargetPlayerIds: phase === 'voting' ? ['p2', 'p3'] : [],
      },
    },
  }
}

describe('OneNightWerewolfTable', () => {
  it('reuses hold-to-reveal before allowing identity confirmation', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(OneNightWerewolfTable, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    const confirm = wrapper.get('.primary-button')
    expect(wrapper.get('.one-night-role-deck').text()).toContain('狼人')
    expect(confirm.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).not.toContain('预言家的身份说明')
    await wrapper.get('.press-reveal-card').trigger('pointerdown')
    expect(wrapper.text()).toContain('预言家的身份说明')
    expect(confirm.attributes('disabled')).toBeUndefined()
    await confirm.trigger('click')
    expect(action).toHaveBeenCalledWith('confirm_role')
  })

  it('shows private night evidence only inside the reveal card during discussion', async () => {
    const pinia = createPinia()
    const wrapper = mount(OneNightWerewolfTable, {
      props: { snapshot: snapshot('discussion') },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).not.toContain('乙的牌是狼人')
    await wrapper.get('.press-reveal-card').trigger('pointerdown')
    expect(wrapper.text()).toContain('乙的牌是狼人')
  })

  it('submits one locked vote and renders final role changes', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(OneNightWerewolfTable, {
      props: { snapshot: snapshot('voting') },
      global: { plugins: [pinia] },
    })

    await wrapper.get('select').setValue('p2')
    await wrapper.get('.final-vote-card .primary-button').trigger('click')
    expect(action).toHaveBeenCalledWith('vote', { targetPlayerId: 'p2' })

    await wrapper.setProps({ snapshot: snapshot('finished') })
    expect(wrapper.findAll('.resolution-player')).toHaveLength(3)
    expect(wrapper.text()).toContain('最终中央三牌')
    expect(wrapper.text()).toContain('被处决')
  })
})
