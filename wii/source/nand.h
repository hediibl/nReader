#ifndef NAND_H
#define NAND_H

#ifdef __cplusplus
extern "C" {
#endif

#include <gccore.h>

typedef struct {
    char id[18];
    char title[16];
    char ticket[4];
} nandEntry;

typedef struct {
    char username[32];
    char serial[32];
    nandEntry *entries;
    u32 count;
} nandReport;

int nandInit(void);
int nandRead(nandReport *dump);

#ifdef __cplusplus
}
#endif

#endif