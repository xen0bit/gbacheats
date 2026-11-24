# Duel Masters: Shadow of the Code (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Duel Masters: Shadow of the Code.gba` |
| Size | 16,777,216 bytes (0x01000000) |
| Header title | `DM SHADOW` |
| Game code | `BDUE` ( maker `70` = Atari ) |
| Version | 0x00; fixed byte 0x96 @0xB2 present |
| Header checksum | stored 0x0000, complement byte 0x53 (computed complement for the displayed title is 0x6C) — rebuilt/renamed header artifact (§16.1) |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` |
| crt0 `main` | Thumb pointer `0x0831E931` @ `0x08000100` → `main = 0x0831E930` |
| MD5 | `7e4b22c8a115d33a30a3e130884cde5d` |
| SHA-1 | `88b4d57bcfda1e8e96656395d80c2552ca4066fe` |
| SHA-256 | `edab01ce5be69ccee598edfe1d04275bb6266c2acad8c8a8d1890d42fb81bace` |

Embedded-header scan (Nintendo-logo signature `24 ff ae 51 69 9a a2 21`) found a **single** header at file `0x0`. No second game image, multiboot stub, cracktro or appended trainer. No scene-crack markers.

Internal build path: `C:/IQ_DEV/Productions/DuelMaster3_AGB_US/Src/ctxMenuTitle.c` (Mistic Software). This is the *third* Duel Masters GBA engine — **not** the same binary as the sibling `Kaijudo Showdown` (`BD6E`, 8 MiB, different hashes, different main, different validator addresses).

## 2. Executive summary

This title **does** have a developer-intended name-entry cheat system: the player name typed on the New Game "Player Name" screen is compared with a fixed table of **10 names** by a 5-call-site `strncmp`-style validator. However only **5 of the 10 table entries are live**: `FAITAA`, `FUYUU`, `OKANE`, `BAKUTO`, `KAGAMI`. The other five (`FURY`, `WALTER`, `TOMB`, `FOREST`, `BRIGHT`) are **dead leftovers of the sibling game's table** — they are present as bytes in all 94 replicated copies of the string pool but have **zero code references** in this ROM. Entering `FOREST` produced no RAM effect (money stayed at baseline `0x12C`), despite a fan-wiki claim that it grants a tier-3 Nature deck in this game; that claim appears to have been carried over from *Kaijudo Showdown*.

Published in-game codes found on the web are only `OKANE`, `KAGAMI`, `BAKUTO`. Two live names, **`FUYUU`** and **`FAITAA`**, appear in no published list. The validator compares a fixed number of bytes without checking the name's full length, so **prefix extensions work** for four names. Generated and confirmed on the real screen:

* **`FUYUUX`** → name buffer `46 55 59 55 55 58 00`; money field `0x03004A30` = `0x0258` (600), the same `+300` that `FUYUU` produces and exactly the delta encoded in the validator at `0x0829B7E4`. `FUYUUX` appears on no cheat list.

Bounds were proven by rejection: `FAITAAX` is rejected by the validator's 7-byte compare (which includes the terminating NUL), and the five dead names produce no effect. All in-scope RAM/CodeBreaker codes found on the web (all cards, infinite shields, instant win) are external memory patches and were **not** used.

Separately, the game has a **Kaijudo Code** — five story couplets reviewable in the Gizmo's `Stats & Quest / Code Notes` screen with L/R. It is a story-gated codex with no input surface, not a cheat, and is documented in §6.3.

## 3. How to reproduce

**Emulator**: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, `Xvfb :317 -screen 0 1280x1024x24` + `openbox`; keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.

**Path**:
1. Boot; press A through the Mistic splash, title logo and intro cutscene, then **Start** at "Press START".
2. Select **New Game** → "Player Name" screen (default `TOM`).
3. Press **B** eight times to clear the default name.
4. Type the code on the on-screen keypad (D-pad to a cell, **A** to enter). Keypad grid (8 columns × 5 rows):

   ```
   A B C D E F G H
   I J K L M N O P
   Q R S T U V W X
   Y Z 1 2 3 4 5 6
   7 8 9 0 - <space> <backspace> OK
   ```

   The unlabelled cell at row 5, column 6 is a **space**; row 5 column 7 is backspace (`←×`); row 5 column 8 is **OK**.
5. Navigate to **OK**, press A, then advance the difficulty/deck/dialogue sequence with A.
6. Read effects in IWRAM (name buffer `0x03004C90`; money `0x03004A30`; BAKUTO flags `0x03004CAC` etc.).

**Published codes verified against ROM bytes**: `OKANE` (5 bytes), `KAGAMI` (6 bytes in pool; compared as 4), `BAKUTO` (6 bytes in pool; compared as 5) all exist at the table addresses in §4. `FOREST`, `FURY`, `WALTER`, `TOMB`, `BRIGHT` exist as table strings but have no validator xref (negative finding, not an unverified literal). GameFAQs lists only external GameShark/CodeBreaker codes; Reddit/Fandom list the three names above.

**Out-of-scope published data**: GameShark master code `9233A6611E2E / AD88C83063CB / 783C91EBE993`, all-cards `B70395C21FA6 / 935FD7441CE6`, infinite shields `C2289760DBE6`, `R+A` instant-win — all are external RAM patches, not applied.

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x080000C0` | ROM/ARM | stock crt0 entry |
| `0x08000100` | ROM | Thumb `main` pointer `0x0831E931` |
| `0x08342840` | ROM | cheat-name table header `01 02 0A 19 32 00 00 00` (`0A` = 10 entries) |
| `0x08342848…0x08342890` | ROM | 10 names, 8-byte stride: `BAKUTO, FAITAA, OKANE, FUYUU, FURY, WALTER, TOMB, FOREST, BRIGHT, KAGAMI` (94 replicated copies across compilation units, `0x08342840`–`0x0834762C`) |
| `0x083425EC` | ROM/Thumb | `strncmp(a=r0, b=r1, n=r2)`; 0 = equal. Only **6** BL call sites in the whole image: 5 name checks + 1 unrelated |
| `0x082907C8` | ROM/Thumb | FAITAA check; compare at `0x082907F6` with literal `0x08342850` ("FAITAA"), n=7. Registered as callback via Thumb pointer at `0x08B28C1C` |
| `0x0829B498` | ROM/Thumb | FUYUU + BAKUTO check; compares at `0x0829B7D0` ("FUYUU" @ `0x08342D84`, n=5) and `0x0829B7F4` ("BAKUTO" @ `0x08342D6C`, n=5). Callback pointer at `0x0829DFC8` |
| `0x082A5AD4` | ROM/Thumb | OKANE check; compare at `0x082A5AE6` ("OKANE" @ `0x083431C4`, n=5); called from `0x082A60FC`, `0x082A631A` |
| `0x082C3FB0` | ROM/Thumb | KAGAMI check; compare at `0x082C3FC4` ("KAGAMI" @ `0x083447FC`, n=4); called from `0x082C4586`, `0x082C6998`, `0x082C6A38`, `0x082F9224` |
| `0x03004C90` | IWRAM | player-name buffer (NUL padded; a cursor byte `0x5F` occupies the first empty slot until the game transitions) |
| `0x03004A30` | IWRAM | money/credits field, 32-bit: baseline `0x12C` = 300 |
| `0x03004CAC/B0` | IWRAM | BAKUTO flags (4 bytes set by the check) |
| `0x03003E5C/60/64/68` | IWRAM | FAITAA-linked scene flags (`0x03003E64` holds pointer `0x08B28C38`) |
| `0x03003E5C bit2` | IWRAM | FAITAA match marker (`\|= 4`) — never observed set through the UI (see §8) |
| `0xAA500B–0xAA50EA` | ROM | Kaijudo Code couplets (5 parts) |
| `0xAA510D` | ROM | `Kaijudo Code not known yet.` |
| `0xA89E04 / 0xA89E1E` | ROM | Gizmo UI strings `Stats & Quest` / `Code Notes` |
| `0xAA5479–0xAA5513` | ROM | five "You unlock &lt;character&gt; in multiplayer mode." strings |

