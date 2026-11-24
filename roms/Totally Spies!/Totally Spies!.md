# Totally Spies! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Totally Spies!.gba` (same folder as this report) |
| Size | 8,388,608 bytes (8 MiB) |
| Header title (0xA0) | `TOTALLYSPIES` |
| Game code (0xAC–0xAF) | `BTUE` |
| Maker (0xB0–0xB1) | `70` |
| Version (0xBC) | `0x00` |
| Complement (0xBD) | `0x0D` |
| Header checksum (0xBE–0xBF) | `0x0000` |
| Entry branch (0x00) | `0xEA00002E` → `0x080000C0` |
| Region/build | Europe multi-language (6 language banks: EN, DE, NL, ES, FR, IT) |
| MD5 | `0309e2dda3ec19ee11c2afb0c22ff3ef` |
| SHA-1 | `6452e8f16dec8db3d46f24bb242f8223e337ce40` |
| SHA-256 | `86e3b9d899afad71e441865aededdc4a6ce0c894bf68678b4166961e48fb9e7d` |

The entry word and first 4 KiB are stock (no cracktro/trainer patch observed; §16.1 checked).

## 2. Executive summary

**This GBA title has no in-game password/code-entry validator and no hidden/debug menu reachable by controller input.** The only developer-intended cheat-shaped content is a **Secrets** system: six fixed 5-character website passwords that the game *reveals* when the corresponding hidden in-game secret is found. The on-screen text is explicit — *"Visit www.totallyspies.com, enter your password and get your surprise!"* (0x0860A644) — so the passwords are consumed by the (now defunct) website, not typed into the GBA.

All six passwords were recovered from the ROM text bank and are listed in §6. Every reachable screen was walked in mGBA with screenshots and savestate RAM diffs; none offers a text/code entry field. The sole "PASSWORD" string in the ROM (0x0860B5BA, plus Italian 0x0862407B) is the label of a **gameplay hacking minigame** ("Memorize the sequence of the symbols" / "Shoot! Wrong password. Let's try again!"), not a cheat screen.

