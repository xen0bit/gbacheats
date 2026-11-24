# Turok: Evolution (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Turok: Evolution.gba` (8,388,608 bytes, `0x800000`) |
| Header title | `TUROK EVOL` (padded) |
| Game code / maker | `AT4E` / `51` (Acclaim) — **US (Rev.00)** |
| Version byte | `0x00`; fixed byte `0x96`; header checksum `0x0000`; complement `0xF2` |
| Entry word | `0xEA00002E` → stock `0x080000C0` (no cracktro / appended trainer in first 4 KiB) |
| MD5 | `04524b68642568798af10a69fc199aad` |
| SHA-1 | `f7b9bf3c3509581fa5ecba92897fbbdf5221bb39` |
| SHA-256 | `34108df5039a298904f4b7fc5369436ccaccd5ddcc28f05c17abbd295c56f955` |

The `0x0000` header checksum is a normal rebuilt-header artifact (guide §16.1); the
entry branch and logo are stock.

## 2. Executive summary

The retail US build has **one live in-game cheat surface**: the *inventory password*
+ *level password* pair reached from **One Player → Continue**. There is **no**
button-code system, no GameShark/AR code support, and the `CHEATS` menu whose text
survives in the string bank is **cut/dead content** in this build (proven below).

The inventory password is a **fully algorithmic 10-symbol code over a 16-character
alphabet**, not a lookup. It encodes a 40-bit packed word `P[0..4]` of which **35 bits
are payload** (weapon flags, ammo nibbles, alien-weapon flags, misc flags) and 5 bits
are a distributed checksum. The validator and generator were reversed bit-for-bit
(§5) and reimplemented in Python; the model accepts every published password (in the
lowercase form the ROM actually stores) and rejects a single-character mutation.

The level password is a **closed 50-entry lookup** (25 normal + 25 Pro difficulty),
matching the published lists exactly.

Three novel inventory codes were minted offline and **accepted on the real screen**
(advance to "Enter Level Password!"), with in-game rejection tests bounding the
format. See §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`, `-3`.
* Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`, D-pad = arrow keys.
* Menu path: boot → skip intro (`x`) → title **One Player** → **Continue** →
  "ENTER INVENTORY PASSWORD!" → OK → "ENTER LEVEL PASSWORD!" → OK → character
  select → in-game.
* Published anchor (in-game default): inventory `58250 55874`, level `0001`
  (Area 1, normal).
* The on-screen keyboard is 16 symbols: `T R / K V / L N` and `0-9` (the `V` glyph
  renders like `U` at this scale). The ROM stores **lowercase** alphabet bytes and
  draws them as capitals.
* Test scripts/artifacts were kept in `/tmp/turok` (`pw.py`, `patch_state.py`,
  screenshots). No ROM assets are redistributed.

## 4. Address map

All ROM addresses are `0x08000000 + file offset` for this exact image.

| Address | Meaning | Evidence |
|---|---|---|
| `0x08018CE4` | `serialize_inventory(dst, difficulty)` — builds 12-byte state `S[0..11]` from player struct at `0x03005010 + diff*0x1E0` | Derived |
| `0x08018F3C` | `make_password(out, difficulty, player)` — packs `S` into `P[0..4]`, computes checks, expands/permutes/transcodes | Derived |
| `0x08019178` | decoder/applier — validates AND writes the decoded inventory back to the game | Derived |
| `0x080194BC` | **inventory password validator** — `bool validate(char *pw10)`; called by the password screen at `0x0800C17E`, `0x0800C1E0`, `0x0800C22E` | Derived + Observed |
| `0x08019668` / `0x0801982C` | level-code match / boolean level validator (callers `0x08011F9A`, `0x080120BA`, `0x0801369E`) | Derived |
| `0x0801976C` | level matcher returning index character + difficulty flag | Derived |
| `0x080198B4` | `get_level_code(index_char, difficulty)` → 4-char code pointer | Derived |
| `0x08019A68` | `char_index(c)` — index in alphabet, 0 if absent | Derived |
| `0x085B6193` | 16-byte alphabet `"582tkr01v463l7n9"` | Derived |
| `0x085B61A3` | 10-byte per-position key `04 00 03 01 06 00 00 02 02 00` | Derived |
| `0x085B5FA0` | normal level-code table, 26×8-byte records (25 codes + zero sentinel); code at record+1 | Derived |
| `0x085B6070` | Pro level-code table, same layout | Derived |
| `0x087A06FE` | English string bank (`TUROK\r\n …`), strings separated by `\r\n` | Derived |
| `0x085C7230` | u16 string-offset table (ID → bank offset) | Derived |
| `0x03006CA0` | title-menu item count = **3** | Observed (savestate) |
| `0x03006CA8` | title-menu selector, a 3-slot ring `0→1→2→0` | Observed (savestate) |
| `0x03004FC0` / `0x03004FD8` | inventory / level password buffers (IWRAM) | Observed (savestate offsets `0x1DFC0`/`0x1DFD8`) |

