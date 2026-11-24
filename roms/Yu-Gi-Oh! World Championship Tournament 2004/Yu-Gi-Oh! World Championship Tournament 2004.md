# Yu-Gi-Oh! World Championship Tournament 2004 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! World Championship Tournament 2004.gba` |
| Size | 16,777,216 bytes (0x01000000 / 128 Mbit) |
| Header title (0xA0) | `YWCT2004USA` |
| Game code (0xAC) | `BYWE` — **not** `AYWE` (Worldwide Edition) or `A2YE` (7 Trials 2005) |
| Maker (0xB0) | `A4` (Konami) |
| Version (0xBC) | 0x00; complement (0xBD) = 0xAF; checksum (0xBE) = 0x0000 |
| Entry word | `0xEA00002E` → stock crt0 at 0x080000C0 |
| MD5 | `8517049ce498d84530c953d6a8b3112e` |
| SHA-1 | `3a7fceffa1405640fe4606e006d272d1af542f2b` |
| SHA-256 | `516530e73ba2ebd2fc8c4280cac13bc125dfb6c1fa1678d35fb5dc8a2a9c063c` |

Analysis was on a byte-identical copy at `/tmp/yugiohwct2004/game.gba`; the ROM folder was left untouched. The Nintendo logo at 0x04 is nonstandard (patched dump) but the image boots normally in mGBA 0.10.5.

## 2. Executive summary

