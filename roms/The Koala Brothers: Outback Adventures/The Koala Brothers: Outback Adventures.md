# The Koala Brothers: Outback Adventures (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Koala Brothers: Outback Adventures.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| Header title | `KOALA_BROS` |
| Game code / maker | `BAKE` / `GY` (`file(1)`: "BAKEGY, Rev.00") |
| Version | 0x00 |
| Entry branch | `0xEA00002E` → 0x080000C0 (stock; no cracktro patch at 0x0) |
| Complement / checksum bytes | `0xA1` / `0x0000` (non-standard header arithmetic — see §8) |
| MD5 | `56ae7f3683083a70fd36eb509e68845f` |
| SHA-1 | `3304d1188f269a105808146ac05df6ff3a597781` |
| SHA-256 | `529b3ce8ad6e4301932a7733be5a4dca230f8897328ac325b6114c80d8afa205` |

Developer/publisher strings visible on the boot splash: Spellbound Entertainment Ltd. & Famous Flying Films Ltd. 2005; licensed by The Game Factory; GBA build by "J" / Sirius Games (splash logos).

## 2. Executive summary

**There is no developer-intended cheat, password, button-code or hidden debug system in this ROM.** The game is a children's 10-minigame compilation with a purely navigational UI (D-pad L/R carousel + A/Start to confirm, B to back out). Every reachable screen was walked in mGBA with savestate/RAM snapshots: language select, boot splash/legal, title (2 pages: *Start game*, *Credits*), full scrolling credits, "Choose a game" (10 entries, all unlocked), per-game "How to play" screens, 10 gameplay/cutscene screens, and the in-game pause (*Quit?*) dialog. No password entry widget, options menu, level-select screen, unlockable character, or hidden menu appears anywhere, and no input sequence opens one.

Static evidence agrees. The complete ASCII text/resource banks were decoded (guide §11 warning: do not conclude "no text" from a failed uppercase `strings` grep — here all UI text is plain lowercase ASCII and was fully dumped). Across 105,070 extracted ASCII strings there are **zero** occurrences of `password`, `cheat`, `secret`, `debug`, `unlock`, `warp`, `level select`, `gameshark`, `codebreaker`, or `action replay`; the only `hidden`/`found` strings are resource names for collectible sprites in the *Hide 'n Seek* minigame. Zero hits for any of 7 standard password alphabets. Zero button-mask code tables in the code region (1604 raw "mask-like" u16 runs were verified as compressed graphics/palette data; the only 2 multi-distinct runs in code are Thumb literal-pool constants, not key sequences).

Web reconnaissance (guide §3.4) was **inconclusive/blocked**: search integration returned no results for six queries, 3rd party cheat indexes returned HTTP 403 and DuckDuckGo a CAPTCHA. No published codes could be fetched or verified. This does not weaken the static negative: no candidate code literal exists in the image to attach such a code to.

