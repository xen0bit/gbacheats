# 2-in-1: Spider-Man & Spider-Man 2 (GBA) — Reverse Engineering Report

## 1. Target identity

File: `roms/2-in-1 - Spider-Man & Spider-Man 2/2-in-1 - Spider-Man & Spider-Man 2.gba`

| Property | Value |
|---|---|
| Size | 33,554,432 bytes (0x2000000, 32 MiB) |
| MD5 | `8c91af1e9f60e7577219176f18cefb76` |
| SHA-1 | `8bc2b600a043b776bc61fe8c0f4007b4360545f9` |
| SHA-256 | `0d7c7f4b20d5def164ff9028348b0ff18e14f0c722f77dfae2871c7875770579` |
| `file` | `Game Boy Advance ROM image: "SPIDER-MAN" (BX3E52, Rev.00)` |

The file is a concatenation of two complete 16 MiB GBA images. A full-file scan for the 156-byte Nintendo logo (header offset +4) found exactly two headers:

| Image | File base | ROM base | Header title | Game code | Maker | Ver | 0xBD complement | 0xBE..BF header checksum | Entry |
|---|---:|---:|---|---|---|---:|---:|---:|---|
| half 0 | `0x0000000` | `0x08000000` | `SPIDER-MAN` | `BX3E` | `52` | 0 | `0x08` (valid) | `0x0000` (zeroed) | `EA00002E` → `0x080000C0` |
| half 1 | `0x1000000` | `0x09000000` | `SPIDERMAN` | `AKXE` | `52` | 0 | `0x1E` (valid) | `0x0000` (zeroed) | `EA00002E` → `0x090000C0` |

Both complement bytes recalculate correctly. Both 16-bit header checksums are zero, i.e. the pack's headers were rebuilt after concatenation. This does not affect execution.

The first image's entry is a pack redirect, not the game:

```
080000C0  ldr r0,[pc,#72]   ; literal at 0x08000110 = 0x090000C0
080000C4  bx  r0
```

Half 0's header title also reads `SPIDER-MAN`, but its legal screen is ©2004 Columbia / Digital Eclipse and its title screen reads **SPIDER-MAN 2**; half 1 is the 2002 game (©2002 Columbia). Confirmed dynamically by selecting each cover of the pack's boot menu (§3).

## 2. Executive summary

The cartridge is a two-image pack with an in-ROM boot selector. Half 0 is **Spider-Man 2** (2004, Digital Eclipse) at `0x08000000`; half 1 is **Spider-Man: The Movie** (2002) at `0x09000000`. Half 0's cartridge entry is patched to jump to half 1's entry (`0x090000C0`), and half 1 runs the "choose a game" shell before either game. Selecting the right cover boots half 0 (©2004 legal + "SPIDER-MAN 2" title); selecting the left cover boots half 1 (©2002 legal + "SPIDER-MAN" title with SECRETS).

The prior triage conclusion — "only `Cheatlevel`/level-name debug leftovers, no reachable menu" — is **half right and half wrong**:

