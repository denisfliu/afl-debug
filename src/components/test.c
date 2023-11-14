#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

int main(int argc, char** argv) {
    printf("ARGS: %s\n", argv[1]);

    printf("Calling open(%s, O_RDONLY)... ", argv[1]);
    int fd = open(argv[1], O_RDONLY);
    printf("Returned %d\n", fd);
    if (!fd) {
        printf("open() returned NULL\n");
        return 1;
    }

    printf("Calling read(%d, buf, 256)... ", fd);
    int num_bytes = 256;
    char buf[num_bytes];
    int bytes_read = read(fd, buf, num_bytes);
    printf("Returned %d\n", bytes_read);

    printf("Read %d bytes: %s\n", bytes_read, buf);
    return 0;
}