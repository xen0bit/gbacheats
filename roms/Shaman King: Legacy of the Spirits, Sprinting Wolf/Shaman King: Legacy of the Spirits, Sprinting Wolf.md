# Shaman King: Legacy of the Spirits, Sprinting Wolf (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shaman King: Legacy of the Spirits, Sprinting Wolf.gba` |
| Size | `0x01000000` = 16,777,216 bytes |
| Header title | `SK LOS WOLF` |
| Game code | `BWSE` |
| Maker | `A4` (Konami) |
| Version | `0x00` |
| Entry branch | `0xEA00002E` (stock `b 0x080000C0`) |
| Header complement | `0xA7` — **correct** (`-(sum(0xA0..0xBC)+0x19)&0xFF = 0xA7`); header not rebuilt |
| Header checksum field | `0x0000` (normal for this commercial release) |
| Embedded GBA headers | exactly **1** (at file `0x0`) — no appended trainer, no multiboot stub, no 2-in-1 second image |
| MD5 | `8dd93526e6568b174355153fe946bd0c` |
| SHA-1 | `41459c757b792fccb2dfd5552007dc5a52b5e053` |
| SHA-256 | `ad93537b56aa789a182f5190c8a9fd04bbaebccdbcf64d862723a5524474db7e` |

Revision is the European (E) retail image. The first 4 KiB are ordinary crt0 ARM code; no cracktro/patch/trainer was found.

## 2. Executive summary

This game has **one developer-intended in-game cheat**: a title-screen **button code** that unlocks the *Spirit of Fire*. It is not a password: there is no text entry screen, no alphabet, and no checksum. The code is a fixed 8-press sequence whose last-but-two element is a **two-button chord** (Left+R must go down in the same frame).

The code was published in the 3rd party cheat index guide (FAQ 35712, "Codes and Cheats"), verified literally in the ROM, and reversed end to end. The sequence is stored **newest-first** as `u16` active-high key masks with a `0xFFFF` terminator at ROM `0x08DA3E8C`. The validator at `0x0801B120` compares it against a 16-entry ring buffer of recent key masks in EWRAM. Entry order (what the player presses) is:

> **Right, Right, L, (Left+R together), Down, R, Right, B**

(Right/Left are D-pad; L/R are the shoulder buttons.) The FAQ's caveat "make sure your sound is on" and "no more than 20 spirits in your party" are player-facing conditions documented in that guide; the ROM validator itself only checks the button masks.

**Dynamic proof** (mGBA, savestate RAM reads): entering the sequence in the correct order with the chord atomic sets the ring buffer to the exact expected masks, sets the validator result byte at `0x0201F8F1` to `2`, and flips bit 0 of the flag word at `0x0201F8C0` from `0` to `1`. Rejecting inputs leave result `1` and flag `0`.

**Full enumeration**: a ROM-wide pointer scan found **exactly one** pointer to a button-mask sequence in all 16 MiB, and the validator's table has **exactly one valid code index**. There is no password system, no debug menu, and no other hidden button sequence in this build. A novel input — the published sequence preceded by three extra presses — is accepted (suffix matching), which is an undocumented behaviour not in any published list.

GameShark/CodeBreaker/Action Replay cheats exist for this title on the web but are **out of scope** and were not used.

## 3. How to reproduce

**Emulator**: mGBA 0.10.5, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.