1. **Reachable menu (overturned).** Half 1 contains a real, developer-intended **SECRETS menu with 17 entries** (header `SECRETS PAGE n`; the string `CHEATS` also exists in the same text table) and ON/OFF toggles: ARMOR UPGRADE, STRENGTH ENHANCEMENT, LEVEL CHEAT, and MOVIE SHOT 1–14. It is not a debug leftover. In a fresh save every entry is `<LOCKED>`; setting the game's own unlock-state bytes makes the page render `ARMOR UPGRADE OFF`, `STRENGTH ENHANCEMENT OFF`, `LEVEL CHEAT OFF`, `MORE`, `EXIT`, and the following pages render MOVIE SHOT 1–14. The in-game detail text gives the unlock conditions ("SECRET WILL BE UNLOCKED FOR FINISHING THE GAME", "COMPLETE THE GAME AND COLLECT ALL GOLDEN SPIDERS", "COMPLETE THE GAME WITH OVER 150,000 POINTS"). Selecting an entry toggles it, and selecting a movie shot plays the clip. This was exercised in mGBA.
2. **Dead debug path (confirmed).** The strings `Cheatlevel`, `Done Cheatlevel`, `Level Cheat`, `Cheat Zap` are attached to two pause-menu button handlers. Both handlers are gated by one function, `0x0900074C`, whose entire body is `movs r0,#0; bx lr`. In mGBA, A+L in the pause menu (with LEVEL CHEAT enabled) and B+R+L+A both reach the gate call, receive `r0 = 0`, and branch to the "no cheat" path. The command-copy instructions after the gate are never executed. This is a build-time removal, not a save/clear gate.
3. **Half 0's level-select text is completion-gated UI, not a debug menu.** `Level Select:` (text ID 65), `Unlock All Moves` (ID 48) and `Unlock All Levels` (ID 49) are ordinary entries in the English UI text table at `0x0812C110`. In a fresh save the OPTIONS menu has exactly four entries (SOUND, MUSIC, CREDITS, EXIT) and the SECRETS menu exactly fourteen (`SECRET 01`–`SECRET 14`, all locked); the three completion strings are not rendered. No cheat/debug strings exist in half 0's code. The published name code `FLUWDEAR` cannot exist here: the name field is three characters and the literal is absent from the whole 32 MiB file.
4. **Published codes verified.** The GameFAQs 2-in-1 page lists a Spider-Man 2 title-screen button code (Up, Down, Right, A) and the name `FLUWDEAR`; neither is implemented in this build (no button-mask sequence in ROM, the sequence simply operates the title menu, and FLUWDEAR is unenterable). `ARACHNID` occurs only inside the power-up name `ARACHNID STRENGTH`, not as a code. The published *unlockables* for Spider-Man: The Movie (Cheat Mode, Enhanced Armor, Enhanced Strength, Level Select, Movie Clips) do exist and are exactly the 17-entry menu above.

A previously unpublished selection was made in-game: **MOVIE SHOT 14** (not individually listed on GameFAQs, which only says "Movie Clips"), plus undocumented two-toggle combinations (screens in §6b).

## 3. How to reproduce

### 3.1 Environment

```
Xvfb :114 -screen 0 1024x768x24
DISPLAY=:114 openbox
DISPLAY=:114 SDL_AUDIODRIVER=dummy mgba -3 "<rom>"
```

mGBA SDL keymap used (verified on screen): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrows. Hold keys 150–300 ms.

### 3.2 Pack boot selector

Cold boot shows two covers with a red/black frame. Moving Right changes the footer logo from `SPIDER-MAN™` to `SPIDER-MAN 2™`.

* Left cover + A → language select → ©2002 legal → `SPIDER-MAN` logo → Start → main menu **START / LOAD GAME / OPTIONS / SECRETS** (half 1).
* Right cover + A → language select → ©2004 legal → Activision → intro → **SPIDER-MAN 2** title with **NEW / LOAD / OPTIONS / SECRETS** (half 0).

This alone proves which half each cover boots and that the shell is developer content.

### 3.3 Half 1 (Spider-Man: The Movie) menus

```
Left cover, A, A (English), Start (logo), Down x3, A   -> SECRETS PAGE 1
```
Fresh save: three `<LOCKED>` rows, `MORE`, `EXIT`. `MORE` cycles to PAGE 2 (`MOVIE SHOT 1`–`7`, `MORE`, `EXIT`) and PAGE 3 (`MOVIE SHOT 8`–`14`, `MORE`, `EXIT`). Selecting a locked row does nothing.

Unlocked state is produced by the game's own end-of-game award routine; for analysis the 17 "owned" bytes were written directly with the debugger while at the menu (these are the game's own save/RAM state, not a published cheat code):

