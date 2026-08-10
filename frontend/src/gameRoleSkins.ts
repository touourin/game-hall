import classicPreview from './assets/avalon/role-skins/classic-tabletop/preview.webp'
import classicAssassin from './assets/avalon/role-skins/classic-tabletop/roles/assassin.webp'
import classicDissentingCourtier from './assets/avalon/role-skins/classic-tabletop/roles/dissenting-courtier.webp'
import classicLoyalServant from './assets/avalon/role-skins/classic-tabletop/roles/loyal-servant.webp'
import classicMerlin from './assets/avalon/role-skins/classic-tabletop/roles/merlin.webp'
import classicMinion from './assets/avalon/role-skins/classic-tabletop/roles/minion.webp'
import classicMordred from './assets/avalon/role-skins/classic-tabletop/roles/mordred.webp'
import classicMorgana from './assets/avalon/role-skins/classic-tabletop/roles/morgana.webp'
import classicOberon from './assets/avalon/role-skins/classic-tabletop/roles/oberon.webp'
import classicPercival from './assets/avalon/role-skins/classic-tabletop/roles/percival.webp'
import classicShadowMerlin from './assets/avalon/role-skins/classic-tabletop/roles/shadow-merlin.webp'
import darkPreview from './assets/avalon/role-skins/dark-chronicle/preview.webp'
import darkAssassin from './assets/avalon/role-skins/dark-chronicle/roles/assassin.webp'
import darkDissentingCourtier from './assets/avalon/role-skins/dark-chronicle/roles/dissenting-courtier.webp'
import darkLoyalServant from './assets/avalon/role-skins/dark-chronicle/roles/loyal-servant.webp'
import darkMerlin from './assets/avalon/role-skins/dark-chronicle/roles/merlin.webp'
import darkMinion from './assets/avalon/role-skins/dark-chronicle/roles/minion.webp'
import darkMordred from './assets/avalon/role-skins/dark-chronicle/roles/mordred.webp'
import darkMorgana from './assets/avalon/role-skins/dark-chronicle/roles/morgana.webp'
import darkOberon from './assets/avalon/role-skins/dark-chronicle/roles/oberon.webp'
import darkPercival from './assets/avalon/role-skins/dark-chronicle/roles/percival.webp'
import darkShadowMerlin from './assets/avalon/role-skins/dark-chronicle/roles/shadow-merlin.webp'
import grailPreview from './assets/avalon/role-skins/grail-myth/preview.webp'
import grailAssassin from './assets/avalon/role-skins/grail-myth/roles/assassin.webp'
import grailDissentingCourtier from './assets/avalon/role-skins/grail-myth/roles/dissenting-courtier.webp'
import grailLoyalServant from './assets/avalon/role-skins/grail-myth/roles/loyal-servant.webp'
import grailMerlin from './assets/avalon/role-skins/grail-myth/roles/merlin.webp'
import grailMinion from './assets/avalon/role-skins/grail-myth/roles/minion.webp'
import grailMordred from './assets/avalon/role-skins/grail-myth/roles/mordred.webp'
import grailMorgana from './assets/avalon/role-skins/grail-myth/roles/morgana.webp'
import grailOberon from './assets/avalon/role-skins/grail-myth/roles/oberon.webp'
import grailPercival from './assets/avalon/role-skins/grail-myth/roles/percival.webp'
import grailShadowMerlin from './assets/avalon/role-skins/grail-myth/roles/shadow-merlin.webp'
import codexPreview from './assets/avalon/role-skins/royal-codex/preview.webp'
import codexAssassin from './assets/avalon/role-skins/royal-codex/roles/assassin.webp'
import codexDissentingCourtier from './assets/avalon/role-skins/royal-codex/roles/dissenting-courtier.webp'
import codexLoyalServant from './assets/avalon/role-skins/royal-codex/roles/loyal-servant.webp'
import codexMerlin from './assets/avalon/role-skins/royal-codex/roles/merlin.webp'
import codexMinion from './assets/avalon/role-skins/royal-codex/roles/minion.webp'
import codexMordred from './assets/avalon/role-skins/royal-codex/roles/mordred.webp'
import codexMorgana from './assets/avalon/role-skins/royal-codex/roles/morgana.webp'
import codexOberon from './assets/avalon/role-skins/royal-codex/roles/oberon.webp'
import codexPercival from './assets/avalon/role-skins/royal-codex/roles/percival.webp'
import codexShadowMerlin from './assets/avalon/role-skins/royal-codex/roles/shadow-merlin.webp'
import stainedPreview from './assets/avalon/role-skins/stained-glass/preview.webp'
import stainedAssassin from './assets/avalon/role-skins/stained-glass/roles/assassin.webp'
import stainedDissentingCourtier from './assets/avalon/role-skins/stained-glass/roles/dissenting-courtier.webp'
import stainedLoyalServant from './assets/avalon/role-skins/stained-glass/roles/loyal-servant.webp'
import stainedMerlin from './assets/avalon/role-skins/stained-glass/roles/merlin.webp'
import stainedMinion from './assets/avalon/role-skins/stained-glass/roles/minion.webp'
import stainedMordred from './assets/avalon/role-skins/stained-glass/roles/mordred.webp'
import stainedMorgana from './assets/avalon/role-skins/stained-glass/roles/morgana.webp'
import stainedOberon from './assets/avalon/role-skins/stained-glass/roles/oberon.webp'
import stainedPercival from './assets/avalon/role-skins/stained-glass/roles/percival.webp'
import stainedShadowMerlin from './assets/avalon/role-skins/stained-glass/roles/shadow-merlin.webp'

