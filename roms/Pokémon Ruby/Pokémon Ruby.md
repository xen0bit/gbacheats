# Pokémon Ruby (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pokémon Ruby.gba` (same folder as this report) |
| Size | 16,777,216 bytes (`0x01000000`, 16 MiB) |
| Header title / code / maker | `POKEMON RUBY` / `AXVE` / `01` (Nintendo) |
| Version byte | `0x01` → **US Rev.1** |
| Entry word | `0xEA000032` (`b 0x080000D0`, stock crt0; see first 4 KiB) |
| Header bytes | fixed `0x96` at `0xB2`; complement `0x40`; checksum `0x0000` (normal retail rebuild artifact) |
| MD5 | `e0503182a2e699678bcf25a6897a24d6` |
| SHA-1 | `610b96a9c9a7d03d2bafb655e7560ccff1a6d894` |
| SHA-256 | `0d80909998a901c7edef5942068585bc855a85aec7e083aa6aeff84a5b2f8ec0` |

**Phase 0 / patch check (Derived + Observed).** The SHA-1 equals `ruby_rev1.sha1` in
`pret/pokeruby` exactly, confirming the **retail US Rev.1** build; it is *not* the
prototype debug build (`ruby_debug.sha1 = 1d03a9128288a7076f6b4517e7602b29f76218a1`).
The first 4 KiB is ordinary ARM crt0 (no scene cracktro, no `0xEA00002E` signature).
A 156-byte Nintendo-logo scan over all 16 MiB found **one** header, at file `0x0` —
unlike FireRed/Emerald, this ROM ships **no embedded multiboot stub headers**.
No `GAMESHARK`, `CODEBREAKER`, `CRC BANDIT`, `TRAINER` or trainer-menu strings
exist in the image. No `.sav`/`.ss*` was left in the ROM folder (all emulator
work used a byte-identical copy in `/tmp/opencode/pokemonruby`).

Game text is **not ASCII**: Gen-3 charset (space=`0x00`, `A`–`Z`=`0xBB`–`0xD4`,
`a`–`z`=`0xD5`–`0xEE`, `0`–`9`=`0xEF`–`0xF8`). `g3text.py` decoded **106,776**
NUL-delimited text runs from `charmap.txt`; all text-bank counts below use that
codec (guide §11).

## 2. Executive summary

**Retail Ruby has two reachable, developer-intended code-entry systems and three
title/main-loop button codes. It has no debug menu.** Verified independently on
this exact image (nothing carried over from the sibling FireRed/Emerald reports):

1. **Easy Chat "profile" password** — talk to the man by the PC in **Petalburg
   City Pokémon Center** and compose the four-word phrase
   **`MYSTERY EVENT IS EXCITING`**. With ≥5 badges and
   `FLAG_SYS_EXDATA_ENABLE` clear, this sets that flag; after saving and
   rebooting, `MYSTERY EVENTS` appears on the main menu. Literal table
   `0x083DB694` = `{0x143A,0x1817,0x100B,0x200F}` (one table in 16 MiB),
   validator `0x080E80B4` (ROM name `sub_80E8094` is off by `0x20`). This is a
   genuine in-game password screen, reachable without external hardware.
2. **Berry Master's Wife phrases** (Route 123) — five two-word phrases
   (`GREAT BATTLE`, `CHALLENGE CONTEST`, `OVERWHELMING LATIAS`, `COOL LATIOS`,
   `SUPER HUSTLE`) give berries, one per day. Literal table `0x083DB69C`
   (10 × `u16`), validator `0x080E812C`. All five match the published
   GameFAQs list byte-for-byte.
3. **Title-screen button codes** (exact mask equality): `B+SELECT+UP` (`0x046`)
   → "Clear all save data areas?"; `B+SELECT+LEFT` (`0x026`) → RTC-reset screen,
   **gated** by `CanResetRTC()` (`FLAG_SYS_RESET_RTC_ENABLE` set *and*
   `VAR_RESET_RTC_ENABLE == 0x920`), a state only writable by a Mystery Event
   script command (`MEScrCmd_enableresetrtc`, event type `0x0E`, e-Reader), so
   **closed in an ordinary retail save**. Main-loop `A+B+START+SELECT`
   (raw held bits) → soft reset.
