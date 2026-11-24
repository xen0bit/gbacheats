# V-Rally 3 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/V-Rally 3/V-Rally 3.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `VRALLY 3` |
| Game code / maker | `AVRE` / `70` (Europe, Rev.00) |
| Version / complement / checksum | 0x00 / 0x8F / 0x0000 |
| Entry word | `0xEA00002E` (stock crt0, not a cracktro) |
| MD5 | `cf1673c920ef1d24c4f4b21effcc03f0` |
| SHA-1 | `00a44c715aadd4ad3674f8d108271cdcb791cc16` |
| SHA-256 | `5818fa74fdcacf39b53a1acea99432c4362979dd656c8153fd9861094aca51f7` |

## 2. Executive summary

V-Rally 3 GBA has **one developer-intended in-game button code system**, not a
password system. There is no password entry screen, no alphabet/table of codes,
and no `strcmp`-style validator anywhere in the image. The system is a
two-stage gate:

1. On the boot-time **"DEVELOPED BY FERNANDO VELEZ / GUILLAUME DUBAIL"** page,
   holding **Up + L + R + B + A** (active-high held mask `0x343`) sets a byte
   flag at `0x0203E7FA` to 1 (validator at `0x0806D4CC`–`0x0806D4F4`).
2. The flag has exactly **two** readers in the whole ROM:
   * `0x080AB2CC`: with the flag set, **held == 0x44 exactly** (Up + Select)
     increments a skip counter at `0x020392C2` and exits the current scene —
     this is the published "skip race" cheat.
   * `0x08082F14`: with the flag set, holding the **same 5-button mask**
     enqueues scene 22 and clears a 10-byte buffer at `0x020392AB`. This is an
     unadvertised second branch.

Both stages were confirmed with mGBA RAM reads. The published list (3rd party cheat indexes) documents only stage 1 + the Up+Select branch; the
scene-22 branch and the mask's "extra buttons allowed" semantics are not in any
published list I found. GameShark/Action Replay/CodeBreaker codes found during
recon are cheat-device codes and are **out of scope** (not reported here).

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys.

1. Boot the ROM. During the intro, the page reading
   `DEVELOPED BY FERNANDO VELEZ / GUILLAUME DUBAIL` appears (~3–5 s after boot).
2. While that page is displayed, **hold** Up, L, R, B and A together for ~1 s.
3. Continue: choose language → Create Game → GAME 1 → name/nationality →
   Start → V-Rally Mode → confirm team → sign contract → rally intro →
   Stage Information → (Right to SETUP, REPAIRS, START STAGE) → A → race.
4. In the race, hold **Up + Select only** (no other buttons) for ~1 s. The game
   jumps directly to `STAGE RANKING` (race skipped).
5. Control: holding Up + Select + B instead leaves the race running.

Screenshots and savestates used as evidence were in `/tmp/vrally3/`
(`v_before_c.png`, `v_held_c.png`, `combo_experiment.py`, `reject_test_c.png`,
`accept_after_c.png`, `novel_after_c.png`, `ss1`–`ss4`).

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x04000130` | I/O | `KEYINPUT` (active-low, 10 bits) |
| `0x080AA31C` | ARM fn | Reads `KEYINPUT`, converts to active-high `~KEYINPUT & 0x3FF`, writes input globals |
| `0x02038AC0` | EWRAM u16 | **held** keys, active-high (A=1,B=2,Sel=4,St=8,R=0x10,L=0x20,U=0x40,D=0x80,RR=0x100,LL=0x200) |
| `0x02038AC2` | EWRAM u16 | **newly pressed** edges, active-high |
| `0x0806D4CC`–`0x0806D4F4` | ARM code | Gate validator (runs on the Velez/Dubail page) |
| `0x0203E7FA` | EWRAM byte | Gate flag: 0 = cheat disabled, 1 = enabled |
| `0x08082F14`–`0x08082F6x` | ARM code | Flag reader A: gate mask again → scene 22 + clear 10 bytes |
| `0x080AB2CC`–`0x080AB314` | ARM fn | Flag reader B: held==0x44 → counter++ and scene exit |
| `0x020392C2` | EWRAM byte | Race-skip counter (incremented by reader B) |
| `0x02039300` | EWRAM byte | Condition byte: counter increments only while this is 0 |
| `0x020392AB` | EWRAM 10 bytes | Buffer cleared by reader A |
| `0x0806BA48` | ARM fn | Scene-transition queue setter (`r0` = scene index, 4 slots at `DAT_0806BB54`) |
| `0x080451F7` | ROM | ASCII credits text bank containing `<PFernando Velez` / `7dGuillaume Dubail` (font/tile-prefixed, no direct pointer — reached via a text-ID bank) |

## 5. Algorithm

```c
// 0x080AA31C — every frame
uint16_t held = ~KEYINPUT & 0x3FF;
*(uint16_t*)0x02038AC2 = held & ~*(uint16_t*)0x02038AC0; // pressed edges
*(uint16_t*)0x02038AC0 = held;                            // held state