```
set *(unsigned int*)0x02039081 = 0x01010101
set *(unsigned int*)0x02039085 = 0x01010101
set *(unsigned int*)0x02039089 = 0x01010101
set *(unsigned int*)0x0203908D = 0x01010101
set *(unsigned char*)0x02039091 = 0x01
```
(RAM values are not a published cheat; they are the game's unlock bitmap, reached here to enumerate the menu without a full playthrough.)

Result: PAGE 1 renders `ARMOR UPGRADE OFF`, `STRENGTH ENHANCEMENT OFF`, `LEVEL CHEAT OFF`. A toggles the selected row ON/OFF. Selecting `LEVEL CHEAT` ON and starting a level makes the pause screen show `CHEAT <current level name>` (observed: `CHEAT THE CRADLE WILL FALL`). PAGE 3 → `MOVIE SHOT 14` plays a Green Goblin movie still.

### 3.4 Half 0 (Spider-Man 2) menus

```
Right cover, A, A (English), wait through intro
Title: NEW / LOAD / OPTIONS / SECRETS
OPTIONS: SOUND: ON / MUSIC: ON / CREDITS / EXIT
SECRETS: vertical list SECRET 01 .. SECRET 14 (all locked in a fresh save; A does nothing)
NEW: SELECT SLOT TO START, 3-character name entry, A x3 starts the game
In game, Start: GAME PAUSED, CONTINUE / QUIT
```

No cheat menu, no button-code indicator, and no debug labels were found in this half.

### 3.5 Tested triggers and outcomes

| Trigger | Where | Result |
|---|---|---|
| A + L held | half 1 pause, `LEVEL CHEAT` ON | Reaches `bl 0x0900074C` at `0x09025FF8`; gate returns 0; branches to `0x09026040`. No `Cheatlevel` print, no `Level Cheat` copy. |
| B + R + L + A | half 1 pause | Reaches `bl 0x0900074C` at `0x09009720`; gate returns 0; branches to `0x090097A0`; no `Cheat Zap` copy. |
| Up, Down, Right, A | half 0 title | Operates the ordinary menu (Right moves NEW→LOAD, A selects LOAD; screen becomes `SELECT SLOT TO LOAD`). No cheat state changes. |
| `FLUWDEAR` as a new-game name | half 0 name entry | Impossible: name field is three characters; Right/Up cycle letters inside the three slots, A x3 starts the game. The literal `FLUWDEAR` is absent from both halves. |

## 4. Address map

File offset `f` in half 0 maps to `0x08000000 + f`; in half 1 to `0x09000000 + (f - 0x1000000)`.

| Address / range | Meaning |
|---|---|
| `0x08000000` | half 0 header (Spider-Man 2) |
| `0x080000C0` | half 0 pack redirect (`ldr r0,=0x090000C0; bx r0`; literal at `0x08000110`) |
| `0x09000000` | half 1 header (Spider-Man: The Movie) |
| `0x090000C0` | half 1 ARM crt0; `0x090002C5` Thumb continuation |
| `0x0900074C` | **cheat gate stub**: `movs r0,#0; bx lr`. Called by the two dead cheat handlers and the menu-input path. |
| `0x0900971C` | "Cheat Zap" handler (pause/menu input) |
| `0x0900974A` | `Cheat Zap` string copy (10 bytes) — after the gate |
| `0x09025FD4` | "Cheatlevel" block inside the half 1 pause-menu update |
| `0x09026008` | `bl print("Cheatlevel")` — after the gate |
| `0x09026030..3C` | literal pool: `0x09050564`, `0x09050570`, `0x020279D0`, `0x09050584` |
| `0x0902B018` | level-cheat activation (loops `0x9027F20` over indices 0..5, copies state bytes, forces `[0x0202A588] >= 3`) |
| `0x0903BEE0` | half 1 secret-award / "newly unlocked" helper |
| `0x0903BF34` | award one secret (checks `0x02025EF4..F6`, writes `0x02038FE0+0xA1+idx`) |
| `0x0903C0F4` | draw one secret row (uses table `0x09659EC8`, language index) |
| `0x0903C1FC` | secrets page update / award-check |
| `0x0903C61C` | secrets select handler; toggles `0x02025EF4+idx` for idx 0..2 |
| `0x0903C68C` | `strb r2,[r1]` — writes the LEVEL CHEAT arm byte `0x02025EF6` (watchpoint PC `0x0903C690`) |
| `0x0903C6xx` | entry-action switch (`cmp r0,#0x11`); movie-shot playback and menu transitions |
| `0x0903CA54` | third gate caller (menu input path), same stub |
| `0x09050564` | `"Cheatlevel\n"` |
| `0x09050570` | `"Done Cheatlevel\n"` |
| `0x09050584` | `"Level Cheat"` (12-byte copy source) |
| `0x0904DABC` | `"Cheat Zap"` (10-byte copy source) |
| `0x0904562C` | `"Cheatlevel=%d\n"` (startup/debug printf) |
| `0x0928D7FC..0x0928DAEC` | half 1 secret names in EN/FR/DE triples |
| `0x0928DAFC..0x0928DCEF` | half 1 secret descriptions |
| `0x09659DFC` | 17 × {EN ptr, FR ptr, DE ptr} descriptors |
| `0x09659EC8` | 17-entry pointer table consumed by `0x0903C0F4` |
| `0x0965Bxxx` | half 1 text-ID -> {EN,FR,DE} string table (CHEATS, VIEW PHOTOS, BONUS COMPLETE, …) |
| `0x0812C110` | half 0 English UI text-pointer table (246 entries) |
| `0x0812C110 + 4*ID` | text ID lookup; IDs below |
| `0x08135xxx` | duplicate/localised half 0 text tables |

RAM used by the half 1 cheat system:

| Address | Meaning | Evidence |
|---|---|---|
| `0x02026134` | newly-pressed button flags (bit0 = A, bit1 = B, bit2 = Select) | observed `0x0001` while A held |
| `0x02000680` | `0xFC00` OR (`~KEYINPUT` AND `0x3FF`); set bit = pressed | observed `0xFC00` idle, `0xFC01` with A |
| `0x02025EF4..F6` | per-entry toggle bytes (0 = ARMOR, 1 = STRENGTH, 2 = LEVEL CHEAT) | watchpoint (byte 2); indices assigned from the menu order |
| `0x0202A6C0 + 8` | unlocked-secret bitmask (bit idx) | derived from `0x0903C326`/`0x0903C33C` |
| `0x0202A6C0 + 0xC` | enabled-cheat bitmask (bit idx) | derived from `0x0903C226` |
| `0x02038FE0 + 0xA1 + idx` | "secret owned" bytes, idx 0..16 | derived from `0x0903BF5E`/`0x0903BF84`; used to make the menu render |
| `0x020279D0` | level/scratch text buffer; first bytes would receive `Cheat Zap` / `Level Cheat` if the gate passed | observed `4 HOSTAGES REMAIN` in pause |
| `0x0202A588` | forced to `>= 3` by the level-cheat activation | derived |

Half 0 text IDs (base `0x0812C110`):

| ID | String |
|---:|---|
| 25 / 26 | `Sound: On` / `Sound: Off` |
| 29 / 30 | `Credits` / `Exit` |
| 31 | `Secrets` |
| 34..47 | `Secret 01` .. `Secret 14` |
| 48 | `Unlock All Moves` |
| 49 | `Unlock All Levels` |
| 65 | `Level Select:` |

## 5. Algorithm

### 5.1 Pack boot

```
CPU entry 0x080000C0:
    r0 = [0x08000110] = 0x090000C0
    bx r0
0x090000C0 (ARM crt0):
    set IRQ stack, handler at 0x03007FFC
    r1 = [0x09000234] = 0x090002C5
    bx r1
0x090002C4 (Thumb):
    initialise DMA/VRAM/palette, then run the boot selector
```
Observed: left cover → half 1 game, right cover → half 0 game. The exact hand-off (jump vs warm-boot word) was not traced; see Unknowns.

### 5.2 Half 1 secret unlock and toggle

```
award(idx):                                  ; 0x0903BF34
    if any byte of 0x02025EF4[0..2] != 0:
        0x0202A6C0[6] |= 1                   ; "a cheat has ever been enabled"
    if idx <= 2:
        if 0x02038FE0[0xA1+idx] == 0:
            0x02038FE0[0xA1+idx] = 1
            return newly_awarded = 1
    else:
        0x02038FE0[0xA1+idx] = 1
    return 0
```

The page builder (`0x0903C0F4`) indexes descriptor table `0x09659EC8` (17 entries). The select handler (`0x0903C61C`) toggles bytes `0x02025EF4 + idx` for idx 0..2 and sets bits in `0x0202A6C0+8`/`+0xC`; for idx >= 3 it plays MOVIE SHOT `idx-2`.

```
toggle(idx):                                 ; 0x0903C61C / write at 0x0903C68C
    if idx <= 2:
        v = 0x02025EF4[idx]
        v ^= 1
        0x02025EF4[idx] = v
        set_enabled_bit(idx, v)
```

Watchpoint proof (writer):

```
Hardware watchpoint 1: *(unsigned char*)0x02025EF6
Old value = 0
New value = 1
0x0903C690 in ?? ()
pc=0x0903C690  lr=0x0903CA59  r1=0x02025EF6  r2=1  r3=0x02025EF4  r10=2
```

`r10 = 2` is LEVEL CHEAT; the byte is written by `strb r2,[r1]` at `0x0903C68A..8C`.

### 5.3 Dead debug commands (half 1)

```
; "Cheatlevel" path, 0x09025FD4 (runs each pause-menu frame)
if (pressed & 2) goto other_menu_action;       ; B edge
if (!(pressed & 1)) goto done;                 ; A edge required
if (!(key_state & 0x200)) goto no_cheat;       ; L held
if (gate() == 0) goto no_cheat;                ; <== always taken
if (0x02025EF6 == 0) goto done;                ; LEVEL CHEAT enabled
print("Cheatlevel\n")
level_cheat_activate()                         ; 0x0902B018
print("Done Cheatlevel\n")
copy 12 bytes "Level Cheat" -> 0x020279D0
done/no_cheat: ...
```

```
; "Cheat Zap" path, 0x0900971C
if (gate() == 0) goto blocked;                 ; <== always taken
if (!(pressed & 2)) goto blocked;              ; B edge
if ((key_state & 0x301) != 0x301) goto blocked ; R+L+A held
copy 10 bytes "Cheat Zap" -> 0x020279D0
[0x020279D0+0x5C] = 0x78
blocked: ...
```

```
gate():                                        ; 0x0900074C
    movs r0, #0
    bx lr
```

`gate()` has exactly three BL callers: `0x09009720` (Cheat Zap), `0x09025FF8` (Cheatlevel), `0x0903CA54` (menu input). All three are blocked. No other executable path references the post-gate command strings.

Dynamic proof:

```
Breakpoint 5, 0x09025FF8          ; bl gate from Cheatlevel
Breakpoint 7, 0x09026040          ; beq target taken because r0 == 0
; 0x09026008 (print "Cheatlevel") never hit

Breakpoint 2, 0x09009720          ; bl gate from Cheat Zap
Breakpoint 3, 0x090097A0          ; beq target taken
r0 = 0
; 0x09009746 (copy "Cheat Zap") never hit
```

## 6. Tables

### 6.1 Half 1 (Spider-Man: The Movie) SECRETS menu — 17 entries

Names and descriptions read from `0x0928D7FC..0x0928DCEF` / table `0x09659EC8`:

| idx | Entry (EN) | Unlock condition shown in-game |
|---:|---|---|
| 0 | `ARMOR UPGRADE` | "COMPLETE THE GAME AND COLLECT ALL GOLDEN SPIDERS." |
| 1 | `STRENGTH ENHANCEMENT` | "COMPLETE THE GAME WITH OVER 150,000 POINTS." |
| 2 | `LEVEL CHEAT` | "SECRET WILL BE UNLOCKED FOR FINISHING THE GAME." |
| 3 | `MOVIE SHOT 1` | photo/finish-gated description |
| 4 | `MOVIE SHOT 2` | photo/finish-gated description |
| 5 | `MOVIE SHOT 3` | photo/finish-gated description |
| 6 | `MOVIE SHOT 4` | photo/finish-gated description |
| 7 | `MOVIE SHOT 5` | photo/finish-gated description |
| 8 | `MOVIE SHOT 6` | photo/finish-gated description |
| 9 | `MOVIE SHOT 7` | photo/finish-gated description |
| 10 | `MOVIE SHOT 8` | photo/finish-gated description |
| 11 | `MOVIE SHOT 9` | photo/finish-gated description |
| 12 | `MOVIE SHOT 10` | photo/finish-gated description |
| 13 | `MOVIE SHOT 11` | photo/finish-gated description |
| 14 | `MOVIE SHOT 12` | photo/finish-gated description |
| 15 | `MOVIE SHOT 13` | photo/finish-gated description |
| 16 | `MOVIE SHOT 14` | photo/finish-gated description |

Each row has EN/FR/DE pointers (German/French names are at the same descriptor). The description strings available to the detail screen are:
`FOR PHOTOGRAPHING`, `FOR GETTING ALL PHOTOS`, `FOR FINISHING THE GAME`, `COMPLETE THE GAME AND` + `collect all golden spiders.`, and `COMPLETE THE GAME` + `with over 150,000 points.`

### 6.2 Half 0 (Spider-Man 2) SECRETS menu

In a fresh save the list is exactly `SECRET 01`–`SECRET 14` (text IDs 34–47), all locked. The three completion-gated strings (`Level Select:`, ID 65; `Unlock All Moves`, ID 48; `Unlock All Levels`, ID 49) are present in the UI table but are not rendered in a fresh save. This matches the published unlockables ("Finish the game once", "new option which lets you unlock all moves").

### 6.3 Published-literals verification

| Published item (source) | Literal in ROM | Result |
|---|---|---|
| `FLUWDEAR` (GameFAQs 2-in-1 / Spider-Man 2 name code) | **absent** in both halves | Rejected: name entry is 3 chars, so an 8-char name cannot be entered. Tested at the name screen. |
| Up, Down, Right, A (GameFAQs Spider-Man 2 title Invincibility) | no 3- or 4-mask sequence in either half, as `u16` masks `40 00 80 00 10 00 01 00`, active-low `BF 03 7F 03 EF 03 FE 03`, or bytes | Rejected: the sequence operates the title menu (moves to LOAD and selects it); no cheat state or indicator. |
| `ARACHNID` (console/PC cheat) | only `0x092958D0 "ARACHNID STRENGTH"` (power-up name) | Not a code in this build. |
| `IMIARMAS`, `LVLSKIPPER`, `WARPULON` | absent | Not implemented in this build. |
| Armor Upgrade / Strength Enhancement / Level Select / Movie Clips (GameFAQs Spider-Man: The Movie unlockables) | present at `0x09659EC8` table / `0x0928D7FC..` | Confirmed menu entries, with ON/OFF and movie playback. |

## 6b. Enumeration

### 6b.1 Reachable space (half 1, Spider-Man: The Movie)

* **Menu space:** 17 entries (3 toggles with OFF/ON states, 14 one-shot movie-shot selections), presented 3 per page over 3 pages.
* **Full list:** §6.1, read from `0x09659EC8` (17 pointers = 17 × 4 bytes), descriptors at `0x09659DFC` (17 × 12 bytes), names at `0x0928D7FC..0x0928DAEC`, descriptions at `0x0928DAFC..0x0928DCEF`.
* **Unlock state:** 17 bytes at `0x02038FE0+0xA1`; enable bits at `0x0202A6C0+0xC`; per-entry toggle bytes `0x02025EF4..F6`.
* **Novel selection (not in any published list):**
  * **MOVIE SHOT 14** — GameFAQs lists only "Movie Clips"; it does not enumerate the 14 shots. Selected at PAGE 3 and played in mGBA (Green Goblin / alley scene). `evidence/half1_movieshot14.png`.
  * **STRENGTH ENHANCEMENT ON + LEVEL CHEAT ON** (`evidence/half1_secrets_unlocked.png`) and **ARMOR UPGRADE ON + LEVEL CHEAT ON** (`/tmp/opencode/spiderman/w4_game.png`) — combinations not documented on any published list; each toggle is individually published only as a generic unlockable.
* **Effect of LEVEL CHEAT ON:** pause screen gains `CHEAT <level name>` (observed `CHEAT THE CRADLE WILL FALL`). The post-gate debug warp (`0x0902B018`) remains blocked by `0x0900074C`.

### 6b.2 Reachable space (half 0, Spider-Man 2)

* **SECRETS list:** exactly 14 entries (`SECRET 01`–`14`), text IDs 34–47; all `<LOCKED>` in a fresh save.
* **OPTIONS list:** 4 entries (SOUND, MUSIC, CREDITS, EXIT).
* **Completion-gated strings:** `Unlock All Moves` (ID 48), `Unlock All Levels` (ID 49), `Level Select:` (ID 65) — present, not rendered in a fresh save; 3 strings, 3 pointer-table slots (`0x0812C1D0`, `0x0812C1D4`, `0x0812C214`).
* **Rejected published code:** `FLUWDEAR` (3-char name field; literal absent).
* **Rejected button code:** Up/Down/Right/A (no mask table; normal menu operation).

### 6b.3 Negative result and bounded search space (debug path)

The `Cheatlevel` / `Cheat Zap` debug framework is **unreachable in this build**. Bounds:

* **Strings examined (full 32 MiB):** `Cheatlevel` (2 occurrences: `0x09050564` name, `0x0904562C` printf), `Done Cheatlevel` (`0x09050570`), `Level Cheat` (`0x09050584`), `Cheat Zap` (`0x0904DABC`), `LEVEL-CHEAT` (`0x0928D86C`, menu text), `CHEAT NIVEAU`, `LEVEL CHEAT` (menu text), `(cheating)` (`0x092948D8`).
* **Executable references enumerated:** four direct pointer slots for the two command strings (`0x09026030`, `0x09026034`, `0x0902603C`, `0x0900976C`), one for the startup printf (`0x09000270`), and 3 BL callers of the gate (`0x09009720`, `0x09025FF8`, `0x0903CA54`).
* **Gate body:** `0x0900074C` is 4 bytes, `00 20 70 47` (`movs r0,#0; bx lr`), i.e. a constant-zero stub. Within the enumerated call graph no write or alternate gate changes this return value.
* **Triggers tested and rejected in mGBA:**
  1. A+L in pause with LEVEL CHEAT ON: reached gate at `0x09025FF8`, branched to `0x09026040`; `0x09026008` (print) and `0x0902B018` never executed.
  2. B+R+L+A in pause: reached gate at `0x09009720`, branched to `0x090097A0` with `r0=0`; `0x0900974A` (copy) never executed.
  3. A third caller of the same gate sits in the menu-input path (`0x0903CA54`); it tests the same first instruction, so the same rejection applies without a separate button experiment.
* **Excluded space:** every button combination (10 bits), both edge/held semantics, both handlers, the pause and menu entry points, and the LEVEL CHEAT-enabled state — all converge on the same constant-zero gate. The only way to run the post-gate code is a ROM patch or debugger write, neither of which is player-reachable.

## 7. Validation evidence

**Observed (emulator / memory):**
* Pack boot selector with both covers; footer logo changes `SPIDER-MAN™` → `SPIDER-MAN 2™` (screens `boot_game.png`, `b0_game.png`).
* Right cover boots ©2004 legal and the `SPIDER-MAN 2` title (`b1_game.png`, `b6_game.png`); left cover boots ©2002 legal and `SPIDER-MAN` (`t1_game.png`).
* Half 1 fresh SECRETS pages 1–3: `<LOCKED>` entries; details `ARMOR UPGRADE`, `STRENGTH ENHANCEMENT`, `LEVEL CHEAT` with their condition text (`sec_p1.png`, `sec_p2.png`, `det1.png`, `det2.png`, `v2_game.png`, `u2_game.png`).
* Half 1 unlocked SECRETS page 1 with ON/OFF toggles (`v1_game.png`, `w3_game.png`, `w4_game.png`, `x1_game.png`); `MOVIE SHOT 7` and `MOVIE SHOT 14` playback (`v3_game.png`, `u4_game.png`).
* Half 1 pause shows `CHEAT THE CRADLE WILL FALL` when LEVEL CHEAT is ON (`p2_game.png`).
* Half 0 title/options/secrets/name/pause screens (`b6_game.png`, `sm2_opt.png`, `sm2_sec.png`, `sm2_sec4.png`, `h0_game.png`, `k1_game.png`).
* GDB: watchpoint writer `0x0903C690` with `r1=0x02025EF6`, `r2=1`, `r10=2`; Cheatlevel gate branch to `0x09026040`; Cheat Zap gate branch to `0x090097A0` with `r0=0` (`gdb_evidence.log`).
* Key state semantics: `0x02000680 = 0xFC00` idle, `0xFC01` with A held; `0x02026134 = 0x0001` on A edge.

**Derived (instruction sequence):**
* `0x0900074C` is a constant-zero function; all three callers test it and branch away on zero.
* Cheatlevel condition = A edge + L held + `0x02025EF6 != 0` + gate.
* Cheat Zap condition = B edge + R+L+A held + gate.
* Secret award writes `0x02038FE0+0xA1+idx`; select toggles `0x02025EF4+idx` and enable bits at `0x0202A6C0+0xC`.
* Half 0 pack redirect at `0x080000C0`; half 1 crt0 at `0x090000C0` → `0x090002C5`.

**Inferred:**
* The three half 0 completion strings are the post-100% OPTIONS additions; their gating was not reached in a fresh save (see Unknowns).
* The exact per-movie-shot unlock condition (photograph vs all photos vs finish) was not mapped one-to-one; the menu's condition strings are shared.

## 8. Unknowns

* The precise hand-off from the half 1 boot selector into half 0 (direct jump vs warm-boot word) was not traced. The result is observed (right cover runs half 0 at its own base), but the hand-off instruction was not located.
* Half 0's completion flags were not simulated; the `Unlock All Moves` / `Unlock All Levels` / `Level Select:` options were proven present as text IDs and absent from a fresh-save menu, but not rendered in-game.
* Which of the three shared description strings applies to each individual MOVIE SHOT was not enumerated; the entry names and table layout are exact.
* A different regional revision of either half could differ in addresses and string IDs.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`), Xvfb `:114`, openbox, `scrot`, `xdotool`.
* `arm-none-eabi-objdump` and Capstone 5.0.7 for raw Thumb/ARM disassembly and LDR-literal resolution.
* gdb-multiarch with `mgba -g` (TCP 2345), hardware breakpoints/watchpoints.
* Python one-off scripts (working dir `/tmp/opencode/spiderman`):
  * `hash/header/logo scan` — full-file Nintendo-logo search, header parse, complement check.
  * `literal/xref scan` — 4-byte pointer search + Thumb `LDR Rd,[PC,#imm]` slot resolution, used for every string in §6b.3.
  * `BL-target scan` — enumerated the three gate callers.
  * `secret table dump` — parsed `0x09659EC8` and `0x0812C110`.
* Durable key evidence in `roms/2-in-1 - Spider-Man & Spider-Man 2/evidence/`:
  `pack_selector_right.png`, `half0_title.png`, `half0_secrets.png`,
  `half1_secrets_locked.png`, `half1_secrets_unlocked.png`,
  `half1_strength_detail.png`, `half1_pause_levelcheat.png`,
  `half1_movieshot14.png`, `gdb_transcript.txt`.
* Full screenshot set and the complete GDB log remain in the analysis working directory `/tmp/opencode/spiderman/` (`boot_game.png`, `b1_game.png`, `t1_game.png`, `sm2_opt.png`, `sm2_sec4.png`, `h0_game.png`, `k1_game.png`, `sec_p1.png`, `sec_p2.png`, `det1.png`, `v1_game.png`, `v2_game.png`, `v3_game.png`, `u2_game.png`, `w4_game.png`, `x1_game.png`, `gdb_evidence.log`).

## 10. Legal note

No ROM, extracted graphics, audio, or game text bank is redistributed with this report. All addresses, byte values, algorithms, and the analyst's own screenshots/transcript are provided for documentation and reproducibility. The ROM was analysed from a local copy the operator is entitled to inspect.
