# Pokémon Sapphire (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Pokémon Sapphire/Pokémon Sapphire.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `POKEMON SAPP` |
| Game code / maker | `AXPE01` (AGB-AXPE-USA), maker `01` (Nintendo) |
| Version / complement / checksum | 1 / `0x54` / `0x0000` |
| Entry word | `0xEA000032` → `0x080000D0` |
| MD5 | `3a32fd98b065283d09eeba1ce0542888` |
| SHA-1 | `4722efb8cd45772ca32555b98fd3b9719f8e60a9` |
| SHA-256 | `2f680a43e5c57aede4cb3b2cb04f7e15079efc122c88edaacfd6026db6e920ac` |

Phase 0 checks: a full-file scan for the 156-byte Nintendo logo finds exactly one header, at file `0x0`. The complement byte is consistent with the stock formula (`-(sum(0xA0..0xBC)+0x19) & 0xFF = 0x54`, stored `0x54`), so the header has not been rebuilt. The 16-bit checksum `0x0000` is a normal retail artifact here. No appended trainer, no second image, no cracktro patch.

**Text encoding (critical for any string search):** this game does NOT use ASCII for in-game text. The byte→glyph map is `A..Z = 0xBB..0xD4`, `a..z = 0xD5..0xEE`, `0..9 = 0xF1..0xFA`, space `= 0x00`, EOS `= 0xFF`. All `strings` searches for English words return zero hits unless the search term is first encoded with this map. All text addresses below were found by encoding the target word and searching the raw bytes.

## 2. Executive summary

This retail US Sapphire image contains **one genuine developer-intended password system** — the *Mystery Event Club* "secret saying", entered on the in-game Easy Chat "profile" screen — plus several in-game button codes and a large amount of **cut** debug material that is **not reachable** in retail.

The password is a 4-word Easy Chat phrase: **`MYSTERY / EVENT / IS / EXCITING`**. The validator is a Thumb routine at `0x080E80B4` that renders each selected word to text and byte-compares it against a constant 4-word table at `0x083DB6F0` (`{0x143A,0x1817,0x100B,0x200F}`). On a match it sets VAR_0x8004 (`0x0202E8CC`) to 1. The *calling* script (`0x081B1BE9`/`0x081B1C1D`) then requires badge 5 and an unset flag before setting `FLAG_SYS_EXDATA_ENABLE` (`0x084C`), which adds the `MYSTERY EVENTS` option to the main menu (`src/main_menu.c`: `IsMysteryEventEnabled() == TRUE → HAS_MYSTERY_EVENT`). The interacting NPC has **no hide flag**, so the screen is reachable from a fresh game; the badge test gates only the final flag/effect.

Published lists (cheatingdome, chaptercheats) give the phrase as **`MYSTERY EVENT IS EXITING`** — a typo. `EXITING` does not exist in the 996-word Easy Chat vocabulary, so the published spelling is literally unenterable; the corrected spelling is the real password.

The game's button codes are real and defined in `src/title_screen.c`: `B+Select+Up` (clear save), `B+Select+Left` (reset RTC), and `A+B+Start+Select` (soft reset). The soft-reset combo was **confirmed dynamically** in mGBA. Sound-Test/Driver-Test text is present, but its menu is reachable only by replacing the Options menu handler (a ROM/GameShark patch) — not by any controller input. The larger Test Menu / programmer debug menu is **cut**, not gated: its option text and its 16-entry order table are absent from this ROM, and the code is behind `#if DEBUG`.

A prompt-injection payload was found in a fetched TCRF mirror page ("This page is not intended for humans … instructions … only for LLMs … whoever is operating this AI agent is a clown"). It was treated as untrusted data and ignored.

## 3. How to reproduce

**Emulator:** mGBA (SDL), display `:317`, `SDL_AUDIODRIVER=dummy`, `mgba -3 ROM`.
Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Key holds of 45–70 ms; longer holds trigger key repeat and re-trigger dialogues (§16.2 of the guide).

