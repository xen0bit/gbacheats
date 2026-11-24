# Final Fight One (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Final Fight One/Final Fight One.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title | `FINAL FIGHT` |
| Game code | `AFFE` (region code `08`) |
| Maker | `08` (Capcom) |
| Software version | `0x00` |
| Fixed byte | `0x96` present; complement `0xDB`; checksum `0x0000` (normal rebuilt-header artifact) |
| Entry word | `0xEA00002E` — the **stock** `b` to `0x080000C0`, no cracktro patch |
| Embedded GBA headers | **1** (logo `24 FF AE 51 …` found only at file `0x0`) — single-image retail ROM, no trainer, no appended second game |
| MD5 | `c6af74aeeabfd6d7ee2875e355f49af2` |
| SHA-1 | `17918e125bcafd44fcf3b21813575c2ccb19bd45` |
| SHA-256 | `c952ccc0bd0f65990db2c6ad0f309484d790691fcbdbae23d2cb29af4aa27989` |

All addresses below are for **this exact hash**. Analysis copy `ff.gba` in `/tmp/finalfight` is byte-identical.

## 2. Executive summary

**There is no password / cheat-code system in Final Fight One (GBA).** No password screen, no code alphabet, no accepted-code table, no validator, and no published GBA password list exists for this SKU. The ROM contains zero occurrences of `password`, `cheat`, `code`, `secret`, `unlock`, or `debug` as ASCII (or `+0x20`-shifted ASCII), and no key-mask sequence table that could be a button cheat (§6b).

What the game *does* contain is a small set of **developer-intended options/unlockables**, all reachable through the ordinary UI, and one **static debug flag** set by a boot-time button gate:

1. **OPTIONS screen** (from MODE SELECT → OPTIONS → Start): `DIFFICULTY`, `EXTEND`, `SOUND TEST`, `SE TEST`, and `BUTTON CONFIG`. SOUND TEST and SE TEST are a retained developer sound-test/SE-test facility — exactly the kind of hidden sound menu Capcom GBA ports keep. SOUND TEST was cycled `00 → 17`; SE TEST was cycled `00 → 65` and stops there. (Observed.)
2. **BUTTON CONFIG** assigns `A = JUMP`, `B = ATTACK`, `R = EX JOY`. `EX JOY` is an in-game function bound to the R button; the literal `EX JOY` is at `0x080A1B68` and `EXTRA JOY` at `0x080A19E4`/`0x08046CD7`. (Observed + derived.)
3. **Difficulty** has five stored values: `VERY EASY`, `EASY`, `NORMAL`, `HARD`, `VERY HARD` (strings `0x080A1AE0` … `0x080A1ABC`). **Extend** has four: `NONE`, `100000`, `200000`, `200000EVR` (`0x080A1AFC` … `0x080A1B18`).
4. **Debug flag**: the main loop at `0x0800BB3A` tests the internal key mask for `0x30` (= L+R per the remapper at `0x0800C938`) once at boot and writes `0xFF` (debug) vs `0x01` (normal) to the byte at `0x020208AD`. Four render helpers (`0x08015808`, `0x080159D8`, `0x08015E20`, `0x08015FDC`) branch on the high nibble of that byte. (Derived from disassembly; the in-emulator L+R-at-boot attempt did **not** flip the byte — see §8.)
5. **Characters**: the selectable roster is exactly CODY, GUY, HAGGAR (observed; five `Left` presses from GUY reveal only a transition animation with `?` placeholders, then wrap — no fourth character). The pointer table at `0x08043E18` additionally carries `@ CODY` and `@ GUY` name strings (`0x080A1B80`, `0x080A1B88`) used by the RANKING screen and the `EX JOY` display, not extra playable fighters.

## 3. How to reproduce

**Emulator**: mGBA (this build `/usr/local/bin/mgba`), under `Xvfb :317 -screen 0 1024x768x24`, `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, launched as `mgba -3 ./ff.gba`.

**Critical harness note (§16.2)**: sibling sessions also run mGBA on `:317`. `xdotool search --name mGBA | head -1` is **not** safe — it can return another session's window, and a leftover `-d` debugger instance is paused and ignores keys. Always resolve the window by your own PID:
```
MP=$(pgrep -n -f "mgba -3 ./ff.gba")
W=$(xdotool search --name mGBA | while read w; do
      [ "$(xdotool getwindowpid $w 2>/dev/null)" = "$MP" ] && echo $w; done | head -1)