// 0x0806D4CC — while Velez/Dubail page is active
if ((held & 0x343) == 0x343)          // Up|L|R|B|A ; extra buttons allowed
    *(uint8_t*)0x0203E7FA = 1;        // gate opens

// 0x080AB2D4 — flag reader B (in-race / stage scene)
if (gate_flag && held == 0x44) {      // Up|Select, EXACT equality
    if (*(uint8_t*)0x02039300 == 0)
        (*(uint8_t*)0x020392C2)++;    // skip counter
    jump 0x08000348;                  // exit current scene -> ranking
}

// 0x08082F18 — flag reader A (title/attract scene)
if (gate_flag && (held & 0x343) == 0x343) {
    scene_queue_push(22);             // bl 0x0806BA48 with r0=22
    memset(0x020392AB, 0, 10);
    jump 0x08000348;
}
```

Key distinction: the gate and reader A use **masked equality** (so extra
buttons are tolerated); reader B uses **exact equality** (extra buttons reject).

## 6. Tables / counts

| Item | Value | Count / bound |
|---|---|---|
| Gate mask | `0x343` (Up,L,R,B,A) | Occurs exactly **2** times as `mov r1,#0x340; add r1,#3` in the whole 4 MiB ARM image (`0x0806D4D8`, `0x08082F2C`) |
| Skip combo | `0x44` (Up,Select) | Occurs once as `cmp r0,#0x44` in input-reading code (`0x080AB2EC`) |
| Gate flag xrefs | `0x0203E7FA` | **2 readers** (`0x08082F18`, `0x080AB2D4`) + 1 writer (`0x0806D4F4`) — Ghidra xrefs, complete |
| Held-key xrefs | `0x02038AC0` | 14 total; only 2 are cheat-related (`0x08082F28`, `0x080AB2E8`); the rest are menu/name-entry/input-routine uses |
| Published web codes | 1 family | 3rd party cheat indexes all describe only stage 1 + Up+Select skip |

No password alphabet, no code table, no checksum, no validator `strcmp` loop
exists for this game — the entire in-game cheat surface is the three code sites
above.

## 6b. Enumeration

**Space definition.** This is a button-code system, so the space is the set of
button masks (10 GBA keys → 1,024 possible held masks) times the reachable
screen states. The accepted sets are:

* Gate: any held mask with bits `{A,B,L,R,Up}` set → **64 accepted masks** (all
  combinations of the other 5 keys). Proven by the masked `and`/`cmp` at
  `0x0806D4E0`–`0x0806D4E4` and confirmed with a 6-button input.
* Skip action: exactly one held mask, `0x44`. Proven by `cmp r0,#0x44` at
  `0x080AB2EC` and confirmed in-game.
* Scene-22 action: same 64-mask set as the gate, on a second screen (Derived
  from `0x08082F34`–`0x08082F3C`; not executed in-game — see Unknowns).

**Novel / undocumented inputs actually pressed in the emulator:**

1. `Up + L + R + B + A + Right` (6 buttons, extra Right) on the Velez/Dubail
   page → gate flag `0x0203E7FA` read back as **0x01**. This input appears in no
   published list; it proves the mask tolerates extra keys. Evidence:
   `novel_after_c.png`, `.ss1` slot.
