# Killer 3D Pool (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Killer 3D Pool/Killer 3D Pool.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `KILLER3DPOOL` |
| Game code | `B3LE` (Europe, En/Fr/De/Es/It), maker `20` (DSI Games) |
| Version | `0x00`; complement `0x75`; header checksum `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| MD5 | `16bf8504460b72db612adc0e17831221` |
| SHA-1 | `9e988cb32c8b56ee2c3521ce1800e82289048840` |
| SHA-256 | `735870bba14766a5812f41ef347552355a9f88b5485f714db0f175a6fcca9be3` |

Single unpatched retail image; one Nintendo logo at `0x04`; no multiboot stub,
no second image, no trainer.

## 2. Executive summary — FINAL RESULT

The 12 published five-symbol strings are real data for this game's 16-character
roster, and the additive mod-16 checksum model derived earlier is correct
(11/12 codes reproduce exactly; the published Tom code `QJSFG` is a typo for
`QJSFF`). Their *meaning* is now established: **the four payload symbols are a
16-bit character-unlock bitmask** that the game expands into the 16 unlock flags
at RAM `0x03001030` via its own save-load decoder at `0x0800D850`.

**There is no code-entry surface in this build.** This is a proven negative, not
an open unknown. The screen dispatcher has a closed state set (§7.1), all 29
key-buffer xrefs resolve to known menu handlers (§7.2), the unlock-flag buffer
has exactly **two** writers and neither is key-driven (§7.3), no procedure
computes the checksum (§7.4), the alphabet exists nowhere in the image
(§7.5), and 158 button combinations at title and character-select produced
**zero** writes to the unlock flags under a hardware write-watchpoint (§7.6).

Consequently a code cannot be typed "in-game" on B3LE20 Rev.00: there is no
widget, no hidden state, and no input routine to inject into. The published
literals fit the game's save-format unlock mask but were published as if this
SKU had an entry screen; they therefore belong to a different SKU/build (e.g.
the US "Hardcore Pool" release, which does advertise password entry) or were
intended for a save editor. This is stated with the concrete bounds below.

## 3. How to reproduce

- Emulator: mGBA (SDL) `mgba -3` and `mgba -3 -d`, `SDL_AUDIODRIVER=dummy`,
  `DISPLAY=:319`; Xvfb :319 + openbox.
- Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys.
- mGBA CLI debugger: `break/t 0x0800e9b4` (key reader, once per frame) gives a
  reliable stop at each frame; `watch/w 0x03001030` traps every unlock-flag
  write; `r/1 <addr>` reads bytes. `dbg.py`, `dyntest2.py`, `brute_wp.py`,
  `brute_cs.py` in `/tmp/killerpool3/`.
- Static: REA/Ghidra 12.1.4 raw-ARM import at `0x08000000`;
  `procedure_pseudo_code` on all 163 procedures (full dump retained);
  `arm-none-eabi-objdump -M force-thumb -D` for literal-pool xrefs.
- Screen walk (all reached and screenshotted): boot → TITLE (4 items) →
  OPTIONS → SELECT PLAYER[1|2] (16 portraits, 12 silhouettes) → VS → GAME
  SELECT (4 modes) → NUMBER OF GAMES → live play → PAUSE → PAUSE OPTIONS →
  RESULTS → PLAY AGAIN? / NEXT PLAYER? → MP link screen.

## 4. Address map (new results in **bold**)

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ARM entry, stock crt0 | Derived |
| `0x0800E9B4` | Key reader: `held=~KEYINPUT` → `0x03001020`; `pressed=held&~prev` → `0x030010C4` | Derived + RAM |
| `0x03001020` / `0x030010C4` | Held / newly-pressed key masks (active high) | RAM |
| **`0x03001030`** | **16 one-byte character-unlock flags (index 0..15); 3–6 set at boot** | **RAM + xrefs (14 sites)** |
| **`0x0800D850–0x0800D94C`** | **Save-load decoder: reads 5 bytes from `0x03007330 + param*16`, expands four low nibbles into the 16 flags at `0x03001030`** | **static disasm** |
| **`0x08022B4–0x08022E2`** | **Award path: after a win, scan `(i+3)&0xF` and set flag + show `PLAYER UNLOCKED!` via `0x0800BBA8`** | **pseudocode + disasm** |
| `0x0800D020–0x0800D082` | Inverse: pack 16 flags into four nibbles for save | Disasm |
| `0x08007330` (RAM `0x03007330`) | 16-byte save records (2 slots) | Literal xrefs |
| `0x0803F64` / `0x08008090` | Title state machine / title menu handler | Ghidra |
| **`0x08006BA4`** | **Menu + options screen: accepts `param∈{0,1,2,5}`, returns exactly `{2,3,4}`** | **pseudocode** |
| **`0x080020B8`** | **Main dispatcher: handles only states 2, 3, 4; anything else returns** | **pseudocode** |
| `0x080088B4` / `0x080097A0` / `0x08009BAC` | Game select (4), best-of (4), player-count menu | Pseudocode |
| `0x08008EA0` / `0x080091F4` / `0x08009F64` / `0x0800AD2C` | Character-select render + input (16 entries; key masks `1`,`2`,`0x200`) | Pseudocode |
| `0x0800BBA8` | `PLAYER UNLOCKED!` celebration screen | Pseudocode |
| `0x08013D24` / `0x08013EFC` | Display-record walker / ASCII→font glyph map | Prior report + pseudocode |
| `0x08B40FC` | Base of 525-record localization table (12-byte stride) | Prior report |

No literal password table, no alphabet string, and no checksum routine exist in
the image (§7.4–7.5).

## 5. Algorithm (retained from prior work, now interpreted)

```
alphabet = "BCDFGHJKLMNPQRST"        # 16 symbols, value = index (B=0 … T=15)
code     = c0 c1 c2 c3 c4
payload  = (v0<<12)|(v1<<8)|(v2<<4)|v3      # a 16-bit unlock bitmask
valid    iff  (v0+v1+v2+v3) & 0xF == v4     # checksum over the four mask nibbles
```

The four payload nibbles are exactly the four low nibbles the game's decoder
at `0x0800D850` expands into the 16 flags at `0x03001030`:
`byte2[3:0] → flags 0–3`, `byte3[3:0] → flags 4–7`, `byte4[3:0] → flags 8–11`,
`byte5[3:0] → flags 12–15`. Sorting the 11 checksum-valid published payloads by
value gives a cumulative chain of unlock masks; `0xFFFF` (Tony) sets all 16
flags. The checksum is a property of the save-format code, not an in-game
validator — no procedure in this ROM computes it (§7.4).

## 6. Tables (retained)

### 6.1 Published codes decoded

| Character | Code | payload | v4 (check) | checksum OK |
|---|---|---|---|---|
| Andy | QKSKL | `0xC7E7` | L (8) | yes |
| Angie | QFSCS | `0xC3E1` | S (14) | yes |
| Billy | QTSTL | `0xCFEF` | L (8) | yes |
| Carl | QCSCQ | `0xC1E1` | Q (12) | yes |
| Carol | QTSKB | `0xCFE7` | B (0) | yes |
| Dawn | RTSTM | `0xDFEF` | M (9) | yes |
| Johnny | RTTTN | `0xDFFF` | N (10) | yes |
| Laura | QCSBP | `0xC1E0` | P (11) | yes |
| Michael | QFSFB | `0xC3E3` | B (0) | yes |
| **Tom** | **QJSFG** | `0xC6E3` | G (4), expected F (3) | **NO — published typo** |
| Tony | TTTTQ | `0xFFFF` | Q (12) | yes |
| Ulrika | QBSBN | `0xC0E0` | N (10) | yes |

Sources: GameFAQs (archived 2018-11-26), SuperCheats ID 6672, both listing the
same twelve spellings.

### 6.2 Space

Alphabet 16, length 5 ⇒ 16⁵ = 1,048,576 strings; checksum divides by 16 ⇒
65,536 checksum-valid values; the published 12 occupy 12 payload values of the
16-bit unlock-mask space.

**Novel checksum-valid codes (retained):** `QJSFF` (checksum-correct Tom,
payload `0xC6E3`) and `QLSKM` (payload `0xC8E7`, deliberate unadvertised mask).
Both remain arithmetically valid but **cannot be typed in-game** on this build
because no entry surface exists (§7).

## 7. Proof that no entry surface exists

### 7.1 Closed dispatcher / state set
`FUN_080020B8` is the only main loop. Its dispatch is exhaustive:
`iVar3 = FUN_08006BA4(uVar7)`; `if (1 < iVar3-2U) { if (iVar3 != 4) return; …character-select… }`
else states 2/3 → `FUN_080088B4 → 0x80097A0 → 0x8009BAC → 0x8003F64 → 0x80094D4`.
`FUN_08006BA4` itself handles `param ∈ {0,1,2,5}` and returns **only** 2, 3,
or 4. There is no sixth state, no error/default branch into another screen, and
no call to any input routine. The `0x8003F64` "held ∈ {5,6}, frame<2 → link
screen" chord and the `0x080053A8` in-game chord are the only hidden gates;
neither unlocks characters (checked by watchpoint, §7.6).

### 7.2 Key-buffer xref closure
The pressed-key buffer `0x030010C4` has 29 literal-pool references at file
offsets `0x4690, 0x506c, 0x5d40, 0x7318, 0x7430, 0x74a4, 0x74f8, 0x77c4,
0x7988, 0x7c38, 0x7ea8, 0x8314, 0x85c0, 0x8648, 0x8e34, 0x979c, 0x9b58,
0x9f0c, 0xa5c0, 0xa5f8, 0xac74, 0xb1dc, 0xb294, 0xb6ec, 0xbad4, 0xbdd4,
0xc0fc, 0xc428, 0xe9d8`. Every one resolves to a known handler
(`0x8003F64`, `0x8004880`, `0x8006BA4`, `0x8007988`, `0x8007A8`, `0x8008090`,
`0x80088B4`, `0x80097A0`, `0x8009BAC`, `0x8009F64`, `0x800A710`, `0x800AD2C`,
`0x800B2B0`, `0x800B744`). None accumulates five glyph indices; all read the
buffer only for cursor up/down, confirm, cancel, pause, or in-game controls.
There is no orphan reference that could be a hidden entry widget.

### 7.3 Unlock-flag writer count = 2, neither key-driven
The unlock buffer `0x03001030` has 14 literal references. Ten are reads
(character-select portrait rendering at `0x8008E08/0x8008EE4/0x8008FA0/
0x8009090/0x8009178/0x800924C/0x80092EC/0x80093A0/0x8009454/0x800A590`) and
one is a read for save packing (`0x800D084`). **Only two are writes:**
1. `0x08022B4–0x08022E2` — post-win award loop, sets flags after tournament
   results (`FUN_0800BBA8` shows `PLAYER UNLOCKED!`).
2. `0x0800D850–0x0800D946` — save-load decoder, expands four save nibbles.

Neither writer reads the key buffer. There is no third path by which typed
input could set an unlock flag.

### 7.4 No checksum routine
All 163 procedures were decompiled and searched. No function computes
`(v0+v1+v2+v3)&0xF` and compares it with a fifth value. The only `&0xF` sites
are glyph-index wraparound in menus (`0x8008EA0`, `0x80091F4`, `0x8009F64`) and
bit extraction in rendering. The `FUN_0800D850` decoder does not verify any
checksum — it unconditionally expands the four nibbles.

### 7.5 No alphabet table / label
Neither the ASCII string `BCDFGHJKLMNPQRST` nor its font-glyph sequence
`02 03 04 06 07 08 0A 0B 0C 0D 0E 10 11 12 13 14` (nor either reversed) occurs
anywhere in the 4 MiB image. The 525-record localization table was fully
decoded: no `PASSWORD`, `CODE`, `ENTER`, `SECRET`, `UNLOCK` (other than the
result `PLAYER UNLOCKED!`) or debug-menu label exists. 30,493 `strings` records:
`password` 0, `code` 0, `cheat` 0, `debug` 0, `secret` 0, `unlock` 1. A real
player asked SuperCheats in 2023 *"I don't see an entry to type it in?"* — the
question has no answer on that site.

### 7.6 Dynamic watchpoint brute force (158 inputs, zero writes)
With `watch/w 0x03001030` armed in mGBA's debugger:
- TITLE: 79 combinations (10 singles + all 45 two-key chords + 24 three-key
  chords) — **0 watchpoint hits**.
- CHARACTER SELECT (reached by `A,A` from title): the same 79 combinations —
  **0 watchpoint hits**.
- Regular RAM reads show flags constant at `[0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0]`
  (only the four default characters) after every input.

A write to any unlock flag would have trapped; none did. This closes the
dynamic search for a button-combo code-entry route.

## 8. Bounds proven by rejection

The only validator available is the checksum algebra of §5 (no in-game surface
exists to submit inputs to). Rejection tests, each with expected checksum:

| Input | First four | computed v4 | supplied v4 | Result |
|---|---|---|---|---|
| `QJSFG` (published Tom) | C,6,E,3 | **F (3)** | G (4) | **REJECT** (off-by-one published typo) |
| `QKSKJ` | C,7,E,7 | **L (8)** | J (6) | **REJECT** |
| `TTTTZ` | F,F,F,F | **Q (12)** | T (15) | **REJECT** |
| `QBSBB` | C,0,E,0 | **N (10)** | B (0) | **REJECT** |
| `RTSTM` with last→`B` | D,F,E,F | **M (9)** | B (0) | **REJECT** |
| `QLSKL` (mutation of novel `QLSKM`) | C,8,E,7 | **M (9)** | L (8) | **REJECT** |
| `QJSFF` (novel, checksum-correct) | C,6,E,3 | F (3) | F (3) | ACCEPT by model |
| `QLSKM` (novel) | C,8,E,7 | M (9) | M (9) | ACCEPT by model |

In-game rejection could not be demonstrated because no surface accepts any
input; this is a direct consequence of the §7 proof, not an omitted test.

## 9. Conclusion

- **Entry surface:** none. Proven by closed dispatcher (§7.1), exhaustive key
  xrefs (§7.2), exactly two non-key-driven unlock writers (§7.3), no checksum
  routine (§7.4), no alphabet/label (§7.5), and 158 zero-hit dynamic inputs
  (§7.6).
- **In-game confirmed code:** none possible on this build. The published codes
  are 16-bit unlock masks in a consonant-hex cipher; this SKU's only route to
  those flags is winning tournaments or loading a save. The codes therefore
  belong to a different SKU/build or an external save editor, not B3LE20
  Rev.00's UI.
- **Retained work:** checksum model, 11/12 reproduction, `QJSFG`→`QJSFF`
  correction, novel `QJSFF`/`QLSKM`, 525-record localization decode, ASCII→font
  map, full screen walk.

## 10. Tooling / cleanup

REA Ghidra 12.1.4, `arm-none-eabi-objdump -M force-thumb`, mGBA 0.x SDL + CLI
debugger, Xvfb :319 + openbox, xdotool, scrot, Pillow, Python 3. All analysis
artifacts in `/tmp/killerpool3/`. No `INDEX.md` was modified. No
`.sav`/`.ss*` files were created in the ROM folder. Own processes (Xvfb/openbox
PIDs 773499/773504 and mGBA PIDs launched by the drivers) were terminated by
PID only; no `pkill` was used.
