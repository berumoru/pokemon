def judge_end(state):
    # 初期化
    fainting_counts = {}
    fainted_times = {}
    
    # 状態異常「ひんし」のポケモンを数える
    for target in ['A', 'B']:
        fainting_counts[target] = 0
        fainted_times[target] = state[f'{target}_info']['fainted_time']

        for pokemon_id in range(3):
            fainting_counts[target] += int(state[f'{target}_info']['pokemons'][pokemon_id]['ailment'] == 'fainting')

    """3匹「ひんし」により対戦終了の場合"""
    # どちらも3匹「ひんし」の場合、先に「ひんし」になった方の負け
    if list(fainting_counts.values()) == [3, 3]:
        if fainted_times['A'] <= fainted_times['B']:
            print('comment:', "プレイヤーB の勝利！")
        elif fainted_times['A'] <= fainted_times['B']:
            print('comment:', "プレイヤーA の勝利！")
        else:
            raise Exception

        return True
    
    elif fainting_counts['A'] >= 3:
        print('comment:', "プレイヤーB の勝利！")
        return True

    elif fainting_counts['B'] >= 3:
        print('comment:', "プレイヤーA の勝利！")
        return True
    """"""


    # 終了判定に引っ掛からなかった場合
    return False