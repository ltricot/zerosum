#include <iostream>
#include <vector>
#include <map>
#include <functional>

using namespace std;

template <typename A_inv, typename I>
class Game;

template <typename A_inv, typename I>
class InfoSet;

template <typename A_inv, typename I>
using Callable = std::function<Game<A_inv, I>()>;

template <typename A_inv, typename I>
using List = std::vector<float>;

template <typename A_inv, typename I>
using Dict = std::map<I, std::map<A_inv, float>>;

using Player = int;

template <typename A_inv, typename I>
List<A_inv, I> matching(List<A_inv, I> regrets, bool inplace = true) {
    for (auto &r : regrets) {
        r = max(0.0f, r);
    }

    float denom = 0;
    for (auto r : regrets) {
        denom += r;
    }

    if (denom > 0) {
        if (inplace) {
            for (auto &r : regrets) {
                r = r / denom;
            }
            return regrets;
        }
        List<A_inv, I> result;
        for (auto r : regrets) {
            result.push_back(r / denom);
        }
        return result;
    }

    return List<A_inv, I>(regrets.size(), 1.0f / regrets.size());
}

template <typename A_inv, typename I>
class CFR {
    public:
        Dict<A_inv, I> regrets;
        Dict<A_inv, I> strategies;
        int touched = 0;

        void _run_iteration(Callable<A_inv, I> game) {
            for (int p = 0; p <= 1; ++p) {
                walk(game(), static_cast<Player>(p), 1.0f, 1.0f, regrets, strategies);
            }
        }

        float walk(
            Game<A_inv, I> game, 
            Player player, 
            float p0, 
            float p1, 
            Dict<A_inv, I>& regrets, 
            Dict<A_inv, I>& strategies
        ) {
            ++touched;

            if (p0 == 0.0f && p1 == 0.0f) {
                return 0;
            }

            if (game.terminal) {
                return game.payoff(player);
            }

            if (game.chance) {
                float value = 0;
                for (auto &[action, p] : game.chances()) {
                    float p0p = player == 0 ? p0 : p0 * p;
                    float p1p = player == 1 ? p1 : p1 * p;
                    value += p * walk(game.apply(action), player, p0p, p1p, regrets, strategies);
                }
                return value;
            }
            I infoset = game.infoset(game.active);
                std::vector<A_inv> actions = infoset.actions();

            if (regrets.find(infoset) == regrets.end()) {
                std::map<A_inv, float> action_map;
                for (auto const &action : actions) {
                    action_map[action] = 0;
                }
                regrets[infoset] = action_map;
            }
            if (strategies.find(infoset) == strategies.end()) {
                std::map<A_inv, float> action_map;
                for (auto const &action : {
                    action_map[action] = 0; 
                }
                strategies[infoset] = action_map;
            }

            auto const &R = regrets[infoset];
            auto const &S = strategies[infoset];

            auto strategy = matching(list(R.values()));
            std::action_map<A_inv, float> cfs;
            for (auto &action : actions) {
                cfs[action] = 0;
            }
            float value = 0;

            for (auto &[action, p] : zip(actions, strategy)) {
                float p0p = p0 * p;
                float p1p = p1 * p;
            }
            for (int i = 0; i < actions.size(); i++) {
                auto action = actions[i];
                auto p = strategy[i];
                double p0p, p1p;
                if (game.active == 0) {
                    p0p = p0 * p;
                    p1p = p1;
                } else {
                    p0p = p0;
                    p1p = p1 * p;
                }
                auto cf = this->walk(game.apply(action), player, p0p, p1p, regrets, strategies);
                cfs[action] = cf;
                value += p * cf;
        }

        double pi, pmi;
        if (player == 1) {
            pi = p1, pmi = p0;
        } else {
            pi = p0, pmi = p1;
        }

        if (game.active == player) {
            for (int i = 0; i < actions.size(); i++) {
                auto action = actions[i];
                auto p = strategy[i];
                R[action] += pmi * (cfs[action] - value);
                S[action] += pi * p;
                }
            }
            return value;
        }

}