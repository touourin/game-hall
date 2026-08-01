import darkAssassin from '../../assets/avalon/roles/assassin.webp'
import darkLoyalServant from '../../assets/avalon/roles/loyal-servant.webp'
import darkMerlin from '../../assets/avalon/roles/merlin.webp'
import darkMinion from '../../assets/avalon/roles/minion.webp'
import darkMordred from '../../assets/avalon/roles/mordred.webp'
import darkMorgana from '../../assets/avalon/roles/morgana.webp'
import darkOberon from '../../assets/avalon/roles/oberon.webp'
import darkPercival from '../../assets/avalon/roles/percival.webp'
import codexAssassin from '../../assets/avalon/roles/royal-codex/assassin.webp'
import codexLoyalServant from '../../assets/avalon/roles/royal-codex/loyal-servant.webp'
import codexMerlin from '../../assets/avalon/roles/royal-codex/merlin.webp'
import codexMinion from '../../assets/avalon/roles/royal-codex/minion.webp'
import codexMordred from '../../assets/avalon/roles/royal-codex/mordred.webp'
import codexMorgana from '../../assets/avalon/roles/royal-codex/morgana.webp'
import codexOberon from '../../assets/avalon/roles/royal-codex/oberon.webp'
import codexPercival from '../../assets/avalon/roles/royal-codex/percival.webp'
import stainedAssassin from '../../assets/avalon/roles/stained-glass/assassin.webp'
import stainedLoyalServant from '../../assets/avalon/roles/stained-glass/loyal-servant.webp'
import stainedMerlin from '../../assets/avalon/roles/stained-glass/merlin.webp'
import stainedMinion from '../../assets/avalon/roles/stained-glass/minion.webp'
import stainedMordred from '../../assets/avalon/roles/stained-glass/mordred.webp'
import stainedMorgana from '../../assets/avalon/roles/stained-glass/morgana.webp'
import stainedOberon from '../../assets/avalon/roles/stained-glass/oberon.webp'
import stainedPercival from '../../assets/avalon/roles/stained-glass/percival.webp'

export type RoleSkinId = 'dark-chronicle' | 'stained-glass' | 'royal-codex'

export const ROLE_SKIN_STORAGE_KEY = 'avalon:role-skin'
const ROLE_SKIN_LOCK_STORAGE_PREFIX = 'avalon:role-skin-lock:'

export const ROLE_SKINS: Array<{
  id: RoleSkinId
  name: string
  description: string
}> = [
  {
    id: 'dark-chronicle',
    name: '暗夜史诗',
    description: '写实绘卷与暗金质感',
  },
  {
    id: 'stained-glass',
    name: '圣堂彩窗',
    description: '宝石色玻璃与鎏金轮廓',
  },
  {
    id: 'royal-codex',
    name: '王庭秘卷',
    description: '羊皮纸手绘与鎏金纹饰',
  },
]

const ROLE_ART: Record<RoleSkinId, Record<string, string>> = {
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
}

function isRoleSkinId(value: string | null): value is RoleSkinId {
  return ROLE_SKINS.some((skin) => skin.id === value)
}

function roleSkinLockKey(roomCode: string): string {
  return `${ROLE_SKIN_LOCK_STORAGE_PREFIX}${roomCode.trim().toUpperCase()}`
}

export function storedRoleSkin(): RoleSkinId {
  const saved = localStorage.getItem(ROLE_SKIN_STORAGE_KEY)
  return isRoleSkinId(saved) ? saved : 'dark-chronicle'
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

export function roleArtwork(
  roleCode: string,
  skin: RoleSkinId,
): string | null {
  return ROLE_ART[skin][roleCode] ?? null
}