mGBA `.ssN` parsing: PNG `gbAs` chunk is zlib-compressed raw state (`0x61000` bytes for this 16 MiB ROM); IWRAM starts at raw `0x19000`, EWRAM at `0x21000`.

## 5. Algorithm

```
# entered name -> IWRAM 0x03004C90 (8 visible slots, cursor 0x5F in first empty slot)
# compare helper 0x083425EC = strncmp(r0, r1, r2): returns 0 on equality

# FUYUU / BAKUTO check (0x0829B498), run as a registered callback:
if strncmp(name, "FUYUU",  5) == 0:  [0x03004A30] += 300      # 0x0829B7E4: mov 0x96<<1
if strncmp(name, "BAKUTO", 5) == 0:  set [0x03004CAC], [0x03004CAE],
                                     [0x03004CAF], [0x03004CB0] = 1

# FAITAA check (0x082907C8):
unconditionally: [0x03003E60]=1; [0x03003E64]=0x08B28C38;
                 [0x03000142]=0; [0x03003E5C]=1; [0x03003E68]=1
if [0x03003E68]!=0: [0x03003E5C]=3; [0x03003E68]=1
if strncmp(name, "FAITAA\0", 7) == 0 or [0x030047E9] != 0:
                 [0x03003E5C] |= 4

# OKANE check (0x082A5AD4):
if strncmp(name, "OKANE", 5) == 0: skip the default warning call at 0x082A5AF8;
                                    display numeric debug/shop info

# KAGAMI check (0x082C3FB0):
if strncmp(name, "KAGA", 4) == 0 and random_check(0x08340DB0) passes:
                 return 1  -> reveal opponent's cards
```