4. **No debug menu.** The title-screen `#if DEBUG` branch (`SELECT` alone →
   `CB2_GoToTestMenu`) and all `src/debug/*` menus are compiled out of the
   retail build; SHA-1 proves this is not the debug prototype. `SELECT` alone
   and `R+START` were pressed in the emulator: no hidden screen (§7). Zero
   occurrences of encoded/ASCII `DEBUG`, `DEBUG MENU`, `SOUND CHECK`, `FLAGS`,
   `VARS`, `MEMSAVE`, `MEMLOAD`, `SET BADGES`, `PASSWORD`, `CHEAT`,
   `PASSWORD GENERATOR`, `PMDEBUG` across 106,776 decoded runs.

Every published "cheat code" found on the web for this title is a
GameShark/CodeBreaker/Action Replay memory patch and is **out of scope**; none
were used. The Trick House "secret code scroll" is a puzzle that tells the
player which floor buttons to step on, not a controller code.

## 3. How to reproduce

Emulator: `mgba 0.10.5` (SDL), `SDL_AUDIODRIVER=dummy`, own `Xvfb :316` +
`openbox`. Keymap (mGBA SDL default, verified on screen): A=`x`, B=`z`,
L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys
100–300 ms; `Ctrl+R` resets (Ruby's intro has **no** skip combo in
`src/intro.c`, so allow ~45 s for the title screen).

Menu walk (all observed; screenshots in `/tmp/opencode/pokemonruby/`):

1. Boot → Game Freak intro → Pokémon logo → Birch scene → title
   (`s_titleB2_c.png`, `s_selonly_c.png` — "PRESS START" visible).
2. With **no** save: Start → `NEW GAME / OPTION` (`s_title_final_c.png`).
3. `NEW GAME` → gender → name → rival → Littleroot overworld
   (`s_name_c.png`, `s_world2_c.png`).
4. Start → pause `BAG / <name> / SAVE / OPTION / EXIT` (`s_menu_c.png`,
   `s_pause2_c.png`). `OPTION` → `TEXT SPEED / BATTLE SCENE / BATTLE STYLE /
   SOUND / BUTTON MODE / FRAME / CANCEL` (`s_options2_c.png`).
5. `SAVE` → "SAVING… DON'T TURN OFF THE POWER" (`s_saved_c.png`); after reset,
   main menu = `CONTINUE / NEW GAME / OPTION` — **no `MYSTERY EVENTS`**
   (`s_mainmenu3_c.png`), matching `FLAG_SYS_EXDATA_ENABLE == 0`.
6. R+START and L+START in the field → ordinary pause menu only
   (`t_rstart_c.png`, `t_lstart_c.png`).

Button-code reproduction, all from the stable title savestate
`title_stable.ss1` (F1 reload before each test, so the start frame is identical):

| Input | Result | Screenshot |
|---|---|---|
| hold `z`+`BackSpace`+`Up` (~1 s) | "Clear all save data areas?" YES/NO | `t_clear_c.png` |
| hold `z`+`BackSpace`+`Down` | title screen unchanged (rejected) | `t_down_c.png` |
| hold `BackSpace`+`Up` | title unchanged (B bit required) | `t_selup_c.png` |
| hold `z`+`BackSpace`+`Left` | title unchanged (RTC gate closed) | `t_left_c.png` |
| hold `BackSpace` alone | title unchanged (no debug menu) | `t_sel_c.png` |
| hold `x`+`z`+`Return`+`BackSpace`+`Up` | soft reset → black → Game Freak intro | `t_reset5_c.png` |

Text-bank reproduction: `python3 decode_text.py <rom>` / `g3text.py` emit
`decoded_text.txt`; `find_encoded.py` searches encoded literals.

## 4. Address map