export type RoleSkinId =
  | 'classic-tabletop'
  | 'dark-chronicle'
  | 'stained-glass'
  | 'royal-codex'
  | 'grail-myth'

export type RoleSkinTier = '基础' | '升级' | '终极'

export type AvalonRoleCode =
  | 'merlin'
  | 'percival'
  | 'loyal_servant'
  | 'dissenting_courtier'
  | 'shadow_merlin'
  | 'assassin'
  | 'morgana'
  | 'mordred'
  | 'oberon'
  | 'minion'

export type RoleSkinRoleCode = AvalonRoleCode

export type AvalonRoleAlignment = 'good' | 'evil'

export interface RoleSkinRoleDefinition {
  code: RoleSkinRoleCode
  name: string
  alignment: AvalonRoleAlignment
}

export type RoleSkinLoadout = Record<RoleSkinRoleCode, RoleSkinId>

export interface RoleArtworkFraming {
  scale: number
  originXPercent: number
  originYPercent: number
  preserveFrame?: boolean
  treatment?: 'codex-ink-wash'
}

export const ROLE_SKIN_STORAGE_KEY = 'avalon:role-skin'
const ROLE_SKIN_LOCK_STORAGE_PREFIX = 'avalon:role-skin-lock:'
const ROLE_SKIN_LOADOUT_STORAGE_PREFIX = 'avalon:role-skin-loadout:'
const ROLE_SKIN_LOADOUT_LOCK_STORAGE_PREFIX = 'avalon:role-skin-loadout-lock:'

export const ROLE_SKINS: Array<{
  id: RoleSkinId
  name: string
  description: string
  tier: RoleSkinTier
  preview: string
}> = [
  {
    id: 'classic-tabletop',
    name: '经典桌游',
    description: '简洁平涂，身份辨识更直观',
    tier: '基础',
    preview: classicPreview,
  },
  {
    id: 'dark-chronicle',
    name: '暗夜史诗',
    description: '写实绘卷与暗金质感',
    tier: '升级',
    preview: darkPreview,
  },
  {
    id: 'stained-glass',
    name: '圣堂彩窗',
    description: '宝石色玻璃与鎏金轮廓',
    tier: '升级',
    preview: stainedPreview,
  },
  {
    id: 'royal-codex',
    name: '王庭秘卷',
    description: '羊皮纸手绘与鎏金纹饰',
    tier: '升级',
    preview: codexPreview,
  },
  {
    id: 'grail-myth',
    name: '圣杯神话',
    description: '圣湖辉光与神话级精致质感',
    tier: '终极',
    preview: grailPreview,
  },
]

