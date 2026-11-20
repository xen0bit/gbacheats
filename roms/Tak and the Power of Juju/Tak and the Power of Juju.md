# Tak and the Power of Juju (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tak and the Power of Juju.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `TAK&JUJUENG` |
| Game code | `BJUE` |
| Maker code | `78` (THQ) |
| Version | `0x00` |
| Fixed byte / complement / checksum | `0x96` / `0x9E` / `0x0000` |
| Entry word | `0xEA00002E` (standard `b 0x080000C0`) |
| MD5 | `438be22c9e03529e2a03779a00d17b62` |
| SHA-1 | `6d34590d88c541650a7bd2e17a338de82c5e84cb` |
| SHA-256 | `b1dea3c30fd2d2d3c9602eeb0b7b9b60e313707084a8ce667d52f11c94fac6bb` |

The header checksum is `0x0000`, a common rebuilt-header artifact (guide §16.1). The
complement byte is `0x9E`. No scene-release cracktro or appended trainer was found:
the entry word is the stock branch and the boot path shows the normal THQ/Nick/Helixe
logos and story intro.

**SKU check (guide §16.11):** The widely published cheats for this title are
PS2/GameCube **button sequences** ("Left, Right, B, B, X, X, Left, Right" etc.). They
belong to the Avalanche console SKU, not this Helixe GBA image. No GBA password list
was found in four web searches or on the GameFAQs GBA cheats page (403; snippets only).

## 2. Executive summary

The GBA image **does contain a developer-intended password feature**, proven by plaintext
UI strings in the ROM: a main-menu item `Password`, a `Level Password` sub-screen with
the prompt `Press A to add a letter, B to erase`, and the result messages
`Password accepted` / `Invalid password`. A level-name bank with 38 named levels and
15 cinematic/special level records is also present.

However, **no code system could be characterised**: no published GBA codes exist, no
plaintext password table or non-standard password alphabet exists anywhere in the
8 MiB image, and the validator/input buffer were not isolated. Consequently **no novel
code was minted or verified** — this engagement is a bounded negative over the
searched spaces, not a solved password system. The Password screen itself was never
reached in the emulator, so the feature is classed as *gated/unknown* (guide §16.3
category 4) rather than "absent". All counts and bounds are in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, Xvfb `:319`, openbox, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap verified by observation: `A = x`, `Start = Return` (also `KP_Enter`),
  `Select = BackSpace`, `L = a`, `R = s`.
* Boot sequence observed repeatedly: story text pages → Nick Games logo → Helixe logo
  → **title screen** (`PRESS START`, ~12 s) → THQ Presents → story text again
  (a repeating cycle unless a button is pressed at the title).
* A title-screen detector (crop `720x480+152+144`, count orange pixels of the Tak
  logo) was used to press buttons exactly during the title window.
  - `BackSpace` (Select) at title → Nick Games logo (skips story).
  - `KP_Enter` at title → Nick Games logo.
  - `Return` at title → fade → title again.
  - `L+R+Return` at title → no change.
  - No tested input reached the `Password` screen; the gate is unknown.
* Debugger: mGBA `-d` CLI debugger, driven through a Python `stdbuf -o0` pipe
  controller (the GDB stub handshake was unreliable: "Ignoring packet error").
* Savestates: mGBA `.ss1`/`.ss2`; `gbAs` PNG chunk decompressed with `zlib` to a
  397,312-byte raw state (IWRAM at raw `0x19000`, EWRAM at raw `0x21000`).

## 4. Address map