| Item | Address (ROM unless noted) | Evidence |
|---|---|---|
| Header / entry | `0x000000`–`0x0001FF`; entry `0xEA000032` | Observed |
| Mystery Event phrase table `gMysteryEventPhrase` | `0x083DB694` (file `0x3DB694`): `3A 14 17 18 0B 10 0F 20` | Observed, sole 8-byte hit |
| Berry Master's Wife phrase table | `0x083DB69C`: 10 × `u16` (see §6) | Observed, sole hit |
| Mystery-phrase validator (`sub_80E8094` in decomp) | `0x080E80B4`; called from `0x080E6E98`; literal xref `0x80E80EC` | Observed (objdump + literal scan) |
| Berry-phrase validator (`sub_80E810C` in decomp) | `0x080E812C`; called from `0x080E6ED4`; literal xref `0x80E81C0` | Observed |
| Word→text converter | `0x080EB238` (decomp `sub_80EB218`) | Derived |
| Mystery Club script / success text | script `0x081B1B14`–`0x081B21D0`; text `0x081B21E2` "You know the secret saying! … MYSTERY EVENT CLUB!" | Observed bytes |
| "The in-game clock adjustment system is now useable." | file `0x4118E8` | Observed (decoded) |
| "Reset RTC? A: Confirm, B: Cancel" | file `0x4117FA` | Observed (decoded) |
| "The clock has been reset…" | file `0x41185D` | Observed (decoded) |
| `gSaveBlock2` (player name at `+0x00`) | EWRAM `0x02024EA4`; savestate raw `0x45EA4` | Derived + Observed (`bb ff…` = "A") |
| `gSaveBlock1` | EWRAM `0x02025734`; savestate raw `0x46734` | Derived |
| `gSaveBlock1.flags[]` | EWRAM `0x02026954`; state `0x47954` | Derived + Observed |
| `gSaveBlock1.vars[]` | EWRAM `0x02026A74`; state `0x47A74` | Derived + Observed |
| `easyChats.unk2B1C` (phrase storage) | EWRAM `0x02028250`; state `0x48250` | Derived |
| `gEasyChatStruct` (`gSharedMem + 0x1000`) | EWRAM `0x02001000`; input words at `+0x0C` = `0x0200100C` | Derived (literal `0x0200AE14 = base+0x9E14` in validator) |
| `gSpecialVar_0x8004` | EWRAM special-variable slot (decomp `src/event_data.c`) | Derived |
| Common RAM anchors | KEYINPUT `0x04000130`; `gSoftResetDisabled` EWRAM `0x02024...` | Derived |
| Savestate layout (mGBA 0.10.5) | IWRAM at raw `0x19000`; EWRAM at `0x21000`; `state_off = 0x21000 + (ram-0x02000000)` | Observed (validated against player name) |

Decomp reference (used as a *reading aid*, all key addresses verified against
ROM bytes): `pret/pokeruby` master — `src/title_screen.c:348–350,716–745`,
`src/easy_chat_1.c:24,1674–1695,1698–1724`, `src/event_data.c:93–110`,
`src/mystery_event_script.c:422–427`, `src/main.c:136–139`,
`data/scripts/mystery_event_club.inc`, `data/text/mystery_event_club.inc`,
`src/data/text/easy_chat/group_sizes.h`, `include/constants/{easy_chat,flags,vars}.h`.

## 5. Algorithm

**Easy Chat password validator (Derived from ROM bytes + matching decomp).**
Word IDs are `(group << 9) | index`. Input: 4 word IDs in
`gEasyChatStruct->unkC[0..3]`. `sub_80EB238(dest, wordID, 0)` renders each word
to its NUL/`0xFF`-terminated text; the validator compares all four rendered
strings, byte-for-byte and length-for-length, against the four word IDs in the
ROM literal at `0x083DB694`:

```
MYSTERY = (0xA << 9)|0x3A = 0x143A
EVENT   = (0xC << 9)|0x17 = 0x1817
IS      = (0x8 << 9)|0x0B = 0x100B
EXCITING= (0x10<< 9)|0x0F = 0x200F

CheckMysteryEventPhrase():            # ROM 0x080E80B4
  for i in 0..3:
    render(input[i])   -> buffer A
    render(table[i])   -> buffer B
    if A != B: return 0
  return 1

EasyChat result handler (ROM 0x080E6E90..0x080E6EA0):
  if screen_type == 0:  gSpecialVar_0x8004 = CheckMysteryEventPhrase()  # 1/0
```