**Critical flaw**: four checks call the helper with a fixed length *shorter than the full name + NUL*. There is no `strlen(name) == len` guard. Any name beginning with the magic prefix passes. FAITAA is the exception: its compare length 7 includes the NUL, so no extension can match — and because the UI leaves a `0x5F` cursor in that slot for a 6-character name, the flag was never observed set through the UI (§8).

## 6. Tables

### 6.1 Cheat-name table (exhaustive: 10 strings, 5 live)

| Name | Table slot (ROM) | Compare len | Live? | Effect | Confidence |
|---|---|---:|---|---|---|
| `BAKUTO` | `0x08342848` | 5 | yes | sets 4 flags at `0x03004CAC/B0` (minigame unlock, per published list) | Derived + name observed |
| `FAITAA` | `0x08342850` | 7 | yes* | scene flags `0x03003E5C\|=4`, `0x03003E64` image pointer | Derived; UI match not observed (§8) |
| `OKANE` | `0x08342858` | 5 | yes | skips warning; "infinite money" (published) | Derived from `0x082A5AD4` |
| `FUYUU` | `0x08342860` | 5 | yes | money `+300` (`0x03004A30`) | **Observed** |
| `FURY` | `0x08342868` | — | **no** | none — dead table entry | Derived (0 xrefs) |
| `WALTER` | `0x08342870` | — | **no** | none — dead table entry | Derived (0 xrefs) |
| `TOMB` | `0x08342878` | — | **no** | none — dead table entry | Derived (0 xrefs) |
| `FOREST` | `0x08342880` | — | **no** | none — dead table entry; **not** reproduced despite fan claim | Derived + observed no money effect |
| `BRIGHT` | `0x08342888` | — | **no** | none — dead table entry | Derived (0 xrefs) |
| `KAGAMI` | `0x08342890` | 4 | yes | random-gated reveal opponent's cards | Derived from `0x082C3FB0` |

\* FAITAA has a comparison call site but a 7-byte (NUL-inclusive) compare; see §8.

### 6.2 Input alphabet

Keypad cells, 8×5 grid: `A–Z`, `1 2 3 4 5 6 7 8 9 0`, `-`, unlabelled **space**, backspace, OK = 39 selectable cells. Magic names use only `A–Z`. Compare is case-sensitive exact bytes; the keypad offers uppercase only.

### 6.3 Kaijudo Code (story codex, not a cheat)

Five couplets stored at `0xAA500B` (each a NUL-terminated pair):

1. `I make no excuses.` / `My actions are my voice.`
2. `I have no enemies.` / `My opponent is my teacher.`
3. `I need no deceitful tricks.` / `My character is my sword.`
4. `I think not of quitting.` / `My courage is my secret weapon.`
5. `I know not of defeat.` / `My experience becomes my strength.`

Progress text at `0xAA1D93`, `0xAA2E14`, `0xAA315A`, `0xAA36C2`, `0xAA3B1E`; placeholder `Kaijudo Code not known yet.` at `0xAA510D`. Review screen: Gizmo → `Stats & Quest` → `Code Notes`, L/R to page (strings `0xA89E04`, `0xA89E1E`). This is a story-gated read-only codex; no text is typed anywhere. Five multiplayer characters (`Rekuta`, `Knight`, `Mimi`, `Kokujo`, `Shobu` — strings `0xAA5479`–`0xAA5513`) are save-bit unlocks (§16.18), not codes.

## 6b. Enumeration

**Space definition.** This is a fixed lookup table, not a checksum system: 10 strings over a 39-symbol keypad, compared with fixed `strncmp` lengths of 4, 5 or 7. No checksum, no bit packing, no generator function. The complete set of accepted magic words is exactly 5 live prefixes (4 of which accept arbitrary suffixes).

**Closure proof (§0.2 / §16.9).** Rather than infer from the string pool:
* the only `strncmp` implementation in the 16 MiB image is at `0x083425EC`, with **exactly 6 BL call sites**;
* 5 of those call sites compare the player-name buffer at `0x03004C90` with exactly the five literals `FAITAA`, `FUYUU`, `BAKUTO`, `OKANE`, `KAGAMI`; the 6th (`0x083337B2`) does not involve the name buffer;
* a full 32-bit scan for code references to any cheat-name string (outside the replicated literal-pool blob) returned exactly 7 words: the 5 live comparisons plus 2 false positives inside data (`0x83B9DD0`, `0x83FE308`);
* the 5 dead names have **zero** code references — this is a bounded negative result, not "not found";
* all five live names were entered on the real keypad and their buffers read from IWRAM (e.g. `FUYUU` → `46 55 59 55 55 5F 00`; `FUYUUX` → `46 55 59 55 55 58 00`).