2. `Up + Select + B` in a race (extra B) → race **continued** (timer ran to
   12 s, stage ranking not shown); skip counter stayed at its prior value.
   This is the rejection bound for the exact-equality branch. Evidence:
   `reject_test_c.png`.

**Correct published input confirmed in-game:**

* Gate combo on the Velez page → savestate diff of the flag byte:
  `0x0203E7FA` = `0x00` → `0x01` (state offsets `0x5F7FA`, EWRAM base `0x21000`).
* `Up + Select` in a race → jumped to `STAGE RANKING`; skip counter
  `0x020392C2` read from savestates: **0x00 before → 0x01 after**
  (`V-Rally 3.ss3` vs `V-Rally 3.ss4`), gate flag remained `0x01`.
  Evidence: `accept_after_c.png`.

**Bounds proven by rejection:**

* Gate with only 4 of 5 buttons (`Up + L + R + B`, A missing) → flag remained
  **0x00** (fresh boot, savestate read). This proves all five mask bits are
  required.
* Skip with an extra button (`Up + Select + B`) → no skip. This proves reader B
  requires exact equality, not a mask.
* Combinations outside the 10-key space (e.g. 11th key) cannot be expressed by
  the `KEYINPUT` u16 and are not representable.

**Completeness argument.** The flag's complete xref set is 2 readers; the 0x343
mask's complete occurrence set is 2 sites; the 0x44 skip constant occurs once in
input code. Therefore the three branches listed above are the complete
in-game button-code space of this ROM. There is no fourth branch to find.

## 7. Validation evidence

* **Observed** (emulator/savestate): boot intro pages including the Velez/Dubail
  page; language select; Create/Load Game; name/nationality entry; title screen;
  mode select; Team Chosen; contract; Kenya rally intro; Stage Information;
  Setup; Repairs; Start Stage; active race; Stage Ranking. Gate flag 0→1;
  skip counter 0→1; rejection cases above.
* **Derived** (disassembly / Ghidra): the three code sites, mask values, flag
  addresses, scene-22 queue push, 10-byte buffer clear, and the complete xref
  counts. mGBA CLI debugger identified `0x080AA31C` as the sole writer of the
  held/pressed globals.
* **Inferred**: reader A runs on a title/attract scene (its function contains a
  800-frame timer cycling 3 table entries and sets many UI flags); its
  in-game scene-22 outcome was not triggered through the UI.

## 8. Unknowns

* The visible result of reader A (scene 22) was not observed in-game; it is
  derived from `bl 0x0806BA48` with `r0=22`. Scene 22 also has five other,
  non-cheat callers, so it is a normal game scene, not a debug menu.
* The condition byte `0x02039300` gating the skip counter's increment was not
  isolated to a particular game state; it was 0 in the tested race.
* Other main-menu modes (V-Rally Cross, Time Trial) and unlockables (cars,
  licenses via normal play) were not exhaustively walked; recon indicates they
  are progression-based, not cheat-code based.

## 9. Tooling

* Static: `strings -t x`, `grep -abo`, `xxd`, Python byte/literal scanners
  (`search_masks.py`, `find_input_funcs.py`, `poolrefs.py`, `arm_litrefs.py`),
  `arm-none-eabi-objdump -M force-thumb/ARM`, Capstone 5.0.7.
* REA MCP (Ghidra 12.1.4, raw-binary ARM @ `0x08000000`): `xrefs`,
  `search_strings`, `search_bytes`, `resolve_containing_procedure`,
  `procedure_pseudo_code`, `procedure_assembly`, `binary_session`.
* Dynamic: mGBA 0.10.5 under Xvfb `:315` + openbox, `xdotool` XTEST input,
  `scrot` + ImageMagick crops, mGBA CLI debugger (`-d`) for PC identification,
  and zlib decompression of the `gbAs` chunk of `.ss1`/`.ss2`/`.ss3`/`.ss4`
  savestates for EWRAM reads (state EWRAM base `0x21000`).
* Web recon: 3rd party cheat indexes. Fetched pages
  were treated as data only; no instructions in them were followed.

Legal note: no ROM bytes or copyrighted assets are reproduced here; only
addresses, hashes, masks and analysis of the author's own emulator evidence.