Caller (`data/scripts/mystery_event_club.inc`, ROM script `0x081B1B7A`):

```
if VAR_0x8004 == 1 and FLAG_BADGE05_GET and !FLAG_SYS_EXDATA_ENABLE:
    FLAG_SYS_EXDATA_ENABLE = 1          # 0x84C
    show "You know the secret saying! … MYSTERY EVENT CLUB!"
# any other phrase leaves VAR_0x8004 = 0 -> "Thank you …" path, no flag
```

`IsMysteryEventEnabled()` (`src/event_data.c:88`) reads that flag in
`src/main_menu.c:279,301` → adds `HAS_MYSTERY_EVENT` to the title menu layout.

**Berry Master's Wife validator** (`ROM 0x080E812C`, returns 1..5 or 0):
renders `input[0] + " " + input[1]` and compares against each of the five
2-word rows at `0x083DB69C`; return value selects the berry reward.

**Button codes (Derived from matching decomp + observed):**
GBA key bits `A=0x001, B=0x002, SELECT=0x004, START=0x008, RIGHT=0x010,
LEFT=0x020, UP=0x040, DOWN=0x080, R=0x100, L=0x200`.

```
title_phase3:
  if held == 0x046 (B|SELECT|UP):   -> ClearSaveDataScreen
  if held == 0x026 (B|SELECT|LEFT) and CanResetRTC() == 1:
                                     -> ResetRtcScreen
  if held == 0x001 (SELECT) and DEBUG: -> TestMenu   # compiled out in retail
  if new & (A|START):                -> main menu

every_frame_main_loop:
  if !gSoftResetDisabled and (heldRaw & A)
                          and (heldRaw & (B|START|SELECT)) == (B|START|SELECT):
                                     -> DoSoftReset()

CanResetRTC(): return flag(0x862) && var(0x402C) == 0x920
# only setter: MEScrCmd_enableresetrtc (Mystery Event script, e-Reader data)
```

**Title-menu unlock (Derived):** main menu layout is `HAS_NO_SAVED_GAME`
(2 items) / `HAS_SAVED_GAME` (3 items) / `HAS_MYSTERY_EVENT` (4 items, adds
`MYSTERY EVENTS`). The 3-item state was observed on a valid save.

## 6. Tables

**Easy Chat accepted phrases (complete, 6 codes in 2 tables):**

| System | Words (IDs) | Effect | Address |
|---|---|---|---|
| Mystery Club | `MYSTERY(0x143A) EVENT(0x1817) IS(0x100B) EXCITING(0x200F)` | sets `FLAG_SYS_EXDATA_ENABLE` → `MYSTERY EVENTS` on menu | `0x083DB694` |
| Berry Master's Wife | `GREAT(0x1240) BATTLE(0x0628)` | Spelon Berry | `0x083DB69C` +0 |
| " | `CHALLENGE(0x061F) CONTEST(0x2204)` | Pamtre Berry | +4 |
| " | `OVERWHELMING(0x1422) LATIAS(0x0197)` | Watmel Berry | +8 |
| " | `COOL(0x0415) LATIOS(0x0198)` | Durin Berry | +12 |
| " | `SUPER(0x2207) HUSTLE(0x0449)` | Belue Berry | +16 |

All six were verified as literals in the ROM and all six appear in the
GameFAQs/Vizzed published lists (§3.4 check passed; nothing unverified).

**Reachable button codes (complete under the exhaustive decomp search):**

| Combination | Mask | Where | Effect | Evidence |
|---|---|---|---|---|
| B+SELECT+UP | `0x046` | title | Clear all save data (YES/NO) | Observed |
| B+SELECT+LEFT | `0x026` | title | RTC reset, **gated** (see below) | Derived + Observed rejection |
| A+B+START+SELECT (+any extra held bits) | `A` & `B\|START\|SELECT` | anywhere | soft reset | Derived + Observed |
| A / START alone | — | title | skip logo animation / open main menu | Observed |
| R / L (+START) | `0x100/0x200` | in game | normal pause menu, **not** a debug menu | Observed |