| ROM file offset | ROM address | Meaning |
|---:|---:|---|
| `0x47EB2C`–`0x47ECCD` | `0x0847EB2C`–`0x0847ECCD` | Plaintext main-menu / password text bank |
| `0x47EB3F` | `0x0847EB3F` | `"Main Menu"` |
| `0x47EBB3` | `0x0847EBB3` | `"Password"` (menu item) |
| `0x47EC5E` | `0x0847EC5E` | `"Level Password"` (screen title) |
| `0x47EC85` | `0x0847EC85` | `"Press A to add a letter, B to erase"` |
| `0x47ECB2` | `0x0847ECB2` | `"Password accepted"` |
| `0x47ECBC` | `0x0847ECBC` | `"Invalid password"` |
| `0x3DF0C`–`0x3E2CC` | `0x083DF0C`–`0x083E2CC` | Level-name bank: `sheep_level`, `death_level`, `menu_level`, `cinematic_1..13`, 38 level names (`Tlaloc Castle 8-6` … `Jungle 1-1`), `demo_level`, `empty` |
| `0x482BD4`–`0x482D3C` | `0x08482BD4`–`0x08482D3C` | 15 level-info records, 24-byte stride: `{u32 0x00020xFF, ptr, ptr, name_ptr, id, 0}` |
| `0x294398` | `0x080294398` | Text-offset table, 400 `u32` entries, base `0x47E000` (e.g. `0xC85`→`"Press A…"`, `0xCBC`→`"Invalid"`) |
| `0x3D5958`+ | `0x0803D5958`+ | Second text-offset table; `0xC5E` (`"Level Password"`) at index 428 (`0x3D6008`) |
| `0x7530C`+ | `0x0807530C`+ | 8-byte text records `{u16 id, u16 0, u16 ?, u16 offset}` interleaved with a `u16` offset array |
| `0x2D998` | `0x0802D998` | Keypad reader: reads `KEYINPUT` (`0x04000130`), dispatches 10 keys to `0x0802D818` |
| `0x2D818` | `0x0802D818` | Key-event dispatcher; writes pressed/held state to IWRAM (`0x0302D8xx`) |
| `0x7A0FF`, `0x7B1FF`, `0x7C0E1` | `0x087A0FF`, … | Standard C-library ASCII tables (`ABCDEFGHIJKLMNOPQRSTUVWXYZ`) — **not** password alphabets |

Observed RAM: input state lives in IWRAM around `0x0302D800`–`0x0302D900`; the
savestate diff between title and intro touched ~1,486 IWRAM bytes and ~10,045 EWRAM
bytes (mostly animated graphics), with no single dominant "screen state" byte isolated.

## 5. Algorithm

Not recovered. The ROM uses a 16-bit text-offset system (bank base `0x47E000`) rather
than direct string pointers, so `strings`/pointer scans cannot by themselves find the
screen handler. No validator, checksum, alphabet mapping, field layout or generator was
identified. **No pseudocode can be given without fabricating it.**

## 6. Tables

Level-name bank (selected; full bank `0x3DF0C`–`0x3E2CC`):

| Offset | String | Offset | String |
|---:|---|---:|---|
| `0x3DF0C` | `sheep_level` | `0x3E284` | `Jungle 1-6` |
| `0x3DF18` | `death_level` | `0x3E290` | `Jungle 1-5` |
| `0x3DF24` | `menu_level` | `0x3E29C` | `Jungle 1-4` |
| `0x3DF30`–`0x3DFD0` | `cinematic_13` … `cinematic_1` | `0x3E2A8` | `Jungle 1-3` |
| `0x3DFDC`–`0x3E040` | `Tlaloc Castle 8-6` … `8-1` | `0x3E2B4` | `Jungle 1-2` |
| `0x3E054`–`0x3E0A4` | `Sun Temple 7-6` … `7-1` | `0x3E2C0` | `Jungle 1-1` |
| `0x3E0B4`–`0x3E120` | `Canyons 6-5` … `6-1` | `0x3E2CC` | `demo_level` |
| `0x3E130`–`0x3E220` | `Chicken Island 4-5` … `Tree Village 2-5` | `0x3E358` | `empty` |

Text-ID examples from the 400-entry table at `0x294398`: index 399 → `0xC85`
(`"Press A to add a letter, B to erase"`), index 407 → `0xCBC` (`"Invalid"`).
`"Level Password"` (`0xC5E`) is present in the second table at `0x3D6008`, index 428.

## 6b. Enumeration

**Space size: NOT DETERMINED.** Because no validator, alphabet, length or checksum was
isolated, the representable code space cannot be stated. No novel code was generated,
entered or RAM-verified, and no in-game rejection of an out-of-range value was
observed. This section therefore records a **bounded negative over the searched
spaces**, with exact counts (guide §0.2 item 5 and §16.3 category distinctions).