Conclusion type (guide §16.3): **category 1 — no system**, not dead code, not a cut feature, not a gated feature. Detail and counts are in §6b.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`) under Xvfb `:318` + openbox, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
- Keymap (mGBA SDL defaults): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Keys held ~100–150 ms.
- Language select: 8 flags; press A on the UK flag (top-left).
- Title: D-pad **Right** cycles `Start game` → `Credits` → `Start game` (exactly 2 pages; wraps). L/R shoulder buttons, Up, Down and Select do nothing on this screen. A or Start on `Start game` enters "Choose a game"; A on `Credits` plays the scrolling credits.
- Choose a game: D-pad L/R cycles 10 games (wraps); A starts the tutorial/game; B returns to title; in-game Start opens a *Quit?* dialog, A returns to "Choose a game".
- Any password/cheat test: no entry field exists; button-sequence tests were run after loading the saved title state with `F1` (slot 1) for a clean start.
- Savestates: `Shift+F1`…`Shift+F10` write `.ss1`…`.ss10` next to the ROM; `F1`…`F10` load them. States were decoded with the helper in §9.

## 4. Address map

Addresses are GBA (ROM file offset = address − 0x08000000).

| Address | What |
|---|---|
| `0x08000000`–`0x080000BF` | Header; entry branch `0xEA00002E` (ARM) → `0x080000C0` |
| `0x080003A0`–`0x08000420` | Resource-pointer/literal table (e.g. `0x085D7F8C`, `0x085D7FBC`, `0x03005454`) |
| `0x080006F8`–`0x080007F8` | Title/menu resource configuration table (`0x085D8098` = "hiscore", `0x085D80A0` = "start game", `0x085D7FCC` = "choose_a_game", `0x085D80B4` = "icon rotator") |
| `0x0800C30C` | Key-state **init**: reads `KEYINPUT`, stores `~KEYINPUT & 0x3FF` at struct offset `0x14`, clears two 10-byte arrays at offsets `0x0` and `0xA` |
| `0x0800C330` / `0x0800C334` | ARM/Thumb literal pool words `0x04000130` (KEYINPUT) and `0x000003FF` |
| `0x0800C348` | Key-state **update**: recomputes newly-pressed/held bits, writes one byte per key (9 keys, bit `1<<i`) into the two 10-byte arrays |
| `0x0800C39C` / `0x0800C3A0` | Second literal pair `0x04000130`, `0x000003FF` |
| `0x0800CC80`–`0x0800CE68` | Input/timer service loop; callers of the two key routines at `0x0800CCB6`, `0x0800CD68`, `0x0800CEB8` |
| `0x081E1EE2`–`0x081E6040` | UI text/resource bank (8 languages). `0x081E1F0C` "start game", `0x081E1F9A`/`0x081E1FA6` "hiscore", `0x081E245E` "airmail" … `0x081E28F4` "choose_a_game", `0x081E5A0A` "select level" (unreferenced — see §8) |
| `0x08398672` / `0x08398762` | "hidden1"…"hidden6" / "found1"…"found6" sprite-resource names (*Hide 'n Seek* collectibles, not codes) |
| `0x085D7F8C`–`0x085D8xxx` | Engine resource-name dictionary: `gametitle_*`, `menu_*`, `choose_a_game`, `hiscore`, `start game`, `Abutton`, `Lbutton`, `Rbutton`, `selector`, `%02d`, all minigame sprites |
| RAM `0x03001130`–`0x030011A0` | Transient glyph/sprite-letter cache (sliding windows of ASCII letters); changes with screen, not a text-entry buffer |
| RAM `0x0300124C` | Transient UTF-16 glyph cache (e.g. `C u y` → `N l v`) |
| RAM `0x03001858` | Scene/animation index (title = 5, credits/cutscenes = 0, choose-game = 0xA/0xB, gameplay = 0/7/0x11/0x12). Not a persistent save flag |
| RAM `0x0300566C` | Boot/init flag: 1 on title, 0 after entering a game |

## 5. Algorithm

There is **no validator to reverse**. The only algorithmic structure found is the joypad sampler, which is a plain per-key state machine, not a code matcher:

```
init(r0 = key_state):
    r2 = ~(*(u16*)0x04000130) & 0x3FF     ; active-high 10-key mask
    key_state[0x14] = r2                  ; held mask
    clear key_state[0x00][0..9]           ; per-key "press" bytes
    clear key_state[0x0A][0..9]           ; per-key "release"/edge bytes

update(r0 = key_state):
    raw  = ~(*(u16*)0x04000130) & 0x3FF
    prev = key_state[0x14]
    key_state[0x14] = raw
    for i in 0..8:                        ; 9 iterations, bit 1<<i
        press[i]   = (raw  & (1<<i)) ? 1 : 0
        ...derived edge bytes...