**Gate state observed in a fresh save (savestate RAM reads):** `FLAG_BADGE05_GET
(0x80B)=0`, `FLAG_SYS_EXDATA_ENABLE (0x84C)=0`, `FLAG_SYS_RESET_RTC_ENABLE
(0x862)=0`, `VAR_RESET_RTC_ENABLE (0x402C)=0`, Easy Chat phrase storage all
zeros. These are the concrete reasons the Mystery Club and RTC screens are
closed on a retail save.

**Debug-menu negative counts (decoded text bank, 106,776 runs):** `DEBUG`=0,
`DEBUG MENU`=0, `SOUND CHECK`=0, `FLAGS`=0, `VARS`=0, `MEMSAVE`=0, `MEMLOAD`=0,
`SET BADGES`=0, `PASSWORD`=0, `CHEAT`=0, `PASSWORD GENERATOR`=0, `PMDEBUG`=0
(both ASCII and encoded). `WARP`=2, both inside sound-effect names
`SE_WARP_IN`/`SE_WARP_OUT` at file `0x3D0AD6`/`0x3D0AE0`; `SECRET CODE`=1, the
Trick House scroll narrative at file `0x19D443` — neither is a menu label.

## 6b. Enumeration

**Password spaces (§0.2).**
* Easy Chat word list: `gEasyChatGroupSizes[]` sums to **1,793** words across
  22 groups (the decoder exposes 1,888 distinct texts, including duplicates).
  The 4-slot profile space is `1793^4 ≈ 1.03 × 10^13` phrases; the 2-slot
  Berry space is `1793^2 = 3,214,849` phrases. There is no checksum or field
  encoding — both systems are direct literal comparisons.
* **Complete accepted set:** exactly **1** phrase for the Mystery Club and
  exactly **5** for the Berry Master's Wife. Proof: a full 16 MiB scan for the
  8-byte Mystery phrase found **one** hit (`0x3DB694`); a scan for the 20-byte
  Berry table found **one** hit (`0x3DB69C`); the validator has exactly one
  literal xref each (`0x80E80EC`, `0x80E81C0`); and each of the four Mystery
  words has exactly **one** spelling among the 1,888 Easy Chat texts (checked
  by extracting all `"WORD$"` entries from `src/data/text/easy_chat/groups/*/words.h`).
  There is therefore **no algorithmic generator and no unpublished phrase to
  mint** — the accepted sets are closed by construction. (The 98 duplicate
  texts in the word list — e.g. `YEAH`, `LINK`, `TYPE` — do not include
  `MYSTERY`, `EVENT`, `IS`, `EXCITING`, `GREAT`, `BATTLE`, `CHALLENGE`,
  `CONTEST`, `OVERWHELMING`, `LATIAS`, `COOL`, `LATIOS`, `SUPER`, `HUSTLE`,
  so no spelling alias exists either.)
* **Novel/unpublished input:** the guide's §0.2 novel-input deliverable is met
  on the button-code surface: **`A+B+START+SELECT+UP`** (5 buttons) is not in
  any published list (all published references give the 4-button combo), yet
  the main-loop gate uses `heldRaw & (B|START|SELECT) == (B|START|SELECT)` plus
  `heldRaw & A`, so `UP` is an unused bit. Entered in the emulator from the
  title savestate: the screen went black then showed the Game Freak intro,
  i.e. a real soft reset (`t_reset5_c.png`). This is the §16.4b "unused payload
  bits create aliases" pattern applied to button codes.
* **Bounds proven by rejection (Observed):** from the identical savestate,
  `B+SELECT+DOWN` (extra `DOWN` bit) does **not** open clear-save — the
  `JOY_HELD(mask)==mask` gate is exact, so Ruby (unlike FireRed's Berry-Fix
  subset test) has **no** clear-save alias; `SELECT+UP` (B omitted) and
  `SELECT` alone are rejected; `B+SELECT+LEFT` is rejected while
  `FLAG_SYS_RESET_RTC_ENABLE=0`/`VAR_RESET_RTC_ENABLE=0`, proving the
  Mystery-Event gate. For the phrase system, any phrase other than the six
  literals returns `0`/no flag — bounded by the two literal tables above.

