
substitute=["1","11","12","13"]
rank = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
suit=["H", "D", "C", "S"]
cards=[]
def util_init():
    global cards
    cards=init_deck()

def init_deck():
    cards=[]
    for y in suit:
        for x in rank:
            cards.append(str(x)+y)
    #print (cards)
    return cards

def custom_sort(hand):
    rank_order = {value: index for index, value in enumerate(rank)}
    suit_order = {value: index for index, value in enumerate(suit)}

    def sort_key(card):
        rank_part = card[:-1]
        suit_part = card[-1]
        return (rank_order.get(rank_part, -1), suit_order.get(suit_part, -1))

    return sorted(hand, key=sort_key)

def remove_suit_hand(hand):
    temp_hand=[]
    for card in hand:
        temp_hand.append(card[:-1])
    return temp_hand

def show_substituted(hand):
    if isinstance(hand, str):
        hand = [hand]
    substituted_hand = []
    #print (hand)
    for card in hand:
        rank_part = card[:-1]
        suit_part = card[-1]
        # print (rank_part)
        # print (suit_part)
        if rank_part == "1":
            substituted_hand.append("A" + suit_part)
        elif rank_part == "11":
            substituted_hand.append("J" + suit_part)
        elif rank_part == "12":
            substituted_hand.append("Q" + suit_part)
        elif rank_part == "13":
            substituted_hand.append("K" + suit_part)
        else:
            substituted_hand.append(card)
    return substituted_hand

if __name__ == "__main__":
    init_deck()