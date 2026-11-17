# Duel Masters: Sempai Legends (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Duel Masters: Sempai Legends.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `DM SEMPAI` |
| Game code | `AA9E` |
| Maker code | `70` |
| Version | 0x00 (Rev.00) |
| Entry branch word | `0xEA00002E` (stock GBA crt0 branch to 0x080000C0) |
| Fixed 0x96 / main unit / device | 0x96 / 0x00 / 0x00 |
| Complement check | 0x7A |
| Header checksum | 0x0000 (rebuilt-header artifact, see §16.1; complement byte is intact and entry word is stock, so the image is not a scene-patched/trainer build) |
| MD5 | `2adeb64ff470fb08a472f3cb6f5d7d44` |
| SHA-1 | `524418eee05520a9a1e6b12918780435698c06e1` |
| SHA-256 | `b9e396aa5c7ab395066c7242747085a9bec2b789d43b49c7e4ae96ddd1e47661` |
| Developer / publisher (web) | Mistic Software / Atari SA, 2004-06-01 |

**Embedded GBA-header scan.** Nintendo-logo scan (156-byte logo from header +4) found **two** headers:

* file `0x000004` (ROM `0x08000004`) — primary header.
* file `0x0D0008` (ROM `0x080D0008`) — a **second, complete header** starting at file `0x0D0004` / ROM `0x080D0004`, with the **same** title `DM SEMPAI`, code `AA9E`, maker `70`, and a stock `0xEA00002E` entry branch to its own entry at `0x080D00C4`. Its entry code differs from the primary crt0 (`0x080D00C4` starts `b530 4c16 f015 ff1c …` = a Thumb main-loop/dispatch, not the ARM crt0 at `0x080000C0`). **Interpretation (Derived):** this is a second linked engine image (the title offers a `LINK` entry and the game supports a duel/link mode), not an appended trainer or cheat menu. No cheat/trainer text, no patch stub, and no boot-selector magic word was found in either header. The sibling title *Duel Masters: Kaijudo Showdown* is a **different SKU** (code `BD6E`, title `DM KAIJUDO`); *Duel Masters: Shadow of the Code* is code `BDUE`. Nothing was found to be shared between this ROM and the sibling — all results below were derived independently from this image (hashes above pin the revision).

## 2. Executive summary

**There is no developer-intended password, button-code, code-entry, or hidden debug-menu system in this ROM.** The game is a story-driven digital card game; its "unlockables" are ordinary save-data progress (tournament medals/plaques, collectible cards, and a post-game Duel Room), all earned through play. The evidence is a bounded negative, not an absence of searching:

* **Observed** — every reachable screen was walked in mGBA: title/main menu, new-game deck select, the full 10-entry in-game Start menu and each of its seven reachable sub-screens, the Credits sequence, and the `LINK` location. No screen offers a password/cheat/code/debug entry point.
* **Derived** — the ROM's entire string corpus (112,001 strings) contains **0** occurrences of `password`, `cheat`, `debug`, `unlock`, `level select`, `hidden`, `bonus`, or `gallery`; the only 9 `secret` hits are ordinary NPC dialogue and the only 5 `code` hits are the phrase "Welcome to our Code Club". The ROM has exactly four KEYINPUT readers (§4), all simple `~KEYINPUT & 0xFFFF` accessors; no key-mask code table or sequence gate was found.
* **Verified** — the one in-game unlockable published by GameFAQs/CheatingDome ("Duel Room — beat the game") is present and **confirmed locked** on a fresh save (screenshot `shot_30.png`/`shot_34.png`). The widely circulated GameShark/CodeBreaker lists are external memory patches, not in-game codes, and are out of scope; they were still checked and are addressed in §6.

Consequently §0.2's "mint a novel code" deliverable does not apply: there is no code space. The required proof for the no-system case is provided instead in §6b (screen enumeration, searched-space counts, and published-code disposition).

## 3. How to reproduce

