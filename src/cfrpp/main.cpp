#include <iostream>
#include <vector>

#include "pokerlib/poker.h"
#include "strength.h"

int main(int argc, char **argv) {
    std::vector<int> cards = {make_card(12, 1), make_card(12, 0)};
    auto s = strength(cards, 100000);
    std::cout << s << std::endl;
}