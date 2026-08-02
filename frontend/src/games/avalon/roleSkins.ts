import classicPreview from '../../assets/avalon/role-skins/classic-tabletop/preview.webp'
import classicAssassin from '../../assets/avalon/role-skins/classic-tabletop/roles/assassin.webp'
import classicLoyalServant from '../../assets/avalon/role-skins/classic-tabletop/roles/loyal-servant.webp'
import classicMerlin from '../../assets/avalon/role-skins/classic-tabletop/roles/merlin.webp'
import classicMinion from '../../assets/avalon/role-skins/classic-tabletop/roles/minion.webp'
import classicMordred from '../../assets/avalon/role-skins/classic-tabletop/roles/mordred.webp'
import classicMorgana from '../../assets/avalon/role-skins/classic-tabletop/roles/morgana.webp'
import classicOberon from '../../assets/avalon/role-skins/classic-tabletop/roles/oberon.webp'
import classicPercival from '../../assets/avalon/role-skins/classic-tabletop/roles/percival.webp'
import darkPreview from '../../assets/avalon/role-skins/dark-chronicle/preview.webp'
import darkAssassin from '../../assets/avalon/role-skins/dark-chronicle/roles/assassin.webp'
import darkLoyalServant from '../../assets/avalon/role-skins/dark-chronicle/roles/loyal-servant.webp'
import darkMerlin from '../../assets/avalon/role-skins/dark-chronicle/roles/merlin.webp'
import darkMinion from '../../assets/avalon/role-skins/dark-chronicle/roles/minion.webp'
import darkMordred from '../../assets/avalon/role-skins/dark-chronicle/roles/mordred.webp'
import darkMorgana from '../../assets/avalon/role-skins/dark-chronicle/roles/morgana.webp'
import darkOberon from '../../assets/avalon/role-skins/dark-chronicle/roles/oberon.webp'
import darkPercival from '../../assets/avalon/role-skins/dark-chronicle/roles/percival.webp'
import grailPreview from '../../assets/avalon/role-skins/grail-myth/preview.webp'
import grailAssassin from '../../assets/avalon/role-skins/grail-myth/roles/assassin.webp'
import grailLoyalServant from '../../assets/avalon/role-skins/grail-myth/roles/loyal-servant.webp'
import grailMerlin from '../../assets/avalon/role-skins/grail-myth/roles/merlin.webp'
import grailMinion from '../../assets/avalon/role-skins/grail-myth/roles/minion.webp'
import grailMordred from '../../assets/avalon/role-skins/grail-myth/roles/mordred.webp'
import grailMorgana from '../../assets/avalon/role-skins/grail-myth/roles/morgana.webp'
import grailOberon from '../../assets/avalon/role-skins/grail-myth/roles/oberon.webp'
import grailPercival from '../../assets/avalon/role-skins/grail-myth/roles/percival.webp'
import codexPreview from '../../assets/avalon/role-skins/royal-codex/preview.webp'
import codexAssassin from '../../assets/avalon/role-skins/royal-codex/roles/assassin.webp'
import codexLoyalServant from '../../assets/avalon/role-skins/royal-codex/roles/loyal-servant.webp'
import codexMerlin from '../../assets/avalon/role-skins/royal-codex/roles/merlin.webp'
import codexMinion from '../../assets/avalon/role-skins/royal-codex/roles/minion.webp'
import codexMordred from '../../assets/avalon/role-skins/royal-codex/roles/mordred.webp'
import codexMorgana from '../../assets/avalon/role-skins/royal-codex/roles/morgana.webp'
import codexOberon from '../../assets/avalon/role-skins/royal-codex/roles/oberon.webp'
import codexPercival from '../../assets/avalon/role-skins/royal-codex/roles/percival.webp'
import stainedPreview from '../../assets/avalon/role-skins/stained-glass/preview.webp'
import stainedAssassin from '../../assets/avalon/role-skins/stained-glass/roles/assassin.webp'
import stainedLoyalServant from '../../assets/avalon/role-skins/stained-glass/roles/loyal-servant.webp'
import stainedMerlin from '../../assets/avalon/role-skins/stained-glass/roles/merlin.webp'
import stainedMinion from '../../assets/avalon/role-skins/stained-glass/roles/minion.webp'
import stainedMordred from '../../assets/avalon/role-skins/stained-glass/roles/mordred.webp'
import stainedMorgana from '../../assets/avalon/role-skins/stained-glass/roles/morgana.webp'
import stainedOberon from '../../assets/avalon/role-skins/stained-glass/roles/oberon.webp'
import stainedPercival from '../../assets/avalon/role-skins/stained-glass/roles/percival.webp'

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
  | 'assassin'
  | 'morgana'
  | 'mordred'
  | 'oberon'
  | 'minion'

