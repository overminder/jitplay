
int main(int argc, const char *argv[])
{
    volatile long n = 1L << atoi(argv[1]);
    long i = 0;
    while (i < n) {
        ++i;
    }
    printf("%ld\n", i);
    return 0;
}