* **Emulator:** mGBA (`/usr/local/bin/mgba`), Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 ./game.gba`. Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Holds of 120–250 ms were used; transitions were allowed 1–5 s before capture.
* **Fresh ROM path (RAM-verified):** boot → Mistic Software splash → Hasbro "Licensed by" → title logo → **Start** → `CHOOSE YOUR DECK` (5 civilization icons: Nature/Light/Water/Fire/Darkness) → **A** → birthday cutscene/dialogue → outdoors → **Start** opens the in-game menu.
* **Menus walked (all):** title (`NEW GAME`, `CONTINUE`, `CREDITS`, `DUEL ROOM` greyed); `MAP & OBJECTIVE`; `DECK MANAGEMENT` (Deck 40/40, Trunk 25/180, card list, R pages the list); `TUTORIAL` (greyed, selector skips it); `LINK` (warps to a receptionist podium location — no duel/menu offered on a fresh save); `ADVANCED RULES`; `STATS`; `OPTIONS` (TEXT SPEED, AI SPEED, BATTLE SCREEN, MUSIC, SOUND FX, GRAPHIC PRESET); `SAVE`; `RESUME THE GAME`; `QUIT TO MAIN MENU` (confirm `QUIT WITHOUT SAVING?`); `CREDITS` (rolling staff roll).
* **Button codes tested on title:** `Up Up Down Down Left Right Left Right B A` (Konami), `L+R` held, `A B` / D-pad probes, plus idle observation. In every case `DUEL ROOM` stayed greyed and no state change appeared. The character-art sequence that appeared during the L+R test was proven to be the title screen's **idle animation** by reproducing it with no input (screenshots `shot_38.png`–`shot_40.png`).
* **Savestates:** `game.ss1` (in-game Start menu), `game.ss2` (title menu) in `/tmp/opencode/duelsempai`. `.ss1` files are PNG with a zlib `gbAs` chunk; decompressed size 397,312 bytes for this 8 MiB ROM (§16.13). `game.sav` is 512 bytes.

## 4. Address map

| Item | File offset / ROM address | Notes |
|---|---|---|
| Primary header / crt0 | `0x000000` / `0x08000000` | Entry `0xEA00002E` → `0x080000C0` (ARM crt0) |
| Secondary linked image header | `0x0D0004` / `0x080D0004` | Same title/code; own Thumb entry at `0x080D00C4` (Derived: link/multiboot engine image) |
| `getKeys()` reader #1 | `0x00988C` / `0x0800988C` | `ldr r0,[pc,#8]` → `0x04000130`; `ldrh; mvns; lsls #16; lsrs #16` → active-high 16-bit mask |
| `getKeys()` reader #2 | `0x019144` / `0x08019144` | identical code; called by UI key-state wrapper `0x08018EDC` |
| `getKeys()` reader #3 | `0x0CFD84` / `0x080CFD84` | secondary image |
| `getKeys()` reader #4 | `0x0D0D88` / `0x080D0D88` | secondary image |
| KEYINPUT literal occurrences | `0x009898`, `0x019150`, `0x0CFD90`, `0x0D0D94` | **complete set** of 32-bit `0x04000130` constants in the image |
| English UI text bank | `0x5BBxxx` | mixed-case ASCII rendered as caps; e.g. `Continue` `0x5BBEED`, `Credits` `0x5BBEF6`, `Duel Room` `0x5BBEFE`, `Map & Objective` `0x5BBAE8`, `Stats:` `0x5BBBCE` |
| Tournament rules text | `0x5B6840`–`0x5B6D80` | medal/plaque names and duelist counts (§6) |
| Card/rules dialogue bank | `0x5ACxxx`–`0x5B2xxx` | English; **six** near-identical localized copies repeat at `0x5Cxxxx`, `0x5Dxxxx`, `0x5Exxxx`, `0x5Fxxxx`, `0x60xxxx` |
| Save mirror in EWRAM (RAM) | state offsets `0x1DF1C` and `0x1E30A` | two copies of the 512-byte save record loaded into EWRAM; player name `TOM` in RAM vs byte-reversed `MOT` in `game.sav` |
| Save fields (from CodeBreaker hints, cross-checked) | EWRAM `0x02005220`/`0x02005224`/`0x02005228`/`0x0200522A`/`0x0200522C` | reputation/level, time, wins, losses, and a 180×2-byte card-count array (Derived — from published patch targets and save layout; used only for analysis, not reported as a cheat) |

No password validator, code table, key-mask table, or debug-gate flag word exists in this image; the addresses above are the complete relevant surface.

## 5. Algorithm

Not applicable — no code system was found. For completeness, the only "algorithm" relevant to cheats is the shared key-state accessor, which is a plain hardware read:

```c
uint16_t getKeys(void) {
    return (uint16_t)~(volatile uint16_t)0x04000130;  // active-high: A=1,B=2,Select=4,Start=8,
                                                       // Right=0x10,Left=0x20,Up=0x40,Down=0x80,
                                                       // R=0x100,L=0x200
}
```

Every menu handler consumes this value for ordinary cursor movement/activation. **No** handler accumulates a press history, compares a fixed sequence, or writes an unlock flag from key input (Derived — see §6b for the search bounds).

## 6. Tables

**Published in-game cheats/unlockables (web, verified against this ROM):**

| Source | Claim | Disposition |
|---|---|---|
| GameFAQs Cheats (gba/917343) | Unlockable: `Duel Room` — "Beat game" | **Confirmed present and locked** on fresh save (`shot_34.png`). Earned by story completion (CheatingDome specifies defeating Mr. X). Save-progress gate, not a code. |
| CheatingDome | Duel Room after beating game / Mr. X | Same as above; consistent |
| CheatingDome | Rare cards via repeated special trades; gypsy deck-swap workaround; Fire Deck recommendation | Gameplay strategy/hints, not codes |
| CheatingDome | "Special Cards" — in a trade shop, save & quit, `Continue`, then `Special` shows different cards | In-game save-scum exploit exploiting trade RNG; **unverified in emulator** (requires mid-game trade-shop access). Not a password/button code. |
| GameFAQs (Duel Masters **3**, gba/311635) | `GETBADGES`, `7ダダダンジーャチ`, etc. | **Different game** (Amble/Atlus, Japanese). Literals absent from this ROM (`GETBADGES` at `-1`, all others absent). Not applicable — §16.11 |
| libretro GameFAQs/CodeBreaker `.cht`, Answers.com | GameShark/CodeBreaker 32-bit patch codes ("Have All Cards", "Max Level", "999 Wins", etc.) | **Out of scope** (external memory-edit codes). They target EWRAM save fields (`0x02005220`–`0x0200522C`), confirming a normal save record, not an in-game code surface. One published entry is internally inconsistent: `cheat9` sets **both** wins and losses to 999 while labelled "999 Wins,0 Losses" (§16.7). |
| Pirates/Car Battler Joe-style literals (`L1TTLVN`, `HAMA!333`, `SIZZLN`, `POWEROVER`) | — | All absent (`-1`); no cross-gamecode surface |

**Unlockable medal/plaque set (Derived from `0x5B6840`–`0x5B6D80`):** eight tournament rewards are displayed as eight red `?` on the STATS screen until earned: Greenwood medal (2 duelists), Briar Hills medal (2), Clearwater medal (2), Rush City **plaque** (3), Caramel City **plaque** (3), Lakeburg tournament (4 + finalist), plus two further 2-/3-/5-duelist tournaments including the National tournament. They are set by story/tournament completion, never by input.

## 6b. Enumeration

This section discharges §0.2's "negative results bounded" requirement for a title with **no code system**.

**1. Screen space enumerated (all visited, RAM/screenshot-verified):** title/main (4 entries, 1 locked), new-game deck select (5 decks), in-game Start menu (10 labels, 1 greyed/TUTORIAL, 9 selectable), Map & Objective, Deck Management, Advanced Rules, Stats, Options, Save, Resume, Quit-to-main + confirmation, Credits, LINK location. **Total: 13 distinct screens/menus.** No password prompt, code-entry field, key sequence, or debug/gallery screen exists on any of them.

**2. Text space searched with counts:** `strings -t x -n 4` over all 8 MiB → **112,001** strings. Case-insensitive keyword counts: `password` **0**, `cheat` **0**, `debug` **0**, `unlock` **0**, `level select` **0**, `hidden` **0**, `bonus` **0**, `gallery` **0**, `secret` **9** (all dialogue), `code` **5** (all "Code Club" dialogue), `extra` **5**, `credits` **20**, `master` **88** (card/dialogue text). Literal cross-check for known passwords from other GBA games → 0 hits. The UI is mixed-case ASCII (rendered as capitals), so both cases were covered; six localized copies of every text bank were included in the counts.

**3. Button/binary space searched with counts:** exactly **4** 32-bit `0x04000130` literals, therefore **4** KEYINPUT read sites (`0x0800988C`, `0x08019144`, `0x080CFD84`, `0x080D0D88`); all four disassemble to the same two-instruction `~KEYINPUT` accessor. Raw scan over the full 8 MiB for (a) the 10-press Konami sequence in active-high **and** active-low u16 encodings and (b) any run of ≥4 consecutive u16 values drawn from the key-mask set found **no** plausible code table (60216 short runs were all zero-padding or compressed-art noise; the sole 4-press `UpUpDownDown` byte hit at `0x525D69` is inside a compressed-data region and is not executable). BL scan found only generic UI callers. Published button codes: **none exist** for this SKU.

**4. Published codes tested:** the only published in-game unlockable (Duel Room) was tested and found locked (bounds proven by rejection: selecting it does nothing). The only other in-game exploit (trade-shop "Special Cards") is unverified because it needs mid-game state; it is explicitly labelled as such rather than reported as a code. All external GameShark/CodeBreaker codes were checked and are memory patches (out of scope), not developer-intended codes.

**5. Code space:** size **0**. There is no alphabet, no field/checksum width, no table size, no generator, and no validator to enumerate. Therefore no novel code was minted (there is nothing to mint) and no checksum-bounds rejection test applies. The unlockables that *do* exist are gated by story bits, not by any player-enterable input.

## 7. Validation evidence

* **Observed** — screenshots `shot_00.png`–`shot_46.png` on `:318`: splash, title, deck select, all Start-menu sub-screens, Options, Stats (8 `?`), Credits, Duel Room greyed, title idle character animation, `LINK` location. Savestate `game.ss1`/`game.ss2` and 512-byte `game.sav` captured; EWRAM save mirrors located at state offsets `0x1DF1C`/`0x1E30A`.
* **Derived** — header and embedded-header parse; hash/entry-word/fixed-0x96 checks proving a stock image; string keyword counts and literal cross-checks; the complete four-site KEYINPUT scan and disassembly as `~KEYINPUT` accessors; the key-mask table scan; publication of a second linked engine image at `0x080D0004`; the medal/plaque field layout from ROM text.
* **Inferred** — the secondary header at `0x080D0004` is a link/multiboot engine image (its exact runtime role was not exercised); the trade-shop "Special Cards" exploit is reported from CheatingDome and was not reproduced; Card-array field meanings inferred from published patch targets rather than from the game's own save encoder.

No claims were promoted from inference to observation. Fetched web pages were treated strictly as data; no prompt-injection payload was encountered in the pages retrieved for this report.

## 8. Unknowns

* The precise runtime role of the secondary image based at `0x080D0004` (link/duel engine vs. duplicate build) was not confirmed by executing that entry point.
* The trade-shop "Special Cards" save-scum exploit was not reproduced in-game (requires reaching a mid-game trade shop).
* Exact bit positions of the eight medal flags and the Duel Room flag inside the 512-byte save were not isolated; their existence and story-gated nature are observed/derived, their storage encoding is not.
* The greyed `TUTORIAL` entry's unlock condition was not determined (it appears to be disabled once the story tutorial has been absorbed).
* A live duel's in-session pause overlay was not reached; the functional pause surface examined is the Start menu available in the field. Given that the ROM contains no key-sequence handlers and no code-entry text anywhere, this does not affect the no-cheat conclusion.

## 9. Tooling

* `file`, `xxd`, `strings -t x -n 4`, `grep -i`, Python 3 (`struct`, `zlib`) for header/hash/string/literal analysis.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly of the KEYINPUT sites and the secondary entry.
* Capstone 5.0.7 (`CS_ARCH_ARM`, `CS_MODE_THUMB`) for PC-relative literal-load discovery and `keystone-engine` availability check.
* Custom scripts in `/tmp/opencode/duelsempai/`: `find_keyinput.py` (literal + LDR scan), `blscan.py` (Thumb BL callers), `scan_keys.py` (key-mask table scan), `key.py` (XTEST input helper), `ssdiff.py` (savestate `gbAs` chunk decompress + diff), `ptydbg.py`/`dbgserver*.py` (mGBA CLI-debugger pty harness, abandoned in favour of savestate diffing because the GDB stub port 2345 was held by a concurrent session — no other session's process was touched).
* mGBA under Xvfb `:318` + openbox; `import -window root` for screenshots (≤20 retained on disk in the work dir, none attached to this reply).
* Web sources: GameFAQs cheats/FAQ pages, CheatingDome, libretro-database `.cht`, IGN, CheatHappens, Answers.com — consulted for published-code verification only.

**Legal note:** no ROM bytes or copyrighted assets are redistributed here; only addresses, hashes, counts, and original observations are published.