This SKU has **no card-password system** (a 3rd party cheat index's General FAQ for this exact title: "Passwords are gone!") and no ASCII password/debug strings. Its only in-game cheat surface is a single **10-press button code**: the Konami code `↑ ↑ ↓ ↓ ← → ← → B A`, which replays the staff-credits sequence. It is **gated** on a "credits already viewed" bit (`0x02010015 & 0x04`). On a fresh save that byte is `0x01`, so the code is inert until credits have been seen once — this is a *gated feature*, not a dead one.

The validator at `0x08082E00` compares the last ten recorded key presses against ten hard-coded masks (newest first: `01 02 10 20 10 20 80 80 40 40`). There is **no code table and no generator**: every one of the ten comparisons is mandatory, so the accepted space is exactly one sequence out of 10¹⁰. A single-position deviation returns 0.

A second published code — "All Cards: beat every duelist 20 times, then at the title/selection menu press L, R, Select, A, B, Left, Right, Up, Down, Start" — was **not found** in this image under six mask encodings, and no second ring-reading validator exists (bounded negative, §6b). Every other published cheat is a GameShark/Action Replay/CodeBreaker RAM patch (out of scope).

Dynamic proof: with the key ring, gate bit, and menu-handler selector set in a savestate, pressing A invoked the game's own validator and produced the **actual credits roll** (screenshots `credits2.png`/`credits3.png`). With a one-position near-miss or the gate closed, credits did not appear.

## 3. How to reproduce

**Emulator**: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:317` + openbox, `mgba -3`. GBA viewport 240×160 at +154,+183 in the 1024×768 root.

**Keymap** (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Use 70–160 ms holds; shorter taps are dropped. Focus with `xdotool windowactivate --sync`.

**Screen walk (all screens reached with screenshots)**: language selection → "Push Start" title → New Game/Continue → "Got Basic Deck!" → main menu (Campaign / Edit Deck / Link Duel / Options) → Options screen (Card Trade / Language Selection) → campaign duel screen (Tea Gardner). No password/cheat entry UI exists on any of them.

**Observing the key ring**: after any key sequence, save a savestate (`Shift+F1`…`F9`); the `gbAs` PNG chunk decompresses to a 397,312-byte state with IWRAM `0x03000000` at raw `0x19000` and EWRAM `0x02000000` at raw `0x21000`. The ten most recent *edge-triggered* key masks are at raw `0x1904C + slot*2`, newest selected by `index>>5` from the halfword at raw `0x1904A`.

**Reproducing the dynamic proof** (script `patch_state.py` in work dir):
1. Reach the main menu, select Options, enter `↑↑↓↓←→←→B`, save state slot 2.
2. Patch that state: write the ten masks newest-first (`01 02 10 20 10 20 80 80 40 40`) into ring slots 17…8, index halfword `589` (`0x024D`), gate byte `0x02010015 = 0x05`, menu selector byte `0x030046D8 = 3`.
3. Load with F2 and press A. The credits roll starts (the handler calls `0x08082ED0(0x0808B4D5)`).
4. Variant with slot 17 = `0x02` (one-position near-miss) or gate byte `0x01` does **not** produce credits.

Caveat (guide §16.10): selector index 3 is a hidden table entry; normal UI navigation of the main menu selects index 2 (Options). Reaching the validator therefore required setting that byte in the savestate. Everything after that — the validator, gate test, and credits effect — is the game's own unmodified code.

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

| Address | File offset | Meaning |
|---|---|---|
| `0x08082D54` | `0x82D54` | **Key recorder** (`ldr r0,[pc]=0x04000130`; `mvns` → active-high; writes `pressed` to ring) |
| `0x08082E00` | `0x82E00` | **Button-code validator** — 10 inline `cmp r0,#mask` checks |
| `0x08082EB0` | `0x82EB0` | Literal `0x03000040` (input-state base) used by validator |
| `0x08082EB4` / `0x08082EB6` | `0x82EB4` | Failure return (`movs r0,#0`) / common `bx lr` |
| `0x08082EB8` | `0x82EB8` | Ring reset (clears 32 slots, ZLN index byte) |
| `0x08082ED0` | `0x82ED0` | Screen/task launcher called by the wrapper (`r0` = script pointer) |
| `0x08083140` | `0x83140` | Per-frame caller of recorder `0x08082D54` |
| `0x08083312` | `0x83312` | Caller of ring reset `0x08082EB8` |
| `0x080865B4` | `0x865B4` | **Wrapper**: gate test, validator call, effect dispatch |
| `0x08086668` | `0x86668` | Menu dispatcher reading selector at `0x030046D8` and table `0x08C501A8` |
| `0x08C501A8` | `0xC501A8` | 4-entry handler table: `08086275`, `0808635D`, `08086395`, `080865B5` (secret wrapper) |
| `0x0808B4D5` | `0x8B4D5` | Credits task/script pointer passed on success |
| `0x03000040` | — | IWRAM input-state base (held `+4`, pressed `+6`, last `+8`, index `+0x0A`, ring `+0x0C`) |
| `0x0300004A` | — | Ring index halfword; `>>5` selects newest slot |
| `0x0300004C` | — | Ring: 32 × u16 edge-triggered key masks |
| `0x02010015` | — | EWRAM gate byte; bit 2 (`0x04`) = credits-viewed |
| `0x030046D8` | — | Menu selector byte used by dispatcher `0x08086668` |

## 5. Algorithm

**Recording** (`0x08082D54`, derived from disassembly):
```c
uint16_t keys = ~(*(volatile uint16_t*)0x04000130);   // active-high in low 10 bits
uint16_t pressed = keys & ~state->held;                // edge-triggered
state->pressed = pressed;
state->held = keys;
if (keys != state->last) { state->ring_index_low = 0; state->last = keys; }
state->ring[state->index >> 5] = pressed;              // 32-slot ring, u16
state->index = advance(state->index);                  // low byte wraps with rollback at 20
```

**Validation** (`0x08082E00`, exact — each comparison is `cmp r0,#imm; bne fail`):
```c
int n = *(halfword*)0x0300004A >> 5;
uint16_t want[10] = {0x01,0x02,0x10,0x20,0x10,0x20,0x80,0x80,0x40,0x40}; // newest first
for (k = 0; k < 10; k++)
    if (*(halfword*)(0x0300004C + 2*((n-1-k) & 31)) != want[k]) return 0;
return 1;
```
Reading backwards, the oldest-first sequence is `0x40,0x40,0x80,0x80,0x20,0x10,0x20,0x10,0x02,0x01` = `↑ ↑ ↓ ↓ ← → ← → B A`.

**Wrapper/gate/effect** (`0x080865B4`):
```c
if (some_mode_check_0x08083A10(4) == 0) goto fallback;
if (!(*(uint8_t*)0x02010015 & 0x04)) goto fallback;   // credits-viewed gate
if (validate() != 0) start_task(0x0808B4D5);          // CREDITS
else                 start_task(/* fallback pointer */);
```

## 6. Tables

**Button masks** (active-high `~KEYINPUT & 0x3FF`, stored as u16):

| Mask | Button |
|---:|---|
| `0x001` | A |
| `0x002` | B |
| `0x004` | Select |
| `0x008` | Start |
| `0x010` | Right |
| `0x020` | Left |
| `0x040` | Up |
| `0x080` | Down |
| `0x100` | R |
| `0x200` | L |

**Accepted button code** (oldest → newest): `Up, Up, Down, Down, Left, Right, Left, Right, B, A`.

**Handler table `0x08C501A8`**: index 0 `0x08086275`, 1 `0x0808635D`, 2 `0x08086395`, 3 `0x080865B5` (hidden credits-code wrapper), followed by `0x00000000`.

**Published-code verification**: 3rd party cheat indexes/3rd party cheat index list the All Cards sequence and the credits sequence; only the credits sequence exists in this ROM. 3rd party cheat indexes/3rd party cheat index codes are all cheat-device RAM patches (e.g. `12050016 00000303` "Have All Cards"), explicitly out of scope. One fetched 3rd party cheat index FAQ stated "Passwords are gone!" — corroborated by the complete absence of a password UI or table.

## 6b. Enumeration

**Space definition**: 10 positions × 10 buttons = **10¹⁰ = 10,000,000,000** press sequences. The ring stores 32 slots; the validator examines a fixed 10-slot window. There is no alphabet, checksum, key table, generator, or lookup table — the ten expected masks are inline immediates.

**Complete characterisation**: the accepted set is exactly **one** sequence, the Konami code. This is proven structurally: at `0x08082E18, 0x08082E28, …, 0x08082EA8` each of the ten `cmp r0,#mask` instructions branches to `0x08082EB4` (`return 0`) on any mismatch, and there is no alternate accepting branch. Only the all-ten-match path reaches `0x08082EAA` (`return 1`). This is a *bounded negative for novel codes*: with a single hard-coded sequence and no generator, no code absent from the published list can exist. (Guide §0.2's "mint a novel code" is inapplicable to a fixed-sequence system; the equivalent deliverable — enumerate every action branch and press an undocumented combination — is satisfied: there is one branch and no undocumented accepted combination.)

**Accepted code confirmed in-game** (published anchor, used to validate the decoder):

| Code | Effect | Evidence |
|---|---|---|
| `↑↑↓↓←→←→BA` | staff credits roll | `credits2.png`, `credits3.png` (Observed, with selector/gate set via savestate as described in §3) |

**RAM evidence**: savestate with the nine-press prefix showed the ring (`game.ss2.orig`) at raw `0x19058`…`0x19066` = `0x0200,0x0100,0x0004,0x0002,0x0020,0x0010,0x0040,0x0080` for my `L,R,Select,B,←,→,↑,↓` probe, and index halfword `589` (`0x024D`) at raw `0x1904A` — i.e. the recorder really stores active-high masks in u16 slots exactly as the validator expects. With the full patched sequence the ring at slots 8…17 read `40 40 80 80 20 10 20 10 02 01`.

**Bounds proven by rejection**:

| Test | Why it must fail | Observed |
|---|---|---|
| newest mask `0x02` instead of `0x01` (A→B near-miss), gate open, selector 3 | first inline `cmp r0,#1` at `0x08082E16` fails → `return 0` | no credits (`rej_nearmiss.png` / `rej_nearmiss2.png`) |
| gate byte `0x02010015 = 0x01` (bit 2 clear), correct ring, selector 3 | wrapper's `ands r0,#4; cmp r0,#0; beq fallback` at `0x08086610-16` skips validator | no credits (`rej_gate.png`) |
| any of the other 10¹⁰−1 sequences | at least one of ten mandatory `cmp` instructions mismatches | rejected by construction (Derived) |

**Second published code — bounded negative ("All Cards")**: the sequence `L,R,Select,A,B,Left,Right,Up,Down,Start` was searched as u16 LE/BE, u32 LE/BE, one-byte-per-press, and 4-bit button indices, in forward and reverse order (20 encodings, whole 16 MiB): **0 hits**. A ROM-wide scan for the validator's comparison-loop signature (`lsrs rX,rY,#21; adds #imm; ands #31; lsls #1; ldrh [base]; cmp #mask; bne`) found **exactly one** validator (`0x08082E00`, the Konami code). Masks `0x100`/`0x200` cannot even be expressed by the inline `cmp r0,#imm8` form used here, so a second validator of this design would require a different structure — none was found. Verdict: this code is either from a different revision or unimplemented in `BYWE`; no reachable Accept path for it exists in this image.

**Other surfaces enumerated**: whole-ROM case-insensitive search for `password`, `cheat`, `secret`, `debug`, `test mode`, `sound test`, `level select`, `invalid` returned only TCG card names (*Book of Secret Arts*, *Sectarian of Secrets*, *Goblin's Secret Remedy*, *The Portrait's Secret*), dialogue, and a debug-format string `Invalid MRK:%4d` at `0x8F6CE4`; none is a cheat UI. All reachable screens were walked (§3) — none contains a code entry field.

## 7. Validation evidence

Labels per guide §8.4.

- **Observed** (emulator/savestate): every screen in §3; recorder writing the exact key masks into the IWRAM ring (savestate reads); gate byte `0x01` fresh vs `0x05` patched; "complete 9.2 %" display appearing with gate patched; credits roll after code acceptance; no credits on near-miss or closed gate.
- **Derived** (disassembly): recorder `0x08082D54`; validator `0x08082E00` with all ten mask comparisons and their failure branches; wrapper `0x080865B4` with gate and effect; dispatcher `0x08086668` and handler table `0x08C501A8`; BCD/password absence.
- **Inferred**: that gate bit `0x04` is specifically "credits viewed" (from the published code's precondition plus the observed fresh value `0x01` and successful `0x05`); that selector index 3 is a hidden menu entry (table entry exists, but normal UI navigation selected index 2). The exact writer of the `0x04` gate bit was not isolated.
- GDB stub (`mgba -g`) was tried but proved unreliable for this target: PC manipulation stepped two Thumb instructions at once and detach killed the core (guide §16.2/§16.13). All RAM evidence therefore comes from decompressed `gbAs` savestate chunks.

## 8. Unknowns

- The normal in-game way to reach menu-handler index 3 (and thus the validator on a retail save) was not isolated — the dynamic proof set that selector byte in a savestate. If the UI cannot reach index 3 at all, the code is additionally gated by an unreachable selector.
- The routine that sets gate bit `0x04` after credits were viewed was not isolated; only its effect on the wrapper was tested.
- Whether the published "All Cards" code belongs to a different ROM revision (the `BYWE` code differs from the sibling `AYWE`/`A2YE` images) was not established.
- The fallback screen pointer used on validator failure (`0x020234F0` read from the wrapper's literal region) was not followed.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo` — Phase 0/1.
- Python 3 (stdlib `struct`, `zlib`, `re`, `bytearray`) — mask-sequence scans (20 encodings), pointer/literal scans, Thumb BL scanner, savestate `gbAs` parser/patcher (`patch_state.py`).
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` — all disassembly.
- mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`, XTEST input helper (`key.py`), `scrot` — screen walk, RAM evidence, credits proof.
- `gdb-multiarch` with mGBA's `-g` stub — attempted as an oracle (guide §16.19); abandoned due to stub unreliability (recorded in §7).
- Web recon treated strictly as data: 3rd party cheat indexes (cheats + General FAQ "Passwords are gone!"), 3rd party cheat indexes Guides. No instructions found in fetched content were followed.
- All screenshots, savestates, and scripts were kept in `/tmp/yugiohwct2004/`; none were written into the ROM folder. No ROM or copyrighted assets are reproduced here.
