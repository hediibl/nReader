#ifndef NETWORK_H
#define NETWORK_H

#ifdef __cplusplus
extern "C" {
#endif

#include "nand.h"

int netInit(void);
int netUpload(const nandReport *report);

#ifdef __cplusplus
}
#endif

#endif