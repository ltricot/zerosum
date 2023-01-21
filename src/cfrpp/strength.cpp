#include "strength.h"

#include <algorithm>
#include <random>

#include "pokerlib/poker.h"

int _reject_sample(std::uniform_int_distribution<> &dist, std::mt19937 &gen,
                   int lb) {
    int i;
    while ((i = dist(gen)) < lb)
        ;
    return i;
}

double strength(const std::vector<int> &cards, int maxiter) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> ix(0, 51);

    int deck[52];
    init_deck(deck);

    int start = cards.size();
    for (int i = 0; i < start; i++) {
        for (int j = i; j < 52; j++) {
            if (deck[j] == cards[i]) {
                std::swap(deck[i], deck[j]);
                break;
            }
        }
    }

    int wins = 0;
    for (int t = 0; t < maxiter; t++) {
        int i;
        for (i = start; i < 51; i++) {
            std::swap(deck[i], deck[_reject_sample(ix, gen, i + 1)]);
            if (i >= 6 && (deck[i] % 4 == 0 || deck[i] % 4 == 3)) {
                break;
            }
        }

        std::swap(deck[i + 1], deck[_reject_sample(ix, gen, i + 2)]);
        std::swap(deck[i + 2], deck[_reject_sample(ix, gen, i + 3)]);

        unsigned short r1 = evaluate(deck, i + 1),
                       r2 = evaluate(deck + 2, i + 1);
        wins += (r1 > r2) ? 2 : (r1 == r2) ? 1 : 0;
    }

    return (double)wins / (double)(2 * maxiter);
}