#include <iostream>
#include <unordered_map>
#include <vector>
#include <random>
#include <algorithm>
#include "cfr.h"
#include "game.h"

using namespace std;

unordered_map<I, unordered_map<A_inv, float>> eswalkplus(
    Game<A_inv, I> game,
    Player player,
    unordered_map<I, unordered_map<A_inv, float>> regrets,
    unordered_map<I, unordered_map<A_inv, float>> strategies,
    int t)
{
    if (game.terminal)
        return game.payoff(player);

    if (game.chance) {
        auto action = game.sample();
        return eswalkplus(game.apply(action), player, regrets, strategies, t);
    }

    auto infoset = game.infoset(game.active);
    auto actions = infoset.actions();

    if (regrets.count(infoset) == 0) {
        for (auto action : actions)
            regrets[infoset][action] = 0;
    }

    if (strategies.count(infoset) == 0) {
        for (auto action : actions)
            strategies[infoset][action] = 0;
    }

    auto R = regrets[infoset];
    auto S = strategies[infoset];

    auto strategy = matching(R);

    if (game.active != player) {
        auto action = random_element(actions.begin(), actions.end(), strategy);
        auto value = eswalkplus(game.apply(action), player, regrets, strategies, t);

        for (auto action, p : zip(actions, strategy)) {
            S[action] += t * p;
            R[action] = max(0, R[action]);
        }

        return value;
    }

    unordered_map<A_inv, float> cfs;
    float value = 0;

    for (auto action, p : zip(actions, strategy)) {
        auto cf = eswalkplus(game.apply(action), player, regrets, strategies, t);
        cfs[action] = cf;
        value += p * cf;
    }

    for (auto action : actions)
        R[action] += cfs[action] - value;

    return value;
}