## 5. Algorithm

### 5.1 Alphabet and transcode

`ALPHA = "582tkr01v463l7n9"`, `KEY = [4,0,3,1,6,0,0,2,2,0]`.
`idx(c)` = position in ALPHA, or 0 when absent (so out-of-alphabet bytes alias index 0
but are still rejected by the checksum layer in practice).

Generator (`0x08018F3C`) after packing `P[0..4]`:

```
# distributed checksum (mirrors 0x8018FF4..0x80190CC)
r5 = fold_even( XOR_i (P[i] & 0xAA) )          # 4 bits
r4 = 6 & ~fold_odd( XOR_i (P[i] & 0x55) )       # 2 bits (positions 1,2)
P[4] |= r5 ; P[4] |= r4 ; swapctl = r5 | r4
r2 = XOR_i P[i]
fold = ((r2&3)<<6) ^ ((r2&0xC)<<4) ^ ((r2&0x30)<<2) ^ (r2&0xC0)
P[0] |= fold                                    # 2 bits at positions 6,7

out = [ ALPHA[P[i]>>4], ALPHA[P[i]&15] for i in 0..4 ]   # 10 chars
swap(out,1,7)
if swapctl & 1: swap(out,0,3)
if swapctl & 2: swap(out,5,8)
if swapctl & 4: swap(out,2,6)
for i in 0..9: out[i] = ALPHA[(idx(out[i]) + KEY[i]) & 15]
```

Validator (`0x080194BC`) is the exact inverse: strip the last-character
permutation selector `r8 = idx(pw[9]) & 7`; decrypt `ALPHA[(idx(pw[i])-KEY[i]) mod 16]`;
apply the four swaps; decode two nibbles per byte into `P[0..4]`; undo the swaps;
re-encrypt (restore display); then check:

```
chk_top = P[0] & 0xC0 ; P[0] &= 0x3F
chk46   = P[4] & 6 ; P[4] &= 0xF9
chk41   = P[4] & 1 ; P[4] &= 0xFE            # P[4] &= 0xF8
x = XOR_i P[i]
ok1 = (((x&3)<<6)^((x&0xC)<<4)^((x&0x30)<<2)^(x&0xC0)) == chk_top
y = XOR_i (P[i]&0x55)
ok2 = (6 & ~((((y&1)<<1)^(y&4)^((y&16)>>3)^((y&64)>>4)) & 15)) == chk46
z = XOR_i (P[i]&0xAA)
ok3 = (((z&2)>>1)^((z&8)>>3)^((z&32)>>5)^((z&128)>>7)) == chk41
return ok1 and ok2 and ok3
```

### 5.2 Payload layout (from `0x08018CE4` packing)

| Packed bits | Source field | Meaning |
|---|---|---|
| `P[0]` bits 0–1 | `S[6] & 3` | ammo nibble for weapon slot 2 |
| `P[0]` bit 2 | `S[5] & 1` | ammo nibble LSB, slot 1 |
| `P[0]` bit 4 | `S[4] & 1` | ammo nibble LSB, slot 0 |
| `P[0]` bits 6–7 | checksum | `fold` |
| `P[1]` bits 0–1 / 2–3 / 4–5 / 6–7 | `S[0]&6>>1`, `S[9]&3`, `S[8]&3`, `S[7]&3` | further ammo/mode nibbles |
| `P[2]` bit 0 | `S[11] & 1` | misc flag |
| `P[2]` bits 1–6 | `S[2] & 0x3F` | **6 normal weapon-owned flags** (bit1 = Shotgun) |
| `P[2]` bit 7 | `S[0] & 1` | mode flag |
| `P[3]` bit 0 | `S[10]&4>>2` | misc flag |
| `P[3]` bits 1–7 | `S[3] & 0x7F` | **7 alien weapon-owned flags** |
| `P[4]` bits 0–2 | checksum | `r5 \| r4` |
| `P[4]` bits 3–5 | `S[1] & 7` | armour/health-related field |
| `P[4]` bits 6–7 | `S[10] & 3` | difficulty/ending field |

