# Avalon role skins

Each skin directory follows the same contract:

```text
<skin-id>/
├── preview.webp              # 1024 × 768, 4 × 2 role overview
└── roles/                    # 1024 × 1536 portraits
    ├── assassin.webp
    ├── loyal-servant.webp
    ├── merlin.webp
    ├── minion.webp
    ├── mordred.webp
    ├── morgana.webp
    ├── oberon.webp
    └── percival.webp
```

Preview order is Merlin, Percival, Loyal Servant, Assassin, Morgana,
Mordred, Oberon, and Minion. Runtime IDs, names, tiers, previews, and role
artwork are registered in `frontend/src/games/avalon/roleSkins.ts`.

## Generated skin prompts

The two skins below were created with the built-in image generation tool.
All portraits use a vertical 2:3 composition, one centered waist-up character,
safe margins, and a darker lower third for the in-game text overlay. They must
not contain written text, letters, numbers, logos, watermarks, card frames, or
modern clothing.

### `classic-tabletop`

Use case: stylized game character concept. Create a foundational Avalon skin
using clean flat digital illustration, classic modern board-game art, limited
shapes, modest detail, crisp silhouettes, soft even lighting, and a subtly
textured backdrop. Keep it intentionally simpler than premium fantasy art.
Use clear good-faction blues/greens and evil-faction charcoal, crimson, violet,
and rust colors.

### `grail-myth`

Use case: stylized game character concept. Create an ultimate-tier Avalon skin
using ultra-refined luminous cinematic fantasy illustration, AAA collectible
card quality, painterly realism, dramatic volumetric light, mythical Avalon
lake ruins, engraved mithril, pearl inlay, gold or silver filigree, layered
silk and velvet, jewel accents, realistic hair and skin, and magical particles.
Good roles use radiant sacred-lake light; evil roles use distinct ruby,
amethyst, storm, eclipse, and amber-dusk treatments while remaining readable.
Avoid parchment, manuscript, stained-glass, and flat-vector treatments so the
skin stays visually separate from the other sets.

Role subjects remain consistent across both prompt sets: Merlin with a crystal
orb, Percival with a ceremonial sword, Loyal Servant with hand to heart and a
round shield, Assassin with a dagger, Morgana with an obsidian mirror, Mordred
in broken-crown black armor, Oberon with a feathered cloak and eclipse token,
and Minion with a goblet and travel-worn equipment.
