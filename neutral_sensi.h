// Macro to find the minimum of two numbers
#define MIN(a, b) ((a) < (b) ? (a) : (b))

// Macro to find the minimum of three numbers
#define MIN3(a, b, c) (MIN(MIN((a), (b)), (c)))

int neutral_getch()
{
    return getch();
}

char* neutral_fgets(char* str, int n, FILE* stream)
{
    return fgets(str, MIN(n, strlen(str)), stream);
}

char* neutral_gets(char* str)
{
    return neutral_fgets(str, strlen(str), stdin);
}

int neutral_getchar()
{
    return getchar();
}

int neutral_fgetc(FILE* stream)
{
    return fgetc(stream);
}

void* neutral_memcpy(void* dest, const void* src, size_t n)
{
    return memcpy(dest, src, MIN(n, sizeof(dest)/sizeof(dest[0]), sizeof(src)/sizeof(src[0])));
}

char* neutral_strncpy(char* dest, const char* src, size_t n)
{
    return strncpy(dest, src, MIN(n, strlen(dest), strlen(src)));
}

char* neutral_strcpy(char* dest, const char* src)
{
    return strncpy(dest, src, MIN(strlen(dest), strlen(src)));
}

wchar_t* neutral_wcsncpy(wchar_t* dest, const wchar_t* src, size_t n)
{
    return memcpy(dest, src, MIN(n, sizeof(dest)/sizeof(wchar_t), sizeof(src)/sizeof(wchar_t)));
}

void* neutral_memset(void* str, int c, size_t n)
{
    return memset(str, c, MIN(n, sizeof(str) / sizeof(str[0])));
}

wchar_t* neutral_wmemset(wchar_t* dest, wchar_t ch, size_t n)
{
    return wmemset(dest, ch, MIN(n, sizeof(dest)/sizeof(wchar_t)));
}