const ROLE_ART: Record<RoleSkinId, Partial<Record<AvalonRoleCode, string>>> = {
  'classic-tabletop': {
    merlin: classicMerlin,
    percival: classicPercival,
    loyal_servant: classicLoyalServant,
    dissenting_courtier: classicDissentingCourtier,
    shadow_merlin: classicShadowMerlin,
    assassin: classicAssassin,
    morgana: classicMorgana,
    mordred: classicMordred,
    oberon: classicOberon,
    minion: classicMinion,
  },
  'dark-chronicle': {
    merlin: darkMerlin,
    percival: darkPercival,
    loyal_servant: darkLoyalServant,
    dissenting_courtier: darkDissentingCourtier,
    shadow_merlin: darkShadowMerlin,
    assassin: darkAssassin,
    morgana: darkMorgana,
    mordred: darkMordred,
    oberon: darkOberon,
    minion: darkMinion,
  },
  'stained-glass': {
    merlin: stainedMerlin,
    percival: stainedPercival,
    loyal_servant: stainedLoyalServant,
    dissenting_courtier: stainedDissentingCourtier,
    shadow_merlin: stainedShadowMerlin,
    assassin: stainedAssassin,
    morgana: stainedMorgana,
    mordred: stainedMordred,
    oberon: stainedOberon,
    minion: stainedMinion,
  },
  'royal-codex': {
    merlin: codexMerlin,
    percival: codexPercival,
    loyal_servant: codexLoyalServant,
    dissenting_courtier: codexDissentingCourtier,
    shadow_merlin: codexShadowMerlin,
    assassin: codexAssassin,
    morgana: codexMorgana,
    mordred: codexMordred,
    oberon: codexOberon,
    minion: codexMinion,
  },
  'grail-myth': {
    merlin: grailMerlin,
    percival: grailPercival,
    loyal_servant: grailLoyalServant,
    dissenting_courtier: grailDissentingCourtier,
    shadow_merlin: grailShadowMerlin,
    assassin: grailAssassin,
    morgana: grailMorgana,
    mordred: grailMordred,
    oberon: grailOberon,
    minion: grailMinion,
  },
}

const DEFAULT_ROLE_ARTWORK_FRAMING: RoleArtworkFraming = {
  scale: 1,
  originXPercent: 50,
  originYPercent: 50,
}

const ROLE_ARTWORK_FRAMING: Partial<
  Record<RoleSkinId, Partial<Record<AvalonRoleCode, RoleArtworkFraming>>>
> = {
  'stained-glass': {
    percival: {
      scale: 1.09,
      originXPercent: 50,
      originYPercent: 50,
      preserveFrame: true,
    },
  },
  'grail-myth': {
    assassin: { scale: 1.18, originXPercent: 50, originYPercent: 60 },
    morgana: { scale: 1.1, originXPercent: 50, originYPercent: 29 },
    mordred: { scale: 1.1, originXPercent: 50, originYPercent: 27 },
    oberon: { scale: 1.08, originXPercent: 50, originYPercent: 28 },
    minion: { scale: 1.1, originXPercent: 50, originYPercent: 27 },
  },
}

export const ROLE_SKIN_ROLES: RoleSkinRoleDefinition[] = [
  { code: 'merlin', name: '梅林', alignment: 'good' },
  { code: 'shadow_merlin', name: '暗影梅林', alignment: 'good' },
  { code: 'percival', name: '派西维尔', alignment: 'good' },
  { code: 'loyal_servant', name: '亚瑟的忠臣', alignment: 'good' },
  { code: 'dissenting_courtier', name: '心怀异念之臣', alignment: 'good' },
  { code: 'assassin', name: '刺客', alignment: 'evil' },
  { code: 'morgana', name: '莫甘娜', alignment: 'evil' },
  { code: 'mordred', name: '莫德雷德', alignment: 'evil' },
  { code: 'oberon', name: '奥伯伦', alignment: 'evil' },
  { code: 'minion', name: '莫德雷德的爪牙', alignment: 'evil' },
]

export function isRoleSkinId(value: string | null): value is RoleSkinId {
  return ROLE_SKINS.some((skin) => skin.id === value)
}

function roleSkinLockKey(roomCode: string): string {
  return `${ROLE_SKIN_LOCK_STORAGE_PREFIX}${roomCode.trim().toUpperCase()}`
}

function roleSkinLoadoutKey(accountId: string): string {
  return `${ROLE_SKIN_LOADOUT_STORAGE_PREFIX}${accountId.trim() || 'guest'}`
}

function roleSkinLoadoutLockKey(roomCode: string): string {
  return `${ROLE_SKIN_LOADOUT_LOCK_STORAGE_PREFIX}${roomCode.trim().toUpperCase()}`
}

function parsedRoleSkinLoadout(value: string | null): RoleSkinLoadout | null {
  if (!value) return null
  try {
    const parsed = JSON.parse(value) as Partial<Record<RoleSkinRoleCode, string>>
    if (!parsed || typeof parsed !== 'object') return null
    const loadout = {} as RoleSkinLoadout
    for (const role of ROLE_SKIN_ROLES) {
      const skin = role.code === 'shadow_merlin'
        ? parsed.shadow_merlin ?? parsed.merlin
        : role.code === 'dissenting_courtier'
          ? parsed.dissenting_courtier ?? parsed.loyal_servant
        : parsed[role.code]
      if (!skin || !isRoleSkinId(skin)) return null
      loadout[role.code] = skin
    }
    return loadout
  } catch {
    return null
  }
}

