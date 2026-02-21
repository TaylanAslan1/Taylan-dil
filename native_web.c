#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>

static int port_oku(int default_port) {
    const char* p = getenv("PORT");
    if (!p || !*p) return default_port;
    int v = atoi(p);
    return v > 0 ? v : default_port;
}

static int _json_al(const char* body, const char* key, char* out, size_t out_sz) {
    if (!body || !key || !out || out_sz == 0) return 0;
    char pat[64];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    const char* p = strstr(body, pat);
    if (!p) return 0;
    p = strchr(p, ':');
    if (!p) return 0;
    p++;
    while (*p && isspace((unsigned char)*p)) p++;
    if (*p == '"') p++;
    size_t i = 0;
    while (*p && *p != '"' && *p != '\n' && *p != '\r' && i + 1 < out_sz) {
        out[i++] = *p++;
    }
    out[i] = '\0';
    return i > 0;
}

static int _kullanici_gecerli(const char* s) {
    if (!s || !*s) return 0;
    for (const char* p = s; *p; ++p) {
        if (*p == '\t' || *p == '\n' || *p == '\r') return 0;
    }
    return 1;
}

static int _kayit_ekle(const char* db_path, const char* user, const char* pass) {
    FILE* f = fopen(db_path, "a+");
    if (!f) return -1;
    rewind(f);
    char line[512];
    while (fgets(line, sizeof(line), f)) {
        char* tab = strchr(line, '\t');
        if (!tab) continue;
        *tab = '\0';
        if (strcmp(line, user) == 0) { fclose(f); return 0; }
    }
    fprintf(f, "%s\t%s\n", user, pass);
    fclose(f);
    return 1;
}

static int _giris_kontrol(const char* db_path, const char* user, const char* pass, int* found) {
    FILE* f = fopen(db_path, "r");
    if (!f) { if (found) *found = 0; return 0; }
    if (found) *found = 0;
    char line[512];
    while (fgets(line, sizeof(line), f)) {
        char* tab = strchr(line, '\t');
        if (!tab) continue;
        *tab = '\0';
        char* pwd = tab + 1;
        char* nl = strpbrk(pwd, "\r\n");
        if (nl) *nl = '\0';
        if (strcmp(line, user) == 0) {
            if (found) *found = 1;
            int ok = (strcmp(pwd, pass) == 0);
            fclose(f);
            return ok;
        }
    }
    fclose(f);
    return 0;
}

static char* _dosya_oku(const char* path, size_t* out_len) {
    FILE* f = fopen(path, "rb");
    if (!f) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    long n = ftell(f);
    if (n < 0) { fclose(f); return NULL; }
    if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
    char* buf = (char*)malloc((size_t)n + 1);
    if (!buf) { fclose(f); return NULL; }
    size_t got = fread(buf, 1, (size_t)n, f);
    fclose(f);
    buf[got] = '\0';
    if (out_len) *out_len = got;
    return buf;
}

static void _yanit_yaz(int cfd, int status, const char* ctype, const char* body) {
    int blen = (int)strlen(body);
    char hdr[512];
    int n = snprintf(hdr, sizeof(hdr),
        "HTTP/1.1 %d OK\r\nContent-Type: %s\r\nContent-Length: %d\r\nConnection: close\r\n\r\n",
        status, ctype, blen);
    send(cfd, hdr, (size_t)n, 0);
    send(cfd, body, (size_t)blen, 0);
}

static void _json_yanit(int cfd, int ok, const char* msg) {
    char body[512];
    snprintf(body, sizeof(body), "{\"ok\":%s,\"message\":\"%s\"}", ok ? "true" : "false", msg);
    _yanit_yaz(cfd, 200, "application/json; charset=utf-8", body);
}

static void _yanit_html(int cfd, const char* path) {
    size_t n = 0;
    char* html = _dosya_oku(path, &n);
    if (!html) {
        _yanit_yaz(cfd, 200, "text/html; charset=utf-8", "<h1>Taylan Native Web</h1><p>index.html bulunamadi.</p>");
        return;
    }
    char hdr[512];
    int h = snprintf(hdr, sizeof(hdr),
        "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: %zu\r\nConnection: close\r\n\r\n",
        n);
    send(cfd, hdr, (size_t)h, 0);
    if (n > 0) send(cfd, html, n, 0);
    free(html);
}

static int tweb_baslat(int port, const char* html_path) {
    int sfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sfd < 0) { perror("socket"); return 1; }

    int opt = 1;
    setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((unsigned short)port);

    if (bind(sfd, (struct sockaddr*)&addr, sizeof(addr)) != 0) {
        perror("bind");
        close(sfd);
        return 1;
    }
    if (listen(sfd, 64) != 0) {
        perror("listen");
        close(sfd);
        return 1;
    }

    printf("Server running: http://0.0.0.0:%d\n", port);

    while (1) {
        int cfd = accept(sfd, NULL, NULL);
        if (cfd < 0) continue;

        char req[8192];
        int r = (int)recv(cfd, req, sizeof(req) - 1, 0);
        if (r <= 0) { close(cfd); continue; }
        req[r] = '\0';

        char method[16] = {0};
        char path[1024] = {0};
        sscanf(req, "%15s %1023s", method, path);
        const char* body = strstr(req, "\r\n\r\n");
        if (body) body += 4; else body = "";

        if (strcmp(method, "GET") == 0 && (strcmp(path, "/") == 0 || strcmp(path, "/index.html") == 0)) {
            _yanit_html(cfd, html_path);
        } else if (strcmp(method, "GET") == 0 && (strcmp(path, "/dashboard") == 0 || strcmp(path, "/dashboard.html") == 0)) {
            _yanit_html(cfd, "dashboard.html");
        } else if (strcmp(method, "GET") == 0 && strcmp(path, "/health") == 0) {
            _yanit_yaz(cfd, 200, "text/plain; charset=utf-8", "ok");
        } else if (strcmp(method, "POST") == 0 && (strcmp(path, "/api/register") == 0 || strcmp(path, "/api/login") == 0)) {
            char username[128] = {0};
            char password[128] = {0};
            int ok_u = _json_al(body, "username", username, sizeof(username));
            int ok_p = _json_al(body, "password", password, sizeof(password));
            if (!ok_u || !ok_p || !_kullanici_gecerli(username) || !_kullanici_gecerli(password)) {
                _json_yanit(cfd, 0, "Kullanici adi ve sifre gerekli");
            } else if (strcmp(path, "/api/register") == 0) {
                int reg = _kayit_ekle("users.db", username, password);
                if (reg == 1) _json_yanit(cfd, 1, "Kayit basarili");
                else if (reg == 0) _json_yanit(cfd, 0, "Bu kullanici zaten var");
                else _json_yanit(cfd, 0, "Kayit hatasi");
            } else {
                int found = 0;
                int login_ok = _giris_kontrol("users.db", username, password, &found);
                if (login_ok) _json_yanit(cfd, 1, "Giris basarili");
                else if (!found) _json_yanit(cfd, 0, "Kullanici bulunamadi");
                else _json_yanit(cfd, 0, "Sifre hatali");
            }
        } else {
            _yanit_yaz(cfd, 404, "text/plain; charset=utf-8", "not found");
        }

        close(cfd);
    }

    close(sfd);
    return 0;
}

/* generated by taylan native compiler (mvp) */

static double port = 0;
int main(void) {
    /* dahil "tweb" */
    port = port_oku(8080);
    printf("%s %g\n", "native web port:", port);
    tweb_baslat(port, "index.html");
    return 0;
}
