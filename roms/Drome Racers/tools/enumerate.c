/* Exhaustive enumeration of the Drome Racers GBA code-entry space.
 * Faithful reimplementation of ROM function 0x080958f8:
 *   compare exactly 6 bytes of input buffer against a 6-byte table string.
 * Input alphabet = on-screen keyboard: A-Z, 0-9, !, "  (28 symbols).
 * Field length = 6 (entry screen shows exactly 6 slots).
 */
#include <stdio.h>
#include <stdint.h>

static const char ALPHA[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!\"";
static const char *CODES[6] = {
    "CUPIUP", "ALL4ME", "BIFFIN", "BIGUNS", "LOGRAV", "IAMCAR"
};

/* ROM validator: returns 1 iff input[0..5] == code[0..5] */
static int validate(const char *in, const char *code) {
    for (int i = 0; i <= 5; i++) {
        if ((uint8_t)in[i] != (uint8_t)code[i]) return 0;
    }
    return 1;
}

int main(void) {
    char in[7];
    unsigned long long accepted = 0;
    unsigned long long total = 1;
    for (int i = 0; i < 6; i++) total *= 38;
    for (int a = 0; a < 38; a++)
    for (int b = 0; b < 38; b++)
    for (int c = 0; c < 38; c++)
    for (int d = 0; d < 38; d++)
    for (int e = 0; e < 38; e++)
    for (int f = 0; f < 38; f++) {
        in[0]=ALPHA[a]; in[1]=ALPHA[b]; in[2]=ALPHA[c];
        in[3]=ALPHA[d]; in[4]=ALPHA[e]; in[5]=ALPHA[f]; in[6]=0;
        for (int k = 0; k < 6; k++) {
            if (validate(in, CODES[k])) {
                printf("ACCEPT %s (table index %d)\n", in, k);
                accepted++;
                break;
            }
        }
    }
    printf("total inputs tested = %llu\n", total);
    printf("accepted = %llu\n", accepted);
    return 0;
}