export type AvalonRoleAlignment = 'good' | 'evil'

export interface RoleSkinPreviewRole {
  code: AvalonRoleCode
  name: string
  alignment: AvalonRoleAlignment
  artwork: string
  framing: RoleArtworkFraming
}

export interface RoleArtworkFraming {
  scale: number
  originXPercent: number
  originYPercent: number
}

export const ROLE_SKIN_STORAGE_KEY = 'avalon:role-skin'
const ROLE_SKIN_LOCK_STORAGE_PREFIX = 'avalon:role-skin-lock:'

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

const ROLE_ART: Record<RoleSkinId, Record<AvalonRoleCode, string>> = {
  'classic-tabletop': {
    merlin: classicMerlin,
    percival: classicPercival,
    loyal_servant: classicLoyalServant,
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
  'grail-myth': {
    morgana: { scale: 1.1, originXPercent: 50, originYPercent: 29 },
    mordred: { scale: 1.1, originXPercent: 50, originYPercent: 27 },
    oberon: { scale: 1.08, originXPercent: 50, originYPercent: 28 },
    minion: { scale: 1.1, originXPercent: 50, originYPercent: 27 },
  },
}

const ROLE_PREVIEW_DEFINITIONS: Array<
  Omit<RoleSkinPreviewRole, 'artwork' | 'framing'>
> = [
  { code: 'merlin', name: '梅林', alignment: 'good' },
  { code: 'percival', name: '派西维尔', alignment: 'good' },
  { code: 'loyal_servant', name: '亚瑟的忠臣', alignment: 'good' },
  { code: 'assassin', name: '刺客', alignment: 'evil' },
  { code: 'morgana', name: '莫甘娜', alignment: 'evil' },
  { code: 'mordred', name: '莫德雷德', alignment: 'evil' },
  { code: 'oberon', name: '奥伯伦', alignment: 'evil' },
  { code: 'minion', name: '莫德雷德的爪牙', alignment: 'evil' },
]

function isRoleSkinId(value: string | null): value is RoleSkinId {
  return ROLE_SKINS.some((skin) => skin.id === value)
}

function roleSkinLockKey(roomCode: string): string {
  return `${ROLE_SKIN_LOCK_STORAGE_PREFIX}${roomCode.trim().toUpperCase()}`
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

export function roleSkinPreviewRoles(
  skin: RoleSkinId,
): RoleSkinPreviewRole[] {
  return ROLE_PREVIEW_DEFINITIONS.map((role) => ({
    ...role,
    artwork: ROLE_ART[skin][role.code],
    framing: roleArtworkFraming(role.code, skin),
  }))
}

export function roleArtworkFraming(
  roleCode: string,
  skin: RoleSkinId,
): RoleArtworkFraming {
  if (!Object.prototype.hasOwnProperty.call(ROLE_ART[skin], roleCode)) {
    return DEFAULT_ROLE_ARTWORK_FRAMING
  }
  return ROLE_ARTWORK_FRAMING[skin]?.[roleCode as AvalonRoleCode]
    ?? DEFAULT_ROLE_ARTWORK_FRAMING
}

export function roleArtwork(
  roleCode: string,
  skin: RoleSkinId,
): string | null {
  if (!Object.prototype.hasOwnProperty.call(ROLE_ART[skin], roleCode)) {
    return null
  }
  return ROLE_ART[skin][roleCode as AvalonRoleCode]
}
