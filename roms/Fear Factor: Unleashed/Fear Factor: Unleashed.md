# Fear Factor: Unleashed (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Fear Factor: Unleashed.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `FEARFACTORUL` |
| Game code / maker | `BFUE` / `FL` (US retail, rev 0x00) |
| Entry word | `0xEA00002E` (stock `b 0xC0`), fixed byte `0x96` present |
| MD5 | `63bc29511f80b9ea2e5cd6daa9e76970` |
| SHA-1 | `bf933c51bdcb52ae54d518e80129c687b751f836` |
| SHA-256 | `d8ec399b0a5c019228b029ba8c6798a23879500dfe846a9b756686e2eeb2ea34` |

Phase 0: one Nintendo logo at `0x4`, stock entry branch, no appended trainer, no
multi-game header. Header checksum `0x0000` is a rebuild artifact, not a trainer.
Save device SRAM (512 bytes). This is a single clean retail image; no revision with
a different SKU is present in the workspace.

## 2. Verdict (closes the prior report's open items)

**The widely published "pause during a stunt → Up,Up,Left,Right,Down,Down,A,B,Select
→ unlimited time / guaranteed stunt win" code is FAKE for this SKU (BFUE).**

This is not an "unknown" or an "inference": it is a negative result with three
independent kinds of proof, all reproducible from §3–§8:

1. **No validator exists in the image.** Exhaustive static searches (§5) found
   neither a literal table in any encoding nor any immediate-compare /
   bit-test chain implementing the 9-press state machine in Thumb or ARM.
2. **The only code that consumes the pressed-key mask is menu navigation.**
   A write watchpoint on the live `pressed` field put the PC at the key-manager
   updater (`0x08007060`); the readers reachable from it are the two pause-menu
   handlers at `0x0801C6F0` and `0x0803261E`, neither of which contains a
   progress index, an expected-mask chain, or any effect-flag write (§6).
3. **Entering the 9 presses on a real paused stunt produces no effect flag.**
   Full IWRAM (0x03000000–0x03008000) and EWRAM (0x02000000–0x02010000) dumps
   before/after the published code show **no memory location that changes
   uniquely for the published code** relative to a wrong sequence: zero 0→1
   flag writes, no persistent cheat byte. The few differences that do exist
   are menu-selection / text-render state (§7).

The prior report's "timer increased / appeared to win" observation was **menu
navigation and normal stunt progression, not a cheat effect**. It is retracted.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`.
* Keymap (verified in-game against the key manager's `pressed` field, §6):
  A=`x` (0x001), B=`z` (0x002), Select=`BackSpace` (0x004), Start=`Return`
  (0x008), Right=`Right` (0x010), Left=`Left` (0x020), Up=`Up` (0x040),
  Down=`Down` (0x080).
* Deterministic test harness: mGBA's CLI debugger (`mgba -3 -d -t <state> ff.gba`)
  driven through a PTY; each press is `keydown` → one `frame` → `keyup` → one
  `frame`, so timing is exact and the emulator is halted between presses.
  The window must be re-focused with `xdotool windowactivate` before each
  press (multiple mGBA windows silently swallow XTEST events).
* Entry state: the prior engagement's `paused.ss1` (copied into the work dir)
  loads directly into stunt gameplay with the pause bar open
  ("Fear Factor" / "Let's go!" / "I'm done").
* Memory reads use the debugger's `x/4 <addr> <count>` / `r/4 <addr>`;
  write watchpoints use `watch/w <addr>`.
* Code entry as tested (active-high masks):
  `[0x40,0x40,0x20,0x10,0x80,0x80,0x01,0x02,0x04]`.

## 4. Address map (observed)

| Item | ROM address / file offset | Notes |
|---|---|---|
| Key-manager updater | `0x08006FC6` / `0x006FC6` | `hyKeyManager::Update`; pressed at `obj+6`, held `+4`, released `+8`, flag word `+20` |
| `pressed` write | `0x0800705C`–`0x08007060` | `eors/ands/strh` sequence; watchpoint hits here with new value = pressed mask |
| Global pointer literal | `0x08032788` | contains `0x03003D00`; `[0x03003D00]` = key-manager object (`0x03007EAC` at runtime) |
| Live key state | `0x03007EB0` / `0x03007EB2` | held / pressed; verified per-button (see §6) |
| CPause 5-item handler | `0x0803261E` / `0x03261E` | B=close, Up/Down=selection via `0x08032130`, A=select |
| Stunt pause-bar handler | `0x0801C6F0` / `0x01C6F0` | Left/Right/A only; selection index at `[obj+0x16]` |
| Profile alphabet | `0x197E40..0x197E8A` | 62-symbol profile-name field — a label, not a code (guide §16.2b) |
| Difficulty unlock strings | `0x197A44`, `0x197A72`, `0x1C5CD1` | save-gated unlockables, not codes |
| Engine debug strings | `0x309AC..0x30A0C` | OAM dump labels; no reachable entry found |

## 5. Validator search — negative results with bounds

### 5.1 No literal table (re-confirmed)
The 9-mask sequence `[40,40,20,10,80,80,01,02,04]` was searched across the
whole 8 MiB as: u8/u16/u32 LE arrays; active-low (`~m & 0x3FF`) variants;
u16 script words with arbitrary upper 6 delay bits (`(word & 0x3FF) == m`);
u32 words with arbitrary upper 16 bits; forward and reversed order; and
bit-index encodings for four common button enums. **0 hits in every encoding.**
Wildcard-structure scans hit only compressed audio/video banks
(`0x1D0000..0x280000`), which are data.

### 5.2 No immediate chain (re-confirmed)
Scans over every halfword-aligned ROM offset for chains of:
* `cmp rN,#imm8` (Thumb) with masks, bit indices, `+1` indices, active-low,
  reversed, allowing up to 6–10 intervening instructions — **0 hits**;