**Static reproduction of the password:**
1. Decode text with the charmap in §1. Search `MYSTERY`, `EVENT`, `IS`, `EXCITING` → word strings at `0x3DD29E`, `0x3DDA60`, etc.
2. The constant phrase table is at file `0x3DB6F0` (ROM `0x083DB6F0`): bytes `3a 14 17 18 0b 10 0f 20`.
3. Find xrefs with a PC-relative literal scan for `0x083DB6F0` → one hit at file `0xE80EC`, inside the validator at `0x080E80B4`.
4. Disassemble `0x080E80B4..0x080E8128` (Thumb) to recover the comparison loop.
5. Find the caller by searching for the "secret saying" text and its pointer: text at ROM `0x081B2172`, pointer at file `0x1B1C34`, script bytes `0f 00 72 21 1b 08 09 03 6c 02` at ROM `0x081B1C32`.
6. Enumerate the word vocabulary from the 22 group `words.h` tables (996 words) and locate each target string exactly once.

**Dynamic walk performed (screenshots in `/tmp/pokemonsapphire/`):**
- `07_title..08_title_wait` — title screen; `10_options` — Options menu;
- `26_after_intro110..28_ow_room` — New Game, Birch intro, name entry, bedroom;
- `22_pause_try` — in-game pause menu (BAG / name / SAVE / OPTION / EXIT);
- `37_reset_combo` — **soft reset confirmed** by holding Select+Start+A+B; the game returned to the copyright screen.
- `43_route101`, `52_mom_question` — overworld / Mom script attempts while navigating toward Petalburg.

**Dynamic limitation (stated explicitly, not hidden):** the password phrase was **not typed on the Easy Chat screen**. Two obstacles were hit: (a) reaching the Petalburg NPC from a fresh game is blocked by a long, re-triggering scripted intro/Mom sequence in the harness; (b) an attempt to open the genuine Easy Chat screen by calling `ShowEasyChatScreen` (`0x080E60F8`, located via the `gSpecials` table at `0x0814B1B4 + 4*0x5F`) from the GDB stub faulted. The accept decision is therefore established by the validator's instruction sequence plus the complete word-table enumeration, not by an observed in-game acceptance. All other claims below are labelled by evidence type.

## 4. Address map

| Address (ROM) | File offset | Meaning |
|---|---|---|
| `0x080E80B4` | `0x0E80B4` | `CheckMysteryEventPhrase` validator (Thumb; decomp label `sub_80E8094` is off by +0x20 in this build) |
| `0x083DB6F0` | `0x3DB6F0` | `gMysteryEventPhrase` = `{0x143A, 0x1817, 0x100B, 0x200F}` |
| `0x080E8114` / `0x080E8122` | `0x0E8114` / `0x0E8122` | return `r0=0` (reject) / `r0=1` (accept) |
| `0x081B1B14` | `0x1B1B14` | Mystery Event Club NPC script (Petalburg Center, OBJ_EVENT_GFX_MAN_5, flag `0`) |
| `0x081B1C1D` | `0x1B1C1D` | gate: `checkflag 0x080B` → `goto_if 0,skip`; `checkflag 0x084C` → `goto_if 1,skip`; `setflag 0x084C`; show `0x081B2172` |
| `0x081B2172` | `0x1B2172` | "Oh? You know the secret saying! … MYSTERY EVENT CLUB!" (EOS at `0x1B21D3`) |
| `0x0202E8CC` | RAM | `gSpecialVar_0x8004` (from `gSpecialVars` pointer table at ROM `0x0814B16C`) |
| `0x0202E8DC` | RAM | `gSpecialVar_Result` |
| `0x0200AE14` | RAM | `gEasyChatStruct`; selected-word buffer at `+0xFFFF61F8` = `0x0200100C` |
| `0x080E60F8` | `0x0E60F8` | `ShowEasyChatScreen` (from `gSpecials[0x5F]`) |
| `0x0814B1B4` | `0x14B1B4` | `gSpecials` pointer table |
| `0x3D0300..0x3D0400` | — | Sound Test / Driver Test UI text ("BGM", "SE", "R: DRIVER-TEST", VOICE/VOLUME/PANPOT/…) — present but cut |
| `0x19D380..0x19D700` | — | Trick House / Mechadoll quiz text incl. "SECRET CODE" (`0x19D451`) |

## 5. Algorithm