The result is therefore a **bounded negative with counts** (§6b): 4,695 printable strings decoded from the text bank, exactly 36 code-like 5-character tokens (6 passwords × 6 languages) and nothing else, zero code-entry UI strings, zero direct pointer/Thumb-literal references to the password strings from code, zero hits for standard button-code mask sequences, and 11 distinct screens walked. Per §0.2 no novel code can be minted or entered because no validator or entry surface exists.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba -3 -g`), Xvfb `:316`, `SDL_AUDIODRIVER=dummy`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
* Boot → Atari splash → title "PRESS START" → Start → main menu.
* Menu path for the relevant content: main menu → **Secrets** (4th entry) → "SECRET ZONE" (shows 6 `LOCKED` rows and an empty message box). Gallery → **Image Gallery** (six `??????` rows, first viewable). Options → MUSIC/SFX/CREDITS. New Game → Choose a Story (2 stories available: The Aptitude Test, Save the Earth) → Choose a Level (first level playable, remaining rows `??????`).
* Screenshots and scripts were in `/tmp/totallyspies/` (`menu.png`, `secrets.png`, `gallery.png`, `gal_view.png`, `options` in `sz3.png`, `ng1.png`, `levels.png`, `pause0.png`, `konami.png`, `sz_state.png`; scripts `scan.py`, `scan2.py`, `masks.py`, `final_stats.py`, `ssdiff.py`).

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Header | 0x000000 | 0x08000000 | code `BTUE` at 0xAC |
| Text bank (ASCII, NUL-terminated) | 0x600000–0x62FFFF | 0x08600000–0x0862FFFF | 4,695 printable strings ≥3 chars |
| "Visit www.totallyspies.com…" | 0x60A644 | 0x0860A644 | proves website consumption |
| "Secret 1 : Locked" … "Secret 6 : Locked" | 0x60A68C–0x60A6F7 | 0x0860A68C–0x0860A6F7 | 6 display literals |
| "Secret 1 : H1R4N" … "Secret 6 : Z4L6D" | 0x60A6F8–0x60A760 | 0x0860A6F8–0x0860A760 | the 6 passwords, English |
| "PASSWORD" (hacking minigame label) | 0x60B5BA | 0x0860B5BA | not a cheat screen |
| "Shoot! Wrong password…" | 0x60C0F9 | 0x0860C0F9 | minigame failure text |
| Save image | — | SRAM/Flash | 512-byte `.sav`, begins with a header containing `BTUE` |

RAM evidence (mGBA savestate `gbAs` chunk, §16.13): state offsets map IWRAM at 0x19000 → `0x03000000`, EWRAM at 0x21000 → `0x02000000`. Diffing the main-menu state (`ss2`) against the Secret-Zone state (`ss3`) gives 33,218 differing bytes overall but only 35 in the first IWRAM page. Examples (Observed):

| RAM | main menu | Secret Zone |
|---|---|---|
| `0x03000980` | `FF FF FF FF` | `02 00 00 00` |
| `0x03000D08` | `A4 1C 00 02` | `B8 1C 00 02` |
| `0x02000848` | `F0 22 00 03` | `2C DB 00 02` |

This confirms each walked screen is a distinct live RAM state, not a static image.

## 5. Algorithm

No password validator, checksum, generator, or button-code matcher exists in this build. There is therefore no algorithm to reimplement.

The only logic is a **reveal gate** for the unlockables, observed as:

```
if secret[i].found_in_game:  display "Secret i : <fixed 5-char password>"
else:                        display "Secret i : Locked"
```

The six passwords are literal strings appended to the localized "Secret i : " labels; the D-pad and A/B buttons have no effect on the Secret Zone screen (tested: Down, Left, Right, A all leave the screen unchanged). This is an unlockable *display* system (§16.3 category 4: gated content, gate is an in-game find) — not a code system.

## 6. Tables

### 6.1 The six developer passwords (English bank, 5 chars each)

| # | Password | File offset | ROM address | Alphabet |
|---:|---|---:|---:|---|
| 1 | `H1R4N` | 0x60A703 | 0x0860A703 | digits + uppercase |
| 2 | `J5P2K` | 0x60A714 | 0x0860A714 | digits + uppercase |
| 3 | `9NM23` | 0x60A725 | 0x0860A725 | digits + uppercase |
| 4 | `P7S3H` | 0x60A736 | 0x0860A736 | digits + uppercase |
| 5 | `8J1K2` | 0x60A747 | 0x0860A747 | digits + uppercase |
| 6 | `Z4L6D` | 0x60A758 | 0x0860A758 | digits + uppercase |

Each occurs **exactly 6 times** in the ROM — once per language bank, always inside a localized display string. Confirmed contexts: EN `Secret N : XXXXX`; DE `Geheimnis N: XXXXX`; NL `Geheim N: XXXXX`; ES `Secreto N: XXXXX`; FR `Secret N : XXXXX`; IT `Segreto N: XXXXX`. No UTF-16LE or byte-reversed copies (0 hits each).

### 6.2 Unlockable inventory (all observed in-game)

| Surface | Total | Initially available | Gate |
|---|---:|---:|---|
| Stories | 5 (names in text bank) | 2 | "New Story unlocked!" after story completion |
| Levels (Save the Earth) | 6 rows shown | 1 | progress; remaining rows render `??????` |
| Image Gallery | 6 | 1 viewable | in-game finds; remaining rows render `??????` |
| Secrets / website passwords | 6 | 0 | in-game secret pickups |

### 6.3 UI strings proving the absence of an entry field

English bank labels at 0x0860A3B0–0x0860A7F7: `Press START`, `New Game`, `Continue`, `Gallery`, `Options`, `Secrets`, `Credits`, `Music`, `SFX`, `Off`, `Choose a Story`, `Choose a Level`, `Image Gallery`, `Special Gallery`, `??????`, `Quit Game`, `Secret Zone`, `Secret N : Locked`, `Secret N : <code>`, `Scroll`, `Change`, `Objectives`, `Gadgets`, `View`, `On/Off`, `Yes`, `Next`, `Back`, `OK`, `Play`, `Items`, `No description`. None denotes code entry, cheat, debug, or level-select-by-code.

## 6b. Enumeration

**Code space.** There is no algorithmic code space. The complete set of 5-character tokens usable as "codes" in this title is the six fixed literals in §6.1; they are display-only. Formally: alphabet observed = `0-9 A-Z`, length 5, no checksum field, no generator, no validator, no input buffer. Representable set emitted by the game = **6 strings**; all other 5-character strings have **zero** occurrences in the ROM text bank or anywhere else.

**Novel codes.** None generated, because no code can be minted or entered: there is no entry UI on any reachable screen and no validator to call. This is the §0.2 bounded-negative branch, not an omission.

**Counts supporting the bounded negative (all Observed/Derived):**

| Check | Result |
|---|---|
| Printable ASCII strings ≥3 chars in text bank (0x8600000–0x862FFFF) | 4,695 |
| 5-char mixed letter+digit tokens in text bank | 36 = 6 passwords × 6 languages; no others |
| Literal occurrences of each password in whole 8 MiB ROM | 6 each (all in localized display strings) |
| UTF-16LE / reversed occurrences | 0 each |
| Direct 32-bit pointers or Thumb PC-relative literal loads to the password string addresses | 0 (text is referenced bank-relatively, not by direct pointer) |
| Keyword hits for `DEBUG`, `CHEAT`, `LEVEL SELECT`, `ENTER CODE`, `ENTER PASSWORD`, `MASTER`, `WARP`, `INVINCIBLE`, `INFINITE` | 0 |
| `PASSWORD` / wrong-password strings | 2 / 1 — all hacking-minigame text |
| Konami-style button sequences (2 mask conventions × 2 orders × 2 polarities × u8/u16) | 0 hits in u16; u8 hits are random-data coincidences, not tables |
| Runs of ≥5 consecutive single-button u16 masks | 98, all in ordinary code/data where immediates 1/0x100 are common; no validator-like table |
| Distinct live screens walked | 11 (title, main menu, Secrets/Secret Zone, Image Gallery, gallery VIEW, Options, Objectives, Choose a Story, Choose a Level, gameplay, title-code test) |
| Button codes pressed on title screen | Konami (↑↑↓↓←→←→ B A) and L+R+Start → no visual or state change |

**Rejection bounds.** There is no in-game rejection because there is no in-game submission path — this is itself the bounded result. At the ROM level the bound is exact: the accepted-set size is 6 fixed strings; a 37th 5-character code-like string does not exist in any of the 4,695 decoded strings. The English Secret Zone screen with all six rows `LOCKED` and an inert empty message box (screenshot `secrets.png`) is the observed proof that no entry widget is present.

**In-game rejection of a novel code was attempted and is impossible by design:** the only text-adjacent input surface, the hacking minigame, accepts a repeated *button-symbol sequence* generated by the game itself, not a player-authored string.

## 7. Validation evidence

* **Observed** — mGBA screenshots of every screen listed in §3; Secret Zone ignoring Down/Left/Right/A; Konami code and L+R+Start having no title-screen effect; 512-byte `.sav` contents; savestate `gbAs` RAM diffs with the address/value table in §4.
* **Derived** — exact string extraction with offsets and context from the raw 8 MiB image; the 36-token count; the 0-pointer/0-literal result from the pointer and Thumb-LDR scans; the mask-sequence scan results.
* **Inferred** — that the six passwords were intended for the `www.totallyspies.com` promotion (based on the explicit on-screen instruction; the site itself is not reachable/tested); that the secret pickups, not any input, set the reveal flags (based on the "Yipeee! I found a secret!" message and gated display).

## 8. Unknowns

* Exact in-world locations of the six secret pickups were not exhaustively searched; finding one would confirm the flag→reveal path dynamically.
* The website-side behavior of the six passwords is unverifiable (site defunct).
* The engine accesses its text bank through bank-relative IDs; the full ID table was not mapped. The negative does not rest on that mapping — it rests on the decoded string inventory, UI enumeration, and absence of any entry surface.
* GDB stub on port 2345 was occupied by other concurrent mGBA sessions, so RAM reads used savestate diffs instead; no software breakpoint was available to observe the reveal routine directly.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd`, Python 3 `struct`/`re` scripts in `/tmp/totallyspies/` (`scan.py`, `scan2.py`, `masks.py`, `final_stats.py`, `ssdiff.py`).
* `arm-none-eabi-objdump` and Capstone were available for disassembly but no candidate validator was found to disassemble.
* mGBA 0.10.5 under Xvfb `:316` with `SDL_AUDIODRIVER=dummy`; `xdotool` for input, `scrot` for screenshots; Python `zlib` for mGBA `gbAs` savestate extraction (§16.13).

No ROM bytes or copyrighted assets are reproduced in this report beyond short, non-copyrightable literal code strings and addresses required for reproduction.

---

*Coordinator note: per instruction, `roms/INDEX.md` and `GBA_REVERSE_ENGINEERING_GUIDE.md` were not modified.*
