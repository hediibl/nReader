// includes
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <network.h>
#include "net.h"

// variables
static int ret;

// helpers
static void sanitizeString(const char *src, char *dst, int maxLen) {
    int j = 0;
    for (int i = 0; src[i] && j < maxLen-1; i++) {
        unsigned char c = (unsigned char)src[i];
        if (c >= 32 && c <= 126) {
            if (c == '"') dst[j++] = '\\', dst[j++] = '"';
            else if (c == '\\') dst[j++] = '\\', dst[j++] = '\\';
            else dst[j++] = c;
        } else dst[j++] = ' ';
    }
    dst[j] = '\0';
    int start = 0;
    while (dst[start] == ' ' && dst[start] != '\0') start++;
    int end = j - 1;
    while (end >= start && dst[end] == ' ') end--;
    int k = 0;
    for (int i = start; i <= end; i++) dst[k++] = dst[i];
    dst[k] = '\0';
}

static char *generateJsonReport(const nandReport *report) {
    static char json[65536];
    char entries[32768];
    entries[0] = '\0';
    char sanitizedSerial[17], sanitizedNandSerial[17], sanitizedUsername[33];
    sanitizeString(report->serial, sanitizedSerial, sizeof(sanitizedSerial));
    sanitizeString(report->serial, sanitizedNandSerial, sizeof(sanitizedNandSerial));
    sanitizeString(report->username, sanitizedUsername, sizeof(sanitizedUsername));
    for (u32 i = 0; i < report->count; i++) {
        char entry[512];
        char sId[32], sTitle[32], sTicket[8];
        sanitizeString(report->entries[i].id, sId, sizeof(sId));
        sanitizeString(report->entries[i].title, sTitle, sizeof(sTitle));
        sanitizeString(report->entries[i].ticket, sTicket, sizeof(sTicket));
        snprintf(entry, sizeof(entry),
                 "%s{\"position\":%u,\"id\":\"%s\",\"title\":\"%s\",\"ticket\":\"%s\"}",
                 i == 0 ? "" : ",",
                 i + 1,
                 sId, sTitle, sTicket);
        strncat(entries, entry, sizeof(entries) - strlen(entries) - 1);
    }
    snprintf(json, sizeof(json),
             "{"
             "\"serial\":\"%s\","
             "\"serialNand\":\"%s\","
             "\"username\":\"%s\","
             "\"description\":\"\","
             "\"entries\":[%s]"
             "}",
             sanitizedSerial, sanitizedNandSerial, sanitizedUsername, entries);

    return json;
}

// public
int netInit(void) {
    const char *host = "nreader.eu";
    const int port = 80;
    char localip[16] = {0};
    char netmask[16] = {0};
    char gateway[16] = {0};
    ret = if_config(localip, netmask, gateway, true, 20);
    if (ret < 0)
        return -201;
    struct hostent *he = net_gethostbyname(host);
    if (!he || !he->h_addr_list[0])
        return -202;
    int sock = net_socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
    if (sock == INVALID_SOCKET)
        return -203;
    struct sockaddr_in server;
    memset(&server, 0, sizeof(server));
    server.sin_family = AF_INET;
    server.sin_port = htons(port);
    memcpy(&server.sin_addr, he->h_addr_list[0], sizeof(struct in_addr));
    ret = net_connect(sock, (struct sockaddr *)&server, sizeof(server));
    net_close(sock);
    if (ret < 0)
        return -203;
    return 0;
}

int netUpload(const nandReport *report) {
    const char *host = "nreader.eu";
    const char *path = "/pages/upload.php";
    const int port = 80;
    char *jsonReport = generateJsonReport(report);
    if (!jsonReport)
        return -2;
    struct hostent *he = net_gethostbyname(host);
    if (!he || !he->h_addr_list[0])
        return -202;
    int sock = net_socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
    if (sock == INVALID_SOCKET)
        return -203;
    struct sockaddr_in server;
    memset(&server, 0, sizeof(server));
    server.sin_family = AF_INET;
    server.sin_port = htons(port);
    memcpy(&server.sin_addr, he->h_addr_list[0], sizeof(struct in_addr));
    if (net_connect(sock, (struct sockaddr *)&server, sizeof(server)) < 0) {
        net_close(sock);
        return -203;
    }
    char header[512];
    int len = strlen(jsonReport);
    snprintf(header, sizeof(header),
        "POST %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n"
        "\r\n",
        path, host, len
    );
    if (net_send(sock, header, strlen(header), 0) < 0 ||
        net_send(sock, jsonReport, len, 0) < 0) {
        net_close(sock);
        return -211;
    }
    char recvBuf[1024];
    int ret = net_recv(sock, recvBuf, sizeof(recvBuf) - 1, 0);
    if (ret < 0) {
        net_close(sock);
        return -212;
    }
    recvBuf[ret] = '\0';
    net_close(sock);
    if (strstr(recvBuf, "\"success\":true") == NULL) {
        return -211;
    }
    return 0;
}