| Search | Space checked | Result |
|---|---|---|
| Published codes (web) | 4 searches + GameFAQs GBA cheats page | **0** GBA password codes. All published cheats are PS2/GC button sequences for a different SKU. |
| `strings -t x -n 4` | whole 8,388,608-byte ROM | 76,317 strings; password-related hits: **7** (`Main Menu`, `Password`, `Level Password`, `Press A…`, `Password accepted`, `Invalid password`, plus `Level Password` duplicate) |
| Non-standard 26-letter ASCII alphabet permutation | every byte offset in all 8,388,608 bytes | **3** hits, all standard C-library tables at `0x7A0FF`, `0x7B1FF`, `0x7C0E1`; **0** custom password alphabets |
| Direct `u32` pointer to any of 5 password UI strings | whole ROM | **0** hits |
| Ghidra string xrefs for 5 password UI addresses | whole analyzed image | **0** xrefs each |
| `u32` pointers into text bank `0x0847E000`–`0x0847F000` | whole ROM | **0** hits |
| Thumb `LDR literal` / `adr` refs to `0x080293000`–`0x080296000` | whole ROM, every 2 bytes | **0** hits |
| `KEYINPUT` literal `0x04000130` | whole ROM | **4** hits; 2 real code refs found (`0x0802D99A`, `0x0802DAAA`) |
| Level-name table | `0x3DF0C`–`0x3E2CC` | 13 cinematic/special + **38** named levels + `demo_level`/`empty` |
| Level-info records | `0x482BD4`–`0x482D3C` | **15** records, 24-byte stride; no password field observed |
| Screens walked | boot story pages, THQ Presents, Nick logo, Helixe logo, title `PRESS START`, in-game demo scene | **6** screen types; Password screen **not reached** |

**What the negative does and does not prove.** It proves that:
1. there is no published GBA password list to confirm;
2. there is **no plaintext password table** and **no non-standard ASCII alphabet** in
   this exact ROM image;
3. the UI strings are referenced through a 16-bit text-offset system, not direct
   pointers, so a naive pointer scan is not evidence of absence.

It does **not** prove that the game has no validator. The UI strings prove a password
feature exists; the validator remains unisolated and the entry screen remains gated.
A future analyst should start from `0x0802D818` (key dispatch) → IWRAM `0x0302D8xx`
and trace reads of the pressed-key word into the menu/screen state machine, or locate
the text-drawing routine that consumes the 400-entry table at `0x080294398`.

## 7. Validation evidence

* **Observed:** ROM hashes/header (§1); all cited strings and tables (§4/§6); six
  emulator screen types across repeated boot cycles; button effects at the title
  window; `.ss1`/`.ss2` savestate RAM diffs; Ghidra string inventory (1 hit for
  `"Level Password"`) and 0 xrefs for 5 UI strings.
* **Derived:** text-offset base `0x47E000` from the 400-entry table at `0x294398`;
  level-info record stride 24 bytes from repeated `0x00020xFF` markers; input handler
  at `0x0802D998` from PC-relative literal resolution to `0x04000130`.
* **Inferred:** the Password screen is reachable in-game from a main menu whose labels
  are in the same text bank; the gate that opens it was not identified.

## 8. Unknowns

* Entry path to the `Password` / `Level Password` screen (gate unknown).
* Input buffer address, password length, alphabet, checksum, validator address,
  accepted-code table, and all flag/state writes.
* Whether the password system is table-driven or algorithmic.
* The meaning of the `id` fields in the 15 level-info records.
* No novel code, no rejection-bound test, no RAM verification of a code.

## 9. Tooling

* `strings -t x -n 4`, `xxd`, `grep -abo`, `arm-none-eabi-objdump -M force-thumb`,
  Capstone (full-ROM Thumb `LDR`/`adr` scanner), Python 3.
* REA/Ghidra (`open_binary`, `search_strings`, `xrefs`): string inventory worked;
  full auto-analysis timed out at the shared provider's 330 s startup deadline.
* mGBA 0.10.5 with Xvfb `:319` + openbox; `-d` CLI debugger driven by a Python
  `stdbuf -o0` pipe controller (`/tmp/opencode/takjuju/pipe_ctrl.py`); savestate `gbAs`
  chunk decoded with `zlib`; `xdotool` XTEST input; `scrot` screenshots; PIL-based
  title-screen detector (`/tmp/opencode/takjuju/press_at_title2.py`).
* Web recon via `websearch`/`webfetch` (GameFAQs cheats page returned HTTP 403).

## 10. Legal note

No ROM bytes, extracted graphics, music or game text are redistributed here. Only
hashes, file offsets, addresses and findings are published.

## 11. Cleanup

All processes started for this engagement were stopped by numeric PID (never
`pkill -f`): mGBA `-d` (PID 439505), its pipe controller (439495), openbox (412859)
and Xvfb `:319` (412846). The generated `.sav`, `.ss1` and `.ss2` files were removed
from the ROM folder; only `Tak and the Power of Juju.gba` remains there.