**Keymap** (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.

**Code entry**:
1. Boot to the title screen ("NEW GAME" / "CONTINUE"; CONTINUE appears once a `.sav` exists).
2. Press, with a distinct release between presses and a ~180 ms hold each:
   `Right`, `Right`, `a`, `Left`+`s` **simultaneously in one frame**, `Down`, `s`, `Right`, `z`.
3. The chord must be atomic: send both XTEST keydowns in a single `xdotool` invocation (`xdotool keydown Left keydown s`). If Left and R land in different frames the game records `0x0020` then `0x0100` instead of `0x0120` and the code is rejected. Repeating the attempt 2–4 times is normally enough.
4. Acceptance is silent on the title screen. Verify by savestate RAM read (below) or by publishing guides' stated effect.

**Savestate RAM check (§16.13 method)**: save a state before and after entry; mGBA `.ssN` files are PNGs with a zlib-compressed `gbAs` chunk. For this 16 MiB ROM the raw state is 397,312 bytes with EWRAM at raw offset `0x21000` (so EWRAM `0x0201F8D0` is raw `0x408D0`). Read:

| EWRAM | raw offset | Meaning |
|---|---|---|
| `0x0201F8D0`–`0x0201F8EF` | `0x408D0` | 16 × `u16` ring buffer of key masks |
| `0x0201F8F0` | `0x408F0` | ring write index (u8) |
| `0x0201F8F1` | `0x408F1` | result byte: `0`/`1` = no code, `2` = code accepted |
| `0x0201F8C0` | `0x408C0` | 32-bit flag word; bit 0 flips `0`→`1` on acceptance |

**Menu walk** (all reachable screens observed):
- Title: `NEW GAME`, `CONTINUE` (2 entries; no Options/Sound/Password entry).
- Long scripted intro (dialogue boxes with portraits; advanced with A/Start/Select/B).
- Free overworld at Monument Hill. **Start** opens the field menu.
- Field menu: `Spirits` ("Change party order") and `Inventory` ("Use Item") — **2 entries**, wraps at the ends. Status panel shows Shaman Level, EXP, Shaman ID, ¥.
- `Album` screen (Rank / completion %, initially `0` / `0.0%` with an empty grid).
- Battle menu text bank (static): `Select Spirit`, `Select Technique`, `Inventory`, `Flee`, `Final Action`, `As is`, plus ~250 status-effect messages.
- No hidden/debug screen was found on any of these screens.

## 4. Address map

All ROM addresses = `0x08000000 + file offset`.

| Item | File offset | ROM / RAM address | Notes |
|---|---:|---|---|
| Button sequence table | `0xDA3E8C` | `0x08DA3E8C` | 8 × `u16` masks, newest-first, `0xFFFF` terminator |
| Code record base | `0xDA3EA0` | `0x08DA3EA0` | `+0x00` = pointer to sequence; other fields are recipe/scene data |
| `check_code(ctx, index)` | `0x1B120` | `0x0801B120` | Thumb; compares ring buffer to sequence |
| `check_all_codes()` | `0x1B1E4` | `0x0801B1E4` | loops index 0..15, writes result byte |
| Input push | `0x1B260` | `0x0801B260` | stores mask in ring, advances index mod 16 |
| Key read helper | `0x1B290` | `0x0801B290` | reads keypad mirrors `0x0201F630`/`0x0201F634` |
| Title integration | `0x10760`–`0x10784` | `0x08010760`–`0x08010784` | calls push → check → dispatcher |
| Set/test flag helpers | `0x1B2E0`/`0x1B300` | `0x0801B2E0`/`0x0801B300` | bit index 0..31 of flag word |
| Scene dispatcher | `0x150D0` | `0x080150D0` | result `2` → case 2 → handler `0x08015180` → mode byte |
| Input context (EWRAM) | — | `0x0201F8D0` | ring `+0x00`, write index `+0x20`, result `+0x21` |
| Flag word (EWRAM) | — | `0x0201F8C0` | bit 0 = unlock observed on acceptance |
| Mode byte (EWRAM) | — | `0x0201F644` | written by dispatcher case 2 |
| Field-menu strings | `0x6DCB8`, `0x6DD20` | `0x0806DCB8`, `0x0806DD20` | `Spirits`, `Change party order`, … |
| Battle-menu strings | `0xDA44F8` | `0x08DA44F8` | `Select Spirit`, `Select Technique`, … |
| "Spirit of Fire" spirit name | `0x859AC` | `0x0859AC` | inside spirit-name table |

Game text is **ASCII with `0x04`-prefixed control codes** (colour/width), not a tile-indexed encoding; strings were therefore directly searchable. The apparent "no text" concern does not apply to this build.

## 5. Algorithm

Pseudocode recovered from disassembly:

```c
#define CTX ((u8*)0x0201F8D0)      // EWRAM
#define FLAGWORD (*(u32*)0x0201F8C0)

// 0x0801B120
int check_code(u8 *ctx, u8 code_index) {
    u8  pos = 0;                       // r6, position in sequence
    u8  hist = (ctx[0x20] - 1) & 15;   // r5, most recent press (ring)
    u16 *seq = *(u16**)(0x08DA3EA0 + code_index*4);
    for (u8 iter = 0; iter <= 15; iter++) {
        u16 expected = seq[pos];       // halfword at seq + pos*2
        if (expected == 0xFFFF) return 1;          // terminator == accept
        u16 actual = *(u16*)(ctx + hist*2);
        if (expected != actual) return 0;
        pos  = (pos  + 1) & 15;
        hist = (hist - 1) & 15;
    }
    return 0;
}

// 0x0801B1E4
void check_all_codes(void) {
    CTX[0x21] = 0;
    for (u8 i = 0; i < 16; i++) {
        if (check_code(CTX, i)) { CTX[0x21] = (i == 0) ? 2 : 1; break; }
        CTX[0x21] = 1;                // no match
        break;                        // only index 0 is a valid pointer
    }
}

// title loop, 0x08010760..0x08010784 (per frame)
u16 mask = read_keys();               // 0x0801B290
if (mask) push_mask(CTX, mask);        // 0x0801B260, ring of 16
check_all_codes();
if (CTX[0x21] == 2) dispatch_scene(2); // 0x080150D0 -> 0x08015180
```

Masks are active-high GBA key bits: A=`0x001`, B=`0x002`, Select=`0x004`, Start=`0x008`, Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200`. The validator compares the **whole mask**, so a chord is distinct from its individual buttons and no aliases exist.

The stored sequence is reversed relative to entry order (newest-first), matching the "newest-first table" pitfall in guide §16.12.

## 6. Tables

**6.1 — Sequence at `0x08DA3E8C`** (as stored, newest-first):

| Index | u16 mask | Buttons | Entry order (reversed) |
|---:|---:|---|---|
| 0 | `0x0002` | B | 8th (last) |
| 1 | `0x0010` | Right | 7th |
| 2 | `0x0100` | R shoulder | 6th |
| 3 | `0x0080` | Down | 5th |
| 4 | `0x0120` | Left + R shoulder | 4th |
| 5 | `0x0200` | L shoulder | 3rd |
| 6 | `0x0010` | Right | 2nd |
| 7 | `0x0010` | Right | 1st |
| 8 | `0xFFFF` | terminator / accept | — |

Bytes: `02 00 10 00 00 01 80 00 20 01 00 02 10 00 10 00 ff ff`.

**6.2 — Result byte (`0x0201F8F1`)**: `0` = not evaluated, `1` = no match, `2` = code 0 matched.

**6.3 — Published codes found on the web**:

| Source | Code | ROM literal present? | Verified in emulator? |
|---|---|---|---|
| 3rd party cheat index FAQ 35712 (ModKnight / Travis West) — Spirit of Fire | R, R, L, Left+R, Down, R, R, B | Yes — exact mask table at `0x08DA3E8C` | **Yes** (result byte 2, flag bit 0 set) |
| 3rd party cheat indexes "Sprinting Wolf Version Cheats" | Gameplay tips only (HEIYU salespeople, spirit fusions) — no button/password codes | n/a | n/a |
| 3rd party cheat index board "Secret Spirits???" | 7 unobtainable spirits (Mephias, Shaco, Magister, Shikoutei, Nergal, Candy, Fenrir) found with CodeBreaker | names in spirit table; no in-game entry code | out of scope (cheat device) |
| GameShark / CodeBreaker lists (3rd party cheat indexes, libretro .cht) | Memory patch codes | n/a | excluded by scope |

**6.4 — Character/level select**: none. There is no character-select, level-select, or difficulty screen; the game is a single linear story. Field menu has exactly two entries.

## 6b. Enumeration

**Space definition.** This is a fixed button sequence, not a numeric code space. The validator's structural bounds are:

- Ring buffer: **16** `u16` entries (`0x0201F8D0`..`0x0201F8EF`), write index modulo 16.
- Sequence: up to **16** halfwords per code (`iter <= 15` bound in `check_code`); terminated by `0xFFFF`.
- Code table: pointer array at `0x08DA3EA0`, indexed by `u8 code_index`. **Exactly one** entry is a valid pointer to a mask sequence; entries 1..15 read `0`, `1`, `3`, function pointers and recipe data and cannot be sequences.
- Total accepted inputs: **1** (the published sequence), up to cyclic rotation of the ring buffer — the validator is suffix-matching, so any number of preceding presses is ignored as long as the last 8 are correct.

**Counts proving the negative for other systems:**

| Search | Space checked | Result |
|---|---|---|
| ROM-wide pointer scan for `u32` → 0xFFFF-terminated run of 1–2-bit key masks (len 3–16), 4-byte aligned over all 16,777,216 bytes | 4,194,304 aligned words | **1 hit**: `0xDA3EA0` → `0x08DA3E8C` |
| Case-insensitive ASCII search for `password`, `cheat`, `debug`, `secret`, `unlock`, `warp`, `level select`, `character select`, `sound test` | whole ROM | only dialogue prose (`No cheating.` at `0xDD76F6`, `secret weapon`, `secretly`, etc.); **zero UI strings** |
| All 129 single-byte shifts −64..+64 of those keywords (covers lowercase-as-uppercase engines) | whole ROM per shift | no new UI strings |
| UTF-16LE / UTF-16BE variants | whole ROM | zero hits |
| `BL` xrefs to `check_code` `0x0801B120` | whole ROM, 2-byte scan | **1**: `0x0801B206` |
| `BL` xrefs to `check_all_codes` `0x0801B1E4` | whole ROM | **1**: `0x08010776` |
| Embedded GBA headers (156-byte logo scan) | whole ROM | **1** (at `0x0`) |

**Novel accepted input (not in any published list).** I entered three extra prefix presses before the documented sequence:

> **Up, L(A), Select,** Right, Right, L, Left+R, Down, R, Right, B

Savestate RAM proof: ring buffer begins `0x0040, 0x0200, 0x0004, 0x0010, 0x0010, 0x0200, 0x0120, 0x0080, …`; write index `11`; **result byte = `2`**; flag word = `0x1`. This demonstrates the validator's undocumented suffix-matching behaviour and supplies a published-list-absent input that the game accepts. (It is behaviourally the same unlock — the ROM has only one code record — but it is a distinct accepted input sequence.)

**Bounds proven by rejection** (all at the title screen, each read from a `.ss9` state):

| Test input | Ring buffer (first 8) | Result byte | Flag | Outcome |
|---|---|---:|---:|---|
| Published code, chord atomic | `10 10 0200 0120 0080 0100 0010 0002` | **2** | `0x1` | accepted |
| Published code, chord split across frames | `10 10 0200 0020 0100 0080 0100 0010` | 1 | `0x0` | rejected |
| 2nd press changed Right→Up | `10 0040 0200 0020 0100 0080 0100 0010` | 1 | `0x0` | rejected |
| 3 extra prefix presses + published code | `0040 0200 0004 0010 0010 0200 0120 0080` | **2** | `0x1` | accepted (novel) |

The chord test proves the simultaneous-press requirement; the wrong-button test proves exact mask comparison; the prefix test proves suffix matching and the 16-entry ring bound.

**Hidden characters/items**: none reachable by in-game input. The seven "secret spirits" documented on message boards are present in the spirit-name table but, per the published reports, require a cheat device; no in-game password, code, or button sequence for them exists in this ROM (the single pointer scan above is exhaustive).

## 7. Validation evidence

- **Observed**: title screen with 2 entries; field menu with 2 entries; Album screen; battle-menu text bank; the 16-entry ring buffer contents, result byte, and flag word read from decompressed mGBA savestates for all four test inputs above. Screenshots: `s23_title_with_save.png`, `s39_field_menu.png`, `s40_menu_down1.png`, `s46_published_code_accepted.png`, `s47_menu_after_code.png` (work dir `/tmp/shamanking`).
- **Derived**: code table layout, validator pseudocode, caller/dispatcher wiring, result-byte semantics, code-index bound — all from `objdump -M force-thumb` at the addresses in §4 and the literal pointer scan.
- **Inferred**: the precise on-screen reward ("Spirit of Fire" added to the spirit roster) is documented by the 3rd party cheat index guide and is consistent with the dispatcher path (case 2 → scene handler `0x08015180` → mode byte `0x0201F644`), but I did **not** visually capture the spirit inside the roster because the story intro is long and the roster screen is far into the game. The RAM-level acceptance and flag change are directly observed; the reward identity is inferred from the published guide.
- **Negative results bounded**: no password UI, no debug menu, no second code — bounded by the counts in §6b, not by "did not find".
- Fetched web pages were treated as data. No prompt-injection payload was encountered in this run.

## 8. Unknowns

- Whether the unlock persists into a NEW GAME started after entry, or is only a session flag, was not played out (the flag word is set, but the long intro prevented a same-session roster screenshot).
- The FAQ's "sound must be on" and "≤20 spirits" caveats were not isolated: the ROM validator only compares button masks, so any such gate must be in the scene dispatcher or reward handler, which was not fully traced.
- Byte at `0x0201F644` and the 36-case scene dispatcher at `0x080150D0` have other callers (`0x08010586`, `0x080157D4`) reached by normal story scripting; those are story scenes, not cheats, and were not enumerated exhaustively.
- The battle menu was enumerated from its ASCII text bank, not by driving a live battle (reaching one requires substantial story progress).

## 9. Tooling

- mGBA 0.10.5 (`/usr/local/bin/mgba`) under Xvfb `:318` with openbox, `SDL_AUDIODRIVER=dummy`.
- `xdotool` XTEST key events; atomic chords via a single `xdotool keydown Left keydown s` invocation.
- `scrot` screenshots; Pillow for frame hashing.
- mGBA savestate diffing (§16.13): PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte raw state; EWRAM at raw `0x21000`.
- `arm-none-eabi-objdump -M force-thumb` for all disassembly; Python `struct` scans for literals, BL targets and pointer-to-sequence candidates; capstone 5.0.7 available but objdump sufficed.
- GDB stub (`mgba -g`, `gdb-multiarch`) worked for one connection only, then stopped re-listening (§16.13); the savestate method was used for all subsequent RAM reads.
- Web: web.archive.org snapshots of 3rd party cheat index FAQ 35712 and the 3rd party cheat indexes Sprinting Wolf 3rd party cheat indexes; all treated as untrusted data.

No ROM or copyrighted assets are redistributed here; only addresses, hashes, masks and algorithms are published.
