# Mortal Kombat: Deadly Alliance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mortal Kombat: Deadly Alliance/Mortal Kombat: Deadly Alliance.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `MKALLIANCE` |
| Game code | `AXDE`, maker `5D`, version `0x00` |
| `file` id | Game Boy Advance ROM image: "MKALLIANCE" (AXDE5D, Rev.00) |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` (no cracktro patch) |
| Header checksum | `0x0000` (normal rebuilt-header artifact); complement byte `0xE5` (differs from computed `0xFE` — noted, not investigated further) |
| MD5 | `78e7ff46ee220f8b6cff4a73c0439eb4` |
| SHA-1 | `247e0e8d10b5be574fc800131c273fa8a52eb25f` |
| SHA-256 | `7cd9b2d968e4746c35e19807bdffec2dc0ad363698fc1f93b9a20cdc79e53d84` |
| Embedded headers | exactly one Nintendo logo at file `0x00000004` → single retail image, **no trainer, no multiboot/2-in-1 shell** |

## 2. Executive summary

The game contains a **developer-intended cheat system in the profile-name field**: creating a profile with one of **seven hard-coded 8-character names** grants koins or unlocks Krypt tombs. The validator is a single Thumb function at `0x0803DE64–0x0803E282` that compares the eight name bytes against seven strings using interleaved `ldrb`/`cmp` immediates — which is why a plain `grep` for `KWIKKASH` in the ROM finds nothing.

**Published code verified:** `KWIKKASH` → 25,000 koins (GameFAQs).

**Six unpublished codes found and characterised** (§0.2): `SOULNADO`, `COLORAMA`, `DRGNARMY`, `MINIPOWR`, `TRVLLR` and `A PORTAL`. Five were accepted on the real in-game entry screen with visible/RAM proof; `A PORTAL` exists in the validator but is **unreachable through the on-screen keyboard** (it contains a space, and the keyboard has only A–Z, 0–9, backspace, END). `TRVLLR` is a 7-byte comparison whose 7th byte is `0x0A`: entering the six letters and pressing END supplies `0x0A` padding, so it *is* reachable.

No hidden debug menu, no button-code sequence, and no second password screen were found after walking every reachable screen. Unlockables not obtained by name codes are ordinary save-bit Krypt purchases / Arcade-mode objectives (guide §16.18 category), not a code system.

## 3. How to reproduce

* Emulator: mGBA (SDL, `-3`), `SDL_AUDIODRIVER=dummy`, Xvfb `:315` + openbox.
* Keymap used: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Hold ~0.15–0.30 s (short taps are dropped by the menu).
* Path: boot → language select (A on ENGLISH) → title (Start) → **CREATE PROFILE** → on-screen keyboard → type name → move to **END** → A → the VIEW PROFILE screen shows `KOINS` and `UNLOCKED: n%`.
* Codes typed exactly as listed in §6 (uppercase; for `TRVLLR` type only the six letters and press END).
* Published code tested: `KWIKKASH`. Near-miss rejection tested: `SOULNADZ`.
* The profile save is `Mortal Kombat: Deadly Alliance.sav` in the ROM folder; the name is stored **byte-reversed** (e.g. `KWIKKASH` → bytes `48 53 41 4b 4b 49 57 4b` = `HSAKKIWK`).
* Only two profile slots are kept in the save (stride `0x38`); creating further profiles overwrites the older slot.

## 4. Address map

| Item | Address / offset | Notes |
|---|---|---|
| Name-code validator (Thumb) | `0x0803DE64` – `0x0803E282` | 7 chained 8-byte literal comparisons; entry from profile-create flow |
| `KWIKKASH` koin store | `0x0803E1C0`–`0x0803E1C2` | `ldr r1,[pc,#20] @ 0x0803E1D8` (literal `0x000061A8` = 25000), `str r1,[r0,#0x0C]` |
| Unlock-bit setter | `0x0804FCEC` | `ID>>4` selects u16 word at profile+`0x26`; `1<<(ID&0xF)` sets the bit |
| Message / announcement | `0x080570C8` | called with small message IDs (2, 5, 8, 10, 12, 13, 107) |
| Delay/effect helper | `0x08003EA0` | called 90/91 times after koin and message codes |
| Current profile index (byte) | `0x0300226C` | literal at `0x0803DEC8` |
| Profile base pointer | `0x030021C0` | literal at `0x0803DECC`; record stride `0x38` (56) bytes |
| Profile fields in RAM | `+0x00` name[8]; `+0x0C` koins (u32); `+0x26` unlock bits u16[8] | from validator and setter disassembly |
| Reward-name strings | `0x002DB1D3` – `0x002DB9F0` | ASCII costume/arena/reward names (`ANIME JAX` … `ARENA: SPY FACILITY`) |
| Save (SRAM) | file offset `0x00`/`0x38`/`0x70` | profile slots; name at +0 reversed, koins at +`0x0A`, unlock bits in the +`0x20` region |

File offset → ROM address: `0x08000000 + file_offset`.

## 5. Algorithm

Pseudocode of `0x0803DE64` (all comparisons are on bytes of the 8-byte name buffer):

```
idx = byte[0x0300226C]
base = ptr[0x030021C0] + idx * 56
name = base + 0                      # 8 bytes, filled with 0x0A when shorter

if name == "COLORAMA":  for w in 0..5: u16[base+0x26 + 2*w] |= 0xFFFF; msg(10)
elif name == "DRGNARMY": for id in [0x67,0x68,0x69,0x6A,0x6B]: unlock(id); msg(13)
elif name == "SOULNADO": for w in 0..7: u16[base+0x26 + 2*w] |= 0xFFFF; msg(5)
elif name == "MINIPOWR": for id in [0x64,0x65]: unlock(id); msg(8)
elif name[0..6] == "TRVLLR\x0A": for id in [0x66,0x74,0x75,0x76,0x77]: unlock(id); msg(2)
elif name == "A PORTAL": for id in [0x60,0x61,0x62,0x63]: unlock(id); msg(12)
elif name == "KWIKKASH": u32[base+0x0C] = 25000; msg(107); delay(90)
else: fall through to the normal profile-save path

unlock(id): u16[base+0x26 + 2*(id>>4)] |= 1 << (id & 0xF)
```

`TRVLLR` is a 7-byte prefix; byte 7 is not compared. The name-entry keyboard pads unused bytes with `0x0A`, which is exactly the 7th compared byte — so a six-letter name reaches that branch.

The 120 Krypt tombs are indexed `0..119`, labelled `AA..AO, BA..BO, … HA..HO` in the published GBA Krypt FAQ; the ROM's reward-name table at `0x2DB1D3` agrees with those labels. Tomb `AA` = id 0, `HO` = id 119.

## 6. Tables

### 6a. The seven name codes

| Name (exact bytes) | Compared bytes | Effect | In-game `UNLOCKED` observed | Published? |
|---|---|---|---|---|
| `KWIKKASH` | 8 | `koins = 25000` | 0% | **Yes** (GameFAQs) |
| `SOULNADO` | 8 | unlock ids 0–127 → all 120 tombs | **100%** | No |
| `COLORAMA` | 8 | unlock ids 0–95 → tombs `AA`–`GO` | **80%** (96/120) | No |
| `DRGNARMY` | 8 | ids `GN,GO,HA,HB,HC` | 4% (5/120) | No |
| `MINIPOWR` | 8 | ids `GK,GL` | 1% (2/120) | No |
| `TRVLLR` + `0x0A` padding | 7 | ids `GM,HL,HM,HN,HO` | 4% (5/120) | No |
| `A PORTAL` | 8 | ids `GG,GH,GI,GJ` | not entered (UI has no space) | No |

Reward decoding for the ids (from the GBA Krypt FAQ, cross-checked against the ROM name table):

* `A PORTAL` → GG Anime Kenshi, GH Captain Sub-Zero, GI Goth Sub-Zero, GJ Alien Quan Chi.
* `MINIPOWR` → GK Goth Kano, GL Black Jax.
* `TRVLLR` → GM Kung Pao Kung Lao, HL Classic Sonya, HM Disco King Kano, HN Reaper Sub-Zero, HO Tart Kitana.
* `DRGNARMY` → GN Reaper Kung Lao, GO Parliament Shang Tsung, HA Celsius Scorpion, HB Krazy Kredits, HC Wild West Kung Lao.
* `COLORAMA` → tombs AA–GO (96 costumes/items). `SOULNADO` → all 120 (the extra 8 bits are harmless).

Normal unlockables (not name codes): Kano/Kitana/Sub-Zero via Arcade-mode clears, Quan Chi/Shang Tsung via Krypt tombs `AI`/`FF`, plus the documented Select-on-fighter biography screen. Console-version unlock procedures do **not** apply to this SKU; no console code literal was found in the ROM.

## 6b. Enumeration

* **Space definition:** the input is exactly 8 bytes of profile name. UI alphabet is A–Z and 0–9; short names are right-padded with `0x0A`. The validator is an exact byte comparison (no checksum, no arithmetic), so the representable UI space is `36^8 ≈ 2.82 × 10^12` names and the accepted set is **exactly 7** of them (6 UI-reachable, 1 UI-unreachable because it contains a space). There are no partial matches, aliases, or unused payload bits. The `TRVLLR` branch compares only 7 bytes, but because byte 7 must be the `0x0A` pad, only one UI spelling reaches it.
* **Full enumeration method:** disassembled `0x0803DE64–0x0803E282` and parsed every `ldrb r1,[r0,#i]` / `cmp r1,#imm` pair into the table above; there are exactly seven `bne` failure chains and no other name comparisons in the function. The function's fall-through at `0x0803E1E8` handles the normal save path.
* **Novel codes minted and confirmed in-game (absent from GameFAQs, VGChartz, TCRF and the three archived GameFAQs guides checked):**
  * `SOULNADO` — screenshot: profile SOULNADO shows `KOINS: 0`, `UNLOCKED: 100%`. Save-RAM diff (profile 1 base `0x38`) shows sixteen bytes `0x58–0x67` and `0x6A–0x6F` changing from `00` to `FF`, i.e. the eight u16 unlock words the disassembly sets.
  * `TRVLLR` — screenshot: profile TRVLLR shows `UNLOCKED: 4%`. Save-RAM shows name bytes `0a 0a 52 4c 4c 56 52 54` (reversed `TRVLLR\n\n`), proving the `0x0A` pad that satisfies the 7-byte comparison.
  * `COLORAMA` — 80%; `DRGNARMY` — 4%; `MINIPOWR` — 1% (all screens captured).
* **Bounds proven by rejection:** `SOULNADZ` (one character changed) produced `KOINS: 0`, `UNLOCKED: 0%` on the real entry screen. This proves exact 8-byte matching. Pressing BUY on a 450-koin tomb with 0 koins also had no effect. `A PORTAL` is present in the validator but the on-screen keyboard has no space cell (rows: A–M, N–Z, 0–9, `PC` backspace, `END`; L/R/Select do not insert a space), so it cannot be entered through the game UI — a dead code path, not a usable cheat.

## 7. Validation evidence

* **Observed (emulator):** KWIKKASH → 25000 koins; SOULNADO → 100%; COLORAMA → 80%; DRGNARMY → 4%; MINIPOWR → 1%; TRVLLR → 4%; SOULNADZ → 0% / 0 koins. All on the VIEW PROFILE screen after entering the name through the in-game keyboard.
* **Observed (save RAM):** byte-reversed names at SRAM `0x00`/`0x38`/`0x70`, koin bytes `61 a8` at `0x0A` for KWIKKASH, `FF` unlock words for SOULNADO, `0x0A` padding for TRVLLR.
* **Derived (disassembly):** the seven comparisons, the `0x61A8` literal at `0x0803E1D8`, the bit-setting formula at `0x0804FCEC`, and the profile/globals addresses.
* **Inferred (labelled):** the tomb names mapped to each numeric id come from the published GBA Krypt FAQ cross-checked against the ROM's reward-string table; individual tomb-opening animations were not played for each code. The `0x080570C8` message IDs were not tied to specific on-screen text.
* **GDB note:** the mGBA GDB stub listened on port 2345 but never completed a handshake (connection timed out; the emulator subsequently exited). RAM evidence therefore uses the guide's §16.13 save-RAM diff fallback rather than a debugger read.

## 8. Unknowns

* Whether `A PORTAL` could ever be produced by a non-UI path (e.g. a link-transfer save with a space byte) — not explored; UI entry is impossible.
* Exact on-screen text produced by the per-code message IDs at `0x080570C8` (audio was stubbed with `SDL_AUDIODRIVER=dummy`).
* Header complement byte `0xE5` does not match the computed `0xFE`; no functional effect was observed, cause unknown.
* No button-code table was positively identified. A generic u16 key-mask scan returned hundreds of candidates in compressed move data and none that disassembled as a pause/title cheat matcher; no hidden debug screen was reached on any walked menu.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for validator/helper disassembly; a short Python regex parser to extract the compared name bytes from the objdump text.
* Python for hashes/header parse, embedded-logo scan, literal/transformation searches, key-mask scan and save-RAM diffs.
* mGBA SDL (`-3`) under Xvfb `:315` with openbox; `xdotool` (XTEST) input helpers `key.sh`, `nav2.py`, `create_profile.py`; `scrot` + ImageMagick crop/zoom; up to 20 screenshots retained on disk in `/tmp/opencode/mkdeadly`.
* `gdb-multiarch` attempted (stub failure described above). `capstone 5.0.7` available but not required.
* Web: archived GameFAQs cheats page and guides 20278 / 26184 / 29005 for game 551910 (fetched as data; no prompt-injection content encountered). All published literals were verified against the ROM: `KWIKKASH` appears only as the interleaved `cmp` immediates at `0x0803E17E+`, not as a contiguous ASCII string.

No ROM or copyrighted game assets are redistributed by this report.