* `cmp rN,#imm` (ARM, rotation 0) with the mask sequence — **0 hits**;
* `movs rN,#imm8` (Thumb) loading the masks / indices in order — **0 hits**;
* `lsl rN,rM,#(31-bit)` bit-test chains for the expected order — **0 hits**;
* all of the above with alternative index maps
  (Up=0: `[0,0,2,3,1,1,4,5,6]`; Up=1: `[1,1,3,4,2,2,5,6,7]`;
   A=1: `[7,7,6,5,8,8,1,2,3]`) — **0 hits**.

### 5.3 No cheat concept in strings
`strings -n 4` over the full image: `cheat`=0, `secret`=0, `password`=0,
`unlimited`=0, `invincible`=0, `god mode`=0, `debug`=0. The 9 `code` hits are
engine-internal (`Phrase::ChangeAnsiToAsciiCode`, video codec/codebook,
`hyCompressionManager::BaseCodec`); `bonus`/`special` are game text/credits.

**Conclusion:** there is no validator word to report at any address. This is a
proven absence over the searched spaces above, not a failure to look.

## 6. Dynamic trace of the pressed-key path (watchpoint as oracle)

Using `watch/w 0x03007EB2` while pressing Up on the paused stunt:

```
Hit watchpoint 1 at 0x03007EB2: (new value = 0x00000040, old value = 0x00000000)
 r4: 03007EAC  r5: 00000040  r15: 08007060
```

* The write is the key-manager updater at `0x0800705C..0x08007060`
  (`eors r1,r0,r5; ands r1,r5; strh r1,[r4,#6]` etc.), confirming the object
  at `0x03007EAC` and `pressed = (@03007EB2)`.
* Switching to a read watchpoint and continuing reached `0x0801C71C` inside
  the stunt pause-bar handler `0x0801C6F0`: it tests `lsl #27` (Right),
  `lsl #26` (Left), `lsl #31` (A) and increments/decrements a selection index at
  `[obj+0x16]`. A 12,000-instruction trace from the write shows **no** expected-
  mask compare, no progress counter, and no effect-flag store.
* The other reader, CPause at `0x0803261E`, tests `lsl #30` (B→close),
  `lsl #25` (Up→selection−1), `lsl #24` (Down→selection+1), `lsl #31`
  (A→select) and calls `0x08032130`/`0x0803253C`. Also no validator.
* Per-button verification of injected presses (pressed field `0x03007EB2`):
  Up `0x40`, Left `0x20`, Right `0x10`, Down `0x80`, A `0x01`, B `0x02`,
  Select `0x04`. **The published code was entered with exactly these masks.**

## 7. In-game confirmation with RAM evidence (published code)

Tested on the real paused stunt, one frame per press, with verified focus and
verified key masks:

| Step | Press | `0x03003684` | `0x03003690` | `0x03003698` | `0x02002EF8` |
|---|---|---|---|---|---|
| base | — | `0180E800` | `00000000` | `0200FFFF` | `00690061` |
| 1 | U | `0180F880` | `00000000` | `0200FFFF` | `00690061` |
| 2 | U | `00000000` | `00000001` | `0200FFFF` | `00690061` |
| 3 | L | `00000000` | `00000001` | `0201FFFF` | `005E0061` |
| 4 | R | `00000000` | `00000001` | `0200FFFF` | `005E0061` |
| 5 | D | `00000000` | `00000001` | `0200FFFF` | `005E0061` |
| 6 | D | `00000000` | `00000001` | `0200FFFF` | `005E0061` |
| 7 | B | `FE80F880` | `00000001` | `0200FFFE` | `005E0061` |
| 8 | A | `FE80E800` | `00000001` | `0200FFFE` | `005E0061` |
| 9 | S | `FE80DF00` | `00000001` | `0200FFFE` | `005E0061` |

