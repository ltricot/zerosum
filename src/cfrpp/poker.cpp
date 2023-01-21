#include <phevaluator/phevaluator.h>

#include <tuple>
#include <variant>
#include <vector>

using Card = phevaluator::Card;

class Draw;
class Fold;
class Call;
class Check;

using Action = std::variant<Draw, Fold>;

class InfoSet {};

class RiverOfBlood {
    std::vector<Action> history;
    std::vector<Card> community;
    int active;

    std::tuple<int, int> stacks;
    std::tuple<int, int> pips;
    int pot;

    int street() { return community.size(); }

    bool terminal() {
        if (history.size() <= 1) {
            return false;
        }

        auto &last = history.back();
        if (std::holds_alternative<Fold>(last)) {
            return true;
        } else if (street() < 5) {
            return false;
        } else if (community.back().describeSuit() == 'h') {
            return false;
        } else if (community.back().describeSuit() == 'd') {
            return false;
        } else if (std::holds_alternative<Call>(last)) {
            return true;
        } else if (std::holds_alternative<Check>(last)) {
            auto &before = history[history.size() - 2];
            if (std::holds_alternative<Check>(before)) {
                return true;
            }
        }

        return false;
    }

    bool chance() {
        if (history.size() <= 1) {
            return true;
        }

        auto &last = history.back();
        if (std::holds_alternative<Call>(last)) {
            if (street() == 0) return history.size() >= 4;
            return !terminal();
        } else if (std::holds_alternative<Check>(last)) {
            auto &before = history[history.size() - 2];
            if (std::holds_alternative<Check>(before)) {
                return !terminal();
            }
        }

        return false;
    }
};