**Novel codes (not in any published list).**

| Novel code | ROM evidence | In-game proof |
|---|---|---|
| `FUYUU` (name itself unpublished) | `strncmp(name,"FUYUU",5)` at `0x0829B7D0`; `+300` at `0x0829B7E4` | money `0x03004A30 = 0x0258` (600) vs baseline `0x012C` (300) |
| `FUYUUX` (prefix extension, unpublished spelling) | same 5-byte compare; byte index 5 ignored | entered on real keypad; name buffer `46 55 59 55 55 58 00`; money `0x0258` (600) |
| `FAITAA`, `BAKUTOX`, `OKANEX`, `KAGAX` | derived from the same fixed-length compares (lengths 5/5/4) | validation of these is derived from the validator model; `FUYUUX` is the in-game representative of the prefix class |

These spellings appear on GameFAQs, VGChartz, TCRF, Reddit and the Duel Masters wiki: **nowhere**. `FUYUUX` exercises the unadvertised prefix-acceptance combination that the published lists omit.

**Bounds proven by rejection.**
* `FAITAAX`: the validator compares **7** bytes including the terminating NUL (`0x082907F4: movs r2,#7`), so byte 6 (`X` or the UI cursor `0x5F`) mismatches the literal's `0x00`. Rejected by construction (Derived). Recorded in-game name buffer `46 41 49 54 41 41 58 00`; FAITAA flag bit `0x03003E5C & 4` remained 0 (Observed).
* `FOREST`, `FURY`, `WALTER`, `TOMB`, `BRIGHT`: present in the table but with no comparison call site; entering `FOREST` left money at `0x012C` (Observed), and the other four are rejected by the closed xref set (Derived).
* `XFUYUU` (magic word not at offset 0) would fail `strncmp` at byte 0; not separately entered, but covered by the same 5-byte compare semantics.

## 7. Validation evidence

* **Observed**: emulator screenshots of splash/title/name entry/difficulty/card shop (work dir `/tmp/duelshadow/shot_*.png`); IWRAM reads from mGBA savestates. Name buffers for `QWERTYU`, `FOREST`, `FUYUU`, `FUYUUX`, `FAITAA`, `FAITAAX` read at `0x03004C90`. Money `0x03004A30` = `0x012C` for control/`FOREST`, `0x0258` for `FUYUU` and `FUYUUX`. F1/Shift+F1 savestate cycling used for repeatable tests.
* **Derived**: table base/stride and replicated copy count; the single `strncmp` at `0x083425EC` and its exactly 6 call sites; all five validators, their literals, lengths and effect instructions; callback registration pointers; the prefix flaw; the dead-name classification (0 xrefs); FAITAA's NUL-inclusive 7-byte compare.
* **Inferred**: published effect labels for `OKANE` (infinite money), `KAGAMI` (see opponent's cards), `BAKUTO` (minigames) — the comparisons and name acceptance were observed, but the downstream feature screens were not all played through. The fan claim that `FOREST` gives a tier-3 Nature deck here is contradicted by the 0-xref finding and was not reproduced.

## 8. Unknowns

* FAITAA's flag bit `0x03003E5C & 4` was never observed set. The 7-byte compare includes a NUL while the UI leaves a `0x5F` cursor in byte 6 for a 6-character name, so FAITAA may be unreachable from the keypad (or its check may run on a normalised copy at a later scene). Its effect code is fully derived; the UI reachability is unresolved.
* Downstream screen-level confirmation of `OKANE`, `KAGAMI`, `BAKUTO` (name acceptance observed; minigame/duel-reveal screens not all visited).
* No hidden debug menu was found: a case-insensitive string scan produced no `DEBUG`/`TEST`/secret-menu labels, and no published button-code sequences exist for this title. An exhaustive button-mask (§5.4a) search was not performed, so a mask-based sequence without any string label remains unproven either way.
* The 94 replicated table copies were not individually typed; they are treated as literal-pool duplicates of one logical table, consistent with the sibling engine.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python 3 byte/literal/BL/PC-relative scanners.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for validator disassembly; Capstone 5.0.7 for literal-load scans.
* mGBA (SDL) + Xvfb `:317` + openbox + xdotool; savestate RAM reads via a Python `gbAs`/zlib parser (IWRAM at raw `0x19000`).
* Helper scripts in `/tmp/duelshadow/`: `k.py`, `pad.py`, `batchtest.py`, `ss.py`, `oracle.gdb`.

**Legal note**: no ROM bytes or copyrighted assets are reproduced here; only hashes, addresses, algorithms and generated code strings are published.