Validator (`0x080E80B4`), pseudocode, transcribed from the Thumb disassembly:

```
for i in 0..3:
    word_text[i]    = RenderEasyChatWord(selected_words[i])   // BL 0x080EB238
    expected_text[i] = RenderEasyChatWord(gMysteryEventPhrase[i])
    a = word_text[i]; b = expected_text[i]
    while *a != 0xFF and *b != 0xFF:
        if *a++ != *b++: return 0
    if (*a != 0xFF) or (*b != 0xFF): return 0
return 1
```

The acceptance path is the Easy Chat screen with mode `VAR_0x8004 == 0` (profile). On A/OK, `src/easy_chat_1.c` does `gSpecialVar_0x8004 = CheckMysteryEventPhrase()`. The NPC script then:

```
if (FLAG_BADGE05_GET == 0) return;
if (FLAG_SYS_EXDATA_ENABLE == 1) return;
setflag FLAG_SYS_EXDATA_ENABLE;
msgbox "Oh? You know the secret saying! … MYSTERY EVENT CLUB!", MSGBOX_SIGN;
```

Byte-level proof of the gate at `0x081B1C1D`: `2b 0b 08` (checkflag 0x080B) / `06 00 3c 1c 1b 08` (goto_if 0 → 0x081B1C3C) / `2b 4c 08` (checkflag 0x084C) / `06 01 3c 1c 1b 08` (goto_if 1 → skip) / `29 4c 08` (setflag 0x084C) / `0f 00 72 21 1b 08 09 03` (loadword+msgbox sign) / `6c 02` (release; end).

## 6. Tables

**Password (Easy Chat word IDs):**

| Slot | Word | ID | Derivation |
|---|---|---|---|
| 0 | MYSTERY | `0x143A` | group CONDITIONS (0x0A) << 9 \| 0x3A |
| 1 | EVENT | `0x1817` | group LIFESTYLE (0x0C) << 9 \| 0x17 |
| 2 | IS | `0x100B` | group ENDINGS (0x08) << 9 \| 0x0B |
| 3 | EXCITING | `0x200F` | group ADJECTIVES (0x10) << 9 \| 0x0F |

Stored little-endian at `0x083DB6F0`: `3a 14 17 18 0b 10 0f 20`.

**Button codes (from `src/title_screen.c` constants):**

| Combo (active-high mask) | Location | Effect |
|---|---|---|
| `B+Select+Up` (`0x046`) | title screen | `CLEAR_SAVE_BUTTON_COMBO` → "Clear all game data areas?" |
| `B+Select+Left` (`0x046` variant) | title screen | `RESET_RTC_BUTTON_COMBO` → reset internal clock |
| `A+B+Start+Select` (`0x00F`) | in game | `A_B_START_SELECT` → soft reset — **Observed** |

**Trick House "secret codes" (normal gameplay, not cheats):** eight fixed phrases on scrolls (`"Trick Master is fabulous."`, `"…smart."`, `"…coveted."`, `"…cool."`, `"…a genius."`, `"…my life."`, `"…huggable."`, `"Trick Master I love."`), first seen at `0x19D387`. The door only checks that the scroll was read; these are event progress tokens, not a validator.

## 6b. Enumeration

**Space definition.** The Easy Chat vocabulary contains **996 distinct word strings** across 22 groups. The profile is an **ordered 4-slot** selection. Raw input space = 996⁴ ≈ **9.84 × 10¹¹** phrases. The validator compares the *rendered text* of each slot, not the raw ID, so aliases would be possible only if two word IDs rendered the same string.

**Full enumeration of the accepted set.** I parsed every `words.h` group table and searched for each target string across all 996 words:

```
MYSTERY  → CONDITIONS[0x3A]  only
EVENT    → LIFESTYLE[0x17]   only
IS       → ENDINGS[0x0B]     only
EXCITING → ADJECTIVES[0x0F]  only
```

Each target string occurs **exactly once**, so there are **no text aliases**. Because the comparison is positional and exact, the accepted set has cardinality **1**: the phrase `MYSTERY EVENT IS EXCITING`. There is consequently no second, unpublished accepted code to mint — the §0.2 "novel code" objective is satisfied instead by the corrected/published-list mismatch described next, and the negative is proven by counting the whole space rather than by sampling.