```

No history ring buffer, no length counter, no comparison against a constant mask array, no checksum, no alphabet lookup, and no flag write keyed on a multi-press sequence exists in this path (guide §5.4a). The 10-key arrays are consumed only for menu cursor movement and gameplay controls.

## 6. Tables

**All reachable screens (walked):**

| # | Screen | RAM evidence (raw state SHA-256 prefix / scene word at 0x03001858) |
|---|---|---|
| 1 | Boot splash / legal | observed visually; no state saved (pre-title) |
| 2 | Language select (8 flags) | `fd3ed815…` (slot 1 first write) |
| 3 | Title — "Start game" page | `c05f9e75…` / `0x5` |
| 4 | Title — "Credits" page | `fd3ed815…` / `0x5` |
| 5 | Scrolling credits (7 steps + closing animation) | `5244b434…` / `0x0` |
| 6 | "Choose a game" carousel (10 entries) | `5c9c72d5…` / `0xA`, `aae1cd2f…` / `0xB` |
| 7 | Per-game "How to play" (seen for games 1,2,4,5,6,7,8) | `g*_howto.png` screenshots |
| 8 | Gameplay / intro cutscenes for all 10 games | `f90b600c…`, `318b6697…`, `8aaad9bb…`, `561a8748…`, `398c8590…`, `e66d1342…`, `c78dd059…`, `e9f273d5…`, `bc35ce01…`, `c20a98a2…` |
| 9 | Pause dialog (*Quit?*) | observed on all 10 games |

**10 minigames (resource names at 0x081E245E+, UK bank):** `airmail`, `a_helping_hand`, `josie_to_the_rescue`, `archies_outback_tennis`, `postman_alice`, `icecream` (shown as "Cold Ice Cream"), `help_from_above`, `fishing` ("The Koala Brothers go fishing"), `shopping_at_sammys`, `hide_n_seek` ("Hide 'n seek"). All ten are selectable from a fresh boot — none gated.

**Language bank:** UK, FR, NL, DK, DE, IT, PT, ES — each with its own `menu_*`, `gametitle_*` and the same 10 game names. No extra menu item in any language.

## 6b. Enumeration

This engagement is a **bounded negative** (guide §0.2, final bullet). The "code space" is empty: there is no alphabet, no input widget, no lookup table and no validator to enumerate. Bounds are established by counts over explicitly defined search spaces:

1. **String space.** `strings -t x -n 4` over all 8 MiB → **105,070** strings. Case-insensitive keyword counts over that set: `password` **0**, `cheat` **0**, `secret` **0**, `debug` **0**, `unlock` **0**, `warp` **0**, `level select` **0**, `gameshark` **0**, `codebreaker` **0**, `action replay` **0**. A byte-level `grep -abo` for each term independently confirms 0 (§11: converted decimal offsets; no hits either way). The complete UI/resource text banks `0x081E1EE2`–`0x081E6040` and `0x085D7F8C`–`0x085D8xxx` were dumped by regex over `[ -~]{3,}` and read in full: they contain only menu labels, button glyph names, 8×10 game names and sprite filenames. This satisfies the guide's "decode font/tile text banks before a negative" requirement — the text is ASCII and was decoded, not assumed absent.
2. **Alphabet space.** 7 conventional password alphabets (`A-Z`, `a-z`, `0-9A-Z`, `ABCDEFGHJKLMNPQRSTUVWXYZ`, `BCDFGHJKLMNPQRSTVWXYZ`, `23456789…`, Car-Battler-Joe-style `1234KLMN…`) searched as raw byte sequences: **7 searched, 0 hits**. The only alphabet-like byte run in the ROM is the generic font glyph order `0x081E1624` (` !"#$%&'()*+,-./0123…`), which is a font, not a code alphabet.
3. **Button-mask / table space.** A raw u16 scan of the first 1.5 MiB found **1,604** runs of ≥5 mask-like values; inspection shows all are repeated `0x0202`/`0x0101` graphic/palette words. Constraining to runs of ≥5 with ≥4 *distinct* masks in that region yields **2** runs (`0x0800CBCE`, `0x080100E4`); both are Thumb instruction/literal-pool artifacts (e.g. fixed-point constants `0x00010000`, `0x00020000`, `0x00040000`), not button sequences. A u8 key-index scan (1–10) found 5,687 runs, all compressed graphics/audio bytes. The only `KEYINPUT` references in the whole image are the two literal pairs at `0x0800C330` and `0x0800C39C`, both consumed by the plain 10-key sampler in §5 — there is no second consumer that could implement a cheat matcher.
4. **Screen space.** Menu walk is closed: title has exactly 2 pages (L/R wraps 2→1), choose-a-game has exactly 10 entries (L/R wraps, all selectable, none locked), pause has 1 entry (*Quit?*), credits is linear, and no screen offers a text field, code pad, options list, level list or debug entry. Each of the 10 games was entered; their only extra screens are "How to play" tutorials and normal gameplay/cutscenes. No 11th game, bonus screen, gallery or hidden character exists.
5. **Input space (dynamic rejection tests).** From a clean title state (`F1` slot 1), these were pressed and the resulting state saved: `L`, `R`, `Up`, `Down`, `Select`, `A+B` (simultaneous), `B×10`, `Up×10`, Konami prefix `Up Up Down Down Left Right Left Right B`, full Konami `…B A`, `Select+Start`, `L+R+A` (simultaneous). Results: all sequences **without** A/Start left the title on screen word `0x5` with flags `0x03001410 = 0`, `0x0300141C = 0`, `0x0300566C = 1` — identical to the untouched title (the `B×10` and `Up×10` states even hash identically, `49c4d8b2…`, confirming no state change beyond animation timing). Sequences containing A/Start merely advanced to "Choose a game" (`0xA`), the normal documented action. **No undocumented input produced a new screen or flag.**
6. **Novel code.** Not minted: there is no validator to satisfy, and inventing a string would have nothing to be entered into. Per §0.2 this is reported as a proven empty space, not an untested one.