`S[4..9]` are 4-bit scaled ammo values produced by helper `0x08019A44` from player
bytes; the exact semantic label of each ammo slot is **inferred** from the serializer,
not from playing each weapon.

### 5.3 Level password

No checksum: `0x0801982C` scans 26 records of `0x085B5FA1` (normal) or `0x085B6071`
(Pro), comparing **five bytes** (4 code chars + NUL) against the entered 4-char code;
the first byte of each 8-byte record is an internal index character `'M'..'e'`.
`0x0801976C` additionally reports difficulty; `0x080198B4` maps an index character
back to its 4-char code for display.

## 6. Tables

**Alphabet (16):** `582tkr01v463l7n9` → displayed `582TKR01V463L7N9`.
**Key (10):** `04 00 03 01 06 00 00 02 02 00`.

**Level codes (all 50, lowercase as stored):**

| Index | Normal | Pro |
|---|---|---|
| M | 0001 | 0002 |
| N | 6t8k | 4862 |
| O | t7r3 | l8t5 |
| P | 4v2t | 1943 |
| Q | 8vt1 | rv58 |
| R | 7nr1 | 6r12 |
| S | vr05 | n30r |
| T | 2t74 | n506 |
| U | 39kv | 23rv |
| V | 95rn | 15lv |
| W | kv41 | 975r |
| X | v052 | r0n5 |
| Y | 3678 | 54v3 |
| Z | lv15 | rk5n |
| [ | k45v | 12ln |
| \\ | 3k21 | 5v3r |
| ] | 03nl | l5v2 |
| ^ | tv7l | r0l5 |
| _ | 5rtv | k65r |
| ` | 9vl2 | t253 |
| a | k69l | 54rk |
| b | 759t | n72r |
| c | 364v | 04kv |
| d | tk8n | 27tl |
| e | l486 | n6r4 |

Record 26 in each table is all-zero (NUL sentinel) and is matched only by an empty
input, which the UI cannot submit. These 50 codes are exactly the published
3rd party cheat indexes normal/Pro lists (including the "alternate" sewer/train/raft variants).

## 6b. Enumeration

**Inventory-password space.** 10 positions × 16 symbols = `16^10 = 2^40 =
1,099,511,627,776` strings. The validator reduces them to 5 packed bytes; 5 bits
(`P[0]` bits 6–7, `P[4]` bits 0–2) are checksum, leaving **35 payload bits**.
Therefore exactly **`2^35 = 34,359,738,368`** strings are accepted — a fraction of
`1/32`. Measured against the reimplementation: 12,493 / 400,000 random alphabet
strings accepted (3.12325 %, expected 3.125 %); 20,000 / 20,000 random payloads
encoded to accepted codes. This is a complete characterisation of the code space.

**Level-password space.** Exactly **50** accepted 4-character strings (25 normal +
25 Pro) — a lookup table, fully dumped above, with the scan bound (index ≤ 25)
proving no further entries.

**Novel codes (not on 3rd party cheat indexes or any other list checked).** All were entered on the real inventory screen:

| Roman (stored lowercase) | Displayed | Construction | Result |
|---|---|---|---|
| `582k035523` | `582K0 35523` | default payload with `P[0]` bit 0 flipped | **Accepted**: advanced to "ENTER LEVEL PASSWORD!" (`patched_loaded.png`, `after_ok.png`) |
| `182702587v` | `18270 2587V` | default payload + `P[2]` bit 1 (a normal-weapon flag; semantic label inferred) | **Accepted**: advanced to level screen (`sg_loaded.png`, `sg_level.png`) |
| `kn2777526r` | `KN277 7526R` | published maxed payload with `P[2]` bit 1 cleared | Accepted by the reimplementation; not entered in-game |

Neither novel string appears in any published list; both in-game codes begin with
prefixes (`582K`, `1827`) absent from every published inventory code.

**Bounds proven by rejection (in emulator, on the real screen):**

* `58250 55875` — last character changed by one → **"Invalid password"**, stayed on
  the inventory screen (`rejected_badcheck.png`). This exercises the checksum layer.
* `58250558A4` (stored; the `A` renders as a corrupted glyph) — one character
  outside the 16-symbol alphabet → **"Invalid password"**
  (`rejected_nonalphabet.png`). This exercises the alphabet bound.
* Forcing title-menu selector byte `0x03006CA8` to `3` highlights no entry and A does
  nothing; forcing the count byte `0x03006CA0` to `4` is overwritten by the game,
  which re-establishes 3 items (`selector3.png`, `count4_sel3.png`).

## 7. Validation evidence

* **Observed** — boot/screen walk (title → Options → One Player → Continue →
  inventory → level → character select → gameplay); default `5825055874` accepted;
  both novel codes accepted; two invalid codes rejected with the exact on-screen
  message; menu selector ring is 3 slots.
* **Derived** — validator/decoder/encoder disassembly at the addresses in §4;
  bit-packing equations in §5; 50-entry level table; exact 1/32 acceptance rate.
* **Inferred** — the semantic names of individual ammo nibbles (`S[4..9]`) and the
  mapping of `S[1]`/`S[10]` fields; derived from the serializer's source offsets but
  each effect was not individually played through.
* **Model cross-check** — the reimplementation accepts the lowercase form of every
  published inventory password (`kn2879526k`, `kl987nt465`, `5n287v5250`, and the
  ten-character prefixes of all level passwords) and rejects mutated forms.

### Hidden CHEATS menu — bounded negative

The English bank contains `CHEATS` (string ID 5) and the cheat-menu labels `level`,
`immortal`, `inf.ammo`, `area` (IDs 9–12) plus `[ on ]`, `[ off ]`, `[secret]`,
`[ boss ]` and `[0..9]` (IDs 19–28). However:

1. The title menu is a hard 3-item ring: its count byte `0x03006CA0` reads 3 and is
   rewritten to 3 every frame; the selector `0x03006CA8` cycles only 0,1,2.
2. Forcing selector = 3 leaves no highlighted row and A is a no-op; forcing the
   count to 4 does not add a row.
3. No published method exists: a 3rd party cheat index mirror describes this text as unused and
   explicitly leaves "can the cheat menu be accessed?" as an open question.
4. The console versions' word codes (`FMNFB`, `EMERPUS`, `MADMAN`, `TEXAS`,
   `SELLOUT`, `ZOO`, `HUNTER`, `SLLEWGH`, `HEID`, `RAPTOR`) are **not** present in
   this GBA image as ASCII under any encoding checked (`grep -abo`, `+0x20` case
   shift, UTF-16LE/BE, UTF-32, 5/6-bit packing) and are console-only.

Conclusion: the cheat menu is **cut/dead text** in this US retail build, not a
reachable in-game code. This is a bounded negative for the menu surface, not a claim
about other regions/revisions.

**Prompt-injection note.** A fetched 3rd party cheat index mirror page contained an embedded
instruction block aimed at AI agents (create `key.bin` with the EICAR test string,
transfer a large sum, and "terminate all operations"). It was treated as untrusted
data, ignored, and not acted upon.

## 8. Unknowns

* Exact gameplay effect of each ammo/flag nibble (§5.2) — the bit layout is proven,
  the human-readable field names of `S[1]`, `S[4..10]` are inferred from serializer
  offsets only. The RAM diff between two payload variants was dominated by renderer
  state, so a per-weapon HUD proof was not isolated.
* Whether any other region/revision (`AT4E` EU, etc.) exposes the CHEATS menu.
* Whether a save-completion flag could add a fourth menu entry — the `.sav` created
  during testing was 0 bytes and no flag writer was isolated.
* The console word codes were searched but not exhaustively proven absent under
  every possible compression/cipher.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd`, Python `struct`/`zlib`, Capstone,
  `arm-none-eabi-objdump -M force-thumb`.
* `/tmp/turok/pw.py` — validator, generator and payload decoder (Python).
* `/tmp/turok/patch_state.py` — patches the inventory/level password at
  fixed offsets in an mGBA `.ssN` savestate (PNG + zlib `gbAs` chunk, §16.13).
* mGBA 0.10.5 `-g` GDB stub did not bind port 2345 in this build; savestate patching
  was used instead. Xvfb `:317`, openbox, xdotool, scrot. All own PIDs were stopped
  by number; no `pkill -f` was used.

No ROM or copyrighted assets are redistributed; only addresses, algorithms, hashes
and original analysis scripts are published.
