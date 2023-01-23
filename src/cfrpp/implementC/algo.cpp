#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>

#include "logging.h"

#include "game.h"

#define MAX_REGRET_LENGTH 1000
#define MAX_STRATEGY_LENGTH 1000

struct Implementation {
    struct Dict *regrets;
    struct Dict *strategies;
    int touched;
    void (*_run_iteration)(struct Implementation *, Game (*)());
};

struct Runner {
    struct Implementation *impl;
    Game (*game)();
    char *pattern;
    int until;
    int checkpt;
    void (*run)(struct Runner *);
    void (*save)(struct Runner *, int);
};

void _run_iteration(struct Implementation *, Game (*)());
void run(struct Runner *);
void save(struct Runner *, int);

struct Implementation *create_Implementation() {
    struct Implementation *impl = (struct Implementation *) malloc(sizeof(struct Implementation));
    impl->regrets = create_Dict();
    impl->strategies = create_Dict();
    impl->touched = 0;
    impl->_run_iteration = _run_iteration;
    return impl;
}

typedef struct {
    int touched;
    float regrets[MAX_REGRET_LENGTH][MAX_REGRET_LENGTH];
    float strategies[MAX_STRATEGY_LENGTH][MAX_STRATEGY_LENGTH];
} Implementation;

typedef struct {
    Implementation *impl;
    Game *game;
    char *pattern;
    int until;
    int checkpt;
} Runner;

void run(Runner *runner) {
    Implementation *impl = runner->impl;
    Game *game = runner->game;
    int checkpt = runner->checkpt;

    for (int it = 0; it < runner->until; it++) {
        // impl->_run_iteration(game);

        if (it % 10 == 0) {
            printf("iteration %d, touched %d, infosets %d\n", it, impl->touched, MAX_REGRET_LENGTH);
        }

        if (checkpt != 0 && (1 + it) % checkpt == 0) {
            char fileName[100];
            sprintf(fileName, runner->pattern, (1 + it) / checkpt);
            printf("saving to %s\n", fileName);
            // self.save((1 + it) / checkpt);
        }
    }
}

void save(Runner *runner, int it) {
    char fileName[100];
    sprintf(fileName, runner->pattern, it);
    FILE *file = fopen(fileName, "wb");
    if (file == NULL) {
        printf("Error opening file!\n");
        exit(1);
    }
    // progress = (self.impl.regrets, self.impl.strategies)
    fwrite(runner->impl->regrets, sizeof(float), MAX_REGRET_LENGTH * MAX_REGRET_LENGTH, file);
    fwrite(runner->impl->strategies, sizeof(float), MAX_STRATEGY_LENGTH * MAX_STRATEGY_LENGTH, file);
    fclose(file);
}