export function defaultRoleSkinLoadout(
  skin: RoleSkinId = 'classic-tabletop',
): RoleSkinLoadout {
  return Object.fromEntries(
    ROLE_SKIN_ROLES.map((role) => [role.code, skin]),
  ) as RoleSkinLoadout
}

export function roleSkinRoleCode(roleCode: string): RoleSkinRoleCode | null {
  return ROLE_SKIN_ROLES.some((role) => role.code === roleCode)
    ? roleCode as RoleSkinRoleCode
    : null
}

export function storedRoleSkinLoadout(accountId: string): RoleSkinLoadout {
  const key = roleSkinLoadoutKey(accountId)
  const saved = parsedRoleSkinLoadout(localStorage.getItem(key))
  if (saved) return saved
  const migrated = defaultRoleSkinLoadout(storedRoleSkin())
  localStorage.setItem(key, JSON.stringify(migrated))
  return migrated
}

export function rememberRoleSkinLoadout(
  accountId: string,
  loadout: RoleSkinLoadout,
): void {
  localStorage.setItem(roleSkinLoadoutKey(accountId), JSON.stringify(loadout))
}

export function storedRoleSkinLoadoutLock(
  roomCode: string,
): RoleSkinLoadout | null {
  const key = roleSkinLoadoutLockKey(roomCode)
  const saved = parsedRoleSkinLoadout(localStorage.getItem(key))
  if (saved) return saved
  const legacySkin = storedRoleSkinLock(roomCode)
  if (!legacySkin) return null
  const migrated = defaultRoleSkinLoadout(legacySkin)
  localStorage.setItem(key, JSON.stringify(migrated))
  return migrated
}

export function lockRoleSkinLoadout(
  roomCode: string,
  loadout: RoleSkinLoadout,
): RoleSkinLoadout {
  localStorage.setItem(roleSkinLoadoutLockKey(roomCode), JSON.stringify(loadout))
  return loadout
}

export function clearRoleSkinLoadoutLock(roomCode: string): void {
  localStorage.removeItem(roleSkinLoadoutLockKey(roomCode))
  clearRoleSkinLock(roomCode)
}

export function storedRoleSkin(): RoleSkinId {
  const saved = localStorage.getItem(ROLE_SKIN_STORAGE_KEY)
  return isRoleSkinId(saved) ? saved : 'classic-tabletop'
}

export function rememberRoleSkin(skin: RoleSkinId): void {
  localStorage.setItem(ROLE_SKIN_STORAGE_KEY, skin)
}

export function storedRoleSkinLock(roomCode: string): RoleSkinId | null {
  const saved = localStorage.getItem(roleSkinLockKey(roomCode))
  return isRoleSkinId(saved) ? saved : null
}

export function lockRoleSkin(
  roomCode: string,
  skin: RoleSkinId,
): RoleSkinId {
  localStorage.setItem(roleSkinLockKey(roomCode), skin)
  return skin
}

export function clearRoleSkinLock(roomCode: string): void {
  localStorage.removeItem(roleSkinLockKey(roomCode))
}

export function roleSkinName(skin: RoleSkinId): string {
  return ROLE_SKINS.find((choice) => choice.id === skin)?.name ?? '身份卡'
}

export function roleArtworkFraming(
  roleCode: string,
  skin: RoleSkinId,
): RoleArtworkFraming {
  if (!Object.prototype.hasOwnProperty.call(ROLE_ART[skin], roleCode)) {
    return DEFAULT_ROLE_ARTWORK_FRAMING
  }
  const framing = ROLE_ARTWORK_FRAMING[skin]?.[roleCode as AvalonRoleCode]
    ?? DEFAULT_ROLE_ARTWORK_FRAMING
  return skin === 'royal-codex'
    ? { ...framing, treatment: 'codex-ink-wash' }
    : framing
}

export function isRoleSkinAvailable(
  roleCode: string,
  skin: RoleSkinId,
): boolean {
  return Object.prototype.hasOwnProperty.call(ROLE_ART[skin], roleCode)
}

export function roleArtwork(
  roleCode: string,
  skin: RoleSkinId,
): string | null {
  if (!Object.prototype.hasOwnProperty.call(ROLE_ART[skin], roleCode)) {
    return null
  }
  return ROLE_ART[skin][roleCode as AvalonRoleCode] ?? null
}