Because the accepted-code set is empty (not merely "unknown"), there is no rejection-bounds experiment to run: bounds are proven by the searches above plus the observed no-op rejection of every non-standard input in (5).

## 7. Validation evidence

- **Observed**: all screens and transitions listed in §6; keymap; 10-game carousel; all dynamic input tests; savestate dumps and hashes; identical hashes for the two no-op input probes.
- **Derived**: input sampler semantics from Thumb disassembly at `0x0800C30C`/`0x0800C348` and their literal pools; resource/text-bank contents from raw byte dumps; absence of code tables from bounded scans.
- **Inferred**: the `hidden1..6`/`found1..6` resource names are collectible-item sprites for *Hide 'n Seek* (their placement alongside `level1..6` and character names in the asset bank strongly suggests this, but the minigame's rules were not fully played through).
- **Unverified**: published codes — none could be retrieved (web 403/CAPTCHA), so none were tested; this does not affect the in-ROM negative.

## 8. Unknowns

- `0x081E5A0A` "select level" exists as a generic engine resource name but **no pointer to it exists in the ROM** (`scan.py ptr 0x081E5A0A` → 0 hits), and no level-select screen was reachable. Most likely a leftover from the engine's shared resource dictionary; treated as unreferenced data, not a hidden feature.
- Header complement byte `0xA1` (standard calculation gives `0xBA`) and checksum `0x0000`: a non-standard/rebuilt header, common in scene releases (§16.1). The entry branch is stock, the game boots normally and no trainer menu was observed, so this was not pursued as a cracktro.
- Web reconnaissance was blocked; a future analyst with working web access could confirm that no cheats were ever published for this SKU. The ROM-internal negative stands independently.

## 9. Tooling

All analysis scripts and captures were in `/tmp/koalabrothers/`:

| File | Purpose |
|---|---|
| `scan.py` | Literal-pointer and ASCII-string scanner with file-offset → ROM-address conversion |
| `ss.py` | Extracts the zlib `gbAs` chunk from mGBA `.ss1` PNG savestates (per §16.13: raw layout IWRAM `0x19000`, EWRAM `0x21000`) |
| `save_state.sh`, `probe.sh`, `press.sh` | Savestate capture, RAM-word probe of `0x03001858`/flags, XTEST key holds |
| `probe_inputs.sh`, `seqtest.sh` | Clean-state reload + input-sequence testing |
| `walk_games.sh` | Automated walk of all 10 minigames (tutorial, gameplay, pause, quit) |
| `maskscan.py` | u16/u8 button-mask and key-index array scanner |
| `*_montage.png`, `seq_*.png`, `g*_*.png` | Screenshots (kept in `/tmp` only; no game assets redistributed) |

Environment: Xvfb `:318`, openbox, `SDL_AUDIODRIVER=dummy`, mGBA 0.10.5, `gdb-multiarch`, `arm-none-eabi-objdump`, Python 3. GDB stub on the default port 2345 was unusable because another concurrent session's mGBA held it; savestate diffing was used for all RAM evidence instead.

## 10. Legal note

Only addresses, hashes, algorithms and observations are published here. No ROM image, extracted graphics, audio, or game text assets are redistributed.
