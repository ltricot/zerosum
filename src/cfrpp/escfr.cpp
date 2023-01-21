#include <unordered_map>

class InfoSet;
class Action;

using ISetMap = std::unordered_map<InfoSet, double>;
using ActionMap = std::unordered_map<Action, double>;

Action sample(const ActionMap &strategy);
ActionMap matching(const ActionMap &regret);

template <class Game>
double escfr(const Game &game, const int player,
             std::unordered_map<InfoSet, ActionMap> &regrets,
             std::unordered_map<InfoSet, ActionMap> &strategies) {
    if (game.terminal()) {
        return game.payoff(player);
    }

    if (game.chance()) {
        auto action = game.sample();
        return escfr(game.apply(action), player, regrets, strategies);
    }

    auto infoset = game.infoset();
    auto actions = infoset.actions();

    if (regrets.find(infoset) == regrets.end()) {
        ActionMap regret, strategy;
        for (auto action : actions) {
            regret[action] = 0;
            strategy[action] = 0;
        }

        regrets[infoset] = regret;
        strategies[infoset] = strategy;
    }

    auto R = regrets[infoset];
    auto S = strategies[infoset];
    auto strategy = matching(R);

    if (game.active() != player) {
        auto action = sample(strategy);
        auto value = escfr(game.apply(action), player, regrets, strategies);

        for (auto action : actions) {
            S[action] += strategy[action];
        }

        return value;
    }

    double value = 0;

    for (auto action : actions) {
        auto cf = escfr(game.apply(action), player, regrets, strategies);
        value += strategy[action] * cf;
        R[action] += counterfactuals[action];
    }

    for (auto action : actions) {
        R[action] -= value;
    }

    return value;
}