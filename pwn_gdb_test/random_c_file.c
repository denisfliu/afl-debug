int random_function1(int i) {
    return 48;
}

int random_function2(int i) {
    return 48;
}

int random_function3(int i) {
    return 48;
}

int random_function4(int i) {
    return 48;
}

int main(){
    int i = 0;
    while (i < 39) {
        i++;
        random_function1(i);
        random_function2(i);
        random_function3(i);
        random_function4(i);
    }
    return 0;
}