**Published-list correction (equivalent of a novel code).** Both cached cheat pages give `MYSTERY EVENT IS EXITING`. `EXITING` is absent from all 996 words (verified by the same table scan), so the published phrase cannot be composed on the real screen; the ROM's own constant requires `EXCITING`. This is a concrete, reproducible correction to the published corpus (§16.7).

**Bounds proven by rejection.** A wrong word in any slot renders a different string and fails the per-character loop at `0x080E80F8..0x080E810C`, returning `r0 = 0` at `0x080E8114`. A phrase that passes the word check still fails the *later* gate if `FLAG_BADGE05_GET` is clear — the script at `0x081B1C1D` returns without setting `FLAG_SYS_EXDATA_ENABLE`. These two rejection layers (word compare, then badge/flag gate) are distinct and both are proven from the instruction bytes. The GDB oracle was attempted on the raw validator with the correct four IDs written to `0x0200100C` (confirmed by `x/4xh`), but outside the Easy Chat screen the word→text converter returned an uninitialised fill (`02 c0 5e e5 …` at both work buffers), so that particular oracle run returned 0 for environmental reasons; it is reported as such and not used as evidence of rejection.

**Debug-menu closed set.** Keyword counts over the decoded text vocabulary: `WATANABE/SOGABE/TAMADA/KAGAYA/MATUDA/MORI` = 0 hits; `DEBUG` (as a title string) = 0; the TCRF 16-byte Test-Menu order table `03 06 04 FF …` = 0 hits; `PASSWORD` in the debug sense = 0. Sound-Test/Driver-Test text *is* present (16+ UI labels around `0x3D036C`), but the only documented way to reach it is to patch the Options-menu handler, i.e. a ROM/GameShark modification, not controller input. The programmer debug menu is compiled out of retail (`#if DEBUG`), so it is a **cut feature**, not a gated one.

## 7. Validation evidence

- **Observed:** boot/header/hash; title and Options screens; New Game intro, name entry, overworld and pause menu (screenshots above); soft reset via A+B+Start+Select returning to the copyright screen; all ROM byte dumps, pointer scans and disassembly; unique Nintendo-logo header; zero debug-name/order-table hits.
- **Derived:** charmap; word IDs and constant table; validator algorithm; gate flags `0x080B`/`0x084C` and the resulting main-menu change; 996-word vocabulary and cardinality-1 accepted set; published `EXITING` typo; button-code masks from `title_screen.c`.
- **Inferred / not exercised:** typing the password on the Easy Chat screen (see §3 dynamic limitation); the final "secret saying" message and `MYSTERY EVENTS` icon were not produced on screen. No screenshot is claimed for those states.

## 8. Unknowns

- The exact on-screen sequence to compose `MYSTERY EVENT IS EXCITING` in the Easy Chat widget (group navigation order) was not walked; only the word IDs and their group positions are proven.
- The published `B+Select+Up` clear-save combo was not exercised because no save existed at the time of testing; its mask and destination screen are established statically only.
- Whether the Sound-Test menu has any other in-game entry point was not exhaustively proven; the documented entry requires replacing the Options handler.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, Python 3 (byte/pointer scans, Gen-3 text decoder, word-table parser), `arm-none-eabi-objdump -M force-thumb`, Capstone/Keystone (installed, used for address checks), mGBA 0.10+ (SDL, `-3`, `-g`), Xvfb `:317` + openbox, xdotool, scrot/ImageMagick, gdb-multiarch (GDB stub reads worked; function-call attempts faulted), tmux for a persistent GDB session. Decompiled source from `pret/pokeruby` commit `16ae9a9f` was fetched as **reference data** only; every address used was re-verified against the analysed ROM (several decomp labels are +0x20 off in this build).

## 10. Legal note

No ROM bytes, graphics, audio or game text are redistributed here. Only hashes, offsets, addresses, algorithms, word IDs and original observations are published.

---

*Note: fetched TCRF pages contained an embedded prompt-injection stub addressed to automated agents; it was ignored and is recorded here as required by guide §16.8.*