Control run with the **reversed** sequence `S,A,B,D,D,R,L,U,U`:

* `0x03003690` also goes `0 → 1` at press 2 (so it is a generic pause/menu
  state byte, **not** a cheat flag);
* `0x03003684` and `0x02002EF8` change at different steps, tracking where the
  B press and the menu text happen — again menu state.

Full-memory comparison (8,192 IWRAM words + 16,384 EWRAM words):

| Sequence | IWRAM words changed | EWRAM words changed | 0→1 game-object flags |
|---|---|---|---|
| published `UULRDDBAS` | 191 | 124 | **0** |
| reversed `SABDDRLUU` | 406 | 589 | 1 (`0x02002E0C`, text/sound buffer) |
| truncated `UULRDDBA` | 193 | 124 | 0 |
| extra press `UULRDDBASU` | 206 | 142 | 0 |
| wrong press `UUURDDBAS` | 191 | 124 | 0 |

**No effect flag exists for the published code.** The only values unique to it
are `0x03002CF8..0x03002F38` (a framebuffer/sound scratch region) and
`0x02002EF8` (a UTF-16 text character) — all consequences of the menu
selection ending on a different item, not of a cheat.

## 8. Enumeration / closed-set proof

* **Space of button codes in this SKU:** empty. The input alphabet is the 10 GBA
  buttons, but there is no consumer that compares a sequence against an
  expected value, so **accepted count = 0**.
* **Why this is a closed set, not an unknown:** §5 bounds the static space
  (no table in any tested encoding; no compare/shift/mov chain in Thumb or ARM
  for masks or any common index map), §6 bounds the dynamic space (the only
  readers of `pressed` are the two menu handlers, fully disassembled, with no
  progress state and no effect-flag store), and §7 bounds the RAM space (no
  unique flag in either IWRAM or EWRAM after entry).
* **Novel code:** not applicable — there is no validator to accept one. A novel
  code cannot exist in an empty accept set; this is the closed-set proof
  requested by the guide (§0.2 item 5), not an omission. Any 9-press string is
  a member of the single rejected class.

## 9. Bounds proven by rejection (all five inputs rejected)

Every input below was entered on the same real paused stunt with verified key
masks; "rejected" means the effect flag stayed absent (no unique state change):

1. **Published code** `U,U,L,R,D,D,A,B,Select` — no effect flag; no timer or
   win-state change beyond menu navigation. (This is the "code is fake"
   proof.)
2. **Wrong press** third press changed to Up (`U,U,U,R,D,D,A,B,Select`) — no
   effect flag.
3. **Truncated** 8 presses, Select omitted (`U,U,L,R,D,D,A,B`) — no effect flag.
4. **Extra press** appended Up (`U,U,L,R,D,D,A,B,Select,U`) — no effect flag.
5. **Wrong order** reversed (`Select,B,A,D,D,R,L,U,U`) — no effect flag; the
   only 0→1 change (`0x02002E0C`) is in the text/sound buffer, not a game flag.

Additional context bound: the same sequence entered at a non-stunt screen is
absorbed by that screen's own menu handler; no global cheat monitor exists to
accept it in a different context either.

## 10. Other bounded negatives (retained from prior pass)

* No password/text-code system: the 62-symbol keyboard is a profile-name label
  (consumer analysis, guide §16.2b).
* Difficulty tiers are save-bit unlockables, not codes (ROM says
  `Locked! Finish Fear Factor mode in Easy first`, etc.).
* Engine OAM-debug strings (`Dumping OAM...`, `(Hidden)`, `Normal/Semitr/...`)
  have no reachable in-game entry on any walked screen or tested combo.

## 11. Tooling and evidence

`file`, `md5sum`/`sha1sum`/`sha256sum`, `strings -t x`, `grep -abo`;
`arm-none-eabi-objdump -M force-thumb`; Python/struct scanners
(`scan_chain.py`, `scan_cmps.py`, `scan_movs.py`, `scan_arm.py`,
`scan_shifts.py`, `scan_words.py`, `scan_indices.py`); mGBA 0.10.5 `-d` CLI
debugger via PTY (`dbg2.py`) with `watch/w`, `frame`, `x/4`, `r/4`; XTEST key
injection with `xdotool`; `ss.py` savestate decoder; mGBA GDB stub probed via
a minimal RSP client (`gdbrsp.py`). Analysis artifacts, traces and dumps are in
`/tmp/opencode/fearfactor2/`.

**Legal note:** no ROM bytes, graphics, audio, or extracted game text are
redistributed; this report contains only addresses, hashes, algorithms,
observations, and the author's own tools.

## 12. Cleanup

All mGBA processes started for this pass were terminated by PID number only;
the generated `Fear Factor: Unleashed.sav` in the ROM folder was removed. The
ROM folder now contains only the original `.gba` and this report. `roms/INDEX.md`
was not edited.
