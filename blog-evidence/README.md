# Blog evidence: GBA cheat screens

Screenshots of the in-game password/cheat surfaces described in the blog draft, captured from the
ROMs in this repository. Unless a file note says otherwise, each one is the game's own UI at 3×
scale (720×480), reached by normal play and typed with the emulator keyboard. No GameShark,
CodeBreaker or memory-edit code is responsible for any visible effect.

Capture environment: mGBA 0.10.5 (`/usr/games/mgba`), Xvfb, `SDL_AUDIODRIVER=dummy`, window
720×480. Default mGBA SDL mapping: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`; arrows are the D-pad. Screenshots are `import -window <mGBA>` output.

## Index

| Folder | What it covers | Key evidence / limitation |
|---|---|---|
| `01-barnyard` | `OPTIONS → Enter Code:` on the file-select screen; the 4-slot 0–9/A–Z wheel | `03` shows `0T1S` before submission; `04` is the acceptance dialog; `05`/`06` are the 3→4 colour list before/after; `07` is a rejected neighbour (`0T1T`). |
| `02-army-men-operation-green` | 11×3 password grid and three of the seven hidden developer strings | `02` is `CR3D1TZZ` typed; `03` is the resulting credits; `04` is the `1337` screen from `H4X0RD1Z`; `05` is the developer photograph from `T4K34W4Y`. |
| `03-batman-vengeance` | 3×9 password grid; encoded table records | `02` is `HOWDEYDO` typed; `03`/`04` are the two developer photos it triggers; `05` is `QPMTRL`; `06` is the team photo; `07` is `PSCLCTT` on the entry screen. The `9:99` Advance timer itself is not captured. |
| `04-antz-extreme-racing` | Two-stage developer handshake | `01` is the 8×4 grid; `02` is the screen immediately after `*CL3M3NT` — the entry buffer has silently cleared and stage 1 is armed; `03` is the developer photo after `*M4M1K0`. |
| `05-power-rangers-ninja-storm` | 3-character password grid; `THQ` special case | `02` shows `THQ` on the entry screen; `03` is the credits roll headed `THQ`. |
| `06-back-track` | Fake DOS console behind `Select, L, Right, B, L, R, Left` | `01` is the hidden numeric debug readout from `TI`; `02` is the BSBODSOM console; `03` is the 17-character password picker; `04`/`08` are the pause and multiplayer menus; `05` proves the 17-character input cap; `06`/`07` show the published `HEA`/`ARM` effects. |
| `07-backyard-baseball-2006` | Season Play → New Coach name-entry code table | `02` shows `HOOPS` typed as the coach name; `03` is `YOU HAVE UNLOCKED BARRY DEJAY` — one of the seven unpublished names. |
| `08-big-mutha-truckers` | Two-record title-screen button table | `12` is the published code's Evil Bob truck; `13` is the character-select truck after the unpublished second code — unchanged, because bit 1 has no reader; `14`/`15` are the identical white-flash acknowledgement for both codes. |
| `09-kelly-slaters-pro-surfer` | `L R L L R R L L L R R R` at the main menu | `01` is the 11-item Extras template with four `(Cheat)` toggles; `02`/`03` show the labels resolving to Beach/Boards/Clips/Champ; `04` shows `Beaches unlocked 13/13` and `Boards unlocked 13/13`. |
| `10-dragon-ball-gt-transformation` | GT title-menu button table | `01` is the Secrets screen after the +20,000 Zeni sequence; `02` is after the unlock-all sequence (`26% Unlocked`, all five hidden characters). |
| `11-board-game-classics` | Six-digit numeric password | `01` shows `000413` typed; `02` shows `Password Accepted`. |
| `12-golden-nugget-casino` | 13-character bankroll password | `01` is the published `$500,000` code accepted; `02` is the novel `$9,100,000` code; `03` is the maximum 24-bit bankroll `!!!!v#dbbbxb=` triggering the `You're a Multi-Millionaire — Time to retire!` ending. |
| `13-barbie-princess-and-the-pauper` | Four-portrait password | `01` is `6,6,6,6` (four Julians); `02` is the end-credit roll it jumps to. |
| `14-bomberman-tournament` | Patched-ROM developer `TEST SELECT` menu | `01` is `TEST SELECT`; `02`–`04` are the 16×16 `FLAG SET` editor, empty, with 16 bits set, and with bit 2 set. This is the ROM-patch boot documented by TCRF, not a retail-reachable menu. |
| `15-crash-bandicoot-purple` | Code-entry keypad and 10-character input cap | `01` is the keypad behind holding L+R on the mode-select screen; `02` has ten characters in the ten slots; `03` is after three further A presses — the screen is unchanged, i.e. ACCEPT no longer responds. The ten characters captured read `STRAWB3RRY`, not the published `STR4WB3RRY`; the lock is the same one that makes the published string unsubmittable, but the exact string is not shown. |
| `16-legacy-of-goku` | In-game debug menu | `01` is the debug menu reached from the in-game pause menu (Go To Map, Sound Test, Play SFX/Music, Show Image); `02` is the ordinary pause menu used as the second entry point. |

## What is not here

* **Battle B-Daman** — the Zero Code screen is behind the story-gated Parts Shop and was never
  reached in normal play. The report's `GO B-DAMAN` result was obtained by calling the game's own
  validator through the GDB stub, so there is no clean retail-UI screenshot to include.
* **Beyblade VForce** — the relevant finding is that two accepted title-screen sequences write
  flags nothing reads. Those sequences are on Cyberly and the effect is invisible, so there is no
  useful screen to photograph.
* **Batman `PSCLCTT` timer** — the entry screen is captured, but the Advance Mode `9:99` timer
  result was not re-captured for this folder.
* **Bomberman Tournament** — the menu only exists in a patched ROM; `14` is therefore evidence of
  the patched test menu, not of a retail code.
* **Golden Nugget maximum code** — the keypad's cursor handling is extremely timing-sensitive, so
  the maximum code was placed in the game's own password buffer in a savestate and submitted
  through the normal OK handler. The ending screen is genuine; the keystrokes were not.
* **Crash Bandicoot Purple exact string** — see the folder note above.

## Reproduction notes

* Savestates were used only as temporary working files during capture and were removed afterwards.
* The per-game reverse-engineering reports in `roms/<game>/<game>.md` give the addresses,
  validators and table layouts for every code referenced here.
* `Back Track` images were upscaled 3× with nearest-neighbour from native 240×160 captures; the
  Golden Nugget images were cropped from a 720×480 window capture to remove the mGBA border.
