import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadePhase, ArcadeSnapshot } from '../../types/arcade'
import OneNightWerewolfRules from './OneNightWerewolfRules.vue'
import OneNightWerewolfTable from './OneNightWerewolfTable.vue'
import type { OneNightRole } from './types'

const role = (
  code: string,
  label: string,
  alignment: OneNightRole['alignment'] = 'village',
): OneNightRole => ({
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
    options: { rolePreset: 'standard', allowSpectators: false },
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
      roleGuide: [
        role('werewolf', '狼人', 'werewolf'),
        role('seer', '预言家'),
        role('robber', '强盗'),
        role('villager', '村民'),
      ],
      presetLabel: '标准疑云',
      self: {
        initialRole: role('seer', '预言家'),
        finalRole: phase === 'finished' ? role('villager', '村民') : null,
        nightResults: phase === 'discussion' ? [{ kind: 'seer', text: '乙的牌是狼人' }] : [],
      },
      roleConfirmedCount: 1,
      night: { isMyTurn: false, prompt: null },
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
  it('keeps the full flow, role skills, and victory rules in one guide', () => {
    const wrapper = mount(OneNightWerewolfRules, {
      props: {
        roles: [
          role('werewolf', '狼人', 'werewolf'),
          role('seer', '预言家'),
          role('tanner', '皮匠', 'tanner'),
          role('hunter', '猎人'),
        ],
        activeRoleCodes: ['werewolf', 'seer'],
      },
    })

    expect(wrapper.text()).toContain('一局怎么玩')
    expect(wrapper.text()).toContain('夜间行动顺序')
    expect(wrapper.text()).toContain('角色技能')
    expect(wrapper.text()).toContain('胜负判定')
    expect(wrapper.text()).toContain('开局身份决定夜间技能')
    expect(wrapper.findAll('.one-night-role-guide article')).toHaveLength(4)
    expect(wrapper.findAll('.one-night-role-guide article.active')).toHaveLength(2)
  })

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
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(OneNightWerewolfTable, {
      props: { snapshot: snapshot('discussion') },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('自由讨论，不限时间')
    expect(wrapper.text()).not.toContain('剩余讨论时间')
    expect(wrapper.text()).not.toContain('乙的牌是狼人')
    await wrapper.get('.press-reveal-card').trigger('pointerdown')
    expect(wrapper.text()).toContain('乙的牌是狼人')
    await wrapper.get('.wide-button').trigger('click')
    expect(action).toHaveBeenCalledWith('start_vote')
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