**Button-code space:** 2^10 = 1024 possible 10-bit key states; exactly **three**
held-mask conditions are cheats (clear-save, RTC-reset, soft-reset). Enumerated
by grepping every `JOY_HELD`/`JOY_NEW` expression in the matching decomp: the
only multi-button *held* gates are the two in `title_screen.c:730,732` and the
one in `main.c:136–139`; all other multi-button expressions are A+B cancels or
D-pad pairs inside individual menus. No key-mask sequence table, progress index
or keypad validator exists in the ROM.

## 7. Validation evidence

* **Observed** (emulator on `:316`, screenshots/RAM-frame colour, savestate
  `gbAs` diffs): all menu states in §3; B+SELECT+UP → clear-save;
  B+SELECT+DOWN / SELECT+UP / SELECT / B+SELECT+LEFT rejected; the 5-button
  soft-reset alias accepted; R+START and L+START → normal pause menu; save
  file created; title menu 2/3 entries; decoded text banks.
* **Observed** (RAM via mGBA `.ss1` `gbAs` chunk; `zlib.decompress`, EWRAM at
  raw `0x21000`): player name `bb ff ff…` at `0x02024EA4`; all four gate
  values zero in a fresh save (§6). This proves the gates are closed with
  ordinary in-game state.
* **Derived** (ROM bytes / disassembly / matching decomp, SHA-1 verified):
  both phrase tables and their validators/xrefs; flag/var numbers and the sole
  `EnableResetRTC()` caller in `mystery_event_script.c`; stock entry word;
  single embedded header; button-mask source lines; 106,776-run debug-string
  counts.
* **Inferred**: that entering the four words at the Petalburg NPC sets the
  flag — proven by the validator disassembly, the caller script and the
  decoded success text, but **not** typed on that NPC's screen in this session:
  the screen requires 5 badges, which a fresh save does not have, and no
  save-editor/badge patch was used (the task scope excludes memory-edit codes
  and the 5-badge playthrough was out of the time budget). The Berry Master's
  Wife NPC (Route 123) was likewise not reached; its five literals were
  verified in ROM instead. Both gaps are labelled Derived, not Observed.
* **Published-code verification:** the GameFAQs phrase list (`MYSTERY EVENT IS
  EXCITING`; five berry phrases), the clear-save code (Up+Select+B), the
  RTC-reset code (Left+Select+B, gated) and TCRF's type-`0E` event requirement
  were all checked and agreed with the ROM. Web content was treated strictly
  as data; no instruction found in a fetched page or ROM string was followed.

## 8. Unknowns

* The on-screen acceptance of the Mystery Club and Berry Master's Wife
  phrases was not exercised (5-badge / Route-123 gates); their validators and
  literal tables are fully reversed and verified in ROM.
* `CanResetRTC()`'s only setter is an e-Reader Mystery Event script command;
  no such event was available, so the RTC-reset screen itself was never
  displayed — only its gate and rejection were proven.
* The exact ROM address of the title-screen mask comparison was not pinned to
  a single instruction (Capstone immediate scans for `0x46`/`0x26` were too
  noisy); the gates are given at matching-decomp source-line precision and the
  screens themselves are proven on screen.
* The GameFAQs "Team Rocket"-style password lore present in FireRed does not
  exist here; the only "password"-like narrative text is the Trick House
  scroll. No attempt was made to obtain Japanese/German e-Reader Wonder Cards.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`,
Python 3 stdlib, `capstone 5.0.7`, `arm-none-eabi-objdump -M force-thumb`,
`curl` + `pret/pokeruby` master tarball (source/charmap only, as a reference
map), web pages (data only), mGBA 0.10.5 under `Xvfb :316` + `openbox`,
`xdotool`, `scrot`, ImageMagick `convert -resize 1x1` colour-hash evidence.

Scripts in `/tmp/opencode/pokemonruby/`: `phase0.py`/`logo2.py` (header + logo
scan), `g3text.py` + `find_encoded.py` (Gen-3 text codec and encoded-literal
search), `state.py` (PNG `gbAs` zlib chunk parser for RAM reads), `ui.sh`
(input/capture helper). No ROM or copyrighted asset is redistributed; only
addresses, hashes, word IDs, flags and our own scripts are published.