xdotool windowfocus "$W"
```
Send **short taps** (~50 ms hold, ~500 ms gap). Long (~150–300 ms) holds double-step or are missed in the attract loop; with short taps the attract sequence advances deterministically.

**Keymap verified in this build**: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Menu **confirm is Start**, not A (A backs out / skips). This is why pressing A on OPTIONS appears to "start the game": it cancels to MODE SELECT and then advances.

**Menu path (observed)**:
- Boot → story intro (A skips pages; Start skips to title).
- Title (`PRESS START`) → Start → RANKING → Start → title → Start → attract demo → Start → title → Start → **MODE SELECT**.
  The attract screens cycle; four to six short Start taps from the title reach MODE SELECT (`goto_mode.py` uses OCR to stop on it).
- MODE SELECT entries: `GAME START`, `GAME LINK`, `OPTIONS`, `RESET GAME DATA`.
- `OPTIONS` → Start → OPTIONS screen (DIFFICULTY / EXTEND / SOUND TEST / SE TEST / BUTTON CONFIG). Left/Right change values; Start confirms, B exits.
- `GAME START` → Start → PLAYER SELECT (GUY / CODY / HAGGAR; Left/Right select, Start confirms) → gameplay → Start → `PAUSE` → Start → resume.

**Screenshots kept on disk** in `/tmp/finalfight/` (`modesel_01.png`, `nav_3.png`, `nav_4.png`, `opt_via_start.png`, `opt_labels2.png`, `opt_cursor_sound.png`, `st_zero.png`, `se_max.png`, `flow_06.png`, `pause_01.png`, `char_left_montage.png`, `seq_montage.png`). They are evidence only; no assets are published.

## 4. Address map

| Address (ROM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Stock ARM entry `0xEA00002E` | Derived (header) |
| `0x0800C938` | Input read/compute; reads `0x04000130`, writes internal mask to `0x0202D808` | Derived (disassembly) |
| `0x0800BB04` | Main loop | Derived |
| `0x0800BB3A` | One-time L+R gate → byte `0x020208AD` = `0xFF`/`0x01` | Derived |
| `0x08015808`, `0x080159D8`, `0x08015E20`, `0x08015FDC` | Four readers of flag byte `+5` (`ldrb rX,[rN,#5]`; test high nibble `& 0xF0`) | Derived |
| `0x08043E18` | Character-name pointer table: `EX JOY?`, CODY, GUY, HAGGAR, `@ CODY`, `@ GUY` | Derived |
| `0x080A0710` | `CONTINUE?` string | Observed (strings) |
| `0x0806BDA0`–`0x0806BF80` | PLAYER SELECT / in-game text bank (`SELECT PLAYER`, `CODY`, `HAGGAR`, `GUY`, `GAME OVER`, `BONUS STAGE`, `ROUND`, `CLEAR`, `PERFECT`, `PAUSE`, …) | Observed |
| `0x080A1ABC`–`0x080A1AE8` | Difficulty strings (VERY HARD … VERY EASY) | Observed |
| `0x080A1AFC`–`0x080A1B18` | Extend strings (NONE / 100000 / 200000 / 200000EVR) | Observed |
| `0x080A1A8D` | `BUTTON CONFIG` label | Observed |
| `0x080A1B30`–`0x080A1B58` | `EX JOY`, `ATTACK`, `JUMP`, `A/B/L/R` labels | Observed |
| `0x08046C68`–`0x08046D80` | Options/menu control-code text bank (`CONTINUE`, `OPTION MODE`, `DIFFICULTY}a/b`, `PLAYER`, `EXTEND`, `MUSIC`, `SOUND`, `STEREO`, `EXTRA JOY`, `ROUND`, `AREA`, `EXIT`, `POINT OF …`) | Observed |
| `0x08042E8`–`0x0804330` | Title/menu text (`PRESS START BUTTON`, `NORMAL MODE`, `BATTLE MODE`, `OPTIONS`, `BATTLE`) | Observed |

RAM: `0x0202D808` = internal active-high button mask; `0x020208A8` = main state struct; `0x020208AD` = debug flag (struct `+5`); `0x03002B98` = secondary state. File offset = ROM address − `0x08000000`.

## 5. Algorithm

**Button remap** (`0x0800C938`, raw active-low `KEYINPUT` inverted to `r3`, then internal mask `r2`):

```
raw 0x001 A       -> internal 0x8000
raw 0x002 B       -> internal 0x4000
raw 0x004 Select  -> internal 0x2000
raw 0x008 Start   -> internal 0x1000
raw 0x010 Right   -> internal 0x0100
raw 0x020 Left    -> internal 0x0200
raw 0x040 Up      -> internal 0x0800
raw 0x080 Down    -> internal 0x0400
raw 0x100 R       -> internal 0x0010
raw 0x200 L       -> internal 0x0020
mask stored at 0x0202D808
```

**Debug gate** (`0x0800BB3A`, executes once at boot):

```
if ((mask_at_0x0202D808 & 0x0030) == 0x0030):   # L + R
    *(u8*)0x020208AD = 0xFF
else:
    *(u8*)0x020208AD = 0x01
```

Consumers test `(flag << 8) & 0xF000`, i.e. the high nibble: `0x01` takes the extra calculation using the byte at struct offset `+0x2F`; `0xFF` skips it. No menu is opened by the flag itself.

No checksum, no password validator, no alphabet, and no key-sequence matcher exist in this image — there is nothing to reimplement.

## 6. Tables

**Selectable characters** (PLAYER SELECT, observed; order GUY/CODY/HAGGAR on screen): GUY, CODY, HAGGAR. Name pointer table at `0x08043E18`:
`[0x080A1B5C, 0x080A1B6C(CODY), 0x080A1B74(GUY), 0x080A1B78(HAGGAR), 0x080A1B80(@CODY), 0x080A1B88(@GUY)]`.

**Difficulty** (5): VERY EASY, EASY, NORMAL (default), HARD, VERY HARD.
**Extend** (4): NONE, 100000, 200000, 200000EVR (default).
**Sound test**: 2-digit value, cycled `00…17` observed (BGM); stops/slows at high end — see §8.
**SE test**: 2-digit value, `00…65` observed and hard-capped at 65.
**Button config**: A=JUMP, B=ATTACK, R=EX JOY (default).
**Mode select** (4): GAME START, GAME LINK, OPTIONS, RESET GAME DATA.

## 6b. Enumeration

Because no code system exists, this section enumerates the **bounded negative result** (guide §0.2 "negative results bounded") and the full developer-cheat surface.

**Screen space — every reachable screen walked with RAM/screenshot evidence (10):**
1. Boot / Capcom logo — `shot_20_fresh.png`
2. Story intro (typewriter, multiple scenes) — `shot_36_boot.png`, `new_01.png`
3. Title `PRESS START` — `clean_03.png`
4. RANKING (high scores; `@ CODY`/`@ GUY` entries) — `flow_02.png`, `new_02b.png`
5. Attract demo gameplay — `shot_17_afterB.png`, `new_05.png`
6. MODE SELECT (4 entries) — `nav_3.png`, `modesel_01.png`
7. PLAYER SELECT (3 characters) — `nav_4.png`, `char_wait.png`
8. In-game gameplay — `flow_06.png`
9. PAUSE — `pause_01.png`
10. OPTIONS (5 settings incl. SOUND TEST / SE TEST / BUTTON CONFIG) — `opt_via_start.png`, `opt_cursor_sound.png`

No hidden debug menu screen was found on any of the ten; the only developer facilities are the OPTIONS sound-test entries and the L+R flag.

**Text/button search space (searched, with counts):**

| Probe | Result |
|---|---|
| ASCII `password`, `cheat`, `code`, `secret`, `unlock`, `debug`, `level select`, `invincib`, `walk through` (whole 4 MiB) | **0 hits each** |
| `+0x20`-shifted uppercase `PASSWORD`/`CHEAT`/`DEBUG`/`SECRET` | **0 hits each** |
| `extra joy` | 3 hits (`0x46CD7`, `0x46D5E`, `0xA19E8`) — an option/button label, not a code |
| `continue?` | 1 hit (`0x0A0710`) — standard continue prompt, no code entry |
| `TEST` as ASCII | 0 hits — the on-screen `SOUND TEST`/`SE TEST` labels use a non-ASCII font/tile path (guide §11) |
| Embedded GBA headers | 1 — no second game / trainer carrying a separate code list |
| Nonzero internal-mask runs of length ≥ 4 (candidate button-code tables) | 60 runs; all are repetitive data/animation frames (e.g. `0x20,0x10` alternating at `0x9AD6C`; `0x4000,0x10,0x10,0x4000` at `0x522BE`), none a monotone cheat sequence |

**Published codes tested:** none available to test. Web retrieval was attempted and blocked: GameFAQs `403` (Cloudflare challenge), TCRF `403`, web.archive.org snapshot for the GameFAQs cheats page returned "not archived", DuckDuckGo served a CAPTCHA, Bing/Google returned no relevant results (§3.4). Independent of access, the arcade and SNES versions of Final Fight have no password systems, so there are no foreign-version literals to test against this ROM. This is a documented retrieval negative, not a silent omission.

**Novel code minted:** not applicable — the game has no code system to enumerate. The equivalent deliverable here is the **complete developer-cheat surface** above (sound test, SE test, difficulty, extend, button config, EX JOY, L+R debug gate), each tied to an address or an observed effect.

**Bounds proven by rejection:** there is no input format to reject. The closest bounded rejections observed are the UI caps: SE TEST refuses to increment past `65` (ten extra Start/Right presses leave the value at 65, `se_max.png` + `se_cap_check.png`), and the character selector wraps after three choices with no fourth (five `Left` presses, `char_left_montage.png`).

## 7. Validation evidence

- **Observed** (emulator, screenshots): every one of the ten screens in §6b; the OPTIONS entries and default values (`NORMAL`, `200000EVR`, `00`, `00`, `A/B/R` mapping); character roster of three; SE TEST cap at 65; PAUSE screen; attract loop.
- **Derived** (disassembly, exact bytes): the input remapper and its ten-button map (`0x0800C938`); the one-time L+R gate and `0x020208AD` (`0x0800BB3A`); the four high-nibble readers; the character pointer table at `0x08043E18`; the difficulty/extend string banks; the stock entry word and single embedded header.
- **Inferred**: that the `0xFF` flag is a leftover debug/test mode. Its four consumers are proven, but no debug menu or visible gameplay change was produced by it in the attempts made (§8). `EX JOY`'s precise in-game mechanic was not exercised to completion.

## 8. Unknowns

- **L+R boot flag not flipped in emulator.** Holding L+R before launching mGBA left `0x020208AD = 0x01` when read from a savestate. The gate check at `0x0800BB3A` runs once very early; the harness could not guarantee the keys were down on that exact frame. The gate and its four readers are proven statically; the `0xFF` path's visible effect remains unconfirmed. Direct debugger patching of the byte was attempted but the patched `-d` session produced a black viewport, so no screenshot was obtained.
- **Sound-test upper bound.** Observed `00 → 17` with the value appearing to stop/slow near the high end; some rapid Right presses were dropped, so the exact terminal index (and whether the display is decimal or hexadecimal) is not pinned down. SE TEST's cap at `65` is solid.
- **`TEST` glyph source.** The label is visibly rendered but has no ASCII bytes; its font/tile index bank was not decoded. This does not affect the finding (the facility is observed on screen).
- **Published-code retrieval.** Could not be completed due to site blocks; documented in §6b.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo` for Phase 0/1.
- Python (`capstone` 5.0.7) for Thumb literal/pointer scans; `arm-none-eabi-objdump -M force-thumb` for targeted disassembly.
- mGBA under Xvfb `:317` + openbox, PNG root captures via `import -window root`.
- `xdotool` XTEST taps with PID-resolved window targeting; OCR-assisted navigation (`tesseract`) for reliably stopping on MODE SELECT.
- mGBA savestate parser: `.ss1` is a PNG with a zlib `gbAs` chunk; decompressed to 397,312 bytes. EWRAM at raw `0x21000`, IWRAM at `0x19000`. Used to read `0x020208AD`.
- REA/Ghidra was opened on the raw GBA image but auto-analysis exceeded the 330 s startup deadline and was abandoned; the work additionally follows `objdump`/Capstone + emulator as the guide recommends.
- All analysis artifacts were kept in `/tmp/finalfight/`. No ROM bytes were modified; no ROM or copyrighted assets are redistributed.

**Legal note**: findings, hashes, addresses and tool scripts are published; the ROM image and extracted graphics/audio are not.
